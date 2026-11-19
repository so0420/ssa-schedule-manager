from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config.database import get_db
from entity.role import Role
from repository.activity_log_repository import ActivityLogRepository
from repository.member_repository import MemberRepository
from repository.schedule_repository import ScheduleRepository
from service.member_service import MemberService


class AdminController:

    def __init__(self, templates: Jinja2Templates):
        self._templates = templates
        self.router = APIRouter(prefix="/admin")
        self._setup_routes()

    def _build_service(self, db: Session) -> MemberService:
        return MemberService(
            MemberRepository(db), ActivityLogRepository(db), ScheduleRepository(db)
        )

    def _login_member(self, request: Request):
        return request.session.get("login_member")

    def _is_admin(self, request: Request) -> bool:
        login = self._login_member(request)
        return login is not None and login.get("role") == Role.ADMIN.value

    def _setup_routes(self):
        self.router.add_api_route("/members", self._members, methods=["GET"])
        self.router.add_api_route("/members/{member_id}/approve", self._approve, methods=["POST"])
        self.router.add_api_route("/members/{member_id}/reject", self._reject, methods=["POST"])
        self.router.add_api_route("/members/{member_id}/kick", self._kick, methods=["POST"])
        self.router.add_api_route("/logs", self._logs, methods=["GET"])

    async def _members(self, request: Request, db: Session = Depends(get_db)):
        if not self._is_admin(request):
            return RedirectResponse(url="/", status_code=302)
        svc = self._build_service(db)
        return self._templates.TemplateResponse("admin/members.html", {
            "request": request,
            "pendingMembers": svc.get_pending_members(),
            "approvedMembers": svc.get_approved_members(),
            "message": request.session.pop("message", None),
        })

    async def _approve(self, member_id: int, request: Request,
                       db: Session = Depends(get_db)):
        if not self._is_admin(request):
            return RedirectResponse(url="/", status_code=302)
        login = self._login_member(request)
        svc = self._build_service(db)
        svc.approve_member(member_id, login["name"])
        request.session["message"] = "회원이 승인되었습니다."
        db.commit()
        return RedirectResponse(url="/admin/members", status_code=302)

    async def _reject(self, member_id: int, request: Request,
                      db: Session = Depends(get_db)):
        if not self._is_admin(request):
            return RedirectResponse(url="/", status_code=302)
        login = self._login_member(request)
        svc = self._build_service(db)
        svc.reject_member(member_id, login["name"])
        request.session["message"] = "회원이 거절되었습니다."
        db.commit()
        return RedirectResponse(url="/admin/members", status_code=302)

    async def _kick(self, member_id: int, request: Request,
                    db: Session = Depends(get_db)):
        if not self._is_admin(request):
            return RedirectResponse(url="/", status_code=302)
        login = self._login_member(request)
        svc = self._build_service(db)
        svc.kick_member(member_id, login["name"])
        request.session["message"] = "멤버가 추방되었습니다."
        db.commit()
        return RedirectResponse(url="/admin/members", status_code=302)

    async def _logs(self, request: Request, db: Session = Depends(get_db)):
        if not self._is_admin(request):
            return RedirectResponse(url="/", status_code=302)
        svc = self._build_service(db)
        return self._templates.TemplateResponse("admin/logs.html", {
            "request": request,
            "logs": svc.get_all_logs(),
        })
