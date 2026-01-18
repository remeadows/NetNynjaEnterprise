"""PDF report generation for STIG audit results."""

import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

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
from ..core.logging import get_logger
from ..models import (
    AuditJob,
    AuditResult,
    Target,
    STIGDefinition,
    ComplianceSummary,
    CheckStatus,
)

logger = get_logger(__name__)


def extract_vuln_discussion(description: str) -> str:
    """Extract the VulnDiscussion content from STIG description XML.

    The description field often contains XML-like content with tags such as:
    <VulnDiscussion>...</VulnDiscussion><FalsePositives>...</FalsePositives>...

    This function extracts just the VulnDiscussion content.

    Args:
        description: Raw description that may contain XML tags

    Returns:
        Clean description text
    """
    if not description:
        return ""

    # Try to extract content from <VulnDiscussion> tags
    match = re.search(r'<VulnDiscussion>(.*?)</VulnDiscussion>', description, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If no VulnDiscussion tag, strip any XML-like tags
    # This handles cases where the description might have other XML tags
    cleaned = re.sub(r'<[^>]+>', '', description)
    return cleaned.strip()


def clean_text_for_pdf(text: str) -> str:
    """Clean text for safe PDF rendering.

    Args:
        text: Raw text that may contain special characters

    Returns:
        Text safe for ReportLab PDF rendering
    """
    if not text:
        return ""

    # Escape XML/HTML special characters for ReportLab
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    return text


# Color scheme
COLORS = {
    "header": colors.HexColor("#1f2937"),
    "pass": colors.HexColor("#059669"),
    "fail": colors.HexColor("#dc2626"),
    "na": colors.HexColor("#6b7280"),
    "warning": colors.HexColor("#d97706"),
    "high": colors.HexColor("#dc2626"),
    "medium": colors.HexColor("#d97706"),
    "low": colors.HexColor("#2563eb"),
}


class PDFExporter:
    """PDF report generator for STIG audits."""

    def __init__(self) -> None:
        """Initialize PDF exporter."""
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self) -> None:
        """Add custom paragraph styles."""
        self.styles.add(
            ParagraphStyle(
                "Title2",
                parent=self.styles["Heading1"],
                fontSize=24,
                spaceAfter=30,
                textColor=COLORS["header"],
            )
        )
        self.styles.add(
            ParagraphStyle(
                "Section",
                parent=self.styles["Heading2"],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=10,
                textColor=COLORS["header"],
            )
        )
        self.styles.add(
            ParagraphStyle(
                "FindingHigh",
                parent=self.styles["Normal"],
                textColor=COLORS["high"],
                fontName="Helvetica-Bold",
            )
        )
        self.styles.add(
            ParagraphStyle(
                "FindingMedium",
                parent=self.styles["Normal"],
                textColor=COLORS["medium"],
                fontName="Helvetica-Bold",
            )
        )
        self.styles.add(
            ParagraphStyle(
                "FindingLow",
                parent=self.styles["Normal"],
                textColor=COLORS["low"],
                fontName="Helvetica-Bold",
            )
        )
        self.styles.add(
            ParagraphStyle(
                "Description",
                parent=self.styles["Normal"],
                fontSize=9,
                leftIndent=20,
                spaceBefore=4,
                spaceAfter=4,
                textColor=colors.HexColor("#374151"),
            )
        )
        self.styles.add(
            ParagraphStyle(
                "FixText",
                parent=self.styles["Normal"],
                fontSize=9,
                leftIndent=20,
                spaceBefore=4,
                spaceAfter=8,
                textColor=colors.HexColor("#1d4ed8"),
                fontName="Helvetica-Oblique",
            )
        )
        self.styles.add(
            ParagraphStyle(
                "FieldLabel",
                parent=self.styles["Normal"],
                fontSize=9,
                fontName="Helvetica-Bold",
                textColor=colors.HexColor("#4b5563"),
            )
        )

    def export(
        self,
        job: AuditJob,
        target: Target,
        definition: STIGDefinition,
        results: list[AuditResult],
        summary: ComplianceSummary,
        output_path: Path,
        include_details: bool = True,
        include_remediation: bool = True,
        rule_details: dict[str, dict[str, Any]] | None = None,
    ) -> Path:
        """Export audit results to PDF format.

        Args:
            job: Audit job
            target: Target that was audited
            definition: STIG definition used
            results: Audit results
            summary: Compliance summary
            output_path: Path to write PDF file
            include_details: Include finding details
            include_remediation: Include remediation guidance
            rule_details: Optional dict mapping rule_id to rule info (description, fix_text)

        Returns:
            Path to the generated PDF file
        """
        output_file = output_path / f"{job.id}.pdf"

        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story = []

        # Title
        story.append(Paragraph("STIG Compliance Report", self.styles["Title2"]))
        story.append(Spacer(1, 12))

        # Report metadata
        story.extend(self._build_metadata_section(job, target, definition))
        story.append(Spacer(1, 20))

        # Executive summary
        story.extend(self._build_summary_section(summary))
        story.append(PageBreak())

        # Findings by severity
        story.extend(self._build_findings_section(
            results, include_details, include_remediation, rule_details
        ))

        # Build PDF
        doc.build(story)

        logger.info("pdf_exported", job_id=job.id, path=str(output_file))
        return output_file

    def _build_metadata_section(
        self,
        job: AuditJob,
        target: Target,
        definition: STIGDefinition,
    ) -> list:
        """Build report metadata section."""
        elements = []

        data = [
            ["Report Date:", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
            ["Target:", f"{target.name} ({target.ip_address})"],
            ["Platform:", target.platform.value],
            ["STIG:", definition.title],
            ["STIG ID:", definition.stig_id],
            ["Version:", definition.version or "N/A"],
            ["Audit ID:", job.id],
        ]

        table = Table(data, colWidths=[1.5 * inch, 5 * inch])
        table.setStyle(
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

        elements.append(table)
        return elements

    def _build_summary_section(self, summary: ComplianceSummary) -> list:
        """Build executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles["Section"]))

        # Compliance score
        score_color = (
            COLORS["pass"] if summary.compliance_score >= 80
            else COLORS["warning"] if summary.compliance_score >= 60
            else COLORS["fail"]
        )

        elements.append(
            Paragraph(
                f"Overall Compliance Score: <b>{summary.compliance_score:.1f}%</b>",
                self.styles["Normal"],
            )
        )
        elements.append(Spacer(1, 12))

        # Summary table
        data = [
            ["Category", "Count", "Percentage"],
            ["Passed", str(summary.passed), f"{summary.passed / summary.total_checks * 100:.1f}%"],
            ["Failed", str(summary.failed), f"{summary.failed / summary.total_checks * 100:.1f}%"],
            ["Not Applicable", str(summary.not_applicable), f"{summary.not_applicable / summary.total_checks * 100:.1f}%"],
            ["Not Reviewed", str(summary.not_reviewed), f"{summary.not_reviewed / summary.total_checks * 100:.1f}%"],
            ["Errors", str(summary.errors), f"{summary.errors / summary.total_checks * 100:.1f}%"],
            ["Total Checks", str(summary.total_checks), "100%"],
        ]

        table = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
        table.setStyle(
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
                    # Color rows by status
                    ("TEXTCOLOR", (0, 1), (-1, 1), COLORS["pass"]),
                    ("TEXTCOLOR", (0, 2), (-1, 2), COLORS["fail"]),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 20))

        # Severity breakdown
        elements.append(Paragraph("Findings by Severity", self.styles["Section"]))

        # Helper to safely get severity breakdown values
        def get_sev(severity: str, field: str) -> int:
            breakdown = summary.severity_breakdown.get(severity)
            if breakdown is None:
                return 0
            # Handle both dict and Pydantic model
            if hasattr(breakdown, field):
                return getattr(breakdown, field, 0)
            elif isinstance(breakdown, dict):
                return breakdown.get(field, 0)
            return 0

        sev_data = [
            ["Severity", "Passed", "Failed"],
            [
                "High",
                str(get_sev("high", "passed")),
                str(get_sev("high", "failed")),
            ],
            [
                "Medium",
                str(get_sev("medium", "passed")),
                str(get_sev("medium", "failed")),
            ],
            [
                "Low",
                str(get_sev("low", "passed")),
                str(get_sev("low", "failed")),
            ],
        ]

        sev_table = Table(sev_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch])
        sev_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLORS["header"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 1), (0, 1), COLORS["high"]),
                    ("TEXTCOLOR", (0, 2), (0, 2), COLORS["medium"]),
                    ("TEXTCOLOR", (0, 3), (0, 3), COLORS["low"]),
                ]
            )
        )

        elements.append(sev_table)

        return elements

    def _build_findings_section(
        self,
        results: list[AuditResult],
        include_details: bool,
        include_remediation: bool,
        rule_details: dict[str, dict[str, Any]] | None = None,
    ) -> list:
        """Build detailed findings section.

        Args:
            results: Audit results
            include_details: Include finding details
            include_remediation: Include fix guidance
            rule_details: Optional dict mapping rule_id to rule info
        """
        elements = []
        rule_details = rule_details or {}

        # Sort all results by severity, then by rule_id
        severity_order = {"high": 0, "medium": 1, "low": 2}
        sorted_results = sorted(
            results,
            key=lambda r: (
                severity_order.get(r.severity.value if r.severity else "medium", 3),
                r.rule_id or "",
            ),
        )

        # Build complete findings table (all V-IDs with status)
        elements.append(Paragraph("Complete Findings List", self.styles["Section"]))
        elements.append(
            Paragraph(
                f"All {len(sorted_results)} STIG checks with their compliance status:",
                self.styles["Normal"],
            )
        )
        elements.append(Spacer(1, 12))

        # Status color mapping
        status_colors = {
            CheckStatus.PASS: COLORS["pass"],
            CheckStatus.FAIL: COLORS["fail"],
            CheckStatus.NOT_APPLICABLE: COLORS["na"],
            CheckStatus.NOT_REVIEWED: COLORS["na"],
            CheckStatus.ERROR: COLORS["fail"],
        }

        # Build table data
        table_data = [["V-ID", "Severity", "Status", "Title"]]
        row_styles = []

        for idx, result in enumerate(sorted_results):
            severity = result.severity.value.upper() if result.severity else "MEDIUM"
            status = result.status.value.upper() if result.status else "NOT_REVIEWED"
            # Truncate title for table display
            title = result.title or "No title"
            if len(title) > 60:
                title = title[:57] + "..."

            table_data.append([result.rule_id or "N/A", severity, status, title])

            # Add row-specific styling based on status
            row_num = idx + 1  # +1 for header row
            status_color = status_colors.get(result.status, COLORS["na"])
            row_styles.append(("TEXTCOLOR", (2, row_num), (2, row_num), status_color))

            # Color severity column
            sev_color = COLORS.get(severity.lower(), COLORS["medium"])
            row_styles.append(("TEXTCOLOR", (1, row_num), (1, row_num), sev_color))

        findings_table = Table(
            table_data,
            colWidths=[1.5 * inch, 0.75 * inch, 1 * inch, 3.75 * inch],
        )

        base_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), COLORS["header"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]
        findings_table.setStyle(TableStyle(base_styles + row_styles))

        elements.append(findings_table)
        elements.append(PageBreak())

        # All findings details section with full descriptions
        # Use already sorted results (by severity, then rule_id)
        if not sorted_results:
            elements.append(Paragraph("All Findings Details", self.styles["Section"]))
            elements.append(
                Paragraph(
                    "No checks found.",
                    self.styles["Normal"],
                )
            )
            return elements

        elements.append(Paragraph("All Findings Details", self.styles["Section"]))
        failed_count = sum(1 for r in sorted_results if r.status == CheckStatus.FAIL)
        passed_count = sum(1 for r in sorted_results if r.status == CheckStatus.PASS)
        elements.append(
            Paragraph(
                f"Complete details for all {len(sorted_results)} checks "
                f"({passed_count} passed, {failed_count} failed). "
                "Each finding includes the full description and recommended fix where applicable.",
                self.styles["Normal"],
            )
        )
        elements.append(Spacer(1, 12))

        for result in sorted_results:
            severity = result.severity.value if result.severity else "medium"
            style_name = f"Finding{severity.capitalize()}"

            # Get rule details from the dictionary
            rule_info = rule_details.get(result.rule_id, {})
            raw_description = rule_info.get("description", "")
            fix_text = rule_info.get("fix_text", "")

            # Extract just the VulnDiscussion content from the description
            description = extract_vuln_discussion(raw_description)

            # Build finding block (kept together)
            # Format: V-ID, Severity, Status, Description, Fix Text
            finding_block = []

            # V-ID (Rule ID)
            finding_block.append(
                Paragraph(
                    f"<b>V-ID:</b> {result.rule_id or 'N/A'}",
                    self.styles.get(style_name, self.styles["Normal"]),
                )
            )

            # Severity
            finding_block.append(
                Paragraph(
                    f"<b>Severity:</b> {severity.upper()}",
                    self.styles["Normal"],
                )
            )

            # Status with color coding
            status_text = result.status.value.upper() if result.status else "NOT_REVIEWED"
            status_display = {
                "PASS": "Closed",
                "FAIL": "Open",
                "NOT_APPLICABLE": "N/A",
                "NOT_REVIEWED": "Not Reviewed",
                "ERROR": "Error",
            }.get(status_text, status_text)
            status_color = {
                "PASS": "#059669",  # green
                "FAIL": "#dc2626",  # red
                "NOT_APPLICABLE": "#6b7280",  # gray
                "NOT_REVIEWED": "#d97706",  # amber
                "ERROR": "#dc2626",  # red
            }.get(status_text, "#6b7280")
            finding_block.append(
                Paragraph(
                    f"<b>Status:</b> <font color='{status_color}'>{status_display}</font>",
                    self.styles["Normal"],
                )
            )

            # Title
            finding_block.append(
                Paragraph(
                    f"<b>Title:</b> {clean_text_for_pdf(result.title or 'No title')}",
                    self.styles["Normal"],
                )
            )
            finding_block.append(Spacer(1, 6))

            # Description (Vulnerability Discussion - cleaned)
            if description:
                finding_block.append(
                    Paragraph("<b>Description:</b>", self.styles["FieldLabel"])
                )
                finding_block.append(
                    Paragraph(clean_text_for_pdf(description), self.styles["Description"])
                )

            # Finding details (what was found during the audit)
            if include_details and result.finding_details:
                finding_block.append(
                    Paragraph("<b>Finding Details:</b>", self.styles["FieldLabel"])
                )
                finding_block.append(
                    Paragraph(clean_text_for_pdf(result.finding_details), self.styles["Description"])
                )

            # Fix text (remediation guidance)
            if include_remediation and fix_text:
                finding_block.append(
                    Paragraph("<b>Fix Text (Remediation):</b>", self.styles["FieldLabel"])
                )
                finding_block.append(
                    Paragraph(clean_text_for_pdf(fix_text), self.styles["FixText"])
                )

            # Add separator line
            finding_block.append(Spacer(1, 8))
            finding_block.append(
                Paragraph(
                    "_" * 80,
                    self.styles["Normal"],
                )
            )
            finding_block.append(Spacer(1, 12))

            # Keep the entire finding together on one page if possible
            elements.append(KeepTogether(finding_block))

        return elements
