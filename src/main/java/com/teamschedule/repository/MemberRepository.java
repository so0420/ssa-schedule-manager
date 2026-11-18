package com.teamschedule.repository;

import com.teamschedule.entity.ApprovalStatus;
import com.teamschedule.entity.Member;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface MemberRepository extends JpaRepository<Member, Long> {

    Optional<Member> findByLoginId(String loginId);

    Optional<Member> findByEmail(String email);

    Optional<Member> findByLoginIdAndPassword(String loginId, String password);

    List<Member> findByApprovalStatus(ApprovalStatus status);

    List<Member> findByApprovalStatusAndNameContaining(ApprovalStatus status, String name);

    Optional<Member> findByNameAndEmail(String name, String email);
}
