package com.teamschedule.repository;

import com.teamschedule.entity.ApprovalStatus;
import com.teamschedule.entity.Member;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

/**
 * 회원(Member) 데이터 접근 레포지토리 인터페이스.
 * JpaRepository<Member, Long>을 상속하면 Spring Data JPA가 구현체를 자동 생성한다.
 *
 * JpaRepository가 기본 제공하는 메서드:
 * - save(): 엔티티 저장/수정
 * - findById(): ID로 조회
 * - findAll(): 전체 조회
 * - delete(): 삭제
 * - count(): 개수 조회 등
 *
 * 아래 메서드들은 메서드 이름 규칙에 따라 Spring Data JPA가 자동으로 쿼리를 생성한다.
 * 예: findByLoginId → SELECT * FROM member WHERE login_id = ?
 */
public interface MemberRepository extends JpaRepository<Member, Long> {

    /** loginId로 회원 조회 (로그인, 중복 ID 체크 등에 사용) */
    Optional<Member> findByLoginId(String loginId);

    /** 이메일로 회원 조회 */
    Optional<Member> findByEmail(String email);

    /** loginId와 password가 모두 일치하는 회원 조회 (로그인 인증) */
    Optional<Member> findByLoginIdAndPassword(String loginId, String password);

    /** 특정 승인 상태의 회원 목록 조회 (대기/승인/거절별 필터링) */
    List<Member> findByApprovalStatus(ApprovalStatus status);

    /** 특정 승인 상태 + 이름 포함 검색 (관리자 멤버 검색용) */
    List<Member> findByApprovalStatusAndNameContaining(ApprovalStatus status, String name);

    /** 이름과 이메일로 회원 조회 (ID 찾기 기능에 사용) */
    Optional<Member> findByNameAndEmail(String name, String email);
}
