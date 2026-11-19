"""
홈(대시보드) 컨트롤러 모듈.
메인 페이지(대시보드)를 처리한다.
1주일 내 다가오는 일정 목록을 보여준다.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config.database import get_db
from repository.activity_log_repository import ActivityLogRepository
from repository.member_repository import MemberRepository
from repository.schedule_repository import ScheduleRepository
from service.schedule_service import ScheduleService


class HomeController:
    """
    대시보드 페이지를 처리하는 컨트롤러 클래스.
    루트 경로(/)의 GET 요청을 처리한다.
    """

    def __init__(self, templates: Jinja2Templates):
        """
        생성자: 템플릿 엔진을 주입받고, 라우터와 서비스를 초기화한다.
        Args:
            templates: Jinja2 템플릿 엔진
        """
        self._templates = templates
        self._schedule_svc = ScheduleService(
            ScheduleRepository(), MemberRepository(), ActivityLogRepository()
        )
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """URL-메서드 매핑을 등록한다."""
        self.router.add_api_route("/", self._home, methods=["GET"])

    async def _home(self, request: Request, db: Session = Depends(get_db)):
        """
        GET / — 대시보드 페이지를 렌더링한다.
        1주일 내 다가오는 미완료 일정을 조회하여 화면에 전달한다.
        """
        upcoming = self._schedule_svc.get_upcoming(db)
        return self._templates.TemplateResponse("index.html", {
            "request": request,
            "upcomingSchedules": upcoming,
            "message": request.session.pop("message", None),
        })
