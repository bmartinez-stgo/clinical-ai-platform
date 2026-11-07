import logging

from fastapi import APIRouter, HTTPException, status

from app.core.engine import run_extraction, run_verification
from app.core.schema import ExtractionInput, VerifyValueInput

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


@router.post("/verify/value")
async def verify_value(payload: VerifyValueInput):
    try:
        return run_verification(payload)
    except Exception as exc:
        logger.exception(
            "verify_value failed",
            extra={
                "document_id": payload.document_id,
                "test_name_raw": payload.test_name_raw,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"failed to verify value: {exc}",
        ) from exc
