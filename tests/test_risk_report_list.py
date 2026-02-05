def test_risk_report_list(seeded_db, insert_risk_analysis_fn, api_base_url, api_request) -> None:
    insert_risk_analysis_fn(project_id=1, summary="요약 테스트 A", rationale="근거 테스트 A")
    insert_risk_analysis_fn(project_id=1, summary="요약 테스트 B", rationale="근거 테스트 B")

    url = f"{api_base_url}/api/projects/1/docs/risk_reports"
    params = {"page": 1, "size": 10}
    res = api_request("GET", url, params=params)

    assert res.status_code == 200, res.text
    body = res.json()
    assert "items" in body
    assert isinstance(body["items"], list)
    assert len(body["items"]) >= 2
