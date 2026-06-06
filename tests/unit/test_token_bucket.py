"""Unit tests for the Token Bucket rate limiting algorithm."""

import asyncio
import time

import pytest

from app.algorithms.token_bucket import TokenBucketLimiter


class TestTokenBucketLimiter:
    @pytest.fixture
    def limiter(self):
        return TokenBucketLimiter(max_requests=5, window_seconds=60)

    @pytest.fixture
    def fast_limiter(self):
        # Refills fully in ~3 seconds — safe for timed tests
        return TokenBucketLimiter(max_requests=3, window_seconds=3)

    async def test_allows_requests_within_limit(self, limiter):
        key = f"test-tb-allow-{time.time()}"
        result = await limiter.is_allowed(key)
        assert result.allowed is True
        assert result.remaining <= 5
        assert result.limit == 5

    async def test_blocks_requests_exceeding_limit(self, limiter):
        key = f"test-tb-block-{time.time()}"
        for _ in range(5):
            result = await limiter.is_allowed(key)
            assert result.allowed is True
        result = await limiter.is_allowed(key)
        assert result.allowed is False
        assert result.remaining == 0

    async def test_tokens_refill_over_time(self, fast_limiter):
        key = f"test-tb-refill-{time.time()}"
        for _ in range(3):
            await fast_limiter.is_allowed(key)
        exhausted = await fast_limiter.is_allowed(key)
        assert exhausted.allowed is False
        await asyncio.sleep(3.5)  # wait for full refill
        refilled = await fast_limiter.is_allowed(key)
        assert refilled.allowed is True

    async def test_result_has_required_fields(self, limiter):
        key = f"test-tb-fields-{time.time()}"
        result = await limiter.is_allowed(key)
        for field in ("allowed", "remaining", "limit", "reset_at", "current"):
            assert hasattr(result, field)
        assert isinstance(result.remaining, int)
        assert isinstance(result.limit, int)

    async def test_algorithm_name(self, limiter):
        assert limiter.algorithm_name == "token_bucket"

    async def test_different_keys_are_independent(self, limiter):
        key1 = f"test-tb-k1-{time.time()}"
        key2 = f"test-tb-k2-{time.time()}"
        for _ in range(5):
            await limiter.is_allowed(key1)
        assert (await limiter.is_allowed(key1)).allowed is False
        assert (await limiter.is_allowed(key2)).allowed is True
