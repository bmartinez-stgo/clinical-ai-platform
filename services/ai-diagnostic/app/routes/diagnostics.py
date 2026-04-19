from fastapi import APIRouter, HTTPException

from app.core.engine_client import run_diagnostic_inference
from app.core.schema import DiagnosticRequest, DiagnosticResponse

router = APIRouter(tags=["diagnostics"])


@router.post("/diagnose", response_model=DiagnosticResponse)
def diagnose(payload: DiagnosticRequest) -> DiagnosticResponse:
    try:
        return run_diagnostic_inference(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"diagnostic inference failed: {exc}",
        ) from exc
