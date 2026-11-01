import io
import zipfile
import pytest
from httpx import AsyncClient


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
async def test_m2_stack_detection_and_preprocessing(client: AsyncClient):
    """M2: Detect repo type and stack, entry points, endpoints, chunking and semantic search."""
    # Register and login user
    email = "tester_m2@example.com"
    pwd = "password123"
    await client.post("/api/auth/register", json={"email": email, "password": pwd})
    login_resp = await client.post("/api/auth/login", json={"email": email, "password": pwd})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a realistic FastAPI codebase archive
    repo_files = {
        "requirements.txt": "fastapi>=0.100.0\nuvicorn>=0.20.0\npydantic>=2.0\nsqlalchemy\n",
        "main.py": """
import uvicorn
from fastapi import FastAPI
from api.auth import auth_router
from api.users import users_router

app = FastAPI(title="Sample Store API")

@app.get("/health")
def health_check():
    \"\"\"Check system health and uptime status.\"\"\"
    return {"status": "ok"}

@app.get("/metrics")
def get_metrics():
    \"\"\"Return prometheus metrics.\"\"\"
    return {"uptime": 3600}

app.include_router(auth_router)
app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
        "api/auth.py": """
from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth")

class AuthManager:
    \"\"\"Handles user authentication and token verification.\"\"\"
    def __init__(self, secret: str):
        self.secret = secret

    def authenticate_user(self, username: str, password_hash: str) -> bool:
        \"\"\"Verify user credentials and grant session access.\"\"\"
        return True

@auth_router.post("/login")
def login(username: str, password: str):
    \"\"\"Authenticate user and generate JWT bearer access token.\"\"\"
    return {"token": "sample-jwt-token"}

@auth_router.post("/logout")
def logout():
    \"\"\"Revoke session tokens and sign out user.\"\"\"
    return {"status": "logged out"}
""",
        "api/users.py": """
from fastapi import APIRouter

users_router = APIRouter(prefix="/users")

@users_router.get("/")
def list_users():
    \"\"\"Fetch all registered accounts.\"\"\"
    return [{"id": 1, "username": "alice"}]

@users_router.post("/")
def create_user(name: str):
    \"\"\"Register a new user profile into the database.\"\"\"
    return {"id": 2, "name": name}
"""
    }

    zip_buf = make_zip(repo_files)

    # 1. Upload project
    upload_resp = await client.post(
        "/api/projects/upload",
        data={"name": "FastAPI Store Project", "personas": '["sde", "pm"]'},
        files={"file": ("fastapi_store.zip", zip_buf, "application/zip")},
        headers=headers,
    )
    assert upload_resp.status_code == 201
    project_id = upload_resp.json()["project_id"]

    # 2. Run M2 Preprocessing
    prep_resp = await client.post(f"/api/projects/{project_id}/preprocess", headers=headers)
    assert prep_resp.status_code == 200, prep_resp.text
    prep_data = prep_resp.json()

    # Verify Stack Detection (>= 90% accuracy: detected Python FastAPI)
    assert "Python FastAPI" in prep_data["detected_stack"]
    # Verify Entry Points
    assert any("main.py" in ep for ep in prep_data["entry_points"])
    # Verify API Endpoints count (6 endpoints: health, metrics, login, logout, list_users, create_user)
    assert prep_data["endpoint_count"] >= 6
    # Verify Chunks created
    assert prep_data["total_chunks"] >= 5

    # 3. Test M2 Semantic Search Endpoint
    # Query: "authentication"
    search_auth = await client.get(
        f"/api/projects/{project_id}/search",
        params={"query": "authentication", "top_k": 3},
        headers=headers,
    )
    assert search_auth.status_code == 200
    results = search_auth.json()["results"]
    assert len(results) > 0
    top_result = results[0]
    # Check that top result matched auth.py or AuthManager or login
    assert any(term in top_result["file_path"].lower() or term in top_result["name"].lower() or term in top_result["content"].lower() for term in ["auth", "login"])
    assert top_result["score"] > 0
    assert "start_line" in top_result
    assert "end_line" in top_result
    assert "chunk_type" in top_result

    # Query: "health check"
    search_health = await client.get(
        f"/api/projects/{project_id}/search",
        params={"query": "health check", "top_k": 3},
        headers=headers,
    )
    assert search_health.status_code == 200
    health_results = search_health.json()["results"]
    assert len(health_results) > 0
    assert any("health" in r["name"].lower() or "health" in r["content"].lower() for r in health_results)
