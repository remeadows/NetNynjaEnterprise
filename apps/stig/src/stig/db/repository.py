"""STIG database repositories."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg

from ..core.logging import get_logger
from ..models import (
    Target,
    TargetCreate,
    TargetUpdate,
    STIGDefinition,
    AuditJob,
    AuditJobCreate,
    AuditStatus,
    AuditResult,
    AuditResultCreate,
    CheckStatus,
    TargetDefinition,
    TargetDefinitionCreate,
    TargetDefinitionUpdate,
    TargetDefinitionWithCompliance,
    AuditGroup,
    AuditGroupCreate,
)
from .connection import get_pool

logger = get_logger(__name__)


class TargetRepository:
    """Repository for target operations."""

    @staticmethod
    async def list(
        page: int = 1,
        per_page: int = 20,
        platform: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Target], int]:
        """List targets with pagination and filtering."""
        pool = get_pool()

        conditions = []
        params: list[Any] = []
        param_idx = 1

        if platform:
            conditions.append(f"platform = ${param_idx}")
            params.append(platform)
            param_idx += 1

        if is_active is not None:
            conditions.append(f"is_active = ${param_idx}")
            params.append(is_active)
            param_idx += 1

        if search:
            conditions.append(f"(name ILIKE ${param_idx} OR ip_address::text LIKE ${param_idx})")
            params.append(f"%{search}%")
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        async with pool.acquire() as conn:
            # Get total count
            count_query = f"SELECT COUNT(*) FROM stig.targets WHERE {where_clause}"
            total = await conn.fetchval(count_query, *params)

            # Get paginated results
            offset = (page - 1) * per_page
            query = f"""
                SELECT id, name, ip_address, platform, os_version, connection_type,
                       credential_id, port, is_active, last_audit, created_at, updated_at
                FROM stig.targets
                WHERE {where_clause}
                ORDER BY name ASC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([per_page, offset])

            rows = await conn.fetch(query, *params)

        targets = [
            Target(
                id=str(row["id"]),
                name=row["name"],
                ip_address=str(row["ip_address"]),
                platform=row["platform"],
                os_version=row["os_version"],
                connection_type=row["connection_type"],
                credential_id=row["credential_id"],
                port=row["port"],
                is_active=row["is_active"],
                last_audit=row["last_audit"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

        return targets, total

    @staticmethod
    async def get_by_id(target_id: str) -> Target | None:
        """Get a target by ID."""
        pool = get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, ip_address, platform, os_version, connection_type,
                       credential_id, port, is_active, last_audit, created_at, updated_at
                FROM stig.targets
                WHERE id = $1
                """,
                target_id,
            )

        if not row:
            return None

        return Target(
            id=str(row["id"]),
            name=row["name"],
            ip_address=str(row["ip_address"]),
            platform=row["platform"],
            os_version=row["os_version"],
            connection_type=row["connection_type"],
            credential_id=row["credential_id"],
            port=row["port"],
            is_active=row["is_active"],
            last_audit=row["last_audit"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    async def create(data: TargetCreate) -> Target:
        """Create a new target."""
        pool = get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO stig.targets (name, ip_address, platform, os_version,
                                          connection_type, credential_id, port)
                VALUES ($1, $2::inet, $3, $4, $5, $6, $7)
                RETURNING id, name, ip_address, platform, os_version, connection_type,
                          credential_id, port, is_active, last_audit, created_at, updated_at
                """,
                data.name,
                data.ip_address,
                data.platform.value,
                data.os_version,
                data.connection_type.value,
                data.credential_id,
                data.port,
            )

        logger.info("target_created", target_id=str(row["id"]), name=data.name)

        return Target(
            id=str(row["id"]),
            name=row["name"],
            ip_address=str(row["ip_address"]),
            platform=row["platform"],
            os_version=row["os_version"],
            connection_type=row["connection_type"],
            credential_id=row["credential_id"],
            port=row["port"],
            is_active=row["is_active"],
            last_audit=row["last_audit"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    async def update(target_id: str, data: TargetUpdate) -> Target | None:
        """Update a target."""
        pool = get_pool()

        # Build dynamic update
        updates = []
        params: list[Any] = []
        param_idx = 1

        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                if field == "ip_address":
                    updates.append(f"{field} = ${param_idx}::inet")
                elif field == "platform" or field == "connection_type":
                    updates.append(f"{field} = ${param_idx}")
                    value = value.value if hasattr(value, "value") else value
                else:
                    updates.append(f"{field} = ${param_idx}")
                params.append(value)
                param_idx += 1

        if not updates:
            return await TargetRepository.get_by_id(target_id)

        params.append(target_id)

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                UPDATE stig.targets
                SET {", ".join(updates)}, updated_at = NOW()
                WHERE id = ${param_idx}
                RETURNING id, name, ip_address, platform, os_version, connection_type,
                          credential_id, port, is_active, last_audit, created_at, updated_at
                """,
                *params,
            )

        if not row:
            return None

        logger.info("target_updated", target_id=target_id)

        return Target(
            id=str(row["id"]),
            name=row["name"],
            ip_address=str(row["ip_address"]),
            platform=row["platform"],
            os_version=row["os_version"],
            connection_type=row["connection_type"],
            credential_id=row["credential_id"],
            port=row["port"],
            is_active=row["is_active"],
            last_audit=row["last_audit"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    async def delete(target_id: str) -> bool:
        """Delete a target."""
        pool = get_pool()

        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM stig.targets WHERE id = $1",
                target_id,
            )

        deleted = result == "DELETE 1"
        if deleted:
            logger.info("target_deleted", target_id=target_id)

        return deleted

    @staticmethod
    async def update_last_audit(target_id: str) -> None:
        """Update the last_audit timestamp for a target."""
        pool = get_pool()

        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE stig.targets SET last_audit = NOW() WHERE id = $1",
                target_id,
            )


class DefinitionRepository:
    """Repository for STIG definition operations."""

    @staticmethod
    async def list(
        page: int = 1,
        per_page: int = 20,
        platform: str | None = None,
        search: str | None = None,
    ) -> tuple[list[STIGDefinition], int]:
        """List STIG definitions with pagination."""
        pool = get_pool()

        conditions = []
        params: list[Any] = []
        param_idx = 1

        if platform:
            conditions.append(f"platform = ${param_idx}")
            params.append(platform)
            param_idx += 1

        if search:
            conditions.append(f"(title ILIKE ${param_idx} OR stig_id ILIKE ${param_idx})")
            params.append(f"%{search}%")
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        async with pool.acquire() as conn:
            # Get total count
            count_query = f"SELECT COUNT(*) FROM stig.definitions WHERE {where_clause}"
            total = await conn.fetchval(count_query, *params)

            # Get paginated results
            offset = (page - 1) * per_page
            query = f"""
                SELECT id, stig_id, title, version, release_date, platform,
                       description, xccdf_content, created_at, updated_at,
                       COALESCE(jsonb_array_length(xccdf_content->'rules'), 0) as rules_count
                FROM stig.definitions
                WHERE {where_clause}
                ORDER BY title ASC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([per_page, offset])

            rows = await conn.fetch(query, *params)

        definitions = [
            STIGDefinition(
                id=str(row["id"]),
                stig_id=row["stig_id"],
                title=row["title"],
                version=row["version"],
                release_date=row["release_date"],
                platform=row["platform"],
                description=row["description"],
                rules_count=row["rules_count"] or 0,
                xccdf_content=row["xccdf_content"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

        return definitions, total

    @staticmethod
    async def get_by_id(definition_id: str) -> STIGDefinition | None:
        """Get a STIG definition by ID."""
        pool = get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, stig_id, title, version, release_date, platform,
                       description, xccdf_content, created_at, updated_at,
                       COALESCE(jsonb_array_length(xccdf_content->'rules'), 0) as rules_count
                FROM stig.definitions
                WHERE id = $1
                """,
                definition_id,
            )

        if not row:
            return None

        return STIGDefinition(
            id=str(row["id"]),
            stig_id=row["stig_id"],
            title=row["title"],
            version=row["version"],
            release_date=row["release_date"],
            platform=row["platform"],
            description=row["description"],
            rules_count=row["rules_count"] or 0,
            xccdf_content=row["xccdf_content"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    async def count() -> int:
        """Get total count of definitions."""
        pool = get_pool()

        async with pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM stig.definitions")

    @staticmethod
    async def get_rules(definition_id: str) -> list[dict]:
        """Get STIG rules for a definition from definition_rules table.

        Args:
            definition_id: The definition ID

        Returns:
            List of rule dictionaries with keys:
            vuln_id, rule_id, title, severity, check_text, fix_text
        """
        pool = get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    rule_id,
                    title,
                    severity,
                    description,
                    fix_text,
                    check_text
                FROM stig.definition_rules
                WHERE definition_id = $1
                ORDER BY rule_id
                """,
                definition_id,
            )

        rules = []
        for row in rows:
            rules.append({
                "vuln_id": row["rule_id"],  # Use rule_id as vuln_id
                "rule_id": row["rule_id"],
                "title": row["title"] or "",
                "severity": row["severity"] or "medium",
                "check_text": row["check_text"] or "",
                "fix_text": row["fix_text"] or "",
                "description": row["description"] or "",
            })

        return rules


class AuditJobRepository:
    """Repository for audit job operations."""

    @staticmethod
    async def list(
        page: int = 1,
        per_page: int = 20,
        target_id: str | None = None,
        status: AuditStatus | None = None,
    ) -> tuple[list[AuditJob], int]:
        """List audit jobs with pagination."""
        pool = get_pool()

        conditions = []
        params: list[Any] = []
        param_idx = 1

        if target_id:
            conditions.append(f"target_id = ${param_idx}")
            params.append(target_id)
            param_idx += 1

        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        async with pool.acquire() as conn:
            # Get total count
            count_query = f"SELECT COUNT(*) FROM stig.audit_jobs WHERE {where_clause}"
            total = await conn.fetchval(count_query, *params)

            # Get paginated results
            offset = (page - 1) * per_page
            query = f"""
                SELECT id, name, target_id, definition_id, status, started_at,
                       completed_at, created_by, error_message, created_at, audit_group_id
                FROM stig.audit_jobs
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([per_page, offset])

            rows = await conn.fetch(query, *params)

        jobs = [
            AuditJob(
                id=str(row["id"]),
                name=row["name"],
                target_id=str(row["target_id"]),
                definition_id=str(row["definition_id"]),
                status=AuditStatus(row["status"]),
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                created_by=str(row["created_by"]) if row["created_by"] else None,
                error_message=row["error_message"],
                created_at=row["created_at"],
                audit_group_id=str(row["audit_group_id"]) if row["audit_group_id"] else None,
            )
            for row in rows
        ]

        return jobs, total

    @staticmethod
    async def get_by_id(job_id: str) -> AuditJob | None:
        """Get an audit job by ID."""
        pool = get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, target_id, definition_id, status, started_at,
                       completed_at, created_by, error_message, created_at, audit_group_id
                FROM stig.audit_jobs
                WHERE id = $1
                """,
                job_id,
            )

        if not row:
            return None

        return AuditJob(
            id=str(row["id"]),
            name=row["name"],
            target_id=str(row["target_id"]),
            definition_id=str(row["definition_id"]),
            status=AuditStatus(row["status"]),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            created_by=str(row["created_by"]) if row["created_by"] else None,
            error_message=row["error_message"],
            created_at=row["created_at"],
            audit_group_id=str(row["audit_group_id"]) if row["audit_group_id"] else None,
        )

    @staticmethod
    async def create(data: AuditJobCreate, created_by: str | None = None) -> AuditJob:
        """Create a new audit job."""
        pool = get_pool()

        # Generate name if not provided
        name = data.name
        if not name:
            name = f"Audit-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO stig.audit_jobs (name, target_id, definition_id, created_by, audit_group_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, name, target_id, definition_id, status, started_at,
                          completed_at, created_by, error_message, created_at, audit_group_id
                """,
                name,
                data.target_id,
                data.definition_id,
                created_by,
                data.audit_group_id,
            )

        logger.info("audit_job_created", job_id=str(row["id"]), name=name, audit_group_id=data.audit_group_id)

        return AuditJob(
            id=str(row["id"]),
            name=row["name"],
            target_id=str(row["target_id"]),
            definition_id=str(row["definition_id"]),
            status=AuditStatus(row["status"]),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            created_by=str(row["created_by"]) if row["created_by"] else None,
            error_message=row["error_message"],
            created_at=row["created_at"],
            audit_group_id=str(row["audit_group_id"]) if row["audit_group_id"] else None,
        )

    @staticmethod
    async def update_status(
        job_id: str,
        status: AuditStatus,
        error_message: str | None = None,
    ) -> None:
        """Update audit job status."""
        pool = get_pool()

        async with pool.acquire() as conn:
            if status == AuditStatus.RUNNING:
                await conn.execute(
                    """
                    UPDATE stig.audit_jobs
                    SET status = $2, started_at = NOW()
                    WHERE id = $1
                    """,
                    job_id,
                    status.value,
                )
            elif status in (AuditStatus.COMPLETED, AuditStatus.FAILED, AuditStatus.CANCELLED):
                await conn.execute(
                    """
                    UPDATE stig.audit_jobs
                    SET status = $2, completed_at = NOW(), error_message = $3
                    WHERE id = $1
                    """,
                    job_id,
                    status.value,
                    error_message,
                )
            else:
                await conn.execute(
                    """
                    UPDATE stig.audit_jobs
                    SET status = $2
                    WHERE id = $1
                    """,
                    job_id,
                    status.value,
                )

        logger.info("audit_job_status_updated", job_id=job_id, status=status.value)

    @staticmethod
    async def get_recent(limit: int = 10) -> list[AuditJob]:
        """Get recent audit jobs."""
        pool = get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, target_id, definition_id, status, started_at,
                       completed_at, created_by, error_message, created_at
                FROM stig.audit_jobs
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )

        return [
            AuditJob(
                id=str(row["id"]),
                name=row["name"],
                target_id=str(row["target_id"]),
                definition_id=str(row["definition_id"]),
                status=AuditStatus(row["status"]),
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                created_by=str(row["created_by"]) if row["created_by"] else None,
                error_message=row["error_message"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class AuditResultRepository:
    """Repository for audit result operations."""

    @staticmethod
    async def list_by_job(
        job_id: str,
        page: int = 1,
        per_page: int = 50,
        status: CheckStatus | None = None,
        severity: str | None = None,
    ) -> tuple[list[AuditResult], int]:
        """List audit results for a job."""
        pool = get_pool()

        conditions = ["job_id = $1"]
        params: list[Any] = [job_id]
        param_idx = 2

        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1

        if severity:
            conditions.append(f"severity = ${param_idx}")
            params.append(severity)
            param_idx += 1

        where_clause = " AND ".join(conditions)

        async with pool.acquire() as conn:
            # Get total count
            count_query = f"SELECT COUNT(*) FROM stig.audit_results WHERE {where_clause}"
            total = await conn.fetchval(count_query, *params)

            # Get paginated results
            offset = (page - 1) * per_page
            query = f"""
                SELECT id, job_id, rule_id, title, severity, status,
                       finding_details, comments, checked_at
                FROM stig.audit_results
                WHERE {where_clause}
                ORDER BY
                    CASE severity
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                        ELSE 4
                    END,
                    rule_id ASC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([per_page, offset])

            rows = await conn.fetch(query, *params)

        results = [
            AuditResult(
                id=str(row["id"]),
                job_id=str(row["job_id"]),
                rule_id=row["rule_id"],
                title=row["title"],
                severity=row["severity"],
                status=CheckStatus(row["status"]),
                finding_details=row["finding_details"],
                comments=row["comments"],
                checked_at=row["checked_at"],
            )
            for row in rows
        ]

        return results, total

    @staticmethod
    async def create(data: AuditResultCreate) -> AuditResult:
        """Create an audit result."""
        pool = get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO stig.audit_results (job_id, rule_id, title, severity, status,
                                                finding_details, comments)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, job_id, rule_id, title, severity, status,
                          finding_details, comments, checked_at
                """,
                data.job_id,
                data.rule_id,
                data.title,
                data.severity.value if data.severity else None,
                data.status.value,
                data.finding_details,
                data.comments,
            )

        return AuditResult(
            id=str(row["id"]),
            job_id=str(row["job_id"]),
            rule_id=row["rule_id"],
            title=row["title"],
            severity=row["severity"],
            status=CheckStatus(row["status"]),
            finding_details=row["finding_details"],
            comments=row["comments"],
            checked_at=row["checked_at"],
        )

    @staticmethod
    async def bulk_create(results: list[AuditResultCreate]) -> int:
        """Bulk create audit results."""
        if not results:
            return 0

        pool = get_pool()

        async with pool.acquire() as conn:
            values = [
                (
                    r.job_id,
                    r.rule_id,
                    r.title,
                    r.severity.value if r.severity else None,
                    r.status.value,
                    r.finding_details,
                    r.comments,
                )
                for r in results
            ]

            await conn.executemany(
                """
                INSERT INTO stig.audit_results (job_id, rule_id, title, severity, status,
                                                finding_details, comments)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                values,
            )

        return len(results)

    @staticmethod
    async def get_summary(job_id: str) -> dict[str, int]:
        """Get summary counts for an audit job."""
        pool = get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT status, COUNT(*) as count
                FROM stig.audit_results
                WHERE job_id = $1
                GROUP BY status
                """,
                job_id,
            )

        return {row["status"]: row["count"] for row in rows}

    @staticmethod
    async def get_severity_breakdown(job_id: str) -> dict[str, dict[str, int]]:
        """Get severity breakdown for an audit job."""
        pool = get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT severity, status, COUNT(*) as count
                FROM stig.audit_results
                WHERE job_id = $1 AND severity IS NOT NULL
                GROUP BY severity, status
                """,
                job_id,
            )

        breakdown: dict[str, dict[str, int]] = {
            "high": {"passed": 0, "failed": 0},
            "medium": {"passed": 0, "failed": 0},
            "low": {"passed": 0, "failed": 0},
        }

        for row in rows:
            sev = row["severity"]
            if sev in breakdown:
                if row["status"] == "pass":
                    breakdown[sev]["passed"] = row["count"]
                elif row["status"] == "fail":
                    breakdown[sev]["failed"] = row["count"]

        return breakdown


class TargetDefinitionRepository:
    """Repository for target-STIG assignment operations."""

    @staticmethod
    async def list_by_target(
        target_id: str,
        enabled_only: bool = False,
    ) -> list[TargetDefinitionWithCompliance]:
        """List all STIG definitions assigned to a target with compliance info."""
        pool = get_pool()

        enabled_filter = "AND td.enabled = true" if enabled_only else ""

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT
                    td.id,
                    td.target_id,
                    td.definition_id,
                    td.is_primary,
                    td.enabled,
                    td.notes,
                    td.created_at,
                    td.updated_at,
                    d.stig_id,
                    d.title as stig_title,
                    d.version as stig_version,
                    (SELECT COUNT(*) FROM stig.definition_rules WHERE definition_id = d.id) as rules_count,
                    -- Last audit info
                    (
                        SELECT aj.completed_at
                        FROM stig.audit_jobs aj
                        WHERE aj.target_id = td.target_id
                          AND aj.definition_id = td.definition_id
                          AND aj.status = 'completed'
                        ORDER BY aj.completed_at DESC
                        LIMIT 1
                    ) as last_audit_date,
                    (
                        SELECT aj.status
                        FROM stig.audit_jobs aj
                        WHERE aj.target_id = td.target_id
                          AND aj.definition_id = td.definition_id
                        ORDER BY aj.created_at DESC
                        LIMIT 1
                    ) as last_audit_status,
                    -- Compliance from last completed audit
                    (
                        SELECT
                            CASE WHEN COUNT(*) > 0
                                THEN (COUNT(*) FILTER (WHERE ar.status = 'pass')::float / COUNT(*)::float) * 100
                                ELSE NULL
                            END
                        FROM stig.audit_results ar
                        JOIN stig.audit_jobs aj ON ar.job_id = aj.id
                        WHERE aj.target_id = td.target_id
                          AND aj.definition_id = td.definition_id
                          AND aj.status = 'completed'
                          AND aj.id = (
                              SELECT id FROM stig.audit_jobs
                              WHERE target_id = td.target_id
                                AND definition_id = td.definition_id
                                AND status = 'completed'
                              ORDER BY completed_at DESC LIMIT 1
                          )
                    ) as compliance_score
                FROM stig.target_definitions td
                JOIN stig.definitions d ON td.definition_id = d.id
                WHERE td.target_id = $1 {enabled_filter}
                ORDER BY td.is_primary DESC, d.title ASC
                """,
                target_id,
            )

        return [
            TargetDefinitionWithCompliance(
                id=str(row["id"]),
                target_id=str(row["target_id"]),
                definition_id=str(row["definition_id"]),
                is_primary=row["is_primary"],
                enabled=row["enabled"],
                notes=row["notes"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                stig_id=row["stig_id"],
                stig_title=row["stig_title"],
                stig_version=row["stig_version"],
                rules_count=row["rules_count"],
                last_audit_date=row["last_audit_date"],
                last_audit_status=row["last_audit_status"],
                compliance_score=row["compliance_score"],
            )
            for row in rows
        ]

    @staticmethod
    async def get(target_id: str, definition_id: str) -> TargetDefinition | None:
        """Get a specific target-STIG assignment."""
        pool = get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    td.id, td.target_id, td.definition_id,
                    td.is_primary, td.enabled, td.notes,
                    td.created_at, td.updated_at,
                    d.stig_id, d.title as stig_title, d.version as stig_version,
                    (SELECT COUNT(*) FROM stig.definition_rules WHERE definition_id = d.id) as rules_count
                FROM stig.target_definitions td
                JOIN stig.definitions d ON td.definition_id = d.id
                WHERE td.target_id = $1 AND td.definition_id = $2
                """,
                target_id,
                definition_id,
            )

        if not row:
            return None

        return TargetDefinition(
            id=str(row["id"]),
            target_id=str(row["target_id"]),
            definition_id=str(row["definition_id"]),
            is_primary=row["is_primary"],
            enabled=row["enabled"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            stig_id=row["stig_id"],
            stig_title=row["stig_title"],
            stig_version=row["stig_version"],
            rules_count=row["rules_count"],
        )

    @staticmethod
    async def create(target_id: str, data: TargetDefinitionCreate) -> TargetDefinition:
        """Create a new target-STIG assignment."""
        pool = get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO stig.target_definitions
                    (target_id, definition_id, is_primary, enabled, notes)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, target_id, definition_id, is_primary, enabled, notes, created_at, updated_at
                """,
                target_id,
                data.definition_id,
                data.is_primary,
                data.enabled,
                data.notes,
            )

        return TargetDefinition(
            id=str(row["id"]),
            target_id=str(row["target_id"]),
            definition_id=str(row["definition_id"]),
            is_primary=row["is_primary"],
            enabled=row["enabled"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    async def update(
        target_id: str,
        definition_id: str,
        data: TargetDefinitionUpdate,
    ) -> TargetDefinition | None:
        """Update a target-STIG assignment."""
        pool = get_pool()

        # Build dynamic update
        updates = []
        params: list[Any] = []
        param_idx = 1

        if data.is_primary is not None:
            updates.append(f"is_primary = ${param_idx}")
            params.append(data.is_primary)
            param_idx += 1

        if data.enabled is not None:
            updates.append(f"enabled = ${param_idx}")
            params.append(data.enabled)
            param_idx += 1

        if data.notes is not None:
            updates.append(f"notes = ${param_idx}")
            params.append(data.notes)
            param_idx += 1

        if not updates:
            return await TargetDefinitionRepository.get(target_id, definition_id)

        updates.append("updated_at = NOW()")
        params.extend([target_id, definition_id])

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                UPDATE stig.target_definitions
                SET {", ".join(updates)}
                WHERE target_id = ${param_idx} AND definition_id = ${param_idx + 1}
                RETURNING id, target_id, definition_id, is_primary, enabled, notes, created_at, updated_at
                """,
                *params,
            )

        if not row:
            return None

        return TargetDefinition(
            id=str(row["id"]),
            target_id=str(row["target_id"]),
            definition_id=str(row["definition_id"]),
            is_primary=row["is_primary"],
            enabled=row["enabled"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    async def delete(target_id: str, definition_id: str) -> bool:
        """Remove a target-STIG assignment."""
        pool = get_pool()

        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM stig.target_definitions
                WHERE target_id = $1 AND definition_id = $2
                """,
                target_id,
                definition_id,
            )

        return result == "DELETE 1"

    @staticmethod
    async def bulk_assign(
        target_id: str,
        definition_ids: list[str],
        primary_id: str | None = None,
    ) -> tuple[int, int]:
        """Bulk assign multiple STIGs to a target. Returns (assigned, skipped)."""
        pool = get_pool()
        assigned = 0
        skipped = 0

        async with pool.acquire() as conn:
            for def_id in definition_ids:
                try:
                    is_primary = (def_id == primary_id) if primary_id else False
                    await conn.execute(
                        """
                        INSERT INTO stig.target_definitions
                            (target_id, definition_id, is_primary, enabled)
                        VALUES ($1, $2, $3, true)
                        ON CONFLICT (target_id, definition_id) DO NOTHING
                        """,
                        target_id,
                        def_id,
                        is_primary,
                    )
                    assigned += 1
                except Exception:
                    skipped += 1

        return assigned, skipped


class AuditGroupRepository:
    """Repository for audit group operations."""

    @staticmethod
    async def create(data: AuditGroupCreate, user_id: str | None = None) -> AuditGroup:
        """Create a new audit group."""
        pool = get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO stig.audit_groups (name, target_id, created_by)
                VALUES ($1, $2, $3)
                RETURNING id, name, target_id, status, total_jobs, completed_jobs,
                          created_by, created_at, completed_at
                """,
                data.name,
                data.target_id,
                user_id,
            )

        return AuditGroup(
            id=str(row["id"]),
            name=row["name"],
            target_id=str(row["target_id"]),
            status=AuditStatus(row["status"]),
            total_jobs=row["total_jobs"],
            completed_jobs=row["completed_jobs"],
            created_by=str(row["created_by"]) if row["created_by"] else None,
            created_at=row["created_at"],
            completed_at=row["completed_at"],
        )

    @staticmethod
    async def get_by_id(group_id: str) -> AuditGroup | None:
        """Get an audit group by ID."""
        pool = get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, target_id, status, total_jobs, completed_jobs,
                       created_by, created_at, completed_at
                FROM stig.audit_groups
                WHERE id = $1
                """,
                group_id,
            )

        if not row:
            return None

        return AuditGroup(
            id=str(row["id"]),
            name=row["name"],
            target_id=str(row["target_id"]),
            status=AuditStatus(row["status"]),
            total_jobs=row["total_jobs"],
            completed_jobs=row["completed_jobs"],
            created_by=str(row["created_by"]) if row["created_by"] else None,
            created_at=row["created_at"],
            completed_at=row["completed_at"],
        )

    @staticmethod
    async def get_jobs(group_id: str) -> list[dict]:
        """Get all audit jobs in a group."""
        pool = get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    aj.id, aj.name, aj.status, aj.started_at, aj.completed_at,
                    aj.definition_id, d.stig_id, d.title as stig_title
                FROM stig.audit_jobs aj
                JOIN stig.definitions d ON aj.definition_id = d.id
                WHERE aj.audit_group_id = $1
                ORDER BY d.title
                """,
                group_id,
            )

        return [
            {
                "id": str(row["id"]),
                "name": row["name"],
                "status": row["status"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "definition_id": str(row["definition_id"]),
                "stig_id": row["stig_id"],
                "stig_title": row["stig_title"],
            }
            for row in rows
        ]

    @staticmethod
    async def list_by_target(
        target_id: str,
        limit: int = 10,
    ) -> list[AuditGroup]:
        """List recent audit groups for a target."""
        pool = get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, target_id, status, total_jobs, completed_jobs,
                       created_by, created_at, completed_at
                FROM stig.audit_groups
                WHERE target_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                target_id,
                limit,
            )

        return [
            AuditGroup(
                id=str(row["id"]),
                name=row["name"],
                target_id=str(row["target_id"]),
                status=AuditStatus(row["status"]),
                total_jobs=row["total_jobs"],
                completed_jobs=row["completed_jobs"],
                created_by=str(row["created_by"]) if row["created_by"] else None,
                created_at=row["created_at"],
                completed_at=row["completed_at"],
            )
            for row in rows
        ]
