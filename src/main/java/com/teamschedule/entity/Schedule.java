package com.teamschedule.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Getter @Setter @NoArgsConstructor
public class Schedule {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String title;

    @Column(length = 2000)
    private String content;

    private LocalDateTime startAt;
    private LocalDateTime scheduledAt;
    private boolean completed = false;

    @ManyToOne
    @JoinColumn(name = "created_by")
    private Member createdBy;

    @ManyToMany
    @JoinTable(name = "schedule_tag",
            joinColumns = @JoinColumn(name = "schedule_id"),
            inverseJoinColumns = @JoinColumn(name = "member_id"))
    private List<Member> taggedMembers = new ArrayList<>();

    private LocalDateTime createdAt;
}
