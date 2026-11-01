import io
import time
import zipfile
import pytest
from httpx import AsyncClient
from backend.services.orchestrator import orchestrator
from backend.services.langfuse_tracer import langfuse_tracer


def make_zip(files: dict[str, str | bytes]) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files.items():
            if isinstance(content, str):
                zf.writestr(fname, content.encode("utf-8"))
            else:
                zf.writestr(fname, content)
    buf.seek(0)
    return buf


@pytest.mark.asyncio
async def test_m6_m7_reports_qa_admin(client: AsyncClient):
    """
    Test M6:
    - SDE and PM reports clearly differ in tone and content
    - At least 4 distinct Mermaid diagram types
    - Markdown and PDF exports
    - RAG Q&A with code citations and under 3s response time

    Test M7:
    - Admin CRUD on users and projects
    - Server-side admin guard
    - Analytics overview
    - Langfuse traces tracking tokens, latency, cost, success
    """
    # 1. Register regular user and admin user
    user_email = "regular_dev@example.com"
    admin_email = "admin_boss@example.com"
    pwd = "password123"

    await client.post("/api/auth/register", json={"email": user_email, "password": pwd, "role": "user"})
    await client.post("/api/auth/register", json={"email": admin_email, "password": pwd, "role": "admin"})

    login_user = await client.post("/api/auth/login", json={"email": user_email, "password": pwd})
    user_headers = {"Authorization": f"Bearer {login_user.json()['access_token']}"}

    login_admin = await client.post("/api/auth/login", json={"email": admin_email, "password": pwd})
    admin_headers = {"Authorization": f"Bearer {login_admin.json()['access_token']}"}

    # 2. Upload and analyze project
    repo_files = {
        "main.py": """
from fastapi import FastAPI
app = FastAPI()

@app.get("/orders")
def get_orders():
    \"\"\"List all user orders.\"\"\"
    return [{"order_id": 101, "total": 99.99}]

@app.post("/orders")
def create_order(order: dict):
    \"\"\"Process credit card transaction and place order.\"\"\"
    return {"order_id": 102, "status": "processed"}
""",
        "db.py": """
class OrderModel:
    \"\"\"Database table for orders.\"\"\"
    pass
"""
    }
    zip_buf = make_zip(repo_files)

    up_resp = await client.post(
        "/api/projects/upload",
        data={"name": "Order Management Service", "personas": '["sde", "pm"]'},
        files={"file": ("orders.zip", zip_buf, "application/zip")},
        headers=user_headers,
    )
    assert up_resp.status_code == 201
    project_id = up_resp.json()["project_id"]

    await client.post(f"/api/projects/{project_id}/preprocess", headers=user_headers)
    await orchestrator.run_pipeline(project_id)

    # 3. M6 Check: SDE and PM reports read clearly differently
    sde_resp = await client.get(f"/api/projects/{project_id}/reports/sde", headers=user_headers)
    assert sde_resp.status_code == 200
    sde_text = sde_resp.json()["content_markdown"]

    pm_resp = await client.get(f"/api/projects/{project_id}/reports/pm", headers=user_headers)
    assert pm_resp.status_code == 200
    pm_text = pm_resp.json()["content_markdown"]

    # SDE has technical terms: API, schema, database, deployment, architecture
    assert "### 2. API Specifications" in sde_text
    assert "docker run" in sde_text.lower() or "deployment" in sde_text.lower()
    # PM has business terms: Customer Journeys, Feature Inventory, Business Priority, Roadmap
    assert "Executive Summary" in pm_text
    assert "Customer Journeys" in pm_text
    assert "Business Priority" in pm_text
    # Distinct styles
    assert sde_text != pm_text

    # 4. M6 Check: At least 4 Mermaid diagram types
    diag_resp = await client.get(f"/api/projects/{project_id}/reports/diagrams", headers=user_headers)
    assert diag_resp.status_code == 200
    diagrams = diag_resp.json()["diagrams_json"]
    diag_types = {d["type"] for d in diagrams}
    assert "architecture" in diag_types
    assert "flowchart" in diag_types
    assert "sequence" in diag_types
    assert "er" in diag_types

    # 5. M6 Check: Markdown and PDF export
    md_export = await client.get(f"/api/projects/{project_id}/export/markdown", headers=user_headers)
    assert md_export.status_code == 200
    assert md_export.headers["content-type"].startswith("text/markdown")
    assert "Order Management Service" in md_export.text

    pdf_export = await client.get(f"/api/projects/{project_id}/export/pdf", headers=user_headers)
    assert pdf_export.status_code == 200
    assert pdf_export.headers["content-type"] == "application/pdf"
    assert len(pdf_export.content) > 1000  # Valid non-empty binary PDF generated

    # 6. M6 Check: RAG Q&A responds in under 3 seconds with citations
    start_qa = time.time()
    qa_resp = await client.post(
        f"/api/projects/{project_id}/qa",
        json={"question": "How are orders processed and created?", "persona": "sde"},
        headers=user_headers,
    )
    qa_duration = time.time() - start_qa
    assert qa_resp.status_code == 200
    assert qa_duration < 3.0, f"QA took {qa_duration}s, expected < 3.0s"
    qa_data = qa_resp.json()
    assert qa_data["response_time_ms"] < 3000
    assert len(qa_data["citations"]) > 0
    first_cit = qa_data["citations"][0]
    assert "main.py" in first_cit["file_path"] or "orders" in first_cit["snippet"].lower()

    # 7. M7 Check: Server-side admin route protection
    forbidden_resp = await client.get("/api/admin/users", headers=user_headers)
    assert forbidden_resp.status_code == 403

    # 8. M7 Check: Admin CRUD on users and projects
    users_resp = await client.get("/api/admin/users", headers=admin_headers)
    assert users_resp.status_code == 200
    users_list = users_resp.json()
    assert len(users_list) >= 2

    # Admin project list
    projs_resp = await client.get("/api/admin/projects", headers=admin_headers)
    assert projs_resp.status_code == 200
    assert len(projs_resp.json()) >= 1

    # Admin analytics
    analytics_resp = await client.get("/api/admin/analytics", headers=admin_headers)
    assert analytics_resp.status_code == 200
    analytics = analytics_resp.json()
    assert analytics["total_users"] >= 2
    assert analytics["total_projects"] >= 1
    assert analytics["completion_rate_percent"] >= 0.0

    # 9. M7 Check: Langfuse traces
    langfuse_tracer.record_trace(
        project_id=project_id,
        agent_name="sde_writer",
        prompt="Generate SDE report",
        output="Complete SDE report",
        tokens=850,
        latency_sec=0.45,
        cost_usd=0.0012,
        status="success",
    )
    traces_resp = await client.get("/api/admin/traces", headers=admin_headers)
    assert traces_resp.status_code == 200
    traces_data = traces_resp.json()
    assert traces_data["total_traces"] >= 1
    trace = traces_data["traces"][0]
    assert trace["agent_name"] == "sde_writer"
    assert trace["tokens"] == 850
