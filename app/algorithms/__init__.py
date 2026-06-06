from app.algorithms.base import BaseRateLimiter, RateLimitResult
from app.algorithms.fixed_window import FixedWindowLimiter
from app.algorithms.leaky_bucket import LeakyBucketLimiter
from app.algorithms.sliding_window_log import SlidingWindowLogLimiter
from app.algorithms.token_bucket import TokenBucketLimiter
from app.config import AlgorithmType

ALGORITHM_MAP: dict[AlgorithmType, type[BaseRateLimiter]] = {
    AlgorithmType.FIXED_WINDOW: FixedWindowLimiter,
    AlgorithmType.SLIDING_WINDOW_LOG: SlidingWindowLogLimiter,
    AlgorithmType.TOKEN_BUCKET: TokenBucketLimiter,
    AlgorithmType.LEAKY_BUCKET: LeakyBucketLimiter,
}


def create_limiter(
    algorithm: str | AlgorithmType,
    max_requests: int = 10,
    window_seconds: int = 60,
) -> BaseRateLimiter:
    """Factory function — creates the right rate limiter by algorithm name."""
    algo_key = AlgorithmType(algorithm) if isinstance(algorithm, str) else algorithm
    limiter_class = ALGORITHM_MAP.get(algo_key)

    if limiter_class is None:
        available = ", ".join(a.value for a in AlgorithmType)
        raise ValueError(f"Unknown algorithm: '{algorithm}'. Available: {available}")

    return limiter_class(max_requests=max_requests, window_seconds=window_seconds)


__all__ = [
    "BaseRateLimiter",
    "RateLimitResult",
    "FixedWindowLimiter",
    "SlidingWindowLogLimiter",
    "TokenBucketLimiter",
    "LeakyBucketLimiter",
    "create_limiter",
    "ALGORITHM_MAP",
]
