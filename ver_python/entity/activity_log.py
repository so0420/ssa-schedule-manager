"""
활동 로그(ActivityLog) 엔티티 모듈.
관리자 활동 및 시스템 이벤트를 기록하는 테이블과 매핑된다.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class ActivityLog(Base):
    """
    활동 로그 엔티티 클래스.
    회원가입, 승인/거절, 추방, 일정 CRUD 등 주요 활동을 기록한다.
    actor 필드를 문자열로 저장하여, 회원 탈퇴 후에도 로그가 보존된다.
    (FK 관계 없음 — 의도적 설계)
    """
    __tablename__ = "activity_log"  # 매핑되는 DB 테이블명

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)              # PK, 자동 증가
    action: Mapped[str] = mapped_column(String(500))                                   # 수행된 활동 내용 (예: "일정 등록: 중간발표 준비")
    actor: Mapped[str] = mapped_column(String(100))                                    # 활동 수행자 loginId 또는 "시스템"
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)    # 활동 발생 일시

    def __init__(self, action: str, actor: str):
        """
        활동 로그를 생성한다. 생성 시각은 현재 시각으로 자동 설정된다.
        Args:
            action: 수행된 활동 내용 설명
            actor: 활동을 수행한 사용자의 loginId (시스템 자동 처리 시 "시스템")
        """
        self.action = action
        self.actor = actor
        self.created_at = datetime.now()  # 생성 시점 자동 기록
