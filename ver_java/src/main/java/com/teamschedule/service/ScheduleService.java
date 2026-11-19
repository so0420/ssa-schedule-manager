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

@Service
@RequiredArgsConstructor
@Transactional
public class ScheduleService {

    private final ScheduleRepository scheduleRepository;
    private final MemberRepository memberRepository;
    private final ActivityLogRepository activityLogRepository;

    public Schedule create(String title, String content, LocalDateTime startAt, LocalDateTime scheduledAt,
                           List<Long> taggedMemberIds, Member createdBy) {
        Schedule schedule = new Schedule();
        schedule.setTitle(title);
        schedule.setContent(content);
        schedule.setStartAt(startAt);
        schedule.setScheduledAt(scheduledAt);
        schedule.setCreatedBy(createdBy);
        schedule.setCreatedAt(LocalDateTime.now());

        if (taggedMemberIds != null) {
            List<Member> tagged = memberRepository.findAllById(taggedMemberIds);
            schedule.setTaggedMembers(tagged);
        }

        Schedule saved = scheduleRepository.save(schedule);
        activityLogRepository.save(new ActivityLog("일정 등록: " + title, createdBy.getLoginId()));
        return saved;
    }

    public Optional<Schedule> findById(Long id) {
        return scheduleRepository.findById(id);
    }

    public List<Schedule> getAll() {
        return scheduleRepository.findAllByOrderByScheduledAtDesc();
    }

    public List<Schedule> getUpcoming() {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime weekLater = now.plusDays(7);
        return scheduleRepository.findByCompletedFalseAndScheduledAtBetweenOrderByScheduledAtAsc(now, weekLater);
    }

    public List<Schedule> search(String keyword, Boolean completed) {
        String kw = (keyword != null && keyword.isBlank()) ? null : keyword;
        return scheduleRepository.search(kw, completed);
    }

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

    public void delete(Long id, String actorLoginId) {
        scheduleRepository.findById(id).ifPresent(schedule -> {
            activityLogRepository.save(new ActivityLog("일정 삭제: " + schedule.getTitle(), actorLoginId));
            scheduleRepository.delete(schedule);
        });
    }

    public void toggleComplete(Long id, String actorLoginId) {
        scheduleRepository.findById(id).ifPresent(schedule -> {
            schedule.setCompleted(!schedule.isCompleted());
            scheduleRepository.save(schedule);
            String status = schedule.isCompleted() ? "완료" : "미완료";
            activityLogRepository.save(new ActivityLog("일정 " + status + ": " + schedule.getTitle(), actorLoginId));
        });
    }

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
