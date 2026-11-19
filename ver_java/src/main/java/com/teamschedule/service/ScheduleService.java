package com.teamschedule.service;

import com.teamschedule.entity.ActivityLog;
import com.teamschedule.entity.Member;
import com.teamschedule.entity.Schedule;
import com.teamschedule.repository.ActivityLogRepository;
import com.teamschedule.repository.MemberRepository;
import com.teamschedule.repository.ScheduleRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 일정 관련 비즈니스 로직을 처리하는 서비스 클래스.
 * Controller에서 호출되며, Repository를 통해 DB에 접근한다.
 *
 * @Service: 서비스 계층 Bean으로 등록
 * @RequiredArgsConstructor: 생성자 주입으로 Repository들을 자동 주입 (DI)
 * @Transactional: 모든 메서드에 트랜잭션 적용
 */
@Service
@RequiredArgsConstructor
@Transactional
public class ScheduleService {

    private final ScheduleRepository scheduleRepository;       // 일정 DB 접근
    private final MemberRepository memberRepository;           // 회원 DB 접근 (태그된 멤버 조회용)
    private final ActivityLogRepository activityLogRepository; // 활동 로그 DB 접근

    /**
     * 새 일정 등록.
     * 일정 정보를 받아 Schedule 엔티티를 생성하고 저장한다.
     *
     * @param title           일정명
     * @param content         내용/메모 (nullable)
     * @param startAt         시작일 (null이면 단일일 일정)
     * @param scheduledAt     종료일 또는 단일 일정일
     * @param taggedMemberIds 태그할 회원 ID 목록 (nullable)
     * @param createdBy       일정을 생성한 회원
     * @return 저장된 Schedule 엔티티
     */
    public Schedule create(String title, String content, LocalDateTime startAt, LocalDateTime scheduledAt,
                           List<Long> taggedMemberIds, Member createdBy) {
        Schedule schedule = new Schedule();
        schedule.setTitle(title);
        schedule.setContent(content);
        schedule.setStartAt(startAt);       // null이면 단일일, 값이 있으면 기간 시작일
        schedule.setScheduledAt(scheduledAt);
        schedule.setCreatedBy(createdBy);
        schedule.setCreatedAt(LocalDateTime.now());

        // 태그된 멤버 ID 목록을 실제 Member 엔티티 목록으로 변환하여 설정
        if (taggedMemberIds != null) {
            List<Member> tagged = memberRepository.findAllById(taggedMemberIds);
            schedule.setTaggedMembers(tagged);
        }

        Schedule saved = scheduleRepository.save(schedule);
        activityLogRepository.save(new ActivityLog("일정 등록: " + title, createdBy.getLoginId()));
        return saved;
    }

    /**
     * ID로 일정 조회.
     * @param id 일정 ID
     * @return Optional<Schedule>
     */
    public Optional<Schedule> findById(Long id) {
        return scheduleRepository.findById(id);
    }

    /**
     * 전체 일정 조회 (scheduledAt 내림차순).
     * @return 전체 일정 목록
     */
    public List<Schedule> getAll() {
        return scheduleRepository.findAllByOrderByScheduledAtDesc();
    }

    /**
     * 1주일 이내 다가오는 미완료 일정 조회 (대시보드용).
     * @return 1주일 내 예정된 미완료 일정 목록
     */
    public List<Schedule> getUpcoming() {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime weekLater = now.plusDays(7);
        return scheduleRepository.findByCompletedFalseAndScheduledAtBetweenOrderByScheduledAtAsc(now, weekLater);
    }

    /**
     * 키워드/완료상태 기반 일정 검색.
     * @param keyword   검색 키워드 (일정명/내용에 포함 여부)
     * @param completed 완료 상태 필터 (null이면 전체)
     * @return 검색 결과 일정 목록
     */
    public List<Schedule> search(String keyword, Boolean completed) {
        // 빈 문자열을 null로 변환 (JPQL에서 null은 조건 무시)
        String kw = (keyword != null && keyword.isBlank()) ? null : keyword;
        return scheduleRepository.search(kw, completed);
    }

    /**
     * 일정 수정.
     * ID로 일정을 찾아 필드를 업데이트하고 저장한다.
     *
     * @param id              일정 ID
     * @param title           수정할 일정명
     * @param content         수정할 내용
     * @param startAt         수정할 시작일 (null이면 단일일로 변경)
     * @param scheduledAt     수정할 종료일
     * @param taggedMemberIds 수정할 태그 회원 ID 목록
     * @param actorLoginId    수정한 사용자의 loginId (로그 기록용)
     */
    public void update(Long id, String title, String content, LocalDateTime startAt, LocalDateTime scheduledAt,
                       List<Long> taggedMemberIds, String actorLoginId) {
        scheduleRepository.findById(id).ifPresent(schedule -> {
            schedule.setTitle(title);
            schedule.setContent(content);
            schedule.setStartAt(startAt);
            schedule.setScheduledAt(scheduledAt);

            if (taggedMemberIds != null) {
                List<Member> tagged = memberRepository.findAllById(taggedMemberIds);
                schedule.setTaggedMembers(tagged);
            }

            scheduleRepository.save(schedule);
            activityLogRepository.save(new ActivityLog("일정 수정: " + title, actorLoginId));
        });
    }

    /**
     * 일정 삭제.
     * @param id           삭제할 일정 ID
     * @param actorLoginId 삭제한 사용자의 loginId (로그 기록용)
     */
    public void delete(Long id, String actorLoginId) {
        scheduleRepository.findById(id).ifPresent(schedule -> {
            activityLogRepository.save(new ActivityLog("일정 삭제: " + schedule.getTitle(), actorLoginId));
            scheduleRepository.delete(schedule);
        });
    }

    /**
     * 일정 완료/미완료 토글.
     * completed 필드를 반전시킨다 (true ↔ false).
     *
     * @param id           토글할 일정 ID
     * @param actorLoginId 토글한 사용자의 loginId (로그 기록용)
     */
    public void toggleComplete(Long id, String actorLoginId) {
        scheduleRepository.findById(id).ifPresent(schedule -> {
            schedule.setCompleted(!schedule.isCompleted()); // 완료 상태 반전
            scheduleRepository.save(schedule);
            String status = schedule.isCompleted() ? "완료" : "미완료";
            activityLogRepository.save(new ActivityLog("일정 " + status + ": " + schedule.getTitle(), actorLoginId));
        });
    }

    /**
     * 만료된 일정을 자동으로 완료 처리하는 스케줄러 메서드.
     *
     * @Scheduled(fixedRate = 60000): 60초(1분)마다 주기적으로 실행
     *   → @EnableScheduling (TeamScheduleApplication)에 의해 활성화됨
     *
     * scheduledAt이 현재 시각 이전이고 미완료인 일정을 찾아 자동 완료 처리.
     * actor는 "시스템"으로 기록하여 사용자 직접 완료와 구분한다.
     */
    @Scheduled(fixedRate = 60000)
    public void autoCompleteExpiredSchedules() {
        List<Schedule> expired = scheduleRepository
                .findByCompletedFalseAndScheduledAtBeforeAndScheduledAtIsNotNull(LocalDateTime.now());
        for (Schedule s : expired) {
            s.setCompleted(true);
            scheduleRepository.save(s);
            activityLogRepository.save(new ActivityLog("일정 자동 완료: " + s.getTitle(), "시스템"));
        }
    }
}
