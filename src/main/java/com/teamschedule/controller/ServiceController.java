package com.teamschedule.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/service")
public class ServiceController {

    @GetMapping("/terms")
    public String terms() {
        return "service/terms";
    }

    @GetMapping("/privacy")
    public String privacy() {
        return "service/privacy";
    }
}
