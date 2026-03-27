from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "ai-engine-portal"}


@router.get("/ready")
async def ready() -> dict:
    return {"status": "ready", "service": "ai-engine-portal"}
