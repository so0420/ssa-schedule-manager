"""
일정(Schedule) 서비스 모듈.
일정 관련 비즈니스 로직을 처리하는 서비스 계층이다.
일정 CRUD, 검색/필터, 자동 완료 기능을 담당한다.
"""

from datetime import datetime, timedelta
from typing import Optional, List

from entity.activity_log import ActivityLog
from entity.member import Member
from entity.schedule import Schedule
from repository.activity_log_repository import ActivityLogRepository
from repository.member_repository import MemberRepository
from repository.schedule_repository import ScheduleRepository


class ScheduleService:
    """
    일정 비즈니스 로직 처리 클래스.
    일정 등록, 조회, 수정, 삭제, 완료 처리 등을 담당한다.
    Repository를 주입받아 사용하며, 모든 활동을 ActivityLog에 기록한다.
    Java의 @Service 클래스에 해당한다.
    """

    def __init__(
        self,
        schedule_repo: ScheduleRepository,
        member_repo: MemberRepository,
        log_repo: ActivityLogRepository,
    ):
        """
        생성자: 필요한 Repository들을 주입받는다 (의존성 주입 패턴).
        Args:
            schedule_repo: 일정 데이터 접근 객체
            member_repo: 회원 데이터 접근 객체 (태그 멤버 조회용)
            log_repo: 활동 로그 데이터 접근 객체
        """
        self._schedule_repo = schedule_repo
        self._member_repo = member_repo
        self._log_repo = log_repo

    # ==================== C1. 일정 등록 ====================

    def create(
        self,
        title: str,
        content: Optional[str],
        start_at: Optional[datetime],
        scheduled_at: datetime,
        tagged_member_ids: Optional[List[int]],
        created_by: Member,
    ) -> Schedule:
        """
        새 일정을 등록한다 (유스케이스 C1).
        Args:
            title: 일정 제목
            content: 일정 내용/메모 (선택)
            start_at: 시작일 (기간 일정인 경우, 단일일이면 None)
            scheduled_at: 종료일 또는 단일 일정일
            tagged_member_ids: 태그할 멤버 ID 목록 (선택)
            created_by: 일정 작성자 Member 객체
        Returns:
            저장된 Schedule 객체
        """
        schedule = Schedule()
        schedule.title = title
        schedule.content = content
        schedule.start_at = start_at           # None이면 단일일 일정
        schedule.scheduled_at = scheduled_at
        schedule.created_by = created_by       # N:1 관계 설정
        schedule.created_by_id = created_by.id
        schedule.created_at = datetime.now()

        # 태그된 멤버가 있으면 N:M 관계 설정
        if tagged_member_ids:
            schedule.tagged_members = self._member_repo.find_all_by_ids(tagged_member_ids)

        saved = self._schedule_repo.save(schedule)
        self._log_repo.save(ActivityLog(f"일정 등록: {title}", created_by.login_id))
        return saved

    # ==================== C2. 일정 조회 ====================

    def find_by_id(self, schedule_id: int) -> Optional[Schedule]:
        """ID로 일정을 조회한다. 수정/삭제 화면에서 사용된다."""
        return self._schedule_repo.find_by_id(schedule_id)

    def get_all(self) -> List[Schedule]:
        """모든 일정을 최신순으로 조회한다. 일정 목록 화면에서 사용된다."""
        return self._schedule_repo.find_all_order_by_scheduled_at_desc()

    def get_upcoming(self) -> List[Schedule]:
        """
        1주일 내 다가오는 미완료 일정을 조회한다 (유스케이스 C2-1).
        대시보드 화면에서 사용된다.
        Returns:
            향후 7일 내 미완료 일정 리스트
        """
        now = datetime.now()
        week_later = now + timedelta(days=7)  # 현재 시각 + 7일
        return self._schedule_repo.find_upcoming(now, week_later)

    def search(self, keyword: Optional[str], completed: Optional[bool]) -> List[Schedule]:
        """
        키워드 및 완료 상태로 일정을 검색한다 (유스케이스 C2-2).
        Args:
            keyword: 검색어 (제목/내용에서 LIKE 검색)
            completed: 완료 상태 필터 (True/False/None)
        Returns:
            검색 결과 일정 리스트
        """
        kw = keyword if keyword and keyword.strip() else None  # 빈 문자열 처리
        return self._schedule_repo.search(kw, completed)

    # ==================== C3. 일정 수정 ====================

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
        """
        기존 일정을 수정한다 (유스케이스 C3).
        Args:
            schedule_id: 수정할 일정 ID
            title: 새 제목
            content: 새 내용
            start_at: 새 시작일 (None이면 단일일)
            scheduled_at: 새 종료일
            tagged_member_ids: 새 태그 멤버 ID 목록
            actor_login_id: 수정한 사용자의 loginId (로그 기록용)
        """
        schedule = self._schedule_repo.find_by_id(schedule_id)
        if schedule:
            schedule.title = title
            schedule.content = content
            schedule.start_at = start_at
            schedule.scheduled_at = scheduled_at
            # 태그 멤버 목록 갱신
            if tagged_member_ids is not None:
                schedule.tagged_members = self._member_repo.find_all_by_ids(tagged_member_ids)
            self._schedule_repo.save(schedule)
            self._log_repo.save(ActivityLog(f"일정 수정: {title}", actor_login_id))

    # ==================== C4. 일정 삭제 ====================

    def delete(self, schedule_id: int, actor_login_id: str) -> None:
        """
        일정을 삭제한다 (유스케이스 C4).
        Args:
            schedule_id: 삭제할 일정 ID
            actor_login_id: 삭제한 사용자의 loginId (로그 기록용)
        """
        schedule = self._schedule_repo.find_by_id(schedule_id)
        if schedule:
            self._log_repo.save(ActivityLog(f"일정 삭제: {schedule.title}", actor_login_id))
            self._schedule_repo.delete(schedule)

    # ==================== C5. 일정 완료 처리 ====================

    def toggle_complete(self, schedule_id: int, actor_login_id: str) -> None:
        """
        일정의 완료 상태를 토글한다 (유스케이스 C5-2 수동 완료).
        완료 → 미완료, 미완료 → 완료로 전환한다.
        Args:
            schedule_id: 토글할 일정 ID
            actor_login_id: 처리한 사용자의 loginId (로그 기록용)
        """
        schedule = self._schedule_repo.find_by_id(schedule_id)
        if schedule:
            schedule.completed = not schedule.completed  # 토글: True ↔ False
            self._schedule_repo.save(schedule)
            status = "완료" if schedule.completed else "미완료"
            self._log_repo.save(ActivityLog(f"일정 {status}: {schedule.title}", actor_login_id))

    # ==================== C5-1. 일정 자동 완료 ====================

    def auto_complete_expired(self) -> None:
        """
        예정일이 지난 미완료 일정을 자동으로 완료 처리한다 (유스케이스 C5-1).
        Java의 @Scheduled(fixedRate = 60000)에 해당하며,
        main.py에서 BackgroundScheduler를 통해 60초마다 호출된다.
        actor는 "시스템"으로 기록된다.
        """
        expired = self._schedule_repo.find_expired(datetime.now())
        for s in expired:
            s.completed = True
            self._schedule_repo.save(s)
            self._log_repo.save(ActivityLog(f"일정 자동 완료: {s.title}", "시스템"))
