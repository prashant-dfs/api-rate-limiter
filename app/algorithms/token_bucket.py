"""
Token Bucket Rate Limiter
--------------------------
A bucket holds tokens up to `capacity`.  Tokens refill at a steady rate.
Each request consumes one token.  When the bucket is empty, requests are
rejected until tokens accumulate again.

  Pros: Allows controlled bursts; most popular algorithm in production
        (used by AWS, Google, Stripe).
  Cons: Slightly more complex — stores two values per user in Redis.
"""

import time

from app.algorithms.base import BaseRateLimiter, RateLimitResult
from app.utils.redis_client import get_redis_client


class TokenBucketLimiter(BaseRateLimiter):
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(max_requests, window_seconds)
        self.capacity = max_requests
        self.refill_rate = max_requests / window_seconds  # tokens added per second

    @property
    def algorithm_name(self) -> str:
        return "token_bucket"

    async def is_allowed(self, key: str) -> RateLimitResult:
        client = await get_redis_client()
        now = time.time()
        redis_key = f"tb:{key}"

        lua_script = """
        local key         = KEYS[1]
        local capacity    = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now         = tonumber(ARGV[3])
        local ttl         = tonumber(ARGV[4])

        local bucket      = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens      = tonumber(bucket[1])
        local last_refill = tonumber(bucket[2])

        -- Initialise bucket on first request
        if tokens == nil then
            tokens      = capacity
            last_refill = now
        end

        -- Refill tokens based on elapsed time (capped at capacity)
        local elapsed       = now - last_refill
        local tokens_to_add = elapsed * refill_rate
        tokens = math.min(capacity, tokens + tokens_to_add)

        local allowed   = 0
        local remaining = math.floor(tokens)

        if tokens >= 1 then
            tokens    = tokens - 1
            remaining = math.floor(tokens)
            allowed   = 1
        end

        -- Persist updated state
        redis.call('HMSET', key, 'tokens', tostring(tokens), 'last_refill', tostring(now))
        redis.call('EXPIRE', key, ttl)

        return {allowed, remaining, capacity}
        """

        result = await client.eval(
            lua_script,
            1,
            redis_key,
            str(self.capacity),
            str(self.refill_rate),
            str(now),
            str(int(self.capacity / self.refill_rate) + 2),
        )

        remaining = int(result[1])
        return RateLimitResult(
            allowed=bool(result[0]),
            remaining=remaining,
            limit=self.capacity,
            reset_at=now + (self.capacity - remaining) / self.refill_rate,
            current=self.capacity - remaining,
        )
