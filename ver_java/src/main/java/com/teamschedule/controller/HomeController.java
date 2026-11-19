package com.teamschedule.controller;

import com.teamschedule.entity.Schedule;
import com.teamschedule.service.ScheduleService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

/**
 * 대시보드(메인 페이지) 요청을 처리하는 컨트롤러.
 * 1주일 이내 다가오는 미완료 일정을 조회하여 대시보드에 표시한다.
 *
 * @Controller: Spring MVC 컨트롤러
 * @RequiredArgsConstructor: ScheduleService를 생성자 주입 (DI)
 */
@Controller
@RequiredArgsConstructor
public class HomeController {

    private final ScheduleService scheduleService; // 일정 비즈니스 로직 서비스

    /**
     * 대시보드 페이지 표시.
     * GET /
     *
     * 현재 시각부터 7일 이내의 미완료 일정을 조회하여 모델에 전달.
     *
     * @param model 뷰에 전달할 데이터 (Thymeleaf가 렌더링)
     * @return 대시보드 화면 템플릿 경로
     */
    @GetMapping("/")
    public String home(Model model) {
        List<Schedule> upcoming = scheduleService.getUpcoming(); // 1주일 내 미완료 일정 조회
        model.addAttribute("upcomingSchedules", upcoming);       // 모델에 담아 뷰로 전달
        return "index"; // templates/index.html 렌더링
    }
}
