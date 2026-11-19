package com.teamschedule.repository;

import com.teamschedule.entity.ActivityLog;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

/**
 * 활동 로그(ActivityLog) 데이터 접근 레포지토리 인터페이스.
 * JpaRepository를 상속하여 기본 CRUD 메서드를 자동 제공받는다.
 */
public interface ActivityLogRepository extends JpaRepository<ActivityLog, Long> {

    /**
     * 모든 활동 로그를 생성일시 내림차순으로 조회 (최신 로그가 먼저).
     * 관리자의 활동 로그 열람 화면에서 사용된다.
     *
     * @return 전체 활동 로그 목록 (최신순)
     */
    List<ActivityLog> findAllByOrderByCreatedAtDesc();
}
