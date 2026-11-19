package com.teamschedule.controller;

import com.teamschedule.entity.Member;
import com.teamschedule.entity.Role;
import com.teamschedule.service.MemberService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

/**
 * 관리자(Admin) 전용 요청을 처리하는 컨트롤러.
 * 멤버 가입 승인/거절, 추방, 활동 로그 열람을 담당한다.
 *
 * @Controller: Spring MVC 컨트롤러
 * @RequestMapping("/admin"): 모든 URL이 /admin으로 시작
 * @RequiredArgsConstructor: MemberService를 생성자 주입 (DI)
 *
 * 주의: LoginInterceptor는 "로그인 여부"만 확인하고,
 * "관리자 여부"는 각 메서드 첫 줄에서 직접 체크한다.
 * → ADMIN이 아니면 대시보드(/)로 리다이렉트
 */
@Controller
@RequestMapping("/admin")
@RequiredArgsConstructor
public class AdminController {

    private final MemberService memberService; // 회원 비즈니스 로직 서비스

    /**
     * 멤버 관리 페이지 표시.
     * GET /admin/members
     *
     * 가입 대기(PENDING) 회원과 승인(APPROVED) 회원을 각각 조회하여 표시.
     *
     * @param session 세션에서 로그인 회원 조회 (관리자 체크)
     * @param model   뷰에 전달할 데이터
     * @return 멤버 관리 화면 템플릿 경로
     */
    @GetMapping("/members")
    public String members(HttpSession session, Model model) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        if (loginMember.getRole() != Role.ADMIN) { // 관리자가 아니면 접근 차단
            return "redirect:/";
        }
        model.addAttribute("pendingMembers", memberService.getPendingMembers());   // 가입 대기 목록
        model.addAttribute("approvedMembers", memberService.getApprovedMembers()); // 승인된 멤버 목록
        return "admin/members"; // templates/admin/members.html 렌더링
    }

    /**
     * 멤버 가입 승인 처리.
     * POST /admin/members/{id}/approve
     *
     * 대상 회원의 approvalStatus를 APPROVED로 변경.
     *
     * @param id      승인할 회원 ID (@PathVariable: URL에서 추출)
     * @param session 세션 (관리자 체크 + 관리자 이름 조회)
     * @param ra      리다이렉트 시 메시지 전달
     * @return 리다이렉트 URL
     */
    @PostMapping("/members/{id}/approve")
    public String approve(@PathVariable Long id, HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        if (loginMember.getRole() != Role.ADMIN) return "redirect:/";
        memberService.approveMember(id, loginMember.getName()); // 승인 + 활동 로그 기록
        ra.addFlashAttribute("message", "회원이 승인되었습니다.");
        return "redirect:/admin/members";
    }

    /**
     * 멤버 가입 거절 처리.
     * POST /admin/members/{id}/reject
     *
     * 대상 회원의 approvalStatus를 REJECTED로 변경.
     *
     * @param id      거절할 회원 ID
     * @param session 세션 (관리자 체크)
     * @param ra      리다이렉트 시 메시지 전달
     * @return 리다이렉트 URL
     */
    @PostMapping("/members/{id}/reject")
    public String reject(@PathVariable Long id, HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        if (loginMember.getRole() != Role.ADMIN) return "redirect:/";
        memberService.rejectMember(id, loginMember.getName()); // 거절 + 활동 로그 기록
        ra.addFlashAttribute("message", "회원이 거절되었습니다.");
        return "redirect:/admin/members";
    }

    /**
     * 멤버 추방 처리.
     * POST /admin/members/{id}/kick
     *
     * 대상 회원을 DB에서 삭제하고, 연관 일정 참조를 정리한다.
     *
     * @param id      추방할 회원 ID
     * @param session 세션 (관리자 체크)
     * @param ra      리다이렉트 시 메시지 전달
     * @return 리다이렉트 URL
     */
    @PostMapping("/members/{id}/kick")
    public String kick(@PathVariable Long id, HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        if (loginMember.getRole() != Role.ADMIN) return "redirect:/";
        memberService.kickMember(id, loginMember.getName()); // 참조 정리 + 삭제 + 활동 로그 기록
        ra.addFlashAttribute("message", "멤버가 추방되었습니다.");
        return "redirect:/admin/members";
    }

    /**
     * 활동 로그 열람 페이지 표시.
     * GET /admin/logs
     *
     * 모든 활동 로그를 최신순으로 조회하여 표시.
     *
     * @param session 세션 (관리자 체크)
     * @param model   뷰에 전달할 데이터
     * @return 활동 로그 화면 템플릿 경로
     */
    @GetMapping("/logs")
    public String logs(HttpSession session, Model model) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        if (loginMember.getRole() != Role.ADMIN) return "redirect:/";
        model.addAttribute("logs", memberService.getAllLogs()); // 전체 로그 조회 (최신순)
        return "admin/logs"; // templates/admin/logs.html 렌더링
    }
}
