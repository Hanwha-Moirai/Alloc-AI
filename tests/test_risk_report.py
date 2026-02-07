from pathlib import Path

import pytest


def test_risk_report_generate(seeded_db, api_base_url, api_request) -> None:
    upload_path = Path(__file__).with_name("samples") / "ISO310000_sample.pdf"
    if upload_path.exists():
        with upload_path.open("rb") as fp:
            files = {"file": (upload_path.name, fp, "application/pdf")}
            upload_res = api_request("POST", f"{api_base_url}/upload/pdf", files=files)
            assert upload_res.status_code == 200, upload_res.text
    else:
        pytest.skip(f"Upload skipped: sample PDF not found: {upload_path}")

    payload = {
        "week_start": "2024-01-01",
        "week_end": "2024-01-07",
    }

    project_id = 1
    url = f"{api_base_url}/api/projects/{project_id}/docs/risk_report"
    res = api_request("POST", url, json=payload)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("project_id") == str(project_id)
    assert "likelihood" in body and "impact" in body
    assert "summary" in body and "rationale" in body
