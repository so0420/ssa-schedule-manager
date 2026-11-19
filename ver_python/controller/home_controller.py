from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config.database import get_db
from repository.activity_log_repository import ActivityLogRepository
from repository.member_repository import MemberRepository
from repository.schedule_repository import ScheduleRepository
from service.schedule_service import ScheduleService


class HomeController:

    def __init__(self, templates: Jinja2Templates):
        self._templates = templates
        self.router = APIRouter()
        self._setup_routes()

    def _build_service(self, db: Session) -> ScheduleService:
        return ScheduleService(
            ScheduleRepository(db), MemberRepository(db), ActivityLogRepository(db)
        )

    def _setup_routes(self):
        self.router.add_api_route("/", self._home, methods=["GET"])

    async def _home(self, request: Request, db: Session = Depends(get_db)):
        svc = self._build_service(db)
        upcoming = svc.get_upcoming()
        return self._templates.TemplateResponse("index.html", {
            "request": request,
            "upcomingSchedules": upcoming,
            "message": request.session.pop("message", None),
        })
