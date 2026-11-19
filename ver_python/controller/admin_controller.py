"""
관리자(Admin) 컨트롤러 모듈.
멤버 승인/거절/추방, 활동 로그 열람 등 관리자 전용 기능을 처리한다.
유스케이스: E1(멤버 관리 — 승인/거절/추방), E2(활동 로그 열람)
Java의 AdminController에 해당한다.
"""

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
    """
    관리자 전용 HTTP 요청을 처리하는 컨트롤러 클래스.
    /admin 접두사를 가진 라우트들을 관리한다.
    모든 메서드에서 관리자 권한 체크를 수행한다.
    """

    def __init__(self, templates: Jinja2Templates):
        """
        생성자: 템플릿 엔진을 주입받고, 라우터를 초기화한다.
        Args:
            templates: Jinja2 템플릿 엔진
        """
        self._templates = templates
        self.router = APIRouter(prefix="/admin")
        self._setup_routes()

    def _build_service(self, db: Session) -> MemberService:
        """요청마다 MemberService를 생성한다."""
        return MemberService(
            MemberRepository(db), ActivityLogRepository(db), ScheduleRepository(db)
        )

    def _login_member(self, request: Request):
        """세션에서 로그인된 회원 정보(dict)를 가져온다."""
        return request.session.get("login_member")

    def _is_admin(self, request: Request) -> bool:
        """
        현재 로그인한 사용자가 관리자(ADMIN)인지 확인한다.
        Java의 AdminController에서 loginMember.getRole() != Role.ADMIN 체크에 해당한다.
        Returns:
            관리자이면 True, 아니면 False
        """
        login = self._login_member(request)
        return login is not None and login.get("role") == Role.ADMIN.value

    def _setup_routes(self):
        """URL-메서드 매핑을 등록한다."""
        self.router.add_api_route("/members", self._members, methods=["GET"])                           # 멤버 관리 페이지
        self.router.add_api_route("/members/{member_id}/approve", self._approve, methods=["POST"])      # 회원 승인
        self.router.add_api_route("/members/{member_id}/reject", self._reject, methods=["POST"])        # 회원 거절
        self.router.add_api_route("/members/{member_id}/kick", self._kick, methods=["POST"])            # 멤버 추방
        self.router.add_api_route("/logs", self._logs, methods=["GET"])                                 # 활동 로그

    # ==================== E1. 멤버 관리 ====================

    async def _members(self, request: Request, db: Session = Depends(get_db)):
        """
        GET /admin/members — 멤버 관리 페이지를 렌더링한다.
        가입 대기(PENDING) 목록과 승인된(APPROVED) 멤버 목록을 함께 표시한다.
        """
        if not self._is_admin(request):  # 관리자 권한 체크
            return RedirectResponse(url="/", status_code=302)
        svc = self._build_service(db)
        return self._templates.TemplateResponse("admin/members.html", {
            "request": request,
            "pendingMembers": svc.get_pending_members(),      # 가입 대기 목록
            "approvedMembers": svc.get_approved_members(),    # 승인된 멤버 목록
            "message": request.session.pop("message", None),
        })

    # ==================== E1-1. 회원 승인 ====================

    async def _approve(self, member_id: int, request: Request,
                       db: Session = Depends(get_db)):
        """POST /admin/members/{id}/approve — 회원가입을 승인한다."""
        if not self._is_admin(request):
            return RedirectResponse(url="/", status_code=302)
        login = self._login_member(request)
        svc = self._build_service(db)
        svc.approve_member(member_id, login["name"])  # 관리자 이름을 로그에 기록
        request.session["message"] = "회원이 승인되었습니다."
        db.commit()
        return RedirectResponse(url="/admin/members", status_code=302)

    # ==================== E1-1. 회원 거절 ====================

    async def _reject(self, member_id: int, request: Request,
                      db: Session = Depends(get_db)):
        """POST /admin/members/{id}/reject — 회원가입을 거절한다."""
        if not self._is_admin(request):
            return RedirectResponse(url="/", status_code=302)
        login = self._login_member(request)
        svc = self._build_service(db)
        svc.reject_member(member_id, login["name"])
        request.session["message"] = "회원이 거절되었습니다."
        db.commit()
        return RedirectResponse(url="/admin/members", status_code=302)

    # ==================== E1-2. 멤버 추방 ====================

    async def _kick(self, member_id: int, request: Request,
                    db: Session = Depends(get_db)):
        """
        POST /admin/members/{id}/kick — 멤버를 추방한다.
        일정 참조 정리 → 활동 로그 기록 → 멤버 삭제.
        """
        if not self._is_admin(request):
            return RedirectResponse(url="/", status_code=302)
        login = self._login_member(request)
        svc = self._build_service(db)
        svc.kick_member(member_id, login["name"])
        request.session["message"] = "멤버가 추방되었습니다."
        db.commit()
        return RedirectResponse(url="/admin/members", status_code=302)

    # ==================== E2. 활동 로그 열람 ====================

    async def _logs(self, request: Request, db: Session = Depends(get_db)):
        """GET /admin/logs — 활동 로그 페이지를 렌더링한다 (최신순 정렬)."""
        if not self._is_admin(request):
            return RedirectResponse(url="/", status_code=302)
        svc = self._build_service(db)
        return self._templates.TemplateResponse("admin/logs.html", {
            "request": request,
            "logs": svc.get_all_logs(),  # 전체 활동 로그 (최신순)
        })
