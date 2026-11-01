import io
import zipfile
import pytest
from httpx import AsyncClient


def make_zip(files: dict[str, str | bytes]) -> io.BytesIO:
    """Helper to create an in-memory zip file from a dictionary of filenames to contents."""
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
async def test_signup_login_jwt(client: AsyncClient):
    """M1: Test signup, login, JWT token generation and role retrieval."""
    email = "user1@example.com"
    password = "securepassword123"

    # 1. Register
    reg_resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "role": "user"},
    )
    assert reg_resp.status_code == 201, reg_resp.text
    user_data = reg_resp.json()
    assert user_data["email"] == email
    assert user_data["role"] == "user"

    # Duplicate registration check
    dup_resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]

    # 2. Login
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200, login_resp.text
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["role"] == "user"

    # 3. Authenticated /me endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_resp = await client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email


@pytest.mark.asyncio
async def test_user_project_isolation(client: AsyncClient):
    """M1: Users see only their own projects."""
    # Register user A
    await client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    login_a = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register user B
    await client.post(
        "/api/auth/register",
        json={"email": "bob@example.com", "password": "password123"},
    )
    login_b = await client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "password123"},
    )
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Alice uploads a valid codebase project
    zip_buf = make_zip({"main.py": "print('hello from alice')", "utils.py": "def add(a, b): return a + b"})
    upload_resp = await client.post(
        "/api/projects/upload",
        data={"name": "Alice Project", "personas": '["sde"]', "config": "{}"},
        files={"file": ("alice_code.zip", zip_buf, "application/zip")},
        headers=headers_a,
    )
    assert upload_resp.status_code == 201
    alice_proj_id = upload_resp.json()["project_id"]

    # Bob lists his projects -> should be empty
    bob_list = await client.get("/api/projects", headers=headers_b)
    assert bob_list.status_code == 200
    assert len(bob_list.json()) == 0

    # Bob tries to view Alice's project -> should be 403 Forbidden
    bob_get = await client.get(f"/api/projects/{alice_proj_id}", headers=headers_b)
    assert bob_get.status_code == 403

    # Alice lists her projects -> should see Alice Project
    alice_list = await client.get("/api/projects", headers=headers_a)
    assert alice_list.status_code == 200
    assert len(alice_list.json()) == 1
    assert alice_list.json()[0]["id"] == alice_proj_id


@pytest.mark.asyncio
async def test_validation_wrong_format(client: AsyncClient):
    """M1 Validation: Reject wrong format (RAR, 7z)."""
    login = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # RAR file extension
    rar_resp = await client.post(
        "/api/projects/upload",
        data={"name": "RAR Project"},
        files={"file": ("archive.rar", io.BytesIO(b"dummy rar"), "application/x-rar-compressed")},
        headers=headers,
    )
    assert rar_resp.status_code == 400
    assert "Unsupported archive format" in rar_resp.json()["detail"] or "Only ZIP" in rar_resp.json()["detail"]

    # 7z file extension
    seven_z_resp = await client.post(
        "/api/projects/upload",
        data={"name": "7z Project"},
        files={"file": ("archive.7z", io.BytesIO(b"dummy 7z"), "application/x-7z-compressed")},
        headers=headers,
    )
    assert seven_z_resp.status_code == 400
    assert "Unsupported archive format" in seven_z_resp.json()["detail"] or "Only ZIP" in seven_z_resp.json()["detail"]


@pytest.mark.asyncio
async def test_validation_corrupt_zip(client: AsyncClient):
    """M1 Validation: Reject corrupt or incomplete ZIP."""
    login = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Corrupt zip (random bytes)
    corrupt_resp = await client.post(
        "/api/projects/upload",
        data={"name": "Corrupt Project"},
        files={"file": ("corrupt.zip", io.BytesIO(b"PK\x03\x04corrupted-content-without-valid-zip-header"), "application/zip")},
        headers=headers,
    )
    assert corrupt_resp.status_code == 400
    assert "Corrupt or incomplete ZIP" in corrupt_resp.json()["detail"]


@pytest.mark.asyncio
async def test_validation_empty_repo(client: AsyncClient):
    """M1 Validation: Reject empty repository."""
    login = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Empty zip
    empty_zip = make_zip({})
    resp = await client.post(
        "/api/projects/upload",
        data={"name": "Empty Project"},
        files={"file": ("empty.zip", empty_zip, "application/zip")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_validation_docs_only_or_binary_only(client: AsyncClient):
    """M1 Validation: Reject non-code repo (docs-only or binary-only)."""
    login = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Docs only
    docs_zip = make_zip({"README.md": "# Just documentation", "guide.txt": "Some guide text"})
    docs_resp = await client.post(
        "/api/projects/upload",
        data={"name": "Docs Project"},
        files={"file": ("docs.zip", docs_zip, "application/zip")},
        headers=headers,
    )
    assert docs_resp.status_code == 400
    assert "documentation" in docs_resp.json()["detail"].lower() or "source code" in docs_resp.json()["detail"].lower()

    # Binary only
    binary_zip = make_zip({"logo.png": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", "binary.bin": b"\x00\x01\x02\x03"})
    binary_resp = await client.post(
        "/api/projects/upload",
        data={"name": "Binary Project"},
        files={"file": ("binary.zip", binary_zip, "application/zip")},
        headers=headers,
    )
    assert binary_resp.status_code == 400
    assert "binary" in binary_resp.json()["detail"].lower() or "source code" in binary_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_validation_github_urls(client: AsyncClient):
    """M1 Validation: Reject malformed GitHub URL or private/non-existent repo."""
    login = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Malformed URL
    bad_url_resp = await client.post(
        "/api/projects/github",
        json={"name": "Bad URL", "github_url": "ftp://not-github.com/bad/repo"},
        headers=headers,
    )
    assert bad_url_resp.status_code == 400
    assert "Malformed GitHub URL" in bad_url_resp.json()["detail"]

    # Non-existent or private repo
    non_existent_resp = await client.post(
        "/api/projects/github",
        json={"name": "Non Existent", "github_url": "https://github.com/this-user-definitely-does-not-exist-12345/nonexistent-repo-98765"},
        headers=headers,
    )
    assert non_existent_resp.status_code == 400
    assert "private" in non_existent_resp.json()["detail"].lower() or "not found" in non_existent_resp.json()["detail"].lower()
