# TeamSchedule 시스템 설명서

> **과목**: 소프트웨어시스템분석및설계  
> **프로젝트**: 팀 프로젝트 일정 관리 웹 애플리케이션  
> **버전**: 1.0.0

---

## 1. 프로젝트 개요

### 1.1 목적
팀 프로젝트 일정을 등록, 조회, 수정, 삭제할 수 있는 웹 기반 일정 관리 시스템이다. 팀원 간 일정 공유, 멤버 태그, 승인제 회원 관리, 활동 로그 추적 등의 기능을 제공한다.

### 1.2 기술 스택

| 구분 | 기술 | 버전 |
|------|------|------|
| 언어 | Java | 17 |
| 프레임워크 | Spring Boot | 3.2.0 |
| ORM | Spring Data JPA (Hibernate) | - |
| 템플릿 엔진 | Thymeleaf | - |
| 데이터베이스 | H2 (파일 모드) | - |
| 빌드 도구 | Gradle | 8.5 |
| 코드 간소화 | Lombok | - |

### 1.3 의존성 (build.gradle)
```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'       // Spring MVC
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'  // JPA/Hibernate
    implementation 'org.springframework.boot:spring-boot-starter-thymeleaf' // 템플릿 엔진
    compileOnly 'org.projectlombok:lombok'                                 // 보일러플레이트 제거
    annotationProcessor 'org.projectlombok:lombok'
    runtimeOnly 'com.h2database:h2'                                        // H2 DB
}
```

### 1.4 설계 원칙
- **백엔드 구조 최대한 단순화**: 개발자가 모든 구조를 꿰고 있을 수 있도록, UML 작성 용이하게, 구조 관련 질문에 쉽게 답변 가능하도록 설계
- **Spring Security 미사용**: HttpSession + HandlerInterceptor로 인증 처리 (구조 단순화 목적)
- **프론트엔드 라이브러리 미사용**: 순수 JavaScript로 캘린더, 간트 차트 구현

---

## 2. 시스템 아키텍처

### 2.1 전체 구조 — MVC 패턴

```
[사용자 브라우저]
      │
      ▼
┌─────────────────────────────────────────────┐
│  Presentation Layer (Controller + Template) │
│  - AuthController, ScheduleController, ...  │
│  - Thymeleaf HTML 템플릿                     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Business Logic Layer (Service)             │
│  - MemberService, ScheduleService           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Data Access Layer (Repository)             │
│  - MemberRepository, ScheduleRepository,    │
│    ActivityLogRepository                    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Database (H2 File)                         │
│  - ./data/teamschedule.mv.db               │
└─────────────────────────────────────────────┘
```

**MVC 패턴 적용:**
- **Model**: entity 패키지의 JPA 엔티티 클래스들 (Member, Schedule, ActivityLog)
- **View**: Thymeleaf 템플릿 (.html 파일들)
- **Controller**: controller 패키지의 `@Controller` 클래스들

### 2.2 패키지 구조

```
com.teamschedule
├── TeamScheduleApplication.java      ← 애플리케이션 진입점 (@SpringBootApplication, @EnableScheduling)
├── entity/                           ← JPA 엔티티 (도메인 모델)
│   ├── Member.java                   ← 회원 엔티티
│   ├── Schedule.java                 ← 일정 엔티티
│   ├── ActivityLog.java              ← 활동 로그 엔티티
│   ├── Role.java                     ← 역할 열거형 (USER, ADMIN)
│   └── ApprovalStatus.java           ← 승인 상태 열거형 (PENDING, APPROVED, REJECTED)
├── repository/                       ← 데이터 접근 계층 (JpaRepository 인터페이스)
│   ├── MemberRepository.java
│   ├── ScheduleRepository.java
│   └── ActivityLogRepository.java
├── service/                          ← 비즈니스 로직 계층
│   ├── MemberService.java            ← 회원 관련 비즈니스 로직
│   └── ScheduleService.java          ← 일정 관련 비즈니스 로직
├── controller/                       ← HTTP 요청 처리
│   ├── AuthController.java           ← 인증 (로그인, 회원가입, 로그아웃, ID/PW 찾기)
│   ├── HomeController.java           ← 대시보드 (/)
│   ├── ScheduleController.java       ← 일정 CRUD
│   ├── MemberController.java         ← 프로필 관리 (개인정보 수정, 알림, 탈퇴)
│   ├── AdminController.java          ← 관리자 기능 (멤버 관리, 로그)
│   └── ServiceController.java        ← 이용약관, 개인정보처리방침
└── config/                           ← 설정
    ├── LoginInterceptor.java         ← 로그인 인터셉터 (인증 체크)
    ├── WebConfig.java                ← 인터셉터 등록 및 경로 설정
    └── DataInitializer.java          ← 초기 관리자 계정 생성
```

### 2.3 계층 간 의존 관계

```
Controller → Service → Repository → Database
                ↓
           ActivityLog (모든 주요 동작을 로그로 기록)
```

- **Controller**는 Service만 의존한다. Repository를 직접 호출하지 않는다.
- **Service**는 Repository를 의존하여 DB 접근을 수행한다.
- **Repository**는 `JpaRepository<Entity, Long>`을 상속하며, Spring Data JPA가 구현체를 자동 생성한다.

---

## 3. 엔티티 설계

### 3.1 Member (회원)

```java
@Entity
public class Member {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;                        // PK, 자동 증가

    @Column(unique = true)
    private String loginId;                 // 로그인 ID (유니크 제약)

    private String password;                // 비밀번호 (평문 저장)
    private String name;                    // 사용자명 (표시 이름)
    private String email;                   // 이메일

    @Enumerated(EnumType.STRING)
    private Role role = Role.USER;          // 역할 (기본값: USER)

    @Enumerated(EnumType.STRING)
    private ApprovalStatus approvalStatus   // 승인 상태 (기본값: PENDING)
        = ApprovalStatus.PENDING;

    private boolean notificationEnabled     // 알림 활성화 여부
        = false;
    private String webhookUrl;              // 외부 알림 웹훅 URL

    private LocalDateTime createdAt;        // 가입일시
}
```

**필드별 설명:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | Long | 기본키. `IDENTITY` 전략으로 DB가 자동 증가값을 생성 |
| `loginId` | String | 로그인에 사용하는 고유 ID. `@Column(unique = true)`로 중복 방지 |
| `password` | String | 비밀번호. 학습 프로젝트이므로 평문 저장 (실서비스에서는 BCrypt 등 해싱 필요) |
| `name` | String | 화면에 표시되는 사용자명. 프로필 페이지에서 변경 가능 |
| `email` | String | 이메일. ID 찾기/비밀번호 찾기에 사용 |
| `role` | Role(enum) | `USER` 또는 `ADMIN`. 관리자 페이지 접근 권한 결정 |
| `approvalStatus` | ApprovalStatus(enum) | `PENDING`(가입 대기), `APPROVED`(승인), `REJECTED`(거절). 승인된 회원만 로그인 가능 |
| `notificationEnabled` | boolean | 알림 기능 ON/OFF |
| `webhookUrl` | String | Discord/Slack 등 외부 서비스 웹훅 URL |
| `createdAt` | LocalDateTime | 회원가입 시점. `MemberService.signup()`에서 `LocalDateTime.now()`로 설정 |

### 3.2 Role (역할 열거형)

```java
public enum Role {
    USER,   // 일반 사용자
    ADMIN   // 관리자 — 멤버 승인/거절/추방, 로그 열람 가능
}
```

### 3.3 ApprovalStatus (승인 상태 열거형)

```java
public enum ApprovalStatus {
    PENDING,   // 가입 대기 — 회원가입 직후 기본 상태
    APPROVED,  // 승인됨 — 로그인 가능
    REJECTED   // 거절됨 — 로그인 불가
}
```

**승인 흐름:** 회원가입 → `PENDING` → 관리자가 승인 → `APPROVED` (또는 거절 → `REJECTED`)

### 3.4 Schedule (일정)

```java
@Entity
public class Schedule {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;                // PK

    private String title;           // 일정명

    @Column(length = 2000)
    private String content;         // 내용/메모 (최대 2000자)

    private LocalDateTime startAt;      // 시작일 (기간 일정의 시작. null이면 단일일 일정)
    private LocalDateTime scheduledAt;  // 종료일 또는 단일 일정일

    private boolean completed = false;  // 완료 여부

    @ManyToOne
    @JoinColumn(name = "created_by")
    private Member createdBy;       // 작성자 (N:1 관계)

    @ManyToMany
    @JoinTable(name = "schedule_tag",
        joinColumns = @JoinColumn(name = "schedule_id"),
        inverseJoinColumns = @JoinColumn(name = "member_id"))
    private List<Member> taggedMembers = new ArrayList<>();  // 태그된 멤버 (N:M 관계)

    private LocalDateTime createdAt;    // 등록일시
}
```

**일정 유형 설계 — startAt nullable 패턴:**

| 유형 | startAt | scheduledAt | 의미 |
|------|---------|-------------|------|
| 단일일 일정 | `null` | `2024-12-25 09:00` | 12/25 하루짜리 일정 |
| 기간 일정 | `2024-12-20 09:00` | `2024-12-25 18:00` | 12/20 ~ 12/25 기간 일정 |

이 설계의 장점: 기존 단일일 일정과 완전히 하위 호환. `startAt`이 null이면 단일일, 값이 있으면 기간. 백엔드에 필드 하나만 추가하고 나머지는 프론트엔드에서 처리.

**JPA 관계:**

| 관계 | 설명 | JPA 어노테이션 |
|------|------|---------------|
| Schedule → Member (createdBy) | N:1 (다대일). 여러 일정이 한 멤버에 의해 생성됨 | `@ManyToOne` + `@JoinColumn(name = "created_by")` |
| Schedule ↔ Member (taggedMembers) | N:M (다대다). 일정에 여러 멤버 태그 가능, 멤버도 여러 일정에 태그 가능 | `@ManyToMany` + `@JoinTable(name = "schedule_tag")` |

중간 테이블 `schedule_tag`가 자동 생성되며, `schedule_id`와 `member_id` 두 개의 FK를 가진다.

### 3.5 ActivityLog (활동 로그)

```java
@Entity
public class ActivityLog {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;                    // PK

    private String action;              // 수행된 동작 (예: "일정 등록: 회의")
    private String actor;               // 동작 수행자 loginId (예: "admin")
    private LocalDateTime createdAt;    // 발생 시각

    public ActivityLog(String action, String actor) {
        this.action = action;
        this.actor = actor;
        this.createdAt = LocalDateTime.now();
    }
}
```

**기록되는 동작 목록:**
- 회원가입 신청, 회원 탈퇴
- 회원 승인, 회원 거절, 멤버 추방
- 일정 등록, 일정 수정, 일정 삭제
- 일정 완료/미완료 처리, 일정 자동 완료

ActivityLog는 다른 엔티티와 FK 관계가 없다. `actor` 필드에 loginId를 문자열로 저장하므로, 회원이 탈퇴해도 로그는 보존된다.

---

## 4. 유스케이스별 구현 상세

### A. 계정 관리

#### A1. 회원가입
- **URL**: `GET /auth/signup` (폼 표시), `POST /auth/signup` (가입 처리)
- **Controller**: `AuthController.signupForm()`, `AuthController.signup()`
- **Service**: `MemberService.signup(loginId, password, name, email)`
  1. `MemberRepository.findByLoginId(loginId)`로 중복 ID 체크
  2. `Member` 객체 생성 — `Role.USER`, `ApprovalStatus.PENDING`이 기본값
  3. `createdAt`을 `LocalDateTime.now()`로 설정
  4. `MemberRepository.save(member)`로 DB 저장
  5. `ActivityLogRepository.save()`로 "회원가입 신청" 로그 기록
- **Repository**: `MemberRepository.findByLoginId()`, `MemberRepository.save()`
- **Template**: `auth/signup.html`
- **흐름**: 사용자가 가입 폼 작성 → `AuthController`가 중복 ID 체크 → 중복이면 에러 메시지와 함께 가입 폼으로 리다이렉트 → 중복 아니면 `MemberService.signup()` 호출 → DB 저장 → "관리자 승인 후 로그인 가능합니다" 메시지와 함께 로그인 페이지로 리다이렉트
- **특이사항**: 가입 직후 `ApprovalStatus.PENDING` 상태이므로 로그인 불가. 관리자가 승인해야 로그인 가능.

#### A2. 개인정보 수정

##### A2-1. 사용자명 변경
- **URL**: `POST /member/update-name`
- **Controller**: `MemberController.updateName(name, session, ra)`
- **Service**: `MemberService.updateName(memberId, newName)`
  1. `MemberRepository.findById(memberId)`로 회원 조회
  2. `member.setName(newName)`으로 이름 변경
  3. `MemberRepository.save(member)`로 저장
- **추가 처리**: 세션의 `loginMember` 객체도 `setName()`으로 갱신하여 화면에 즉시 반영
- **Template**: `member/profile.html` (인라인 폼)

##### A2-2. 비밀번호 변경
- **URL**: `POST /member/update-password`
- **Controller**: `MemberController.updatePassword(currentPassword, newPassword, session, ra)`
- **Service**: `MemberService.updatePassword(memberId, currentPassword, newPassword)`
  1. `MemberRepository.findById(memberId)`로 회원 조회
  2. 현재 비밀번호 일치 여부 확인: `member.getPassword().equals(currentPassword)`
  3. 일치하면 `setPassword(newPassword)` → `save()` → `true` 반환
  4. 불일치하면 `false` 반환 → Controller에서 "현재 비밀번호가 일치하지 않습니다" 에러 메시지
- **Template**: `member/profile.html` (2열 그리드 폼)

#### A3. 로그인

##### A3-1. 로그인
- **URL**: `GET /auth/login` (폼 표시), `POST /auth/login` (로그인 처리)
- **Controller**: `AuthController.login(loginId, password, session, ra)`
- **Service**: `MemberService.login(loginId, password)`
  1. `MemberRepository.findByLoginIdAndPassword(loginId, password)`로 조회
  2. `.filter(m -> m.getApprovalStatus() == ApprovalStatus.APPROVED)`로 승인된 회원인지 확인
  3. 조건 불충족 시 `null` 반환
- **로그인 성공 시**: `session.setAttribute("loginMember", member)` → `redirect:/` (대시보드)
- **로그인 실패 시**: "로그인 실패: ID/비밀번호를 확인하거나 승인 대기 중입니다." 에러 메시지 → 로그인 폼
- **Template**: `auth/login.html`

##### A3-2. ID 찾기
- **URL**: `GET /auth/find-id` (폼), `POST /auth/find-id` (조회)
- **Controller**: `AuthController.findId(name, email, model)`
- **Service**: `MemberService.findLoginIdByNameAndEmail(name, email)`
  1. `MemberRepository.findByNameAndEmail(name, email)`로 조회
  2. 존재하면 loginId 반환, 없으면 null
- **결과**: "회원님의 ID는 [ xxx ] 입니다." 또는 "일치하는 회원 정보가 없습니다."
- **Template**: `auth/find-id.html`

##### A3-3. 비밀번호 찾기
- **URL**: `GET /auth/find-password` (폼), `POST /auth/find-password` (조회)
- **Controller**: `AuthController.findPassword(loginId, email, model)`
- **Service**: `MemberService.findPasswordByLoginIdAndEmail(loginId, email)`
  1. `MemberRepository.findByLoginId(loginId)`로 조회
  2. 이메일 일치 확인: `email.equals(member.getEmail())`
  3. 일치하면 비밀번호 반환, 불일치하면 null
- **결과**: 비밀번호 힌트를 마스킹하여 표시 (첫 글자만 보여주고 나머지 `*` 처리)
  - 예: `password123` → `p**********`
- **Template**: `auth/find-password.html`

#### A4. 로그아웃
- **URL**: `GET /auth/logout`
- **Controller**: `AuthController.logout(session)`
- **처리**: `session.invalidate()` — 세션 전체 무효화
- **결과**: 로그인 페이지로 리다이렉트 (`redirect:/auth/login`)
- **특이사항**: GET 메서드 사용. 사이드바에서 "로그아웃" 링크 클릭 시 호출

#### A5. 회원 탈퇴
- **URL**: `POST /member/delete`
- **Controller**: `MemberController.deleteMember(session)`
- **Service**: `MemberService.deleteMember(memberId)`
  1. `cleanupMemberReferences(member)` 호출 — 해당 멤버 관련 일정 참조 정리:
     - 모든 Schedule을 순회하며 `taggedMembers`에서 해당 멤버 제거
     - `createdBy`가 해당 멤버인 일정의 `createdBy`를 `null`로 설정
  2. `ActivityLogRepository.save()` — "회원 탈퇴" 로그 기록
  3. `MemberRepository.delete(member)` — DB에서 멤버 삭제
- **후처리**: `session.invalidate()` → 로그인 페이지로 리다이렉트
- **Template**: `member/profile.html`의 "위험 영역" 섹션에 탈퇴 버튼

### B. 서비스

#### B1. 관리자 문의
- **구현 방식**: 기능 구현이 아닌, 푸터에 연락처(이메일 등)를 텍스트로 제공
- **위치**: `fragments.html`의 footer 영역

#### B2. 이용약관 열람
- **URL**: `GET /service/terms`
- **Controller**: `ServiceController.terms()`
- **처리**: 별도 비즈니스 로직 없음. 정적 페이지 렌더링
- **Template**: `service/terms.html`
- **인증 불필요**: WebConfig에서 `/service/**` 경로를 인터셉터에서 제외

#### B3. 개인정보처리방침 열람
- **URL**: `GET /service/privacy`
- **Controller**: `ServiceController.privacy()`
- **처리**: 별도 비즈니스 로직 없음. 정적 페이지 렌더링
- **Template**: `service/privacy.html`
- **인증 불필요**: WebConfig에서 `/service/**` 경로를 인터셉터에서 제외

### C. 일정

#### C1. 일정 등록
- **URL**: `GET /schedule/new` (폼 표시), `POST /schedule/new` (등록 처리)
- **Controller**: `ScheduleController.createForm(model)`, `ScheduleController.create(title, content, startAt, scheduledAt, taggedMemberIds, session, ra)`
- **Controller 처리 상세**:
  1. `startAt` 파라미터가 존재하고 비어있지 않으면 `LocalDateTime.parse(startAt)`으로 변환, 없으면 `null`
  2. `scheduledAt` 파라미터를 `LocalDateTime.parse(scheduledAt)`로 변환
  3. 세션에서 `loginMember`를 가져와 작성자로 설정
- **Service**: `ScheduleService.create(title, content, startAt, scheduledAt, taggedMemberIds, createdBy)`
  1. `Schedule` 객체 생성 및 필드 설정
  2. `taggedMemberIds`가 있으면 `MemberRepository.findAllById(taggedMemberIds)`로 멤버 목록 조회 → `setTaggedMembers()`
  3. `ScheduleRepository.save(schedule)`로 저장
  4. `ActivityLogRepository.save()` — "일정 등록: {title}" 로그 기록
- **Template**: `schedule/form.html` (등록/수정 공용 폼)
  - `th:action`이 `schedule` 변수 유무에 따라 `/schedule/new` 또는 `/schedule/{id}/edit`로 분기
  - 하루/기간 토글 UI 제공 (`date-type-tab` 버튼)

#### C2. 일정 조회

##### C2-1. 다가오는 일정 조회 (대시보드)
- **URL**: `GET /`
- **Controller**: `HomeController.home(model)`
- **Service**: `ScheduleService.getUpcoming()`
  1. `LocalDateTime.now()`부터 7일 후까지의 범위 계산
  2. `ScheduleRepository.findByCompletedFalseAndScheduledAtBetweenOrderByScheduledAtAsc(now, weekLater)`
  3. 완료되지 않은(`completed = false`) 일정 중 `scheduledAt`이 범위 내인 것만 조회
- **Template**: `index.html` — 카드 그리드로 표시

##### C2-2. 일정 필터 및 검색 (일정 목록)
- **URL**: `GET /schedule?keyword=검색어&completed=true|false`
- **Controller**: `ScheduleController.list(keyword, completed, model)`
- **Service**: `ScheduleService.search(keyword, completed)`
  - 내부적으로 `ScheduleRepository.search()` JPQL 쿼리 호출:
  ```sql
  SELECT s FROM Schedule s
  WHERE (:keyword IS NULL OR s.title LIKE %:keyword% OR s.content LIKE %:keyword%)
  AND (:completed IS NULL OR s.completed = :completed)
  ORDER BY s.scheduledAt DESC
  ```
  - `keyword`가 빈 문자열이면 `null`로 변환하여 전체 조회
- **Template**: `schedule/list.html` — 목록/캘린더/간트 3가지 뷰 지원

##### 캘린더 뷰 (프론트엔드)
- **구현**: `static/js/schedule-views.js`의 `renderCalendar()` 함수
- **로직**: Thymeleaf 인라인 스크립트로 서버 데이터를 JSON 배열로 변환 → JavaScript에서 월별 그리드 렌더링
- **기능**: 월 이동(이전/다음), 오늘 버튼, 일정 표시 (기간 일정은 여러 날에 걸쳐 표시), 클릭 시 수정 페이지 이동

##### 간트 차트 뷰 (프론트엔드)
- **구현**: `static/js/schedule-views.js`의 `renderGantt()` 함수
- **로직**: 모든 일정의 날짜 범위 계산 → 타임라인 헤더(월/일) 생성 → 각 일정을 수평 바로 렌더링
- **기능**: 기간 일정은 바 길이로, 단일일 일정은 짧은 바로 표시. 오늘 날짜에 빨간 세로선. 호버 시 툴팁.

#### C3. 일정 수정
- **URL**: `GET /schedule/{id}/edit` (폼 표시), `POST /schedule/{id}/edit` (수정 처리)
- **Controller**: `ScheduleController.editForm(id, model)`, `ScheduleController.update(id, title, content, startAt, scheduledAt, taggedMemberIds, session, ra)`
- **Service**: `ScheduleService.update(id, title, content, startAt, scheduledAt, taggedMemberIds, actorLoginId)`
  1. `ScheduleRepository.findById(id)`로 기존 일정 조회
  2. 모든 필드 덮어쓰기 (title, content, startAt, scheduledAt, taggedMembers)
  3. `ScheduleRepository.save(schedule)`로 저장
  4. "일정 수정: {title}" 로그 기록
- **폼 재사용**: `schedule/form.html`을 등록과 공유. `schedule` 변수가 있으면 수정 모드, 없으면 등록 모드. 기간 일정이면 자동으로 "기간" 탭 활성화 (`startInput.value`가 있으면 `setType('range')` 호출).

#### C4. 일정 삭제
- **URL**: `POST /schedule/{id}/delete`
- **Controller**: `ScheduleController.delete(id, session, ra)`
- **Service**: `ScheduleService.delete(id, actorLoginId)`
  1. `ScheduleRepository.findById(id)`로 일정 조회
  2. "일정 삭제: {title}" 로그 기록
  3. `ScheduleRepository.delete(schedule)`로 DB 삭제
- **UI**: 삭제 버튼에 `data-confirm="정말 삭제하시겠습니까?"` 속성 → `app.js`에서 confirm 대화상자 표시

#### C5. 일정 완료

##### C5-1. 자동 완료 (시스템)
- **위치**: `ScheduleService.autoCompleteExpiredSchedules()`
- **동작**: `@Scheduled(fixedRate = 60000)` — 60초마다 실행
  1. `ScheduleRepository.findByCompletedFalseAndScheduledAtBeforeAndScheduledAtIsNotNull(now)` — 완료되지 않고 scheduledAt이 현재 시각보다 이전인 일정 조회
  2. 각 일정의 `completed`를 `true`로 변경
  3. "일정 자동 완료: {title}" 로그 기록 (actor: "시스템")
- **활성화**: `TeamScheduleApplication`에 `@EnableScheduling` 어노테이션

##### C5-2. 수동 완료 상태 변경
- **URL**: `POST /schedule/{id}/toggle`
- **Controller**: `ScheduleController.toggleComplete(id, session)`
- **Service**: `ScheduleService.toggleComplete(id, actorLoginId)`
  1. 현재 완료 상태를 반전: `schedule.setCompleted(!schedule.isCompleted())`
  2. "일정 완료: {title}" 또는 "일정 미완료: {title}" 로그 기록
- **UI**: 목록에서 "완료 처리" 또는 "미완료로 변경" 버튼

### D. 알림

#### D1. 알림 켜기/끄기
- **URL**: `POST /member/update-notification`
- **Controller**: `MemberController.updateNotification(notificationEnabled, webhookUrl, session, ra)`
- **Service**: `MemberService.updateNotification(memberId, enabled, webhookUrl)`
  1. `MemberRepository.findById(memberId)`로 회원 조회
  2. `member.setNotificationEnabled(enabled)`, `member.setWebhookUrl(webhookUrl)` 설정
  3. `MemberRepository.save(member)` 저장
- **추가 처리**: 세션의 `loginMember` 객체도 갱신
- **Template**: `member/profile.html`의 알림 설정 섹션 — 토글 스위치 UI

#### D2. 외부 알림 연동 (웹훅 URL 등록)
- D1과 동일한 엔드포인트에서 처리. `webhookUrl` 필드에 URL을 입력하면 연동.
- **UI**: 프로필 페이지에서 웹훅 URL 입력 필드

#### D3. 외부 알림 연동 해제
- D1과 동일한 엔드포인트에서 처리. 토글을 OFF하고 `webhookUrl`을 비우면 해제.

### E. 어드민

#### E1. 멤버 관리

##### E1-1. 멤버 승인/거절
- **URL**: `GET /admin/members` (목록), `POST /admin/members/{id}/approve` (승인), `POST /admin/members/{id}/reject` (거절)
- **Controller**: `AdminController.members()`, `AdminController.approve(id, session, ra)`, `AdminController.reject(id, session, ra)`
- **권한 체크**: `loginMember.getRole() != Role.ADMIN`이면 대시보드로 리다이렉트
- **Service 승인**: `MemberService.approveMember(memberId, adminName)`
  1. 해당 멤버의 `approvalStatus`를 `ApprovalStatus.APPROVED`로 변경
  2. "회원 승인: {loginId}" 로그 기록 (actor: 관리자명)
- **Service 거절**: `MemberService.rejectMember(memberId, adminName)`
  1. 해당 멤버의 `approvalStatus`를 `ApprovalStatus.REJECTED`로 변경
  2. "회원 거절: {loginId}" 로그 기록
- **Template**: `admin/members.html` — 대기 멤버 목록 + 승인된 멤버 목록

##### E1-2. 멤버 추방
- **URL**: `POST /admin/members/{id}/kick`
- **Controller**: `AdminController.kick(id, session, ra)`
- **Service**: `MemberService.kickMember(memberId, adminName)`
  1. `cleanupMemberReferences(member)` — A5와 동일한 참조 정리 로직
  2. "멤버 추방: {loginId}" 로그 기록
  3. `MemberRepository.delete(member)` — DB에서 삭제
- **회원 탈퇴(A5)와의 차이**: A5는 본인이 직접, E1-2는 관리자가 강제. 둘 다 `cleanupMemberReferences()`를 호출하여 일정 참조를 정리.

#### E2. 로그 열람
- **URL**: `GET /admin/logs`
- **Controller**: `AdminController.logs(session, model)`
- **권한 체크**: `loginMember.getRole() != Role.ADMIN`이면 대시보드로 리다이렉트
- **Service**: `MemberService.getAllLogs()`
  - `ActivityLogRepository.findAllByOrderByCreatedAtDesc()` — 최신순 정렬
- **Template**: `admin/logs.html` — 테이블 형태로 action, actor, createdAt 표시

---

## 5. 인증/인가 처리

### 5.1 HttpSession 기반 인증

이 시스템은 Spring Security를 사용하지 않고, **HttpSession + HandlerInterceptor**로 인증을 구현한다.

**인증 흐름:**
1. 사용자가 `/auth/login`에서 loginId, password 입력
2. `AuthController.login()`에서 `MemberService.login()` 호출
3. DB에서 ID/PW가 일치하고 `ApprovalStatus.APPROVED`인 멤버 조회
4. 성공 시 `session.setAttribute("loginMember", member)` — 세션에 Member 객체 저장
5. 이후 모든 요청에서 `session.getAttribute("loginMember")`로 로그인 사용자 조회

### 5.2 LoginInterceptor

```java
public class LoginInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) throws Exception {
        HttpSession session = request.getSession(false);  // 세션이 없으면 null (새로 생성 안 함)
        if (session == null || session.getAttribute("loginMember") == null) {
            response.sendRedirect("/auth/login");  // 로그인 페이지로 강제 이동
            return false;  // 요청 처리 중단
        }
        return true;  // 인증된 사용자 — 요청 계속 처리
    }
}
```

**동작 원리:**
- `request.getSession(false)`: 기존 세션이 있으면 반환, 없으면 `null` (새 세션 생성 안 함)
- 세션이 없거나 `loginMember` 속성이 없으면 → 로그인 페이지로 리다이렉트
- `return false`: DispatcherServlet이 Controller를 호출하지 않음

### 5.3 WebConfig — 인터셉터 등록

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoginInterceptor())
                .addPathPatterns("/**")           // 모든 경로에 적용
                .excludePathPatterns(
                    "/auth/**",                    // 로그인/회원가입/ID찾기/PW찾기
                    "/service/**",                 // 이용약관/개인정보처리방침
                    "/css/**", "/js/**",           // 정적 자원
                    "/h2-console/**"               // H2 콘솔 (개발용)
                );
    }
}
```

**제외 경로 설명:**

| 경로 | 이유 |
|------|------|
| `/auth/**` | 로그인 전에 접근해야 하는 페이지 (로그인, 회원가입, ID/PW 찾기) |
| `/service/**` | 로그인 없이도 볼 수 있어야 하는 정보 (이용약관, 개인정보처리방침) |
| `/css/**`, `/js/**` | 정적 자원 (CSS, JavaScript 파일) — 인증 불필요 |
| `/h2-console/**` | 개발 시 DB 직접 조회용 — 운영에서는 비활성화 권장 |

### 5.4 왜 Spring Security 대신 이 방식인가?

| 항목 | Spring Security | 직접 구현 (현재) |
|------|----------------|----------------|
| 설정 복잡도 | SecurityFilterChain, UserDetailsService, PasswordEncoder 등 다수의 설정 필요 | Interceptor 1개 + Config 1개로 완결 |
| 학습 비용 | 프레임워크 내부 동작 이해 필요 | 순수 Servlet API 수준에서 이해 가능 |
| 코드 투명성 | 필터 체인 내부에서 처리되어 흐름 추적이 어려움 | `preHandle()` 한 메서드에서 모든 인증 로직 확인 가능 |
| UML 작성 | 프레임워크 내부를 표현하기 어려움 | 시퀀스 다이어그램에서 명확히 표현 가능 |

→ 프로젝트 목적(구조 질문 대응, UML 작성 용이)에 맞춰 의도적으로 단순한 방식을 선택.

---

## 6. 프론트엔드 구조

### 6.1 Thymeleaf 템플릿 구조

```
templates/
├── fragments.html          ← 공통 컴포넌트 (head, sidebar, header, footer)
├── index.html              ← 대시보드
├── auth/
│   ├── login.html          ← 로그인 폼
│   ├── signup.html         ← 회원가입 폼
│   ├── find-id.html        ← ID 찾기
│   └── find-password.html  ← 비밀번호 찾기
├── schedule/
│   ├── list.html           ← 일정 목록 (목록/캘린더/간트 뷰)
│   └── form.html           ← 일정 등록/수정 폼 (공용)
├── member/
│   └── profile.html        ← 프로필 (사용자명/비밀번호 변경, 알림 설정, 탈퇴)
├── admin/
│   ├── members.html        ← 멤버 관리 (승인/거절/추방)
│   └── logs.html           ← 활동 로그
└── service/
    ├── terms.html          ← 이용약관
    └── privacy.html        ← 개인정보처리방침
```

**fragments.html 활용:**
- `th:replace="~{fragments :: head('페이지 제목')}"` — `<head>` 태그 (CSS, 폰트 로드)
- `th:replace="~{fragments :: sidebar}"` — 왼쪽 사이드바 (네비게이션)
- `th:replace="~{fragments :: header('섹션 제목')}"` — 상단 헤더
- `th:replace="~{fragments :: footer}"` — 하단 푸터

### 6.2 CSS 디자인 시스템

- **테마**: Jamkubot 그레이스케일 (zinc 팔레트)
- **폰트**: Pretendard Variable (한국어 웹폰트)
- **CSS 변수**:
  ```css
  --db-bg: #f4f4f5;        /* 배경색 */
  --db-accent: #18181b;    /* 강조색 (거의 검정) */
  --db-surface: #ffffff;   /* 카드/패널 배경 */
  --sidebar-width: 240px;  /* 사이드바 너비 */
  ```
- **디자인 특징**: 필 버튼(pill shape), 12px 카드 라디우스, 240px 화이트 사이드바

### 6.3 JavaScript 모듈

#### app.js
- 삭제 확인 대화상자: `data-confirm` 속성이 있는 버튼 클릭 시 `window.confirm()` 호출
- 기타 공통 UI 로직

#### schedule-views.js
- **캘린더 뷰** (`renderCalendar()`):
  - 월별 7열 그리드 렌더링
  - 각 셀에 해당 날짜의 일정을 `.cal-event`로 표시
  - 기간 일정은 `startAt ~ scheduledAt` 범위의 모든 날짜 셀에 표시
  - 최대 3개까지 표시, 초과 시 "+N개" 표시
- **간트 차트 뷰** (`renderGantt()`):
  - 모든 일정의 날짜 범위 계산 → 타임라인 헤더(월/일) 생성
  - 각 일정을 수평 바로 렌더링 (`left`, `width` 계산)
  - 오늘 날짜에 빨간 세로선 표시
  - 완료된 일정은 `.done` 클래스 적용 (흐릿한 색상)
- **뷰 전환**: `.view-tab` 버튼 클릭 → `#view-list`, `#view-calendar`, `#view-gantt` 중 선택된 것만 `display: block`, 나머지 `display: none`

### 6.4 서버 → 프론트엔드 데이터 전달 (Thymeleaf 인라인 스크립트)

```html
<script th:inline="javascript">
    var data = /*[[${schedules}]]*/ [];   // Thymeleaf가 서버 데이터를 JSON으로 주입
    var mapped = [];
    for (var i = 0; i < data.length; i++) {
        mapped.push({
            id: data[i].id,
            title: data[i].title,
            startAt: data[i].startAt ? data[i].startAt.toString() : null,
            scheduledAt: data[i].scheduledAt ? data[i].scheduledAt.toString() : null,
            completed: data[i].completed,
            // ...
        });
    }
    ScheduleViews.init(mapped);
</script>
```

Thymeleaf의 `/*[[...]]*/` 구문으로 서버의 Java 객체 리스트를 JavaScript 배열로 직렬화하여 클라이언트에서 활용.

---

## 7. 주요 설계 결정 및 근거

### 7.1 H2 파일 DB 선택 이유
- **별도 DB 서버 불필요**: 설치/설정 없이 애플리케이션 실행만으로 DB 사용 가능
- **파일 모드 (`jdbc:h2:file:./data/teamschedule`)**: 서버 재시작해도 데이터 보존
- **H2 Console** (`/h2-console`): 웹 브라우저에서 직접 SQL 실행 가능하여 개발/디버깅 편리
- 학습 프로젝트에 적합: MySQL/PostgreSQL 같은 외부 DB 없이 프로젝트 배포 가능

### 7.2 HttpSession 기반 인증 (Spring Security 미사용)
- 위 5.4절 참조. 핵심: **구조 단순화**와 **UML 표현 용이성**

### 7.3 순수 JavaScript (프론트엔드 라이브러리 미사용)
- React, Vue, FullCalendar 등의 라이브러리 없이 순수 JS로 캘린더/간트 차트 구현
- **이유**: 외부 의존성 최소화, 코드 전체를 직접 작성하여 구조 완전 이해 가능
- **장점**: 빌드 도구(webpack 등) 불필요, HTML 파일에 `<script>` 태그만으로 동작

### 7.4 백엔드 최대한 단순하게 유지
- Service 2개 (MemberService, ScheduleService)로 모든 비즈니스 로직 처리
- DTO 클래스 미사용 — 엔티티를 직접 Controller에서 받고 전달
- 별도 예외 클래스 미정의 — `null` 반환으로 에러 상황 처리
- **이유**: 개발자가 모든 구조를 완벽히 파악할 수 있도록

### 7.5 일정의 단일일/기간 설계 (startAt nullable 패턴)
- `startAt` 필드 하나만 추가하여 기간 일정 지원
- `startAt == null`이면 단일일 일정, 값이 있으면 기간 일정
- 기존 단일일 일정 로직에 영향 없음 (하위 호환)
- 프론트엔드에서 "하루/기간" 토글 UI로 사용자 선택

---

## 8. 데이터베이스

### 8.1 설정 (application.properties)

```properties
spring.datasource.url=jdbc:h2:file:./data/teamschedule    # 파일 기반 H2 DB
spring.datasource.driver-class-name=org.h2.Driver
spring.datasource.username=sa
spring.datasource.password=                                 # 비밀번호 없음
spring.jpa.hibernate.ddl-auto=update                        # 엔티티 변경 시 스키마 자동 갱신
spring.h2.console.enabled=true                              # H2 웹 콘솔 활성화
spring.h2.console.path=/h2-console                          # 콘솔 접근 경로
```

**`ddl-auto=update` 의미:**
- 애플리케이션 시작 시 엔티티 클래스와 DB 스키마를 비교
- 새 필드가 추가되면 ALTER TABLE로 컬럼 추가
- 기존 데이터는 유지
- 운영 환경에서는 `validate`나 `none` 권장 (학습 프로젝트이므로 `update` 사용)

### 8.2 테이블 관계도

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   MEMBER     │       │   SCHEDULE   │       │ ACTIVITY_LOG │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │◄──┐   │ id (PK)      │       │ id (PK)      │
│ login_id     │   │   │ title        │       │ action       │
│ password     │   ├───│ created_by   │(FK)   │ actor        │
│ name         │   │   │ content      │       │ created_at   │
│ email        │   │   │ start_at     │       └──────────────┘
│ role         │   │   │ scheduled_at │
│ approval_    │   │   │ completed    │
│   status     │   │   │ created_at   │
│ notification_│   │   └──────┬───────┘
│   enabled    │   │          │
│ webhook_url  │   │          │ N:M
│ created_at   │   │   ┌──────┴───────┐
└──────────────┘   │   │ SCHEDULE_TAG │
                   │   ├──────────────┤
                   └───│ member_id    │(FK)
                       │ schedule_id  │(FK)
                       └──────────────┘
```

**테이블 설명:**
- `MEMBER`: 회원 테이블. PK는 `id` (auto increment)
- `SCHEDULE`: 일정 테이블. `created_by`는 `MEMBER.id`를 참조하는 FK
- `SCHEDULE_TAG`: N:M 관계를 위한 중간 테이블. JPA `@JoinTable`로 자동 생성
- `ACTIVITY_LOG`: 활동 로그 테이블. 다른 테이블과 FK 관계 없음 (독립)

### 8.3 초기 데이터 (DataInitializer)

애플리케이션 최초 실행 시 `CommandLineRunner`로 관리자 계정 자동 생성:
```
loginId: admin / password: admin / name: 관리자 / email: admin@team.com
role: ADMIN / approvalStatus: APPROVED
```

---

## 9. UML 다이어그램 목록

모든 다이어그램은 **StarUML**로 작성되었으며, `docs/diagrams/` 디렉토리에 위치한다.

| 파일명 | 다이어그램 종류 | 설명 |
|--------|---------------|------|
| `TeamSchedule.mdj` | StarUML 프로젝트 | 모든 다이어그램이 포함된 원본 파일 |
| `UseCase_Diagram.png` | 유스케이스 다이어그램 | 팀원/관리자(팀원 일반화)/타이머 액터, 18개 유스케이스, 시스템 경계 |
| `Class_Diagram_Entity.png` | 클래스 다이어그램 (엔티티) | Member, Schedule, ActivityLog 엔티티 + Role, ApprovalStatus 열거형, 연관 관계와 다중성 |
| `Class_Diagram_Application.png` | 클래스 다이어그램 (애플리케이션) | Controller(«boundary») 5개, Service(«service») 2개, Repository(«interface») 3개, 엔티티 3개의 계층 구조와 연관 관계 |
| `Sequence_Login_Success.png` | 시퀀스 다이어그램 (로그인 성공) | 팀원 → AuthController → MemberService → MemberRepository → HttpSession 주 시퀀스 |
| `Sequence_Login_Failure.png` | 시퀀스 다이어그램 (로그인 실패) | 계정이 없거나 승인되지 않은 경우의 대안 시퀀스 |
| `Sequence_CreateSchedule.png` | 시퀀스 다이어그램 (일정 등록) | 팀원 → ScheduleController → HttpSession/ScheduleService → MemberRepository/ScheduleRepository/ActivityLogRepository 흐름 |
| `Communication_CreateSchedule.png` | 커뮤니케이션 다이어그램 (일정 등록) | 일정 등록 시퀀스와 같은 시나리오를 객체 간 연결 중심으로 표현 |
| `StateMachine_Schedule.png` | 상태 머신 다이어그램 (일정) | 진행중 ↔ 완료 상태 전이. 완료 처리/취소, 자동 완료(scheduledAt 경과), 수정, 삭제 이벤트 포함 |
| `StateMachine_Member.png` | 상태 머신 다이어그램 (회원) | 승인 대기 → 승인됨/거절됨 상태 전이. 탈퇴/추방 시 종료 |
| `Activity_Login.png` | 액티비티 다이어그램 (로그인) | 로그인 유스케이스의 흐름. 계정 존재 여부와 승인 상태 분기, 실패 시 재시도 루프 |

---

## 10. 예상 질문 및 답변

### Q1. 유스케이스 다이어그램에서 로그인을 include 관계로 표현하지 않은 이유는?
**A**: 유스케이스 다이어그램은 흐름도가 아니므로 유스케이스 간 선후 관계를 표현하지 않습니다. `«include»`는 여러 유스케이스에 공통으로 들어가는 상호작용을 분리할 때 쓰는 관계이고, "로그인한 상태여야 한다"는 것은 실행 순서에 대한 조건이므로 각 유스케이스 명세의 사전 조건(Precondition)에 적었습니다. 코드에서는 `LoginInterceptor`의 `preHandle()`에서 세션의 `loginMember`를 확인하여 이를 구현했습니다. 관리자는 팀원의 기능을 모두 쓸 수 있으므로 액터 일반화로 표현했고, 1분마다 실행되는 자동 완료는 타이머 액터가 수행하는 유스케이스로 표현했습니다.

### Q2. 클래스 다이어그램에서 Member와 Schedule의 관계가 두 개인 이유는?
**A**: 첫 번째는 `createdBy` 관계로, 일정을 "누가 만들었는지"를 나타내는 N:1(다대일) 관계입니다 (`@ManyToOne`). 두 번째는 `taggedMembers` 관계로, 일정에 "누가 관련되어 있는지"를 나타내는 N:M(다대다) 관계입니다 (`@ManyToMany`). 하나의 일정은 한 명이 만들지만, 여러 멤버를 태그할 수 있고, 한 멤버도 여러 일정에 태그될 수 있습니다.

### Q3. 로그인의 성공/실패 분기는 시퀀스 다이어그램에서 어떻게 표현했는가?
**A**: 하나의 다이어그램에 분기를 넣지 않고 주 시퀀스(성공)와 대안 시퀀스(실패)를 각각의 시퀀스 다이어그램으로 나누어 그렸습니다. `MemberService.login()`이 회원을 반환하면(승인 상태 = APPROVED) 세션에 Member를 저장하고 홈 화면으로 리다이렉트하며, 계정이 없거나 승인되지 않아 반환값이 없으면 에러 메시지와 함께 로그인 페이지로 리다이렉트합니다. 분기 조건은 응답 메시지의 가드 `[조건]`으로 표기했습니다.

### Q4. 인증은 어떻게 구현했는가?
**A**: Spring Security 대신 HttpSession과 HandlerInterceptor를 직접 조합하여 구현했습니다. 로그인 성공 시 `session.setAttribute("loginMember", member)`로 세션에 사용자 정보를 저장합니다. 이후 모든 요청은 `LoginInterceptor.preHandle()`을 거치며, 세션에 `loginMember`가 없으면 로그인 페이지로 리다이렉트됩니다. `/auth/**`, `/service/**`, `/css/**`, `/js/**` 경로는 인터셉터에서 제외하여 인증 없이 접근 가능합니다.

### Q5. 왜 Spring Security를 사용하지 않았는가?
**A**: 프로젝트의 목표가 "백엔드 구조를 최대한 단순하게 유지하여 개발자가 모든 구조를 파악할 수 있도록" 하는 것이었기 때문입니다. Spring Security는 FilterChain, UserDetailsService, PasswordEncoder 등 여러 계층이 추가되어 구조가 복잡해집니다. 반면 Interceptor 방식은 `preHandle()` 메서드 하나에서 인증 로직이 모두 보이므로, 시퀀스 다이어그램에서도 명확히 표현할 수 있고, 질문에 대해 쉽게 답변할 수 있습니다.

### Q6. 일정의 시작일/종료일 처리 로직은?
**A**: `Schedule` 엔티티에 `startAt`(시작일)과 `scheduledAt`(종료일/단일일정일) 두 필드를 두었습니다. `startAt`이 `null`이면 단일일 일정, 값이 있으면 기간 일정입니다. 프론트엔드에서 "하루/기간" 토글 버튼으로 선택하며, "하루" 선택 시 `startAt` 입력 필드가 숨겨지고 값이 비워집니다. Controller에서 `startAt` 파라미터가 비어있으면 `null`로 변환하여 Service에 전달합니다. 캘린더/간트 차트에서는 `startAt`이 있으면 해당 기간에 걸쳐 표시합니다.

### Q7. 상태 머신 다이어그램의 각 상태 전이 조건은?
**A**: 일정(Schedule)의 상태는 `completed` 필드 값에 대응하는 **진행중**과 **완료** 두 가지입니다:
- **[초기] → 진행중**: 사용자가 일정을 등록하면 `completed = false` 상태로 생성
- **진행중 → 완료**: "완료 처리됨" 이벤트 (`toggleComplete()`), 또는 "마감 시각(scheduledAt) 경과" 이벤트로 시스템이 자동 완료 처리 (`@Scheduled(fixedRate = 60000)`)
- **완료 → 진행중**: "완료 취소됨" 이벤트 (토글 방식)
- **진행중 → 진행중, 완료 → 완료**: "일정 수정됨" 이벤트. 수정은 상태를 바꾸지 않음
- **진행중/완료 → [종료]**: "일정 삭제됨" 이벤트

전이 라벨은 `이벤트 / 액션` 형식이며, 액션은 활동 로그 기록입니다. 회원(Member)은 별도 상태 머신으로 그렸습니다: 가입 시 **승인 대기**, 관리자 승인 시 **승인됨**, 거절 시 **거절됨**이 되고, 승인된 회원이 탈퇴하거나 추방되면 종료됩니다.

### Q8. MVC 패턴이 코드에 어떻게 적용되어 있는가?
**A**: 
- **Model**: `entity` 패키지의 `Member`, `Schedule`, `ActivityLog` 클래스가 도메인 모델 역할. JPA `@Entity`로 DB 테이블과 매핑.
- **View**: `templates/` 디렉토리의 Thymeleaf HTML 파일들. `th:text`, `th:each` 등으로 Model 데이터를 화면에 렌더링.
- **Controller**: `controller` 패키지의 `@Controller` 클래스들. HTTP 요청을 받아 Service를 호출하고, 결과를 Model에 담아 View에 전달.
- Controller는 Service만 의존하고, Repository를 직접 호출하지 않아 계층 간 역할이 명확히 분리됩니다.

### Q9. @ManyToMany 관계에서 중간 테이블은 어떻게 생성되는가?
**A**: `Schedule` 엔티티의 `taggedMembers` 필드에 `@ManyToMany`와 `@JoinTable(name = "schedule_tag")`을 선언했습니다. JPA/Hibernate가 `ddl-auto=update` 설정에 따라 애플리케이션 시작 시 `schedule_tag` 테이블을 자동 생성합니다. 이 테이블은 `schedule_id`와 `member_id` 두 개의 외래키를 가지며, 별도의 엔티티 클래스를 작성할 필요 없이 JPA가 관리합니다.

### Q10. 활동 로그(ActivityLog)는 왜 다른 엔티티와 FK 관계가 없는가?
**A**: `actor` 필드를 `String`(loginId)으로 저장하여 의도적으로 FK 관계를 맺지 않았습니다. 이렇게 하면 회원이 탈퇴하거나 추방되어도 로그 기록이 삭제되지 않고 보존됩니다. 또한 시스템 자동 완료 같이 특정 사용자가 아닌 "시스템"이 actor인 경우에도 별도 처리 없이 문자열로 저장할 수 있습니다.

### Q11. 자동 완료 기능의 구현 방식은?
**A**: `ScheduleService`에 `@Scheduled(fixedRate = 60000)` 어노테이션이 붙은 `autoCompleteExpiredSchedules()` 메서드가 있습니다. 이 메서드는 60초(1분)마다 실행되며, `completed = false`이고 `scheduledAt`이 현재 시각보다 이전인 일정을 조회하여 자동으로 `completed = true`로 변경합니다. 이때 actor는 "시스템"으로 기록됩니다. `@EnableScheduling`이 메인 클래스(`TeamScheduleApplication`)에 선언되어 있어야 동작합니다.

### Q12. 프로젝트에서 사용한 디자인 패턴은?
**A**: 
- **MVC 패턴**: Controller-Service-Repository 계층 분리
- **Repository 패턴**: `JpaRepository`를 상속하는 인터페이스로 데이터 접근 추상화. Spring Data JPA가 구현체를 자동 생성
- **Template Method 패턴**: `HandlerInterceptor`의 `preHandle()`을 오버라이드하여 인증 로직 삽입
- **DI (의존성 주입)**: `@RequiredArgsConstructor`(Lombok) + `final` 필드로 생성자 주입. Controller가 Service를, Service가 Repository를 주입받음

### Q13. 관리자 권한 체크는 어떻게 하는가?
**A**: `AdminController`의 각 메서드 첫 줄에서 `loginMember.getRole() != Role.ADMIN`을 체크합니다. ADMIN이 아니면 `redirect:/` (대시보드)로 보냅니다. 이 체크는 인터셉터가 아닌 Controller 레벨에서 수행합니다. 인터셉터는 "로그인 여부"만 확인하고, "어떤 역할인지"는 각 Controller에서 판단합니다.

### Q14. 회원 탈퇴/추방 시 관련 데이터는 어떻게 처리되는가?
**A**: `MemberService.cleanupMemberReferences()` 메서드에서 처리합니다. 모든 Schedule을 순회하면서 (1) `taggedMembers` 목록에서 해당 멤버를 제거하고, (2) `createdBy`가 해당 멤버인 일정의 `createdBy`를 `null`로 설정합니다. 이후 `MemberRepository.delete()`로 멤버를 삭제합니다. 활동 로그(ActivityLog)는 FK 관계가 없으므로 영향 없이 보존됩니다.

### Q15. 프론트엔드에서 서버 데이터를 어떻게 받아 캘린더/간트를 그리는가?
**A**: Thymeleaf의 인라인 스크립트 기능을 사용합니다. `/*[[${schedules}]]*/` 구문으로 서버의 Schedule 리스트를 JSON으로 직렬화하여 JavaScript 변수에 주입합니다. 이 데이터를 `ScheduleViews.init(mapped)`에 전달하면, 순수 JavaScript로 DOM을 조작하여 캘린더 그리드나 간트 바를 렌더링합니다. 별도의 REST API나 AJAX 호출 없이 페이지 로드 시 한 번에 처리됩니다.
