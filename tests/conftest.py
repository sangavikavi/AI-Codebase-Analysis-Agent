import os
import sys
from pathlib import Path
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure test settings use a clean test database
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_codebase_analysis.db"
os.environ["APP_ENV"] = "test"

from backend.database import Base, engine, AsyncSessionLocal
from backend.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Cleanup test db file
    db_file = Path("./test_codebase_analysis.db")
    if db_file.exists():
        try:
            db_file.unlink()
        except Exception:
            pass


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
