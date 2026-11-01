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
async def test_m5_pause_resume_and_chat_guardrails(client: AsyncClient):
    """
    Test M5:
    1. Pause & Resume at any node with zero data loss
    2. Guardrail 1: Questions about ongoing analysis answered from state
    3. Guardrail 2: Context injection directives stored and reflected in final docs
    4. Guardrail 3: Refusal and redirection for off-topic queries
    5. Interaction history persisted in DB
    """
    email = "m5_user@example.com"
    pwd = "password123"
    await client.post("/api/auth/register", json={"email": email, "password": pwd})
    login_res = await client.post("/api/auth/login", json={"email": email, "password": pwd})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    repo_files = {
        "main.py": """
from fastapi import FastAPI
app = FastAPI()

@app.get("/checkout")
def checkout():
    return {"status": "paid"}
"""
    }
    zip_buf = make_zip(repo_files)

    upload_resp = await client.post(
        "/api/projects/upload",
        data={"name": "M5 Interactive Project", "personas": '["sde", "pm"]'},
        files={"file": ("checkout_service.zip", zip_buf, "application/zip")},
        headers=headers,
    )
    assert upload_resp.status_code == 201
    project_id = upload_resp.json()["project_id"]

    await client.post(f"/api/projects/{project_id}/preprocess", headers=headers)

    # 1. Test Chat Guardrail 1: Question about analysis
    q_resp = await client.post(
        f"/api/projects/{project_id}/chat",
        json={"message": "What are you analyzing and what have you found so far?"},
        headers=headers,
    )
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert q_data["message_type"] == "question"
    assert "analyzing" in q_data["response"].lower()
    assert "files" in q_data["response"].lower() or "routes" in q_data["response"].lower()

    # 2. Test Chat Guardrail 2: Context injection
    directive = "Focus strictly on payments processing and note that /admin is deprecated."
    ctx_resp = await client.post(
        f"/api/projects/{project_id}/chat",
        json={"message": directive},
        headers=headers,
    )
    assert ctx_resp.status_code == 200
    ctx_data = ctx_resp.json()
    assert ctx_data["message_type"] == "context"
    assert "received and saved" in ctx_data["response"].lower()

    # 3. Test Chat Guardrail 3: Off-topic refusal and redirection
    ref_resp = await client.post(
        f"/api/projects/{project_id}/chat",
        json={"message": "Write me a funny limerick about pirates."},
        headers=headers,
    )
    assert ref_resp.status_code == 200
    ref_data = ref_resp.json()
    assert ref_data["message_type"] == "refusal"
    assert "restricted" in ref_data["response"].lower() or "notice" in ref_data["response"].lower()

    # 4. Verify Chat History is Persisted
    chat_hist = await client.get(f"/api/projects/{project_id}/chat", headers=headers)
    assert chat_hist.status_code == 200
    history = chat_hist.json()
    assert len(history) == 6  # 3 user messages + 3 agent responses

    # 5. Test Pause & Resume
    pause_resp = await client.post(f"/api/projects/{project_id}/pause", headers=headers)
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "paused"

    # Resume analysis
    resume_resp = await client.post(f"/api/projects/{project_id}/resume", headers=headers)
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "resumed"

    # Complete pipeline run to verify injected context shows up in final docs
    await orchestrator.run_pipeline(project_id)

    # Verify that the injected context shows up in final SDE and PM reports
    sde_resp = await client.get(f"/api/projects/{project_id}/reports/sde", headers=headers)
    assert sde_resp.status_code == 200
    sde_content = sde_resp.json()["content_markdown"]
    assert "payments processing" in sde_content.lower()
    assert "/admin is deprecated" in sde_content.lower()

    pm_resp = await client.get(f"/api/projects/{project_id}/reports/pm", headers=headers)
    assert pm_resp.status_code == 200
    pm_content = pm_resp.json()["content_markdown"]
    assert "payments processing" in pm_content.lower()
