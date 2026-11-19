from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from entity.schedule import Schedule


class ScheduleRepository:

    def __init__(self, db: Session):
        self._db = db

    def find_by_id(self, schedule_id: int) -> Optional[Schedule]:
        return self._db.query(Schedule).filter(Schedule.id == schedule_id).first()

    def find_all_order_by_scheduled_at_desc(self) -> List[Schedule]:
        return self._db.query(Schedule).order_by(Schedule.scheduled_at.desc()).all()

    def find_upcoming(self, start: datetime, end: datetime) -> List[Schedule]:
        return (
            self._db.query(Schedule)
            .filter(
                Schedule.completed == False,
                Schedule.scheduled_at >= start,
                Schedule.scheduled_at <= end,
            )
            .order_by(Schedule.scheduled_at.asc())
            .all()
        )

    def find_expired(self, now: datetime) -> List[Schedule]:
        return (
            self._db.query(Schedule)
            .filter(
                Schedule.completed == False,
                Schedule.scheduled_at < now,
                Schedule.scheduled_at.isnot(None),
            )
            .all()
        )

    def search(self, keyword: Optional[str], completed: Optional[bool]) -> List[Schedule]:
        query = self._db.query(Schedule)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                (Schedule.title.like(like)) | (Schedule.content.like(like))
            )
        if completed is not None:
            query = query.filter(Schedule.completed == completed)
        return query.order_by(Schedule.scheduled_at.desc()).all()

    def find_all(self) -> List[Schedule]:
        return self._db.query(Schedule).all()

    def save(self, schedule: Schedule) -> Schedule:
        self._db.add(schedule)
        self._db.flush()
        self._db.refresh(schedule)
        return schedule

    def delete(self, schedule: Schedule) -> None:
        self._db.delete(schedule)
        self._db.flush()
