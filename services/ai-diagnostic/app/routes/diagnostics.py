from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.engine_client import request_clinical_inference


router = APIRouter(tags=["diagnostics"])


class DiagnosticRequest(BaseModel):
    patient_context: dict = Field(default_factory=dict)
    observations: list[dict] = Field(default_factory=list)
    request_context: dict = Field(default_factory=dict)


@router.post("/infer")
async def infer_diagnostics(payload: DiagnosticRequest) -> dict:
    try:
        return await request_clinical_inference(payload.model_dump())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"failed to request clinical inference: {exc}",
        ) from exc
