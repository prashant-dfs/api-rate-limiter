from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RateLimitResult:
    """Standardised result returned by every rate limiting algorithm."""

    allowed: bool       # Can this request proceed?
    remaining: int      # How many requests are left in this window?
    limit: int          # What is the maximum allowed per window?
    reset_at: float     # Unix timestamp when the window resets
    current: int        # How many requests have been made so far?


class BaseRateLimiter(ABC):
    """Abstract base class — every algorithm must implement this contract."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    @abstractmethod
    async def is_allowed(self, key: str) -> RateLimitResult:
        """Check whether a request from `key` is permitted."""
        ...

    @property
    @abstractmethod
    def algorithm_name(self) -> str:
        """Return the identifier string for this algorithm."""
        ...
