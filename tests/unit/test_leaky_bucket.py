"""Unit tests for the Leaky Bucket rate limiting algorithm."""

import asyncio
import time

import pytest

from app.algorithms.leaky_bucket import LeakyBucketLimiter


class TestLeakyBucketLimiter:

    @pytest.fixture
    def limiter(self):
        return LeakyBucketLimiter(max_requests=3, window_seconds=60)

    @pytest.fixture
    def fast_limiter(self):
        return LeakyBucketLimiter(max_requests=2, window_seconds=2)

    async def test_allows_requests_within_capacity(self, limiter):
        key = f"test-lb-allow-{time.time()}"
        result = await limiter.is_allowed(key)
        assert result.allowed is True
        assert result.limit == 3

    async def test_blocks_when_bucket_full(self, limiter):
        key = f"test-lb-full-{time.time()}"
        for _ in range(3):
            await limiter.is_allowed(key)
        result = await limiter.is_allowed(key)
        assert result.allowed is False

    async def test_bucket_leaks_over_time(self, fast_limiter):
        key = f"test-lb-leak-{time.time()}"
        for _ in range(2):
            await fast_limiter.is_allowed(key)
        exhausted = await fast_limiter.is_allowed(key)
        assert exhausted.allowed is False
        await asyncio.sleep(2.5)  # wait for bucket to drain
        result = await fast_limiter.is_allowed(key)
        assert result.allowed is True

    async def test_algorithm_name(self, limiter):
        assert limiter.algorithm_name == "leaky_bucket"

    async def test_different_keys_are_independent(self, limiter):
        key1 = f"test-lb-k1-{time.time()}"
        key2 = f"test-lb-k2-{time.time()}"
        for _ in range(3):
            await limiter.is_allowed(key1)
        assert (await limiter.is_allowed(key1)).allowed is False
        assert (await limiter.is_allowed(key2)).allowed is True
