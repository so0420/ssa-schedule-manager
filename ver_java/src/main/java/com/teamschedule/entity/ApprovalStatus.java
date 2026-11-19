package com.teamschedule.entity;

/**
 * 회원 가입 승인 상태를 정의하는 열거형(Enum).
 * 본 시스템은 승인제로 운영되며, 관리자가 가입을 승인해야 로그인할 수 있다.
 * DB에는 @Enumerated(EnumType.STRING)에 의해 문자열로 저장된다.
 *
 * 상태 전이: PENDING → APPROVED 또는 REJECTED (관리자가 결정)
 */
public enum ApprovalStatus {
    PENDING,   // 가입 대기: 회원가입 직후 초기 상태. 로그인 불가
    APPROVED,  // 승인됨: 관리자가 승인한 상태. 로그인 가능
    REJECTED   // 거절됨: 관리자가 거절한 상태. 로그인 불가
}
