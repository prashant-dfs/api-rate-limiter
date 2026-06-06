"""
Leaky Bucket Rate Limiter
--------------------------
Requests "fill" the bucket; the bucket "leaks" at a constant rate.
If the bucket overflows, the request is rejected.  This guarantees a
perfectly smooth, constant output rate with zero burst tolerance.

  Pros: Smooth output rate; great for protecting downstream services.
  Cons: No bursting allowed — may feel too strict for end users.
"""

import time

from app.algorithms.base import BaseRateLimiter, RateLimitResult
from app.utils.redis_client import get_redis_client


class LeakyBucketLimiter(BaseRateLimiter):
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(max_requests, window_seconds)
        self.capacity = max_requests
        self.leak_rate = max_requests / window_seconds  # requests leaked per second

    @property
    def algorithm_name(self) -> str:
        return "leaky_bucket"

    async def is_allowed(self, key: str) -> RateLimitResult:
        client = await get_redis_client()
        now = time.time()
        redis_key = f"lb:{key}"

        lua_script = """
        local key       = KEYS[1]
        local capacity  = tonumber(ARGV[1])
        local leak_rate = tonumber(ARGV[2])
        local now       = tonumber(ARGV[3])
        local ttl       = tonumber(ARGV[4])

        local bucket    = redis.call('HMGET', key, 'water', 'last_leak')
        local water     = tonumber(bucket[1])
        local last_leak = tonumber(bucket[2])

        -- Initialise on first request
        if water == nil then
            water     = 0
            last_leak = now
        end

        -- Drain water based on elapsed time (never below 0)
        local elapsed = now - last_leak
        local leaked  = elapsed * leak_rate
        water = math.max(0, water - leaked)

        local allowed   = 0
        local remaining = math.floor(capacity - water)

        if water < capacity then
            water     = water + 1
            allowed   = 1
            remaining = math.floor(capacity - water)
        end

        redis.call('HMSET', key, 'water', tostring(water), 'last_leak', tostring(now))
        redis.call('EXPIRE', key, ttl)

        return {allowed, remaining, capacity}
        """

        result = await client.eval(
            lua_script,
            1,
            redis_key,
            str(self.capacity),
            str(self.leak_rate),
            str(now),
            str(int(self.capacity / self.leak_rate) + 2),
        )

        remaining = int(result[1])
        return RateLimitResult(
            allowed=bool(result[0]),
            remaining=remaining,
            limit=self.capacity,
            reset_at=now + self.capacity / self.leak_rate,
            current=self.capacity - remaining,
        )
