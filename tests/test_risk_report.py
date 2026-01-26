import os
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

_load_seed_sql()

upload_path = Path(__file__).with_name("samples") / "iso_21500.pdf"
if upload_path.exists():
    with upload_path.open("rb") as fp:
        files = {"file": (upload_path.name, fp, "application/pdf")}
        upload_res = requests.post("http://localhost:8000/upload/pdf", files=files)
        print("testing PDF upload....")
        print("[TEST] Upload status:", upload_res.status_code)
        if upload_res.status_code != 200:
            print(upload_res.text)
else:
    print("[TEST] Upload skipped: sample PDF not found:", upload_path)

payload = {
    "week_start": "2024-01-01",
    "week_end": "2024-01-07",
}

project_id = 1
url = f"http://localhost:8000/api/projects/{project_id}/docs/risk_report"

res = requests.post(url, json=payload)

print("=" * 100)
print(f"[TEST] Project ID: {project_id}")
print(f"[TEST] Payload: {payload}")
if res.status_code == 200:
    print("[Success] 응답 결과:")
    print(res.json())
else:
    print(f"[Failed] 상태 코드: {res.status_code}")
    print(res.text)
