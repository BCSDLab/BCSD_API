# BCSDLab INTERNAL - Google Workspace Automation System

## Project Overview
Club management automation system using **n8n** to orchestrate **Google Workspace** (Sheets as database, Forms for input, Docs for reports). FastAPI is optional glue for authorization checks (SpiceDB) when needed.

## Architecture
```
Client → FastAPI (auth, member API) → Google Sheets (database)
       → Google OAuth (ID Token 검증)
       → Resend (학교 이메일 인증)

n8n (automation workflows) → Google Sheets (database) → Slack/Email (output)
```

### Core Principle
- **Google Sheets IS the database** - no PostgreSQL/MongoDB needed
- **FastAPI** handles auth (Google OAuth + JWT) and member CRUD
- **n8n** handles automation workflows (fee reminders, status transitions)
- **SpiceDB** - future consideration for fine-grained authorization

### Components
- **FastAPI**: Auth (Google OAuth, JWT), member API, filter system
- **Google Sheets**: Source of truth (members, fees, groups, events, workflow_logs)
- **n8n**: Automation workflows (fee reminders, notifications)
- **Slack**: BCSDLab workspace (admin access available)
- **Docker Compose**: Local dev + production environment

## Key Technical Decisions
- **Trigger**: Google Sheets trigger (polling, 1-2 min delay) - NOT Apps Script webhooks
- **Notifications**: Email (SMTP) for MVP, Slack DM as enhancement
- **IDs**: `{prefix}-{YYYYMMDDHHmmss}-{random3}` (e.g., `M-20240128143022-A7K`)
- **Package name**: `bcsd_api`
- **Timezone**: `Asia/Seoul` (KST)
- **Fee amount**: 10,000 KRW/month (MVP constant)

## Google Sheets Schema
- `members`: id, name, email, school_email, phone, status, track, team, join_date, payment_status, last_updated
- `fees`: id, member_id, amount, paid_date, payment_method, notes, semester, last_updated
- `groups`: id, name, type, parent_id, size, leader_email, last_updated
- `events`: id, title, date, type, organizer, attendees, notes
- `workflow_logs`: timestamp, workflow_name, status, input_data, output_data, error_message

## Business Rules
- **Fee model**: Payment-logging (rows exist ONLY when money received, NOT invoice model)
- **No `due_date` column** in fees - due dates are implicit (first Monday of each month)
- **Payment status**: Unpaid → Paid (on payment), Paid → Unpaid (semester reset), → Exempt (Mentor promotion)
- **Member status**: Beginner → Regular → Mentor → Alumni
- **Reminders**: Weekly on Mondays at 9am KST (`0 9 * * 1`)
- **Foreign keys**: Store member ID (not email) in fees.member_id; lookups done by email

## Execution Waves
See `memory/plan-tasks.md` for detailed task breakdown.

- **Wave 1** (Foundation): Docker Compose, Google API setup, Sheets schema design
- **Wave 2** (n8n Dev): Sheets integration, Forms templates, data migration
- **Wave 3** (Workflows): Fee payment, reminders, member onboarding, status transitions
- **Wave 4** (Optional): SpiceDB authorization decision + implementation

## Code Conventions (Python / FastAPI / Django)
- indent depth는 2를 넘지 않는다. 1까지만 허용. 깊어지면 함수를 분리한다.
- 삼항 표현식(`x if cond else y`)을 쓰지 않는다.
- `else`를 쓰지 않는다. `match/case`도 허용하지 않는다. early return으로 해결한다.
- 리스트, 딕셔너리, 집합 등 컬렉션 타입을 사용한다. `array` 모듈을 사용하지 않는다.
- 함수명, 변수명은 가능한 한 단어(`snake_case` 기준 최대 두 단어).
- 함수 길이는 15라인을 넘지 않는다. 함수는 한 가지 일만 한다.
- 모든 모델/클래스를 작게 유지한다.
- 이름을 축약하지 않는다.
- 인스턴스 변수는 3개 이하로 유지한다. 단, Pydantic 모델(스키마)은 도메인 필드 수만큼 허용한다.
- 확장성, 의존성, 클린 코드를 고려하여 구조를 설계한다.
- 프레임워크를 적극 활용한다. (FastAPI `Depends`, Pydantic, Django ORM 등)
- 패키지는 기능별로 묶는다.
- 라우터 함수는 요청/응답 스키마 정의와 OpenAPI 문서화 용도로만 사용한다. 로직은 서비스 레이어에 위임한다.
- 모든 API 엔드포인트는 `/v1/`으로 시작한다.
- 템플릿(Cookiecutter, 프로젝트 보일러플레이트, Pydantic BaseModel 상속 등)을 적극 활용하여 반복 코드를 줄인다.

## Documentation Convention
- 각 작업(태스크) 완료 시 `docs/` 디렉토리에 인수인계용 문서를 작성한다.
- 문서에는 다음을 포함한다:
  - 작업 목적 및 배경
  - 구현 내용 상세 (아키텍처, 데이터 흐름, 핵심 로직)
  - 설정 방법 및 환경 변수
  - 테스트/검증 방법
  - 알려진 제약사항 및 향후 개선 사항
- 문서만 보고 다른 사람이 해당 작업을 이해하고 유지보수할 수 있어야 한다.

## Project Conventions
- Commit messages: `feat(scope): description`, `docs(scope): description`
- Workflow exports: `workflows/*.json`
- Documentation: `docs/*.md`
- Source: `src/bcsd_api/`
- Credentials: NEVER commit (`.gitignore` enforced)
