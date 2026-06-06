"""
API Routes
-----------
Defines all public endpoints for the rate limiter demo.
"""

import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.algorithms import ALGORITHM_MAP, create_limiter
from app.config import AlgorithmType

router = APIRouter(prefix="/api", tags=["API"])


@router.get("/health")
async def health_check():
    """Liveness probe — excluded from rate limiting."""
    return {"status": "healthy", "uptime": time.process_time()}


@router.get("/public")
async def public_endpoint():
    """Public endpoint — uses the global rate limiter applied in middleware."""
    return {
        "message": "✅ Public endpoint — default rate limiting applied",
        "timestamp": time.time(),
    }


@router.get("/limited")
async def limited_endpoint(request: Request):
    """
    Stricter per-route rate limit: 5 requests per 30 seconds using Token Bucket.
    Demonstrates how individual routes can have their own independent limits.
    """
    limiter = create_limiter(
        algorithm=AlgorithmType.TOKEN_BUCKET,
        max_requests=5,
        window_seconds=30,
    )
    client_ip = request.client.host if request.client else "unknown"
    # Key includes the route path so this counter is independent of /api/public
    key = f"route-limited:{client_ip}:/api/limited"
    result = await limiter.is_allowed(key)

    if not result.allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": "Stricter rate limit exceeded (5 req / 30s).",
                "remaining": 0,
            },
        )

    return {
        "message": "✅ This endpoint has a stricter rate limit (5 req / 30s)",
        "remaining": result.remaining,
        "timestamp": time.time(),
    }


@router.get("/test/{algorithm}")
async def test_algorithm(algorithm: str, request: Request):
    """Test a specific algorithm by passing its name in the URL."""
    valid_algorithms = [a.value for a in AlgorithmType]

    if algorithm not in valid_algorithms:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Invalid algorithm: '{algorithm}'",
                "available": valid_algorithms,
            },
        )

    limiter = create_limiter(algorithm=algorithm, max_requests=5, window_seconds=60)
    client_ip = request.client.host if request.client else "unknown"
    key = f"test:{algorithm}:{client_ip}"
    result = await limiter.is_allowed(key)

    if not result.allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "algorithm": algorithm,
                "remaining": 0,
            },
        )

    return {
        "message": f"✅ Request allowed using '{algorithm}' algorithm",
        "algorithm": algorithm,
        "remaining": result.remaining,
        "timestamp": time.time(),
    }


@router.get("/algorithms")
async def list_algorithms():
    """List every available rate limiting algorithm with a short description."""
    return {
        "algorithms": [
            {
                "name": algo.value,
                "description": ALGORITHM_MAP[algo].__doc__.strip().split("\n")[0],
            }
            for algo in AlgorithmType
        ]
    }
