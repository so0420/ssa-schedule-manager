from typing import Optional

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config.database import get_db
from repository.activity_log_repository import ActivityLogRepository
from repository.member_repository import MemberRepository
from repository.schedule_repository import ScheduleRepository
from service.member_service import MemberService


class MemberController:

    def __init__(self, templates: Jinja2Templates):
        self._templates = templates
        self.router = APIRouter(prefix="/member")
        self._setup_routes()

    def _build_service(self, db: Session) -> MemberService:
        return MemberService(
            MemberRepository(db), ActivityLogRepository(db), ScheduleRepository(db)
        )

    def _login_member(self, request: Request):
        return request.session.get("login_member")

    def _setup_routes(self):
        self.router.add_api_route("/profile", self._profile, methods=["GET"])
        self.router.add_api_route("/update-name", self._update_name, methods=["POST"])
        self.router.add_api_route("/update-password", self._update_password, methods=["POST"])
        self.router.add_api_route("/update-notification", self._update_notification, methods=["POST"])
        self.router.add_api_route("/delete", self._delete_member, methods=["POST"])

    async def _profile(self, request: Request, db: Session = Depends(get_db)):
        login = self._login_member(request)
        svc = self._build_service(db)
        member = svc.find_by_id(login["id"])
        if not member:
            request.session.clear()
            return RedirectResponse(url="/auth/login", status_code=302)
        return self._templates.TemplateResponse("member/profile.html", {
            "request": request,
            "member": member,
            "message": request.session.pop("message", None),
            "error": request.session.pop("error", None),
        })

    async def _update_name(self, request: Request, db: Session = Depends(get_db),
                           name: str = Form(...)):
        login = self._login_member(request)
        svc = self._build_service(db)
        svc.update_name(login["id"], name)
        login["name"] = name
        request.session["login_member"] = login
        request.session["message"] = "사용자명이 변경되었습니다."
        db.commit()
        return RedirectResponse(url="/member/profile", status_code=302)

    async def _update_password(self, request: Request, db: Session = Depends(get_db),
                               currentPassword: str = Form(...),
                               newPassword: str = Form(...)):
        login = self._login_member(request)
        svc = self._build_service(db)
        success = svc.update_password(login["id"], currentPassword, newPassword)
        if success:
            request.session["message"] = "비밀번호가 변경되었습니다."
        else:
            request.session["error"] = "현재 비밀번호가 일치하지 않습니다."
        db.commit()
        return RedirectResponse(url="/member/profile", status_code=302)

    async def _update_notification(self, request: Request, db: Session = Depends(get_db),
                                   notificationEnabled: Optional[str] = Form(None),
                                   webhookUrl: Optional[str] = Form(None)):
        login = self._login_member(request)
        svc = self._build_service(db)
        enabled = notificationEnabled == "true"
        svc.update_notification(login["id"], enabled, webhookUrl)
        login["notification_enabled"] = enabled
        login["webhook_url"] = webhookUrl
        request.session["login_member"] = login
        request.session["message"] = "알림 설정이 변경되었습니다."
        db.commit()
        return RedirectResponse(url="/member/profile", status_code=302)

    async def _delete_member(self, request: Request, db: Session = Depends(get_db)):
        login = self._login_member(request)
        svc = self._build_service(db)
        svc.delete_member(login["id"])
        request.session.clear()
        db.commit()
        return RedirectResponse(url="/auth/login", status_code=302)
