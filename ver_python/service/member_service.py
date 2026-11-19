"""
회원(Member) 서비스 모듈.
회원 관련 비즈니스 로직을 처리하는 서비스 계층이다.
Controller에서 호출되며, Repository를 통해 데이터를 접근한다.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from entity.activity_log import ActivityLog
from entity.approval_status import ApprovalStatus
from entity.member import Member
from entity.role import Role
from repository.activity_log_repository import ActivityLogRepository
from repository.member_repository import MemberRepository
from repository.schedule_repository import ScheduleRepository


class MemberService:
    """
    회원 비즈니스 로직 처리 클래스.
    회원가입, 로그인, 프로필 수정, 관리자 기능(승인/거절/추방) 등을 담당한다.
    Repository를 주입받아 사용하며, Controller에서 직접 Repository를 호출하지 않는다.
    """

    def __init__(
        self,
        member_repo: MemberRepository,
        log_repo: ActivityLogRepository,
        schedule_repo: ScheduleRepository,
    ):
        """
        생성자: 필요한 Repository들을 주입받는다 (의존성 주입 패턴).
        Args:
            member_repo: 회원 데이터 접근 객체
            log_repo: 활동 로그 데이터 접근 객체
            schedule_repo: 일정 데이터 접근 객체 (멤버 삭제 시 참조 정리용)
        """
        self._member_repo = member_repo
        self._log_repo = log_repo
        self._schedule_repo = schedule_repo

    # ==================== A1. 회원가입 ====================

    def signup(self, db: Session, login_id: str, password: str, name: str, email: str) -> Member:
        """
        새 회원을 등록한다 (유스케이스 A1).
        초기 역할은 USER, 승인 상태는 PENDING으로 설정된다.
        Args:
            db: 데이터베이스 세션
            login_id: 로그인 ID
            password: 비밀번호
            name: 사용자 이름
            email: 이메일 주소
        Returns:
            저장된 Member 객체
        """
        member = Member()
        member.login_id = login_id
        member.password = password
        member.name = name
        member.email = email
        member.role = Role.USER.value
        member.approval_status = ApprovalStatus.PENDING.value
        member.created_at = datetime.now()
        saved = self._member_repo.save(db, member)
        self._log_repo.save(db, ActivityLog(f"회원가입 신청: {login_id}", login_id))
        return saved

    # ==================== A3. 로그인 ====================

    def login(self, db: Session, login_id: str, password: str) -> Optional[Member]:
        """
        로그인 인증을 수행한다 (유스케이스 A3-1).
        ID/비밀번호가 일치하고, 승인 상태가 APPROVED인 경우에만 성공한다.
        Args:
            db: 데이터베이스 세션
            login_id: 로그인 ID
            password: 비밀번호
        Returns:
            인증 성공 시 Member 객체, 실패 시 None
        """
        member = self._member_repo.find_by_login_id_and_password(db, login_id, password)
        if member and member.approval_status == ApprovalStatus.APPROVED.value:
            return member
        return None

    # ==================== 회원 조회 ====================

    def find_by_id(self, db: Session, member_id: int) -> Optional[Member]:
        """ID로 회원을 조회한다."""
        return self._member_repo.find_by_id(db, member_id)

    def find_by_login_id(self, db: Session, login_id: str) -> Optional[Member]:
        """로그인 ID로 회원을 조회한다. 중복 ID 체크에도 사용된다."""
        return self._member_repo.find_by_login_id(db, login_id)

    # ==================== A3-2. ID 찾기 ====================

    def find_login_id_by_name_and_email(self, db: Session, name: str, email: str) -> Optional[str]:
        """
        이름과 이메일로 로그인 ID를 찾는다 (유스케이스 A3-2).
        Args:
            db: 데이터베이스 세션
            name: 사용자 이름
            email: 이메일 주소
        Returns:
            일치하는 로그인 ID 문자열 또는 None
        """
        member = self._member_repo.find_by_name_and_email(db, name, email)
        return member.login_id if member else None

    # ==================== A3-3. 비밀번호 찾기 ====================

    def find_password_by_login_id_and_email(self, db: Session, login_id: str, email: str) -> Optional[str]:
        """
        로그인 ID와 이메일로 비밀번호를 찾는다 (유스케이스 A3-3).
        Args:
            db: 데이터베이스 세션
            login_id: 로그인 ID
            email: 이메일 주소
        Returns:
            일치하는 비밀번호 문자열 또는 None
        """
        member = self._member_repo.find_by_login_id(db, login_id)
        if member and email and member.email == email:
            return member.password
        return None

    # ==================== A2-1. 사용자명 변경 ====================

    def update_name(self, db: Session, member_id: int, new_name: str) -> None:
        """
        사용자 이름을 변경한다 (유스케이스 A2-1).
        Args:
            db: 데이터베이스 세션
            member_id: 회원 ID
            new_name: 새 이름
        """
        member = self._member_repo.find_by_id(db, member_id)
        if member:
            member.name = new_name
            self._member_repo.save(db, member)

    # ==================== A2-2. 비밀번호 변경 ====================

    def update_password(self, db: Session, member_id: int, current_pw: str, new_pw: str) -> bool:
        """
        비밀번호를 변경한다 (유스케이스 A2-2).
        현재 비밀번호가 일치해야 변경 가능하다.
        Args:
            db: 데이터베이스 세션
            member_id: 회원 ID
            current_pw: 현재 비밀번호 (확인용)
            new_pw: 새 비밀번호
        Returns:
            변경 성공 여부 (True/False)
        """
        member = self._member_repo.find_by_id(db, member_id)
        if member and member.password == current_pw:
            member.password = new_pw
            self._member_repo.save(db, member)
            return True
        return False

    # ==================== D1. 알림 설정 ====================

    def update_notification(self, db: Session, member_id: int, enabled: bool, webhook_url: Optional[str]) -> None:
        """
        알림 설정을 변경한다 (유스케이스 D1).
        Args:
            db: 데이터베이스 세션
            member_id: 회원 ID
            enabled: 알림 활성화 여부
            webhook_url: 외부 웹훅 URL (선택)
        """
        member = self._member_repo.find_by_id(db, member_id)
        if member:
            member.notification_enabled = enabled
            member.webhook_url = webhook_url
            self._member_repo.save(db, member)

    # ==================== A5. 회원 탈퇴 ====================

    def delete_member(self, db: Session, member_id: int) -> None:
        """
        회원을 탈퇴시킨다 (유스케이스 A5).
        탈퇴 전 일정의 참조를 정리하고, 활동 로그를 기록한다.
        Args:
            db: 데이터베이스 세션
            member_id: 탈퇴할 회원 ID
        """
        member = self._member_repo.find_by_id(db, member_id)
        if member:
            self._cleanup_member_references(db, member)
            self._log_repo.save(db, ActivityLog(f"회원 탈퇴: {member.login_id}", member.login_id))
            self._member_repo.delete(db, member)

    # ==================== E1. 관리자 — 멤버 관리 ====================

    def get_pending_members(self, db: Session) -> List[Member]:
        """가입 대기(PENDING) 상태 회원 목록을 조회한다."""
        return self._member_repo.find_by_approval_status(db, ApprovalStatus.PENDING)

    def get_approved_members(self, db: Session) -> List[Member]:
        """승인된(APPROVED) 회원 목록을 조회한다."""
        return self._member_repo.find_by_approval_status(db, ApprovalStatus.APPROVED)

    def approve_member(self, db: Session, member_id: int, admin_name: str) -> None:
        """
        회원가입을 승인한다 (유스케이스 E1-1).
        Args:
            db: 데이터베이스 세션
            member_id: 승인할 회원 ID
            admin_name: 승인한 관리자 이름 (로그 기록용)
        """
        member = self._member_repo.find_by_id(db, member_id)
        if member:
            member.approval_status = ApprovalStatus.APPROVED.value
            self._member_repo.save(db, member)
            self._log_repo.save(db, ActivityLog(f"회원 승인: {member.login_id}", admin_name))

    def reject_member(self, db: Session, member_id: int, admin_name: str) -> None:
        """
        회원가입을 거절한다 (유스케이스 E1-1).
        Args:
            db: 데이터베이스 세션
            member_id: 거절할 회원 ID
            admin_name: 거절한 관리자 이름 (로그 기록용)
        """
        member = self._member_repo.find_by_id(db, member_id)
        if member:
            member.approval_status = ApprovalStatus.REJECTED.value
            self._member_repo.save(db, member)
            self._log_repo.save(db, ActivityLog(f"회원 거절: {member.login_id}", admin_name))

    def kick_member(self, db: Session, member_id: int, admin_name: str) -> None:
        """
        멤버를 추방한다 (유스케이스 E1-2).
        추방 전 일정의 참조를 정리하고, 활동 로그를 기록한다.
        Args:
            db: 데이터베이스 세션
            member_id: 추방할 회원 ID
            admin_name: 추방한 관리자 이름 (로그 기록용)
        """
        member = self._member_repo.find_by_id(db, member_id)
        if member:
            self._cleanup_member_references(db, member)
            self._log_repo.save(db, ActivityLog(f"멤버 추방: {member.login_id}", admin_name))
            self._member_repo.delete(db, member)

    # ==================== E2. 활동 로그 조회 ====================

    def get_all_logs(self, db: Session) -> List[ActivityLog]:
        """모든 활동 로그를 최신순으로 조회한다 (유스케이스 E2)."""
        return self._log_repo.find_all_order_by_created_at_desc(db)

    # ==================== Private 메서드 ====================

    def _cleanup_member_references(self, db: Session, member: Member) -> None:
        """
        회원 삭제 전 일정에서 해당 멤버의 참조를 정리한다.
        (1) 태그된 멤버 목록에서 제거
        (2) 작성자가 해당 멤버인 일정의 작성자를 null로 설정
        이렇게 해야 FK 제약조건 위반 없이 멤버를 삭제할 수 있다.
        Args:
            db: 데이터베이스 세션
            member: 삭제될 Member 객체
        """
        all_schedules = self._schedule_repo.find_all(db)
        for s in all_schedules:
            if member in s.tagged_members:
                s.tagged_members.remove(member)
            if s.created_by and s.created_by.id == member.id:
                s.created_by = None
                s.created_by_id = None
            self._schedule_repo.save(db, s)
