# 초기 배포 가이드

## 사전 준비

### 서버 요구사항
- Docker & Docker Compose (v2)
- Git
- SSH 접근 권한

### 필요 권한
- `bcsdlab-credentials` 레포 접근 권한 (GitHub)
- Google Cloud 서비스 계정 JSON 파일
- (선택) Slack webhook URL

## 파일 배치

```
~/bcsdlab-credentials/bcsd-api/backend/
  ├── .env              ← 환경변수 (모든 시크릿)
  ├── credentials.json  ← Google 서비스 계정 JSON
  └── ...               ← 기타 의존 파일

~/BCSD_API/             ← 이 레포 clone
  ├── .env              ← deploy.sh가 복사
  ├── credentials.json  ← deploy.sh가 복사
  └── ...               ← backend/ 내 모든 파일 복사됨
```

`deploy.sh`가 `bcsdlab-credentials/bcsd-api/backend/` 내 모든 파일을 프로젝트 루트로 복사합니다.
Docker Compose가 `credentials.json`을 컨테이너 내부 `/app/credentials.json`에 read-only로 마운트합니다.

## 첫 배포 순서

### 1. 레포 clone

```bash
cd ~
git clone git@github.com:BCSDLab/BCSD_API.git
cd BCSD_API
```

### 2. credentials 레포 clone

```bash
cd ~
git clone git@github.com:BCSDLab/bcsdlab-credentials.git
```

### 3. .env 작성

`bcsdlab-credentials/bcsd-api/backend/.env`를 작성합니다. `.env.example`을 참고하세요.

```bash
cp BCSD_API/.env.example bcsdlab-credentials/bcsd-api/backend/.env
# 각 값을 실제 값으로 수정
```

### 4. credentials.json 배치

Google Cloud Console에서 서비스 계정 키(JSON)를 다운로드하여 배치합니다.

```bash
# 다운로드한 JSON을 credentials 레포에 배치
cp ~/Downloads/service-account-key.json ~/bcsdlab-credentials/bcsd-api/backend/credentials.json
```

### 5. Docker 네트워크 생성

```bash
docker network create bcsd
```

### 6. SSL 초기화

```bash
cd ~/BCSD_API
bash infra/scripts/init-ssl.sh
```

### 7. 첫 배포

```bash
bash infra/scripts/deploy.sh
```

이 스크립트가 수행하는 작업:
1. `bcsdlab-credentials/bcsd-api/backend/` 내 모든 파일을 프로젝트 루트로 복사
2. 새 슬롯(blue/green) 빌드 및 시작
3. 헬스체크 (`/openapi.json`)
4. nginx 트래픽 전환
5. 이전 슬롯 정지

## 이후 배포

main push 시 CI/CD 자동 배포, 또는 수동:

```bash
cd ~/BCSD_API
bash infra/scripts/deploy.sh
```

## 환경변수 목록

| 변수 | 용도 | 예시 |
|------|------|------|
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | `123456.apps.googleusercontent.com` |
| `JWT_SECRET` | JWT 서명 비밀키 | 랜덤 문자열 |
| `JWT_ALGORITHM` | JWT 알고리즘 | `HS256` |
| `JWT_EXPIRE_MINUTES` | JWT 만료 시간(분) | `1440` |
| `GOOGLE_SHEETS_ID` | Google Sheets 문서 ID | Sheets URL의 `/d/` 뒤 값 |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | 서비스 계정 JSON 경로 | `credentials.json` |
| `RESEND_API_KEY` | Resend 이메일 API 키 | `re_...` |
| `RESEND_SENDER` | 발신 이메일 주소 | `noreply@bcsdlab.com` |
| `CORS_ORIGINS` | 허용 CORS origin | `https://internal.bcsdlab.com` |
| `COOKIE_NAME` | 인증 쿠키 이름 | `access_token` |
| `COOKIE_SECURE` | Secure 쿠키 여부 | `true` (프로덕션) |
| `POSTGRES_USER` | PostgreSQL 사용자 | `bcsd` |
| `POSTGRES_PASSWORD` | PostgreSQL 비밀번호 | 랜덤 문자열 |
| `POSTGRES_DB` | PostgreSQL 데이터베이스명 | `bcsd` |
| `POSTGRES_PORT` | PostgreSQL 호스트 포트 | `5432` |
| `POSTGRES_VOLUME_PATH` | PostgreSQL 데이터 경로 | `/home/ubuntu/bcsd-data/postgres` |
| `REDIS_PASSWORD` | Redis 비밀번호 | 랜덤 문자열 |
| `REDIS_PORT` | Redis 호스트 포트 | `6379` |
| `REDIS_VOLUME_PATH` | Redis 데이터 경로 | `/home/ubuntu/bcsd-data/redis` |
| `MONGO_USER` | MongoDB 사용자 | `bcsd` |
| `MONGO_PASSWORD` | MongoDB 비밀번호 | 랜덤 문자열 |
| `MONGO_PORT` | MongoDB 호스트 포트 | `27017` |
| `MONGO_VOLUME_PATH` | MongoDB 데이터 경로 | `/home/ubuntu/bcsd-data/mongo` |
| `SPICEDB_ENDPOINT` | SpiceDB gRPC 주소 | `spicedb:50051` |
| `SPICEDB_TOKEN` | SpiceDB 인증 토큰 | 랜덤 문자열 |
| `DOMAIN` | API 도메인 | `api.bcsdlab.com` |
| `N8N_DOMAIN` | n8n 도메인 (선택) | `n8n.bcsdlab.com` |
| `N8N_AUTH_USER` | n8n 기본 인증 사용자 | `admin` |
| `N8N_AUTH_PASSWORD` | n8n 기본 인증 비밀번호 | 랜덤 문자열 |
| `N8N_ENCRYPTION_KEY` | n8n credential 암호화 키 | 랜덤 문자열 |
| `SLACK_BOT_TOKEN` | Slack Bot 토큰 (공유) | `xoxb-...` |
| `SLACK_ERROR_CHANNEL` | API 에러 알림 채널 ID | `C0XXXXXXXXX` |
| `SLACK_CERTBOT_CHANNEL` | Certbot 갱신 알림 채널 ID | `C0YYYYYYYYY` |
| `SLACK_SERVER_NAME` | Certbot 메시지 prefix | `*[인터널]*` |

## 트러블슈팅

### 컨테이너 로그 확인

```bash
cd ~/BCSD_API
docker compose -f infra/docker/docker-compose.yml logs --tail=50 api-blue
docker compose -f infra/docker/docker-compose.yml logs --tail=50 api-green
```

### credentials.json FileNotFoundError

컨테이너 내부에 파일이 마운트되었는지 확인:

```bash
docker compose -f infra/docker/docker-compose.yml exec api-blue ls -la /app/credentials.json
```

프로젝트 루트에 `credentials.json`이 있는지 확인:

```bash
ls -la ~/BCSD_API/credentials.json
```

없으면 수동 복사:

```bash
cp ~/bcsdlab-credentials/bcsd-api/backend/* ~/BCSD_API/
```

### SSL 인증서 수동 갱신

```bash
docker compose -f infra/docker/docker-compose.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d api.bcsdlab.com \
  --email admin@bcsdlab.com \
  --agree-tos --no-eff-email
docker compose -f infra/docker/docker-compose.yml exec nginx nginx -s reload
```

### docker network "bcsd" not found

```bash
docker network create bcsd
```
