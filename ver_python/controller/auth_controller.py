"""
인증(Auth) 컨트롤러 모듈.
로그인, 회원가입, 로그아웃, ID/비밀번호 찾기를 처리한다.
유스케이스: A1(회원가입), A3(로그인/ID찾기/비밀번호찾기), A4(로그아웃)
Java의 AuthController에 해당한다.
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
    Java의 @Controller + @RequestMapping("/auth")에 해당한다.
    """

    def __init__(self, templates: Jinja2Templates):
        """
        생성자: 템플릿 엔진을 주입받고, 라우터를 초기화한다.
        Args:
            templates: Jinja2 템플릿 엔진 (Java의 Thymeleaf에 해당)
        """
        self._templates = templates                 # 뷰 렌더링용 템플릿 엔진 (private)
        self.router = APIRouter(prefix="/auth")     # /auth 접두사 라우터
        self._setup_routes()                        # 라우트 등록

    def _build_service(self, db: Session) -> MemberService:
        """
        요청마다 Service 인스턴스를 생성한다 (의존성 조립).
        각 Repository를 생성하여 Service에 주입한다.
        Java에서는 Spring이 @Autowired로 자동 주입하지만,
        여기서는 직접 조립한다.
        Args:
            db: 현재 요청의 DB 세션
        Returns:
            MemberService 인스턴스
        """
        return MemberService(
            MemberRepository(db), ActivityLogRepository(db), ScheduleRepository(db)
        )

    def _setup_routes(self):
        """
        URL-메서드 매핑을 등록한다.
        Java의 @GetMapping, @PostMapping 어노테이션에 해당한다.
        """
        self.router.add_api_route("/login", self._login_page, methods=["GET"])             # 로그인 폼
        self.router.add_api_route("/login", self._login, methods=["POST"])                 # 로그인 처리
        self.router.add_api_route("/signup", self._signup_page, methods=["GET"])            # 회원가입 폼
        self.router.add_api_route("/signup", self._signup, methods=["POST"])                # 회원가입 처리
        self.router.add_api_route("/logout", self._logout, methods=["GET"])                 # 로그아웃
        self.router.add_api_route("/find-id", self._find_id_page, methods=["GET"])          # ID 찾기 폼
        self.router.add_api_route("/find-id", self._find_id, methods=["POST"])              # ID 찾기 처리
        self.router.add_api_route("/find-password", self._find_password_page, methods=["GET"])   # 비밀번호 찾기 폼
        self.router.add_api_route("/find-password", self._find_password, methods=["POST"])       # 비밀번호 찾기 처리

    # ==================== A3-1. 로그인 ====================

    async def _login_page(self, request: Request):
        """GET /auth/login — 로그인 폼 페이지를 렌더링한다."""
        return self._templates.TemplateResponse("auth/login.html", {
            "request": request,
            "message": request.session.pop("message", None),  # 플래시 메시지 (회원가입 성공 등)
            "error": request.session.pop("error", None),      # 에러 메시지 (로그인 실패 등)
        })

    async def _login(self, request: Request, db: Session = Depends(get_db),
                     loginId: str = Form(...), password: str = Form(...)):
        """
        POST /auth/login — 로그인 인증을 처리한다.
        성공 시 세션에 회원 정보를 저장하고 대시보드로 리다이렉트한다.
        실패 시 에러 메시지와 함께 로그인 페이지로 리다이렉트한다 (PRG 패턴).
        """
        svc = self._build_service(db)
        member = svc.login(loginId, password)
        if member is None:
            # 로그인 실패: 에러 메시지를 세션에 저장 (플래시 메시지)
            request.session["error"] = "로그인 실패: ID/비밀번호를 확인하거나 승인 대기 중입니다."
            db.commit()
            return RedirectResponse(url="/auth/login", status_code=302)
        # 로그인 성공: 세션에 회원 정보 저장 (Java의 session.setAttribute("loginMember", member))
        request.session["login_member"] = member.to_session_dict()
        db.commit()
        return RedirectResponse(url="/", status_code=302)  # 대시보드로 리다이렉트

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
        svc = self._build_service(db)
        # 중복 ID 체크
        if svc.find_by_login_id(loginId):
            request.session["error"] = "이미 사용 중인 ID입니다."
            db.commit()
            return RedirectResponse(url="/auth/signup", status_code=302)
        svc.signup(loginId, password, name, email)
        request.session["message"] = "회원가입이 완료되었습니다. 관리자 승인 후 로그인 가능합니다."
        db.commit()
        return RedirectResponse(url="/auth/login", status_code=302)  # 로그인 페이지로 리다이렉트

    # ==================== A4. 로그아웃 ====================

    async def _logout(self, request: Request):
        """
        GET /auth/logout — 로그아웃을 처리한다.
        세션을 비우고 로그인 페이지로 리다이렉트한다.
        Java의 session.invalidate()에 해당한다.
        """
        request.session.clear()  # 세션 전체 삭제
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
        svc = self._build_service(db)
        login_id = svc.find_login_id_by_name_and_email(name, email)
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
        svc = self._build_service(db)
        password = svc.find_password_by_login_id_and_email(loginId, email)
        ctx = {"request": request, "result": None, "error": None}
        if password:
            # 비밀번호 첫 글자만 보여주고 나머지는 마스킹 (보안)
            masked = password[0] + "*" * (len(password) - 1)
            ctx["result"] = f"회원님의 비밀번호 힌트: {masked}"
        else:
            ctx["error"] = "일치하는 회원 정보가 없습니다."
        return self._templates.TemplateResponse("auth/find-password.html", ctx)
