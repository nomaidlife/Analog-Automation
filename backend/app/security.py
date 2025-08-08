from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, csp: str|None=None, max_body_bytes: int=1048576):
        super().__init__(app); self.csp=csp; self.max_body_bytes=max_body_bytes
    async def dispatch(self, request, call_next: Callable):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > self.max_body_bytes:
            return Response("Payload too large", status_code=413)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options","nosniff")
        response.headers.setdefault("X-Frame-Options","DENY")
        response.headers.setdefault("Referrer-Policy","strict-origin-when-cross-origin")
        response.headers.setdefault("X-XSS-Protection","0")
        response.headers.setdefault("Permissions-Policy","geolocation=(), microphone=(), camera=()")
        response.headers.setdefault("Strict-Transport-Security","max-age=31536000; includeSubDomains; preload")
        if self.csp: response.headers.setdefault("Content-Security-Policy", self.csp)
        return response
