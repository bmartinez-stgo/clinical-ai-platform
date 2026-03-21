from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/infer", tags=["infer"])


class ClinicalInferenceRequest(BaseModel):
    patient_context: dict = Field(default_factory=dict)
    observations: list[dict] = Field(default_factory=list)
    request_context: dict = Field(default_factory=dict)


@router.post("/clinical")
async def infer_clinical(_: ClinicalInferenceRequest) -> dict:
    raise HTTPException(
        status_code=501,
        detail="clinical inference is not implemented yet",
    )
