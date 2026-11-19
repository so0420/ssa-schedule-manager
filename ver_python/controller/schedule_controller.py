import json
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config.database import get_db
from repository.activity_log_repository import ActivityLogRepository
from repository.member_repository import MemberRepository
from repository.schedule_repository import ScheduleRepository
from service.member_service import MemberService
from service.schedule_service import ScheduleService


class ScheduleController:

    def __init__(self, templates: Jinja2Templates):
        self._templates = templates
        self.router = APIRouter(prefix="/schedule")
        self._setup_routes()

    def _build_services(self, db: Session):
        member_repo = MemberRepository(db)
        schedule_repo = ScheduleRepository(db)
        log_repo = ActivityLogRepository(db)
        schedule_svc = ScheduleService(schedule_repo, member_repo, log_repo)
        member_svc = MemberService(member_repo, log_repo, schedule_repo)
        return schedule_svc, member_svc

    def _login_member(self, request: Request):
        return request.session.get("login_member")

    def _setup_routes(self):
        self.router.add_api_route("", self._list, methods=["GET"])
        self.router.add_api_route("/new", self._create_form, methods=["GET"])
        self.router.add_api_route("/new", self._create, methods=["POST"])
        self.router.add_api_route("/{schedule_id}/edit", self._edit_form, methods=["GET"])
        self.router.add_api_route("/{schedule_id}/edit", self._update, methods=["POST"])
        self.router.add_api_route("/{schedule_id}/delete", self._delete, methods=["POST"])
        self.router.add_api_route("/{schedule_id}/toggle", self._toggle, methods=["POST"])

    async def _list(self, request: Request, db: Session = Depends(get_db),
                    keyword: Optional[str] = Query(None),
                    completed: Optional[str] = Query(None)):
        schedule_svc, _ = self._build_services(db)
        completed_bool: Optional[bool] = None
        if completed == "true":
            completed_bool = True
        elif completed == "false":
            completed_bool = False

        if keyword is not None or completed_bool is not None:
            schedules = schedule_svc.search(keyword, completed_bool)
        else:
            schedules = schedule_svc.get_all()

        schedules_json = json.dumps([
            {
                "id": s.id,
                "title": s.title,
                "content": s.content,
                "startAt": s.start_at.isoformat() if s.start_at else None,
                "scheduledAt": s.scheduled_at.isoformat() if s.scheduled_at else None,
                "completed": s.completed,
                "createdBy": s.created_by.name if s.created_by else None,
                "createdAt": s.created_at.isoformat() if s.created_at else None,
            }
            for s in schedules
        ], ensure_ascii=False)

        return self._templates.TemplateResponse("schedule/list.html", {
            "request": request,
            "schedules": schedules,
            "schedules_json": schedules_json,
            "keyword": keyword,
            "completed": completed_bool,
            "message": request.session.pop("message", None),
        })

    async def _create_form(self, request: Request, db: Session = Depends(get_db)):
        _, member_svc = self._build_services(db)
        return self._templates.TemplateResponse("schedule/form.html", {
            "request": request,
            "schedule": None,
            "members": member_svc.get_approved_members(),
            "taggedIds": [],
        })

    async def _create(self, request: Request, db: Session = Depends(get_db),
                      title: str = Form(...), content: Optional[str] = Form(None),
                      startAt: Optional[str] = Form(None),
                      scheduledAt: str = Form(...),
                      taggedMemberIds: Optional[List[int]] = Form(None)):
        schedule_svc, member_svc = self._build_services(db)
        login = self._login_member(request)
        member = member_svc.find_by_id(login["id"])

        start_dt = datetime.fromisoformat(startAt) if startAt and startAt.strip() else None
        scheduled_dt = datetime.fromisoformat(scheduledAt)

        schedule_svc.create(title, content, start_dt, scheduled_dt, taggedMemberIds, member)
        request.session["message"] = "일정이 등록되었습니다."
        db.commit()
        return RedirectResponse(url="/schedule", status_code=302)

    async def _edit_form(self, schedule_id: int, request: Request,
                         db: Session = Depends(get_db)):
        schedule_svc, member_svc = self._build_services(db)
        schedule = schedule_svc.find_by_id(schedule_id)
        tagged_ids = [m.id for m in schedule.tagged_members] if schedule else []
        return self._templates.TemplateResponse("schedule/form.html", {
            "request": request,
            "schedule": schedule,
            "members": member_svc.get_approved_members(),
            "taggedIds": tagged_ids,
        })

    async def _update(self, schedule_id: int, request: Request,
                      db: Session = Depends(get_db),
                      title: str = Form(...), content: Optional[str] = Form(None),
                      startAt: Optional[str] = Form(None),
                      scheduledAt: str = Form(...),
                      taggedMemberIds: Optional[List[int]] = Form(None)):
        schedule_svc, _ = self._build_services(db)
        login = self._login_member(request)

        start_dt = datetime.fromisoformat(startAt) if startAt and startAt.strip() else None
        scheduled_dt = datetime.fromisoformat(scheduledAt)

        schedule_svc.update(schedule_id, title, content, start_dt, scheduled_dt,
                            taggedMemberIds, login["login_id"])
        request.session["message"] = "일정이 수정되었습니다."
        db.commit()
        return RedirectResponse(url="/schedule", status_code=302)

    async def _delete(self, schedule_id: int, request: Request,
                      db: Session = Depends(get_db)):
        schedule_svc, _ = self._build_services(db)
        login = self._login_member(request)
        schedule_svc.delete(schedule_id, login["login_id"])
        request.session["message"] = "일정이 삭제되었습니다."
        db.commit()
        return RedirectResponse(url="/schedule", status_code=302)

    async def _toggle(self, schedule_id: int, request: Request,
                      db: Session = Depends(get_db)):
        schedule_svc, _ = self._build_services(db)
        login = self._login_member(request)
        schedule_svc.toggle_complete(schedule_id, login["login_id"])
        db.commit()
        return RedirectResponse(url="/schedule", status_code=302)
