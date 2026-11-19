"""
인증(Auth) 컨트롤러 모듈.
로그인, 회원가입, 로그아웃, ID/비밀번호 찾기를 처리한다.
유스케이스: A1(회원가입), A3(로그인/ID찾기/비밀번호찾기), A4(로그아웃)
"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config.database import get_db
from repository.member_repository import MemberRepository
from repository.activity_log_repository import ActivityLogRepository
from repository.schedule_repository import ScheduleRepository
from service.member_service import MemberService


class AuthController:
    """
    인증 관련 HTTP 요청을 처리하는 컨트롤러 클래스.
    /auth 접두사를 가진 라우트들을 관리한다.
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
        self.router = APIRouter(prefix="/auth")
        self._setup_routes()

    def _setup_routes(self):
        """URL-메서드 매핑을 등록한다."""
        self.router.add_api_route("/login", self._login_page, methods=["GET"])
        self.router.add_api_route("/login", self._login, methods=["POST"])
        self.router.add_api_route("/signup", self._signup_page, methods=["GET"])
        self.router.add_api_route("/signup", self._signup, methods=["POST"])
        self.router.add_api_route("/logout", self._logout, methods=["GET"])
        self.router.add_api_route("/find-id", self._find_id_page, methods=["GET"])
        self.router.add_api_route("/find-id", self._find_id, methods=["POST"])
        self.router.add_api_route("/find-password", self._find_password_page, methods=["GET"])
        self.router.add_api_route("/find-password", self._find_password, methods=["POST"])

    # ==================== A3-1. 로그인 ====================

    async def _login_page(self, request: Request):
        """GET /auth/login — 로그인 폼 페이지를 렌더링한다."""
        return self._templates.TemplateResponse("auth/login.html", {
            "request": request,
            "message": request.session.pop("message", None),
            "error": request.session.pop("error", None),
        })

    async def _login(self, request: Request, db: Session = Depends(get_db),
                     loginId: str = Form(...), password: str = Form(...)):
        """
        POST /auth/login — 로그인 인증을 처리한다.
        성공 시 세션에 회원 정보를 저장하고 대시보드로 리다이렉트한다.
        실패 시 에러 메시지와 함께 로그인 페이지로 리다이렉트한다 (PRG 패턴).
        """
        member = self._member_svc.login(db, loginId, password)
        if member is None:
            request.session["error"] = "로그인 실패: ID/비밀번호를 확인하거나 승인 대기 중입니다."
            db.commit()
            return RedirectResponse(url="/auth/login", status_code=302)
        request.session["login_member"] = member.to_session_dict()
        db.commit()
        return RedirectResponse(url="/", status_code=302)

    # ==================== A1. 회원가입 ====================

    async def _signup_page(self, request: Request):
        """GET /auth/signup — 회원가입 폼 페이지를 렌더링한다."""
        return self._templates.TemplateResponse("auth/signup.html", {
            "request": request,
            "error": request.session.pop("error", None),
        })

    async def _signup(self, request: Request, db: Session = Depends(get_db),
                      loginId: str = Form(...), password: str = Form(...),
                      name: str = Form(...), email: str = Form(...)):
        """
        POST /auth/signup — 회원가입을 처리한다.
        중복 ID 체크 후 회원을 생성한다. 초기 상태: PENDING (관리자 승인 대기).
        """
        if self._member_svc.find_by_login_id(db, loginId):
            request.session["error"] = "이미 사용 중인 ID입니다."
            db.commit()
            return RedirectResponse(url="/auth/signup", status_code=302)
        self._member_svc.signup(db, loginId, password, name, email)
        request.session["message"] = "회원가입이 완료되었습니다. 관리자 승인 후 로그인 가능합니다."
        db.commit()
        return RedirectResponse(url="/auth/login", status_code=302)

    # ==================== A4. 로그아웃 ====================

    async def _logout(self, request: Request):
        """
        GET /auth/logout — 로그아웃을 처리한다.
        세션을 비우고 로그인 페이지로 리다이렉트한다.
        """
        request.session.clear()
        return RedirectResponse(url="/auth/login", status_code=302)

    # ==================== A3-2. ID 찾기 ====================

    async def _find_id_page(self, request: Request):
        """GET /auth/find-id — ID 찾기 폼 페이지를 렌더링한다."""
        return self._templates.TemplateResponse("auth/find-id.html", {
            "request": request, "result": None, "error": None,
        })

    async def _find_id(self, request: Request, db: Session = Depends(get_db),
                       name: str = Form(...), email: str = Form(...)):
        """POST /auth/find-id — 이름+이메일로 로그인 ID를 찾는다."""
        login_id = self._member_svc.find_login_id_by_name_and_email(db, name, email)
        ctx = {"request": request, "result": None, "error": None}
        if login_id:
            ctx["result"] = f"회원님의 ID는 [ {login_id} ] 입니다."
        else:
            ctx["error"] = "일치하는 회원 정보가 없습니다."
        return self._templates.TemplateResponse("auth/find-id.html", ctx)

    # ==================== A3-3. 비밀번호 찾기 ====================

    async def _find_password_page(self, request: Request):
        """GET /auth/find-password — 비밀번호 찾기 폼 페이지를 렌더링한다."""
        return self._templates.TemplateResponse("auth/find-password.html", {
            "request": request, "result": None, "error": None,
        })

    async def _find_password(self, request: Request, db: Session = Depends(get_db),
                             loginId: str = Form(...), email: str = Form(...)):
        """POST /auth/find-password — 로그인ID+이메일로 비밀번호 힌트를 조회한다."""
        password = self._member_svc.find_password_by_login_id_and_email(db, loginId, email)
        ctx = {"request": request, "result": None, "error": None}
        if password:
            masked = password[0] + "*" * (len(password) - 1)
            ctx["result"] = f"회원님의 비밀번호 힌트: {masked}"
        else:
            ctx["error"] = "일치하는 회원 정보가 없습니다."
        return self._templates.TemplateResponse("auth/find-password.html", ctx)
