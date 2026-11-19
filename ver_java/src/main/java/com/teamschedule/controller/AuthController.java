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
 * 인증(Authentication) 관련 요청을 처리하는 컨트롤러.
 * 로그인, 회원가입, 로그아웃, ID 찾기, 비밀번호 찾기 기능을 담당한다.
 *
 * @Controller: 이 클래스가 Spring MVC 컨트롤러임을 나타냄 (HTML 뷰를 반환)
 * @RequestMapping("/auth"): 이 컨트롤러의 모든 URL이 /auth로 시작
 * @RequiredArgsConstructor: MemberService를 생성자 주입으로 자동 주입 (DI)
 *
 * LoginInterceptor의 excludePathPatterns에 "/auth/**"가 등록되어 있으므로,
 * 이 컨트롤러의 모든 경로는 로그인 없이 접근 가능하다.
 */
@Controller
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final MemberService memberService; // 회원 비즈니스 로직 서비스

    /**
     * 로그인 페이지 표시.
     * GET /auth/login
     *
     * @return 로그인 화면 템플릿 경로
     */
    @GetMapping("/login")
    public String loginForm() {
        return "auth/login"; // templates/auth/login.html 렌더링
    }

    /**
     * 로그인 처리.
     * POST /auth/login
     *
     * 성공 시: 세션에 loginMember 저장 → 대시보드(/)로 리다이렉트
     * 실패 시: 에러 메시지 → 로그인 페이지로 리다이렉트
     *
     * @param loginId  폼에서 입력한 로그인 ID
     * @param password 폼에서 입력한 비밀번호
     * @param session  HTTP 세션 (로그인 정보 저장용)
     * @param ra       리다이렉트 시 일회성 메시지 전달용 (flash attribute)
     * @return 리다이렉트 URL
     */
    @PostMapping("/login")
    public String login(@RequestParam String loginId, @RequestParam String password,
                        HttpSession session, RedirectAttributes ra) {
        Member member = memberService.login(loginId, password);
        if (member == null) {
            // 로그인 실패: flash attribute로 에러 메시지 전달 (리다이렉트 후 1회만 표시)
            ra.addFlashAttribute("error", "로그인 실패: ID/비밀번호를 확인하거나 승인 대기 중입니다.");
            return "redirect:/auth/login";
        }
        // 로그인 성공: 세션에 회원 정보 저장 (LoginInterceptor가 이 값으로 인증 확인)
        session.setAttribute("loginMember", member);
        return "redirect:/";
    }

    /**
     * 회원가입 페이지 표시.
     * GET /auth/signup
     */
    @GetMapping("/signup")
    public String signupForm() {
        return "auth/signup"; // templates/auth/signup.html 렌더링
    }

    /**
     * 회원가입 처리.
     * POST /auth/signup
     *
     * 중복 ID 체크 후, 새 회원을 PENDING 상태로 생성.
     * 관리자 승인 후에야 로그인 가능.
     *
     * @param loginId  가입할 로그인 ID
     * @param password 비밀번호
     * @param name     사용자명
     * @param email    이메일
     * @param ra       리다이렉트 시 메시지 전달용
     * @return 리다이렉트 URL
     */
    @PostMapping("/signup")
    public String signup(@RequestParam String loginId, @RequestParam String password,
                         @RequestParam String name, @RequestParam String email,
                         RedirectAttributes ra) {
        // 중복 ID 체크
        if (memberService.findByLoginId(loginId).isPresent()) {
            ra.addFlashAttribute("error", "이미 사용 중인 ID입니다.");
            return "redirect:/auth/signup";
        }
        memberService.signup(loginId, password, name, email);
        ra.addFlashAttribute("message", "회원가입이 완료되었습니다. 관리자 승인 후 로그인 가능합니다.");
        return "redirect:/auth/login";
    }

    /**
     * 로그아웃 처리.
     * GET /auth/logout
     *
     * 세션을 무효화(invalidate)하여 모든 세션 데이터를 삭제한다.
     */
    @GetMapping("/logout")
    public String logout(HttpSession session) {
        session.invalidate(); // 세션 무효화 → loginMember 포함 모든 데이터 삭제
        return "redirect:/auth/login";
    }

    /**
     * ID 찾기 페이지 표시.
     * GET /auth/find-id
     */
    @GetMapping("/find-id")
    public String findIdForm() {
        return "auth/find-id";
    }

    /**
     * ID 찾기 처리.
     * POST /auth/find-id
     *
     * 이름과 이메일이 일치하는 회원의 loginId를 화면에 표시.
     *
     * @param name  이름
     * @param email 이메일
     * @param model 뷰에 전달할 데이터
     * @return ID 찾기 화면 (결과 포함)
     */
    @PostMapping("/find-id")
    public String findId(@RequestParam String name, @RequestParam String email, Model model) {
        String loginId = memberService.findLoginIdByNameAndEmail(name, email);
        if (loginId != null) {
            model.addAttribute("result", "회원님의 ID는 [ " + loginId + " ] 입니다.");
        } else {
            model.addAttribute("error", "일치하는 회원 정보가 없습니다.");
        }
        return "auth/find-id"; // 같은 페이지에 결과를 표시 (리다이렉트가 아님)
    }

    /**
     * 비밀번호 찾기 페이지 표시.
     * GET /auth/find-password
     */
    @GetMapping("/find-password")
    public String findPasswordForm() {
        return "auth/find-password";
    }

    /**
     * 비밀번호 찾기 처리.
     * POST /auth/find-password
     *
     * loginId와 이메일이 일치하면 비밀번호 힌트(첫 글자 + 마스킹)를 표시.
     *
     * @param loginId 로그인 ID
     * @param email   이메일
     * @param model   뷰에 전달할 데이터
     * @return 비밀번호 찾기 화면 (결과 포함)
     */
    @PostMapping("/find-password")
    public String findPassword(@RequestParam String loginId, @RequestParam String email, Model model) {
        String password = memberService.findPasswordByLoginIdAndEmail(loginId, email);
        if (password != null) {
            // 비밀번호 첫 글자만 보여주고 나머지는 * 처리 (보안)
            String masked = password.substring(0, 1) + "*".repeat(password.length() - 1);
            model.addAttribute("result", "회원님의 비밀번호 힌트: " + masked);
        } else {
            model.addAttribute("error", "일치하는 회원 정보가 없습니다.");
        }
        return "auth/find-password";
    }
}
