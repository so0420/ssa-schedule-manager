package com.teamschedule.repository;

import com.teamschedule.entity.Schedule;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface ScheduleRepository extends JpaRepository<Schedule, Long> {

    List<Schedule> findByCompletedFalseAndScheduledAtBetweenOrderByScheduledAtAsc(
            LocalDateTime start, LocalDateTime end);

    List<Schedule> findByCompletedFalseAndScheduledAtBeforeAndScheduledAtIsNotNull(
            LocalDateTime now);

    @Query("SELECT s FROM Schedule s WHERE " +
           "(:keyword IS NULL OR s.title LIKE %:keyword% OR s.content LIKE %:keyword%) " +
           "AND (:completed IS NULL OR s.completed = :completed) " +
           "ORDER BY s.scheduledAt DESC")
    List<Schedule> search(@Param("keyword") String keyword,
                          @Param("completed") Boolean completed);

    List<Schedule> findAllByOrderByScheduledAtDesc();
}
