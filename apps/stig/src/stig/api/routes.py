"""STIG API routes."""

from typing import Annotated
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form, status
from fastapi.responses import FileResponse

from ..core.auth import get_current_user, require_role, UserContext
from ..core.config import settings
from ..core.logging import get_logger
from ..db.repository import (
    TargetRepository,
    DefinitionRepository,
    AuditJobRepository,
    AuditResultRepository,
    TargetDefinitionRepository,
    AuditGroupRepository,
)
from ..models import (
    Target,
    TargetCreate,
    TargetUpdate,
    STIGDefinition,
    AuditJob,
    AuditJobCreate,
    AuditStatus,
    AuditResult,
    CheckStatus,
    ComplianceSummary,
    Pagination,
    PaginatedResponse,
    APIResponse,
    ReportFormat,
    ReportRequest,
    Platform,
    TargetDefinition,
    TargetDefinitionCreate,
    TargetDefinitionUpdate,
    TargetDefinitionWithCompliance,
    AuditGroup,
    AuditGroupCreate,
    AuditGroupWithJobs,
    AuditGroupSummary,
    BulkAssignmentRequest,
    BulkAssignmentResponse,
)
from ..services import AuditService, ComplianceService, config_checker
from ..collectors.config_analyzer import detect_platform_from_content
from ..library import (
    STIGCatalog,
    STIGLibraryIndexer,
    get_library_indexer,
    initialize_library,
)
from ..reports import ReportGenerator

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/stig", tags=["stig"])

# Report generator instance
report_generator = ReportGenerator()

# Service instances
audit_service = AuditService()
compliance_service = ComplianceService(audit_service)


# =============================================================================
# Target Endpoints
# =============================================================================


@router.get("/targets", response_model=PaginatedResponse[Target])
async def list_targets(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    platform: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> PaginatedResponse[Target]:
    """List STIG targets with pagination and filtering."""
    await get_current_user(request)

    targets, total = await TargetRepository.list(
        page=page,
        per_page=per_page,
        platform=platform,
        is_active=is_active,
        search=search,
    )

    total_pages = (total + per_page - 1) // per_page

    return PaginatedResponse(
        data=targets,
        pagination=Pagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get("/targets/{target_id}", response_model=APIResponse[Target])
async def get_target(
    request: Request,
    target_id: str,
) -> APIResponse[Target]:
    """Get a specific target by ID."""
    await get_current_user(request)

    target = await TargetRepository.get_by_id(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target not found: {target_id}",
        )

    return APIResponse(data=target)


@router.post("/targets", response_model=APIResponse[Target], status_code=status.HTTP_201_CREATED)
@require_role("admin", "operator")
async def create_target(
    request: Request,
    data: TargetCreate,
    user: UserContext = None,
) -> APIResponse[Target]:
    """Create a new STIG target."""
    target = await TargetRepository.create(data)
    logger.info("target_created", target_id=target.id, user=user.username if user else None)
    return APIResponse(data=target)


@router.put("/targets/{target_id}", response_model=APIResponse[Target])
@require_role("admin", "operator")
async def update_target(
    request: Request,
    target_id: str,
    data: TargetUpdate,
    user: UserContext = None,
) -> APIResponse[Target]:
    """Update a STIG target."""
    target = await TargetRepository.update(target_id, data)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target not found: {target_id}",
        )

    logger.info("target_updated", target_id=target_id, user=user.username if user else None)
    return APIResponse(data=target)


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_role("admin")
async def delete_target(
    request: Request,
    target_id: str,
    user: UserContext = None,
) -> None:
    """Delete a STIG target."""
    deleted = await TargetRepository.delete(target_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target not found: {target_id}",
        )

    logger.info("target_deleted", target_id=target_id, user=user.username if user else None)


# =============================================================================
# Target STIG Assignment Endpoints (Multi-STIG Support - STIG-13)
# =============================================================================


@router.get("/targets/{target_id}/definitions", response_model=APIResponse[list[TargetDefinitionWithCompliance]])
async def list_target_definitions(
    request: Request,
    target_id: str,
    enabled_only: bool = False,
) -> APIResponse[list[TargetDefinitionWithCompliance]]:
    """List all STIG definitions assigned to a target.

    Returns STIGs assigned to the target with compliance info from the last audit.

    Args:
        target_id: Target asset ID
        enabled_only: If true, only return enabled STIGs

    Returns:
        List of STIG assignments with compliance scores
    """
    await get_current_user(request)

    # Verify target exists
    target = await TargetRepository.get_by_id(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target not found: {target_id}",
        )

    definitions = await TargetDefinitionRepository.list_by_target(
        target_id=target_id,
        enabled_only=enabled_only,
    )

    return APIResponse(data=definitions)


@router.post("/targets/{target_id}/definitions", response_model=APIResponse[TargetDefinition], status_code=status.HTTP_201_CREATED)
@require_role("admin", "operator")
async def assign_stig_to_target(
    request: Request,
    target_id: str,
    data: TargetDefinitionCreate,
    user: UserContext = None,
) -> APIResponse[TargetDefinition]:
    """Assign a STIG definition to a target.

    Creates an association between a target asset and a STIG definition.

    Args:
        target_id: Target asset ID
        data: Assignment details (definition_id, is_primary, enabled, notes)

    Returns:
        The created assignment
    """
    # Verify target exists
    target = await TargetRepository.get_by_id(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target not found: {target_id}",
        )

    # Verify definition exists
    definition = await DefinitionRepository.get_by_id(data.definition_id)
    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"STIG definition not found: {data.definition_id}",
        )

    # Check for existing assignment
    existing = await TargetDefinitionRepository.get(target_id, data.definition_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"STIG '{definition.title}' is already assigned to this target",
        )

    try:
        assignment = await TargetDefinitionRepository.create(target_id, data)
        logger.info(
            "stig_assigned_to_target",
            target_id=target_id,
            definition_id=data.definition_id,
            is_primary=data.is_primary,
            user=user.username if user else None,
        )
        return APIResponse(data=assignment)
    except Exception as e:
        logger.error("stig_assignment_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assign STIG: {str(e)}",
        )


@router.post("/targets/{target_id}/definitions/bulk", response_model=APIResponse[BulkAssignmentResponse])
@require_role("admin", "operator")
async def bulk_assign_stigs_to_target(
    request: Request,
    target_id: str,
    data: BulkAssignmentRequest,
    user: UserContext = None,
) -> APIResponse[BulkAssignmentResponse]:
    """Bulk assign multiple STIGs to a target.

    Assigns multiple STIG definitions to a target in a single operation.
    Existing assignments are skipped (not overwritten).

    Args:
        target_id: Target asset ID
        data: Bulk assignment request with definition_ids and optional primary_id

    Returns:
        Count of assigned and skipped STIGs
    """
    # Verify target exists
    target = await TargetRepository.get_by_id(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target not found: {target_id}",
        )

    # Verify all definitions exist
    for def_id in data.definition_ids:
        definition = await DefinitionRepository.get_by_id(def_id)
        if not definition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"STIG definition not found: {def_id}",
            )

    assigned, skipped = await TargetDefinitionRepository.bulk_assign(
        target_id=target_id,
        definition_ids=data.definition_ids,
        primary_id=data.primary_id,
    )

    logger.info(
        "bulk_stig_assignment",
        target_id=target_id,
        assigned=assigned,
        skipped=skipped,
        user=user.username if user else None,
    )

    return APIResponse(
        data=BulkAssignmentResponse(
            assigned=assigned,
            skipped=skipped,
            total=len(data.definition_ids),
        )
    )


@router.patch("/targets/{target_id}/definitions/{definition_id}", response_model=APIResponse[TargetDefinition])
@require_role("admin", "operator")
async def update_target_definition(
    request: Request,
    target_id: str,
    definition_id: str,
    data: TargetDefinitionUpdate,
    user: UserContext = None,
) -> APIResponse[TargetDefinition]:
    """Update a target-STIG assignment.

    Modify properties of an existing assignment (is_primary, enabled, notes).

    Args:
        target_id: Target asset ID
        definition_id: STIG definition ID
        data: Fields to update

    Returns:
        The updated assignment
    """
    assignment = await TargetDefinitionRepository.update(target_id, definition_id, data)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment not found for target {target_id} and definition {definition_id}",
        )

    logger.info(
        "target_definition_updated",
        target_id=target_id,
        definition_id=definition_id,
        user=user.username if user else None,
    )

    return APIResponse(data=assignment)


@router.delete("/targets/{target_id}/definitions/{definition_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_role("admin", "operator")
async def remove_stig_from_target(
    request: Request,
    target_id: str,
    definition_id: str,
    user: UserContext = None,
) -> None:
    """Remove a STIG assignment from a target.

    Removes the association between a target and a STIG definition.
    Does not delete audit history for this combination.

    Args:
        target_id: Target asset ID
        definition_id: STIG definition ID to remove
    """
    deleted = await TargetDefinitionRepository.delete(target_id, definition_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment not found for target {target_id} and definition {definition_id}",
        )

    logger.info(
        "stig_removed_from_target",
        target_id=target_id,
        definition_id=definition_id,
        user=user.username if user else None,
    )


# =============================================================================
# Audit All (Batch Audit) Endpoints
# =============================================================================


@router.post("/targets/{target_id}/audit-all", response_model=APIResponse[AuditGroup], status_code=status.HTTP_201_CREATED)
@require_role("admin", "operator")
async def start_audit_all(
    request: Request,
    target_id: str,
    user: UserContext = None,
) -> APIResponse[AuditGroup]:
    """Start audits for all enabled STIGs assigned to a target.

    Creates an audit group and individual audit jobs for each enabled STIG
    assigned to the target. Jobs are started asynchronously.

    Args:
        target_id: Target asset ID

    Returns:
        The created audit group
    """
    # Verify target exists
    target = await TargetRepository.get_by_id(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target not found: {target_id}",
        )

    # Get enabled STIGs for this target
    definitions = await TargetDefinitionRepository.list_by_target(
        target_id=target_id,
        enabled_only=True,
    )

    if not definitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No enabled STIG definitions assigned to this target. Assign at least one STIG first.",
        )

    # Create audit group
    from datetime import datetime
    group_name = f"Audit All - {target.name} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    group_data = AuditGroupCreate(name=group_name, target_id=target_id)
    group = await AuditGroupRepository.create(group_data, user.id if user else None)

    # Create individual audit jobs for each STIG
    jobs_created = 0
    for td in definitions:
        try:
            job = await audit_service.start_audit(
                target_id=target_id,
                definition_id=td.definition_id,
                name=f"{td.stig_title} - {target.name}",
                created_by=user.id if user else None,
                audit_group_id=group.id,
            )
            jobs_created += 1
        except Exception as e:
            logger.error(
                "audit_job_creation_failed",
                group_id=group.id,
                definition_id=td.definition_id,
                error=str(e),
            )

    logger.info(
        "audit_all_started",
        target_id=target_id,
        group_id=group.id,
        jobs_created=jobs_created,
        user=user.username if user else None,
    )

    # Refresh group to get updated job counts
    group = await AuditGroupRepository.get_by_id(group.id)

    return APIResponse(data=group)


@router.get("/audit-groups", response_model=APIResponse[list[AuditGroup]])
async def list_audit_groups(
    request: Request,
    target_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> APIResponse[list[AuditGroup]]:
    """List audit groups.

    Args:
        target_id: Filter by target (optional)
        limit: Maximum number of groups to return

    Returns:
        List of audit groups
    """
    await get_current_user(request)

    if target_id:
        groups = await AuditGroupRepository.list_by_target(target_id, limit)
    else:
        # List all groups (TODO: add pagination)
        from ..db.connection import get_pool
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, target_id, status, total_jobs, completed_jobs,
                       created_by, created_at, completed_at
                FROM stig.audit_groups
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )
        groups = [
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

    return APIResponse(data=groups)


@router.get("/audit-groups/{group_id}", response_model=APIResponse[AuditGroupWithJobs])
async def get_audit_group(
    request: Request,
    group_id: str,
) -> APIResponse[AuditGroupWithJobs]:
    """Get an audit group with its jobs.

    Args:
        group_id: Audit group ID

    Returns:
        Audit group with list of jobs
    """
    await get_current_user(request)

    group = await AuditGroupRepository.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit group not found: {group_id}",
        )

    jobs = await AuditGroupRepository.get_jobs(group_id)

    return APIResponse(
        data=AuditGroupWithJobs(
            id=group.id,
            name=group.name,
            target_id=group.target_id,
            status=group.status,
            total_jobs=group.total_jobs,
            completed_jobs=group.completed_jobs,
            created_by=group.created_by,
            created_at=group.created_at,
            completed_at=group.completed_at,
            jobs=jobs,
        )
    )


@router.get("/audit-groups/{group_id}/summary", response_model=APIResponse[AuditGroupSummary])
async def get_audit_group_summary(
    request: Request,
    group_id: str,
) -> APIResponse[AuditGroupSummary]:
    """Get compliance summary for an audit group.

    Aggregates compliance data across all completed audits in the group.

    Args:
        group_id: Audit group ID

    Returns:
        Aggregated compliance summary
    """
    await get_current_user(request)

    group = await AuditGroupRepository.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit group not found: {group_id}",
        )

    jobs = await AuditGroupRepository.get_jobs(group_id)

    # Get target info
    target = await TargetRepository.get_by_id(group.target_id)

    # Aggregate compliance across all completed jobs
    total_checks = 0
    total_passed = 0
    total_failed = 0
    total_not_applicable = 0
    total_not_reviewed = 0
    stig_summaries = []

    for job in jobs:
        if job["status"] == "completed":
            summary = await audit_service.get_compliance_summary(job["id"])
            if summary:
                total_checks += summary.total_checks
                total_passed += summary.passed
                total_failed += summary.failed
                total_not_applicable += summary.not_applicable
                total_not_reviewed += summary.not_reviewed

                stig_summaries.append({
                    "stig_id": job["stig_id"],
                    "stig_title": job["stig_title"],
                    "compliance_score": summary.compliance_score,
                    "total_checks": summary.total_checks,
                    "passed": summary.passed,
                    "failed": summary.failed,
                })

    # Calculate overall compliance
    overall_score = 0.0
    if (total_passed + total_failed) > 0:
        overall_score = (total_passed / (total_passed + total_failed)) * 100

    return APIResponse(
        data=AuditGroupSummary(
            group_id=group.id,
            group_name=group.name,
            target_id=group.target_id,
            target_name=target.name if target else "Unknown",
            status=group.status,
            total_stigs=len(jobs),
            completed_stigs=sum(1 for j in jobs if j["status"] == "completed"),
            overall_compliance_score=round(overall_score, 2),
            total_checks=total_checks,
            passed=total_passed,
            failed=total_failed,
            not_applicable=total_not_applicable,
            not_reviewed=total_not_reviewed,
            stig_summaries=stig_summaries,
        )
    )


# =============================================================================
# Definition Endpoints
# =============================================================================


@router.get("/definitions", response_model=PaginatedResponse[STIGDefinition])
async def list_definitions(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    platform: str | None = None,
    search: str | None = None,
) -> PaginatedResponse[STIGDefinition]:
    """List STIG definitions with pagination."""
    await get_current_user(request)

    definitions, total = await DefinitionRepository.list(
        page=page,
        per_page=per_page,
        platform=platform,
        search=search,
    )

    total_pages = (total + per_page - 1) // per_page

    return PaginatedResponse(
        data=definitions,
        pagination=Pagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get("/definitions/{definition_id}", response_model=APIResponse[STIGDefinition])
async def get_definition(
    request: Request,
    definition_id: str,
) -> APIResponse[STIGDefinition]:
    """Get a specific STIG definition by ID."""
    await get_current_user(request)

    definition = await DefinitionRepository.get_by_id(definition_id)
    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Definition not found: {definition_id}",
        )

    return APIResponse(data=definition)


# =============================================================================
# Audit Endpoints
# =============================================================================


@router.get("/audits", response_model=PaginatedResponse[AuditJob])
async def list_audits(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    target_id: str | None = None,
    status_filter: AuditStatus | None = Query(None, alias="status"),
) -> PaginatedResponse[AuditJob]:
    """List audit jobs with pagination."""
    await get_current_user(request)

    jobs, total = await audit_service.list_jobs(
        page=page,
        per_page=per_page,
        target_id=target_id,
        status=status_filter,
    )

    total_pages = (total + per_page - 1) // per_page

    return PaginatedResponse(
        data=jobs,
        pagination=Pagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.post("/audits", response_model=APIResponse[AuditJob], status_code=status.HTTP_201_CREATED)
@require_role("admin", "operator")
async def start_audit(
    request: Request,
    data: AuditJobCreate,
    user: UserContext = None,
) -> APIResponse[AuditJob]:
    """Start a new STIG audit."""
    try:
        job = await audit_service.start_audit(
            target_id=data.target_id,
            definition_id=data.definition_id,
            name=data.name,
            created_by=user.id if user else None,
            audit_group_id=data.audit_group_id,
        )
        return APIResponse(data=job)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/audits/{job_id}", response_model=APIResponse[AuditJob])
async def get_audit(
    request: Request,
    job_id: str,
) -> APIResponse[AuditJob]:
    """Get a specific audit job by ID."""
    await get_current_user(request)

    job = await audit_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit job not found: {job_id}",
        )

    return APIResponse(data=job)


@router.post("/audits/{job_id}/cancel", response_model=APIResponse[AuditJob])
@require_role("admin", "operator")
async def cancel_audit(
    request: Request,
    job_id: str,
    user: UserContext = None,
) -> APIResponse[AuditJob]:
    """Cancel a running audit job."""
    cancelled = await audit_service.cancel_audit(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel job (not found or not cancellable)",
        )

    job = await audit_service.get_job(job_id)
    logger.info("audit_cancelled", job_id=job_id, user=user.username if user else None)
    return APIResponse(data=job)


@router.get("/audits/{job_id}/results", response_model=PaginatedResponse[AuditResult])
async def get_audit_results(
    request: Request,
    job_id: str,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 50,
    status_filter: CheckStatus | None = Query(None, alias="status"),
    severity: str | None = None,
) -> PaginatedResponse[AuditResult]:
    """Get results for an audit job."""
    await get_current_user(request)

    results, total = await audit_service.get_job_results(
        job_id=job_id,
        page=page,
        per_page=per_page,
        status=status_filter,
        severity=severity,
    )

    total_pages = (total + per_page - 1) // per_page

    return PaginatedResponse(
        data=results,
        pagination=Pagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get("/audits/{job_id}/summary", response_model=APIResponse[ComplianceSummary])
async def get_audit_summary(
    request: Request,
    job_id: str,
) -> APIResponse[ComplianceSummary]:
    """Get compliance summary for an audit job."""
    await get_current_user(request)

    summary = await audit_service.get_compliance_summary(job_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit job not found: {job_id}",
        )

    return APIResponse(data=summary)


# =============================================================================
# Report Endpoints
# =============================================================================


@router.post("/reports/generate")
@require_role("admin", "operator")
async def generate_report(
    request: Request,
    data: ReportRequest,
    user: UserContext = None,
) -> APIResponse[dict]:
    """Generate a report for an audit job.

    Returns a download URL for the generated report.
    """
    job = await audit_service.get_job(data.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit job not found: {data.job_id}",
        )

    if job.status != AuditStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only generate reports for completed audits",
        )

    try:
        # Generate the report
        report_path = await report_generator.generate(
            job_id=data.job_id,
            format=data.format,
            include_details=True,
            include_remediation=True,
        )

        logger.info(
            "report_generated",
            job_id=data.job_id,
            format=data.format.value,
            path=str(report_path),
            user=user.username if user else None,
        )

        # Return download URL
        return APIResponse(
            data={
                "status": "completed",
                "job_id": data.job_id,
                "format": data.format.value,
                "download_url": f"/api/v1/stig/reports/download/{data.job_id}?format={data.format.value}",
                "filename": report_path.name,
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("report_generation_failed", job_id=data.job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


@router.get("/reports/download/{job_id}")
async def download_report(
    request: Request,
    job_id: str,
    format: str = Query(default="pdf", description="Report format: pdf, ckl, json"),
) -> FileResponse:
    """Download a generated report.

    Args:
        job_id: ID of the audit job
        format: Report format (pdf, ckl, json)

    Returns:
        The report file as a download
    """
    await get_current_user(request)

    # Map format string to enum
    format_map = {
        "pdf": ReportFormat.PDF,
        "ckl": ReportFormat.CKL,
        "json": ReportFormat.JSON,
    }
    report_format = format_map.get(format.lower())
    if not report_format:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format: {format}. Supported: pdf, ckl, json",
        )

    # Determine file extension
    ext_map = {
        ReportFormat.PDF: ".pdf",
        ReportFormat.CKL: ".ckl",
        ReportFormat.JSON: ".json",
    }
    ext = ext_map[report_format]

    # Check if report exists, generate if not
    report_path = report_generator.output_dir / f"{job_id}{ext}"

    if not report_path.exists():
        # Generate the report
        try:
            report_path = await report_generator.generate(
                job_id=job_id,
                format=report_format,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except Exception as e:
            logger.error("report_generation_failed", job_id=job_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {str(e)}",
            )

    # Get job info for filename
    job = await audit_service.get_job(job_id)
    target = await TargetRepository.get_by_id(job.target_id) if job else None

    # Build download filename
    if target:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in target.name)
        filename = f"{safe_name}_STIG_Report{ext}"
    else:
        filename = f"STIG_Report_{job_id[:8]}{ext}"

    # Content type mapping
    media_types = {
        ReportFormat.PDF: "application/pdf",
        ReportFormat.CKL: "application/xml",
        ReportFormat.JSON: "application/json",
    }

    logger.info("report_downloaded", job_id=job_id, format=format, filename=filename)

    return FileResponse(
        path=report_path,
        filename=filename,
        media_type=media_types[report_format],
    )


# =============================================================================
# Combined Reports from Multiple Job IDs
# =============================================================================


@router.get("/reports/combined-pdf")
async def download_combined_pdf_from_jobs(
    request: Request,
    job_ids: str = Query(..., description="Comma-separated list of job IDs"),
) -> FileResponse:
    """Download a combined PDF report from multiple audit jobs.

    This creates a single PDF with separate sections for each STIG,
    useful when analyzing a config against multiple STIGs.

    Args:
        job_ids: Comma-separated list of audit job IDs

    Returns:
        The combined PDF report as a download
    """
    await get_current_user(request)

    job_id_list = [jid.strip() for jid in job_ids.split(",") if jid.strip()]
    if not job_id_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No job IDs provided",
        )

    # Generate combined report
    try:
        report_path = await report_generator.generate_combined_pdf_from_jobs(job_id_list)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("combined_pdf_generation_failed", job_ids=job_id_list, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )

    # Get target info from first job for filename
    first_job = await audit_service.get_job(job_id_list[0])
    target = await TargetRepository.get_by_id(first_job.target_id) if first_job else None

    if target:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in target.name)
        filename = f"{safe_name}_Combined_STIG_Report.pdf"
    else:
        filename = "Combined_STIG_Report.pdf"

    logger.info("combined_pdf_from_jobs_downloaded", job_count=len(job_id_list), filename=filename)

    return FileResponse(
        path=report_path,
        filename=filename,
        media_type="application/pdf",
    )


@router.get("/reports/combined-ckl")
async def download_combined_ckl_from_jobs(
    request: Request,
    job_ids: str = Query(..., description="Comma-separated list of job IDs"),
) -> FileResponse:
    """Download a ZIP file containing CKL checklists from multiple audit jobs.

    Args:
        job_ids: Comma-separated list of audit job IDs

    Returns:
        A ZIP file containing individual CKL files for each job
    """
    await get_current_user(request)

    job_id_list = [jid.strip() for jid in job_ids.split(",") if jid.strip()]
    if not job_id_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No job IDs provided",
        )

    # Generate combined CKL ZIP
    try:
        report_path = await report_generator.generate_combined_ckl_from_jobs(job_id_list)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("combined_ckl_generation_failed", job_ids=job_id_list, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CKL generation failed: {str(e)}",
        )

    # Get target info from first job for filename
    first_job = await audit_service.get_job(job_id_list[0])
    target = await TargetRepository.get_by_id(first_job.target_id) if first_job else None

    if target:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in target.name)
        filename = f"{safe_name}_STIG_Checklists.zip"
    else:
        filename = "STIG_Checklists.zip"

    logger.info("combined_ckl_from_jobs_downloaded", job_count=len(job_id_list), filename=filename)

    return FileResponse(
        path=report_path,
        filename=filename,
        media_type="application/zip",
    )


# =============================================================================
# Combined Reports for Audit Groups (STIG-13)
# =============================================================================


@router.get("/audit-groups/{group_id}/report/pdf")
async def download_combined_pdf(
    request: Request,
    group_id: str,
) -> FileResponse:
    """Download a combined PDF report for an audit group.

    Args:
        group_id: ID of the audit group

    Returns:
        The combined PDF report as a download
    """
    await get_current_user(request)

    # Check if report exists, generate if not
    report_path = report_generator.output_dir / f"combined_{group_id}.pdf"

    if not report_path.exists():
        try:
            report_path = await report_generator.generate_combined_pdf(group_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except Exception as e:
            logger.error("combined_pdf_generation_failed", group_id=group_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {str(e)}",
            )

    # Get group info for filename
    from ..db.repository import AuditGroupRepository
    group = await AuditGroupRepository.get_by_id(group_id)
    target = await TargetRepository.get_by_id(group.target_id) if group else None

    # Build download filename
    if target:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in target.name)
        filename = f"{safe_name}_Combined_STIG_Report.pdf"
    else:
        filename = f"Combined_STIG_Report_{group_id[:8]}.pdf"

    logger.info("combined_pdf_downloaded", group_id=group_id, filename=filename)

    return FileResponse(
        path=report_path,
        filename=filename,
        media_type="application/pdf",
    )


@router.get("/audit-groups/{group_id}/report/ckl")
async def download_combined_ckl(
    request: Request,
    group_id: str,
) -> FileResponse:
    """Download a ZIP file containing CKL checklists for an audit group.

    Args:
        group_id: ID of the audit group

    Returns:
        A ZIP file containing individual CKL files for each STIG
    """
    await get_current_user(request)

    # Check if ZIP exists, generate if not
    report_path = report_generator.output_dir / f"checklists_{group_id}.zip"

    if not report_path.exists():
        try:
            report_path = await report_generator.generate_combined_ckl_zip(group_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except Exception as e:
            logger.error("combined_ckl_generation_failed", group_id=group_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"CKL generation failed: {str(e)}",
            )

    # Get group info for filename
    from ..db.repository import AuditGroupRepository
    group = await AuditGroupRepository.get_by_id(group_id)
    target = await TargetRepository.get_by_id(group.target_id) if group else None

    # Build download filename
    if target:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in target.name)
        filename = f"{safe_name}_STIG_Checklists.zip"
    else:
        filename = f"STIG_Checklists_{group_id[:8]}.zip"

    logger.info("combined_ckl_downloaded", group_id=group_id, filename=filename)

    return FileResponse(
        path=report_path,
        filename=filename,
        media_type="application/zip",
    )


# =============================================================================
# Dashboard/Compliance Endpoints
# =============================================================================


@router.get("/dashboard")
async def get_dashboard(
    request: Request,
) -> APIResponse[dict]:
    """Get STIG Manager dashboard data."""
    await get_current_user(request)

    dashboard = await compliance_service.get_dashboard()

    return APIResponse(data=dashboard.model_dump())


@router.get("/compliance/summary")
async def get_compliance_summary(
    request: Request,
) -> APIResponse[dict]:
    """Get overall compliance summary across all targets."""
    await get_current_user(request)

    summary = await compliance_service.get_compliance_summary_for_all_targets()

    return APIResponse(data=summary)


# =============================================================================
# Configuration File Analysis Endpoints
# =============================================================================


@router.post("/targets/{target_id}/analyze-config", response_model=APIResponse[dict])
@require_role("admin", "operator")
async def analyze_target_config(
    request: Request,
    target_id: str,
    definition_id: Annotated[str, Form()],
    config_file: UploadFile = File(...),
    user: UserContext = None,
) -> APIResponse[dict]:
    """Analyze a configuration file against a STIG for a target.

    Upload a device configuration file (.txt or .xml) to check compliance
    against the specified STIG definition. This creates an audit job and
    returns the results.

    Args:
        target_id: ID of the target asset
        definition_id: ID of the STIG definition to check against
        config_file: The configuration file to analyze

    Returns:
        Audit job with compliance results
    """
    # Verify target exists
    target = await TargetRepository.get_by_id(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target not found: {target_id}",
        )

    # Verify definition exists
    definition = await DefinitionRepository.get_by_id(definition_id)
    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Definition not found: {definition_id}",
        )

    # --- SEC-017: Validate file before reading ---
    filename = config_file.filename or ""
    valid_extensions = [
        ext.strip() for ext in settings.allowed_config_extensions.split(",") if ext.strip()
    ]
    if not any(filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Supported: {', '.join(valid_extensions)}",
        )

    # SEC-017: Read with size limit — prevents memory exhaustion
    content = await config_file.read()
    if len(content) > settings.max_config_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Configuration file exceeds maximum size "
                   f"({len(content)} bytes > {settings.max_config_upload_size} bytes). "
                   f"Max: {settings.max_config_upload_size // (1024 * 1024)}MB.",
        )

    try:
        config_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration file must be UTF-8 encoded text",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read configuration file: {str(e)}",
        )

    # Create audit job
    job_data = AuditJobCreate(
        name=f"Config Analysis: {target.name} - {filename}",
        target_id=target_id,
        definition_id=definition_id,
    )
    job = await AuditJobRepository.create(job_data, user.id if user else None)

    try:
        # Update job status
        await AuditJobRepository.update_status(job.id, AuditStatus.RUNNING)

        # Load rules from database for this definition
        db_rules = await DefinitionRepository.get_rules(definition_id)
        logger.info(
            "loaded_definition_rules",
            definition_id=definition_id,
            rule_count=len(db_rules),
        )

        # Analyze configuration
        results = await config_checker.analyze_config(
            content=config_content,
            platform=target.platform,
            definition=definition,
            job_id=job.id,
            db_rules=db_rules if db_rules else None,
        )

        # Save results
        if results:
            await AuditResultRepository.bulk_create(results)

        # Update target last audit
        await TargetRepository.update_last_audit(target.id)

        # Complete job
        await AuditJobRepository.update_status(job.id, AuditStatus.COMPLETED)

        # Get summary
        summary = await audit_service.get_compliance_summary(job.id)

        logger.info(
            "config_analysis_completed",
            target_id=target_id,
            job_id=job.id,
            total_checks=len(results),
            user=user.username if user else None,
        )

        return APIResponse(
            data={
                "job_id": job.id,
                "target_id": target_id,
                "definition_id": definition_id,
                "filename": filename,
                "total_checks": len(results),
                "summary": summary.model_dump() if summary else None,
            }
        )

    except Exception as e:
        logger.error("config_analysis_failed", job_id=job.id, error=str(e))
        await AuditJobRepository.update_status(job.id, AuditStatus.FAILED, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration analysis failed: {str(e)}",
        )


@router.post("/analyze-config", response_model=APIResponse[dict])
@require_role("admin", "operator")
async def analyze_config_standalone(
    request: Request,
    config_file: UploadFile = File(...),
    platform: Annotated[str | None, Form()] = None,
    user: UserContext = None,
) -> APIResponse[dict]:
    """Analyze a configuration file without a pre-existing target.

    Upload a device configuration file to check compliance. The platform
    can be auto-detected or specified explicitly.

    Args:
        config_file: The configuration file to analyze
        platform: Optional platform (auto-detected if not specified)

    Returns:
        Compliance analysis results
    """
    # --- SEC-017: Validate file extension ---
    filename = config_file.filename or ""
    valid_extensions = [
        ext.strip() for ext in settings.allowed_config_extensions.split(",") if ext.strip()
    ]
    if not any(filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Supported: {', '.join(valid_extensions)}",
        )

    # SEC-017: Read with size limit
    content = await config_file.read()
    if len(content) > settings.max_config_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Configuration file exceeds maximum size "
                   f"({len(content)} bytes > {settings.max_config_upload_size} bytes). "
                   f"Max: {settings.max_config_upload_size // (1024 * 1024)}MB.",
        )

    try:
        config_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration file must be UTF-8 encoded text",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read configuration file: {str(e)}",
        )

    # Determine platform
    detected_platform: Platform | None = None
    if platform:
        try:
            detected_platform = Platform(platform)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}. Valid options: {[p.value for p in Platform]}",
            )
    else:
        detected_platform = detect_platform_from_content(config_content)
        if not detected_platform:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not auto-detect platform. Please specify the platform parameter.",
            )

    # Analyze configuration
    results = await config_checker.analyze_config(
        content=config_content,
        platform=detected_platform,
        definition=None,
        job_id="standalone",
    )

    # Calculate summary
    total = len(results)
    passed = sum(1 for r in results if r.status == CheckStatus.PASS)
    failed = sum(1 for r in results if r.status == CheckStatus.FAIL)
    not_reviewed = sum(1 for r in results if r.status == CheckStatus.NOT_REVIEWED)
    errors = sum(1 for r in results if r.status == CheckStatus.ERROR)

    compliance_score = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0

    logger.info(
        "standalone_config_analysis_completed",
        platform=detected_platform.value,
        total_checks=total,
        user=user.username if user else None,
    )

    return APIResponse(
        data={
            "platform": detected_platform.value,
            "filename": config_file.filename,
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "not_reviewed": not_reviewed,
            "errors": errors,
            "compliance_score": round(compliance_score, 2),
            "results": [
                {
                    "rule_id": r.rule_id,
                    "title": r.title,
                    "severity": r.severity.value,
                    "status": r.status.value,
                    "finding_details": r.finding_details,
                }
                for r in results
            ],
        }
    )


# =============================================================================
# STIG Library Endpoints
# =============================================================================


@router.get("/library")
async def get_library_catalog(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 50,
    platform: str | None = None,
    stig_type: str | None = None,
    search: str | None = None,
) -> APIResponse[dict]:
    """Get STIG Library catalog with pagination and filtering.

    Browse the available STIG definitions in the library. Filter by platform,
    type (stig/srg), or search by title/ID.

    Args:
        page: Page number (starts at 1)
        per_page: Items per page (max 100)
        platform: Filter by platform (e.g., "arista_eos", "cisco_ios")
        stig_type: Filter by type ("stig" or "srg")
        search: Search term for title or benchmark ID

    Returns:
        Paginated list of STIG entries from the library
    """
    await get_current_user(request)

    indexer = get_library_indexer()
    if not indexer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STIG Library not initialized. Configure STIG_LIBRARY_PATH.",
        )

    # Build filter
    from ..library.catalog import STIGType

    platform_filter = None
    if platform:
        try:
            platform_filter = Platform(platform)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}",
            )

    type_filter = None
    if stig_type:
        try:
            type_filter = STIGType(stig_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stig_type: {stig_type}. Valid: stig, srg",
            )

    # Search catalog
    entries = indexer.catalog.search(
        query=search or "",
        platform=platform_filter,
        stig_type=type_filter,
    )

    # Sort by title
    entries.sort(key=lambda e: e.title)

    # Paginate
    total = len(entries)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_entries = entries[start:end]

    return APIResponse(
        data={
            "entries": [e.to_dict() for e in paginated_entries],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
            },
        }
    )


@router.get("/library/summary")
async def get_library_summary(
    request: Request,
) -> APIResponse[dict]:
    """Get STIG Library summary statistics.

    Returns:
        Library summary with counts by platform and type
    """
    await get_current_user(request)

    indexer = get_library_indexer()
    if not indexer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STIG Library not initialized. Configure STIG_LIBRARY_PATH.",
        )

    summary = indexer.summary()
    return APIResponse(data=summary)


@router.get("/library/platforms/{platform_value}")
async def get_stigs_for_platform(
    request: Request,
    platform_value: str,
) -> APIResponse[dict]:
    """Get all STIGs applicable to a specific platform.

    Args:
        platform_value: Platform identifier (e.g., "arista_eos", "cisco_ios")

    Returns:
        List of applicable STIG entries
    """
    await get_current_user(request)

    indexer = get_library_indexer()
    if not indexer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STIG Library not initialized.",
        )

    try:
        platform = Platform(platform_value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {platform_value}. Valid: {[p.value for p in Platform]}",
        )

    entries = indexer.catalog.get_by_platform(platform)

    # Also get the latest/recommended one
    latest = indexer.catalog.get_latest_for_platform(platform)

    return APIResponse(
        data={
            "platform": platform_value,
            "entries": [e.to_dict() for e in entries],
            "recommended": latest.to_dict() if latest else None,
            "total": len(entries),
        }
    )


@router.get("/library/{benchmark_id}")
async def get_library_entry(
    request: Request,
    benchmark_id: str,
) -> APIResponse[dict]:
    """Get a specific STIG entry from the library.

    Args:
        benchmark_id: STIG benchmark ID (e.g., "RHEL_9_STIG")

    Returns:
        STIG entry details
    """
    await get_current_user(request)

    indexer = get_library_indexer()
    if not indexer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STIG Library not initialized.",
        )

    entry = indexer.catalog.get_entry(benchmark_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"STIG not found: {benchmark_id}",
        )

    return APIResponse(data=entry.to_dict())


@router.get("/library/{benchmark_id}/rules")
async def get_library_rules(
    request: Request,
    benchmark_id: str,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=200)] = 50,
    severity: str | None = None,
    search: str | None = None,
) -> APIResponse[dict]:
    """Get rules for a specific STIG from the library.

    This loads the full XCCDF content on demand. Supports pagination
    and filtering by severity or search term.

    Args:
        benchmark_id: STIG benchmark ID
        page: Page number
        per_page: Rules per page
        severity: Filter by severity (high, medium, low)
        search: Search term for rule title/ID

    Returns:
        Paginated list of STIG rules
    """
    await get_current_user(request)

    indexer = get_library_indexer()
    if not indexer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STIG Library not initialized.",
        )

    entry = indexer.catalog.get_entry(benchmark_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"STIG not found: {benchmark_id}",
        )

    # Load rules (cached if previously loaded)
    rules = indexer.get_rules(benchmark_id)

    # Filter by severity
    if severity:
        rules = [r for r in rules if r.severity == severity.lower()]

    # Filter by search
    if search:
        search_lower = search.lower()
        rules = [
            r
            for r in rules
            if search_lower in r.title.lower()
            or search_lower in r.vuln_id.lower()
            or search_lower in r.rule_id.lower()
        ]

    # Paginate
    total = len(rules)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_rules = rules[start:end]

    return APIResponse(
        data={
            "benchmark_id": benchmark_id,
            "rules": [r.to_dict() for r in paginated_rules],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
            },
        }
    )


@router.post("/library/rescan")
@require_role("admin")
async def rescan_library(
    request: Request,
    user: UserContext = None,
) -> APIResponse[dict]:
    """Rescan the STIG Library folder and rebuild the index.

    Admin only. Use this after adding new STIG ZIP files to the library folder.

    Returns:
        Scan statistics
    """
    indexer = get_library_indexer()
    if not indexer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STIG Library not initialized. Configure STIG_LIBRARY_PATH.",
        )

    logger.info("library_rescan_started", user=user.username if user else None)

    # Force rescan
    indexer.get_or_scan(force_rescan=True)

    summary = indexer.summary()

    logger.info(
        "library_rescan_completed",
        total_entries=summary["total_entries"],
        user=user.username if user else None,
    )

    return APIResponse(
        data={
            "status": "completed",
            "summary": summary,
        }
    )
