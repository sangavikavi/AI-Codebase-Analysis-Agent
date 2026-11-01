import io
import zipfile
import pytest
from httpx import AsyncClient
from backend.services.orchestrator import orchestrator


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
async def test_m3_m4_agents_graph_execution(client: AsyncClient):
    """
    Test M3 (real-time progress, activity feed, PM-readable text, real percentages)
    and M4 (at least 5 agents: coordinator, extractor, web_researcher, sde_writer, pm_writer, diagram_agent, evaluator).
    """
    # 1. Login user
    email = "agent_tester@example.com"
    pwd = "password123"
    await client.post("/api/auth/register", json={"email": email, "password": pwd})
    login_res = await client.post("/api/auth/login", json={"email": email, "password": pwd})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Create codebase
    repo_files = {
        "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\n",
        "main.py": """
from fastapi import FastAPI
app = FastAPI()

@app.get("/items")
def get_items():
    return [{"id": 1, "name": "Item 1"}]

@app.post("/items")
def create_item(item: dict):
    return {"status": "created"}
""",
        "models.py": """
class ItemModel:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
"""
    }
    zip_buf = make_zip(repo_files)

    # Upload project with Deep depth config
    cfg_json = '{"depth": "Deep", "verbosity": "High", "feature_toggles": {"include_owasp": true}}'
    upload_resp = await client.post(
        "/api/projects/upload",
        data={"name": "Agents Pipeline Project", "personas": '["sde", "pm"]', "config": cfg_json},
        files={"file": ("codebase.zip", zip_buf, "application/zip")},
        headers=headers,
    )
    assert upload_resp.status_code == 201
    project_id = upload_resp.json()["project_id"]

    # Preprocess
    prep_resp = await client.post(f"/api/projects/{project_id}/preprocess", headers=headers)
    assert prep_resp.status_code == 200

    # Run the full pipeline sequentially
    await orchestrator.run_pipeline(project_id)

    # Check project status
    proj_resp = await client.get(f"/api/projects/{project_id}", headers=headers)
    assert proj_resp.status_code == 200
    proj_data = proj_resp.json()
    assert proj_data["status"] == "completed"
    assert proj_data["progress_percentage"] == 100.0

    # Verify M3: Activity Feed events
    events_resp = await client.get(f"/api/projects/{project_id}/events", headers=headers)
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) >= 5

    # Check for M3 per-file progress events ("Processing file...")
    has_file_event = any("Processing file" in ev["message"] for ev in events)
    assert has_file_event, "M3 per-file progress event not found"

    # Check event types: milestone, info
    event_types = {ev["event_type"] for ev in events}
    assert "milestone" in event_types
    assert "info" in event_types

    # Verify M4: 5+ Agents contributed to output
    # Coordinator, Extractor, Web Researcher, SDE Writer, PM Writer, Diagram Agent, Evaluator
    stages = {ev["stage"] for ev in events}
    assert "Coordinator" in stages
    assert "Code Extraction" in stages
    assert "Web Research" in stages
    assert "SDE Documentation" in stages
    assert "PM Documentation" in stages
    assert "Diagram Generation" in stages
    assert "Quality Evaluation" in stages

    # Check generated reports in DB
    reps_resp = await client.get(f"/api/projects/{project_id}/reports", headers=headers)
    assert reps_resp.status_code == 200
    reports = reps_resp.json()
    assert len(reports) >= 3  # SDE, PM, Diagrams

    personas_generated = {r["persona"] for r in reports}
    assert "sde" in personas_generated
    assert "pm" in personas_generated
    assert "diagrams" in personas_generated

    # Check that Web Search is cited in SDE report
    sde_rep = next(r for r in reports if r["persona"] == "sde")
    assert "Security Standards" in sde_rep["content_markdown"]
    assert "http" in sde_rep["content_markdown"]  # Web link cited
