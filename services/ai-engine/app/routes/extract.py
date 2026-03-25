import logging

from fastapi import APIRouter, HTTPException, status

from app.core.engine import run_extraction
from app.core.schema import ExtractionInput

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/extract/lab-report")
async def extract_lab_report(payload: ExtractionInput):
    try:
        return run_extraction(payload)
    except Exception as exc:
        logger.exception(
            "extract_lab_report failed",
            extra={
                "document_id": payload.document_id,
                "document_filename": payload.filename,
                "page_count": len(payload.pages),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"failed to extract laboratory report: {exc}",
        ) from exc
