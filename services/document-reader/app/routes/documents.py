import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.lab_service import normalize_lab_document
from app.core.pdf_parser import extract_document_payload, extract_image_payload

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}


def build_document_payload(file_bytes: bytes, filename: str, content_type: str) -> dict:
    if content_type == "application/pdf":
        return extract_document_payload(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
        )
    return extract_image_payload(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
    )


@router.post("/parse")
async def parse_document(file: UploadFile = File(...)):
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="only pdf and common image formats are supported",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uploaded file is empty",
        )

    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="uploaded file exceeds the maximum allowed size",
        )

    try:
        logger.info(
            "starting generic document parse",
            extra={
                "document_filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(file_bytes),
            },
        )
        return build_document_payload(
            file_bytes=file_bytes,
            filename=file.filename or "document",
            content_type=file.content_type or "application/pdf",
        )
    except Exception as exc:
        logger.exception(
            "generic document parse failed",
            extra={
                "document_filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(file_bytes),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"failed to parse pdf: {exc}",
        ) from exc


@router.post("/labs/parse")
async def parse_laboratory_report(file: UploadFile = File(...)):
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="only pdf and common image formats are supported",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uploaded file is empty",
        )

    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="uploaded file exceeds the maximum allowed size",
        )

    try:
        logger.info(
            "starting laboratory document normalization",
            extra={
                "document_filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(file_bytes),
                "ocr_backend": settings.ocr_backend,
            },
        )
        document_payload = build_document_payload(
            file_bytes=file_bytes,
            filename=file.filename or "document",
            content_type=file.content_type or "application/pdf",
        )
        logger.info(
            "laboratory document parsed into page payload",
            extra={
                "document_id": document_payload.get("document_id"),
                "document_filename": document_payload.get("filename"),
                "page_count": len(document_payload.get("pages", [])),
                "character_count": document_payload.get("character_count"),
                "ocr_backend": settings.ocr_backend,
            },
        )
        return await normalize_lab_document(document_payload)
    except Exception as exc:
        logger.exception(
            "laboratory document normalization failed",
            extra={
                "document_filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(file_bytes),
                "ocr_backend": settings.ocr_backend,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"failed to normalize laboratory pdf: {exc}",
        ) from exc
