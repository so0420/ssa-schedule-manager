package com.teamschedule.entity;

/**
 * 회원 역할(권한)을 정의하는 열거형(Enum).
 * DB에는 @Enumerated(EnumType.STRING)에 의해 문자열("USER", "ADMIN")로 저장된다.
 */
public enum Role {
    USER,  // 일반 사용자: 일정 관리, 프로필 수정 등 기본 기능 사용
    ADMIN  // 관리자: 일반 사용자 기능 + 멤버 승인/거절/추방, 활동 로그 열람
}
