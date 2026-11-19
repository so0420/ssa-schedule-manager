package com.teamschedule.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Spring MVC 설정 클래스.
 * WebMvcConfigurer를 구현하여 인터셉터를 등록한다.
 *
 * @Configuration: 이 클래스가 스프링 설정 파일임을 나타냄
 *   → 스프링이 시작될 때 이 클래스를 읽어 설정을 적용함
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    /**
     * 인터셉터를 등록하는 메서드.
     * LoginInterceptor를 모든 경로(/**)에 적용하되,
     * 인증 없이 접근 가능한 경로들은 제외한다.
     *
     * @param registry 인터셉터 등록기
     */
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoginInterceptor())
                .addPathPatterns("/**")          // 모든 경로에 인터셉터 적용
                .excludePathPatterns(
                        "/auth/**",              // 로그인/회원가입/ID찾기/비밀번호찾기 (인증 전 접근 필요)
                        "/service/**",           // 이용약관/개인정보처리방침 (비로그인 상태에서도 열람 가능)
                        "/css/**", "/js/**",     // 정적 리소스 (CSS, JavaScript 파일)
                        "/h2-console/**"         // H2 데이터베이스 웹 콘솔 (개발/디버깅용)
                );
    }
}
