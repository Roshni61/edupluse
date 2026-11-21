import time
from typing import Dict, List
from fastapi import Request, HTTPException, status
from app.core.config import settings


class LoginRateLimiter:
    """
    In-memory sliding window rate limiter for login attempts per IP.
    Requirement: 5 attempts/min/IP in production.
    """
    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: Dict[str, List[float]] = {}

    def check_rate_limit(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        cutoff = now - self.window_seconds

        # Clean old timestamps
        history = [ts for ts in self.attempts.get(client_ip, []) if ts > cutoff]
        
        limit = self.max_attempts
        if len(history) >= limit:
            # Over limit
            self.attempts[client_ip] = history
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again after 60 seconds.",
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Record attempt
        history.append(now)
        self.attempts[client_ip] = history

    def reset(self) -> None:
        """Clear rate limit history (useful for tests)."""
        self.attempts.clear()


login_rate_limiter = LoginRateLimiter(max_attempts=5, window_seconds=60)
