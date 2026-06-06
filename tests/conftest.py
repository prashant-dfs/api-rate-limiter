import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.utils.redis_client import get_redis_client


@pytest.fixture
async def client():
    """Async HTTP test client — sends requests directly to FastAPI in memory."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def redis():
    """Provides a Redis connection and cleans up test keys after each test."""
    r = await get_redis_client()
    yield r
    for prefix in (
        "fw:test-",
        "swl:test-",
        "tb:test-",
        "lb:test-",
        "fw:testserver",
        "swl:testserver",
        "tb:testserver",
        "lb:testserver",
        "fw:127",
        "swl:127",
        "tb:127",
        "lb:127",
        "route-limited:",
        "test:",
    ):
        keys = await r.keys(f"{prefix}*")
        if keys:
            await r.delete(*keys)
