"""
일정(Schedule) 컨트롤러 모듈.
일정 목록, 등록, 수정, 삭제, 완료 처리를 담당한다.
유스케이스: C1(등록), C2(조회/검색), C3(수정), C4(삭제), C5(완료)
Java의 ScheduleController에 해당한다.
"""

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
    """
    일정 관련 HTTP 요청을 처리하는 컨트롤러 클래스.
    /schedule 접두사를 가진 라우트들을 관리한다.
    Java의 @Controller + @RequestMapping에 해당한다.
    """

    def __init__(self, templates: Jinja2Templates):
        """
        생성자: 템플릿 엔진을 주입받고, 라우터를 초기화한다.
        Args:
            templates: Jinja2 템플릿 엔진
        """
        self._templates = templates
        self.router = APIRouter(prefix="/schedule")
        self._setup_routes()

    def _build_services(self, db: Session):
        """
        요청마다 Service 인스턴스들을 생성한다.
        ScheduleService와 MemberService 모두 필요 (멤버 목록 조회 등).
        Returns:
            (ScheduleService, MemberService) 튜플
        """
        member_repo = MemberRepository(db)
        schedule_repo = ScheduleRepository(db)
        log_repo = ActivityLogRepository(db)
        schedule_svc = ScheduleService(schedule_repo, member_repo, log_repo)
        member_svc = MemberService(member_repo, log_repo, schedule_repo)
        return schedule_svc, member_svc

    def _login_member(self, request: Request):
        """세션에서 로그인된 회원 정보(dict)를 가져온다."""
        return request.session.get("login_member")

    def _setup_routes(self):
        """URL-메서드 매핑을 등록한다."""
        self.router.add_api_route("", self._list, methods=["GET"])                              # 일정 목록
        self.router.add_api_route("/new", self._create_form, methods=["GET"])                    # 등록 폼
        self.router.add_api_route("/new", self._create, methods=["POST"])                        # 등록 처리
        self.router.add_api_route("/{schedule_id}/edit", self._edit_form, methods=["GET"])       # 수정 폼
        self.router.add_api_route("/{schedule_id}/edit", self._update, methods=["POST"])         # 수정 처리
        self.router.add_api_route("/{schedule_id}/delete", self._delete, methods=["POST"])       # 삭제 처리
        self.router.add_api_route("/{schedule_id}/toggle", self._toggle, methods=["POST"])       # 완료 토글

    # ==================== C2. 일정 조회/검색 ====================

    async def _list(self, request: Request, db: Session = Depends(get_db),
                    keyword: Optional[str] = Query(None),
                    completed: Optional[str] = Query(None)):
        """
        GET /schedule — 일정 목록 페이지를 렌더링한다.
        검색어(keyword), 완료 상태(completed) 필터를 지원한다.
        캘린더/간트 뷰를 위해 일정 데이터를 JSON으로도 전달한다.
        """
        schedule_svc, _ = self._build_services(db)

        # 쿼리 파라미터의 완료 상태를 bool로 변환
        completed_bool: Optional[bool] = None
        if completed == "true":
            completed_bool = True
        elif completed == "false":
            completed_bool = False

        # 검색/필터 조건이 있으면 search, 없으면 전체 조회
        if keyword is not None or completed_bool is not None:
            schedules = schedule_svc.search(keyword, completed_bool)
        else:
            schedules = schedule_svc.get_all()

        # 캘린더/간트 차트용 JSON 데이터 생성
        # Thymeleaf의 /*[[${schedules}]]*/ 인라인 스크립트에 대응한다
        schedules_json = json.dumps([
            {
                "id": s.id,
                "title": s.title,
                "content": s.content,
                "startAt": s.start_at.isoformat() if s.start_at else None,          # ISO 8601 형식
                "scheduledAt": s.scheduled_at.isoformat() if s.scheduled_at else None,
                "completed": s.completed,
                "createdBy": s.created_by.name if s.created_by else None,
                "createdAt": s.created_at.isoformat() if s.created_at else None,
            }
            for s in schedules
        ], ensure_ascii=False)  # 한글이 유니코드 이스케이프되지 않도록

        return self._templates.TemplateResponse("schedule/list.html", {
            "request": request,
            "schedules": schedules,                 # 목록 뷰용 (ORM 객체 리스트)
            "schedules_json": schedules_json,       # 캘린더/간트 뷰용 (JSON 문자열)
            "keyword": keyword,
            "completed": completed_bool,
            "message": request.session.pop("message", None),
        })

    # ==================== C1. 일정 등록 ====================

    async def _create_form(self, request: Request, db: Session = Depends(get_db)):
        """GET /schedule/new — 일정 등록 폼 페이지를 렌더링한다."""
        _, member_svc = self._build_services(db)
        return self._templates.TemplateResponse("schedule/form.html", {
            "request": request,
            "schedule": None,                                # 신규 등록이므로 None
            "members": member_svc.get_approved_members(),    # 태그 가능한 멤버 목록
            "taggedIds": [],                                 # 태그된 멤버 없음
        })

    async def _create(self, request: Request, db: Session = Depends(get_db),
                      title: str = Form(...), content: Optional[str] = Form(None),
                      startAt: Optional[str] = Form(None),
                      scheduledAt: str = Form(...),
                      taggedMemberIds: Optional[List[int]] = Form(None)):
        """
        POST /schedule/new — 새 일정을 등록한다.
        폼 데이터에서 datetime 문자열을 파싱하여 Service에 전달한다.
        등록 후 일정 목록으로 리다이렉트 (PRG 패턴).
        """
        schedule_svc, member_svc = self._build_services(db)
        login = self._login_member(request)
        member = member_svc.find_by_id(login["id"])  # 세션의 ID로 Member 객체 조회

        # datetime-local 폼 값을 Python datetime으로 변환
        start_dt = datetime.fromisoformat(startAt) if startAt and startAt.strip() else None
        scheduled_dt = datetime.fromisoformat(scheduledAt)

        schedule_svc.create(title, content, start_dt, scheduled_dt, taggedMemberIds, member)
        request.session["message"] = "일정이 등록되었습니다."
        db.commit()  # 트랜잭션 커밋
        return RedirectResponse(url="/schedule", status_code=302)

    # ==================== C3. 일정 수정 ====================

    async def _edit_form(self, schedule_id: int, request: Request,
                         db: Session = Depends(get_db)):
        """GET /schedule/{id}/edit — 일정 수정 폼 페이지를 렌더링한다."""
        schedule_svc, member_svc = self._build_services(db)
        schedule = schedule_svc.find_by_id(schedule_id)
        # 현재 태그된 멤버 ID 목록 (폼에서 선택 상태 유지용)
        tagged_ids = [m.id for m in schedule.tagged_members] if schedule else []
        return self._templates.TemplateResponse("schedule/form.html", {
            "request": request,
            "schedule": schedule,                            # 수정할 일정 객체
            "members": member_svc.get_approved_members(),    # 태그 가능한 멤버 목록
            "taggedIds": tagged_ids,                         # 현재 태그된 멤버 ID 리스트
        })

    async def _update(self, schedule_id: int, request: Request,
                      db: Session = Depends(get_db),
                      title: str = Form(...), content: Optional[str] = Form(None),
                      startAt: Optional[str] = Form(None),
                      scheduledAt: str = Form(...),
                      taggedMemberIds: Optional[List[int]] = Form(None)):
        """POST /schedule/{id}/edit — 일정을 수정한다."""
        schedule_svc, _ = self._build_services(db)
        login = self._login_member(request)

        start_dt = datetime.fromisoformat(startAt) if startAt and startAt.strip() else None
        scheduled_dt = datetime.fromisoformat(scheduledAt)

        schedule_svc.update(schedule_id, title, content, start_dt, scheduled_dt,
                            taggedMemberIds, login["login_id"])
        request.session["message"] = "일정이 수정되었습니다."
        db.commit()
        return RedirectResponse(url="/schedule", status_code=302)

    # ==================== C4. 일정 삭제 ====================

    async def _delete(self, schedule_id: int, request: Request,
                      db: Session = Depends(get_db)):
        """POST /schedule/{id}/delete — 일정을 삭제한다."""
        schedule_svc, _ = self._build_services(db)
        login = self._login_member(request)
        schedule_svc.delete(schedule_id, login["login_id"])
        request.session["message"] = "일정이 삭제되었습니다."
        db.commit()
        return RedirectResponse(url="/schedule", status_code=302)

    # ==================== C5-2. 수동 완료/미완료 토글 ====================

    async def _toggle(self, schedule_id: int, request: Request,
                      db: Session = Depends(get_db)):
        """POST /schedule/{id}/toggle — 완료 상태를 토글한다 (완료 ↔ 미완료)."""
        schedule_svc, _ = self._build_services(db)
        login = self._login_member(request)
        schedule_svc.toggle_complete(schedule_id, login["login_id"])
        db.commit()
        return RedirectResponse(url="/schedule", status_code=302)
