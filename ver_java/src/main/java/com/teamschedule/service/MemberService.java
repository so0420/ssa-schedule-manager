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

/**
 * 회원 관련 비즈니스 로직을 처리하는 서비스 클래스.
 * Controller에서 호출되며, Repository를 통해 DB에 접근한다.
 *
 * @Service: 이 클래스가 비즈니스 로직 계층(서비스 계층)임을 나타냄
 * @RequiredArgsConstructor: final 필드들을 인자로 받는 생성자를 자동 생성
 *   → 스프링이 MemberRepository, ActivityLogRepository, ScheduleRepository를 자동 주입 (DI)
 * @Transactional: 이 클래스의 모든 메서드에 트랜잭션을 적용
 *   → 메서드 실행 중 예외 발생 시 DB 변경사항을 자동 롤백
 */
@Service
@RequiredArgsConstructor
@Transactional
public class MemberService {

    private final MemberRepository memberRepository;       // 회원 DB 접근
    private final ActivityLogRepository activityLogRepository; // 활동 로그 DB 접근
    private final ScheduleRepository scheduleRepository;    // 일정 DB 접근 (회원 삭제 시 참조 정리용)

    /**
     * 회원가입 처리.
     * 새 회원을 PENDING(대기) 상태로 생성하고, 활동 로그를 기록한다.
     *
     * @param loginId  로그인 ID
     * @param password 비밀번호
     * @param name     사용자명
     * @param email    이메일
     * @return 저장된 Member 엔티티
     */
    public Member signup(String loginId, String password, String name, String email) {
        Member member = new Member();
        member.setLoginId(loginId);
        member.setPassword(password);
        member.setName(name);
        member.setEmail(email);
        member.setCreatedAt(LocalDateTime.now());
        // Role과 ApprovalStatus는 엔티티 기본값(USER, PENDING) 사용
        Member saved = memberRepository.save(member);
        activityLogRepository.save(new ActivityLog("회원가입 신청: " + loginId, loginId));
        return saved;
    }

    /**
     * 로그인 처리.
     * ID/PW가 일치하고, 승인 상태(APPROVED)인 회원만 로그인 성공.
     *
     * @param loginId  로그인 ID
     * @param password 비밀번호
     * @return 로그인 성공 시 Member, 실패 시 null
     */
    @Transactional(readOnly = true) // 조회 전용 트랜잭션 (성능 최적화)
    public Member login(String loginId, String password) {
        return memberRepository.findByLoginIdAndPassword(loginId, password)
                .filter(m -> m.getApprovalStatus() == ApprovalStatus.APPROVED) // 승인된 회원만 통과
                .orElse(null); // 조건 불일치 시 null 반환
    }

    /**
     * ID로 회원 조회.
     * @param id 회원 ID
     * @return Optional<Member> (존재하지 않을 수 있음)
     */
    @Transactional(readOnly = true)
    public Optional<Member> findById(Long id) {
        return memberRepository.findById(id);
    }

    /**
     * loginId로 회원 조회 (중복 ID 체크에 사용).
     * @param loginId 로그인 ID
     * @return Optional<Member>
     */
    @Transactional(readOnly = true)
    public Optional<Member> findByLoginId(String loginId) {
        return memberRepository.findByLoginId(loginId);
    }

    /**
     * 이름과 이메일로 loginId 찾기 (ID 찾기 기능).
     * @param name  사용자명
     * @param email 이메일
     * @return 일치하는 회원의 loginId, 없으면 null
     */
    @Transactional(readOnly = true)
    public String findLoginIdByNameAndEmail(String name, String email) {
        return memberRepository.findByNameAndEmail(name, email)
                .map(Member::getLoginId) // Member에서 loginId만 추출
                .orElse(null);
    }

    /**
     * loginId와 이메일로 비밀번호 찾기 (비밀번호 힌트 제공).
     * @param loginId 로그인 ID
     * @param email   이메일
     * @return 일치하는 회원의 비밀번호, 없으면 null
     */
    @Transactional(readOnly = true)
    public String findPasswordByLoginIdAndEmail(String loginId, String email) {
        return memberRepository.findByLoginId(loginId)
                .filter(m -> email != null && email.equals(m.getEmail())) // 이메일도 일치하는지 확인
                .map(Member::getPassword)
                .orElse(null);
    }

    /**
     * 사용자명 변경.
     * @param memberId 회원 ID
     * @param newName  새 사용자명
     */
    public void updateName(Long memberId, String newName) {
        memberRepository.findById(memberId).ifPresent(m -> {
            m.setName(newName);
            memberRepository.save(m);
        });
    }

    /**
     * 비밀번호 변경.
     * 현재 비밀번호가 일치하는 경우에만 변경 허용.
     *
     * @param memberId        회원 ID
     * @param currentPassword 현재 비밀번호 (확인용)
     * @param newPassword     새 비밀번호
     * @return 변경 성공 여부
     */
    public boolean updatePassword(Long memberId, String currentPassword, String newPassword) {
        return memberRepository.findById(memberId)
                .filter(m -> m.getPassword().equals(currentPassword)) // 현재 비밀번호 확인
                .map(m -> {
                    m.setPassword(newPassword);
                    memberRepository.save(m);
                    return true;
                }).orElse(false);
    }

    /**
     * 알림 설정 변경.
     * @param memberId 회원 ID
     * @param enabled  알림 활성화 여부
     * @param webhookUrl 웹훅 URL (Discord, Slack 등)
     */
    public void updateNotification(Long memberId, boolean enabled, String webhookUrl) {
        memberRepository.findById(memberId).ifPresent(m -> {
            m.setNotificationEnabled(enabled);
            m.setWebhookUrl(webhookUrl);
            memberRepository.save(m);
        });
    }

    /**
     * 회원 탈퇴 처리.
     * 연관된 일정 참조를 정리한 후, 회원을 삭제한다.
     *
     * @param memberId 탈퇴할 회원 ID
     */
    public void deleteMember(Long memberId) {
        memberRepository.findById(memberId).ifPresent(m -> {
            cleanupMemberReferences(m);  // 일정의 createdBy, taggedMembers에서 참조 제거
            activityLogRepository.save(new ActivityLog("회원 탈퇴: " + m.getLoginId(), m.getLoginId()));
            memberRepository.delete(m);
        });
    }

    /**
     * 가입 대기(PENDING) 상태 회원 목록 조회.
     * @return 대기 중인 회원 목록
     */
    @Transactional(readOnly = true)
    public List<Member> getPendingMembers() {
        return memberRepository.findByApprovalStatus(ApprovalStatus.PENDING);
    }

    /**
     * 승인(APPROVED) 상태 회원 목록 조회.
     * @return 승인된 회원 목록
     */
    @Transactional(readOnly = true)
    public List<Member> getApprovedMembers() {
        return memberRepository.findByApprovalStatus(ApprovalStatus.APPROVED);
    }

    /**
     * 관리자가 회원 가입을 승인.
     * @param memberId  대상 회원 ID
     * @param adminName 승인한 관리자 이름 (로그 기록용)
     */
    public void approveMember(Long memberId, String adminName) {
        memberRepository.findById(memberId).ifPresent(m -> {
            m.setApprovalStatus(ApprovalStatus.APPROVED);
            memberRepository.save(m);
            activityLogRepository.save(new ActivityLog("회원 승인: " + m.getLoginId(), adminName));
        });
    }

    /**
     * 관리자가 회원 가입을 거절.
     * @param memberId  대상 회원 ID
     * @param adminName 거절한 관리자 이름 (로그 기록용)
     */
    public void rejectMember(Long memberId, String adminName) {
        memberRepository.findById(memberId).ifPresent(m -> {
            m.setApprovalStatus(ApprovalStatus.REJECTED);
            memberRepository.save(m);
            activityLogRepository.save(new ActivityLog("회원 거절: " + m.getLoginId(), adminName));
        });
    }

    /**
     * 관리자가 멤버를 추방.
     * 회원 탈퇴와 동일하게 참조 정리 후 삭제하되, 로그에 "멤버 추방"으로 기록.
     *
     * @param memberId  추방할 회원 ID
     * @param adminName 추방한 관리자 이름 (로그 기록용)
     */
    public void kickMember(Long memberId, String adminName) {
        memberRepository.findById(memberId).ifPresent(m -> {
            cleanupMemberReferences(m);
            activityLogRepository.save(new ActivityLog("멤버 추방: " + m.getLoginId(), adminName));
            memberRepository.delete(m);
        });
    }

    /**
     * 전체 활동 로그 조회 (최신순).
     * @return 전체 활동 로그 목록
     */
    @Transactional(readOnly = true)
    public List<ActivityLog> getAllLogs() {
        return activityLogRepository.findAllByOrderByCreatedAtDesc();
    }

    /**
     * 회원 삭제 전, 해당 회원에 대한 일정 참조를 정리하는 private 메서드.
     *
     * 모든 일정을 순회하며:
     * 1. taggedMembers 목록에서 해당 회원을 제거
     * 2. createdBy가 해당 회원인 일정의 createdBy를 null로 설정
     *
     * 이렇게 해야 외래키 제약 위반 없이 회원을 삭제할 수 있다.
     *
     * @param member 삭제할 회원
     */
    private void cleanupMemberReferences(Member member) {
        List<Schedule> allSchedules = scheduleRepository.findAll();
        for (Schedule s : allSchedules) {
            s.getTaggedMembers().remove(member);    // N:M 관계에서 제거
            if (s.getCreatedBy() != null && s.getCreatedBy().getId().equals(member.getId())) {
                s.setCreatedBy(null);                // N:1 관계 해제
            }
            scheduleRepository.save(s);
        }
    }
}
