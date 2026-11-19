"""
일정(Schedule) 엔티티 모듈.
DB의 schedule 테이블과 매핑되는 SQLAlchemy ORM 모델이다.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Table, Column, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

# N:M (다대다) 관계를 위한 중간 테이블 정의
# Schedule과 Member 사이의 '태그된 멤버' 관계를 표현한다.
schedule_tag = Table(
    "schedule_tag",
    Base.metadata,
    Column("schedule_id", Integer, ForeignKey("schedule.id"), primary_key=True),
    Column("member_id", Integer, ForeignKey("member.id"), primary_key=True),
)


class Schedule(Base):
    """
    일정 엔티티 클래스.
    팀 프로젝트의 개별 일정 정보를 담는 도메인 객체이다.
    하나의 일정은 한 명이 생성하고(N:1), 여러 멤버를 태그할 수 있다(N:M).
    """
    __tablename__ = "schedule"

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # === 날짜 필드 ===
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # === 상태 필드 ===
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # === 관계 필드 ===
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("member.id"), nullable=True
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # N:1 관계 — 일정을 생성한 멤버
    created_by = relationship("Member", foreign_keys=[created_by_id], lazy="joined")

    # N:M 관계 — 일정에 태그된 멤버 목록
    tagged_members: Mapped[List["Member"]] = relationship(
        "Member", secondary=schedule_tag, lazy="joined"
    )
