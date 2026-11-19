from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Table, Column, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

schedule_tag = Table(
    "schedule_tag",
    Base.metadata,
    Column("schedule_id", Integer, ForeignKey("schedule.id"), primary_key=True),
    Column("member_id", Integer, ForeignKey("member.id"), primary_key=True),
)


class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("member.id"), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_by = relationship("Member", foreign_keys=[created_by_id], lazy="joined")
    tagged_members: Mapped[List["Member"]] = relationship(
        "Member", secondary=schedule_tag, lazy="joined"
    )
