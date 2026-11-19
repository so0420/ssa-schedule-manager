from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base
from entity.role import Role
from entity.approval_status import ApprovalStatus


class Member(Base):
    __tablename__ = "member"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login_id: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=Role.USER.value)
    approval_status: Mapped[str] = mapped_column(String(20), default=ApprovalStatus.PENDING.value)
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_session_dict(self) -> dict:
        return {
            "id": self.id,
            "login_id": self.login_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "approval_status": self.approval_status,
            "notification_enabled": self.notification_enabled,
            "webhook_url": self.webhook_url,
        }
