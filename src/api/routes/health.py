"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check():
    """Readiness check - verify all services are ready."""
    # TODO: Add actual service checks
    return {
        "status": "ready",
        "services": {
            "api": True,
            "database": True,  # Add actual check
            "vector_store": True,  # Add actual check
        },
    }
