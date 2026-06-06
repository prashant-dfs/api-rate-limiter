"""
Sliding Window Log Rate Limiter
--------------------------------
Stores a sorted set of request timestamps in Redis.  For each new request
it removes stale entries outside the window, counts what remains, then
conditionally adds the new timestamp — all atomically via Lua.

  Pros: Most precise — no boundary burst issues.
  Cons: Higher memory usage (stores every timestamp).
"""

import time
import uuid

from app.algorithms.base import BaseRateLimiter, RateLimitResult
from app.utils.redis_client import get_redis_client


class SlidingWindowLogLimiter(BaseRateLimiter):

    @property
    def algorithm_name(self) -> str:
        return "sliding_window_log"

    async def is_allowed(self, key: str) -> RateLimitResult:
        client = await get_redis_client()
        now = time.time()
        window_start = now - self.window_seconds
        redis_key = f"swl:{key}"

        lua_script = """
        local key          = KEYS[1]
        local window_start = tonumber(ARGV[1])
        local now          = tonumber(ARGV[2])
        local max_requests = tonumber(ARGV[3])
        local ttl          = tonumber(ARGV[4])
        local unique_id    = ARGV[5]

        -- Remove entries older than the sliding window
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

        -- Count entries currently in window
        local current = redis.call('ZCARD', key)

        if current < max_requests then
            -- Admit request: add unique timestamp entry
            redis.call('ZADD', key, now, now .. '-' .. unique_id)
            redis.call('EXPIRE', key, ttl)
            return {1, max_requests - current - 1, current + 1}
        else
            redis.call('EXPIRE', key, ttl)
            return {0, 0, current}
        end
        """

        result = await client.eval(
            lua_script,
            1,
            redis_key,
            str(window_start),
            str(now),
            str(self.max_requests),
            str(self.window_seconds + 1),
            str(uuid.uuid4()),
        )

        return RateLimitResult(
            allowed=bool(result[0]),
            remaining=int(result[1]),
            limit=self.max_requests,
            reset_at=now + self.window_seconds,
            current=int(result[2]),
        )
