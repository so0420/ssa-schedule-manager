package com.teamschedule.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

/**
 * 서비스 정보 페이지 요청을 처리하는 컨트롤러.
 * 이용약관, 개인정보처리방침 열람 기능을 담당한다.
 *
 * @Controller: Spring MVC 컨트롤러
 * @RequestMapping("/service"): 모든 URL이 /service로 시작
 *
 * LoginInterceptor의 excludePathPatterns에 "/service/**"가 등록되어 있으므로,
 * 로그인하지 않은 사용자도 이 페이지에 접근할 수 있다.
 *
 * 별도의 Service 계층 호출 없이, 정적 HTML 템플릿만 반환한다.
 */
@Controller
@RequestMapping("/service")
public class ServiceController {

    /**
     * 이용약관 페이지 표시.
     * GET /service/terms
     *
     * @return 이용약관 화면 템플릿 경로
     */
    @GetMapping("/terms")
    public String terms() {
        return "service/terms"; // templates/service/terms.html 렌더링
    }

    /**
     * 개인정보처리방침 페이지 표시.
     * GET /service/privacy
     *
     * @return 개인정보처리방침 화면 템플릿 경로
     */
    @GetMapping("/privacy")
    public String privacy() {
        return "service/privacy"; // templates/service/privacy.html 렌더링
    }
}
