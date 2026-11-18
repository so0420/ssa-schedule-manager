package com.teamschedule.service;

import com.teamschedule.entity.ActivityLog;
import com.teamschedule.entity.ApprovalStatus;
import com.teamschedule.entity.Member;
import com.teamschedule.entity.Schedule;
import com.teamschedule.repository.ActivityLogRepository;
import com.teamschedule.repository.MemberRepository;
import com.teamschedule.repository.ScheduleRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
@Transactional
public class MemberService {

    private final MemberRepository memberRepository;
    private final ActivityLogRepository activityLogRepository;
    private final ScheduleRepository scheduleRepository;

    public Member signup(String loginId, String password, String name, String email) {
        Member member = new Member();
        member.setLoginId(loginId);
        member.setPassword(password);
        member.setName(name);
        member.setEmail(email);
        member.setCreatedAt(LocalDateTime.now());
        Member saved = memberRepository.save(member);
        activityLogRepository.save(new ActivityLog("회원가입 신청: " + loginId, loginId));
        return saved;
    }

    @Transactional(readOnly = true)
    public Member login(String loginId, String password) {
        return memberRepository.findByLoginIdAndPassword(loginId, password)
                .filter(m -> m.getApprovalStatus() == ApprovalStatus.APPROVED)
                .orElse(null);
    }

    @Transactional(readOnly = true)
    public Optional<Member> findById(Long id) {
        return memberRepository.findById(id);
    }

    @Transactional(readOnly = true)
    public Optional<Member> findByLoginId(String loginId) {
        return memberRepository.findByLoginId(loginId);
    }

    @Transactional(readOnly = true)
    public String findLoginIdByNameAndEmail(String name, String email) {
        return memberRepository.findByNameAndEmail(name, email)
                .map(Member::getLoginId)
                .orElse(null);
    }

    @Transactional(readOnly = true)
    public String findPasswordByLoginIdAndEmail(String loginId, String email) {
        return memberRepository.findByLoginId(loginId)
                .filter(m -> email != null && email.equals(m.getEmail()))
                .map(Member::getPassword)
                .orElse(null);
    }

    public void updateName(Long memberId, String newName) {
        memberRepository.findById(memberId).ifPresent(m -> {
            m.setName(newName);
            memberRepository.save(m);
        });
    }

    public boolean updatePassword(Long memberId, String currentPassword, String newPassword) {
        return memberRepository.findById(memberId)
                .filter(m -> m.getPassword().equals(currentPassword))
                .map(m -> {
                    m.setPassword(newPassword);
                    memberRepository.save(m);
                    return true;
                }).orElse(false);
    }

    public void updateNotification(Long memberId, boolean enabled, String webhookUrl) {
        memberRepository.findById(memberId).ifPresent(m -> {
            m.setNotificationEnabled(enabled);
            m.setWebhookUrl(webhookUrl);
            memberRepository.save(m);
        });
    }

    public void deleteMember(Long memberId) {
        memberRepository.findById(memberId).ifPresent(m -> {
            cleanupMemberReferences(m);
            activityLogRepository.save(new ActivityLog("회원 탈퇴: " + m.getLoginId(), m.getLoginId()));
            memberRepository.delete(m);
        });
    }

    @Transactional(readOnly = true)
    public List<Member> getPendingMembers() {
        return memberRepository.findByApprovalStatus(ApprovalStatus.PENDING);
    }

    @Transactional(readOnly = true)
    public List<Member> getApprovedMembers() {
        return memberRepository.findByApprovalStatus(ApprovalStatus.APPROVED);
    }

    public void approveMember(Long memberId, String adminName) {
        memberRepository.findById(memberId).ifPresent(m -> {
            m.setApprovalStatus(ApprovalStatus.APPROVED);
            memberRepository.save(m);
            activityLogRepository.save(new ActivityLog("회원 승인: " + m.getLoginId(), adminName));
        });
    }

    public void rejectMember(Long memberId, String adminName) {
        memberRepository.findById(memberId).ifPresent(m -> {
            m.setApprovalStatus(ApprovalStatus.REJECTED);
            memberRepository.save(m);
            activityLogRepository.save(new ActivityLog("회원 거절: " + m.getLoginId(), adminName));
        });
    }

    public void kickMember(Long memberId, String adminName) {
        memberRepository.findById(memberId).ifPresent(m -> {
            cleanupMemberReferences(m);
            activityLogRepository.save(new ActivityLog("멤버 추방: " + m.getLoginId(), adminName));
            memberRepository.delete(m);
        });
    }

    @Transactional(readOnly = true)
    public List<ActivityLog> getAllLogs() {
        return activityLogRepository.findAllByOrderByCreatedAtDesc();
    }

    private void cleanupMemberReferences(Member member) {
        List<Schedule> allSchedules = scheduleRepository.findAll();
        for (Schedule s : allSchedules) {
            s.getTaggedMembers().remove(member);
            if (s.getCreatedBy() != null && s.getCreatedBy().getId().equals(member.getId())) {
                s.setCreatedBy(null);
            }
            scheduleRepository.save(s);
        }
    }
}
