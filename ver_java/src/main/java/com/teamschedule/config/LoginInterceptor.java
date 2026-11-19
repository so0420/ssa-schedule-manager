package com.teamschedule.config;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 로그인 여부를 확인하는 인터셉터.
 * Spring MVC의 HandlerInterceptor를 구현하여, 모든 HTTP 요청 전에 인증 체크를 수행한다.
 *
 * Spring Security를 사용하지 않는 대신, 이 인터셉터로 간단하게 인증을 처리한다.
 * WebConfig에서 인터셉터를 등록하고, 인증이 필요 없는 경로를 제외(exclude) 설정한다.
 *
 * 동작 흐름:
 * 1. 사용자의 HTTP 요청이 들어옴
 * 2. preHandle()이 호출됨
 * 3. 세션에 loginMember가 있으면 → 요청을 계속 진행 (return true)
 * 4. 세션에 loginMember가 없으면 → 로그인 페이지로 리다이렉트 (return false)
 */
public class LoginInterceptor implements HandlerInterceptor {

    /**
     * 컨트롤러 메서드 실행 전에 호출되는 메서드.
     *
     * @param request  HTTP 요청 객체
     * @param response HTTP 응답 객체
     * @param handler  요청을 처리할 핸들러(컨트롤러 메서드)
     * @return true면 요청 계속 진행, false면 요청 중단
     */
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) throws Exception {
        // getSession(false): 세션이 이미 존재하면 반환, 없으면 null (새로 생성하지 않음)
        HttpSession session = request.getSession(false);

        // 세션이 없거나, 세션에 loginMember 속성이 없으면 → 미인증 상태
        if (session == null || session.getAttribute("loginMember") == null) {
            response.sendRedirect("/auth/login"); // 로그인 페이지로 리다이렉트
            return false; // 요청 중단
        }
        return true; // 인증 통과 → 컨트롤러로 요청 전달
    }
}
