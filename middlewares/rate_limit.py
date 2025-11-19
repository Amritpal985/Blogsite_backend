from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta, timezone
from .logger import send_log

RATE_LIMIT = 100
WINDOW_SECONDS= 60 

request_log = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request:Request,call_next):
        ip = request.client.host
        now = datetime.now(timezone.utc)

        if ip not in request_log:
            request_log[ip] = []
        
        request_log[ip] = [timestamp for timestamp in request_log[ip] if now - timestamp < timedelta(seconds=WINDOW_SECONDS)]   
        if len(request_log[ip]) >= RATE_LIMIT:
            send_log({
                "event": "RATE_LIMIT_BLOCKED",
                "ip": ip,
                "path": request.url.path,
                "method": request.method,
                "timestamp": str(now)
            })
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        request_log[ip].append(now)
        response = await call_next(request)
        return response

