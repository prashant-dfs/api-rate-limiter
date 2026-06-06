"""
Shared test fixtures
---------------------
conftest.py is automatically loaded by pytest before running any tests.
Fixtures here are available to all test files without explicit imports.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.utils.redis_client import close_redis_client, get_redis_client


@pytest.fixture
async def client():
    """
    Async HTTP test client.
    Sends requests directly to the FastAPI app in memory — no real server needed.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def redis():
    """
    Provides a Redis connection and cleans up test keys after each test,
    so tests never interfere with each other.
    """
    r = await get_redis_client()
    yield r
    # Teardown: remove all keys created by tests
    for prefix in ("fw:test-", "swl:test-", "tb:test-", "lb:test-"):
        keys = await r.keys(f"{prefix}*")
        if keys:
            await r.delete(*keys)


@pytest.fixture(autouse=True)
async def cleanup_redis():
    """Runs automatically after every test — ensures the Redis client is closed."""
    yield
    await close_redis_client()
