# Sync 독립 구현 검토 — 최초 차단 반례

검토자: live-kit-independent-sync-review. 이 검토자는 logger/UI를 구현했지만 service/sender는 작성하지 않았습니다. 실제 앱 훅·원격 전달·브라우저/390px 검증을 주장하지 않습니다. 서비스/sender/테스트/demo 소스는 수정하지 않았습니다.

## 최초 읽은 소스와 검증 경계

- live_service.py SHA256 `625db161d54b8fef3d9efb3550a7e9154ff6e31787060470ac346ee649357637`
- live_sender.py SHA256 `f6895cd9f827cb85f6ba2cbcecdb5165b8453e77fa6e6358ef6b04eefa26d619`
- demo_setup.py SHA256 `bad45bb23d0d4c4cf5acc8ba1c80a78a1be12512c6b9938f765a15dc0620d2ca`
- test_live.py SHA256 `80869ed3e87512b717240993f8e26c6c90c37564ac356e47dfa2977de3ee911b`

`python3 specs/ai-pms-live/test_live.py`는 샌드박스 bind 차단 후 승인된 제한 밖에서 실행했습니다. 이 시점 결과는 30개 중16fail+1error입니다. 주요 원인은 최신 sample 전체 source를 테스트 registry에 admission하지 않은 seed403, 서로 다른 dynamic module의 TransportError 클래스에 대한 assertRaises mismatch입니다. 이를 제품의 성공 증거로 사용하지 않습니다. 구현 담당자가 수정 중인 테스트와 별개로 아래 반례는 tempfile의 실제 private I/O, 실제 Sender.scan/tick 및 durable LiveStore.apply/read를 직접 실행했습니다. 네트워크 호출만 direct adapter로 대체했으므로 HTTP transport 실증과 구분합니다.

## 차단 결과 — 수정 전 역사적 상태

1. **P0 출처 context에 따른 native 이벤트 분리가 sender에서 소실됩니다.** `live_sender.py:58` hook entity가 event_id만 사용하고 `:81` known_events 역시 event_id 하나로 덮어씁니다. 같은 인증 writer의 허가된 서로 다른 native UUID에서 동일 event ID가 오면 첫 native context만 저장하고 두 번째를 native_id_conflict로 버립니다. 실제 두 줄 입력을 scan/tick한 결과 `native_contexts_stored=1`, 오류 `native_id_conflict`였습니다. actor/environment/native UUID/event ID를 함께 identity에 넣고 건강파일처럼 project 없는 ID가 여러 context와 일치하면 모호 상태를 명시해야 합니다.

2. **P0 건강파일 누락·손상이 중앙의 이전 정상 주장을 취소하지 않습니다.** `live_sender.py:106-117` 파일이 없으면 아무것도 송신하지 않고, 손상/읽기 실패/context 미연결이면 로컬 오류만 남깁니다. 정상 capture를 먼저 전달하고 건강파일을 삭제한 실제 실행에서 중앙 status는 `observed → observed`였습니다. 손상 JSON 이후도 observed 그대로이며 health_unavailable만 로컬에 남았습니다. 이전에 알고 있던 context를 durable하게 유지하고 누락·손상 때 동일 capture entity를 unknown/degraded로 갱신해야 합니다. 최근 정상 시각은 유지할 수 있지만 정상 status를 유지하면 안 됩니다.

3. **P0 실패 격리가 다른 entity의 전달까지 막습니다.** `live_sender.py:129-143` 큐 첫 항목이 conflict/quarantined면 즉시 break합니다. 서로 무관한 pending 항목은 계속 남습니다. 실제 durable queue `[conflict, unrelated pending]`에서 다음 tick의 unrelated request 수는0, 큐2건 그대로였습니다. 막힌 entity는 격리하되 그 entity에 종속되는 후속 revision은 보존하고 다른 entity는 계속 전달해야 합니다. 중앙 base revision conflict는 overwrite하면 안 됩니다.

4. **P1 제공되는 공동 프로젝트 demo가 초기 기준 hash 없이 충돌합니다.** `demo_setup.py:59`는 project base_revision1만 기록하고 `live_sender.py:45` hashes는 빈 값입니다. manager가 seeded revision1을 저장한 뒤 각 writer가 동일 project를 최초 변경처럼 재송신하여 첫 writer가 revision2로 올리고 다음 writer는 base1 conflict가 됩니다. 실제 setup 파일 생성→전체 manager seed→각 sender 실행에서 Alice/laptop과 Bob/bob-work가 각각 conflict1/pending1로 남았습니다. 서버에 실제 저장된 payload hash와 revision의 baseline을 함께 명시해야 하며 seed 성공 전 baseline을 사실로 취급하면 안 됩니다. seed 후 local 파일 변경은 초기 기준과 다른 payload로 송신해야 합니다.

5. **P1 demo seed의 redirect/ACK 경계가 약합니다.** `demo_setup.py:76`의 opener는 기본 redirect handler를 유지합니다. Authorization header는 redirected 요청으로 넘어갈 수 있어 localhost-only 초기 URL 검증만으로 외부 전달을 막지 못합니다. `:82`는 read 크기가 무제한이고 ACK의 event_id/cursor/정확한 필드를 검증하지 않습니다. 이는 코드 추론이며 공격 HTTP 서버를 실행한 증거는 아닙니다. sender의 NoRedirect·bounded read·정확한 ACK 검증을 재사용해야 합니다.

## 현재 보이는 안전 근거 — 코드 추론

서비스는 전체 state에 event receipt/revision/cursor를 저장한 뒤 ACK하며 append journal 대신 atomic replace와 fsync를 사용합니다. 읽기와 적용은 프로세스 lock+file lock으로 직렬화합니다. 같은 이벤트 ID의 payload 변경과 낡은 base를409로 거부합니다. cookie 로그인은 manager-only, HttpOnly/SameSite=Strict, TLS에서는 Secure이며 POST cookie 요청 Origin과 Host를 확인합니다. 익명 루트는 빈 shell만 제공합니다. source admission과 기존 peer documents/attempts/traceability/tasks/reviews/updates 보호가 있습니다. 입력 runner/observed/review 표시는 외부 인증 증명으로 승격하지 않는다는 계약/UI 경계를 유지합니다. key는 owner-only read 뒤 OpenSSL에 전달하며 외부 bind에는 TLS를 요구합니다. clock-driven projection 변경은 cursor/operations 변경을 내구 저장합니다.

이 안전 근거는 전체 구현 인수가 아니라 읽은 코드의 판단입니다. 최초 blocker는 수정 완료 후 새 코드 hash와 실행 반례를 대조하여 별도 재판정합니다.
