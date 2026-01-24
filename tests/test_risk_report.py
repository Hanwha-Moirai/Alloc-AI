import requests

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
