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

@SpringBootApplication
@EnableScheduling
public class TeamScheduleApplication {

    public static void main(String[] args) {
        SpringApplication.run(TeamScheduleApplication.class, args);
    }

    @Bean
    CommandLineRunner initData(MemberRepository memberRepository) {
        return args -> {
            if (memberRepository.count() == 0) {
                Member admin = new Member();
                admin.setLoginId("admin");
                admin.setPassword("admin");
                admin.setName("관리자");
                admin.setEmail("admin@team.com");
                admin.setRole(Role.ADMIN);
                admin.setApprovalStatus(ApprovalStatus.APPROVED);
                admin.setNotificationEnabled(false);
                admin.setCreatedAt(LocalDateTime.now());
                memberRepository.save(admin);
            }
        };
    }
}
