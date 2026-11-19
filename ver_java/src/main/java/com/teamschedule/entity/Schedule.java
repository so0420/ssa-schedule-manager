package com.teamschedule.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 일정(Schedule) 엔티티 클래스.
 * DB의 schedule 테이블과 매핑되며, 팀 프로젝트의 개별 일정을 나타낸다.
 *
 * 일정 유형:
 * - 단일일 일정: startAt이 null, scheduledAt만 사용
 * - 기간 일정: startAt(시작일) ~ scheduledAt(종료일)
 *
 * 관계:
 * - createdBy: 일정을 생성한 회원 (N:1 관계)
 * - taggedMembers: 일정에 태그된 회원들 (N:M 관계, 중간 테이블 schedule_tag)
 */
@Entity
@Getter @Setter @NoArgsConstructor
public class Schedule {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id; // 일정 고유 식별자

    private String title; // 일정명

    @Column(length = 2000) // 최대 2000자 허용 (기본값 255자보다 넓힘)
    private String content; // 일정 내용/메모

    private LocalDateTime startAt;     // 시작일 (null이면 단일일 일정)
    private LocalDateTime scheduledAt; // 종료일 또는 단일 일정일
    private boolean completed = false; // 완료 여부 (기본값: 미완료)

    /**
     * 일정을 생성한 회원과의 다대일(N:1) 관계.
     * @ManyToOne: 여러 일정이 한 회원에 의해 생성될 수 있음
     * @JoinColumn: DB에 'created_by' 외래키(FK) 컬럼 생성
     */
    @ManyToOne
    @JoinColumn(name = "created_by")
    private Member createdBy;

    /**
     * 일정에 태그된 회원들과의 다대다(N:M) 관계.
     * @ManyToMany: 한 일정에 여러 회원이 태그되고, 한 회원이 여러 일정에 태그될 수 있음
     * @JoinTable: 중간 테이블 'schedule_tag'를 생성하여 관계를 관리
     *   - joinColumns: schedule_tag.schedule_id → schedule.id
     *   - inverseJoinColumns: schedule_tag.member_id → member.id
     */
    @ManyToMany
    @JoinTable(name = "schedule_tag",
            joinColumns = @JoinColumn(name = "schedule_id"),
            inverseJoinColumns = @JoinColumn(name = "member_id"))
    private List<Member> taggedMembers = new ArrayList<>();

    private LocalDateTime createdAt; // 일정 등록 일시
}
