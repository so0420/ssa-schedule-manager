package com.teamschedule.controller;

import com.teamschedule.entity.Member;
import com.teamschedule.entity.Schedule;
import com.teamschedule.service.MemberService;
import com.teamschedule.service.ScheduleService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.time.LocalDateTime;
import java.util.List;

@Controller
@RequestMapping("/schedule")
@RequiredArgsConstructor
public class ScheduleController {

    private final ScheduleService scheduleService;
    private final MemberService memberService;

    @GetMapping
    public String list(@RequestParam(required = false) String keyword,
                       @RequestParam(required = false) Boolean completed,
                       Model model) {
        List<Schedule> schedules;
        if (keyword != null || completed != null) {
            schedules = scheduleService.search(keyword, completed);
        } else {
            schedules = scheduleService.getAll();
        }
        model.addAttribute("schedules", schedules);
        model.addAttribute("keyword", keyword);
        model.addAttribute("completed", completed);
        return "schedule/list";
    }

    @GetMapping("/new")
    public String createForm(Model model) {
        model.addAttribute("members", memberService.getApprovedMembers());
        return "schedule/form";
    }

    @PostMapping("/new")
    public String create(@RequestParam String title,
                         @RequestParam(required = false) String content,
                         @RequestParam(required = false) String startAt,
                         @RequestParam String scheduledAt,
                         @RequestParam(required = false) List<Long> taggedMemberIds,
                         HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        LocalDateTime startDateTime = (startAt != null && !startAt.isBlank()) ? LocalDateTime.parse(startAt) : null;
        LocalDateTime dateTime = LocalDateTime.parse(scheduledAt);
        scheduleService.create(title, content, startDateTime, dateTime, taggedMemberIds, loginMember);
        ra.addFlashAttribute("message", "일정이 등록되었습니다.");
        return "redirect:/schedule";
    }

    @GetMapping("/{id}/edit")
    public String editForm(@PathVariable Long id, Model model) {
        scheduleService.findById(id).ifPresent(schedule -> {
            model.addAttribute("schedule", schedule);
            model.addAttribute("taggedIds", schedule.getTaggedMembers().stream()
                    .map(Member::getId).toList());
        });
        model.addAttribute("members", memberService.getApprovedMembers());
        return "schedule/form";
    }

    @PostMapping("/{id}/edit")
    public String update(@PathVariable Long id,
                         @RequestParam String title,
                         @RequestParam(required = false) String content,
                         @RequestParam(required = false) String startAt,
                         @RequestParam String scheduledAt,
                         @RequestParam(required = false) List<Long> taggedMemberIds,
                         HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        LocalDateTime startDateTime = (startAt != null && !startAt.isBlank()) ? LocalDateTime.parse(startAt) : null;
        LocalDateTime dateTime = LocalDateTime.parse(scheduledAt);
        scheduleService.update(id, title, content, startDateTime, dateTime, taggedMemberIds, loginMember.getLoginId());
        ra.addFlashAttribute("message", "일정이 수정되었습니다.");
        return "redirect:/schedule";
    }

    @PostMapping("/{id}/delete")
    public String delete(@PathVariable Long id, HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        scheduleService.delete(id, loginMember.getLoginId());
        ra.addFlashAttribute("message", "일정이 삭제되었습니다.");
        return "redirect:/schedule";
    }

    @PostMapping("/{id}/toggle")
    public String toggleComplete(@PathVariable Long id, HttpSession session) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        scheduleService.toggleComplete(id, loginMember.getLoginId());
        return "redirect:/schedule";
    }
}
