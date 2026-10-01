# 승인 A 전달 구현 명세 독립 검토

검토자: independent-transport-reviewer. 판정: **aligned**, 승인 A의 합성 로컬 API/loopback 구현 범위에 한정한다. 실제 다중 사용자 전달 및 제품 완료는 false다. 읽은 파일: PRODUCT-INTENT.md, approval.json, spec.md, plan.json, DELEGATION.md, 이전 delivery/spec.md 및 logger.py의 로그 기록 지점.

- source SHA-256: e277f3669b0f7c8046f44bb463a853e3dd92791b465b449e6c4c70f9024d54a3
- spec SHA-256: 2736677dd53fe9d2f52efae5b65f7e5ff20f28cd45d9a66d987a1330ca59c9aa
- 승인 대상 이전 delivery/spec SHA-256: 8032669a26a0f7db58431eb1378e02b89d7ce2a7e9ad273d1cb0a30d79d67d2f (approval.json과 일치)

## 핵심 발견과 해소

최초 T2의 등록 project 전용 JSONL/otherproject 스캔 금지는 실제 logger.py:205의 날짜별 혼합 기록과 모순됐다. 부모가 최신 명세에 직계 YYYY-MM-DD.jsonl bounded read와 parsed project_id 필터, 타project 내용 미기록·미전송, project-index/transcript/하위경로 미읽기로 수정했다. 최신 문단을 직접 확인했고 이 모순은 해소됐다. A에서 실행할 로그는 합성 임시 fixture이며 실제 글로벌 로그/사용자 데이터 읽기로 확대하지 않는다.

현재 명세에서 패킷 발행을 막는 핵심 미결정을 발견하지 않았다. 구현 세부에서 아래 조건을 증명해야 하며 이는 구현이 완료됐다는 판정이 아니다.

## 요구사항과 불변조건

- central-1: 등록 credential은 body 입력 actor/environment를 믿지 않고 등록 context/project에 귀속된다. 같은 UUID 두 context 분리, 다른 actor/project 위조, registry 제거 후 replay 거부가 인수 반례다. raw batch 불변/완전 ACK 대조/재시작과 ID 본문 충돌 상태는 송수신 원본 보존에 정렬된다.
- central-2/3: 기존 관리자 목표/Phase/결정/Agent·산출물·검사·인수의 정확 버전 링크 및 원문 탐색을 유지한다. 등록만 된 context/heartbeat의 연결 확인은 작업 관측이 아니다. 서버 mirror hash는 사용자 원본 파일 hash로 표현하지 않는다.
- central-4: fsync 실패에는 ACK 금지, inbox 영속 후 metadata 실패에는 durable ACK 허용+error marker 유지라는 구분이 구체적이다. snapshot invalidation marker를 metadata 변경 전에 영속 기록하고 전체 성공 뒤 해제하는 순서가 stale 성공 snapshot을 가리는 방향이다. aggregate가 immutable inbox에서 queued를 복구하고 중앙 commit/이벤트 hash 대조 뒤 aggregated를 기록한다. 중앙 cap/손상에도 독립 상태와 fail-safe 화면을 제공해야 한다.
- central-5: T1/T2/T3 개별 검사는 부분 구현 검증이다. 최종 부모 verify_transport 및 실제 loopback 두 context/부모 목록→상세→원본·검색·오류·빈등록·390px 인수에서만 A의 로컬 흐름을 닫는다. 실제 두 사용자 앱 전달 인수는 별도 B 이후이며 현재 false를 유지한다.

## 작업 원자화와 공유 계약

T1이 common 공개 계약과 receive/aggregate의 durable ACK/inbox/metadata 불변조건을 소유하는 분할은 적절하다. T2 송신과 T3 화면은 T1 계약/테스트 완료 뒤 발행하며 쓰는 파일이 서로 다르다. T3가 central.py의 기존 공개 validator/import 함수 의미를 바꾸면 T1/T2 의존성이 달라지므로 부모 반환/명세 재검토를 해야 한다. optional summarize/render 인자는 기존 offline 호출과 호환돼야 한다. 공통 파일 변경은 T2/T3가 임의 수행하지 않는다. 부모는 계약 고정, 독립 review, 통합 반례, Phase 종료 및 실제 UI 관측을 소유한다.

## 후속 코드 검토의 필수 확인과 잔여 한계

- HTTP framing/Content-Length/Transfer-Encoding/content type/timeout, loopback literal/ProxyHandler/redirect 거부를 실제 HTTP 반례로 확인한다. ::1 지원과 host 거부도 loopback 범위에서 검증한다.
- write_private의 tempfile/file+parent fsync와 replay 재fsync, queue cap의 temp overhead 정책, sender outbox-before-checkpoint 복구 및 ACK state 실패 재송신을 확인한다. cap에서 성공/버림을 만들지 않는다.
- renderer는 marker/snapshot 조합을 읽는 중 변경돼도 성공으로 단정하지 않는 fail-safe를 유지해야 한다. 상태 파일 손상/unknown inbox/등록 제거/중앙 저장 읽기 실패가 배너/관리 항목으로 보이는지 부모가 직접 관측한다.
- registry/context/project 중복, schema bool/int, bounded JSON nesting, UTF8/raw body hash, credential/개인경로/원문 비출력 및 label XSS를 확인한다. 자유텍스트 goal/summary의 완전한 민감정보 제거를 보장하지 않는다.
- inbox/outbox64MiB/state8MiB 및 파일럿 보관은 유한 운영 한도다. 자동 retention/외부 호스팅/SSO/실제 hook trust/실 credential은 이번 범위가 아니다.

이 검토자는 구현/네트워크/테스트/설정/키/배포를 실행하지 않았고 두 review 파일만 썼다. 세 구현 검사 exit2 및 준비 gate exit0은 부모의 기준선 보고로 읽었으며 독립 실행 결과로 주장하지 않는다. 실제 구현 해시와 테스트/부모 UI 관측은 후속 검토 대상이다.
