package com.teamschedule.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 회원(Member) 엔티티 클래스.
 * DB의 member 테이블과 매핑되며, 시스템 사용자 정보를 담는다.
 *
 * @Entity: JPA가 이 클래스를 DB 테이블과 매핑하도록 지정
 * @Getter/@Setter: Lombok이 모든 필드의 getter/setter 메서드를 자동 생성
 * @NoArgsConstructor: 기본 생성자를 자동 생성 (JPA 엔티티에 필수)
 */
@Entity
@Getter @Setter @NoArgsConstructor
public class Member {

    @Id // 이 필드가 테이블의 기본키(PK)임을 지정
    @GeneratedValue(strategy = GenerationType.IDENTITY) // DB가 자동으로 ID 증가 (AUTO_INCREMENT)
    private Long id; // 회원 고유 식별자

    @Column(unique = true) // 중복 불가 (DB에 UNIQUE 제약조건 생성)
    private String loginId; // 로그인 ID

    private String password; // 비밀번호 (평문 저장 — 학습 프로젝트이므로 해싱 미적용)
    private String name;     // 사용자명
    private String email;    // 이메일 주소

    @Enumerated(EnumType.STRING) // enum을 문자열("USER"/"ADMIN")로 DB에 저장
    private Role role = Role.USER; // 역할 (기본값: 일반 사용자)

    @Enumerated(EnumType.STRING) // enum을 문자열로 DB에 저장
    private ApprovalStatus approvalStatus = ApprovalStatus.PENDING; // 승인 상태 (기본값: 대기)

    private boolean notificationEnabled = false; // 알림 활성화 여부
    private String webhookUrl;                   // 외부 알림 연동 URL (Discord, Slack 등)

    private LocalDateTime createdAt; // 가입 일시
}
