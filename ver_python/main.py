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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)


def _init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        repo = MemberRepository(db)
        if repo.find_by_login_id("admin") is None:
            admin = Member()
            admin.login_id = "admin"
            admin.password = "admin"
            admin.name = "관리자"
            admin.email = "admin@team.com"
            admin.role = Role.ADMIN.value
            admin.approval_status = ApprovalStatus.APPROVED.value
            admin.created_at = datetime.now()
            repo.save(admin)
            db.commit()
    finally:
        db.close()


def _auto_complete_loop():
    while True:
        time.sleep(60)
        db = SessionLocal()
        try:
            svc = ScheduleService(
                ScheduleRepository(db), MemberRepository(db), ActivityLogRepository(db)
            )
            svc.auto_complete_expired()
            db.commit()
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()
    t = threading.Thread(target=_auto_complete_loop, daemon=True)
    t.start()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(LoginMiddleware)
app.add_middleware(SessionMiddleware, secret_key="teamschedule-secret-key")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def _format_datetime(value, fmt="%Y-%m-%d %H:%M"):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.strftime(fmt)


def _format_datetime_local(value):
    if value is None:
        return ""
    return value.strftime("%Y-%m-%dT%H:%M")


templates.env.filters["datefmt"] = _format_datetime
templates.env.filters["dtlocal"] = _format_datetime_local


from controller.auth_controller import AuthController
from controller.home_controller import HomeController
from controller.schedule_controller import ScheduleController
from controller.member_controller import MemberController
from controller.admin_controller import AdminController
from controller.service_controller import ServiceController

app.include_router(AuthController(templates).router)
app.include_router(HomeController(templates).router)
app.include_router(ScheduleController(templates).router)
app.include_router(MemberController(templates).router)
app.include_router(AdminController(templates).router)
app.include_router(ServiceController(templates).router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
