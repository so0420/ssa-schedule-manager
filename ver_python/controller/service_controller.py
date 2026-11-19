"""
서비스 정보 컨트롤러 모듈.
이용약관, 개인정보처리방침 페이지를 처리한다.
유스케이스: B2(이용약관 열람), B3(개인정보처리방침 열람)
"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


class ServiceController:
    """
    서비스 정보 페이지를 처리하는 컨트롤러 클래스.
    /service 접두사를 가진 라우트들을 관리한다.
    비즈니스 로직 없이 정적 페이지만 렌더링한다.
    """

    def __init__(self, templates: Jinja2Templates):
        """
        생성자: 템플릿 엔진을 주입받는다.
        Args:
            templates: Jinja2 템플릿 엔진
        """
        self._templates = templates
        self.router = APIRouter(prefix="/service")
        self._setup_routes()

    def _setup_routes(self):
        """URL-메서드 매핑을 등록한다."""
        self.router.add_api_route("/terms", self._terms, methods=["GET"])
        self.router.add_api_route("/privacy", self._privacy, methods=["GET"])

    async def _terms(self, request: Request):
        """GET /service/terms — 이용약관 페이지를 렌더링한다 (유스케이스 B2)."""
        return self._templates.TemplateResponse("service/terms.html", {"request": request})

    async def _privacy(self, request: Request):
        """GET /service/privacy — 개인정보처리방침 페이지를 렌더링한다 (유스케이스 B3)."""
        return self._templates.TemplateResponse("service/privacy.html", {"request": request})
