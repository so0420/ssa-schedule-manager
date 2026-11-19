"""
회원(Member) 엔티티 모듈.
DB의 member 테이블과 매핑되는 SQLAlchemy ORM 모델이다.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base
from entity.role import Role
from entity.approval_status import ApprovalStatus


class Member(Base):
    """
    회원 엔티티 클래스.
    시스템의 모든 사용자(일반 회원, 관리자) 정보를 담는 도메인 객체이다.
    JPA의 @Entity에 해당하며, SQLAlchemy의 declarative 매핑을 사용한다.
    """
    __tablename__ = "member"  # 매핑되는 DB 테이블명

    # === 기본 식별 필드 ===
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)          # PK, 자동 증가
    login_id: Mapped[str] = mapped_column(String(100), unique=True)                # 로그인 ID (고유값)
    password: Mapped[str] = mapped_column(String(255))                             # 비밀번호 (평문 저장 — 학습 프로젝트)
    name: Mapped[str] = mapped_column(String(100))                                 # 사용자 이름
    email: Mapped[str] = mapped_column(String(255))                                # 이메일 주소

    # === 권한/상태 필드 ===
    role: Mapped[str] = mapped_column(String(20), default=Role.USER.value)         # 역할 (USER 또는 ADMIN)
    approval_status: Mapped[str] = mapped_column(                                  # 가입 승인 상태
        String(20), default=ApprovalStatus.PENDING.value                           # 기본값: PENDING (승인 대기)
    )

    # === 알림 설정 필드 ===
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=False)     # 알림 활성화 여부
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # 외부 알림 웹훅 URL (선택)

    # === 메타 정보 ===
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 가입 일시

    def to_session_dict(self) -> dict:
        """
        세션에 저장할 회원 정보를 딕셔너리로 변환한다.
        비밀번호는 보안상 세션에 저장하지 않는다.
        Returns:
            세션 저장용 딕셔너리 (password 제외)
        """
        return {
            "id": self.id,
            "login_id": self.login_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "approval_status": self.approval_status,
            "notification_enabled": self.notification_enabled,
            "webhook_url": self.webhook_url,
        }
