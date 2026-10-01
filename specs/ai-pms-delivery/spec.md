# 실환경 전달 — 승인 전 구현 준비 명세

정본: ../../PRODUCT-INTENT.md. 상태: **제안/승인 대기**. 새 API·전송기·수신 서비스 구현/실행, 글로벌 훅 설치, 외부 전송, 배포, 인증 키 발급은 아직 승인받지 않았다. 이 문서는 계약 제안이며 활성 API 계약 변경이 아니다.

## 현재 근거와 이번 작업

- 기존 `../ai-pms-central/central.py`: valid_event, source_key, import_sources, atomic_write, summarize, render. v1 JSONL을 actor/environment/project별로 격리하고 파일 가져오기/중앙 화면을 구현했다.
- 기존 `~/.claude/harness/activity/logger.py`: hook_event/record_event/base_event, 개인정보 allowlist, POSIX 파일 잠금. 훅은 로컬에만 기록하며 네트워크 전송은 없다. 기존 v1 이벤트 본문은 유지한다.
- 2026-10-01 부모 기준선: `python3 specs/ai-pms-central/verify_acceptance.py` exit 0 (2 tests OK). 실제 다중 사용자 전달=false, 제품 완료=false.
- 설치 버전 read-only 확인: codex-cli 0.159.2, Claude Code 2.1.243. 문서 지원과 현재 앱의 실제 이벤트 전달은 별개다. 설정 전체/실제 사용자 환경 인수는 미실행.
- 이번 허용 작업은 로컬 명세·독립 검토·샘플 없는 실행 준비 검사·현 앱 관측 절차다. 네트워크/설정/프로덕션 데이터를 건드리지 않는 `check_preparation.py`와 `runtime-inventory.json`, `RUNBOOK.md`, `APPROVAL.md`를 handoff로 작성한다. 검사는 준비 여부만 출력하고 실제 전달 성공으로 승격하지 않는다.

## 선택한 최소 구조 (구현은 승인 후)

앱의 동기 command hook → 기존 logger v1 로컬 JSONL → 별도 전송기 → 인증된 중앙 수신함 → 기존 중앙 import/render → 관리자가 연결 근거 확인. 훅에서 HTTP를 호출하지 않는다. 네트워크 장애가 앱의 도구 실행을 막지 않으며 원본 로그를 삭제/수정하지 않는다. DB·클라우드 큐·새 프레임워크 없이 작은 stdlib 프로세스와 소유자 전용 파일을 사용한다. 처음 구현 검증은 loopback만 사용하고 외부 HTTPS 목적지와 호스팅은 별도 승인한다.

### 사용자/환경 등록과 인증

관리자가 동의된 참여자마다 actor_id, 환경마다 environment_id를 등록하고 허용 project UUID와 안전한 표시 label을 지정한다. 환경별 독립 bearer credential은 서버의 등록 context에 묶인다. body의 actor/environment/label을 신뢰하지 않고 해당 필드를 받지 않는다. project UUID는 등록된 allowlist에 없으면 거부한다. 같은 UUID라도 actor/environment가 다르면 기존 중앙 규칙대로 분리하며, 동기화된 공동 프로젝트로 자동 합치지 않는다.

실제 사용자 신원 확인은 참여자 동의와 관리자 등록에 의존하는 파일럿이다. provider 계정 인증/조직 SSO를 구현했다고 표현하지 않는다. 공급자 tool source와 agent ID는 사용자 신원으로 재사용하지 않는다. 환경 자격은 ingest 전용이며 관리자 화면 조회/다른 환경 접근 권한이 아니다. 서버 token digest와 로컬 자격 파일은 소유자 전용; 토큰 원문/Authorization은 로그·보고서·URL·argv·예제에 남기지 않는다. 실제 비밀 생성/저장은 별도 명시 승인 후 한다. 이번 준비물에는 키가 없다.

### 제안 수신 계약

`POST /v1/events`, UTF-8 application/json, Authorization bearer. 문서상의 제안일 뿐 아직 route나 서버를 만들지 않는다.

요청의 정확한 필드: `protocol_version`(정수 1), `batch_id`(canonical UUID), `project_id`(등록 UUID), `events`(기존 v1 JSON object 배열). 한 배치는 한 프로젝트. 최대 100개 이벤트/요청 body 1 MiB/이벤트 65,536 bytes. events=[]는 등록된 환경의 연결 확인용이며 목표나 최근 작업 시각을 새로 만들어내지 않는다. body에 경로·프롬프트·명령·transcript·키·외부 URL·actor/environment/표시 label을 추가하지 않는다. JSON duplicate key/nonfinite 값/32단계 초과 nesting을 거부하고 정확한 v1 계약과 개인정보 allowlist를 송신/수신 양쪽에서 검사한다. 정규식은 알려진 일부 비밀 패턴만 차단하며 완전한 익명화 보장은 아니다.

응답의 필드: protocol_version, batch_id, payload_sha256(수신한 요청 body의 SHA-256), actor_id, environment_id(인증으로 정한 context), event_ids(요청에 담긴 ID 전부), status=`durable_inbox`, received_at. 입력 순서 그대로 event_ids를 돌려준다. 승인 뒤 실제 테스트용 dummy 자격은 런타임 임시 폴더에서만 만들고 실제 자격과 구분한다.

인증/등록 검사를 먼저 하고 malformed/unknown field/버전/project 불일치를 전량 거부한다. 단일 배치 안 중복 event_id도 거부한다. batch_id 범위는 인증 environment+project이며 동일 batch_id·동일 body 재시도는 최초 영수증을 반환한다. 동일 batch_id·다른 body는 409 conflict, 원본을 덮지 않는다. 401은 자격 불인정, 403은 등록/프로젝트 권한 실패, 400은 계약/형식 실패, 413은 크기 한도, 409는 배치 ID 내용 충돌, 429는 용량/요청 제한, 503은 저장 실패/임시 불가다. 오류에는 원문/개인 경로/토큰을 포함하지 않는다.

### durable ACK, 재시도, 집계의 경계

서버는 **검증한 v1 이벤트와 배치 해시·인증 context·최초 수신 시각·반환 영수증을 한 immutable inbox 파일**에 소유자 전용으로 원자 기록하고 파일/디렉터리 fsync가 성공한 뒤에만 ACK한다. 환경/project/batch별 저장 이름은 안전한 해시/UUID로 결정하고 잠금으로 동일 배치 경쟁을 막는다. 인증을 재검사한 후 기존 영수증을 재사용한다. ACK 응답 분실/송신기 재시작은 같은 영속 batch_id와 바이트로 재시도하므로 원본을 잃지 않는다. ACK는 중앙 수신함 영속 기록 성공만 뜻하며 집계/관리 화면 반영 완료를 뜻하지 않는다.

집계 작업은 inbox의 검증된 body를 v1 JSONL mirror로 변환하고 서버 등록으로 만든 manifest를 기존 import_sources에 전달한다. 사용자 actor/environment 입력 manifest를 서버 인증 우회 경로로 사용하지 않는다. inbox는 집계 실패에도 보존되며 재시도한다. 기존 중앙 저장은 읽기/쓰기 한도를 유지하고 같은 event_id·다른 본문 충돌을 원본 덮기 없이 관리 항목으로 남긴다. 배치 간 event_id 충돌은 수신함 ACK 후 집계 단계에서 드러날 수 있다; 이때 durable ACK를 정상 연결/업무 완료로 표현하지 않는다. 파일럿에서 자동 삭제/retention 작업은 하지 않는다.

집계 상태는 중앙 이벤트 저장과 독립적인 owner-only `delivery-state.json`에 잠금/원자 기록한다. 정확한 필드는 version=1, registered_contexts(서버 등록 actor_id/environment_id/project_id/label), batches(서버 context 키+batch_id+payload_sha256+received_at+event_count+state+reason_code+updated_at)이며 state는 queued/aggregated/conflict/failed, reason_code는 안전한 오류 enum이다. 원문 메시지·경로·키는 받지 않는다. immutable inbox에 있는 배치의 상태가 없으면 queued로 계산한다. 중앙 import 저장 성공과 해당 이벤트 본문 hash 대조가 모두 끝난 뒤에만 aggregated를 기록한다. crash로 상태 갱신이 빠져도 재집계/대조로 복구하며 conflict/failed는 inbox를 보존한다. 중앙 파일 cap/오류에서도 독립 상태 기록과 화면 렌더는 가능해야 한다. 상태 파일의 크기 상한은 8 MiB, cap/손상/읽기 실패는 상태 불명 관리 항목이며 성공 기본값이 아니다.

기존 render에 선택적 로컬 `--delivery-state` 입력을 승인 A에서 추가한다. 서버 등록 context만 기존 프로젝트 목록에 결합하고 이벤트 없는 등록 환경도 관측 없음으로 표시한다. 마지막 연결 확인은 inbox.received_at, 최근 작업은 실제 event.observed_at만 사용한다. 상태 입력이 없으면 기존 offline 화면 동작을 유지한다. 관리자 GET API는 만들지 않는다. metadata만 바뀌어도 HTML을 다시 만들며 중앙 import 실패가 화면 갱신을 막지 않는다. 이 통합 역시 승인 후 구현·브라우저 인수 대상이다.

중앙 관리자에는 환경의 마지막 연결 확인, 최근 event.observed_at, 수신함 대기 배치/집계 오류/충돌을 분리 표시한다. 연결 확인만으로 최근 작업을 갱신하지 않는다. 새 envelope metadata는 v1 이벤트 본문 바깥에 둔다. mirror 파일 SHA/행 번호는 **서버가 생성한 수신 배치 근거**이며 생산자 원본 파일을 검증한 해시라고 표현하지 않는다. 원본 v1 이벤트의 authority/occurred_at:null과 Agent 후보/모호함을 보존한다. 관리자 열람은 파일럿 중앙 호스트의 로컬 소유자에게만 제공한다; ingest 자격으로 공개 HTML을 내려받을 수 없다. 공개 관리자 웹 화면은 별도 인증·배포 승인 전 제공하지 않는다.

### 전송기와 장애 처리

전송기는 설정에 명시된 log directory/허용 project UUID만 읽는다. transcript나 project-index/private source path를 전송하지 않는다. 기존 logger를 변경하지 않는다. 100개/1 MiB 두 한도를 모두 만족하도록 직렬화 크기를 계산해 배치를 분할한다. enqueue 전 용량을 검사하고 단일 sender 실행 잠금을 잡는다. 소유자 전용 outbox에 batch_id와 전송 바이트를 원자 기록하고 파일/부모 디렉터리 fsync가 끝난 뒤 전송한다. ACK된 이벤트 identity+canonical body hash를 기록해 작은 파일럿에서는 로그를 재스캔한다(단순 O(n) 방식; 로그량 증가 시 측정 후 offset index 도입). 미완성 마지막 줄은 대기하고 완성된 잘못된 줄은 원문 없이 숫자/행 번호만 오류로 남긴다. 바뀐 event_id 본문은 신규 배치로도 무시/성공 처리하지 않는다.

기본 주기 2초, 요청 timeout 10초, 네트워크/429/5xx는 1→2→4→8→16→30초 상한 backoff+jitter; Retry-After는 파싱/상한 제한해 반영한다. 영속 batch/ACK 확인 없는 자동 버림은 없다. 400/401/403/409/413은 해당 배치의 blocked 상태와 메타데이터를 남기고 ACK/체크포인트를 진행시키지 않는다. 수동 수정/재등록 전 오류 상태를 성공으로 바꾸지 않는다. 응답의 exact fields/types, protocol_version 정수 1, status=durable_inbox, 유효 UTC received_at, 배치/해시/context/순서 포함 ID 전체가 대조되지 않으면 ACK로 인정하지 않는다. outbox와 inbox 각각 64 MiB 파일럿 한도, 중앙 저장도 기존 64 MiB; cap에서는 읽고 보내기를 무한 누적하지 않고 명시 backpressure/관리 항목을 남긴다. 원본 로그는 자동으로 지우지 않는다.

원격 목적지는 HTTPS이며 TLS 검증을 유지한다. redirect는 따라가지 않고 Authorization을 다른 호스트로 보내지 않는다. localhost HTTP는 명시 loopback 테스트 모드에서만(127.0.0.1 또는 ::1), 기본 수신 bind는 loopback. DNS나 실제 호스트/키가 없으면 외부 전송은 비활성이다. 서비스 autostart/방화벽/터널/공개 포트는 별도 승인 전 만들지 않는다.

## 승인 뒤 실행할 구현 패킷과 인수

승인 범위 A는 로컬 sender/receiver/inbox 집계 및 제안 API 계약의 구현과 loopback 통합 테스트다. 기존 central.py의 공통 validator/import/render를 재사용하되 새 파일/편집점/반례 테스트를 새 handoff 계획으로 발행한다. 기존 테스트 삭제/skip 금지. 글로벌 hook/trust/실제 자격/외부 전달/배포는 A에 포함하지 않는다. 기존 UI 증거에 해당하는 생성기 해시가 바뀌면 재생성 및 전체 중앙 흐름 부모 브라우저 인수를 반복한다.

승인 범위 B는 목적지 HTTPS URL/관리 호스트, 참여자와 환경별 자격/프로젝트 등록, 실제 앱 훅 설치·trust 및 데이터 보관/열람 범위를 정한 이후 별도 요청한다. 두 CLI를 같은 사용자 컴퓨터에서 돌려도 서로 다른 실제 사용자의 전달 인수로 표현하지 않는다.

실제 인수는 두 동의된 사용자/환경에서 앱 안의 도구를 실행해 얻은 source/session/tool_call/event ID → logger → sender outbox → 인증 수신함 영수증 → 중앙 집계 → 관리 화면 원본의 event ID와 본문 hash를 대조한다. 핵심 반례: 한 환경의 다른 actor/project 위조, ACK 분실 후 재시도/재시작, endpoint 오프라인 후 회복, 저장 실패, 잘못된 status/protocol/시각을 포함한 wrong ACK, 크기별 배치 분할/경쟁 sender, 손상된 delivery metadata, import 성공 후 상태 기록 전 crash, 같은 batch ID 다른 body, 다른 배치 같은 event ID 충돌, heartbeat만 도착, 집계 저장 한도와 입력 누락, 목표/Phase 없는 작업, 산출물 버전 불일치. 실환경 event evidence와 합성 loopback 테스트는 별도 영수증으로 남긴다.

## 이번 준비 패킷의 합격 기준

`python3 specs/ai-pms-delivery/check_preparation.py --selftest`와 `python3 specs/ai-pms-delivery/check_preparation.py`가 실행된다. 부모의 최종 verify_preparation.py는 원문/명세 독립 검토 해시, 준비물 파일 해시, 로컬 검사 결과와 API 승인/실제 전달=false를 확인한다. 이는 구현/전송 성공 관문이 아니라 승인 요청 준비 관문이다. 초기 selftest 명령은 구현 전 파일 없음 exit 2로 확인한다. 실제 승인 기록 없이 endpoint/secret이나 승인 플래그를 만들어내지 않는다.

실제 목적지와 두 참여자의 동의는 아직 없으며 배포 결정을 위임하지 않는다. 준비 명세 자체는 목적 정렬 검토를 받은 뒤 고정한다. 실환경 단계에서는 사용자 지정 운영정보와 승인 후 명세를 확정하고 재검토한다.
