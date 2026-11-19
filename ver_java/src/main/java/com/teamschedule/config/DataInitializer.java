package com.teamschedule.config;

import com.teamschedule.entity.ApprovalStatus;
import com.teamschedule.entity.Member;
import com.teamschedule.entity.Role;
import com.teamschedule.repository.MemberRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final MemberRepository memberRepository;

    @Override
    public void run(String... args) {
        if (memberRepository.findByLoginId("admin").isEmpty()) {
            Member admin = new Member();
            admin.setLoginId("admin");
            admin.setPassword("admin");
            admin.setName("관리자");
            admin.setEmail("admin@team.com");
            admin.setRole(Role.ADMIN);
            admin.setApprovalStatus(ApprovalStatus.APPROVED);
            admin.setCreatedAt(LocalDateTime.now());
            memberRepository.save(admin);
        }
    }
}
