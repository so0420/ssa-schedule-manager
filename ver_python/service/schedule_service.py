from datetime import datetime, timedelta
from typing import Optional, List

from entity.activity_log import ActivityLog
from entity.member import Member
from entity.schedule import Schedule
from repository.activity_log_repository import ActivityLogRepository
from repository.member_repository import MemberRepository
from repository.schedule_repository import ScheduleRepository


class ScheduleService:

    def __init__(
        self,
        schedule_repo: ScheduleRepository,
        member_repo: MemberRepository,
        log_repo: ActivityLogRepository,
    ):
        self._schedule_repo = schedule_repo
        self._member_repo = member_repo
        self._log_repo = log_repo

    def create(
        self,
        title: str,
        content: Optional[str],
        start_at: Optional[datetime],
        scheduled_at: datetime,
        tagged_member_ids: Optional[List[int]],
        created_by: Member,
    ) -> Schedule:
        schedule = Schedule()
        schedule.title = title
        schedule.content = content
        schedule.start_at = start_at
        schedule.scheduled_at = scheduled_at
        schedule.created_by = created_by
        schedule.created_by_id = created_by.id
        schedule.created_at = datetime.now()

        if tagged_member_ids:
            schedule.tagged_members = self._member_repo.find_all_by_ids(tagged_member_ids)

        saved = self._schedule_repo.save(schedule)
        self._log_repo.save(ActivityLog(f"일정 등록: {title}", created_by.login_id))
        return saved

    def find_by_id(self, schedule_id: int) -> Optional[Schedule]:
        return self._schedule_repo.find_by_id(schedule_id)

    def get_all(self) -> List[Schedule]:
        return self._schedule_repo.find_all_order_by_scheduled_at_desc()

    def get_upcoming(self) -> List[Schedule]:
        now = datetime.now()
        week_later = now + timedelta(days=7)
        return self._schedule_repo.find_upcoming(now, week_later)

    def search(self, keyword: Optional[str], completed: Optional[bool]) -> List[Schedule]:
        kw = keyword if keyword and keyword.strip() else None
        return self._schedule_repo.search(kw, completed)

    def update(
        self,
        schedule_id: int,
        title: str,
        content: Optional[str],
        start_at: Optional[datetime],
        scheduled_at: datetime,
        tagged_member_ids: Optional[List[int]],
        actor_login_id: str,
    ) -> None:
        schedule = self._schedule_repo.find_by_id(schedule_id)
        if schedule:
            schedule.title = title
            schedule.content = content
            schedule.start_at = start_at
            schedule.scheduled_at = scheduled_at
            if tagged_member_ids is not None:
                schedule.tagged_members = self._member_repo.find_all_by_ids(tagged_member_ids)
            self._schedule_repo.save(schedule)
            self._log_repo.save(ActivityLog(f"일정 수정: {title}", actor_login_id))

    def delete(self, schedule_id: int, actor_login_id: str) -> None:
        schedule = self._schedule_repo.find_by_id(schedule_id)
        if schedule:
            self._log_repo.save(ActivityLog(f"일정 삭제: {schedule.title}", actor_login_id))
            self._schedule_repo.delete(schedule)

    def toggle_complete(self, schedule_id: int, actor_login_id: str) -> None:
        schedule = self._schedule_repo.find_by_id(schedule_id)
        if schedule:
            schedule.completed = not schedule.completed
            self._schedule_repo.save(schedule)
            status = "완료" if schedule.completed else "미완료"
            self._log_repo.save(ActivityLog(f"일정 {status}: {schedule.title}", actor_login_id))

    def auto_complete_expired(self) -> None:
        expired = self._schedule_repo.find_expired(datetime.now())
        for s in expired:
            s.completed = True
            self._schedule_repo.save(s)
            self._log_repo.save(ActivityLog(f"일정 자동 완료: {s.title}", "시스템"))
