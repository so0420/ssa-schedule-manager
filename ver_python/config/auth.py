"""
인증 미들웨어 모듈.
로그인하지 않은 사용자가 보호된 페이지에 접근하면 로그인 페이지로 리다이렉트한다.
Java의 LoginInterceptor (HandlerInterceptor)에 해당한다.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

# 인증 없이 접근 가능한 URL 접두사 목록
# Java의 WebConfig.addInterceptors()에서 excludePathPatterns로 설정한 것과 동일하다.
EXCLUDE_PREFIXES = ("/auth", "/service", "/static")


class LoginMiddleware(BaseHTTPMiddleware):
    """
    로그인 인증 미들웨어.
    모든 HTTP 요청을 가로채서 세션에 로그인 정보가 있는지 확인한다.
    로그인 정보가 없으면 로그인 페이지로 리다이렉트한다.

    Java의 LoginInterceptor.preHandle()에 해당한다:
    - preHandle()에서 session.getAttribute("loginMember") 체크
    - null이면 /auth/login으로 redirect

    Spring Security를 사용하지 않고 직접 구현한 가벼운 인증 방식이다.
    """

    async def dispatch(self, request: Request, call_next):
        """
        요청을 가로채서 인증을 확인한다.
        Args:
            request: HTTP 요청 객체
            call_next: 다음 미들웨어/라우터 호출 함수
        Returns:
            인증 성공 시 원래 응답, 실패 시 로그인 페이지 리다이렉트
        """
        path = request.url.path

        # 제외 경로 체크 — 로그인/회원가입/정적 파일은 인증 불필요
        if any(path.startswith(p) for p in EXCLUDE_PREFIXES):
            return await call_next(request)

        # 세션에서 로그인 정보 확인
        login_member = request.session.get("login_member")
        if login_member is None:
            # 미로그인 상태 → 로그인 페이지로 리다이렉트
            return RedirectResponse(url="/auth/login", status_code=302)

        # 인증 통과 → 원래 요청 처리 계속
        return await call_next(request)
