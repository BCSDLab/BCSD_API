# n8n Workflow 관리 규칙

## 원칙

- **n8n UI가 source of truth** — 실제 실행되는 워크플로우는 n8n 볼륨에 저장
- **이 디렉토리는 버전 관리용 백업** — Git에서 변경 이력 추적
- **배포 시 자동 import는 첫 배포만** — 이후에는 n8n 볼륨 상태 유지

## 워크플로우 수정 절차

1. **n8n UI**에서 워크플로우 수정 및 테스트
2. 동작 확인 후 **n8n UI에서 export** (Workflow → `...` → Download)
3. 다운받은 JSON으로 `workflows/*.json` 업데이트
4. **커밋 메시지**에 변경 내용 기록: `docs(workflow): {변경 내용}`

## Export 시 주의사항

- n8n export에 credential 데이터는 포함되지 않음 (ID만 포함)
- credential ID는 환경마다 다르므로 **커밋 전 ID를 빈 문자열로 교체**:
  ```json
  "credentials": {"postgres": {"id": "", "name": "BCSD PostgreSQL"}}
  ```
- 이렇게 해야 다른 환경에서 첫 배포 시 credential 수동 연결만 하면 됨

## 파일 목록

| 파일 | 워크플로우 ID | 설명 |
|------|--------------|------|
| `pg_sheets_sync.json` | `pg-sheets-sync` | PG → Google Sheets 동기화 (5분) |
| `link_auto_expire.json` | `link-auto-expire` | 만료 링크 자동 처리 (1분) |

## Credential 관리

- n8n 볼륨(`n8n-data`)에 암호화 저장, `N8N_ENCRYPTION_KEY`로 보호
- 첫 배포 시 n8n UI에서 수동 생성:
  - **BCSD PostgreSQL**: host=`postgres`, port=`5432`, .env의 DB 정보
  - **Google Sheets SA**: Service Account, bcsd-credentials의 SA JSON 사용
- 이후 배포에서는 볼륨에 보존되므로 재설정 불필요

## 볼륨 유실 시 복구

1. `n8n import:credentials` — bcsd-credentials에서 export한 파일로 복구
2. `n8n import:workflow` — 이 디렉토리의 JSON 파일로 복구
3. n8n UI에서 각 워크플로우의 credential 재연결
4. 워크플로우 Publish
