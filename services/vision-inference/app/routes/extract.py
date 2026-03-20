from fastapi import APIRouter, HTTPException, status

from app.core.engine import run_extraction
from app.core.schema import ExtractionInput

router = APIRouter()


@router.post("/extract/lab-report")
async def extract_lab_report(payload: ExtractionInput):
    try:
        return run_extraction(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"failed to extract laboratory report: {exc}",
        ) from exc
