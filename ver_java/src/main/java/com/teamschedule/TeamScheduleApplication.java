package com.teamschedule;

import com.teamschedule.entity.ApprovalStatus;
import com.teamschedule.entity.Member;
import com.teamschedule.entity.Role;
import com.teamschedule.repository.MemberRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.scheduling.annotation.EnableScheduling;

import java.time.LocalDateTime;

/**
 * TeamSchedule 애플리케이션의 진입점(Entry Point) 클래스.
 *
 * @SpringBootApplication: 아래 세 가지 어노테이션을 한 번에 적용한다.
 *   - @Configuration: 이 클래스가 스프링 설정 클래스임을 나타냄
 *   - @EnableAutoConfiguration: 클래스패스의 의존성을 기반으로 자동 설정
 *   - @ComponentScan: 이 패키지 하위의 @Component, @Service, @Controller 등을 자동 스캔
 *
 * @EnableScheduling: @Scheduled 어노테이션이 붙은 메서드를 주기적으로 실행하도록 활성화
 *   → ScheduleService.autoCompleteExpiredSchedules()가 60초마다 실행됨
 */
@SpringBootApplication
@EnableScheduling
public class TeamScheduleApplication {

    /**
     * 애플리케이션 시작 메서드.
     * SpringApplication.run()으로 내장 톰캣 서버를 시작하고,
     * 스프링 컨텍스트(Bean 컨테이너)를 초기화한다.
     *
     * @param args 커맨드라인 인자
     */
    public static void main(String[] args) {
        SpringApplication.run(TeamScheduleApplication.class, args);
    }

    /**
     * 애플리케이션 최초 실행 시 초기 데이터를 삽입하는 Bean.
     * CommandLineRunner를 반환하면 스프링 부트가 시작된 후 자동으로 실행된다.
     *
     * DB에 회원이 하나도 없으면 관리자(admin) 계정을 생성한다.
     * - ID: admin / PW: admin
     * - 역할: ADMIN, 승인 상태: APPROVED (즉시 로그인 가능)
     *
     * @param memberRepository 회원 레포지토리 (스프링이 자동 주입)
     * @return CommandLineRunner 인스턴스
     */
    @Bean
    CommandLineRunner initData(MemberRepository memberRepository) {
        return args -> {
            if (memberRepository.count() == 0) { // DB에 회원이 없을 때만 실행
                Member admin = new Member();
                admin.setLoginId("admin");
                admin.setPassword("admin");
                admin.setName("관리자");
                admin.setEmail("admin@team.com");
                admin.setRole(Role.ADMIN);                       // 관리자 역할 부여
                admin.setApprovalStatus(ApprovalStatus.APPROVED); // 승인 상태로 설정
                admin.setNotificationEnabled(false);
                admin.setCreatedAt(LocalDateTime.now());
                memberRepository.save(admin);
            }
        };
    }
}
