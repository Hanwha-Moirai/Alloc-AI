import os
from pathlib import Path
from typing import Iterator

import mariadb
import pytest
import requests


def _get_db_config() -> tuple[str, int, str, str, str]:
    host = os.getenv("RAG_TEST_MARIADB_HOST", "127.0.0.1")
    port = int(os.getenv("RAG_TEST_MARIADB_PORT", "3306"))
    user = os.getenv("RAG_TEST_MARIADB_USER", os.getenv("RAG_MARIADB_USER"))
    password = os.getenv("RAG_TEST_MARIADB_PASSWORD", os.getenv("RAG_MARIADB_PASSWORD"))
    database = os.getenv("RAG_TEST_MARIADB_DATABASE", os.getenv("RAG_MARIADB_DATABASE"))
    if not user or not password or not database:
        pytest.skip("Missing MariaDB env vars for test: RAG_MARIADB_USER/PASSWORD/DATABASE")
    return host, port, user, password, database


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return os.getenv("RAG_API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def db_config() -> tuple[str, int, str, str, str]:
    return _get_db_config()


def _load_seed_sql(conn: mariadb.Connection) -> None:
    sql_path = Path(__file__).with_name("seed_metadata.sql")
    statements = [stmt.strip() for stmt in sql_path.read_text(encoding="utf-8").split(";") if stmt.strip()]
    cur = conn.cursor()
    for stmt in statements:
        if stmt.upper().startswith("USE "):
            # Avoid overriding the configured database.
            continue
        cur.execute(stmt)
    conn.commit()


@pytest.fixture()
def seeded_db(db_config: tuple[str, int, str, str, str]) -> Iterator[None]:
    host, port, user, password, database = db_config
    conn = mariadb.connect(host=host, port=port, user=user, password=password, database=database)
    try:
        _load_seed_sql(conn)
        yield
    finally:
        conn.close()


def _request_or_skip(method: str, url: str, **kwargs) -> requests.Response:
    try:
        return requests.request(method, url, **kwargs)
    except requests.RequestException:
        pytest.skip("API server not reachable at configured base URL.")


@pytest.fixture()
def api_request() -> callable:
    return _request_or_skip


@pytest.fixture()
def insert_risk_analysis_fn(db_config: tuple[str, int, str, str, str]) -> callable:
    def _insert(*, project_id: int, summary: str, rationale: str) -> int:
        import json
        from datetime import datetime, timezone

        host, port, user, password, database = db_config
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
            return int(cur.lastrowid)
        finally:
            conn.close()

    return _insert
