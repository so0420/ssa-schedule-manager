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

    def __init__(self, templates: Jinja2Templates):
        self._templates = templates
        self.router = APIRouter(prefix="/auth")
        self._setup_routes()

    def _build_service(self, db: Session) -> MemberService:
        return MemberService(
            MemberRepository(db), ActivityLogRepository(db), ScheduleRepository(db)
        )

    def _setup_routes(self):
        self.router.add_api_route("/login", self._login_page, methods=["GET"])
        self.router.add_api_route("/login", self._login, methods=["POST"])
        self.router.add_api_route("/signup", self._signup_page, methods=["GET"])
        self.router.add_api_route("/signup", self._signup, methods=["POST"])
        self.router.add_api_route("/logout", self._logout, methods=["GET"])
        self.router.add_api_route("/find-id", self._find_id_page, methods=["GET"])
        self.router.add_api_route("/find-id", self._find_id, methods=["POST"])
        self.router.add_api_route("/find-password", self._find_password_page, methods=["GET"])
        self.router.add_api_route("/find-password", self._find_password, methods=["POST"])

    async def _login_page(self, request: Request):
        return self._templates.TemplateResponse("auth/login.html", {
            "request": request,
            "message": request.session.pop("message", None),
            "error": request.session.pop("error", None),
        })

    async def _login(self, request: Request, db: Session = Depends(get_db),
                     loginId: str = Form(...), password: str = Form(...)):
        svc = self._build_service(db)
        member = svc.login(loginId, password)
        if member is None:
            request.session["error"] = "로그인 실패: ID/비밀번호를 확인하거나 승인 대기 중입니다."
            db.commit()
            return RedirectResponse(url="/auth/login", status_code=302)
        request.session["login_member"] = member.to_session_dict()
        db.commit()
        return RedirectResponse(url="/", status_code=302)

    async def _signup_page(self, request: Request):
        return self._templates.TemplateResponse("auth/signup.html", {
            "request": request,
            "error": request.session.pop("error", None),
        })

    async def _signup(self, request: Request, db: Session = Depends(get_db),
                      loginId: str = Form(...), password: str = Form(...),
                      name: str = Form(...), email: str = Form(...)):
        svc = self._build_service(db)
        if svc.find_by_login_id(loginId):
            request.session["error"] = "이미 사용 중인 ID입니다."
            db.commit()
            return RedirectResponse(url="/auth/signup", status_code=302)
        svc.signup(loginId, password, name, email)
        request.session["message"] = "회원가입이 완료되었습니다. 관리자 승인 후 로그인 가능합니다."
        db.commit()
        return RedirectResponse(url="/auth/login", status_code=302)

    async def _logout(self, request: Request):
        request.session.clear()
        return RedirectResponse(url="/auth/login", status_code=302)

    async def _find_id_page(self, request: Request):
        return self._templates.TemplateResponse("auth/find-id.html", {
            "request": request, "result": None, "error": None,
        })

    async def _find_id(self, request: Request, db: Session = Depends(get_db),
                       name: str = Form(...), email: str = Form(...)):
        svc = self._build_service(db)
        login_id = svc.find_login_id_by_name_and_email(name, email)
        ctx = {"request": request, "result": None, "error": None}
        if login_id:
            ctx["result"] = f"회원님의 ID는 [ {login_id} ] 입니다."
        else:
            ctx["error"] = "일치하는 회원 정보가 없습니다."
        return self._templates.TemplateResponse("auth/find-id.html", ctx)

    async def _find_password_page(self, request: Request):
        return self._templates.TemplateResponse("auth/find-password.html", {
            "request": request, "result": None, "error": None,
        })

    async def _find_password(self, request: Request, db: Session = Depends(get_db),
                             loginId: str = Form(...), email: str = Form(...)):
        svc = self._build_service(db)
        password = svc.find_password_by_login_id_and_email(loginId, email)
        ctx = {"request": request, "result": None, "error": None}
        if password:
            masked = password[0] + "*" * (len(password) - 1)
            ctx["result"] = f"회원님의 비밀번호 힌트: {masked}"
        else:
            ctx["error"] = "일치하는 회원 정보가 없습니다."
        return self._templates.TemplateResponse("auth/find-password.html", ctx)
