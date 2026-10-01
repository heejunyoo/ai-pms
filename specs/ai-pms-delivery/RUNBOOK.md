# 실제 앱 전달 인수 절차 — 실행 전 준비

상태: **미실행**. `check_preparation.py`는 고정된 로컬 설정 8개에서 알려진 logger 경로와 `hook` 토큰을 가진 **후보 선언**만 셉니다. shell 의미를 실행·해석하지 않아 echo/comment의 오탐이나 custom wrapper의 미탐이 가능하며 활성 증거가 아닙니다. 플러그인·managed 설정·다른 계층, hook trust/실제 활성화, 앱 이벤트, 전송, 중앙 수신 여부는 검사하지 않습니다. `runtime-inventory.json`의 선언 수는 전달 성공 증거가 아닙니다. 새 API 구현과 실제 송신·배포·훅·비밀 작업은 [APPROVAL.md](APPROVAL.md)의 별도 승인 범위입니다.

## 승인 후 관측 순서

1. **참여자와 출처를 확정합니다.** 동의한 서로 다른 두 실제 사용자와 각 앱 환경에 관리자 등록 actor_id/environment_id를 따로 부여하고 허용 project UUID·label을 기록합니다. 같은 컴퓨터의 두 임시 로그 디렉터리는 이 조건을 충족하지 않습니다. 관리자 열람 권한과 보관 범위를 먼저 정합니다. goal/summary 자유 텍스트에는 정규식이 잡지 못한 민감정보가 남을 수 있으므로 동의 범위에 맞게 별도 검토합니다. 증거 문서에는 실제 토큰·개인 경로·프롬프트·명령 원문을 넣지 않습니다.
2. **실제 앱 안에서 훅을 확인합니다.** 각 사용자의 Codex 또는 Claude Code에서 해당 프로젝트의 유효 설정과 trust 상태를 확인한 뒤 지원되는 로컬 도구 실행을 한 번 관측합니다. Codex hosted tool 예외와 Claude PostToolUse/PostToolUseFailure 차이를 구분합니다. 설정의 logger 명령 선언만으로 통과시키지 않습니다. 앱에서 새로 생성된 로컬 v1 이벤트의 `source`, `project_id`, `session_id`, `tool_call_id`, `event_id`, `observed_at`, `missing_fields`를 원본과 대조합니다. native `occurred_at`이나 agent ID가 없으면 null/누락으로 보존합니다.
3. **로컬 원본과 송신 대기를 대조합니다.** 승인된 전송기가 허용 JSONL만 읽었는지 확인하고, 각 이벤트의 `(actor_id, environment_id, project_id, event_id)`와 canonical v1 본문 SHA-256을 기록합니다. outbox의 batch_id·요청 body SHA-256·event ID 목록을 원본과 대조합니다. 원본 로그를 지우거나 누락된 이벤트를 성공으로 처리하지 않습니다.
4. **인증 수신함까지 대조합니다.** 환경별 등록 자격으로만 수신됐는지, outbox/inbox의 등록 project 귀속을 확인합니다. 수신 영수증의 `protocol_version` 정수 1, batch_id·payload_sha256·인증에서 정한 actor/environment·순서 있는 event_ids·`durable_inbox`·최초 received_at을 outbox와 대조합니다. 영수증은 영속 수신함 기록 증거이며 집계 완료가 아닙니다. 원본 토큰이나 Authorization 값은 증거에 남기지 않습니다.
5. **중앙 화면의 원본으로 내려갑니다.** 해당 batch의 집계 상태가 `aggregated`인지, 중앙 저장의 출처 키와 모든 event ID·본문 hash가 원본과 일치하는지 확인합니다. 관리자 목록에서 두 프로젝트의 목표·Phase·최근 변경·Agent·산출물·검사와 관리 항목을 비교하고, 프로젝트 → 관계 목록 → 원본 이벤트를 엽니다. 입력 파일 해시/행 번호는 서버 mirror의 근거로만 표기하고 사용자 로컬 원본 파일 해시라고 부르지 않습니다. 목표/Phase 선언이 없으면 누락으로 보여야 합니다.
6. **두 종류의 증거를 따로 남깁니다.** 합성 loopback 검사 영수증과 실제 두 사용자 앱 실행 영수증을 분리합니다. 실환경 영수증에는 동의된 참여자/환경 alias, 앱·도구 이벤트 종류, 각 단계의 event ID/본문 hash/배치 ID/수신·집계 상태, 화면 관측 시각과 원본 링크를 남깁니다. 민감한 원본은 소유자 전용 저장소에만 보관합니다. 두 사용자 경로와 부모의 화면 인수 전에는 `actual_delivery_verified=false`, `product_complete=false`를 유지합니다.

## 실패 판정

- 훅 선언은 있는데 실제 앱 이벤트가 없거나 trust가 확인되지 않으면 **전달 미검증**입니다. actor/environment/project 귀속이 틀리거나 서로 합쳐지면 실패입니다.
- outbox 영속 기록 전 송신, ACK 분실 뒤 같은 batch 재시도 실패, 틀린 ACK 필드·해시·ID 순서·시각·status 수락, 자격/프로젝트 위조 허용은 실패입니다. 오프라인·429/5xx·저장 실패·용량 한도에서는 원본과 재시도 가능 상태를 보존해야 합니다.
- 수신함 ACK만 있고 중앙 집계가 대기·오류·충돌이면 완료가 아닙니다. batch_id는 같고 본문이 다르거나, 다른 batch의 같은 event_id 본문이 다르면 원본을 덮지 않고 충돌을 보입니다. import 성공 뒤 상태 기록 전 중단, 손상된 delivery metadata, heartbeat만 도착한 경우도 정상 진행으로 표시하지 않습니다.
- 목표/Phase 부재, baseline 버전 미연결 결정, 산출물 버전 불일치 검사·인수, 미래·오래된 `observed_at`이 화면에서 정상 완료로 보이면 실패입니다. 도구 성공·Stop·검사 통과를 사용자 인수로 바꾸지 않습니다.

이 절차는 [spec.md](spec.md)의 제안 계약을 기준으로 한 인수 계획입니다. 현재 API·전송기·수신함·실환경 증거는 없습니다.
