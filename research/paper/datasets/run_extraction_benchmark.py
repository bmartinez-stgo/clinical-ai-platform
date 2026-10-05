"""Corre los 150 PDFs sintéticos contra /documents/labs/parse en producción.

Credenciales via variables de entorno (nunca hardcodeadas ni commiteadas):
  RESEARCH_CLIENT_ID, RESEARCH_CLIENT_SECRET

Uso: RESEARCH_CLIENT_ID=... RESEARCH_CLIENT_SECRET=... python3 run_extraction_benchmark.py
Salida: ../results/raw/<report_id>.json (respuesta cruda del pipeline)
        ../results/run_log.jsonl (bitácora: tiempos, éxito/fallo)
"""
import json
import os
import time
from pathlib import Path

import requests

BASE_URL = "https://nahui-ai.ddns.net"
TOKEN_URL = f"{BASE_URL}/auth/token"
SUBMIT_URL = f"{BASE_URL}/documents/labs/parse"

BASE_DIR = Path(__file__).parent
CORPUS_DIR = BASE_DIR / "corpus"
RESULTS_DIR = BASE_DIR.parent / "results" / "raw"
LOG_PATH = BASE_DIR.parent / "results" / "run_log.jsonl"

POLL_INTERVAL_SECONDS = 10  # /documents está limitado a 10 req/min por cliente
JOB_TIMEOUT_SECONDS = 300
TOKEN_REFRESH_MARGIN_SECONDS = 120
INTER_JOB_PAUSE_SECONDS = 6  # margen extra entre reportes, aparte del rate limit
MAX_429_RETRIES = 8


class TokenManager:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._expires_at = 0

    def get(self) -> str:
        if self._token is None or time.time() > self._expires_at - TOKEN_REFRESH_MARGIN_SECONDS:
            self._refresh()
        return self._token

    def _refresh(self):
        r = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + data["expires_in"]
        print(f"  [token refrescado, expira en {data['expires_in']}s]")


def _retry_after_seconds(r: requests.Response) -> float:
    try:
        return max(float(r.headers.get("Retry-After", 15)), 1.0)
    except (TypeError, ValueError):
        return 15.0


def submit(pdf_path: Path, token: str) -> str:
    for attempt in range(1, MAX_429_RETRIES + 1):
        with open(pdf_path, "rb") as f:
            r = requests.post(
                SUBMIT_URL,
                headers={"Authorization": f"Bearer {token}"},
                files={"file": (pdf_path.name, f, "application/pdf")},
                timeout=30,
            )
        if r.status_code == 429:
            wait = _retry_after_seconds(r)
            print(f"  [429 en submit, esperando {wait:.0f}s (intento {attempt}/{MAX_429_RETRIES})]")
            time.sleep(wait)
            continue
        if r.status_code != 202:
            raise RuntimeError(f"submit failed: {r.status_code} {r.text[:300]}")
        return r.json()["job_id"]
    raise RuntimeError("submit failed: too many 429s")


def poll(job_id: str, token: str) -> dict:
    deadline = time.time() + JOB_TIMEOUT_SECONDS
    retries = 0
    while time.time() < deadline:
        r = requests.get(
            f"{SUBMIT_URL}/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if r.status_code == 429:
            retries += 1
            if retries > MAX_429_RETRIES:
                raise RuntimeError("poll failed: too many 429s")
            wait = _retry_after_seconds(r)
            print(f"  [429 en poll, esperando {wait:.0f}s (intento {retries}/{MAX_429_RETRIES})]")
            time.sleep(wait)
            continue
        if r.status_code == 404:
            raise RuntimeError("job not found / expired")
        r.raise_for_status()
        data = r.json()
        if data["status"] == "done":
            return data["result"]
        if data["status"] == "failed":
            raise RuntimeError(f"job failed: {data.get('error')}")
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(f"job {job_id} did not finish in {JOB_TIMEOUT_SECONDS}s")


def main():
    client_id = os.environ.get("RESEARCH_CLIENT_ID")
    client_secret = os.environ.get("RESEARCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("set RESEARCH_CLIENT_ID and RESEARCH_CLIENT_SECRET env vars")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    tokens = TokenManager(client_id, client_secret)

    pdfs = sorted(CORPUS_DIR.glob("labtest_*.pdf"))
    print(f"{len(pdfs)} PDFs a procesar\n")

    done, failed = 0, 0
    with open(LOG_PATH, "w", encoding="utf-8") as log:
        for i, pdf_path in enumerate(pdfs, 1):
            report_id = pdf_path.stem
            out_path = RESULTS_DIR / f"{report_id}.json"
            if out_path.exists():
                print(f"[{i}/{len(pdfs)}] {report_id}: ya existe, se omite")
                done += 1
                continue

            t0 = time.time()
            try:
                token = tokens.get()
                job_id = submit(pdf_path, token)
                result = poll(job_id, tokens.get())
                out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                elapsed = time.time() - t0
                done += 1
                print(f"[{i}/{len(pdfs)}] {report_id}: ok ({elapsed:.1f}s)")
                log.write(json.dumps({"report_id": report_id, "status": "ok", "elapsed_s": elapsed}) + "\n")
            except Exception as e:
                failed += 1
                print(f"[{i}/{len(pdfs)}] {report_id}: FALLO -> {e}")
                log.write(json.dumps({"report_id": report_id, "status": "failed", "error": str(e)}) + "\n")
            log.flush()
            time.sleep(INTER_JOB_PAUSE_SECONDS)

    print(f"\n{done} ok, {failed} fallidos de {len(pdfs)}")


if __name__ == "__main__":
    main()
