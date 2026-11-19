from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

EXCLUDE_PREFIXES = ("/auth", "/service", "/static")


class LoginMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in EXCLUDE_PREFIXES):
            return await call_next(request)
        login_member = request.session.get("login_member")
        if login_member is None:
            return RedirectResponse(url="/auth/login", status_code=302)
        return await call_next(request)
