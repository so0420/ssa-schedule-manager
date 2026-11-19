"""
데이터베이스 설정 모듈.
SQLAlchemy 엔진, 세션, Base 클래스를 정의한다.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# === DB 파일 경로 설정 ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ver_python/ 디렉토리
DB_PATH = os.path.join(BASE_DIR, "data", "teamschedule.db")            # SQLite DB 파일 경로
DATABASE_URL = f"sqlite:///{DB_PATH}"                                   # SQLAlchemy 접속 URL

# === SQLAlchemy 엔진 생성 ===
# check_same_thread=False: FastAPI가 멀티스레드로 동작하므로 SQLite 단일 스레드 제한을 해제한다.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# === 세션 팩토리 생성 ===
# autocommit=False: 명시적으로 commit()을 호출해야 DB에 반영된다 (트랜잭션 제어)
# autoflush=False: flush()를 명시적으로 호출해야 SQL이 실행된다
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """
    모든 엔티티(모델) 클래스의 부모 클래스.
    SQLAlchemy의 declarative 매핑 기반 클래스이다.
    모든 Entity 클래스는 이 Base를 상속받아야 테이블이 자동 생성된다.
    """
    pass


def get_db():
    """
    DB 세션을 생성하고 반환하는 의존성 함수 (FastAPI Depends용).
    요청 처리 후 세션을 자동으로 닫는다 (finally 블록).

    사용 예시:
        async def some_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
