import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class DeviceRateLimiter:
    def __init__(self):
        self._records = defaultdict(list)
        self._rules = {
            "/api/auth/login": (5, 60),
            "/api/auth/register": (3, 300),
            "/api/auth/forgot-password": (3, 300),
            "/api/auth/reset-password": (5, 300),
            "/api/ai/chat": (20, 60),
        }
        self._default_rule = (120, 60)

    def is_rate_limited(self, key: str, path: str) -> tuple[bool, int]:
        now = time.time()
        max_requests, window_seconds = self._rules.get(path, self._default_rule)
        record_key = f"{key}:{path}"
        timestamps = self._records[record_key]
        valid_timestamps = [ts for ts in timestamps if now - ts < window_seconds]
        self._records[record_key] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            retry_after = int(window_seconds - (now - valid_timestamps[0])) + 1
            return True, max(1, retry_after)

        self._records[record_key].append(now)
        return False, 0

limiter_instance = DeviceRateLimiter()

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        device_fp = request.headers.get("X-Device-Fingerprint")
        client_ip = request.client.host if request.client else "unknown"
        rate_key = f"dev:{device_fp}" if device_fp else f"ip:{client_ip}"

        is_limited, retry_after = limiter_instance.is_rate_limited(rate_key, path)
        if is_limited:
            content = {
                "detail": "Thiết bị của bạn đã gửi quá nhiều yêu cầu trong thời gian ngắn. Vui lòng thử lại sau ít phút.",
                "retry_after_seconds": retry_after
            }
            return JSONResponse(
                status_code=429,
                content=content,
                headers={"Retry-After": str(retry_after)}
            )

        return await call_next(request)
