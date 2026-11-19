package com.teamschedule.config;

import com.teamschedule.entity.ApprovalStatus;
import com.teamschedule.entity.Member;
import com.teamschedule.entity.Role;
import com.teamschedule.repository.MemberRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

/**
 * 애플리케이션 초기 데이터 설정 클래스.
 * CommandLineRunner를 구현하여, 스프링 부트가 시작된 후 run() 메서드가 자동 실행된다.
 *
 * @Component: 스프링이 이 클래스를 Bean으로 등록하여 관리
 * @RequiredArgsConstructor: final 필드를 인자로 받는 생성자를 자동 생성 (DI 패턴)
 *
 * 역할: DB에 관리자 계정이 없으면 기본 admin 계정을 생성한다.
 * → 최초 실행 시 로그인 가능한 계정이 존재하도록 보장
 */
@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final MemberRepository memberRepository; // 스프링이 자동 주입 (생성자 주입)

    /**
     * 애플리케이션 시작 후 실행되는 메서드.
     * admin 계정이 존재하지 않으면 기본 관리자 계정을 생성한다.
     *
     * @param args 커맨드라인 인자 (사용하지 않음)
     */
    @Override
    public void run(String... args) {
        // admin 계정이 없을 때만 생성 (중복 생성 방지)
        if (memberRepository.findByLoginId("admin").isEmpty()) {
            Member admin = new Member();
            admin.setLoginId("admin");
            admin.setPassword("admin");
            admin.setName("관리자");
            admin.setEmail("admin@team.com");
            admin.setRole(Role.ADMIN);                       // 관리자 역할
            admin.setApprovalStatus(ApprovalStatus.APPROVED); // 승인 상태 (즉시 로그인 가능)
            admin.setCreatedAt(LocalDateTime.now());
            memberRepository.save(admin);
        }
    }
}
