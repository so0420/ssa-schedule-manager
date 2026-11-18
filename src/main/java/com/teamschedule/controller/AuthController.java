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
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final MemberService memberService;

    @GetMapping("/login")
    public String loginForm() {
        return "auth/login";
    }

    @PostMapping("/login")
    public String login(@RequestParam String loginId, @RequestParam String password,
                        HttpSession session, RedirectAttributes ra) {
        Member member = memberService.login(loginId, password);
        if (member == null) {
            ra.addFlashAttribute("error", "로그인 실패: ID/비밀번호를 확인하거나 승인 대기 중입니다.");
            return "redirect:/auth/login";
        }
        session.setAttribute("loginMember", member);
        return "redirect:/";
    }

    @GetMapping("/signup")
    public String signupForm() {
        return "auth/signup";
    }

    @PostMapping("/signup")
    public String signup(@RequestParam String loginId, @RequestParam String password,
                         @RequestParam String name, @RequestParam String email,
                         RedirectAttributes ra) {
        if (memberService.findByLoginId(loginId).isPresent()) {
            ra.addFlashAttribute("error", "이미 사용 중인 ID입니다.");
            return "redirect:/auth/signup";
        }
        memberService.signup(loginId, password, name, email);
        ra.addFlashAttribute("message", "회원가입이 완료되었습니다. 관리자 승인 후 로그인 가능합니다.");
        return "redirect:/auth/login";
    }

    @GetMapping("/logout")
    public String logout(HttpSession session) {
        session.invalidate();
        return "redirect:/auth/login";
    }

    @GetMapping("/find-id")
    public String findIdForm() {
        return "auth/find-id";
    }

    @PostMapping("/find-id")
    public String findId(@RequestParam String name, @RequestParam String email, Model model) {
        String loginId = memberService.findLoginIdByNameAndEmail(name, email);
        if (loginId != null) {
            model.addAttribute("result", "회원님의 ID는 [ " + loginId + " ] 입니다.");
        } else {
            model.addAttribute("error", "일치하는 회원 정보가 없습니다.");
        }
        return "auth/find-id";
    }

    @GetMapping("/find-password")
    public String findPasswordForm() {
        return "auth/find-password";
    }

    @PostMapping("/find-password")
    public String findPassword(@RequestParam String loginId, @RequestParam String email, Model model) {
        String password = memberService.findPasswordByLoginIdAndEmail(loginId, email);
        if (password != null) {
            String masked = password.substring(0, 1) + "*".repeat(password.length() - 1);
            model.addAttribute("result", "회원님의 비밀번호 힌트: " + masked);
        } else {
            model.addAttribute("error", "일치하는 회원 정보가 없습니다.");
        }
        return "auth/find-password";
    }
}
