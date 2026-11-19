from datetime import datetime
from typing import Optional, List

from entity.activity_log import ActivityLog
from entity.approval_status import ApprovalStatus
from entity.member import Member
from entity.role import Role
from repository.activity_log_repository import ActivityLogRepository
from repository.member_repository import MemberRepository
from repository.schedule_repository import ScheduleRepository


class MemberService:

    def __init__(
        self,
        member_repo: MemberRepository,
        log_repo: ActivityLogRepository,
        schedule_repo: ScheduleRepository,
    ):
        self._member_repo = member_repo
        self._log_repo = log_repo
        self._schedule_repo = schedule_repo

    def signup(self, login_id: str, password: str, name: str, email: str) -> Member:
        member = Member()
        member.login_id = login_id
        member.password = password
        member.name = name
        member.email = email
        member.role = Role.USER.value
        member.approval_status = ApprovalStatus.PENDING.value
        member.created_at = datetime.now()
        saved = self._member_repo.save(member)
        self._log_repo.save(ActivityLog(f"회원가입 신청: {login_id}", login_id))
        return saved

    def login(self, login_id: str, password: str) -> Optional[Member]:
        member = self._member_repo.find_by_login_id_and_password(login_id, password)
        if member and member.approval_status == ApprovalStatus.APPROVED.value:
            return member
        return None

    def find_by_id(self, member_id: int) -> Optional[Member]:
        return self._member_repo.find_by_id(member_id)

    def find_by_login_id(self, login_id: str) -> Optional[Member]:
        return self._member_repo.find_by_login_id(login_id)

    def find_login_id_by_name_and_email(self, name: str, email: str) -> Optional[str]:
        member = self._member_repo.find_by_name_and_email(name, email)
        return member.login_id if member else None

    def find_password_by_login_id_and_email(self, login_id: str, email: str) -> Optional[str]:
        member = self._member_repo.find_by_login_id(login_id)
        if member and email and member.email == email:
            return member.password
        return None

    def update_name(self, member_id: int, new_name: str) -> None:
        member = self._member_repo.find_by_id(member_id)
        if member:
            member.name = new_name
            self._member_repo.save(member)

    def update_password(self, member_id: int, current_pw: str, new_pw: str) -> bool:
        member = self._member_repo.find_by_id(member_id)
        if member and member.password == current_pw:
            member.password = new_pw
            self._member_repo.save(member)
            return True
        return False

    def update_notification(self, member_id: int, enabled: bool, webhook_url: Optional[str]) -> None:
        member = self._member_repo.find_by_id(member_id)
        if member:
            member.notification_enabled = enabled
            member.webhook_url = webhook_url
            self._member_repo.save(member)

    def delete_member(self, member_id: int) -> None:
        member = self._member_repo.find_by_id(member_id)
        if member:
            self._cleanup_member_references(member)
            self._log_repo.save(ActivityLog(f"회원 탈퇴: {member.login_id}", member.login_id))
            self._member_repo.delete(member)

    def get_pending_members(self) -> List[Member]:
        return self._member_repo.find_by_approval_status(ApprovalStatus.PENDING)

    def get_approved_members(self) -> List[Member]:
        return self._member_repo.find_by_approval_status(ApprovalStatus.APPROVED)

    def approve_member(self, member_id: int, admin_name: str) -> None:
        member = self._member_repo.find_by_id(member_id)
        if member:
            member.approval_status = ApprovalStatus.APPROVED.value
            self._member_repo.save(member)
            self._log_repo.save(ActivityLog(f"회원 승인: {member.login_id}", admin_name))

    def reject_member(self, member_id: int, admin_name: str) -> None:
        member = self._member_repo.find_by_id(member_id)
        if member:
            member.approval_status = ApprovalStatus.REJECTED.value
            self._member_repo.save(member)
            self._log_repo.save(ActivityLog(f"회원 거절: {member.login_id}", admin_name))

    def kick_member(self, member_id: int, admin_name: str) -> None:
        member = self._member_repo.find_by_id(member_id)
        if member:
            self._cleanup_member_references(member)
            self._log_repo.save(ActivityLog(f"멤버 추방: {member.login_id}", admin_name))
            self._member_repo.delete(member)

    def get_all_logs(self) -> List[ActivityLog]:
        return self._log_repo.find_all_order_by_created_at_desc()

    def _cleanup_member_references(self, member: Member) -> None:
        all_schedules = self._schedule_repo.find_all()
        for s in all_schedules:
            if member in s.tagged_members:
                s.tagged_members.remove(member)
            if s.created_by and s.created_by.id == member.id:
                s.created_by = None
                s.created_by_id = None
            self._schedule_repo.save(s)
