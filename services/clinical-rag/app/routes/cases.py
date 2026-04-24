from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.core import embedder, store
from app.core.schema import (
    SimilarCase,
    SimilarCasesRequest,
    SimilarCasesResponse,
    StoreCaseRequest,
    StoreCaseResponse,
)

router = APIRouter(prefix="/cases", tags=["cases"])
logger = logging.getLogger(__name__)


@router.post("", response_model=StoreCaseResponse, status_code=201)
def store_case(req: StoreCaseRequest) -> StoreCaseResponse:
    case_id = req.case_id or str(uuid.uuid4())
    text = embedder.case_text(
        req.patient.age,
        req.patient.sex,
        req.lab_snapshot.results,
        req.doctor_notes or "",
    )
    embedding = embedder.embed(text)

    metadata = {
        "patient_age": req.patient.age,
        "patient_sex": req.patient.sex,
        "patient_ethnicity": req.patient.ethnicity or "",
        "report_date": req.lab_snapshot.report_date,
        "validated_diagnosis": req.validated_diagnosis,
        "differential": json.dumps(req.differential, ensure_ascii=False),
        "doctor_notes": req.doctor_notes or "",
        "approved_by": req.approved_by or "",
    }

    store.upsert(case_id, embedding, metadata, text)
    total = store.count()
    logger.info("stored case %s, total=%d", case_id, total)
    return StoreCaseResponse(case_id=case_id, stored=True, total_cases=total)


@router.post("/similar", response_model=SimilarCasesResponse)
def find_similar(req: SimilarCasesRequest) -> SimilarCasesResponse:
    text = embedder.case_text(req.patient.age, req.patient.sex, req.lab_results)
    embedding = embedder.embed(text)
    results, total = store.query(embedding, req.top_k)

    if not results:
        return SimilarCasesResponse(cases=[], total_cases_in_store=total)

    cases: list[SimilarCase] = []
    for i, cid in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i]
        similarity = round(1.0 - results["distances"][0][i], 3)
        cases.append(
            SimilarCase(
                case_id=cid,
                similarity=similarity,
                patient_summary=f"{meta['patient_sex']} {meta['patient_age']}y",
                validated_diagnosis=meta["validated_diagnosis"],
                differential=json.loads(meta.get("differential", "[]")),
                doctor_notes=meta.get("doctor_notes") or None,
            )
        )

    return SimilarCasesResponse(cases=cases, total_cases_in_store=total)


@router.delete("/{case_id}", status_code=204, response_model=None)
def delete_case(case_id: str) -> None:
    try:
        store.delete(case_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}") from exc
