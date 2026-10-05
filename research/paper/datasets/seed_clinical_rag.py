"""Carga los casos de rag_seed_cases.py al store de clinical-rag vía
POST /rag/cases (gateway). Casos reales de literatura, no los del Estudio 2.
"""
import os
import requests

from rag_seed_cases import SEED_CASES

BASE_URL = "https://nahui-ai.ddns.net"


def get_token(client_id: str, client_secret: str) -> str:
    r = requests.post(
        f"{BASE_URL}/auth/token",
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def main():
    client_id = os.environ.get("RESEARCH_CLIENT_ID")
    client_secret = os.environ.get("RESEARCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("set RESEARCH_CLIENT_ID and RESEARCH_CLIENT_SECRET")

    token = get_token(client_id, client_secret)
    headers = {"Authorization": f"Bearer {token}"}

    for case in SEED_CASES:
        r = requests.post(f"{BASE_URL}/rag/cases", headers=headers, json=case["request"], timeout=15)
        if r.status_code == 201:
            data = r.json()
            print(f"ok: {case['request']['validated_diagnosis']} -> case_id={data['case_id']} (total en store: {data['total_cases']})")
        else:
            print(f"FALLO ({r.status_code}): {case['request']['validated_diagnosis']} -> {r.text[:200]}")


if __name__ == "__main__":
    main()
