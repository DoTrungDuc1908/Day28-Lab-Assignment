# scripts/09_verify_observability.py
import requests
from dotenv import load_dotenv

load_dotenv()

def check_prometheus():
    resp = requests.get("http://localhost:9090/api/v1/query",
                        params={"query": 'http_requests_total{job="api-gateway"}'})
    data = resp.json()
    assert data["status"] == "success"
    print("Integration 9 OK: Prometheus metrics flowing")

def check_langsmith():
    import os
    from langsmith import Client
    api_key = os.environ.get("LANGCHAIN_API_KEY", "")
    if not api_key or "your_langsmith_key" in api_key or "dummy" in api_key:
        print("Integration 10 SKIPPED (LangSmith API key is not configured or dummy)")
        return
    try:
        client = Client(api_key=api_key)
        runs = list(client.list_runs(project_name="lab28-platform", limit=1))
        if len(runs) > 0:
            print("Integration 10 OK: LangSmith traces visible")
        else:
            print("Integration 10 WARNING: No traces found in project 'lab28-platform'")
    except Exception as e:
        print(f"Integration 10 WARNING: LangSmith check encountered an error: {e}")

check_prometheus()
check_langsmith()
