# URL 단축 + QR 코드 생성

## 목적

BCSDLab 내부/외부 용도로 긴 URL을 단축하고, 임의 텍스트에서 QR 코드를 생성하는 기능.
동아리 링크 공유(Google Forms, Docs 등)와 외부 홍보/이벤트(모집 폼, 행사 안내 QR 배포) 모두 지원.

## 데이터 모델

Google Sheets에 2개 시트 추가 (마이그레이션 V003).

### `links` 시트

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | string | `L-YYYYMMDDHHmmss-XXX` |
| code | string | 단축 코드 (랜덤 6자 또는 커스텀) |
| title | string | 링크 제목 |
| description | string \| null | 링크 설명 (선택) |
| url | string | 원본 URL |
| creator_id | string | 생성자 member ID |
| created_at | datetime | 생성 시각 (KST) |
| expires_at | datetime \| null | 예정 만료 시각 (없으면 영구) |
| expired_at | datetime \| null | 실제 만료 처리 시각 (수동 조기 만료 시 설정) |
| updated_at | datetime | 마지막 수정 시각 (KST) |

### `link_clicks` 시트

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | string | `LC-YYYYMMDDHHmmss-XXX` |
| link_id | string | FK → links.id |
| clicked_at | datetime | 클릭 시각 (KST) |
| referer | string \| null | HTTP Referer |
| user_agent | string \| null | User-Agent |

## API 엔드포인트

### URL 단축 (인증: Regular 이상)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/v1/shorten` | 단축 URL 생성 |
| GET | `/v1/shorten` | 전체 목록 (필터/페이징) |
| GET | `/v1/shorten/filters` | 필터 옵션 목록 |
| GET | `/v1/shorten/{link_id}` | 상세 + 클릭 통계 |
| POST | `/v1/shorten/{link_id}` | 수정 — title, description, expires_at (생성자 권한 동일 시 본인만) |
| PATCH | `/v1/shorten/{link_id}/toggle` | 만료 토글 — active ↔ expired (생성자 권한 이상) |
| DELETE | `/v1/shorten/{link_id}` | 삭제 (생성자 권한 이상) |

### 리다이렉트 (공개)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/s/{code}` | 302 리다이렉트 + 클릭 기록 |

> `/s/{code}`는 `/v1/` prefix 컨벤션의 의도적 예외. 공개 단축 URL은 경로가 최대한 짧아야 하므로.

### QR 코드 (인증: Regular 이상)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/v1/qr?text=...&format=png&size=300` | 텍스트 → QR 이미지 |

## 상세 설계

### 코드 생성
- 랜덤: 영문 소문자 + 숫자 6자 (예: `a3x7k9`), 중복 시 최대 5회 재생성
- 커스텀: 유니코드 문자 허용 (한글, 영문 등), `-` 허용, 특수문자(`/`, `?`, `#`, `&`, `=`, `%`, `\` 등 URL 예약 문자) 불가, 2~100자, 중복 시 409 Conflict
- 커스텀 코드는 URL 인코딩되므로 `bcsdlab.com/s/2025모집` 같은 형태 가능

### 리다이렉트 흐름
1. `GET /s/{code}` 요청
2. `links` 시트에서 code 조회
3. 없으면 404 NotFound
4. 만료 체크 (순서 중요):
   - `expired_at` 존재 → 410 Gone (수동 만료 또는 n8n 자동 처리 완료)
   - `expires_at` 존재하고 `expires_at < now()` → 410 Gone (n8n이 아직 처리 안 한 경우)
5. `link_clicks`에 row 추가 (`BackgroundTasks`로 비동기 — 리다이렉트 응답 차단 방지)
6. 302 리다이렉트 (301 아님 — 브라우저 캐시로 인한 추적 누락/만료 체크 우회 방지)

### 통계
- `GET /v1/shorten/{link_id}` 시 `link_clicks`에서 해당 link_id rows 조회
- 총 클릭 수 + 날짜별 클릭 수 집계

### 삭제
- row 삭제 (soft delete 없음)
- `link_clicks` 먼저 삭제 후 `links` row 삭제 (순서 중요 — link 먼저 삭제 시 클릭 orphan 발생)
- 권한: SpiceDB `check(link, delete, user_id)` — 본인이거나 생성자보다 상위 권한이면 허용, 아니면 403 Forbidden

### 필터 (`LinkFilter` 클래스, `BaseFilter` 확장)
- creator_id: 생성자 필터
- expired: `active` / `expired` / `all` (서비스 레이어에서 `expired_at` 존재 또는 `expires_at < now()`로 판단 후 필터링)

### 필터 옵션 (`/v1/shorten/filters`)
- creators: `list[CreatorOption]` — `{id: string, name: string}` (links 시트의 고유 creator_id → members 시트에서 이름 조회)
- expired: `["active", "expired", "all"]` 고정값

### QR 코드
- 파라미터를 Pydantic 모델(`QrParams`)로 검증: `text` (필수, 최대 2000자), `format` (`png`/`svg`, 기본 `png`), `size` (100~1000, 기본 300)
- 매번 생성 (저장 안 함 — CPU 연산 ~10ms, 캐시 불필요)
- 응답: `StreamingResponse` (image/png 또는 image/svg+xml)

## 모듈 구조

```
src/bcsd_api/
├── shorten/
│   ├── router.py      # 엔드포인트 8개
│   ├── service.py     # 생성, 목록, 상세, 삭제, 필터
│   ├── schema.py      # Request/Response 모델
│   └── repository.py  # links + link_clicks 시트 접근
│
├── qr/
│   ├── router.py      # GET /v1/qr
│   ├── schema.py      # QrParams 모델
│   └── service.py     # QR 생성 (qrcode 라이브러리)
│
├── redirect.py         # GET /s/{code} (단일 파일, track.py 패턴)
```

`redirect.py`는 `shorten.service`의 조회/클릭 기록 함수를 재사용.

## 권한 모델 (SpiceDB)

### 권한 레벨 (낮음 → 높음)
General(0) < Beginner(1) < Regular(2) < Edu Leader(3) < Track Leader(4) < Vice President(5) < President(6) < Mentor(7)

- status: General, Beginner, Regular, Mentor
- role: Edu Leader, Track Leader, Vice President, President
- 사용자의 권한 레벨 = `max(status 레벨, role 레벨)`

### 권한 규칙
1. 생성자 권한 **이상**이면 삭제/만료 가능
2. 생성자 권한과 **동일**하면 본인만 수정 가능

### SpiceDB 스키마
link 생성 시 `creator` relation 추가. 권한 체크는 `AuthzClient.check()`로 처리.

### members 시트 변경
`role` 컬럼 추가 (V003 마이그레이션에 포함). 값: `null`(없음), `edu_leader`, `track_leader`, `vice_president`, `president`

## 사전 작업 (기존 코드 수정)

### SheetsClient 확장
- `delete_row(sheet, column, value)` — 단일 row 삭제
- `delete_rows(sheet, column, value)` — 매칭되는 모든 rows 삭제 (역순 삭제로 인덱스 밀림 방지)

### 예외 클래스 추가
- `Gone` (410) — `exception/errors.py`에 추가

### main.py 라우터 등록
- `shorten_router`, `qr_router`, `redirect_router`를 `create_app()`에 등록

## 의존성 추가

- `qrcode[pil]` — PNG/SVG QR 생성

## 마이그레이션

V003: `links`, `link_clicks` 시트 생성 + members 시트에 `role` 컬럼 추가 (기존 V001, V002 패턴 따름)

## n8n workflow

### 자동 만료 처리 (cron)
- 주기: n8n cron trigger
- 로직: `links` 시트에서 `expires_at < now() && expired_at == null` 인 row들에 `expired_at = now()` 기록
- Google Sheets 노드로 직접 처리

## nginx 설정

`bcsdlab.com/s/{code}` — `stage.bcsdlab.com` server 블록에 `/s/` location 추가, API upstream으로 프록시.
