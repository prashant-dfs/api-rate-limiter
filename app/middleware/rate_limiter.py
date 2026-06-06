"""
Rate Limiter Middleware
------------------------
Intercepts every HTTP request before it reaches a route handler.
Applies the configured rate limiting algorithm and:
  - Adds X-RateLimit-* headers to every response
  - Returns HTTP 429 Too Many Requests when the limit is exceeded
  - Skips rate limiting for excluded paths (health check, docs, etc.)
"""

import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.algorithms import BaseRateLimiter, create_limiter
from app.config import AlgorithmType, settings


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        algorithm: str | AlgorithmType = settings.rate_limit_algorithm,
        max_requests: int = settings.rate_limit_max_requests,
        window_seconds: int = settings.rate_limit_window_seconds,
        key_func=None,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.limiter: BaseRateLimiter = create_limiter(
            algorithm=algorithm,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )
        self.key_func = key_func or self._default_key_func
        # These paths are never rate-limited
        self.exclude_paths = exclude_paths or [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/health",
        ]

    @staticmethod
    def _default_key_func(request: Request) -> str:
        """
        Derive a unique key for each client.
        Handles reverse proxies by reading X-Forwarded-For first.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        key = self.key_func(request)
        result = await self.limiter.is_allowed(key)

        if not result.allowed:
            retry_after = max(1, int(result.reset_at - time.time()))
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    "limit": result.limit,
                    "remaining": 0,
                    "reset_at": result.reset_at,
                },
                headers={
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(result.reset_at)),
                    "X-RateLimit-Algorithm": self.limiter.algorithm_name,
                    "Retry-After": str(retry_after),
                },
            )

        # Request allowed — forward to the route handler
        response = await call_next(request)

        # Attach informational rate-limit headers
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_at))
        response.headers["X-RateLimit-Algorithm"] = self.limiter.algorithm_name

        return response
