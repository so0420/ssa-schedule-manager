"""
회원(Member) 리포지토리 모듈.
회원 테이블에 대한 모든 데이터 접근(CRUD)을 담당한다.
"""

from typing import Optional, List

from sqlalchemy.orm import Session

from entity.member import Member
from entity.approval_status import ApprovalStatus


class MemberRepository:
    """
    회원 데이터 접근 객체 (Repository 패턴).
    SQLAlchemy Session을 주입받아 member 테이블에 대한 CRUD 작업을 수행한다.
    Service 계층에서만 사용되며, Controller에서 직접 호출하지 않는다.
    Java의 JpaRepository<Member, Long>에 해당한다.
    """

    def __init__(self, db: Session):
        """
        생성자: DB 세션을 주입받아 내부에 저장한다.
        Args:
            db: SQLAlchemy 데이터베이스 세션
        """
        self._db = db  # 캡슐화: 외부에서 직접 접근 불가 (private)

    def find_by_id(self, member_id: int) -> Optional[Member]:
        """
        PK(id)로 회원을 조회한다.
        Args:
            member_id: 조회할 회원의 고유 식별자
        Returns:
            Member 객체 또는 None (존재하지 않을 경우)
        """
        return self._db.query(Member).filter(Member.id == member_id).first()

    def find_by_login_id(self, login_id: str) -> Optional[Member]:
        """
        로그인 ID로 회원을 조회한다. ID 찾기, 중복 체크 등에 사용된다.
        Args:
            login_id: 조회할 로그인 ID
        Returns:
            Member 객체 또는 None
        """
        return self._db.query(Member).filter(Member.login_id == login_id).first()

    def find_by_email(self, email: str) -> Optional[Member]:
        """
        이메일로 회원을 조회한다.
        Args:
            email: 조회할 이메일 주소
        Returns:
            Member 객체 또는 None
        """
        return self._db.query(Member).filter(Member.email == email).first()

    def find_by_login_id_and_password(self, login_id: str, password: str) -> Optional[Member]:
        """
        로그인 ID와 비밀번호로 회원을 조회한다. 로그인 인증에 사용된다.
        Args:
            login_id: 로그인 ID
            password: 비밀번호 (평문 비교 — 학습 프로젝트)
        Returns:
            일치하는 Member 객체 또는 None
        """
        return (
            self._db.query(Member)
            .filter(Member.login_id == login_id, Member.password == password)
            .first()
        )

    def find_by_name_and_email(self, name: str, email: str) -> Optional[Member]:
        """
        이름과 이메일로 회원을 조회한다. ID 찾기 기능에 사용된다.
        Args:
            name: 사용자 이름
            email: 이메일 주소
        Returns:
            일치하는 Member 객체 또는 None
        """
        return (
            self._db.query(Member)
            .filter(Member.name == name, Member.email == email)
            .first()
        )

    def find_by_approval_status(self, status: ApprovalStatus) -> List[Member]:
        """
        승인 상태별 회원 목록을 조회한다. 관리자 멤버 관리 화면에서 사용된다.
        Args:
            status: 조회할 승인 상태 (PENDING, APPROVED, REJECTED)
        Returns:
            해당 상태의 회원 리스트
        """
        return self._db.query(Member).filter(Member.approval_status == status.value).all()

    def find_all(self) -> List[Member]:
        """
        모든 회원을 조회한다.
        Returns:
            전체 회원 리스트
        """
        return self._db.query(Member).all()

    def find_all_by_ids(self, ids: List[int]) -> List[Member]:
        """
        여러 ID에 해당하는 회원들을 한 번에 조회한다.
        일정의 태그된 멤버 목록을 가져올 때 사용된다.
        Args:
            ids: 조회할 회원 ID 리스트
        Returns:
            해당 ID의 회원 리스트 (빈 리스트 가능)
        """
        if not ids:
            return []  # 빈 리스트 전달 시 불필요한 쿼리 방지
        return self._db.query(Member).filter(Member.id.in_(ids)).all()

    def save(self, member: Member) -> Member:
        """
        회원을 저장(신규 생성 또는 수정)한다.
        flush()로 DB에 즉시 반영하고, refresh()로 자동생성된 값(id 등)을 가져온다.
        Args:
            member: 저장할 Member 객체
        Returns:
            저장 완료된 Member 객체 (id가 채워진 상태)
        """
        self._db.add(member)       # 세션에 추가 (이미 존재하면 수정으로 동작)
        self._db.flush()           # DB에 SQL 실행 (아직 커밋은 아님)
        self._db.refresh(member)   # DB에서 최신 상태 다시 로드 (auto-increment id 등)
        return member

    def delete(self, member: Member) -> None:
        """
        회원을 삭제한다. 회원 탈퇴 및 관리자 추방에 사용된다.
        Args:
            member: 삭제할 Member 객체
        """
        self._db.delete(member)
        self._db.flush()
