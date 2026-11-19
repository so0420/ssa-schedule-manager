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

/**
 * 일정 관리 요청을 처리하는 컨트롤러.
 * 일정 CRUD(생성, 조회, 수정, 삭제) 및 완료 처리 기능을 담당한다.
 *
 * @Controller: Spring MVC 컨트롤러
 * @RequestMapping("/schedule"): 모든 URL이 /schedule로 시작
 * @RequiredArgsConstructor: ScheduleService, MemberService를 생성자 주입 (DI)
 */
@Controller
@RequestMapping("/schedule")
@RequiredArgsConstructor
public class ScheduleController {

    private final ScheduleService scheduleService; // 일정 비즈니스 로직 서비스
    private final MemberService memberService;     // 회원 서비스 (태그 가능한 멤버 조회용)

    /**
     * 일정 목록 페이지 표시.
     * GET /schedule
     *
     * 키워드/완료상태 파라미터가 있으면 검색, 없으면 전체 조회.
     * 목록/캘린더/간트 뷰를 모두 이 페이지에서 제공 (뷰 전환은 프론트엔드 JS가 처리).
     *
     * @param keyword   검색 키워드 (선택)
     * @param completed 완료 상태 필터 (선택)
     * @param model     뷰에 전달할 데이터
     * @return 일정 목록 화면 템플릿 경로
     */
    @GetMapping
    public String list(@RequestParam(required = false) String keyword,
                       @RequestParam(required = false) Boolean completed,
                       Model model) {
        List<Schedule> schedules;
        if (keyword != null || completed != null) {
            schedules = scheduleService.search(keyword, completed); // 키워드/상태 검색
        } else {
            schedules = scheduleService.getAll(); // 전체 조회
        }
        model.addAttribute("schedules", schedules);
        model.addAttribute("keyword", keyword);       // 검색 폼에 현재 키워드 유지
        model.addAttribute("completed", completed);   // 필터 상태 유지
        return "schedule/list"; // templates/schedule/list.html 렌더링
    }

    /**
     * 새 일정 등록 폼 페이지 표시.
     * GET /schedule/new
     *
     * 태그 가능한 승인된 멤버 목록을 조회하여 폼에 전달.
     *
     * @param model 뷰에 전달할 데이터
     * @return 일정 등록 폼 화면 템플릿 경로
     */
    @GetMapping("/new")
    public String createForm(Model model) {
        model.addAttribute("members", memberService.getApprovedMembers());
        return "schedule/form"; // templates/schedule/form.html 렌더링
    }

    /**
     * 새 일정 등록 처리.
     * POST /schedule/new
     *
     * 폼에서 입력한 데이터를 받아 일정을 생성하고, 목록으로 리다이렉트.
     * PRG(Post-Redirect-Get) 패턴으로 중복 제출을 방지한다.
     *
     * @param title           일정명
     * @param content         내용/메모 (선택)
     * @param startAt         시작일 문자열 (선택 — null이면 단일일 일정)
     * @param scheduledAt     종료일/일정일 문자열
     * @param taggedMemberIds 태그된 멤버 ID 목록 (선택)
     * @param session         세션에서 로그인 회원 정보 조회
     * @param ra              리다이렉트 시 메시지 전달
     * @return 리다이렉트 URL
     */
    @PostMapping("/new")
    public String create(@RequestParam String title,
                         @RequestParam(required = false) String content,
                         @RequestParam(required = false) String startAt,
                         @RequestParam String scheduledAt,
                         @RequestParam(required = false) List<Long> taggedMemberIds,
                         HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        // 시작일: 빈 문자열이면 null (단일일 일정), 값이 있으면 LocalDateTime으로 파싱
        LocalDateTime startDateTime = (startAt != null && !startAt.isBlank()) ? LocalDateTime.parse(startAt) : null;
        LocalDateTime dateTime = LocalDateTime.parse(scheduledAt);
        scheduleService.create(title, content, startDateTime, dateTime, taggedMemberIds, loginMember);
        ra.addFlashAttribute("message", "일정이 등록되었습니다.");
        return "redirect:/schedule";
    }

    /**
     * 일정 수정 폼 페이지 표시.
     * GET /schedule/{id}/edit
     *
     * @param id    수정할 일정 ID (@PathVariable: URL 경로에서 추출)
     * @param model 뷰에 전달할 데이터
     * @return 일정 수정 폼 화면 (등록 폼과 같은 템플릿 재사용)
     */
    @GetMapping("/{id}/edit")
    public String editForm(@PathVariable Long id, Model model) {
        scheduleService.findById(id).ifPresent(schedule -> {
            model.addAttribute("schedule", schedule);
            // 현재 태그된 멤버 ID 목록을 추출하여 폼에서 선택 상태 유지
            model.addAttribute("taggedIds", schedule.getTaggedMembers().stream()
                    .map(Member::getId).toList());
        });
        model.addAttribute("members", memberService.getApprovedMembers());
        return "schedule/form"; // 등록/수정 폼을 같은 템플릿으로 재사용
    }

    /**
     * 일정 수정 처리.
     * POST /schedule/{id}/edit
     *
     * @param id              수정할 일정 ID
     * @param title           수정할 일정명
     * @param content         수정할 내용 (선택)
     * @param startAt         수정할 시작일 (선택)
     * @param scheduledAt     수정할 종료일
     * @param taggedMemberIds 수정할 태그 멤버 ID 목록 (선택)
     * @param session         세션에서 로그인 회원 정보 조회
     * @param ra              리다이렉트 시 메시지 전달
     * @return 리다이렉트 URL
     */
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

    /**
     * 일정 삭제 처리.
     * POST /schedule/{id}/delete
     *
     * @param id      삭제할 일정 ID
     * @param session 세션에서 로그인 회원 정보 조회
     * @param ra      리다이렉트 시 메시지 전달
     * @return 리다이렉트 URL
     */
    @PostMapping("/{id}/delete")
    public String delete(@PathVariable Long id, HttpSession session, RedirectAttributes ra) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        scheduleService.delete(id, loginMember.getLoginId());
        ra.addFlashAttribute("message", "일정이 삭제되었습니다.");
        return "redirect:/schedule";
    }

    /**
     * 일정 완료/미완료 토글 처리.
     * POST /schedule/{id}/toggle
     *
     * completed 값을 반전(true↔false) 시킨다.
     *
     * @param id      토글할 일정 ID
     * @param session 세션에서 로그인 회원 정보 조회
     * @return 리다이렉트 URL
     */
    @PostMapping("/{id}/toggle")
    public String toggleComplete(@PathVariable Long id, HttpSession session) {
        Member loginMember = (Member) session.getAttribute("loginMember");
        scheduleService.toggleComplete(id, loginMember.getLoginId());
        return "redirect:/schedule";
    }
}
