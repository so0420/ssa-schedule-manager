package com.teamschedule.controller;

import com.teamschedule.entity.Member;
import com.teamschedule.service.MemberService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

/**
 * 개인 정보 관리 요청을 처리하는 컨트롤러.
 * 프로필 조회, 사용자명/비밀번호 변경, 알림 설정, 회원 탈퇴를 담당한다.
 *
 * @Controller: Spring MVC 컨트롤러
 * @RequestMapping("/member"): 모든 URL이 /member로 시작
 * @RequiredArgsConstructor: MemberService를 생성자 주입 (DI)
 */
@Controller
@RequestMapping("/member")
@RequiredArgsConstructor
public class MemberController {

    private final MemberService memberService; // 회원 비즈니스 로직 서비스

    /**
     * 프로필 페이지 표시.
     * GET /member/profile
     *
     * 세션의 loginMember ID로 DB에서 최신 회원 정보를 조회하여 표시.
     * 회원이 존재하지 않으면(탈퇴된 경우) 세션 무효화 후 로그인 페이지로 이동.
     *
     * @param session 세션에서 로그인 회원 정보 조회
     * @param model   뷰에 전달할 데이터
     * @return 프로필 화면 템플릿 경로
     */
    @GetMapping("/profile")
    public String profile(HttpSession session, Model model) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        var member = memberService.findById(loginMember.getId());
        if (member.isEmpty()) {
            session.invalidate(); // 회원이 삭제된 경우 세션 무효화
            return "redirect:/auth/login";
        }
        model.addAttribute("member", member.get());
        return "member/profile"; // templates/member/profile.html 렌더링
    }

    /**
     * 사용자명 변경 처리.
     * POST /member/update-name
     *
     * DB와 세션의 사용자명을 모두 업데이트한다.
     *
     * @param name    새 사용자명
     * @param session 세션 (세션 내 loginMember 갱신용)
     * @param ra      리다이렉트 시 메시지 전달
     * @return 리다이렉트 URL
     */
    @PostMapping("/update-name")
    public String updateName(@RequestParam String name, HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        memberService.updateName(loginMember.getId(), name);
        // 세션에도 변경된 이름을 반영 (다음 요청부터 사이드바 등에 새 이름 표시)
        loginMember.setName(name);
        session.setAttribute("loginMember", loginMember);
        ra.addFlashAttribute("message", "사용자명이 변경되었습니다.");
        return "redirect:/member/profile";
    }

    /**
     * 비밀번호 변경 처리.
     * POST /member/update-password
     *
     * 현재 비밀번호가 일치하는 경우에만 변경 허용.
     *
     * @param currentPassword 현재 비밀번호 (확인용)
     * @param newPassword     새 비밀번호
     * @param session         세션
     * @param ra              리다이렉트 시 메시지 전달
     * @return 리다이렉트 URL
     */
    @PostMapping("/update-password")
    public String updatePassword(@RequestParam String currentPassword,
                                 @RequestParam String newPassword,
                                 HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        boolean success = memberService.updatePassword(loginMember.getId(), currentPassword, newPassword);
        if (success) {
            ra.addFlashAttribute("message", "비밀번호가 변경되었습니다.");
        } else {
            ra.addFlashAttribute("error", "현재 비밀번호가 일치하지 않습니다.");
        }
        return "redirect:/member/profile";
    }

    /**
     * 알림 설정 변경 처리.
     * POST /member/update-notification
     *
     * @param notificationEnabled 알림 활성화 여부 (체크박스 → 미체크 시 false)
     * @param webhookUrl          웹훅 URL (선택)
     * @param session             세션 (세션 내 알림 설정 갱신용)
     * @param ra                  리다이렉트 시 메시지 전달
     * @return 리다이렉트 URL
     */
    @PostMapping("/update-notification")
    public String updateNotification(@RequestParam(defaultValue = "false") boolean notificationEnabled,
                                     @RequestParam(required = false) String webhookUrl,
                                     HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        memberService.updateNotification(loginMember.getId(), notificationEnabled, webhookUrl);
        // 세션에도 변경사항 반영
        loginMember.setNotificationEnabled(notificationEnabled);
        loginMember.setWebhookUrl(webhookUrl);
        session.setAttribute("loginMember", loginMember);
        ra.addFlashAttribute("message", "알림 설정이 변경되었습니다.");
        return "redirect:/member/profile";
    }

    /**
     * 회원 탈퇴 처리.
     * POST /member/delete
     *
     * 회원 데이터를 삭제하고 세션을 무효화한다.
     * MemberService.deleteMember()가 연관 일정 참조도 정리한다.
     *
     * @param session 세션 (무효화용)
     * @return 리다이렉트 URL (로그인 페이지)
     */
    @PostMapping("/delete")
    public String deleteMember(HttpSession session) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        memberService.deleteMember(loginMember.getId());
        session.invalidate(); // 세션 무효화 → 로그아웃 처리
        return "redirect:/auth/login";
    }
}
