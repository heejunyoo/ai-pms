# 사람·세션·북극성 Live PMS

이 패키지는 로컬 logger → 명시적인 sender → 자체 호스팅 중앙 service → same-origin dashboard의 증분 갱신을 위한 실행 자료입니다. 공개 예시는 합성이며 공개 정적 사이트를 영속 수신기로 주장하지 않습니다. 실제 앱 hook·원격 두 환경·운영 브라우저 증명은 별도이며 미검증입니다.

[처음 다운로드한 사용자의 전체 도입 순서](../../docs/adoption.md)를 먼저 확인하세요. 모든 명령은 README.md가 있는 **GitHub 저장소 최상위 폴더**에서 실행합니다. Python 3.11+와 Node.js가 필요합니다. Harness Kit의 PMS 배포 범위는 훅 수집이며 중앙 runtime는 이 저장소에서 실행합니다. Kit ZIP의 `pms/` 경로는 사용하지 않습니다.

## 1. 로컬 수집 상태

`kit/activity/logger.py`, `kit/activity/connectivity.py`를 함께 설치합니다. 기존 hook 설정과 안전 검사를 보존한 뒤 지원되는 Codex/Claude command hook에 logger 명령을 직접 병합합니다. 전역 설정과 trust는 자동 변경하지 않습니다. Codex `/hooks` 리뷰·trust는 사용자가 승인합니다. Cursor/Gemini hook는 미지원입니다.

```sh
python3 kit/activity/logger.py health --log-dir "$PMS_LOG_DIR"
python3 kit/activity/test_logger.py
```

`PMS_LOG_DIR`은 운영자가 정한 로컬 로그 디렉터리입니다. 건강 JSON의 정확한 필드는 `{version:1,last_event_id,last_recorded_at,errors,last_failure_at,status,at}`입니다. `capture-health.json`은 logdir writer 전체의 마지막 fsync 완료 기록이며 프로젝트별 heartbeat가 아닙니다. 여러 프로젝트가 같은 logdir를 쓰면 한 프로젝트의 성공을 다른 프로젝트의 건강 증거로 읽지 마세요. sender identity 부착은 명시적인 출처 연결이며 실제 앱별 훅 커버리지를 보증하지 않습니다. 마지막 기록60초 초과는 stale일 수 있지만 미사용 중일 수도 있어 실패로 단정하지 않습니다.

파일 없음·손상·읽기 실패는 unknown, 실제 오류 기록은 degraded입니다. 마지막 정상 ID/시각은 실패 후 보존합니다. 기록 성공 후 건강 저장만 실패하면 안전 stderr가 두 결과를 구별합니다. 건강 원본 손상과 symlink는 보존하며 정상으로 덮지 않습니다. Codex Stop/SubagentStop은 실패에도 exit0과 JSON `{}`를 반환하고 stderr 실패 표시는 유지합니다. 첫 malformed stdin만 있으면 정상 관측이 없어 건강파일이 missing/unknown일 수 있습니다.

## 2. 중앙 서비스와 sender 준비

`live_service.py`, `live_sender.py`, `portfolio.py`, `operations.py`, `management.py`, `work.py`와 기존 transport common/receiver 의존 파일을 상대 위치를 유지하여 함께 배치합니다. `catalog-work.template.json`과 `operations.template.json`에서 실사용 source identity, session 목표, task ID와 revision을 검토합니다. goal acceptance는 선언이며 현재 검증과 목표 정의에 묶어야 합니다. 북극성 실측과 기여 연결을 분리하고 개인 프로젝트에 회사 연결을 강제하지 않습니다.

owner-only registry에 writer의 actor/environment/native project UUID/token SHA256 및 별도 manager 자격을 등록합니다. token 원문은 owner-only credential 파일로 관리하고 URL·로그·공개 예시·localStorage에 두지 않습니다. 서비스는 loopback 기본이며 외부 bind에는 TLS cert/key가 필요합니다. sender는 HTTPS 원격 또는 명시적 loopback-test HTTP만 사용합니다. 실제 목적지와 자격을 운영자가 정하고 sender를 opt-in합니다.

합성 로컬 파일럿은 다음 순서로 실행합니다. 프로젝트 루트(공개 GitHub 체크아웃 또는 Download ZIP 압축 해제 루트)에서 시작합니다. `PMS_RUN_DIR`은 아직 비어 있는 실제 경로를 선택합니다. macOS의 `/tmp`·`/var` 별칭 대신 실제 경로를 사용합니다.

```sh
PMS_RUN_DIR="$HOME/pms-local-pilot"
python3 specs/ai-pms-live/demo_setup.py --directory "$PMS_RUN_DIR"
python3 specs/ai-pms-live/live_service.py --data-dir "$PMS_RUN_DIR/central" --registry "$PMS_RUN_DIR/registry.json" --port 8765 --synthetic-demo
```

서비스를 유지한 채 두 번째 터미널에서 최초 seed 후 sender를 시작합니다. 준비된 7개 writer 중 아래는 서로 다른 두 사용자의 예시입니다. 다른 writer도 각자의 `sender.json`으로 실행할 수 있습니다.

```sh
PMS_RUN_DIR="$HOME/pms-local-pilot"
python3 specs/ai-pms-live/demo_setup.py --directory "$PMS_RUN_DIR" --seed
python3 specs/ai-pms-live/live_sender.py --config "$PMS_RUN_DIR/Alice-laptop/sender.json" --watch
```

다른 터미널에서 Bob의 `Bob-bob-work/sender.json`을 사용합니다. `http://127.0.0.1:8765/`에서 관리자 로그인 후 확인합니다. 관리자 자격은 자신의 private `manager.credential`에 있으며 서버나 명령은 원문을 출력하지 않습니다. 이 파일럿은 합성 자료이고 실제 앱 hook를 설치하지 않습니다. 샘플 JSONL은 과거 관측이며 건강파일이 없어 수집 상태는 unknown으로 시작합니다.

writer 설정의 필수 키는 `{version:1,url,actor_id,environment_id,project_ids,token_file,logdir,catalog,operations,outbox,loopback_test}`입니다.

| 설정 | 의미 |
|---|---|
| `url` | 서비스 base URL |
| `project_ids` | native UUID 배열 |
| 파일·디렉터리 경로 | owner-only 로컬 파일·디렉터리. `catalog`·`operations`는 null 허용 |
| 선택 `role` | writer가 기본값이며 manager도 사용 가능 |
| 선택 `base_revisions` | kind:id → 정수 |
| 선택 `base_hashes` | kind:id → SHA256 |

manager가 실제 seed한 payload의 기준 revision과 hash를 bootstrap에 함께 사용합니다. 변경된 내용을 같다고 취급하거나 충돌을 덮어쓰는 옵션이 아닙니다.

writer를 시작하기 전에 seed를 완료하세요. 한 outbox는 한 인증 context와 한 서비스에만 사용합니다. 대상이나 identity를 바꾸면 새 outbox를 사용합니다.

실사용에서는 합성 registry를 재사용하지 않습니다. 운영자가 writer별 허가 project UUID와 별도 manager를 등록하고 HTTPS 서비스·private token_file을 연결합니다. service는 `--data-dir`, `--registry`, 선택 `--host`, `--port`, `--tls-cert`, `--tls-key`를 받습니다. 외부 bind에는 TLS가 필수이며 인증서 hostname에 맞는 공개 host로 bind해야 합니다. 현재 reverse proxy host 재작성 및 IPv6 외부 운영은 인수하지 않았습니다. 운영 배포와 실제 참여자 동의/보관 범위는 별도로 결정합니다.

## 2-1. 세션 목표와 인수 기록

훅만으로 목적을 추론하지 않습니다. Handoff 계획을 v3 catalog로 가져온 뒤 현재 세션 ID·native 프로젝트 UUID·담당 작업 ID를 명시적으로 연결합니다. 해당 private 파일은 sender가 변경을 감지해 개별 record로 전달합니다.

```sh
python3 specs/ai-pms-live/session_goal.py --catalog "$PMS_CATALOG" --operations "$PMS_OPERATIONS" bind --project-id "$PMS_PROJECT" --source-project-id "$PMS_NATIVE_UUID" --actor-id "$PMS_ACTOR" --environment-id "$PMS_ENVIRONMENT" --source codex --session-id "$PMS_SESSION" --goal-version goal-v1 --task-id "$PMS_TASK"
python3 specs/ai-pms-live/session_goal.py --catalog "$PMS_CATALOG" --operations "$PMS_OPERATIONS" decide --session-record-id "$PMS_SESSION_RECORD" --actor-id "$PMS_ACTOR" --decision accepted
```

각 변수는 검토한 실제 catalog/session의 값입니다. goal을 생략하면 현재 프로젝트 목표를 사용합니다. 최신 연결 작업의 검증이 충족되지 않으면 accepted를 거부합니다. 인수는 현재 목표·검증 정의의 해시에 묶이며 정의가 바뀌면 재인수가 필요합니다. 로컬 actor 문자열은 인간 신원 인증이 아니며 중앙 writer 인증으로 소유권을 검사합니다. 훅의 Stop는 턴 종료이고, SessionEnd의 종료와 목표 충족/인수도 서로 다릅니다.

sender는 초기 catalog와 operations를 entity별로 감시하고 hook JSONL을 context-filter하여 내구 outbox로 보냅니다. `--once`는 한 주기, `--watch`는 지속 감시입니다. 송신 실패는 outbox를 보존하며 재시작 후 재전송합니다. 서버 ACK는 영속 저장/투영 완료 뒤에만 반영합니다. 오래된 base revision은 conflict이고 조용히 overwrite하지 않습니다. entity 삭제는 미지원이며 unsupported/conflict를 확인해야 합니다. 브라우저 로그인은 manager 자격 POST→HttpOnly/SameSite cookie이며 토큰 입력은 메모리에서 지웁니다. 정적 기본 화면은 네트워크 요청하지 않고 live 모드만2초 polling합니다.

## 3. 검증과 실제 앱 확인

연구 체크아웃에서 `python3 specs/ai-pms-live/verify_live.py`를 실행합니다. `test_kit_live.py`는 export된 `kit/activity/logger.py`가 있으면 이를 우선 검사하고, 연구 체크아웃만 존재하면 홈의 정본 logger를 검사합니다. health·손상·symlink·경합·privacy·Codex stdout 반례는 `test_kit_live.py`로 재현합니다. legacy logger/workflow 검사를 보존합니다.

실제 사용 전 앱에서 선택 hook을 발생시킨 뒤 해당 event ID가 로컬 JSONL과 건강파일에 있는지, sender ACK가 있는지, 중앙 changes와 화면에서 같은 source/session 목표에 연결되는지 확인합니다. Stop만으로 목표 인수를 주장하지 않습니다. 로컬 synthetic HTTP 검사는 실제 원격 두 사용자 전달이나 전역 앱 설치 증명이 아닙니다. 공개 export에는 합성 기록만 넣습니다.

## 4. 증분 계약과 저장 한도

`POST /api/records`는 `{version:1,event_id,kind,base_revision,payload}`를 받습니다. kind는 hook/project/session/north_star/contribution/capture이며 레코드 하나씩 전송합니다. hook payload는 `{actor_id,environment_id,event}`이고 나머지는 해당 entity 전체의 작은 변경 단위입니다. 거대한 전체 snapshot 전송이나 field-level JSON patch 방식이 아닙니다. ACK는 `{event_id,cursor,entity_revision,status:"applied"}`이고 영속 저장이 끝나야 반환합니다. 같은 context·ID·본문은 중복 처리하고 다른 본문은409입니다. 서로 다른 사용자/환경/native UUID는 격리합니다. 동일 native UUID의 서로 다른 provider가 같은 native event ID로 다른 본문을 보내면409로 보존하며 자동 병합하지 않습니다.

관리자는 인증된 `GET /api/changes?after=N`에서 `{cursor,reset,project_updates,operations,generated_at}`를 받아 화면을 갱신합니다. `project_updates`는 변경 프로젝트이고 `operations`는 변경 시 최신 투영, 변경이 없으면 null입니다. source가 미매핑에서 매핑으로 바뀌거나 cursor 보관 범위를 벗어나면 reset으로 안전하게 재동기화합니다. `GET /api/history?after=N`은 영속 영수증의 원래 목표·계획·검사·인수 payload를 최대100개 반환하고 next_after로 이어집니다. latest projection으로 과거 판단을 덮어쓰지 않습니다.

표준 라이브러리 기반 단일 서비스 파일 저장 pilot입니다. 상태64MiB·영수증10,000개·증분 이력200건 한도에서 조용히 삭제하지 않고 저장을 거부합니다. 규모가 커지면 transactional DB와 보관 정책이 필요합니다. 부하/운영 SLA 증명은 없습니다. sender는2초 감시하고 브라우저는2초 조회합니다. 7개 합성 writer 전체 통합과 logger CLI→중앙 갱신을 검사했으며 실제 원격 latency로 해석하지 않습니다.
