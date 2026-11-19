package com.teamschedule.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 활동 로그(ActivityLog) 엔티티 클래스.
 * DB의 activity_log 테이블과 매핑되며, 시스템 내 주요 활동을 기록한다.
 * 예: "회원가입 신청: hong", "일정 등록: 중간발표", "멤버 추방: user1"
 *
 * 다른 엔티티와 외래키(FK) 관계가 없다.
 * → actor를 String(loginId)으로 저장하여 회원 탈퇴/추방 후에도 로그가 보존됨
 * → "시스템"이 actor인 경우(자동 완료 등)도 처리 가능
 */
@Entity
@Getter @Setter @NoArgsConstructor
public class ActivityLog {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id; // 로그 고유 식별자

    private String action;          // 수행된 활동 내용 (예: "일정 등록: 중간발표")
    private String actor;           // 활동을 수행한 주체의 loginId (또는 "시스템")
    private LocalDateTime createdAt; // 활동 발생 일시

    /**
     * 로그 생성 편의 생성자.
     * createdAt을 현재 시각으로 자동 설정한다.
     *
     * @param action 활동 내용
     * @param actor  활동 수행자의 loginId
     */
    public ActivityLog(String action, String actor) {
        this.action = action;
        this.actor = actor;
        this.createdAt = LocalDateTime.now();
    }
}
