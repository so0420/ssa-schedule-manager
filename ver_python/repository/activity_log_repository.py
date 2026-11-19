from typing import List

from sqlalchemy.orm import Session

from entity.activity_log import ActivityLog


class ActivityLogRepository:

    def __init__(self, db: Session):
        self._db = db

    def find_all_order_by_created_at_desc(self) -> List[ActivityLog]:
        return self._db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).all()

    def save(self, log: ActivityLog) -> ActivityLog:
        self._db.add(log)
        self._db.flush()
        return log
