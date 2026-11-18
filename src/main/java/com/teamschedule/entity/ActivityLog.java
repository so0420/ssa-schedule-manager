package com.teamschedule.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Getter @Setter @NoArgsConstructor
public class ActivityLog {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String action;
    private String actor;
    private LocalDateTime createdAt;

    public ActivityLog(String action, String actor) {
        this.action = action;
        this.actor = actor;
        this.createdAt = LocalDateTime.now();
    }
}
