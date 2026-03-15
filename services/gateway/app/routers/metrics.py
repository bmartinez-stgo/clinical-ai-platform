from fastapi import APIRouter

from app.observability import metrics_response

router = APIRouter()


@router.get("/metrics")
async def metrics():
    return metrics_response()
