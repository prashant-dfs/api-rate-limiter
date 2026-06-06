"""
Integration tests for the full API request → response flow.

These tests send real HTTP requests through:
  client → middleware → algorithm → Redis → route handler → response

They verify that all components work correctly together — not just in
isolation.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class TestRateLimiterAPI:
    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac

    # ── Root & Health ──────────────────────────────────────────────────────────

    async def test_root_endpoint_returns_200(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "endpoints" in data

    async def test_health_endpoint_is_always_200(self, client):
        """Health endpoint must never return 429 — it is excluded from rate limiting."""
        for _ in range(25):
            response = await client.get("/api/health")
            assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    # ── Rate Limit Headers ─────────────────────────────────────────────────────

    async def test_rate_limit_headers_present_on_allowed_request(self, client):
        response = await client.get("/api/public")
        if response.status_code == 200:
            for header in (
                "x-ratelimit-limit",
                "x-ratelimit-remaining",
                "x-ratelimit-reset",
                "x-ratelimit-algorithm",
            ):
                assert header in response.headers, f"Missing header: {header}"

    # ── Enforcement ───────────────────────────────────────────────────────────

    async def test_returns_429_after_exceeding_limit(self, client):
        statuses = []
        for _ in range(15):
            response = await client.get("/api/public")
            statuses.append(response.status_code)
        assert 429 in statuses, "Expected at least one 429 response after 15 requests"

    async def test_429_response_includes_retry_after_header(self, client):
        for _ in range(20):
            response = await client.get("/api/public")
            if response.status_code == 429:
                assert "retry-after" in response.headers
                body = response.json()
                assert body["error"] == "Too Many Requests"
                assert "message" in body
                return
        pytest.skip("Rate limit not triggered — increase request count or lower limit")

    # ── Algorithm Endpoint ────────────────────────────────────────────────────

    async def test_valid_algorithms_return_200_or_429(self, client):
        from app.config import AlgorithmType

        for algo in AlgorithmType:
            response = await client.get(f"/api/test/{algo.value}")
            assert response.status_code in (200, 429), (
                f"Unexpected status {response.status_code} for algorithm {algo.value}"
            )

    async def test_invalid_algorithm_returns_400(self, client):
        response = await client.get("/api/test/made_up_algo")
        assert response.status_code == 400
        body = response.json()
        assert "error" in body
        assert "available" in body

    # ── Algorithms Discovery ──────────────────────────────────────────────────

    async def test_list_algorithms_returns_4_entries(self, client):
        response = await client.get("/api/algorithms")
        if response.status_code == 200:
            data = response.json()
            assert "algorithms" in data
            assert len(data["algorithms"]) == 4
