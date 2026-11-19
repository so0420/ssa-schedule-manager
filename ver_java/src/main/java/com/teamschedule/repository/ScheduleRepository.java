package com.teamschedule.repository;

import com.teamschedule.entity.Schedule;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 일정(Schedule) 데이터 접근 레포지토리 인터페이스.
 * JpaRepository를 상속하여 기본 CRUD 메서드를 자동 제공받는다.
 */
public interface ScheduleRepository extends JpaRepository<Schedule, Long> {

    /**
     * 1주일 이내 다가오는 미완료 일정 조회 (대시보드용).
     * completed = false이고, scheduledAt이 start~end 범위인 일정을 시간순 정렬하여 반환.
     *
     * @param start 조회 시작 시각 (보통 현재 시각)
     * @param end   조회 종료 시각 (보통 현재 + 7일)
     * @return 미완료 일정 목록 (시간순 오름차순)
     */
    List<Schedule> findByCompletedFalseAndScheduledAtBetweenOrderByScheduledAtAsc(
            LocalDateTime start, LocalDateTime end);

    /**
     * 만료된 미완료 일정 조회 (자동 완료 스케줄러용).
     * completed = false이고, scheduledAt이 현재 시각 이전인 일정을 반환.
     *
     * @param now 현재 시각
     * @return 만료된 미완료 일정 목록
     */
    List<Schedule> findByCompletedFalseAndScheduledAtBeforeAndScheduledAtIsNotNull(
            LocalDateTime now);

    /**
     * 키워드 및 완료 상태로 일정 검색 (일정 목록 필터링용).
     * JPQL(Java Persistence Query Language)로 직접 작성한 커스텀 쿼리.
     *
     * - keyword가 null이면 키워드 조건 무시
     * - completed가 null이면 상태 조건 무시
     * - scheduledAt 기준 내림차순 정렬
     *
     * @param keyword   검색 키워드 (일정명 또는 내용에 포함 여부)
     * @param completed 완료 상태 필터 (true/false/null)
     * @return 조건에 맞는 일정 목록
     */
    @Query("SELECT s FROM Schedule s WHERE " +
           "(:keyword IS NULL OR s.title LIKE %:keyword% OR s.content LIKE %:keyword%) " +
           "AND (:completed IS NULL OR s.completed = :completed) " +
           "ORDER BY s.scheduledAt DESC")
    List<Schedule> search(@Param("keyword") String keyword,
                          @Param("completed") Boolean completed);

    /** 전체 일정을 scheduledAt 내림차순으로 조회 (최신 일정이 먼저) */
    List<Schedule> findAllByOrderByScheduledAtDesc();
}
