"""
일정(Schedule) 리포지토리 모듈.
일정 테이블에 대한 모든 데이터 접근(CRUD)과 검색/필터를 담당한다.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from entity.schedule import Schedule


class ScheduleRepository:
    """
    일정 데이터 접근 객체 (Repository 패턴).
    SQLAlchemy Session을 주입받아 schedule 테이블에 대한 CRUD 작업을 수행한다.
    Java의 JpaRepository<Schedule, Long>에 해당하며, 커스텀 쿼리 메서드를 포함한다.
    """

    def __init__(self, db: Session):
        """
        생성자: DB 세션을 주입받아 내부에 저장한다.
        Args:
            db: SQLAlchemy 데이터베이스 세션
        """
        self._db = db  # 캡슐화: 외부 접근 불가

    def find_by_id(self, schedule_id: int) -> Optional[Schedule]:
        """
        PK(id)로 일정을 조회한다.
        Args:
            schedule_id: 조회할 일정의 고유 식별자
        Returns:
            Schedule 객체 또는 None
        """
        return self._db.query(Schedule).filter(Schedule.id == schedule_id).first()

    def find_all_order_by_scheduled_at_desc(self) -> List[Schedule]:
        """
        모든 일정을 예정일 기준 최신순으로 조회한다.
        일정 목록 화면에서 사용된다.
        Returns:
            일정 리스트 (최신순 정렬)
        """
        return self._db.query(Schedule).order_by(Schedule.scheduled_at.desc()).all()

    def find_upcoming(self, start: datetime, end: datetime) -> List[Schedule]:
        """
        특정 기간 내 미완료 일정을 조회한다. 대시보드의 '다가오는 일정'에 사용된다.
        Args:
            start: 조회 시작 일시 (보통 현재 시각)
            end: 조회 종료 일시 (보통 7일 후)
        Returns:
            해당 기간의 미완료 일정 리스트 (날짜순 오름차순)
        """
        return (
            self._db.query(Schedule)
            .filter(
                Schedule.completed == False,       # 미완료 일정만
                Schedule.scheduled_at >= start,    # 시작일 이후
                Schedule.scheduled_at <= end,      # 종료일 이전
            )
            .order_by(Schedule.scheduled_at.asc())  # 가까운 일정부터
            .all()
        )

    def find_expired(self, now: datetime) -> List[Schedule]:
        """
        예정일이 지났지만 미완료인 일정을 조회한다.
        자동 완료 스케줄러(@Scheduled 대응)에서 사용된다.
        Args:
            now: 현재 시각
        Returns:
            만료된 미완료 일정 리스트
        """
        return (
            self._db.query(Schedule)
            .filter(
                Schedule.completed == False,          # 미완료
                Schedule.scheduled_at < now,          # 예정일이 지남
                Schedule.scheduled_at.isnot(None),    # 예정일이 설정된 일정만
            )
            .all()
        )

    def search(self, keyword: Optional[str], completed: Optional[bool]) -> List[Schedule]:
        """
        키워드 및 완료 상태로 일정을 검색한다.
        일정 목록의 필터/검색 기능에 사용된다.
        Args:
            keyword: 검색어 (제목 또는 내용에 포함 — LIKE 검색). None이면 필터 안 함
            completed: 완료 상태 필터. None이면 필터 안 함
        Returns:
            조건에 맞는 일정 리스트 (최신순)
        """
        query = self._db.query(Schedule)
        if keyword:
            like = f"%{keyword}%"  # LIKE 패턴 생성
            query = query.filter(
                (Schedule.title.like(like)) | (Schedule.content.like(like))  # 제목 OR 내용
            )
        if completed is not None:
            query = query.filter(Schedule.completed == completed)
        return query.order_by(Schedule.scheduled_at.desc()).all()

    def find_all(self) -> List[Schedule]:
        """
        모든 일정을 조회한다. 멤버 탈퇴 시 참조 정리에 사용된다.
        Returns:
            전체 일정 리스트
        """
        return self._db.query(Schedule).all()

    def save(self, schedule: Schedule) -> Schedule:
        """
        일정을 저장(신규 생성 또는 수정)한다.
        Args:
            schedule: 저장할 Schedule 객체
        Returns:
            저장 완료된 Schedule 객체
        """
        self._db.add(schedule)
        self._db.flush()
        self._db.refresh(schedule)
        return schedule

    def delete(self, schedule: Schedule) -> None:
        """
        일정을 삭제한다.
        Args:
            schedule: 삭제할 Schedule 객체
        """
        self._db.delete(schedule)
        self._db.flush()
