"""
Fixed Window Rate Limiter
--------------------------
Divides time into fixed-size windows and counts requests per window.

  Pros: Simple, low memory usage.
  Cons: Allows a burst of 2x the limit at window boundaries.

  Example (limit=5, window=60s):
    0:55 → 5 requests allowed (fills window)
    1:01 → 5 more allowed (new window)  ← 10 requests in ~6 seconds!
"""

import time

from app.algorithms.base import BaseRateLimiter, RateLimitResult
from app.utils.redis_client import get_redis_client


class FixedWindowLimiter(BaseRateLimiter):
    @property
    def algorithm_name(self) -> str:
        return "fixed_window"

    async def is_allowed(self, key: str) -> RateLimitResult:
        client = await get_redis_client()
        now = time.time()
        window_id = int(now // self.window_seconds)
        redis_key = f"fw:{key}:{window_id}"

        # Atomic Lua script: increment counter + set TTL in one step
        # This prevents race conditions between concurrent requests
        lua_script = """
        local current = redis.call('INCR', KEYS[1])
        if current == 1 then
            redis.call('EXPIRE', KEYS[1], ARGV[1])
        end
        return current
        """

        current = int(await client.eval(lua_script, 1, redis_key, self.window_seconds + 1))
        allowed = current <= self.max_requests
        reset_at = (window_id + 1) * self.window_seconds

        return RateLimitResult(
            allowed=allowed,
            remaining=max(0, self.max_requests - current),
            limit=self.max_requests,
            reset_at=reset_at,
            current=current,
        )
