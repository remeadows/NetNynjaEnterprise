"""Report generation orchestration."""

import asyncio
import json
import signal
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

import nats
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig, DeliverPolicy, AckPolicy

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)

from ..core.config import settings
from ..core.logging import configure_logging, get_logger
from ..db.connection import init_db, close_db
from ..db.repository import (
    TargetRepository,
    DefinitionRepository,
    AuditJobRepository,
    AuditResultRepository,
    AuditGroupRepository,
)
from ..models import ReportFormat, AuditStatus, ComplianceSummary, SeverityBreakdown
from ..services.audit import AuditService
from .ckl import CKLExporter
from .pdf import PDFExporter, COLORS

logger = get_logger(__name__)


class ReportGenerator:
    """Service for generating STIG reports."""

    def __init__(self) -> None:
        """Initialize report generator."""
        self.output_dir = Path(settings.report_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.ckl_exporter = CKLExporter()
        self.pdf_exporter = PDFExporter()
        self.audit_service = AuditService()

        self._nc: nats.NATS | None = None
        self._js: JetStreamContext | None = None
        self._running = False

    async def connect_nats(self) -> None:
        """Connect to NATS for job notifications."""
        try:
            self._nc = await nats.connect(settings.nats_url)
            self._js = self._nc.jetstream()
            logger.info("nats_connected", url=settings.nats_url)
        except Exception as e:
            logger.warning("nats_connection_failed", error=str(e))

    async def disconnect_nats(self) -> None:
        """Disconnect from NATS."""
        self._running = False
        if self._nc:
            await self._nc.drain()
            self._nc = None
            self._js = None

    async def generate(
        self,
        job_id: str,
        format: ReportFormat,
        include_details: bool = True,
        include_remediation: bool = True,
    ) -> Path:
        """Generate a report for an audit job.

        Args:
            job_id: ID of the completed audit job
            format: Report format (pdf, ckl, etc.)
            include_details: Include finding details
            include_remediation: Include fix guidance

        Returns:
            Path to the generated report file

        Raises:
            ValueError: If job not found or not completed
        """
        # Get job and related data
        job = await AuditJobRepository.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status != AuditStatus.COMPLETED:
            raise ValueError(f"Job not completed: {job.status}")

        target = await TargetRepository.get_by_id(job.target_id)
        definition = await DefinitionRepository.get_by_id(job.definition_id)

        if not target or not definition:
            raise ValueError("Target or definition not found")

        # Get all results
        results, _ = await AuditResultRepository.list_by_job(job_id, per_page=1000)

        # Fetch rule details from database for full descriptions and fix text
        db_rules = await DefinitionRepository.get_rules(definition.id)
        rule_details = {
            rule["rule_id"]: {
                "description": rule.get("description", ""),
                "fix_text": rule.get("fix_text", ""),
                "check_text": rule.get("check_text", ""),
            }
            for rule in db_rules
        }

        # Generate based on format
        if format == ReportFormat.CKL:
            return self.ckl_exporter.export(
                job, target, definition, results, self.output_dir, rule_details
            )
        elif format == ReportFormat.PDF:
            summary = await self.audit_service.get_compliance_summary(job_id)
            if not summary:
                raise ValueError("Could not generate compliance summary")

            return self.pdf_exporter.export(
                job,
                target,
                definition,
                results,
                summary,
                self.output_dir,
                include_details,
                include_remediation,
                rule_details,
            )
        elif format == ReportFormat.JSON:
            return await self._export_json(job_id, results)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def generate_combined_pdf(
        self,
        group_id: str,
        include_details: bool = True,
        include_remediation: bool = True,
    ) -> Path:
        """Generate a combined PDF report for an audit group.

        Args:
            group_id: ID of the audit group
            include_details: Include finding details
            include_remediation: Include fix guidance

        Returns:
            Path to the generated PDF file

        Raises:
            ValueError: If group not found or not completed
        """
        # Get group and jobs
        group = await AuditGroupRepository.get_by_id(group_id)
        if not group:
            raise ValueError(f"Audit group not found: {group_id}")

        if group.status != AuditStatus.COMPLETED:
            raise ValueError(f"Audit group not completed: {group.status}")

        jobs = await AuditGroupRepository.get_jobs(group_id)
        if not jobs:
            raise ValueError("No jobs found in audit group")

        # Get target info
        target = await TargetRepository.get_by_id(group.target_id)
        if not target:
            raise ValueError("Target not found")

        output_file = self.output_dir / f"combined_{group_id}.pdf"

        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()
        self._add_combined_styles(styles)

        story = []

        # Title page
        story.append(Paragraph("Combined STIG Compliance Report", styles["Title2"]))
        story.append(Spacer(1, 12))

        # Group metadata
        metadata = [
            ["Report Date:", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
            ["Target:", f"{target.name} ({target.ip_address})"],
            ["Platform:", target.platform.value],
            ["Audit Group:", group.name],
            ["Total STIGs:", str(len(jobs))],
            ["Group ID:", group_id],
        ]

        meta_table = Table(metadata, colWidths=[1.5 * inch, 5 * inch])
        meta_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 20))

        # Collect data for overall summary
        overall_passed = 0
        overall_failed = 0
        overall_na = 0
        overall_nr = 0
        overall_errors = 0
        overall_total = 0
        stig_summaries = []

        for job in jobs:
            if job.status != AuditStatus.COMPLETED:
                continue

            definition = await DefinitionRepository.get_by_id(job.definition_id)
            summary = await self.audit_service.get_compliance_summary(job.id)

            if summary and definition:
                overall_passed += summary.passed
                overall_failed += summary.failed
                overall_na += summary.not_applicable
                overall_nr += summary.not_reviewed
                overall_errors += summary.errors
                overall_total += summary.total_checks

                stig_summaries.append({
                    "title": definition.title,
                    "stig_id": definition.stig_id,
                    "summary": summary,
                    "job": job,
                    "definition": definition,
                })

        # Overall compliance score
        overall_score = (overall_passed / overall_total * 100) if overall_total > 0 else 0

        # Executive Summary
        story.append(Paragraph("Executive Summary", styles["Section"]))
        story.append(
            Paragraph(
                f"Overall Compliance Score: <b>{overall_score:.1f}%</b>",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))

        summary_data = [
            ["Category", "Count", "Percentage"],
            ["Passed", str(overall_passed), f"{(overall_passed / overall_total * 100) if overall_total > 0 else 0:.1f}%"],
            ["Failed", str(overall_failed), f"{(overall_failed / overall_total * 100) if overall_total > 0 else 0:.1f}%"],
            ["Not Applicable", str(overall_na), f"{(overall_na / overall_total * 100) if overall_total > 0 else 0:.1f}%"],
            ["Not Reviewed", str(overall_nr), f"{(overall_nr / overall_total * 100) if overall_total > 0 else 0:.1f}%"],
            ["Errors", str(overall_errors), f"{(overall_errors / overall_total * 100) if overall_total > 0 else 0:.1f}%"],
            ["Total Checks", str(overall_total), "100%"],
        ]

        summary_table = Table(summary_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLORS["header"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 1), (-1, 1), COLORS["pass"]),
                    ("TEXTCOLOR", (0, 2), (-1, 2), COLORS["fail"]),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 20))

        # Per-STIG compliance summary
        story.append(Paragraph("Per-STIG Compliance Summary", styles["Section"]))

        per_stig_data = [["STIG", "Checks", "Passed", "Failed", "Score"]]
        for stig in stig_summaries:
            s = stig["summary"]
            score = s.compliance_score
            per_stig_data.append([
                stig["title"][:40] + "..." if len(stig["title"]) > 40 else stig["title"],
                str(s.total_checks),
                str(s.passed),
                str(s.failed),
                f"{score:.1f}%",
            ])

        per_stig_table = Table(per_stig_data, colWidths=[3 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch])
        per_stig_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLORS["header"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(per_stig_table)
        story.append(PageBreak())

        # Individual STIG sections
        for stig in stig_summaries:
            story.append(Paragraph(f"STIG: {stig['title']}", styles["Section"]))
            story.append(Paragraph(f"STIG ID: {stig['stig_id']}", styles["Normal"]))
            story.append(Spacer(1, 12))

            s = stig["summary"]
            score = s.compliance_score
            score_color = (
                COLORS["pass"] if score >= 80
                else COLORS["warning"] if score >= 60
                else COLORS["fail"]
            )

            story.append(
                Paragraph(
                    f"Compliance Score: <b>{score:.1f}%</b>",
                    styles["Normal"],
                )
            )

            stig_data = [
                ["Passed", str(s.passed)],
                ["Failed", str(s.failed)],
                ["Not Applicable", str(s.not_applicable)],
                ["Not Reviewed", str(s.not_reviewed)],
                ["Total Checks", str(s.total_checks)],
            ]

            stig_table = Table(stig_data, colWidths=[2 * inch, 1 * inch])
            stig_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("ALIGN", (1, 0), (1, -1), "CENTER"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(stig_table)
            story.append(Spacer(1, 20))

        # Build PDF
        doc.build(story)

        logger.info("combined_pdf_exported", group_id=group_id, path=str(output_file))
        return output_file

    async def generate_combined_ckl_zip(self, group_id: str) -> Path:
        """Generate a ZIP file containing CKL checklists for all jobs in an audit group.

        Args:
            group_id: ID of the audit group

        Returns:
            Path to the generated ZIP file

        Raises:
            ValueError: If group not found
        """
        # Get group and jobs
        group = await AuditGroupRepository.get_by_id(group_id)
        if not group:
            raise ValueError(f"Audit group not found: {group_id}")

        jobs = await AuditGroupRepository.get_jobs(group_id)
        if not jobs:
            raise ValueError("No jobs found in audit group")

        # Get target info
        target = await TargetRepository.get_by_id(group.target_id)
        if not target:
            raise ValueError("Target not found")

        output_file = self.output_dir / f"checklists_{group_id}.zip"

        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for job in jobs:
                if job.status != AuditStatus.COMPLETED:
                    continue

                definition = await DefinitionRepository.get_by_id(job.definition_id)
                if not definition:
                    continue

                # Get results for this job
                results, _ = await AuditResultRepository.list_by_job(job.id, per_page=1000)

                # Generate CKL
                ckl_path = self.ckl_exporter.export(
                    job, target, definition, results, self.output_dir
                )

                # Add to ZIP with a descriptive name
                safe_title = definition.stig_id.replace("/", "_").replace("\\", "_")
                zip_filename = f"{target.name}_{safe_title}.ckl"
                zf.write(ckl_path, zip_filename)

                # Clean up individual CKL file
                ckl_path.unlink()

        logger.info("combined_ckl_zip_exported", group_id=group_id, path=str(output_file))
        return output_file

    async def generate_combined_pdf_from_jobs(
        self,
        job_ids: list[str],
        include_details: bool = True,
        include_remediation: bool = True,
    ) -> Path:
        """Generate a combined PDF report from multiple audit job IDs.

        Creates a single PDF with separate sections for each STIG,
        including full details for all findings.

        Args:
            job_ids: List of audit job IDs
            include_details: Include finding details
            include_remediation: Include fix guidance

        Returns:
            Path to the generated PDF file

        Raises:
            ValueError: If no valid jobs found
        """
        if not job_ids:
            raise ValueError("No job IDs provided")

        # Collect job data
        job_data_list = []
        target = None

        for job_id in job_ids:
            job = await AuditJobRepository.get_by_id(job_id)
            if not job:
                logger.warning("job_not_found", job_id=job_id)
                continue

            definition = await DefinitionRepository.get_by_id(job.definition_id)
            if not definition:
                logger.warning("definition_not_found", job_id=job_id)
                continue

            if target is None:
                target = await TargetRepository.get_by_id(job.target_id)

            # Get results and summary
            results, _ = await AuditResultRepository.list_by_job(job_id, per_page=1000)
            summary = await self.audit_service.get_compliance_summary(job_id)

            # Get rule details from database for full descriptions
            db_rules = await DefinitionRepository.get_rules(definition.id)
            rule_details = {
                rule["rule_id"]: {
                    "description": rule.get("description", ""),
                    "fix_text": rule.get("fix_text", ""),
                    "check_text": rule.get("check_text", ""),
                }
                for rule in db_rules
            }

            job_data_list.append({
                "job": job,
                "definition": definition,
                "results": results,
                "summary": summary,
                "rule_details": rule_details,
            })

        if not job_data_list:
            raise ValueError("No valid jobs found")

        if not target:
            raise ValueError("Target not found")

        # Create combined file name using hash of job IDs
        import hashlib
        jobs_hash = hashlib.md5(",".join(job_ids).encode()).hexdigest()[:12]
        output_file = self.output_dir / f"combined_jobs_{jobs_hash}.pdf"

        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()
        self._add_combined_styles(styles)
        self._add_finding_styles(styles)

        story = []

        # Title page
        story.append(Paragraph("Combined STIG Compliance Report", styles["Title2"]))
        story.append(Spacer(1, 12))

        # Metadata
        metadata = [
            ["Report Date:", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
            ["Target:", f"{target.name} ({target.ip_address})"],
            ["Platform:", target.platform.value],
            ["Total STIGs:", str(len(job_data_list))],
        ]

        meta_table = Table(metadata, colWidths=[1.5 * inch, 5 * inch])
        meta_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 20))

        # Calculate overall summary
        overall_passed = sum(d["summary"].passed for d in job_data_list if d["summary"])
        overall_failed = sum(d["summary"].failed for d in job_data_list if d["summary"])
        overall_na = sum(d["summary"].not_applicable for d in job_data_list if d["summary"])
        overall_nr = sum(d["summary"].not_reviewed for d in job_data_list if d["summary"])
        overall_errors = sum(d["summary"].errors for d in job_data_list if d["summary"])
        overall_total = sum(d["summary"].total_checks for d in job_data_list if d["summary"])
        overall_score = (overall_passed / (overall_passed + overall_failed) * 100) if (overall_passed + overall_failed) > 0 else 0

        # Executive Summary
        story.append(Paragraph("Executive Summary", styles["Section"]))
        story.append(
            Paragraph(
                f"Overall Compliance Score: <b>{overall_score:.1f}%</b>",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))

        summary_data = [
            ["Category", "Count", "Percentage"],
            ["Passed", str(overall_passed), f"{(overall_passed / overall_total * 100) if overall_total > 0 else 0:.1f}%"],
            ["Failed", str(overall_failed), f"{(overall_failed / overall_total * 100) if overall_total > 0 else 0:.1f}%"],
            ["Not Applicable", str(overall_na), f"{(overall_na / overall_total * 100) if overall_total > 0 else 0:.1f}%"],
            ["Not Reviewed", str(overall_nr), f"{(overall_nr / overall_total * 100) if overall_total > 0 else 0:.1f}%"],
            ["Errors", str(overall_errors), f"{(overall_errors / overall_total * 100) if overall_total > 0 else 0:.1f}%"],
            ["Total Checks", str(overall_total), "100%"],
        ]

        summary_table = Table(summary_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLORS["header"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 1), (-1, 1), COLORS["pass"]),
                    ("TEXTCOLOR", (0, 2), (-1, 2), COLORS["fail"]),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 20))

        # Per-STIG compliance summary table
        story.append(Paragraph("Per-STIG Compliance Summary", styles["Section"]))

        per_stig_data = [["STIG", "Checks", "Passed", "Failed", "Score"]]
        for data in job_data_list:
            s = data["summary"]
            title = data["definition"].title
            if s:
                per_stig_data.append([
                    title[:40] + "..." if len(title) > 40 else title,
                    str(s.total_checks),
                    str(s.passed),
                    str(s.failed),
                    f"{s.compliance_score:.1f}%",
                ])

        per_stig_table = Table(per_stig_data, colWidths=[3 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch])
        per_stig_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLORS["header"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(per_stig_table)
        story.append(PageBreak())

        # Individual STIG sections with full details
        for data in job_data_list:
            definition = data["definition"]
            results = data["results"]
            summary = data["summary"]
            rule_details = data["rule_details"]

            # STIG header
            story.append(Paragraph(f"STIG: {definition.title}", styles["Section"]))
            story.append(Paragraph(f"STIG ID: {definition.stig_id}", styles["Normal"]))
            if summary:
                story.append(
                    Paragraph(
                        f"Compliance Score: <b>{summary.compliance_score:.1f}%</b> "
                        f"({summary.passed} passed, {summary.failed} failed of {summary.total_checks} checks)",
                        styles["Normal"],
                    )
                )
            story.append(Spacer(1, 12))

            # All findings for this STIG
            story.extend(
                self._build_stig_findings_section(
                    results, rule_details, styles, include_details, include_remediation
                )
            )
            story.append(PageBreak())

        # Build PDF
        doc.build(story)

        logger.info("combined_pdf_from_jobs_exported", job_count=len(job_ids), path=str(output_file))
        return output_file

    async def generate_combined_ckl_from_jobs(self, job_ids: list[str]) -> Path:
        """Generate a ZIP file containing CKL checklists for multiple audit jobs.

        Args:
            job_ids: List of audit job IDs

        Returns:
            Path to the generated ZIP file

        Raises:
            ValueError: If no valid jobs found
        """
        if not job_ids:
            raise ValueError("No job IDs provided")

        # Create combined file name using hash of job IDs
        import hashlib
        jobs_hash = hashlib.md5(",".join(job_ids).encode()).hexdigest()[:12]
        output_file = self.output_dir / f"checklists_jobs_{jobs_hash}.zip"

        target = None
        ckl_files = []

        for job_id in job_ids:
            job = await AuditJobRepository.get_by_id(job_id)
            if not job:
                logger.warning("job_not_found", job_id=job_id)
                continue

            if target is None:
                target = await TargetRepository.get_by_id(job.target_id)

            definition = await DefinitionRepository.get_by_id(job.definition_id)
            if not definition:
                continue

            # Get results for this job
            results, _ = await AuditResultRepository.list_by_job(job_id, per_page=1000)

            # Get rule details from database
            db_rules = await DefinitionRepository.get_rules(definition.id)
            rule_details = {
                rule["rule_id"]: {
                    "description": rule.get("description", ""),
                    "fix_text": rule.get("fix_text", ""),
                    "check_text": rule.get("check_text", ""),
                }
                for rule in db_rules
            }

            # Generate CKL
            ckl_path = self.ckl_exporter.export(
                job, target, definition, results, self.output_dir, rule_details
            )
            ckl_files.append((ckl_path, definition))

        if not ckl_files:
            raise ValueError("No valid jobs found")

        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for ckl_path, definition in ckl_files:
                safe_title = definition.stig_id.replace("/", "_").replace("\\", "_")
                zip_filename = f"{target.name if target else 'Unknown'}_{safe_title}.ckl"
                zf.write(ckl_path, zip_filename)
                # Clean up individual CKL file
                ckl_path.unlink()

        logger.info("combined_ckl_from_jobs_exported", job_count=len(job_ids), path=str(output_file))
        return output_file

    def _add_finding_styles(self, styles) -> None:
        """Add custom styles for finding details."""
        if "FindingHigh" not in styles:
            styles.add(
                ParagraphStyle(
                    "FindingHigh",
                    parent=styles["Normal"],
                    textColor=COLORS["high"],
                    fontName="Helvetica-Bold",
                )
            )
        if "FindingMedium" not in styles:
            styles.add(
                ParagraphStyle(
                    "FindingMedium",
                    parent=styles["Normal"],
                    textColor=COLORS["medium"],
                    fontName="Helvetica-Bold",
                )
            )
        if "FindingLow" not in styles:
            styles.add(
                ParagraphStyle(
                    "FindingLow",
                    parent=styles["Normal"],
                    textColor=COLORS["low"],
                    fontName="Helvetica-Bold",
                )
            )
        if "Description" not in styles:
            styles.add(
                ParagraphStyle(
                    "Description",
                    parent=styles["Normal"],
                    fontSize=9,
                    leftIndent=20,
                    spaceBefore=4,
                    spaceAfter=4,
                    textColor=colors.HexColor("#374151"),
                )
            )
        if "FixText" not in styles:
            styles.add(
                ParagraphStyle(
                    "FixText",
                    parent=styles["Normal"],
                    fontSize=9,
                    leftIndent=20,
                    spaceBefore=4,
                    spaceAfter=8,
                    textColor=colors.HexColor("#1d4ed8"),
                    fontName="Helvetica-Oblique",
                )
            )
        if "FieldLabel" not in styles:
            styles.add(
                ParagraphStyle(
                    "FieldLabel",
                    parent=styles["Normal"],
                    fontSize=9,
                    fontName="Helvetica-Bold",
                    textColor=colors.HexColor("#4b5563"),
                )
            )

    def _build_stig_findings_section(
        self,
        results: list,
        rule_details: dict,
        styles,
        include_details: bool,
        include_remediation: bool,
    ) -> list:
        """Build the findings section for a single STIG.

        Args:
            results: Audit results for this STIG
            rule_details: Rule details dictionary
            styles: PDF styles
            include_details: Include finding details
            include_remediation: Include fix guidance

        Returns:
            List of PDF elements
        """
        from ..reports.pdf import extract_vuln_discussion, clean_text_for_pdf

        elements = []

        # Sort results by severity, then by rule_id
        severity_order = {"high": 0, "medium": 1, "low": 2}
        sorted_results = sorted(
            results,
            key=lambda r: (
                severity_order.get(r.severity.value if r.severity else "medium", 3),
                r.rule_id or "",
            ),
        )

        if not sorted_results:
            elements.append(
                Paragraph("No checks found for this STIG.", styles["Normal"])
            )
            return elements

        # Summary counts
        from ..models import CheckStatus
        failed_count = sum(1 for r in sorted_results if r.status == CheckStatus.FAIL)
        passed_count = sum(1 for r in sorted_results if r.status == CheckStatus.PASS)

        elements.append(
            Paragraph(
                f"All {len(sorted_results)} Findings ({passed_count} passed, {failed_count} failed):",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 12))

        for result in sorted_results:
            severity = result.severity.value if result.severity else "medium"
            style_name = f"Finding{severity.capitalize()}"

            # Get rule details
            rule_info = rule_details.get(result.rule_id, {})
            raw_description = rule_info.get("description", "")
            fix_text = rule_info.get("fix_text", "")

            # Extract clean description
            description = extract_vuln_discussion(raw_description)

            # Build finding block
            finding_block = []

            # V-ID
            finding_block.append(
                Paragraph(
                    f"<b>V-ID:</b> {result.rule_id or 'N/A'}",
                    styles.get(style_name, styles["Normal"]),
                )
            )

            # Severity
            finding_block.append(
                Paragraph(
                    f"<b>Severity:</b> {severity.upper()}",
                    styles["Normal"],
                )
            )

            # Status with color
            status_text = result.status.value.upper() if result.status else "NOT_REVIEWED"
            status_display = {
                "PASS": "Closed",
                "FAIL": "Open",
                "NOT_APPLICABLE": "N/A",
                "NOT_REVIEWED": "Not Reviewed",
                "ERROR": "Error",
            }.get(status_text, status_text)
            status_color = {
                "PASS": "#059669",
                "FAIL": "#dc2626",
                "NOT_APPLICABLE": "#6b7280",
                "NOT_REVIEWED": "#d97706",
                "ERROR": "#dc2626",
            }.get(status_text, "#6b7280")
            finding_block.append(
                Paragraph(
                    f"<b>Status:</b> <font color='{status_color}'>{status_display}</font>",
                    styles["Normal"],
                )
            )

            # Title
            finding_block.append(
                Paragraph(
                    f"<b>Title:</b> {clean_text_for_pdf(result.title or 'No title')}",
                    styles["Normal"],
                )
            )
            finding_block.append(Spacer(1, 6))

            # Description
            if description:
                finding_block.append(
                    Paragraph("<b>Description:</b>", styles["FieldLabel"])
                )
                finding_block.append(
                    Paragraph(clean_text_for_pdf(description), styles["Description"])
                )

            # Finding details
            if include_details and result.finding_details:
                finding_block.append(
                    Paragraph("<b>Finding Details:</b>", styles["FieldLabel"])
                )
                finding_block.append(
                    Paragraph(clean_text_for_pdf(result.finding_details), styles["Description"])
                )

            # Fix text
            if include_remediation and fix_text:
                finding_block.append(
                    Paragraph("<b>Fix Text (Remediation):</b>", styles["FieldLabel"])
                )
                finding_block.append(
                    Paragraph(clean_text_for_pdf(fix_text), styles["FixText"])
                )

            # Separator
            finding_block.append(Spacer(1, 8))
            finding_block.append(
                Paragraph("_" * 80, styles["Normal"])
            )
            finding_block.append(Spacer(1, 12))

            elements.append(KeepTogether(finding_block))

        return elements

    def _add_combined_styles(self, styles) -> None:
        """Add custom styles for combined reports."""
        styles.add(
            ParagraphStyle(
                "Title2",
                parent=styles["Heading1"],
                fontSize=24,
                spaceAfter=30,
                textColor=COLORS["header"],
            )
        )
        styles.add(
            ParagraphStyle(
                "Section",
                parent=styles["Heading2"],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=10,
                textColor=COLORS["header"],
            )
        )

    async def _export_json(self, job_id: str, results: list) -> Path:
        """Export results to JSON format."""
        output_file = self.output_dir / f"{job_id}.json"

        data = {
            "job_id": job_id,
            "generated_at": str(datetime.utcnow()),
            "results": [r.model_dump() for r in results],
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info("json_exported", job_id=job_id, path=str(output_file))
        return output_file

    async def start_consumer(self) -> None:
        """Start consuming report generation requests from NATS."""
        if not self._js:
            logger.warning("nats_not_connected")
            return

        self._running = True

        try:
            # Use pull subscription which supports fetch()
            sub = await self._js.pull_subscribe(
                "stig.results.*",
                durable="report-generator",
                config=ConsumerConfig(
                    deliver_policy=DeliverPolicy.ALL,
                    ack_policy=AckPolicy.EXPLICIT,
                    ack_wait=300,
                    max_deliver=3,
                ),
            )

            logger.info("report_consumer_started", subject="stig.results.*")

            while self._running:
                try:
                    msgs = await sub.fetch(batch=1, timeout=5)
                    for msg in msgs:
                        await self._process_completion(msg)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error("report_processing_error", error=str(e))

        except Exception as e:
            logger.error("report_consumer_failed", error=str(e))

    async def _process_completion(self, msg: nats.aio.msg.Msg) -> None:
        """Process audit completion and generate reports if configured."""
        try:
            data = json.loads(msg.data.decode())
            job_id = data.get("job_id")

            if not job_id:
                await msg.ack()
                return

            logger.info("audit_completed_notification", job_id=job_id)

            # Auto-generate CKL for completed audits
            try:
                await self.generate(job_id, ReportFormat.CKL)
            except Exception as e:
                logger.error("auto_ckl_generation_failed", job_id=job_id, error=str(e))

            await msg.ack()

        except Exception as e:
            logger.error("completion_processing_failed", error=str(e))
            await msg.nak()


from datetime import datetime


async def main() -> None:
    """Main entry point for report generator worker."""
    configure_logging()
    logger.info("starting_report_generator")

    # Initialize database
    await init_db()

    # Create generator
    generator = ReportGenerator()
    await generator.connect_nats()

    # Setup signal handlers
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("shutdown_signal_received")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    # Start consumer
    consumer_task = asyncio.create_task(generator.start_consumer())

    # Wait for shutdown
    await stop_event.wait()

    # Cleanup
    await generator.disconnect_nats()
    consumer_task.cancel()
    await close_db()

    logger.info("report_generator_stopped")


if __name__ == "__main__":
    asyncio.run(main())
