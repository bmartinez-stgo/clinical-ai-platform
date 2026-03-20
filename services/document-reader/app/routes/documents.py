from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.lab_service import normalize_lab_document
from app.core.pdf_parser import extract_document_payload

router = APIRouter()
settings = get_settings()


@router.post("/parse")
async def parse_document(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="only application/pdf files are supported",
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
        return extract_document_payload(
            file_bytes=file_bytes,
            filename=file.filename or "document.pdf",
            content_type=file.content_type,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"failed to parse pdf: {exc}",
        ) from exc


@router.post("/labs/parse")
async def parse_laboratory_report(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="only application/pdf files are supported",
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
        document_payload = extract_document_payload(
            file_bytes=file_bytes,
            filename=file.filename or "document.pdf",
            content_type=file.content_type,
        )
        return normalize_lab_document(document_payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"failed to normalize laboratory pdf: {exc}",
        ) from exc
