import json
import os
from datetime import datetime, timezone
from pathlib import Path

import mariadb
import requests


def _load_seed_sql() -> None:
    host = os.getenv("RAG_MARIADB_HOST", "localhost")
    port = int(os.getenv("RAG_MARIADB_PORT", "3306"))
    user = os.getenv("RAG_MARIADB_USER")
    password = os.getenv("RAG_MARIADB_PASSWORD")
    database = os.getenv("RAG_MARIADB_DATABASE")
    if not user or not password or not database:
        raise RuntimeError("Missing MariaDB env vars for test: RAG_MARIADB_USER/PASSWORD/DATABASE")

    sql_path = Path(__file__).with_name("seed_metadata.sql")
    statements = [stmt.strip() for stmt in sql_path.read_text(encoding="utf-8").split(";") if stmt.strip()]
    conn = mariadb.connect(host=host, port=port, user=user, password=password, database=database)
    try:
        cur = conn.cursor()
        for stmt in statements:
            cur.execute(stmt)
        conn.commit()
    finally:
        conn.close()


def _insert_risk_analysis(project_id: int, summary: str, rationale: str) -> None:
    host = os.getenv("RAG_MARIADB_HOST", "localhost")
    port = int(os.getenv("RAG_MARIADB_PORT", "3306"))
    user = os.getenv("RAG_MARIADB_USER")
    password = os.getenv("RAG_MARIADB_PASSWORD")
    database = os.getenv("RAG_MARIADB_DATABASE")
    if not user or not password or not database:
        raise RuntimeError("Missing MariaDB env vars for test: RAG_MARIADB_USER/PASSWORD/DATABASE")

    citations_json = json.dumps(
        [{"source_type": "weekly_report", "source_id": "1", "excerpt": "문서 인용"}],
        ensure_ascii=False,
    )
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    sql = (
        "INSERT INTO risk_analysis (project_id, likelihood, impact, summary_text, rationale_text, "
        "citations_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    conn = mariadb.connect(host=host, port=port, user=user, password=password, database=database)
    try:
        cur = conn.cursor()
        cur.execute(sql, (project_id, 4, 3, summary, rationale, citations_json, created_at))
        conn.commit()
    finally:
        conn.close()


_load_seed_sql()
_insert_risk_analysis(1, "요약 테스트 A", "근거 테스트 A")
_insert_risk_analysis(1, "요약 테스트 B", "근거 테스트 B")

url = "http://localhost:8000/api/projects/1/docs/risk_reports"
params = {"page": 1, "size": 10}
res = requests.get(url, params=params)

print("=" * 100)
print("[TEST] Risk report list")
print("[TEST] Status:", res.status_code)
if res.status_code == 200:
    print("[Success] 응답 결과:")
    print(res.json())
else:
    print("[Failed] 상태 코드:", res.status_code)
    print(res.text)
    raise RuntimeError(f"List request failed with status {res.status_code}")
