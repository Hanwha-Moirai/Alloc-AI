def test_risk_report_detail(seeded_db, insert_risk_analysis_fn, api_base_url, api_request) -> None:
    report_id = insert_risk_analysis_fn(project_id=1, summary="요약 테스트 상세", rationale="근거 테스트 상세")

    url = f"{api_base_url}/api/projects/1/docs/risk_reports/{report_id}"
    res = api_request("GET", url)

    assert res.status_code == 200, res.text
    body = res.json()
    assert int(body.get("report_id")) == report_id
    assert body.get("project_id") == "1"
