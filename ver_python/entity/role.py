"""
역할(Role) 열거형 모듈.
회원의 권한 수준을 정의한다.
"""

import enum


class Role(str, enum.Enum):
    """
    회원 역할을 나타내는 열거형 (Enum).
    str을 상속하여 JSON 직렬화 및 DB 저장 시 문자열로 자동 변환된다.
    """
    USER = "USER"      # 일반 사용자 — 일정 CRUD, 프로필 관리 가능
    ADMIN = "ADMIN"    # 관리자 — 멤버 승인/거절/추방, 활동 로그 열람 가능
