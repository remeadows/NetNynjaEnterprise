"""Health check endpoints — delegates to shared_python.create_health_router."""

from shared_python import create_health_router

from ..db.connection import check_health as check_db_health

health_router = create_health_router(
    service_name="ipam",
    checks={"database": check_db_health},
)
