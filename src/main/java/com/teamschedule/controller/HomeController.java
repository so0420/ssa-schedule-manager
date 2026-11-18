package com.teamschedule.controller;

import com.teamschedule.entity.Schedule;
import com.teamschedule.service.ScheduleService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@Controller
@RequiredArgsConstructor
public class HomeController {

    private final ScheduleService scheduleService;

    @GetMapping("/")
    public String home(Model model) {
        List<Schedule> upcoming = scheduleService.getUpcoming();
        model.addAttribute("upcomingSchedules", upcoming);
        return "index";
    }
}
