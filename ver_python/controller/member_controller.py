"""
회원(Member) 컨트롤러 모듈.
프로필 조회, 사용자명/비밀번호 변경, 알림 설정, 회원 탈퇴를 처리한다.
유스케이스: A2(개인정보 수정), A5(회원 탈퇴), D1(알림 설정)
"""

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
    """
    회원 프로필 관련 HTTP 요청을 처리하는 컨트롤러 클래스.
    /member 접두사를 가진 라우트들을 관리한다.
    """

    def __init__(self, templates: Jinja2Templates):
        """
        생성자: 템플릿 엔진을 주입받고, 라우터와 서비스를 초기화한다.
        Args:
            templates: Jinja2 템플릿 엔진
        """
        self._templates = templates
        self._member_svc = MemberService(
            MemberRepository(), ActivityLogRepository(), ScheduleRepository()
        )
        self.router = APIRouter(prefix="/member")
        self._setup_routes()

    def _login_member(self, request: Request):
        """세션에서 로그인된 회원 정보(dict)를 가져온다."""
        return request.session.get("login_member")

    def _setup_routes(self):
        """URL-메서드 매핑을 등록한다."""
        self.router.add_api_route("/profile", self._profile, methods=["GET"])
        self.router.add_api_route("/update-name", self._update_name, methods=["POST"])
        self.router.add_api_route("/update-password", self._update_password, methods=["POST"])
        self.router.add_api_route("/update-notification", self._update_notification, methods=["POST"])
        self.router.add_api_route("/delete", self._delete_member, methods=["POST"])

    # ==================== A2. 프로필 조회 ====================

    async def _profile(self, request: Request, db: Session = Depends(get_db)):
        """
        GET /member/profile — 프로필 페이지를 렌더링한다.
        DB에서 최신 회원 정보를 조회하여 화면에 전달한다.
        """
        login = self._login_member(request)
        member = self._member_svc.find_by_id(db, login["id"])
        if not member:
            request.session.clear()
            return RedirectResponse(url="/auth/login", status_code=302)
        return self._templates.TemplateResponse("member/profile.html", {
            "request": request,
            "member": member,
            "message": request.session.pop("message", None),
            "error": request.session.pop("error", None),
        })

    # ==================== A2-1. 사용자명 변경 ====================

    async def _update_name(self, request: Request, db: Session = Depends(get_db),
                           name: str = Form(...)):
        """POST /member/update-name — 사용자 이름을 변경한다."""
        login = self._login_member(request)
        self._member_svc.update_name(db, login["id"], name)
        login["name"] = name
        request.session["login_member"] = login
        request.session["message"] = "사용자명이 변경되었습니다."
        db.commit()
        return RedirectResponse(url="/member/profile", status_code=302)

    # ==================== A2-2. 비밀번호 변경 ====================

    async def _update_password(self, request: Request, db: Session = Depends(get_db),
                               currentPassword: str = Form(...),
                               newPassword: str = Form(...)):
        """
        POST /member/update-password — 비밀번호를 변경한다.
        현재 비밀번호가 일치해야 변경 가능하다.
        """
        login = self._login_member(request)
        success = self._member_svc.update_password(db, login["id"], currentPassword, newPassword)
        if success:
            request.session["message"] = "비밀번호가 변경되었습니다."
        else:
            request.session["error"] = "현재 비밀번호가 일치하지 않습니다."
        db.commit()
        return RedirectResponse(url="/member/profile", status_code=302)

    # ==================== D1. 알림 설정 ====================

    async def _update_notification(self, request: Request, db: Session = Depends(get_db),
                                   notificationEnabled: Optional[str] = Form(None),
                                   webhookUrl: Optional[str] = Form(None)):
        """POST /member/update-notification — 알림 설정을 변경한다."""
        login = self._login_member(request)
        enabled = notificationEnabled == "true"
        self._member_svc.update_notification(db, login["id"], enabled, webhookUrl)
        login["notification_enabled"] = enabled
        login["webhook_url"] = webhookUrl
        request.session["login_member"] = login
        request.session["message"] = "알림 설정이 변경되었습니다."
        db.commit()
        return RedirectResponse(url="/member/profile", status_code=302)

    # ==================== A5. 회원 탈퇴 ====================

    async def _delete_member(self, request: Request, db: Session = Depends(get_db)):
        """
        POST /member/delete — 회원을 탈퇴시킨다.
        일정 참조 정리 → 활동 로그 기록 → 회원 삭제 → 세션 초기화.
        """
        login = self._login_member(request)
        self._member_svc.delete_member(db, login["id"])
        request.session.clear()
        db.commit()
        return RedirectResponse(url="/auth/login", status_code=302)
