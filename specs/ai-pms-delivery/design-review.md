# 실환경 전달 준비 설계 독립 검토

검토자: independent-delivery-reviewer. 판정: **승인 전 준비 단계 목적 정렬 aligned**. 구현/네트워크/API/비밀/배포 승인이 아니다. PRODUCT-INTENT.md, spec.md, sources.md, plan.json을 직접 읽었다. 이번 검토 변경은 두 review 파일뿐이다.

- PRODUCT-INTENT.md SHA-256: e277f3669b0f7c8046f44bb463a853e3dd92791b465b449e6c4c70f9024d54a3
- spec.md SHA-256: 9987c54a0fe5d23ac925ed8f1daeabeea645a944a7295d7bd896d74f0cd7793d

## 최초 검토의 설계 지적 (아래 재검토로 명세상 해소)

1. **ACK 인정 조건의 완전성 · central-1/4.** 응답 계약에는 protocol_version/status/received_at이 있으나 송신기 인정 조건은 batch/hash/context/event ID 대조만 명시한다. protocol_version 정수 1, status=durable_inbox, 유효 최초 수신 시각 및 exact response fields/types까지 검증해야 한다. 잘못된 status 또는 protocol인데 식별 필드만 같은 응답으로 outbox를 ACK 처리하는 반례를 넣는다. 고정 ID 순서, 요청 body 원바이트 SHA 검사는 적절하다.
2. **ACK 이후 집계 실패의 관리자 통합 경로 미확정 · central-2/4.** ACK 뒤 sender 재전송을 멈춰도 inbox를 보존/집계 재시도한다는 경계는 맞다. 그러나 기존 central importer/render는 inbox pending/집계 저장 cap/실패/환경 heartbeat metadata를 직접 받지 않는다. 본 명세는 별도 표시를 약속하지만 이 상태의 durable 저장, 정확한 environment/project/batch 키, 실패 시 관리자 화면 갱신 경로를 정하지 않았다. 특히 중앙 저장 64MiB 때문에 import가 실패할 때 같은 central 저장 갱신으로 오류를 전달하면 화면이 계속 이전 상태가 된다. 중앙 집계 파일과 독립적인 수신/집계 상태 영수증을 지속하고 이를 인증 context로 중앙 관리자에 안전하게 결합하는 계약을 승인 A 구현 명세에 고정해야 한다. 기존 v1 본문 밖이라는 조건과 서버 manifest 등록 context를 유지한다.
3. **재시도/큐의 구현 경계 · central-1/4.** 100개와 body 1MiB를 동시에 만족하는 size-aware batch 분할이 필요하다. 100개의 최대 크기 이벤트를 먼저 영속 배치로 묶으면 413 후 blocked에서 회복이 어려울 수 있다. 큐 cap은 enqueue 전 검사하고 배치 바이트와 batch ID는 fsync 및 parent directory fsync 후 전송한다. 단일 sender 실행 잠금 또는 동일 영속 outbox 파일 갱신 잠금 규칙도 명시해야 한다. 원본 로그 보존과 재시도 ID/바이트 불변은 적절하며, cap의 영구 보관 포화는 작은 파일럿의 알려진 한계다. 자동 삭제 없이 무한 가동을 약속하지 않는다.
4. **입력·개인정보 경계 · central-4/5.** 등록 context에서 actor/environment를 결정하고 프로젝트 allowlist를 적용하는 방식은 적절하다. body hash/strict fields/types가 원바이트와 parsed 객체를 다루므로 duplicate JSON keys/nonfinite 값/과도한 nesting 및 malformed body를 전량 거부해야 한다. 기존 allowlist/정규식은 자유 텍스트 goal/summary에 포함된 모든 비밀·외부 URL·명령을 식별하지 못한다. 현재 명세가 완전 익명화를 보장하지 않는다고 적은 점은 맞으며 참여자 동의/보관·열람 범위에 잔여 민감정보 위험을 명확히 유지해야 한다. token 원문/Authorization/실패 body를 로그로 남기지 않는다.

## 정렬과 검증 한계

환경별 credential/context, bearer를 다른 호스트에 넘기지 않는 redirect 거부, loopback/HTTPS 분리, immutable inbox 파일+파일/디렉터리 fsync 뒤 durable ACK, batch ID 충돌 거부, ACK와 집계 완료의 구분은 중앙 목적에 정렬된다. 연결 heartbeat가 observed_at를 갱신하지 않고 생산자 원본 hash와 서버 mirror hash를 구분하는 점도 맞다.

준비 packet은 설정 원문/command/key/private path를 출력하지 않는 inventory와 실제 앱 관측 runbook만 작성한다. 미승인 A/B 실행을 시작하지 않는다. 요구 central-1의 실제 두 동의 사용자 전달은 미충족이며 central-2/3 기존 중앙 흐름도 새 transport로 연결됐다고 주장할 수 없다. central-4 실패 반례와 central-5 합성/실제 증거 분리는 향후 구현 인수 조건이다. 위 설계 결함은 승인 A의 실행 가능한 구현 명세/반례에서 해소할 사항이며 read-only 준비 패킷 발행 자체를 막는 제품 방향 결함은 아니다.

sources.md의 공식 문서 설명은 앱 hook 지원과 본 프로젝트의 전달 설계 제안을 구분한다. 본 검토에서는 링크된 웹 문서나 실제 앱 hook 동작을 별도로 검증하지 않았다. 영수증 문자열/해시가 실제 전달 성공 또는 독립 UI 실행을 증명하지 않는다.

## 수정 명세 최종 재검토 — aligned 유지

최신 spec.md를 직접 전부 읽고 실제 바이트 SHA-256을 다시 계산했다: 8032669a26a0f7db58431eb1378e02b89d7ce2a7e9ad273d1cb0a30d79d67d2f. PRODUCT-INTENT.md hash는 e277f3669b0f7c8046f44bb463a853e3dd92791b465b449e6c4c70f9024d54a3로 유지된다. 이전 지적의 미확정 표현은 현재 명세의 상태를 뜻하지 않으며 다음처럼 해소됐다.

1. 응답 exact fields/types와 protocol_version 정수 1, status=durable_inbox, 유효 UTC received_at 및 context/batch/hash/ID 순서 대조를 ACK 인정 조건으로 고정했다.
2. 중앙 이벤트 저장과 독립적인 delivery-state.json의 registered_contexts/batches 필드, queued/aggregated/conflict/failed 상태, safe reason enum, 8MiB 한도 및 손상/읽기 실패의 상태 불명을 명시했다. immutable inbox 배치가 metadata에 없으면 queued이며 중앙 저장 성공과 이벤트 본문 hash 대조 뒤만 aggregated로 기록한다. 상태 기록 전 crash는 재집계/대조로 복구한다. optional --delivery-state 로컬 렌더와 이벤트 없는 등록 환경, metadata만 바뀐 화면 재생성, 중앙 import 실패와 독립된 관리자 갱신을 승인 A의 구현 범위로 고정했다.
3. 이벤트 개수와 직렬화 body 크기를 함께 만족하는 분할, enqueue 전 cap 검사, 단일 sender 잠금, outbox 파일/부모 디렉터리 fsync 뒤 전송을 명시했다.
4. duplicate JSON keys/nonfinite/32단계 초과 nesting 거부를 양쪽 validation 경계에 추가했다. 실제 반례 목록도 wrong ACK/경쟁 sender/metadata 손상/import 후 상태 기록 전 crash를 포함한다.

승인 전 read-only 준비 패킷 발행에는 새 차단 결함이 없다. central-1..5 요구를 실제 충족한 제품 인수가 아니라 다음 승인 요청을 검토 가능하게 만드는 정렬 판정이다. A/B는 모두 미승인이고 actual delivery/product complete는 false다. 실제 두 사용자 앱 이벤트의 전달은 여전히 미충족이다.

잔여 경계: reason_code enum의 구체 값, 각 state 전이/실패 복구와 메타데이터 손상 시 render fallback은 승인 A의 실행 가능한 명세/구현 반례로 확정해야 한다. 제안에 적힌 fsync와 hash 대조가 실제 구현에서 올바르게 동작하는지는 아직 검증하지 않았다. 8MiB 상태/64MiB inbox/outbox 보관은 작은 파일럿 한도이며 자동 retention 없이 무한 운영을 약속하지 않는다. 자유텍스트 goal/summary의 완전한 비밀 제거는 보장되지 않아 참여자 동의와 보관/열람 범위, 잔여 민감정보를 sources/runbook/승인 B에 유지해야 한다. 준비 checker가 실 로그를 읽지 않고 고정 설정선언만 조사한다는 범위를 유지한다.
