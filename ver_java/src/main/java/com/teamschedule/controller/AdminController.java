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

@Controller
@RequestMapping("/admin")
@RequiredArgsConstructor
public class AdminController {

    private final MemberService memberService;

    @GetMapping("/members")
    public String members(HttpSession session, Model model) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        if (loginMember.getRole() != Role.ADMIN) {
            return "redirect:/";
        }
        model.addAttribute("pendingMembers", memberService.getPendingMembers());
        model.addAttribute("approvedMembers", memberService.getApprovedMembers());
        return "admin/members";
    }

    @PostMapping("/members/{id}/approve")
    public String approve(@PathVariable Long id, HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        if (loginMember.getRole() != Role.ADMIN) return "redirect:/";
        memberService.approveMember(id, loginMember.getName());
        ra.addFlashAttribute("message", "회원이 승인되었습니다.");
        return "redirect:/admin/members";
    }

    @PostMapping("/members/{id}/reject")
    public String reject(@PathVariable Long id, HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        if (loginMember.getRole() != Role.ADMIN) return "redirect:/";
        memberService.rejectMember(id, loginMember.getName());
        ra.addFlashAttribute("message", "회원이 거절되었습니다.");
        return "redirect:/admin/members";
    }

    @PostMapping("/members/{id}/kick")
    public String kick(@PathVariable Long id, HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        if (loginMember.getRole() != Role.ADMIN) return "redirect:/";
        memberService.kickMember(id, loginMember.getName());
        ra.addFlashAttribute("message", "멤버가 추방되었습니다.");
        return "redirect:/admin/members";
    }

    @GetMapping("/logs")
    public String logs(HttpSession session, Model model) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        if (loginMember.getRole() != Role.ADMIN) return "redirect:/";
        model.addAttribute("logs", memberService.getAllLogs());
        return "admin/logs";
    }
}
