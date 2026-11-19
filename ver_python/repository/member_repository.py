from typing import Optional, List

from sqlalchemy.orm import Session

from entity.member import Member
from entity.approval_status import ApprovalStatus


class MemberRepository:

    def __init__(self, db: Session):
        self._db = db

    def find_by_id(self, member_id: int) -> Optional[Member]:
        return self._db.query(Member).filter(Member.id == member_id).first()

    def find_by_login_id(self, login_id: str) -> Optional[Member]:
        return self._db.query(Member).filter(Member.login_id == login_id).first()

    def find_by_email(self, email: str) -> Optional[Member]:
        return self._db.query(Member).filter(Member.email == email).first()

    def find_by_login_id_and_password(self, login_id: str, password: str) -> Optional[Member]:
        return (
            self._db.query(Member)
            .filter(Member.login_id == login_id, Member.password == password)
            .first()
        )

    def find_by_name_and_email(self, name: str, email: str) -> Optional[Member]:
        return (
            self._db.query(Member)
            .filter(Member.name == name, Member.email == email)
            .first()
        )

    def find_by_approval_status(self, status: ApprovalStatus) -> List[Member]:
        return self._db.query(Member).filter(Member.approval_status == status.value).all()

    def find_all(self) -> List[Member]:
        return self._db.query(Member).all()

    def find_all_by_ids(self, ids: List[int]) -> List[Member]:
        if not ids:
            return []
        return self._db.query(Member).filter(Member.id.in_(ids)).all()

    def save(self, member: Member) -> Member:
        self._db.add(member)
        self._db.flush()
        self._db.refresh(member)
        return member

    def delete(self, member: Member) -> None:
        self._db.delete(member)
        self._db.flush()
