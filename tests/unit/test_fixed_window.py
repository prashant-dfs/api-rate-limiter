"""Unit tests for the Fixed Window rate limiting algorithm."""

import time

import pytest

from app.algorithms.fixed_window import FixedWindowLimiter


class TestFixedWindowLimiter:
    @pytest.fixture
    def limiter(self):
        return FixedWindowLimiter(max_requests=3, window_seconds=60)

    async def test_allows_first_request(self, limiter):
        key = f"test-fw-first-{time.time()}"
        result = await limiter.is_allowed(key)
        assert result.allowed is True
        assert result.remaining == 2
        assert result.limit == 3

    async def test_remaining_decreases_correctly(self, limiter):
        key = f"test-fw-remaining-{time.time()}"
        r1 = await limiter.is_allowed(key)
        assert r1.remaining == 2
        r2 = await limiter.is_allowed(key)
        assert r2.remaining == 1
        r3 = await limiter.is_allowed(key)
        assert r3.remaining == 0

    async def test_blocks_after_exceeding_limit(self, limiter):
        key = f"test-fw-block-{time.time()}"
        for _ in range(3):
            await limiter.is_allowed(key)
        result = await limiter.is_allowed(key)
        assert result.allowed is False
        assert result.remaining == 0

    async def test_result_has_required_fields(self, limiter):
        key = f"test-fw-fields-{time.time()}"
        result = await limiter.is_allowed(key)
        assert hasattr(result, "allowed")
        assert hasattr(result, "remaining")
        assert hasattr(result, "limit")
        assert hasattr(result, "reset_at")
        assert hasattr(result, "current")

    async def test_algorithm_name(self, limiter):
        assert limiter.algorithm_name == "fixed_window"

    async def test_different_keys_are_independent(self, limiter):
        key1 = f"test-fw-k1-{time.time()}"
        key2 = f"test-fw-k2-{time.time()}"
        for _ in range(3):
            await limiter.is_allowed(key1)
        assert (await limiter.is_allowed(key1)).allowed is False
        assert (await limiter.is_allowed(key2)).allowed is True
