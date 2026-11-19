"""
승인 상태(ApprovalStatus) 열거형 모듈.
회원가입 후 관리자의 승인 절차를 위한 상태값을 정의한다.
"""

import enum


class ApprovalStatus(str, enum.Enum):
    """
    회원 가입 승인 상태를 나타내는 열거형.
    회원가입 시 PENDING으로 시작하며, 관리자가 승인/거절한다.
    """
    PENDING = "PENDING"      # 가입 대기 — 회원가입 직후 초기 상태
    APPROVED = "APPROVED"    # 승인됨 — 관리자가 승인한 상태, 로그인 가능
    REJECTED = "REJECTED"    # 거절됨 — 관리자가 거절한 상태, 로그인 불가
