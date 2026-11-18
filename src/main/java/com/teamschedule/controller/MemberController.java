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

@Controller
@RequestMapping("/member")
@RequiredArgsConstructor
public class MemberController {

    private final MemberService memberService;

    @GetMapping("/profile")
    public String profile(HttpSession session, Model model) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        var member = memberService.findById(loginMember.getId());
        if (member.isEmpty()) {
            session.invalidate();
            return "redirect:/auth/login";
        }
        model.addAttribute("member", member.get());
        return "member/profile";
    }

    @PostMapping("/update-name")
    public String updateName(@RequestParam String name, HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        memberService.updateName(loginMember.getId(), name);
        loginMember.setName(name);
        session.setAttribute("loginMember", loginMember);
        ra.addFlashAttribute("message", "사용자명이 변경되었습니다.");
        return "redirect:/member/profile";
    }

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

    @PostMapping("/update-notification")
    public String updateNotification(@RequestParam(defaultValue = "false") boolean notificationEnabled,
                                     @RequestParam(required = false) String webhookUrl,
                                     HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        memberService.updateNotification(loginMember.getId(), notificationEnabled, webhookUrl);
        loginMember.setNotificationEnabled(notificationEnabled);
        loginMember.setWebhookUrl(webhookUrl);
        session.setAttribute("loginMember", loginMember);
        ra.addFlashAttribute("message", "알림 설정이 변경되었습니다.");
        return "redirect:/member/profile";
    }

    @PostMapping("/delete")
    public String deleteMember(HttpSession session) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        memberService.deleteMember(loginMember.getId());
        session.invalidate();
        return "redirect:/auth/login";
    }
}
