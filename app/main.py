"""
Application Entry Point
------------------------
Wires together all components:
  - FastAPI app instance
  - Rate limiter middleware (intercepts every request)
  - API routes
  - Startup/shutdown lifecycle (Redis connect / disconnect)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.routes.api import router as api_router
from app.utils.redis_client import close_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager:
      - Code before `yield` runs at startup
      - Code after  `yield` runs at shutdown
    """
    print(f"🚀 {settings.app_name} v{settings.app_version} starting...")
    print(f"📊 Algorithm : {settings.rate_limit_algorithm.value}")
    print(f"⏱️  Window    : {settings.rate_limit_window_seconds}s")
    print(f"🔢 Max reqs  : {settings.rate_limit_max_requests}")
    yield
    print("🛑 Shutting down — closing Redis connection...")
    await close_redis_client()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready API Rate Limiter supporting 4 algorithms",
    lifespan=lifespan,
)

# Global rate limiter middleware — runs before every request
app.add_middleware(
    RateLimiterMiddleware,
    algorithm=settings.rate_limit_algorithm,
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
    exclude_paths=["/", "/docs", "/redoc", "/openapi.json", "/api/health"],
)

# Register all API routes under /api prefix
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint — quick overview of available routes."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "documentation": "/docs",
        "endpoints": {
            "health":         "GET /api/health",
            "public":         "GET /api/public",
            "limited":        "GET /api/limited",
            "test_algorithm": "GET /api/test/{algorithm}",
            "algorithms":     "GET /api/algorithms",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
