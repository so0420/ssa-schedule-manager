"""
활동 로그(ActivityLog) 리포지토리 모듈.
활동 로그 테이블에 대한 데이터 접근을 담당한다.
"""

from typing import List

from sqlalchemy.orm import Session

from entity.activity_log import ActivityLog


class ActivityLogRepository:
    """
    활동 로그 데이터 접근 객체 (Repository 패턴).
    로그는 조회와 저장만 수행하며, 수정/삭제는 하지 않는다.
    (로그는 한 번 기록되면 변경하지 않는 것이 원칙)
    """

    def find_all_order_by_created_at_desc(self, db: Session) -> List[ActivityLog]:
        """
        모든 활동 로그를 최신순으로 조회한다.
        관리자 로그 열람 화면에서 사용된다.
        Args:
            db: SQLAlchemy 데이터베이스 세션
        Returns:
            전체 활동 로그 리스트 (최신순)
        """
        return db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).all()

    def save(self, db: Session, log: ActivityLog) -> ActivityLog:
        """
        활동 로그를 저장한다.
        Args:
            db: SQLAlchemy 데이터베이스 세션
            log: 저장할 ActivityLog 객체
        Returns:
            저장 완료된 ActivityLog 객체
        """
        db.add(log)
        db.flush()
        return log
