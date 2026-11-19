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
# JPA의 @JoinTable에 해당하며, SQLAlchemy가 자동으로 테이블을 생성/관리한다.
schedule_tag = Table(
    "schedule_tag",          # 테이블명
    Base.metadata,
    Column("schedule_id", Integer, ForeignKey("schedule.id"), primary_key=True),  # 일정 FK
    Column("member_id", Integer, ForeignKey("member.id"), primary_key=True),      # 멤버 FK
)


class Schedule(Base):
    """
    일정 엔티티 클래스.
    팀 프로젝트의 개별 일정 정보를 담는 도메인 객체이다.
    하나의 일정은 한 명이 생성하고(N:1), 여러 멤버를 태그할 수 있다(N:M).
    """
    __tablename__ = "schedule"  # 매핑되는 DB 테이블명

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)              # PK, 자동 증가
    title: Mapped[str] = mapped_column(String(255))                                    # 일정 제목
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)                # 일정 내용/메모 (선택)

    # === 날짜 필드 ===
    # start_at이 null이면 단일일 일정, 값이 있으면 기간 일정 (start_at ~ scheduled_at)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)      # 시작일 (기간 일정용, nullable)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 종료일 또는 단일 일정일

    # === 상태 필드 ===
    completed: Mapped[bool] = mapped_column(Boolean, default=False)                    # 완료 여부 (기본: 미완료)

    # === 관계 필드 ===
    created_by_id: Mapped[Optional[int]] = mapped_column(                              # 작성자 FK (member.id 참조)
        ForeignKey("member.id"), nullable=True                                         # nullable: 작성자 탈퇴 시 null 처리
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)    # 일정 등록 일시

    # N:1 관계 — 일정을 생성한 멤버 (JPA의 @ManyToOne에 해당)
    # lazy="joined": 일정 조회 시 작성자 정보를 함께 로드 (JOIN)
    created_by = relationship("Member", foreign_keys=[created_by_id], lazy="joined")

    # N:M 관계 — 일정에 태그된 멤버 목록 (JPA의 @ManyToMany에 해당)
    # secondary=schedule_tag: 위에서 정의한 중간 테이블을 통해 관계를 맺음
    tagged_members: Mapped[List["Member"]] = relationship(
        "Member", secondary=schedule_tag, lazy="joined"
    )
