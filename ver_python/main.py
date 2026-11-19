"""
FastAPI 애플리케이션 진입점 (main 모듈).

역할:
1. DB 테이블 생성 및 초기 관리자 계정 삽입
2. 만료 일정 자동완료 백그라운드 스레드 실행
3. 미들웨어 등록 (세션, 로그인 인터셉터)
4. 정적 파일/템플릿 설정
5. 컨트롤러 라우터 등록 (URL 매핑)
"""

import os
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from config.auth import LoginMiddleware
from config.database import Base, engine, SessionLocal
from entity import Member, Schedule, ActivityLog, schedule_tag
from entity.approval_status import ApprovalStatus
from entity.role import Role
from repository.activity_log_repository import ActivityLogRepository
from repository.member_repository import MemberRepository
from repository.schedule_repository import ScheduleRepository
from service.schedule_service import ScheduleService

# 프로젝트 루트 디렉토리 (절대 경로)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SQLite DB 파일이 저장될 data 폴더 생성 (없으면 생성)
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

# 싱글톤 Repository/Service 인스턴스 (앱 전체에서 공유)
_member_repo = MemberRepository()
_schedule_repo = ScheduleRepository()
_log_repo = ActivityLogRepository()
_schedule_svc = ScheduleService(_schedule_repo, _member_repo, _log_repo)


def _init_db():
    """
    DB 초기화 함수.
    1. 모든 엔티티의 테이블을 생성한다 (이미 존재하면 무시).
    2. admin 계정이 없으면 기본 관리자 계정을 삽입한다.
    """
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if _member_repo.find_by_login_id(db, "admin") is None:
            admin = Member()
            admin.login_id = "admin"
            admin.password = "admin"
            admin.name = "관리자"
            admin.email = "admin@team.com"
            admin.role = Role.ADMIN.value
            admin.approval_status = ApprovalStatus.APPROVED.value
            admin.created_at = datetime.now()
            _member_repo.save(db, admin)
            db.commit()
    finally:
        db.close()


def _auto_complete_loop():
    """
    만료 일정 자동완료 백그라운드 루프.
    60초마다 마감일이 지난 미완료 일정을 자동으로 완료 처리한다.
    데몬 스레드로 실행되므로 메인 프로세스 종료 시 함께 종료된다.
    """
    while True:
        time.sleep(60)
        db = SessionLocal()
        try:
            _schedule_svc.auto_complete_expired(db)
            db.commit()
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 애플리케이션 생명주기(Lifespan) 이벤트 핸들러.
    애플리케이션 시작 시 DB 초기화 및 백그라운드 스레드를 시작한다.
    """
    _init_db()
    t = threading.Thread(target=_auto_complete_loop, daemon=True)
    t.start()
    yield


# ==================== FastAPI 앱 생성 및 설정 ====================

app = FastAPI(lifespan=lifespan)

# 미들웨어 등록 (등록 역순으로 실행됨)
app.add_middleware(LoginMiddleware)
app.add_middleware(SessionMiddleware, secret_key="teamschedule-secret-key")

# 정적 파일 서빙 (CSS, JS 등)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Jinja2 템플릿 엔진 설정
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ==================== Jinja2 커스텀 필터 ====================

def _format_datetime(value, fmt="%Y-%m-%d %H:%M"):
    """
    Jinja2 커스텀 필터: datetime → 문자열 변환.
    템플릿에서 {{ schedule.scheduledAt | datefmt }} 형태로 사용한다.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.strftime(fmt)


def _format_datetime_local(value):
    """
    Jinja2 커스텀 필터: datetime → HTML datetime-local input 형식 변환.
    <input type="datetime-local"> 의 value 속성에 사용한다.
    """
    if value is None:
        return ""
    return value.strftime("%Y-%m-%dT%H:%M")


templates.env.filters["datefmt"] = _format_datetime
templates.env.filters["dtlocal"] = _format_datetime_local


# ==================== 컨트롤러 라우터 등록 ====================

from controller.auth_controller import AuthController
from controller.home_controller import HomeController
from controller.schedule_controller import ScheduleController
from controller.member_controller import MemberController
from controller.admin_controller import AdminController
from controller.service_controller import ServiceController

app.include_router(AuthController(templates).router)      # /auth/*
app.include_router(HomeController(templates).router)       # /
app.include_router(ScheduleController(templates).router)   # /schedule/*
app.include_router(MemberController(templates).router)     # /member/*
app.include_router(AdminController(templates).router)      # /admin/*
app.include_router(ServiceController(templates).router)    # /service/*

# ==================== 애플리케이션 직접 실행 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
