# 회원 API 인수인계 문서

## 작업 목적
BCSDLab 동아리 회원 관리를 위한 FastAPI 백엔드 구현.
Google OAuth 인증, 학교 이메일/전화번호 인증을 통한 회원가입과 JWT 기반 인증된 회원 조회 API를 제공한다.

## 아키텍처

```
Client → FastAPI → Google Sheets (members 탭)
                 → Google OAuth (ID Token 검증)
                 → Firebase Auth (전화번호 검증)
                 → SMTP (학교 이메일 인증 코드)
```

- **데이터 저장**: Google Sheets `members` 탭 (PostgreSQL 없음)
- **인증**: Google OAuth → JWT 발급
- **회원가입**: Google OAuth + 학교 이메일 인증 + Firebase Phone Auth

## 프로젝트 구조

```
src/bcsd_api/
├── main.py           # FastAPI app factory
├── config.py         # pydantic-settings 환경변수
├── dependencies.py   # 공용 Depends (Settings, Sheets, JWT 인증)
├── id_gen.py         # M-{timestamp}-{random3} ID 생성
├── exception/        # AppException 기반 예외 처리 (Spring @ControllerAdvice 스타일)
├── filter/           # 재사용 필터 시스템 (BaseFilter → MemberFilter)
├── sheets/           # gspread 래퍼 (Google Sheets 접근)
├── auth/             # 인증 (Google OAuth, JWT, 이메일 인증, 회원가입)
└── member/           # 회원 조회 (목록+필터, 상세)
```

## API 엔드포인트

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/v1/auth/login` | No | Google ID Token → JWT (기존 회원만) |
| POST | `/v1/auth/verify-email` | No | 학교 이메일로 인증 코드 발송 |
| POST | `/v1/auth/confirm-email` | No | 인증 코드 검증 |
| POST | `/v1/auth/register` | No | 회원가입 완료 → JWT 발급 |
| GET | `/v1/members` | Yes | 회원 목록 (필터+페이지네이션) |
| GET | `/v1/members/{member_id}` | Yes | 회원 상세 조회 |

### 필터 파라미터 (GET /v1/members)
- `page`, `size`: 페이지네이션
- `sort_by`, `sort_order`: 정렬
- `status`, `track`, `team`, `payment_status`: 완전 일치 필터
- `name`: 부분 일치 검색

## 설정 방법

### 환경 변수 (.env)
`.env.example` 참고. 주요 변수:
- `GOOGLE_CLIENT_ID`: Google OAuth 클라이언트 ID
- `JWT_SECRET`: JWT 서명 키
- `GOOGLE_SHEETS_ID`: Google Sheets 문서 ID
- `GOOGLE_SERVICE_ACCOUNT_FILE`: 서비스 계정 JSON 파일 경로
- `SMTP_*`: 이메일 발송 설정
- `FIREBASE_CREDENTIALS_FILE`: Firebase 서비스 계정 JSON

### Google Sheets 스키마 (members 탭)
헤더 행: `id | name | email | school_email | phone | status | track | team | join_date | payment_status | last_updated`

### 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m bcsd_api.main
```
Swagger UI: http://localhost:8000/docs

## 핵심 설계 결정

### 재사용 필터 시스템
`filter/base.py`의 `BaseFilter` + `apply_filter()`는 어떤 리소스에도 재사용 가능.
새 필터 추가 시 `BaseFilter`를 상속하고 Optional 필드만 추가하면 된다.
`search_fields` 클래스 변수로 부분 일치 검색 필드를 선언한다.

### 예외 처리
`AppException`을 상속하여 선언적으로 에러 정의. `register_handlers()`에서 자동 JSON 매핑.
Spring의 `@ControllerAdvice` 패턴과 동일한 구조.

### 이메일 인증
인메모리 딕셔너리에 코드 저장 (TTL 5분). MVP용이며, 프로덕션에서는 Redis 등으로 교체 권장.

## 알려진 제약사항
- 이메일 인증 코드는 서버 재시작 시 소실 (in-memory)
- Google Sheets API 속도 제한 (분당 60회) → 대량 트래픽 시 캐싱 필요
- Firebase Admin SDK 초기화가 아직 `main.py`에 포함되지 않음 → 회원가입 시 Firebase 설정 필요
- `confirm-email` 성공 여부를 `register` 시점에 서버 측에서 재검증하지 않음 → 클라이언트 플로우에 의존

## 향후 개선 사항
- Redis 기반 인증 코드 저장소
- Firebase Admin SDK 초기화 (`firebase_admin.initialize_app`)
- 회원가입 시 이메일 인증 완료 여부를 서버에서 재확인하는 상태 관리
- 회원 정보 수정 API (PUT /v1/members/{id})
- 비밀번호 없는 인증이므로 refresh token 전략 검토
