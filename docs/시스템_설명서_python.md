# TeamSchedule 시스템 설명서 (Python/FastAPI)

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
| 언어 | Python | 3.10+ |
| 프레임워크 | FastAPI | 0.104+ |
| ORM | SQLAlchemy | 2.0 (Declarative Mapping) |
| 템플릿 엔진 | Jinja2 | - |
| 데이터베이스 | SQLite (파일 모드) | - |
| ASGI 서버 | uvicorn | - |
| 세션 관리 | Starlette SessionMiddleware (itsdangerous) | - |

### 1.3 의존성 (requirements.txt)
```
fastapi
uvicorn[standard]
sqlalchemy
jinja2
itsdangerous
python-multipart
```

- `fastapi`: 웹 프레임워크 (라우팅, 의존성 주입, 폼 처리)
- `uvicorn[standard]`: ASGI 서버 (FastAPI 애플리케이션 실행)
- `sqlalchemy`: ORM (엔티티-테이블 매핑, 쿼리 빌더)
- `jinja2`: 템플릿 엔진 (HTML 렌더링)
- `itsdangerous`: 세션 쿠키 서명 (SessionMiddleware 내부 사용)
- `python-multipart`: HTML 폼 데이터 파싱 (`Form(...)` 사용에 필요)

### 1.4 설계 원칙
- **백엔드 구조 최대한 단순화**: 개발자가 모든 구조를 꿰고 있을 수 있도록, UML 작성 용이하게, 구조 관련 질문에 쉽게 답변 가능하도록 설계
- **순수 미들웨어 인증**: 별도 인증 라이브러리 없이 Starlette `BaseHTTPMiddleware`로 로그인 체크 구현
- **프론트엔드 라이브러리 미사용**: 순수 JavaScript로 캘린더, 간트 차트 구현
- **완전한 OOP**: Entity → Repository → Service → Controller 계층 구조를 클래스로 구현

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
│  - Jinja2 HTML 템플릿                        │
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
│  Database (SQLite File)                     │
│  - ./data/teamschedule.db                   │
└─────────────────────────────────────────────┘
```

**MVC 패턴 적용:**
- **Model**: `entity` 패키지의 SQLAlchemy 모델 클래스들 (Member, Schedule, ActivityLog)
- **View**: Jinja2 템플릿 (.html 파일들)
- **Controller**: `controller` 패키지의 클래스들 (각각 `APIRouter`를 가짐)

### 2.2 패키지 구조

```
ver_python/
├── main.py                               ← 애플리케이션 진입점 (FastAPI 앱 생성, 초기화, 라우터 등록)
├── requirements.txt                      ← 의존성 목록
├── entity/                               ← SQLAlchemy 엔티티 (도메인 모델)
│   ├── __init__.py                       ← 엔티티 모듈 내보내기
│   ├── member.py                         ← 회원 엔티티
│   ├── schedule.py                       ← 일정 엔티티 + schedule_tag 중간 테이블
│   ├── activity_log.py                   ← 활동 로그 엔티티
│   ├── role.py                           ← 역할 열거형 (USER, ADMIN)
│   └── approval_status.py               ← 승인 상태 열거형 (PENDING, APPROVED, REJECTED)
├── repository/                           ← 데이터 접근 계층 (직접 구현한 클래스)
│   ├── member_repository.py
│   ├── schedule_repository.py
│   └── activity_log_repository.py
├── service/                              ← 비즈니스 로직 계층
│   ├── member_service.py                 ← 회원 관련 비즈니스 로직
│   └── schedule_service.py               ← 일정 관련 비즈니스 로직
├── controller/                           ← HTTP 요청 처리
│   ├── auth_controller.py                ← 인증 (로그인, 회원가입, 로그아웃, ID/PW 찾기)
│   ├── home_controller.py                ← 대시보드 (/)
│   ├── schedule_controller.py            ← 일정 CRUD
│   ├── member_controller.py              ← 프로필 관리 (개인정보 수정, 알림, 탈퇴)
│   ├── admin_controller.py               ← 관리자 기능 (멤버 관리, 로그)
│   └── service_controller.py             ← 이용약관, 개인정보처리방침
├── config/                               ← 설정
│   ├── database.py                       ← SQLAlchemy 엔진, 세션, Base 클래스
│   └── auth.py                           ← 로그인 미들웨어 (인증 체크)
├── templates/                            ← Jinja2 HTML 템플릿
│   ├── base.html                         ← 공통 레이아웃 (사이드바, 헤더, 푸터)
│   ├── index.html                        ← 대시보드
│   ├── auth/                             ← 인증 관련 (login, signup, find-id, find-password)
│   ├── schedule/                         ← 일정 관련 (list, form)
│   ├── member/                           ← 회원 관련 (profile)
│   ├── admin/                            ← 관리자 관련 (members, logs)
│   └── service/                          ← 서비스 정보 (terms, privacy)
└── static/                               ← 정적 파일
    ├── css/style.css                     ← 전체 스타일시트
    └── js/
        ├── app.js                        ← 공통 JavaScript (삭제 확인 등)
        └── schedule-views.js             ← 캘린더/간트 차트 뷰
```

### 2.3 계층 간 의존 관계

```
Controller → Service → Repository → Database
                ↓
           ActivityLog (모든 주요 동작을 로그로 기록)
```

- **Controller**는 Service만 의존한다. Repository를 직접 호출하지 않는다.
- **Service**는 Repository를 의존하여 DB 접근을 수행한다.
- **Repository**는 SQLAlchemy `Session`을 사용하여 쿼리를 실행한다.

### 2.4 의존성 주입 (DI) 구조

Python에는 프레임워크 레벨의 자동 DI가 없으므로, **싱글톤 패턴**으로 직접 구현한다.

```python
# main.py — 앱 시작 시 한 번만 생성
_member_repo = MemberRepository()
_schedule_repo = ScheduleRepository()
_log_repo = ActivityLogRepository()
_schedule_svc = ScheduleService(_schedule_repo, _member_repo, _log_repo)

# Controller는 __init__에서 서비스를 직접 생성
class AuthController:
    def __init__(self, templates):
        self._member_svc = MemberService(MemberRepository(), ActivityLogRepository(), ScheduleRepository())
        self.router = APIRouter(prefix="/auth")
```

**DB 세션은 FastAPI의 `Depends(get_db)`로 요청마다 주입:**
```python
async def _login(self, request: Request, db: Session = Depends(get_db), ...):
    member = self._member_svc.login(db, loginId, password)
```

Repository와 Service는 상태를 갖지 않는(stateless) 싱글톤 객체이고, DB 세션(`db`)은 모든 메서드의 첫 번째 인자로 전달된다.

---

## 3. 엔티티 설계

### 3.1 Member (회원)

```python
class Member(Base):
    __tablename__ = "member"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login_id: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))

    role: Mapped[str] = mapped_column(String(20), default=Role.USER.value)
    approval_status: Mapped[str] = mapped_column(String(20), default=ApprovalStatus.PENDING.value)

    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

**필드별 설명:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | int | 기본키. `autoincrement=True`로 DB가 자동 증가값을 생성 |
| `login_id` | str | 로그인에 사용하는 고유 ID. `unique=True`로 중복 방지 |
| `password` | str | 비밀번호. 학습 프로젝트이므로 평문 저장 (실서비스에서는 bcrypt 등 해싱 필요) |
| `name` | str | 화면에 표시되는 사용자명. 프로필 페이지에서 변경 가능 |
| `email` | str | 이메일. ID 찾기/비밀번호 찾기에 사용 |
| `role` | str | `"USER"` 또는 `"ADMIN"`. 관리자 페이지 접근 권한 결정 |
| `approval_status` | str | `"PENDING"`(가입 대기), `"APPROVED"`(승인), `"REJECTED"`(거절). 승인된 회원만 로그인 가능 |
| `notification_enabled` | bool | 알림 기능 ON/OFF |
| `webhook_url` | str (nullable) | Discord/Slack 등 외부 서비스 웹훅 URL |
| `created_at` | datetime (nullable) | 회원가입 시점. `MemberService.signup()`에서 `datetime.now()`로 설정 |

**`to_session_dict()` 메서드:**
세션에 저장할 회원 정보를 딕셔너리로 변환한다. 비밀번호는 보안상 세션에 저장하지 않는다.

### 3.2 Role (역할 열거형)

```python
class Role(str, Enum):
    USER = "USER"     # 일반 사용자
    ADMIN = "ADMIN"   # 관리자 — 멤버 승인/거절/추방, 로그 열람 가능
```

### 3.3 ApprovalStatus (승인 상태 열거형)

```python
class ApprovalStatus(str, Enum):
    PENDING = "PENDING"     # 가입 대기 — 회원가입 직후 기본 상태
    APPROVED = "APPROVED"   # 승인됨 — 로그인 가능
    REJECTED = "REJECTED"   # 거절됨 — 로그인 불가
```

**승인 흐름:** 회원가입 → `PENDING` → 관리자가 승인 → `APPROVED` (또는 거절 → `REJECTED`)

### 3.4 Schedule (일정)

```python
# N:M 중간 테이블 정의
schedule_tag = Table(
    "schedule_tag", Base.metadata,
    Column("schedule_id", Integer, ForeignKey("schedule.id"), primary_key=True),
    Column("member_id", Integer, ForeignKey("member.id"), primary_key=True),
)

class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("member.id"), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # N:1 관계 — 일정을 생성한 멤버
    created_by = relationship("Member", foreign_keys=[created_by_id], lazy="joined")

    # N:M 관계 — 일정에 태그된 멤버 목록
    tagged_members: Mapped[List["Member"]] = relationship(
        "Member", secondary=schedule_tag, lazy="joined"
    )
```

**일정 유형 설계 — start_at nullable 패턴:**

| 유형 | start_at | scheduled_at | 의미 |
|------|----------|--------------|------|
| 단일일 일정 | `None` | `2024-12-25 09:00` | 12/25 하루짜리 일정 |
| 기간 일정 | `2024-12-20 09:00` | `2024-12-25 18:00` | 12/20 ~ 12/25 기간 일정 |

**SQLAlchemy 관계:**

| 관계 | 설명 | SQLAlchemy 선언 |
|------|------|----------------|
| Schedule → Member (created_by) | N:1 (다대일). 여러 일정이 한 멤버에 의해 생성됨 | `relationship("Member", foreign_keys=[created_by_id])` |
| Schedule ↔ Member (tagged_members) | N:M (다대다). 일정에 여러 멤버 태그 가능, 멤버도 여러 일정에 태그 가능 | `relationship("Member", secondary=schedule_tag)` |

중간 테이블 `schedule_tag`는 `Table()` 함수로 직접 정의하며, `schedule_id`와 `member_id` 두 개의 FK를 가진다.

### 3.5 ActivityLog (활동 로그)

```python
class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(500))
    actor: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __init__(self, action: str, actor: str):
        self.action = action
        self.actor = actor
        self.created_at = datetime.now()
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
- **Controller**: `AuthController._signup_page()`, `AuthController._signup()`
- **Service**: `MemberService.signup(db, login_id, password, name, email)`
  1. `MemberRepository.find_by_login_id(db, login_id)`로 중복 ID 체크 (Controller에서 선행)
  2. `Member` 객체 생성 — `Role.USER.value`, `ApprovalStatus.PENDING.value`가 기본값
  3. `created_at`을 `datetime.now()`로 설정
  4. `MemberRepository.save(db, member)`로 DB 저장
  5. `ActivityLogRepository.save()`로 "회원가입 신청" 로그 기록
- **Repository**: `MemberRepository.find_by_login_id()`, `MemberRepository.save()`
- **Template**: `auth/signup.html`
- **흐름**: 사용자가 가입 폼 작성 → `AuthController`가 중복 ID 체크 → 중복이면 에러 메시지와 함께 가입 폼으로 리다이렉트 → 중복 아니면 `MemberService.signup()` 호출 → DB 저장 → "관리자 승인 후 로그인 가능합니다" 메시지와 함께 로그인 페이지로 리다이렉트
- **특이사항**: 가입 직후 `ApprovalStatus.PENDING` 상태이므로 로그인 불가. 관리자가 승인해야 로그인 가능.

#### A2. 개인정보 수정

##### A2-1. 사용자명 변경
- **URL**: `POST /member/update-name`
- **Controller**: `MemberController._update_name(request, db, name)`
- **Service**: `MemberService.update_name(db, member_id, new_name)`
  1. `MemberRepository.find_by_id(db, member_id)`로 회원 조회
  2. `member.name = new_name`으로 이름 변경
  3. `MemberRepository.save(db, member)`로 저장
- **추가 처리**: 세션의 `login_member` 딕셔너리도 `login["name"] = name`으로 갱신하여 화면에 즉시 반영
- **Template**: `member/profile.html` (인라인 폼)

##### A2-2. 비밀번호 변경
- **URL**: `POST /member/update-password`
- **Controller**: `MemberController._update_password(request, db, currentPassword, newPassword)`
- **Service**: `MemberService.update_password(db, member_id, current_pw, new_pw)`
  1. `MemberRepository.find_by_id(db, member_id)`로 회원 조회
  2. 현재 비밀번호 일치 여부 확인: `member.password == current_pw`
  3. 일치하면 `member.password = new_pw` → `save()` → `True` 반환
  4. 불일치하면 `False` 반환 → Controller에서 "현재 비밀번호가 일치하지 않습니다" 에러 메시지
- **Template**: `member/profile.html` (2열 그리드 폼)

#### A3. 로그인

##### A3-1. 로그인
- **URL**: `GET /auth/login` (폼 표시), `POST /auth/login` (로그인 처리)
- **Controller**: `AuthController._login(request, db, loginId, password)`
- **Service**: `MemberService.login(db, login_id, password)`
  1. `MemberRepository.find_by_login_id_and_password(db, login_id, password)`로 조회
  2. `member.approval_status == ApprovalStatus.APPROVED.value`로 승인된 회원인지 확인
  3. 조건 불충족 시 `None` 반환
- **로그인 성공 시**: `request.session["login_member"] = member.to_session_dict()` → `RedirectResponse(url="/")` (대시보드)
- **로그인 실패 시**: "로그인 실패: ID/비밀번호를 확인하거나 승인 대기 중입니다." 에러 메시지 → 로그인 폼
- **Template**: `auth/login.html`

##### A3-2. ID 찾기
- **URL**: `GET /auth/find-id` (폼), `POST /auth/find-id` (조회)
- **Controller**: `AuthController._find_id(request, db, name, email)`
- **Service**: `MemberService.find_login_id_by_name_and_email(db, name, email)`
  1. `MemberRepository.find_by_name_and_email(db, name, email)`로 조회
  2. 존재하면 `member.login_id` 반환, 없으면 `None`
- **결과**: "회원님의 ID는 [ xxx ] 입니다." 또는 "일치하는 회원 정보가 없습니다."
- **Template**: `auth/find-id.html`

##### A3-3. 비밀번호 찾기
- **URL**: `GET /auth/find-password` (폼), `POST /auth/find-password` (조회)
- **Controller**: `AuthController._find_password(request, db, loginId, email)`
- **Service**: `MemberService.find_password_by_login_id_and_email(db, login_id, email)`
  1. `MemberRepository.find_by_login_id(db, login_id)`로 조회
  2. 이메일 일치 확인: `member.email == email`
  3. 일치하면 비밀번호 반환, 불일치하면 `None`
- **결과**: 비밀번호 힌트를 마스킹하여 표시 (첫 글자만 보여주고 나머지 `*` 처리)
  - 예: `password123` → `p**********`
- **Template**: `auth/find-password.html`

#### A4. 로그아웃
- **URL**: `GET /auth/logout`
- **Controller**: `AuthController._logout(request)`
- **처리**: `request.session.clear()` — 세션 전체 초기화
- **결과**: 로그인 페이지로 리다이렉트 (`RedirectResponse(url="/auth/login")`)
- **특이사항**: GET 메서드 사용. 사이드바에서 "로그아웃" 링크 클릭 시 호출

#### A5. 회원 탈퇴
- **URL**: `POST /member/delete`
- **Controller**: `MemberController._delete_member(request, db)`
- **Service**: `MemberService.delete_member(db, member_id)`
  1. `_cleanup_member_references(db, member)` 호출 — 해당 멤버 관련 일정 참조 정리:
     - 모든 Schedule을 순회하며 `tagged_members`에서 해당 멤버 제거
     - `created_by`가 해당 멤버인 일정의 `created_by`와 `created_by_id`를 `None`으로 설정
  2. `ActivityLogRepository.save()` — "회원 탈퇴" 로그 기록
  3. `MemberRepository.delete(db, member)` — DB에서 멤버 삭제
- **후처리**: `request.session.clear()` → 로그인 페이지로 리다이렉트
- **Template**: `member/profile.html`의 "위험 영역" 섹션에 탈퇴 버튼

### B. 서비스

#### B1. 관리자 문의
- **구현 방식**: 기능 구현이 아닌, 푸터에 연락처(이메일 등)를 텍스트로 제공
- **위치**: `base.html`의 footer 영역

#### B2. 이용약관 열람
- **URL**: `GET /service/terms`
- **Controller**: `ServiceController._terms(request)`
- **처리**: 별도 비즈니스 로직 없음. 정적 페이지 렌더링
- **Template**: `service/terms.html`
- **인증 불필요**: `LoginMiddleware`에서 `/service` 경로를 `EXCLUDE_PREFIXES`에 포함

#### B3. 개인정보처리방침 열람
- **URL**: `GET /service/privacy`
- **Controller**: `ServiceController._privacy(request)`
- **처리**: 별도 비즈니스 로직 없음. 정적 페이지 렌더링
- **Template**: `service/privacy.html`
- **인증 불필요**: `LoginMiddleware`에서 `/service` 경로를 `EXCLUDE_PREFIXES`에 포함

### C. 일정

#### C1. 일정 등록
- **URL**: `GET /schedule/new` (폼 표시), `POST /schedule/new` (등록 처리)
- **Controller**: `ScheduleController._create_form(request, db)`, `ScheduleController._create(request, db, title, content, startAt, scheduledAt, taggedMemberIds)`
- **Controller 처리 상세**:
  1. `startAt` 파라미터가 존재하고 비어있지 않으면 `datetime.fromisoformat(startAt)`으로 변환, 없으면 `None`
  2. `scheduledAt` 파라미터를 `datetime.fromisoformat(scheduledAt)`으로 변환
  3. 세션에서 `login_member`를 가져와 `MemberService.find_by_id()`로 작성자 Member 객체 조회
- **Service**: `ScheduleService.create(db, title, content, start_at, scheduled_at, tagged_member_ids, created_by)`
  1. `Schedule` 객체 생성 및 필드 설정
  2. `tagged_member_ids`가 있으면 `MemberRepository.find_all_by_ids(db, tagged_member_ids)`로 멤버 목록 조회 → `schedule.tagged_members`에 설정
  3. `ScheduleRepository.save(db, schedule)`로 저장
  4. `ActivityLogRepository.save()` — "일정 등록: {title}" 로그 기록
- **Template**: `schedule/form.html` (등록/수정 공용 폼)
  - `schedule` 변수 유무에 따라 `/schedule/new` 또는 `/schedule/{id}/edit`로 분기
  - 하루/기간 토글 UI 제공 (`date-type-tab` 버튼)

#### C2. 일정 조회

##### C2-1. 다가오는 일정 조회 (대시보드)
- **URL**: `GET /`
- **Controller**: `HomeController._home(request, db)`
- **Service**: `ScheduleService.get_upcoming(db)`
  1. `datetime.now()`부터 7일 후까지의 범위 계산 (`timedelta(days=7)`)
  2. `ScheduleRepository.find_upcoming(db, now, week_later)` — `completed == False`이고 `scheduled_at`이 범위 내인 일정 조회
- **Template**: `index.html` — 카드 그리드로 표시

##### C2-2. 일정 필터 및 검색 (일정 목록)
- **URL**: `GET /schedule?keyword=검색어&completed=true|false`
- **Controller**: `ScheduleController._list(request, db, keyword, completed)`
- **Service**: `ScheduleService.search(db, keyword, completed)`
  - 내부적으로 `ScheduleRepository.search()` 호출:
  ```python
  query = db.query(Schedule)
  if keyword:
      like = f"%{keyword}%"
      query = query.filter((Schedule.title.like(like)) | (Schedule.content.like(like)))
  if completed is not None:
      query = query.filter(Schedule.completed == completed)
  return query.order_by(Schedule.scheduled_at.desc()).all()
  ```
  - `keyword`가 빈 문자열이면 `None`으로 변환하여 전체 조회
- **JSON 데이터 전달**: Controller에서 일정 리스트를 `json.dumps()`로 JSON 문자열로 변환하여 템플릿에 전달 (캘린더/간트 뷰용)
- **Template**: `schedule/list.html` — 목록/캘린더/간트 3가지 뷰 지원

##### 캘린더 뷰 (프론트엔드)
- **구현**: `static/js/schedule-views.js`의 `renderCalendar()` 함수
- **로직**: Controller에서 JSON으로 전달된 데이터 → JavaScript에서 월별 그리드 렌더링
- **기능**: 월 이동(이전/다음), 오늘 버튼, 일정 표시 (기간 일정은 여러 날에 걸쳐 표시), 클릭 시 수정 페이지 이동

##### 간트 차트 뷰 (프론트엔드)
- **구현**: `static/js/schedule-views.js`의 `renderGantt()` 함수
- **로직**: 모든 일정의 날짜 범위 계산 → 타임라인 헤더(월/일) 생성 → 각 일정을 수평 바로 렌더링
- **기능**: 기간 일정은 바 길이로, 단일일 일정은 짧은 바로 표시. 오늘 날짜에 빨간 세로선. 호버 시 툴팁.

#### C3. 일정 수정
- **URL**: `GET /schedule/{id}/edit` (폼 표시), `POST /schedule/{id}/edit` (수정 처리)
- **Controller**: `ScheduleController._edit_form(schedule_id, request, db)`, `ScheduleController._update(schedule_id, request, db, ...)`
- **Service**: `ScheduleService.update(db, schedule_id, title, content, start_at, scheduled_at, tagged_member_ids, actor_login_id)`
  1. `ScheduleRepository.find_by_id(db, schedule_id)`로 기존 일정 조회
  2. 모든 필드 덮어쓰기 (title, content, start_at, scheduled_at, tagged_members)
  3. `ScheduleRepository.save(db, schedule)`로 저장
  4. "일정 수정: {title}" 로그 기록
- **폼 재사용**: `schedule/form.html`을 등록과 공유. `schedule` 변수가 있으면 수정 모드, 없으면 등록 모드.

#### C4. 일정 삭제
- **URL**: `POST /schedule/{id}/delete`
- **Controller**: `ScheduleController._delete(schedule_id, request, db)`
- **Service**: `ScheduleService.delete(db, schedule_id, actor_login_id)`
  1. `ScheduleRepository.find_by_id(db, schedule_id)`로 일정 조회
  2. "일정 삭제: {title}" 로그 기록
  3. `ScheduleRepository.delete(db, schedule)`로 DB 삭제
- **UI**: 삭제 버튼에 `data-confirm="정말 삭제하시겠습니까?"` 속성 → `app.js`에서 confirm 대화상자 표시

#### C5. 일정 완료

##### C5-1. 자동 완료 (시스템)
- **위치**: `ScheduleService.auto_complete_expired(db)`
- **동작**: `main.py`에서 백그라운드 데몬 스레드로 60초마다 실행
  ```python
  def _auto_complete_loop():
      while True:
          time.sleep(60)
          db = SessionLocal()
          try:
              _schedule_svc.auto_complete_expired(db)
              db.commit()
          finally:
              db.close()

  # lifespan 이벤트에서 데몬 스레드 시작
  t = threading.Thread(target=_auto_complete_loop, daemon=True)
  t.start()
  ```
  1. `ScheduleRepository.find_expired(db, now)` — `completed == False`이고 `scheduled_at < now`인 일정 조회
  2. 각 일정의 `completed`를 `True`로 변경
  3. "일정 자동 완료: {title}" 로그 기록 (actor: "시스템")
- **활성화**: `main.py`의 `lifespan()` 함수에서 `threading.Thread(daemon=True)`로 시작

##### C5-2. 수동 완료 상태 변경
- **URL**: `POST /schedule/{id}/toggle`
- **Controller**: `ScheduleController._toggle(schedule_id, request, db)`
- **Service**: `ScheduleService.toggle_complete(db, schedule_id, actor_login_id)`
  1. 현재 완료 상태를 반전: `schedule.completed = not schedule.completed`
  2. "일정 완료: {title}" 또는 "일정 미완료: {title}" 로그 기록
- **UI**: 목록에서 "완료 처리" 또는 "미완료로 변경" 버튼

### D. 알림

#### D1. 알림 켜기/끄기
- **URL**: `POST /member/update-notification`
- **Controller**: `MemberController._update_notification(request, db, notificationEnabled, webhookUrl)`
- **Service**: `MemberService.update_notification(db, member_id, enabled, webhook_url)`
  1. `MemberRepository.find_by_id(db, member_id)`로 회원 조회
  2. `member.notification_enabled = enabled`, `member.webhook_url = webhook_url` 설정
  3. `MemberRepository.save(db, member)` 저장
- **추가 처리**: 세션의 `login_member` 딕셔너리도 갱신
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
- **Controller**: `AdminController._members()`, `AdminController._approve()`, `AdminController._reject()`
- **권한 체크**: `login_member.get("role") == Role.ADMIN.value`가 아니면 대시보드로 리다이렉트
- **Service 승인**: `MemberService.approve_member(db, member_id, admin_name)`
  1. 해당 멤버의 `approval_status`를 `ApprovalStatus.APPROVED.value`로 변경
  2. "회원 승인: {login_id}" 로그 기록 (actor: 관리자명)
- **Service 거절**: `MemberService.reject_member(db, member_id, admin_name)`
  1. 해당 멤버의 `approval_status`를 `ApprovalStatus.REJECTED.value`로 변경
  2. "회원 거절: {login_id}" 로그 기록
- **Template**: `admin/members.html` — 대기 멤버 목록 + 승인된 멤버 목록

##### E1-2. 멤버 추방
- **URL**: `POST /admin/members/{id}/kick`
- **Controller**: `AdminController._kick(member_id, request, db)`
- **Service**: `MemberService.kick_member(db, member_id, admin_name)`
  1. `_cleanup_member_references(db, member)` — A5와 동일한 참조 정리 로직
  2. "멤버 추방: {login_id}" 로그 기록
  3. `MemberRepository.delete(db, member)` — DB에서 삭제
- **회원 탈퇴(A5)와의 차이**: A5는 본인이 직접, E1-2는 관리자가 강제. 둘 다 `_cleanup_member_references()`를 호출하여 일정 참조를 정리.

#### E2. 로그 열람
- **URL**: `GET /admin/logs`
- **Controller**: `AdminController._logs(request, db)`
- **권한 체크**: `login_member.get("role") == Role.ADMIN.value`가 아니면 대시보드로 리다이렉트
- **Service**: `MemberService.get_all_logs(db)`
  - `ActivityLogRepository.find_all_order_by_created_at_desc(db)` — 최신순 정렬
- **Template**: `admin/logs.html` — 테이블 형태로 action, actor, created_at 표시

---

## 5. 인증/인가 처리

### 5.1 세션 기반 인증

이 시스템은 별도 인증 라이브러리 없이, **Starlette SessionMiddleware + 커스텀 LoginMiddleware**로 인증을 구현한다.

**인증 흐름:**
1. 사용자가 `/auth/login`에서 loginId, password 입력
2. `AuthController._login()`에서 `MemberService.login()` 호출
3. DB에서 ID/PW가 일치하고 `approval_status == "APPROVED"`인 멤버 조회
4. 성공 시 `request.session["login_member"] = member.to_session_dict()` — 세션에 회원 정보 딕셔너리 저장
5. 이후 모든 요청에서 `request.session.get("login_member")`로 로그인 사용자 조회

### 5.2 LoginMiddleware

```python
EXCLUDE_PREFIXES = ("/auth", "/service", "/static")

class LoginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 제외 경로 체크 — 로그인/회원가입/정적 파일은 인증 불필요
        if any(path.startswith(p) for p in EXCLUDE_PREFIXES):
            return await call_next(request)

        # 세션에서 로그인 정보 확인
        if request.session.get("login_member") is None:
            return RedirectResponse(url="/auth/login", status_code=302)

        return await call_next(request)
```

**동작 원리:**
- `EXCLUDE_PREFIXES`에 해당하는 경로는 인증을 건너뛴다
- 세션에 `login_member`가 없으면 → 로그인 페이지로 리다이렉트
- `BaseHTTPMiddleware`를 상속하여 모든 HTTP 요청을 가로챈다

### 5.3 미들웨어 등록 순서

```python
# main.py — 등록 역순으로 실행됨
app.add_middleware(LoginMiddleware)
app.add_middleware(SessionMiddleware, secret_key="teamschedule-secret-key")
```

**실행 순서**: 요청 → `SessionMiddleware` (세션 쿠키 복호화) → `LoginMiddleware` (인증 체크) → Router (Controller)

`SessionMiddleware`가 먼저 실행되어야 `request.session`을 사용할 수 있으므로, 코드에서는 `SessionMiddleware`를 나중에 등록한다 (Starlette는 등록 역순으로 미들웨어를 실행).

### 5.4 제외 경로 설명

| 경로 접두사 | 이유 |
|------------|------|
| `/auth` | 로그인 전에 접근해야 하는 페이지 (로그인, 회원가입, ID/PW 찾기) |
| `/service` | 로그인 없이도 볼 수 있어야 하는 정보 (이용약관, 개인정보처리방침) |
| `/static` | 정적 자원 (CSS, JavaScript 파일) — 인증 불필요 |

### 5.5 왜 별도 인증 라이브러리를 사용하지 않았는가?

| 항목 | FastAPI OAuth/JWT 라이브러리 | 직접 구현 (현재) |
|------|---------------------------|----------------|
| 설정 복잡도 | OAuth2 스키마, JWT 토큰 발급/검증, 의존성 체인 등 다수의 설정 필요 | Middleware 1개로 완결 |
| 학습 비용 | 토큰 기반 인증 개념 이해 필요 | HTTP 세션 수준에서 이해 가능 |
| 코드 투명성 | 라이브러리 내부에서 처리되어 흐름 추적이 어려움 | `dispatch()` 한 메서드에서 모든 인증 로직 확인 가능 |
| UML 작성 | 프레임워크 내부를 표현하기 어려움 | 시퀀스 다이어그램에서 명확히 표현 가능 |

→ 프로젝트 목적(구조 질문 대응, UML 작성 용이)에 맞춰 의도적으로 단순한 방식을 선택.

---

## 6. 프론트엔드 구조

### 6.1 Jinja2 템플릿 구조

```
templates/
├── base.html               ← 공통 레이아웃 (head, sidebar, header, footer)
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

**base.html 활용 (템플릿 상속):**
- `{% block title %}` — 페이지 제목
- `{% block content %}` — 메인 콘텐츠
- 각 페이지는 `{% extends "base.html" %}`로 공통 레이아웃을 상속받는다

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
  - 기간 일정은 `start_at ~ scheduled_at` 범위의 모든 날짜 셀에 표시
  - 최대 3개까지 표시, 초과 시 "+N개" 표시
- **간트 차트 뷰** (`renderGantt()`):
  - 모든 일정의 날짜 범위 계산 → 타임라인 헤더(월/일) 생성
  - 각 일정을 수평 바로 렌더링 (`left`, `width` 계산)
  - 오늘 날짜에 빨간 세로선 표시
  - 완료된 일정은 `.done` 클래스 적용 (흐릿한 색상)
- **뷰 전환**: `.view-tab` 버튼 클릭 → `#view-list`, `#view-calendar`, `#view-gantt` 중 선택된 것만 `display: block`, 나머지 `display: none`

### 6.4 서버 → 프론트엔드 데이터 전달

```python
# ScheduleController._list() 에서
schedules_json = json.dumps([
    {
        "id": s.id,
        "title": s.title,
        "startAt": s.start_at.isoformat() if s.start_at else None,
        "scheduledAt": s.scheduled_at.isoformat() if s.scheduled_at else None,
        "completed": s.completed,
        "createdBy": s.created_by.name if s.created_by else None,
        "createdAt": s.created_at.isoformat() if s.created_at else None,
    }
    for s in schedules
], ensure_ascii=False)
```

Controller에서 `json.dumps()`로 일정 데이터를 JSON 문자열로 직렬화하여 템플릿 변수(`schedules_json`)로 전달한다. Jinja2 템플릿에서 `{{ schedules_json | safe }}`로 출력하면 JavaScript에서 `JSON.parse()` 없이 바로 사용할 수 있다.

---

## 7. 주요 설계 결정 및 근거

### 7.1 SQLite 파일 DB 선택 이유
- **별도 DB 서버 불필요**: 설치/설정 없이 애플리케이션 실행만으로 DB 사용 가능
- **파일 모드 (`./data/teamschedule.db`)**: 서버 재시작해도 데이터 보존
- **SQLAlchemy 호환**: ORM을 통해 접근하므로 나중에 MySQL/PostgreSQL로 변경 시 접속 URL만 바꾸면 됨
- 학습 프로젝트에 적합: 외부 DB 없이 프로젝트 배포 가능

### 7.2 세션 기반 인증 (별도 인증 라이브러리 미사용)
- 위 5.5절 참조. 핵심: **구조 단순화**와 **UML 표현 용이성**

### 7.3 순수 JavaScript (프론트엔드 라이브러리 미사용)
- React, Vue, FullCalendar 등의 라이브러리 없이 순수 JS로 캘린더/간트 차트 구현
- **이유**: 외부 의존성 최소화, 코드 전체를 직접 작성하여 구조 완전 이해 가능
- **장점**: 빌드 도구(webpack 등) 불필요, HTML 파일에 `<script>` 태그만으로 동작

### 7.4 백엔드 최대한 단순하게 유지
- Service 2개 (MemberService, ScheduleService)로 모든 비즈니스 로직 처리
- DTO 클래스 미사용 — 엔티티를 직접 Controller에서 받고 전달
- 별도 예외 클래스 미정의 — `None` 반환으로 에러 상황 처리
- **이유**: 개발자가 모든 구조를 완벽히 파악할 수 있도록

### 7.5 싱글톤 DI 패턴 (db를 메서드 인자로 전달)
- Repository/Service 인스턴스는 앱 시작 시 한 번만 생성 (상태 없는 싱글톤)
- DB 세션(`db: Session`)은 모든 Repository/Service 메서드의 첫 번째 인자로 전달
- **이유**: 클래스 구조를 단순하게 유지하면서도 OOP 원칙(계층 분리, 의존성 주입)을 지킴
- **장점**: 클래스 다이어그램이 달라지지 않고, 이해해야 할 구조가 복잡해지지 않음

### 7.6 일정의 단일일/기간 설계 (start_at nullable 패턴)
- `start_at` 필드 하나만 추가하여 기간 일정 지원
- `start_at == None`이면 단일일 일정, 값이 있으면 기간 일정
- 기존 단일일 일정 로직에 영향 없음 (하위 호환)
- 프론트엔드에서 "하루/기간" 토글 UI로 사용자 선택

---

## 8. 데이터베이스

### 8.1 설정 (config/database.py)

```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "teamschedule.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**주요 설정 설명:**
- `check_same_thread=False`: FastAPI가 비동기로 동작하므로 SQLite의 단일 스레드 제한을 해제
- `autocommit=False`: 명시적으로 `db.commit()`을 호출해야 DB에 반영 (트랜잭션 제어)
- `autoflush=False`: `flush()`를 명시적으로 호출해야 SQL이 실행됨
- `get_db()`: FastAPI의 `Depends`를 위한 제너레이터 함수. 요청 처리 후 `finally`에서 세션을 자동으로 닫음

**테이블 자동 생성:**
```python
# main.py의 _init_db() 함수에서
Base.metadata.create_all(bind=engine)
```
앱 시작 시 모든 엔티티 클래스의 `__tablename__`에 해당하는 테이블을 자동 생성한다 (이미 존재하면 무시).

### 8.2 테이블 관계도

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   MEMBER     │       │   SCHEDULE   │       │ ACTIVITY_LOG │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │◄──┐   │ id (PK)      │       │ id (PK)      │
│ login_id     │   │   │ title        │       │ action       │
│ password     │   ├───│ created_by_id│(FK)   │ actor        │
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
- `SCHEDULE`: 일정 테이블. `created_by_id`는 `MEMBER.id`를 참조하는 FK
- `SCHEDULE_TAG`: N:M 관계를 위한 중간 테이블. `Table()` 함수로 직접 정의
- `ACTIVITY_LOG`: 활동 로그 테이블. 다른 테이블과 FK 관계 없음 (독립)

### 8.3 초기 데이터

`main.py`의 `_init_db()` 함수에서 앱 최초 실행 시 관리자 계정 자동 생성:
```
login_id: admin / password: admin / name: 관리자 / email: admin@team.com
role: ADMIN / approval_status: APPROVED
```

---

## 9. UML 다이어그램 목록

모든 다이어그램은 **StarUML**로 작성되었으며, `docs/diagrams/` 디렉토리에 위치한다. Python 버전도 동일한 클래스 구조이므로 같은 다이어그램을 공유한다.

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
| `StateMachine_Schedule.png` | 상태 머신 다이어그램 (일정) | 진행중 ↔ 완료 상태 전이. 완료 처리/취소, 자동 완료(scheduled_at 경과), 수정, 삭제 이벤트 포함 |
| `StateMachine_Member.png` | 상태 머신 다이어그램 (회원) | 승인 대기 → 승인됨/거절됨 상태 전이. 탈퇴/추방 시 종료 |
| `Activity_Login.png` | 액티비티 다이어그램 (로그인) | 로그인 유스케이스의 흐름. 계정 존재 여부와 승인 상태 분기, 실패 시 재시도 루프 |

---

## 10. 예상 질문 및 답변

### Q1. 유스케이스 다이어그램에서 로그인을 include 관계로 표현하지 않은 이유는?
**A**: 유스케이스 다이어그램은 흐름도가 아니므로 유스케이스 간 선후 관계를 표현하지 않습니다. `«include»`는 여러 유스케이스에 공통으로 들어가는 상호작용을 분리할 때 쓰는 관계이고, "로그인한 상태여야 한다"는 것은 실행 순서에 대한 조건이므로 각 유스케이스 명세의 사전 조건(Precondition)에 적었습니다. 코드에서는 `LoginMiddleware`의 `dispatch()`에서 세션의 `login_member`를 확인하여 이를 구현했습니다. 관리자는 팀원의 기능을 모두 쓸 수 있으므로 액터 일반화로 표현했고, 1분마다 실행되는 자동 완료는 타이머 액터가 수행하는 유스케이스로 표현했습니다.

### Q2. 클래스 다이어그램에서 Member와 Schedule의 관계가 두 개인 이유는?
**A**: 첫 번째는 `created_by` 관계로, 일정을 "누가 만들었는지"를 나타내는 N:1(다대일) 관계입니다 (`relationship("Member", foreign_keys=[created_by_id])`). 두 번째는 `tagged_members` 관계로, 일정에 "누가 관련되어 있는지"를 나타내는 N:M(다대다) 관계입니다 (`relationship("Member", secondary=schedule_tag)`). 하나의 일정은 한 명이 만들지만, 여러 멤버를 태그할 수 있고, 한 멤버도 여러 일정에 태그될 수 있습니다.

### Q3. 로그인의 성공/실패 분기는 시퀀스 다이어그램에서 어떻게 표현했는가?
**A**: 하나의 다이어그램에 분기를 넣지 않고 주 시퀀스(성공)와 대안 시퀀스(실패)를 각각의 시퀀스 다이어그램으로 나누어 그렸습니다. `MemberService.login()`이 회원을 반환하면(승인 상태 = APPROVED) 세션에 회원 정보 딕셔너리를 저장하고 홈 화면으로 리다이렉트하며, 계정이 없거나 승인되지 않아 반환값이 없으면 에러 메시지와 함께 로그인 페이지로 리다이렉트합니다. 분기 조건은 응답 메시지의 가드 `[조건]`으로 표기했습니다.

### Q4. 인증은 어떻게 구현했는가?
**A**: 별도 인증 라이브러리 대신 Starlette의 `SessionMiddleware`와 커스텀 `LoginMiddleware`로 직접 구현했습니다. 로그인 성공 시 `request.session["login_member"] = member.to_session_dict()`로 세션에 사용자 정보를 딕셔너리로 저장합니다. 이후 모든 요청은 `LoginMiddleware.dispatch()`를 거치며, 세션에 `login_member`가 없으면 로그인 페이지로 리다이렉트됩니다. `/auth`, `/service`, `/static` 경로는 `EXCLUDE_PREFIXES`로 인증에서 제외합니다.

### Q5. 왜 별도 인증 라이브러리(OAuth, JWT)를 사용하지 않았는가?
**A**: 프로젝트의 목표가 "백엔드 구조를 최대한 단순하게 유지하여 개발자가 모든 구조를 파악할 수 있도록" 하는 것이었기 때문입니다. OAuth/JWT 방식은 토큰 발급, 검증, 갱신 등 여러 계층이 추가되어 구조가 복잡해집니다. 반면 미들웨어 방식은 `dispatch()` 메서드 하나에서 인증 로직이 모두 보이므로, 시퀀스 다이어그램에서도 명확히 표현할 수 있고, 질문에 대해 쉽게 답변할 수 있습니다.

### Q6. 일정의 시작일/종료일 처리 로직은?
**A**: `Schedule` 엔티티에 `start_at`(시작일)과 `scheduled_at`(종료일/단일일정일) 두 필드를 두었습니다. `start_at`이 `None`이면 단일일 일정, 값이 있으면 기간 일정입니다. 프론트엔드에서 "하루/기간" 토글 버튼으로 선택하며, "하루" 선택 시 `start_at` 입력 필드가 숨겨지고 값이 비워집니다. Controller에서 `startAt` 파라미터가 비어있으면 `None`으로 변환하여 Service에 전달합니다. 캘린더/간트 차트에서는 `start_at`이 있으면 해당 기간에 걸쳐 표시합니다.

### Q7. 상태 머신 다이어그램의 각 상태 전이 조건은?
**A**: 일정(Schedule)의 상태는 `completed` 필드 값에 대응하는 **진행중**과 **완료** 두 가지입니다:
- **[초기] → 진행중**: 사용자가 일정을 등록하면 `completed = False` 상태로 생성
- **진행중 → 완료**: "완료 처리됨" 이벤트 (`toggle_complete()`), 또는 "마감 시각(scheduled_at) 경과" 이벤트로 시스템이 자동 완료 처리 (백그라운드 스레드, 60초 간격)
- **완료 → 진행중**: "완료 취소됨" 이벤트 (토글 방식)
- **진행중 → 진행중, 완료 → 완료**: "일정 수정됨" 이벤트. 수정은 상태를 바꾸지 않음
- **진행중/완료 → [종료]**: "일정 삭제됨" 이벤트

전이 라벨은 `이벤트 / 액션` 형식이며, 액션은 활동 로그 기록입니다. 회원(Member)은 별도 상태 머신으로 그렸습니다: 가입 시 **승인 대기**, 관리자 승인 시 **승인됨**, 거절 시 **거절됨**이 되고, 승인된 회원이 탈퇴하거나 추방되면 종료됩니다.

### Q8. MVC 패턴이 코드에 어떻게 적용되어 있는가?
**A**: 
- **Model**: `entity` 패키지의 `Member`, `Schedule`, `ActivityLog` 클래스가 도메인 모델 역할. SQLAlchemy의 `DeclarativeBase`를 상속하여 DB 테이블과 매핑.
- **View**: `templates/` 디렉토리의 Jinja2 HTML 파일들. `{{ }}`, `{% for %}` 등으로 Model 데이터를 화면에 렌더링.
- **Controller**: `controller` 패키지의 클래스들. HTTP 요청을 받아 Service를 호출하고, 결과를 `TemplateResponse`로 View에 전달.
- Controller는 Service만 의존하고, Repository를 직접 호출하지 않아 계층 간 역할이 명확히 분리됩니다.

### Q9. N:M (다대다) 관계에서 중간 테이블은 어떻게 생성되는가?
**A**: `entity/schedule.py`에서 SQLAlchemy의 `Table()` 함수로 `schedule_tag` 중간 테이블을 직접 정의합니다. `Base.metadata.create_all(bind=engine)` 호출 시 이 테이블이 자동 생성됩니다. 이 테이블은 `schedule_id`와 `member_id` 두 개의 외래키를 가지며, `Schedule` 클래스의 `tagged_members` 관계에 `secondary=schedule_tag`으로 연결됩니다. 별도의 엔티티 클래스를 작성할 필요 없이 SQLAlchemy가 관리합니다.

### Q10. 활동 로그(ActivityLog)는 왜 다른 엔티티와 FK 관계가 없는가?
**A**: `actor` 필드를 `str`(loginId)으로 저장하여 의도적으로 FK 관계를 맺지 않았습니다. 이렇게 하면 회원이 탈퇴하거나 추방되어도 로그 기록이 삭제되지 않고 보존됩니다. 또한 시스템 자동 완료 같이 특정 사용자가 아닌 "시스템"이 actor인 경우에도 별도 처리 없이 문자열로 저장할 수 있습니다.

### Q11. 자동 완료 기능의 구현 방식은?
**A**: `main.py`에서 `threading.Thread(target=_auto_complete_loop, daemon=True)`로 백그라운드 데몬 스레드를 실행합니다. 이 스레드는 `time.sleep(60)`으로 60초마다 반복하면서 `ScheduleService.auto_complete_expired(db)`를 호출합니다. 이 메서드는 `completed == False`이고 `scheduled_at`이 현재 시각보다 이전인 일정을 조회하여 자동으로 `completed = True`로 변경합니다. 이때 actor는 "시스템"으로 기록됩니다. 데몬 스레드이므로 메인 프로세스 종료 시 함께 종료됩니다.

### Q12. 프로젝트에서 사용한 디자인 패턴은?
**A**: 
- **MVC 패턴**: Controller-Service-Repository 계층 분리
- **Repository 패턴**: Repository 클래스로 데이터 접근 추상화. SQLAlchemy 쿼리를 Repository 내부에 캡슐화하여 Service가 쿼리 로직을 몰라도 되도록 함
- **싱글톤 패턴**: Repository/Service 인스턴스를 앱 시작 시 한 번만 생성하여 재사용
- **DI (의존성 주입)**: 생성자에서 Repository를 주입받아 사용. Controller가 Service를, Service가 Repository를 주입받음
- **미들웨어 패턴**: `BaseHTTPMiddleware`를 상속하여 모든 요청에 대한 횡단 관심사(인증) 처리

### Q13. 관리자 권한 체크는 어떻게 하는가?
**A**: `AdminController`의 각 메서드 첫 줄에서 `self._is_admin(request)`를 호출합니다. 이 메서드는 `login_member.get("role") == Role.ADMIN.value`인지 확인합니다. ADMIN이 아니면 `RedirectResponse(url="/")` (대시보드)로 리다이렉트합니다. 미들웨어는 "로그인 여부"만 확인하고, "어떤 역할인지"는 각 Controller에서 판단합니다.

### Q14. 회원 탈퇴/추방 시 관련 데이터는 어떻게 처리되는가?
**A**: `MemberService._cleanup_member_references(db, member)` 메서드에서 처리합니다. 모든 Schedule을 순회하면서 (1) `tagged_members` 목록에서 해당 멤버를 제거하고, (2) `created_by`가 해당 멤버인 일정의 `created_by`와 `created_by_id`를 `None`으로 설정합니다. 이후 `MemberRepository.delete(db, member)`로 멤버를 삭제합니다. 활동 로그(ActivityLog)는 FK 관계가 없으므로 영향 없이 보존됩니다.

### Q15. FastAPI의 의존성 주입(Depends)은 어디에 사용되는가?
**A**: DB 세션 주입에 사용됩니다. `config/database.py`의 `get_db()` 제너레이터 함수를 `Depends(get_db)`로 선언하면, FastAPI가 요청마다 새 DB 세션을 생성하고, 요청 완료 후 `finally` 블록에서 자동으로 세션을 닫습니다. 모든 Controller 메서드에서 `db: Session = Depends(get_db)` 형태로 사용됩니다. 이 방식으로 세션의 생명주기를 HTTP 요청 단위로 관리합니다.
