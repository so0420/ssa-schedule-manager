from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(500))
    actor: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __init__(self, action: str, actor: str):
        self.action = action
        self.actor = actor
        self.created_at = datetime.now()
