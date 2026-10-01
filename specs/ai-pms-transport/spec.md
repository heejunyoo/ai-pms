# 승인 A: 로컬 자동 전달 구현

정본 `../../PRODUCT-INTENT.md`. 사용자 승인 원문/범위는 `approval.json`. 앞 단계 `../ai-pms-delivery/spec.md`의 전송/인증/ACK/개인정보 계약을 승인 A에 한해 구현한다. 준비 단계 파일은 역사 증거로 보존한다. 실제 전달=false, 제품 완료=false이며 합성 loopback 자동 전달만 인수한다.

## 부모가 정한 경계와 재사용

기존 `../ai-pms-central/central.py`의 valid_event, uid, identifier, timestamp, canonical, source_key, import_sources, load_store, summarize, render를 재사용한다. logger v1와 기존 test_central.py는 변경하지 않는다. 현재 준비 gate exit0, 기존 중앙 검사는 이전 turn exit0. central 변경 뒤 과거 준비 gate의 protected hash 불일치는 예상되며 새 transport 관문이 현재 정본이다. 기존 인수 자료는 재작성하지 않고 새 렌더/브라우저 근거를 이 폴더에 보관한다.

A의 CLI는 명시 `--loopback-test`와 literal 127.0.0.1/::1만 허용한다. 실제 외부 HTTPS 연결/운영은 B 승인 뒤 구현·검증한다. 포트는 OS 할당(0) 또는 명시 로컬 포트, 공개 binding/서비스 설치 없음. 합성 credential은 테스트 실행 임시0700 폴더에서만 생성해0600 파일에 보관하고 출력하지 않는다. 영구 샘플·영수증·HTML에는 자격 digest도 포함하지 않는다.

## 공통 내부 계약 (T1이 소유, 뒤 태스크 read-only)

`common.py`는 stdlib만 사용하며 sibling central 모듈을 경로로 import한다. 공개 심볼: `central`, `TransportError(code,status)`, `strict_json(raw, limit=1048576)`, `encode(value)`(UTF8, sort_keys, compact, allow_nan=False), `digest(raw)`(sha256 hex), `now()`(UTC ISO), `read_private(path, limit)`(bounded regular owner-only no symlink/hardlink), `write_private(path, raw)`(atomic file+parent fsync), `private_dir(path)`, `locked(root, name, blocking=True)` contextmanager, `validate_batch(raw)` -> parsed request, `validate_ack(value,batch,raw,actor_id,environment_id)` -> raises or returns None. strict_json은 duplicate key/nonfinite/nesting>32 거부、타입 오류는 safe enum error. Python bool은 protocol/count int가 아니다. MAX_BODY=1MiB, MAX_EVENT=65536, MAX_EVENTS=100, MAX_QUEUE=64MiB, MAX_STATE=8MiB.

한 요청은 exact protocol_version=1,batch_id UUID,project_id UUID,events[]; 이벤트는 기존 v1 validator 통과 및 canonical size<=MAX_EVENT. 동일배치 event_id중복 금지. ACK exact protocol_version,batch_id,payload_sha256,actor_id,environment_id,event_ids,status,received_at. 원바이트 hash/순서전체 ID/context/status durable_inbox/정수1/UTC시각 검사. 응답/오류/로그에는 입력원문/경로/자격을 넣지 않는다. malformed tool_name(리스트 등)도 안전거부한다.

## T1: 인증 수신 → 영속 inbox → 집계

`receiver.py` registry 파일 exact {version:1,environments:[{actor_id,environment_id,token_sha256,projects:[{project_id,label}]}]}. 최대100개 등록 context, actor/environment identifier, project UUID, 안전label<=80, unique actor/environment와 unique token digest. credential은 서버 context에 묶고 request actor/env/label 필드는 금지. registry는 owner-only regular파일; 요청마다 재검사하여 제거된 자격도 replay불가. 인증은 constant time digest대조. 등록되지않은 project403, malformed400, 자격401, body limit413, batch body conflict409, 용량429, 저장503. unknownroute404/GET405로 관리자HTML 노출 없음. http.server는 loopback 파일럿 전용, request timeout10s, bounded Content-Length 필수, duplicate/smuggled Content-Length/Transfer-Encoding/contenttype 거부, safe JSON error만 출력, HTTP access log 비활성.

`make_server(registry_path, root, host='127.0.0.1', port=0)` 반환HTTPServer, `receive(raw, bearer, registry_path, root)` 반환 ACK, `aggregate(registry_path, root, store)` 반환 delivery-state dict. CLI `serve --registry FILE --root DIR --host 127.0.0.1 --port N --loopback-test`, `aggregate --registry FILE --root DIR --store DIR`. 서버프로세스는 SIGTERM/KeyboardInterrupt 정리 가능. serve 출력은 실제 local port만.

단일 root lock 아래 요청원문 JSON bytes(UTF8 text), parsed batch, context, receipt를 immutable inbox/{sha256(context+batchid)}.json에 기록한 뒤 ACK. 원파일/디렉터리 fsync성공이 필수, 기존 동일body replay시도도 fsync재확인해 이전 directory fsync실패를 성공으로 우회하지 않는다. inbox64MiB cap은 쓰기전 projected size계산(교체temp overhead정책 명시). 영수증은 inbox영속만, HTTP에서 집계하지 않는다.

aggregate는 inbox batch를 매번 제한된 pilot O(n) 재검사, 최초 수신시간순으로 central에 전달한다. server registry로 만든 manifest만 사용하고 mirror는 root/mirrors에서 결정적 생성한다. immutable 받은 context+현재registry가 불일치하면 failed registration_changed로 보존한다. mirror는 한배치<=100개라 central MAX_FILE보다 작다. manifest 파일은 상대mirrorpath+synthetic evidence_mode. central.json fsync 및 store directory fsync 뒤에 이벤트 identity+canonical bodyhash가 전부 일치해야 aggregated. 일부 이벤트가 들어갔더라도 missing이면 failed import_failed, 기존같은ID다른본문이면 conflict event_conflict. 빈배치는 heartbeat로 aggregated가능하지만 관측이벤트0. 원본inbox와 mirrored근거는 보존하고 같은배치 retry는 새event생성 금지.

상태파일 exact {version:1,registered_contexts:[{actor_id,environment_id,project_id,label}],batches:[{context_key,batch_id,payload_sha256,received_at,event_count,state,reason_code,updated_at}]}. context_key는 central.source_key의 문자열. state queued/aggregated/conflict/failed; reason_code none/event_conflict/import_failed/registration_changed/inbox_invalid. unknown/invalid inbox는 안전오류로 fail-closed하고 조용히 생략하지 않는다. metadata 제한8MiB. receive는 새 inbox 기록 전에 `delivery-state.error`(고정안전문구)를 먼저 영속 기록한다. 실패하면 inbox기록/ACK 전503으로중단한다. inbox영속후 metadata queued갱신은 best effort이며 실패해도 durable ACK는 유효하지만 기존error marker는유지한다. 이순서로 diskfull때도 이전snapshot이정상으로보이는것을막는다. aggregate도 marker를먼저영속기록하고 immutable inbox를 항상 재열람해 상태없는배치=queued로 시작한 snapshot을 먼저 저장 후 import, 매배치결과 갱신한다. lock으로 receive/aggregate갱신경쟁을 막는다. 상태갱신실패시 error marker와 nonzero CLI; renderer는 missing/corrupt/error-marker를 전달상태불명으로 보여준다. 해당locked operation의 모든 metadata갱신성공후에만 error marker를해제하고 parent fsync한다. 등록이제거된 inbox context는 omission하지않고 state에남기며 UI가등록불일치전역관리항목으로보인다. inbox/fsync실패 ACK 금지와 상태실패 ACK유효를 별도테스트한다.

## T2: 로컬 JSONL → outbox → 수신 영수증

`sender.py` public `run_once(config_path)` 반환 safe stats dict. CLI `--config FILE --once --loopback-test`, `--config FILE --loopback-test` watch(default2s). config exact {version:1,actor_id,environment_id,project_id,log_dir,outbox,endpoint,credential_file}. owner-only config/credential(plain token text) 및 명시한 한project logdir만 읽음. endpoint는 literal loopback http /v1/events, userinfo/query/fragment/다른경로거부; urllib ProxyHandler({})/redirect거부로 환경프록시나 다른호스트유출 금지. 파일IO util은 common재사용. 전송timeout10s, 응답도 bounded body strict_json.

logger.py:205는 log_dir 바로 아래 YYYY-MM-DD.jsonl에 여러 project 이벤트를 함께 기록한다. sender는 이 이름의 직계 regular파일만 읽고 parsed project_id가 등록UUID인 행만 검증/큐에넣는다. 다른project행은 전달/내용기록없이 건너뛴다. project-index/transcript/하위디렉터리/기타파일은읽지않는다. project별파일이있다는가정은하지않는다. 정렬된 파일과 newline완성행만 처리, invalid행은 file hash alias/행번호/reason만오류보고; 마지막 미완성줄은 대기. canonical eventhash와 ID를 key로 이미queued/acked이면 중복 enqueue금지. 같은ID변형은 blocked event_conflict. durable sender-state는 credential/endpoint원문을 제외하고 context+endpoint digest에 결속하여 다른환경/목적지로 outbox재사용을 거부한다. 단일sender lock nonblocking. enqueue가 state checkpoint보다 먼저 fsync되어도 다음시작에서 outbox를 재구성해 중복을 막는다. size-aware batch<=100/1MiB, outbox64MiB cap 초과는 원본보존+backpressure. ack된 batch 바이트도 파일럿에서는 보존하므로 유한운영한도를 명시한다.

각 batch 원바이트/UUID는 immutable 보존, status queued/acked/blocked, attempts,next_retry_at,reason_code 별도state. request실패/429/5xx는 1,2,4,8,16,30s+jitter(cap30), Retry-After秒/HTTP-date파싱상한30. wrongACK는 acked금지+retry; 400/401/403/409/413은 blocked. crash/ACK분실후같은batch재송신; ACK state저장실패는 다음에재송신하도록 보존. 과거blocked가있으면 run_once는재시도/진행하지않고명시적blocked결과, 임의자동해제명령은만들지않음. CLI errors nonzero, rawexception금지. 테스트는 retry clock을patch해 기다리지않고, actual HTTP loopback경로와 restart instance를 사용한다. heartbeat는 명시 `--heartbeat`에 한해빈배치를 enqueue; 자동2초heartbeat누적은하지않는다.

## T3: 전달 상태를 중앙 화면에 결합

`central.py` `load_delivery_state(path)` 추가; optional `summarize(store, delivery_state=None)`, `render(store, output, delivery_state=None)`, renderer CLI `--delivery-state FILE`. metadata schema와context연결/중복/시간/count/enum/size/owner regular검사. missing/corrupt/error marker는 안전한 error object로 바꾸어 전역 전달상태불명 배너와 프로젝트관리항목 표시; 실패를 event0정상으로 숨기지않는다. renderer에서 central store가 손상/한도로 읽기실패하면 metadata입력이있을때만 빈store+중앙저장읽기실패배너로 렌더해관리문제확인가능; metadata없이 기존error동작유지.

등록된 event없는context도 카드로표시하고 goal/phase/observed없음 그대로보존. received_at최대=마지막연결확인, actual event.observed_at=최근작업, queued/failed/conflict/aggregated count분리; aggregated event_count0은 업무관측증거아님. receive메타갱신전이면 error표시 또는 queued, 완료claim금지. 목록/상세에서 표시하며 서버mirror SHA/행이라는provenance문구를해당source에추가. 기존분석/관계원본/검색/390px UI 유지. 새로운프로젝트전체를 조직목표로 묶지않음. XSS용 metadata label도 DOM textContent/JSONescape유지. transport연결은합성loopback이라고표시.

## 인수와 원자화/이관 원칙

T1 수신/집계가 공통계약과 durable ACK의 하나의 불변조건을 소유하므로 더쪼개지않는다. T2 송신은 T1공통계약완료뒤, T3 UI도 T1상태계약완료뒤이며 T2/T3는서로파일겹침없어병렬가능. 단순함수별이관은하지않음. 하위모델은 명세/입출력/편집점/검사/제외범위가 모두정해진 세부구현만 수행. 계약변경·목적/승인판단·공유파일수정 필요·두번째같은실패는부모로반환. 부모가설계/독립review/Phase종료검사/통합2contexts실HTTP흐름/390px브라우저인수소유. 재검토가필요한계약변경은먼저spec와review갱신후발행한다.

T1 `python3 specs/ai-pms-transport/test_receiver.py`, T2 `python3 specs/ai-pms-transport/test_sender.py`, T3 `python3 specs/ai-pms-transport/test_delivery_view.py`; 최종부모 `python3 specs/ai-pms-transport/verify_transport.py`. 새명령구현전missing exit2를기준선으로기록. 기존test삭제/skip금지. 실제HTTP두등록context 같은project UUID분리, native observed+declaredbaseline/artifact/check/acceptance흐름, droppedACK/restart/중복/충돌/위조/wrongACK/오프라인회복/저장실패/heartbeat/metadata오류를검증. UI 부모가 실제목록→상세→원본/검색/전달오류/빈등록/390px확인. 영수증은local_loopback_verified=true일수있지만 actual_multi_user_delivery_verified=false,product_complete=false를고정한다. 임시credential/원본개인경로는영수증/HTML에남기지않는다.
