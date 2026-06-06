"""Unit tests for the Sliding Window Log rate limiting algorithm."""

import asyncio
import time

import pytest

from app.algorithms.sliding_window_log import SlidingWindowLogLimiter


class TestSlidingWindowLogLimiter:

    @pytest.fixture
    def limiter(self):
        return SlidingWindowLogLimiter(max_requests=3, window_seconds=60)

    @pytest.fixture
    def fast_limiter(self):
        return SlidingWindowLogLimiter(max_requests=2, window_seconds=2)

    async def test_allows_requests_within_limit(self, limiter):
        key = f"test-swl-allow-{time.time()}"
        result = await limiter.is_allowed(key)
        assert result.allowed is True
        assert result.limit == 3

    async def test_blocks_after_exceeding_limit(self, limiter):
        key = f"test-swl-block-{time.time()}"
        for _ in range(3):
            await limiter.is_allowed(key)
        result = await limiter.is_allowed(key)
        assert result.allowed is False

    async def test_window_slides_and_allows_new_requests(self, fast_limiter):
        key = f"test-swl-slide-{time.time()}"
        for _ in range(2):
            await fast_limiter.is_allowed(key)
        exhausted = await fast_limiter.is_allowed(key)
        assert exhausted.allowed is False
        await asyncio.sleep(2.5)  # wait for old entries to leave the window
        result = await fast_limiter.is_allowed(key)
        assert result.allowed is True

    async def test_algorithm_name(self, limiter):
        assert limiter.algorithm_name == "sliding_window_log"

    async def test_different_keys_are_independent(self, limiter):
        key1 = f"test-swl-k1-{time.time()}"
        key2 = f"test-swl-k2-{time.time()}"
        for _ in range(3):
            await limiter.is_allowed(key1)
        assert (await limiter.is_allowed(key1)).allowed is False
        assert (await limiter.is_allowed(key2)).allowed is True
