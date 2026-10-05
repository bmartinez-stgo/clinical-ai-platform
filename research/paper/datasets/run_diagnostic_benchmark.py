"""Corre los 20 casos clínicos reales contra /diagnostics/diagnose.

El toggle de RAG (`clinical_rag_enabled`) es a nivel de servicio (env var),
no por request -- por eso este script recibe `--rag-label` solo para
nombrar el archivo de salida; el toggle real se hace aparte con
`kubectl patch configmap` antes de cada corrida (ver results/run_log).

Uso:
  RESEARCH_CLIENT_ID=... RESEARCH_CLIENT_SECRET=... \
  python3 run_diagnostic_benchmark.py --rag-label with_rag
"""
import argparse
import json
import os
import time
from pathlib import Path

import requests

from clinical_cases import CASES

BASE_URL = "https://nahui-ai.ddns.net"
TOKEN_URL = f"{BASE_URL}/auth/token"
DIAGNOSE_URL = f"{BASE_URL}/diagnostics/diagnose"

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR.parent / "results" / "diagnostic_raw"

RATE_LIMIT_PAUSE = 4  # /diagnostics tiene 20 rpm; de sobra con esta pausa
MAX_429_RETRIES = 8


def get_token(client_id: str, client_secret: str) -> str:
    r = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def diagnose(payload: dict, token: str) -> dict:
    for attempt in range(1, MAX_429_RETRIES + 1):
        r = requests.post(
            DIAGNOSE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=120,
        )
        if r.status_code == 429:
            wait = max(float(r.headers.get("Retry-After", 15)), 1.0)
            print(f"  [429, esperando {wait:.0f}s]")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("demasiados 429")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rag-label", required=True, help="etiqueta para el archivo de salida, ej. with_rag / without_rag")
    args = parser.parse_args()

    client_id = os.environ.get("RESEARCH_CLIENT_ID")
    client_secret = os.environ.get("RESEARCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("set RESEARCH_CLIENT_ID and RESEARCH_CLIENT_SECRET")

    out_dir = RESULTS_DIR / args.rag_label
    out_dir.mkdir(parents=True, exist_ok=True)

    token = get_token(client_id, client_secret)
    token_time = time.time()

    for i, case in enumerate(CASES, 1):
        out_path = out_dir / f"{case['case_id']}.json"
        if out_path.exists():
            print(f"[{i}/{len(CASES)}] {case['case_id']}: ya existe, se omite")
            continue
        if time.time() - token_time > 3000:
            token = get_token(client_id, client_secret)
            token_time = time.time()
        try:
            result = diagnose(case["request"], token)
            out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[{i}/{len(CASES)}] {case['case_id']}: ok -> diferencial: {result.get('differential')}")
        except Exception as e:
            print(f"[{i}/{len(CASES)}] {case['case_id']}: FALLO -> {e}")
        time.sleep(RATE_LIMIT_PAUSE)


if __name__ == "__main__":
    main()
