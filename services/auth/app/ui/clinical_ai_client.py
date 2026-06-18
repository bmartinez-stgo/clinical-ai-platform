"""
Clinical AI Platform — Python SDK
==================================
Requires: requests (stdlib only otherwise)

Usage (blocking — waits for extraction to finish):

    from clinical_ai_client import ClinicalAIClient, PatientContext

    client = ClinicalAIClient(
        base_url="https://nahui-ai.ddns.net",
        client_id="<your-client-id>",
        client_secret="<your-client-secret>",
    )

    report = client.parse_lab_report("hemograma.pdf", language="es")
    result = client.diagnose(
        lab_report=report,
        patient=PatientContext(age=34, sex="F"),
        clinical_diagnosis="Fatigue and joint pain, rule out autoimmune",
    )
    print(result.assessment)

Usage (non-blocking — submit and poll manually):

    job = client.submit_lab_report("hemograma.pdf", language="es")
    print(f"Queued at position {job.position}, ~{job.estimated_seconds}s wait")

    while True:
        status = client.get_lab_status(job.job_id)
        if status.status == "done":
            report = status.result
            break
        if status.status == "failed":
            raise RuntimeError(status.error)
        print(f"Status: {status.status}, position: {status.position}")
        time.sleep(5)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ClinicalAIError(Exception):
    """Base exception for all SDK errors."""


class AuthError(ClinicalAIError):
    """Authentication failed — check client_id and client_secret."""


class RateLimitError(ClinicalAIError):
    def __init__(self, retry_after: int):
        super().__init__(f"Rate limited. Retry after {retry_after}s.")
        self.retry_after = retry_after


class APIError(ClinicalAIError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"HTTP {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


# ---------------------------------------------------------------------------
# Response dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Patient:
    name: str = ""
    dob: str = ""
    sex: str = ""
    id: str = ""


@dataclass
class ReportMeta:
    lab_name: str = ""
    report_date: str = ""
    ordering_physician: str = ""
    report_id: str = ""


@dataclass
class Observation:
    test_name: str = ""
    test_name_normalized: str = ""
    loinc_code: str = ""
    value: Any = None
    unit: str = ""
    unit_ucum: str = ""
    interpretation: str = ""
    reference_range: str = ""
    delta_from_range: Optional[float] = None


@dataclass
class LabReport:
    patient: Patient = field(default_factory=Patient)
    report: ReportMeta = field(default_factory=ReportMeta)
    observations: list[Observation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PatientContext:
    age: int
    sex: str  # "M" or "F"


@dataclass
class AutoimmuneFlag:
    marker: str
    value: Any
    loinc_code: str
    interpretation: str


@dataclass
class AbnormalMarker:
    test_name: str
    value: Any
    unit: str
    interpretation: str
    delta_from_range: Optional[float]


@dataclass
class LabJob:
    """Returned by submit_lab_report(). Use job_id to poll get_lab_status()."""
    job_id: str
    status: str  # queued | processing | done | failed
    position: Optional[int] = None
    estimated_seconds: Optional[int] = None
    result: Optional["LabReport"] = None
    error: Optional[str] = None


@dataclass
class DiagnosisResult:
    assessment: str = ""
    differential: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    autoimmune_flags: list[AutoimmuneFlag] = field(default_factory=list)
    abnormal_markers: list[AbnormalMarker] = field(default_factory=list)
    rag_cases_used: int = 0
    raw: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Token manager (thread-safe, auto-renewing)
# ---------------------------------------------------------------------------

class _TokenManager:
    def __init__(self, base_url: str, client_id: str, client_secret: str, session):
        self._url = f"{base_url}/auth/token"
        self._client_id = client_id
        self._client_secret = client_secret
        self._session = session
        self._lock = threading.Lock()
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0

    def get(self) -> str:
        with self._lock:
            if self._access_token is None or time.monotonic() >= self._expires_at:
                self._refresh()
            return self._access_token  # type: ignore[return-value]

    def invalidate(self) -> None:
        with self._lock:
            self._expires_at = 0.0

    def _refresh(self) -> None:
        resp = self._session.post(
            self._url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        if resp.status_code == 401:
            raise AuthError("Invalid client_id or client_secret.")
        if resp.status_code == 429:
            raise RateLimitError(int(resp.headers.get("Retry-After", 60)))
        if not resp.ok:
            raise ClinicalAIError(f"Token fetch failed: HTTP {resp.status_code} — {resp.text}")
        data = resp.json()
        self._access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._expires_at = time.monotonic() + expires_in - 60  # renew 60s early


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------

class ClinicalAIClient:
    """
    Thread-safe client for the Clinical AI Platform API.

    Tokens are acquired on first use and renewed automatically before expiry.
    """

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        timeout: int = 180,
        verify_ssl: bool = True,
    ):
        try:
            import requests  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError("Install 'requests': pip install requests") from exc

        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.verify = verify_ssl
        self._tokens = _TokenManager(self._base, client_id, client_secret, self._session)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_lab_report(
        self,
        pdf: "str | Path | bytes",
        language: str = "es",
        poll_interval: int = 5,
        timeout: int = 600,
    ) -> LabReport:
        """
        Upload a PDF lab report and wait for structured extraction to complete.

        Submits the file to the async queue, then polls until the job is done.
        Raises ClinicalAIError if the job fails or the timeout is exceeded.

        Args:
            pdf: File path (str or Path) or raw PDF bytes.
            language: "es" (default) or "en".
            poll_interval: Seconds between status checks (default 5).
            timeout: Maximum seconds to wait for extraction (default 600).

        Returns:
            LabReport dataclass with patient info, observations, and warnings.
        """
        job = self.submit_lab_report(pdf, language=language)
        deadline = time.monotonic() + timeout
        while True:
            status = self.get_lab_status(job.job_id)
            if status.status == "done":
                return status.result  # type: ignore[return-value]
            if status.status == "failed":
                raise ClinicalAIError(f"Lab extraction failed: {status.error}")
            if time.monotonic() > deadline:
                raise ClinicalAIError(
                    f"Lab extraction timed out after {timeout}s (job_id={job.job_id})"
                )
            time.sleep(poll_interval)

    def submit_lab_report(
        self,
        pdf: "str | Path | bytes",
        language: str = "es",
    ) -> LabJob:
        """
        Submit a PDF lab report to the extraction queue without waiting.

        Returns immediately with a LabJob containing the job_id, queue position,
        and estimated wait time. Call get_lab_status(job.job_id) to poll.

        Args:
            pdf: File path (str or Path) or raw PDF bytes.
            language: "es" (default) or "en".

        Returns:
            LabJob with job_id, position, and estimated_seconds.
        """
        if isinstance(pdf, (str, Path)):
            pdf_bytes = Path(pdf).read_bytes()
            filename = Path(pdf).name
        else:
            pdf_bytes = pdf
            filename = "report.pdf"

        resp = self._request(
            "POST",
            f"/documents/labs/parse?language={language}",
            files={"file": (filename, pdf_bytes, "application/pdf")},
        )
        data = resp.json()
        return LabJob(
            job_id=data["job_id"],
            status=data["status"],
            position=data.get("position"),
            estimated_seconds=data.get("estimated_seconds"),
        )

    def get_lab_status(self, job_id: str) -> LabJob:
        """
        Poll the status of a lab extraction job.

        Args:
            job_id: The job_id returned by submit_lab_report().

        Returns:
            LabJob with updated status. When status is "done", result is a LabReport.
            When status is "failed", error contains the reason.

        Raises:
            APIError with status_code=404 if the job has expired or is unknown.
        """
        resp = self._request("GET", f"/documents/labs/parse/{job_id}")
        data = resp.json()
        result = self._parse_lab_report(data["result"]) if data.get("result") else None
        return LabJob(
            job_id=data["job_id"],
            status=data["status"],
            position=data.get("position"),
            estimated_seconds=data.get("estimated_seconds"),
            result=result,
            error=data.get("error"),
        )

    def diagnose(
        self,
        lab_report: LabReport,
        patient: PatientContext,
        clinical_diagnosis: str,
        language: str = "es",
    ) -> DiagnosisResult:
        """
        Run differential diagnosis on a parsed lab report.

        Args:
            lab_report: Output from parse_lab_report().
            patient: Age and sex for the diagnostic model.
            clinical_diagnosis: Free-text clinical question or suspected diagnosis.
            language: "es" (default) or "en".

        Returns:
            DiagnosisResult with assessment, differential, and flags.
        """
        payload = self._build_diagnostic_request(lab_report, patient, clinical_diagnosis, language)
        resp = self._request("POST", "/diagnostics/diagnose", json=payload)
        return self._parse_diagnosis(resp.json())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs) -> Any:
        import requests  # noqa: PLC0415

        url = f"{self._base}{path}"
        headers = {"Authorization": f"Bearer {self._tokens.get()}"}

        resp = self._session.request(method, url, headers=headers, timeout=self._timeout, **kwargs)

        if resp.status_code == 401:
            # Token may have been revoked server-side; retry once with a fresh token
            self._tokens.invalidate()
            headers["Authorization"] = f"Bearer {self._tokens.get()}"
            resp = self._session.request(method, url, headers=headers, timeout=self._timeout, **kwargs)
            if resp.status_code == 401:
                raise AuthError("Request unauthorized after token refresh.")

        if resp.status_code == 429:
            raise RateLimitError(int(resp.headers.get("Retry-After", 60)))

        if not resp.ok:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise APIError(resp.status_code, str(detail))

        return resp

    @staticmethod
    def _parse_lab_report(data: dict) -> LabReport:
        p = data.get("patient") or {}
        r = data.get("report") or {}
        obs_raw = data.get("observations") or []

        observations = [
            Observation(
                test_name=o.get("test_name_raw", ""),
                test_name_normalized=o.get("test_name_normalized", ""),
                loinc_code=o.get("loinc_code", ""),
                value=o.get("value"),
                unit=o.get("unit_raw", ""),
                unit_ucum=o.get("unit_ucum", ""),
                interpretation=o.get("interpretation", ""),
                reference_range=o.get("reference_range_raw", ""),
                delta_from_range=o.get("delta_from_range"),
            )
            for o in obs_raw
        ]

        return LabReport(
            patient=Patient(
                name=p.get("name", ""),
                dob=p.get("date_of_birth", ""),
                sex=p.get("sex", ""),
                id=p.get("external_id", ""),
            ),
            report=ReportMeta(
                lab_name=r.get("laboratory_name", ""),
                report_date=r.get("report_date", ""),
                ordering_physician=r.get("ordering_physician", ""),
                report_id=r.get("accession_number", ""),
            ),
            observations=observations,
            warnings=data.get("warnings") or [],
        )

    @staticmethod
    def _build_diagnostic_request(
        report: LabReport,
        patient: PatientContext,
        clinical_diagnosis: str,
        language: str,
    ) -> dict:
        lab_series = [
            {
                "loinc_code": o.loinc_code,
                "test_name": o.test_name_normalized or o.test_name,
                "value": o.value,
                "unit": o.unit_ucum or o.unit,
                "interpretation": o.interpretation,
                "reference_range": o.reference_range,
                "delta_from_range": o.delta_from_range,
            }
            for o in report.observations
        ]

        return {
            "patient": {
                "age": patient.age,
                "sex": patient.sex,
                "name": report.patient.name,
                "id": report.patient.id,
            },
            "report_meta": {
                "lab_name": report.report.lab_name,
                "report_date": report.report.report_date,
                "report_id": report.report.report_id,
            },
            "lab_series": lab_series,
            "clinical_diagnosis": clinical_diagnosis,
            "language": language,
        }

    @staticmethod
    def _parse_diagnosis(data: dict) -> DiagnosisResult:
        flags = [
            AutoimmuneFlag(
                marker=f.get("marker", ""),
                value=f.get("value"),
                loinc_code=f.get("loinc_code", ""),
                interpretation=f.get("interpretation", ""),
            )
            for f in (data.get("autoimmune_flags") or [])
        ]
        abnormal = [
            AbnormalMarker(
                test_name=m.get("test_name", ""),
                value=m.get("value"),
                unit=m.get("unit", ""),
                interpretation=m.get("interpretation", ""),
                delta_from_range=m.get("delta_from_range"),
            )
            for m in (data.get("abnormal_markers") or [])
        ]
        return DiagnosisResult(
            assessment=data.get("assessment", ""),
            differential=data.get("differential") or [],
            recommendations=data.get("recommendations") or [],
            autoimmune_flags=flags,
            abnormal_markers=abnormal,
            rag_cases_used=data.get("rag_cases_used", 0),
            raw=data,
        )
