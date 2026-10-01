# 승인 A 코드·부모 인수 최종 독립 검토

검토자: independent-transport-reviewer. 검토일: 2026-10-01. 판정: 승인 A의 합성 loopback 구현에서 현재 확인된 미해소 blocker 없음. 실제 여러 사용자 환경 전달과 제품 완료는 검증하지 않았으며 두 상태는 false로 유지한다.

## 검토 범위와 실행 근거

PRODUCT-INTENT.md, approval.json, transport spec/intent-review, common/receiver/sender, 중앙 import·delivery metadata·renderer, 세 신규 검사와 기존 중앙 검사, 부모 exercise/gate 및 ELI20 보고서를 직접 읽었다. 구현과 테스트 파일은 수정하지 않았고 이 문서만 작성했다. 읽기 검토와 실제 실행을 구별하며 모든 가능한 장애·경쟁을 증명한 검토로 표현하지 않는다.

독립 검토자가 직접 실행한 검사:
- `python3 specs/ai-pms-transport/test_receiver.py`: 실제 HTTP loopback exit 0. 위조 자격·폐기 후 replay·프로젝트 허용 목록·요청 헤더·원바이트 충돌·두 context 격리·inbox/replay fsync 실패·metadata 실패 뒤 유효 ACK와 error marker·집계 충돌·손상 inbox 및 nested 중앙 데이터 실패를 검사했다.
- `python3 specs/ai-pms-transport/test_sender.py`: 실제 HTTP loopback exit 0. 날짜별 혼합 프로젝트 로그·불완성 행·재시작·offline/wrong ACK/응답 분실·프록시 우회 방지·redirect 차단·retry/429·영구 blocked·backpressure·명시 heartbeat·checkpoint/ACK 저장 실패를 검사했다. 재시도 시계와 실패 주입은 모의 제어이며 HTTP 경로는 실제 loopback이다.
- `python3 specs/ai-pms-transport/test_delivery_view.py`: 4 tests, exit 0. metadata 유효성·등록/heartbeat/실패/충돌·in-process receive/aggregate·mirror provenance·안전한 HTML escaping·손상 중앙 저장소 CLI fallback을 검사했다. 브라우저를 실행한 검사는 아니다.
- `python3 specs/ai-pms-central/test_central.py`: 기존 2 tests, exit 0. 기존 검사 삭제/skip 없이 실행했다.
- `python3 specs/ai-pms-transport/exercise_transport.py`: 실제 HTTP exit 0. 두 이벤트 context·등록 context 4개·이벤트 10개, 같은 project UUID 격리, 원본 body 대조, 재시작 batch 중복 없음, heartbeat와 미연결 등록 구분, 정확한 conflict 귀속을 확인했다.
- 최신 `exercise_transport.py --output`도 검토자 전용 임시 폴더에서 exit 0이었다. dashboard/empty/audit/error와 영수증을 실제 생성했고, 저장 산출물의 임시 credential·credential digest·개인 실행 root 유출 검사도 통과했다. error.html은 실제 renderer CLI로 nested store 손상과 durable error marker를 적용해 만들었으며 전달상태 불명·중앙 저장 읽기 실패가 JSON 데이터에 들어 있음을 직접 확인했다. 저장 HTML 생성은 실제 브라우저 클릭 인수와 구별한다.

## 지적과 해소 확인

이전 부모 gate의 생성 귀속 누락은 현재 코드 tuple·HTML/loopback observation hash를 generation.json에 함께 기록하고, gate가 현재 코드·artifact·부모 browser 관측 generation identity를 대조하도록 수정됐다. heartbeat는 정확한 배치/context/hash/event_count=0/aggregated/유효 received_at을, conflict는 정확한 배치/context/hash/state와 event_conflict reason을 검사한다. error.html도 현재 생성·필수 hash 집합에 포함되며 gate는 delivery_state_unknown/central_read_failure 관측 선언을 요구한다.

구현 중 검토에서 발견한 새 directory 부모 fsync 누락, registry JSON 손상의 잘못된 HTTP 400 분류, central.json에 metadata 8MiB 한도를 적용한 오류, HTTP 기본 오류 응답의 안전 JSON 우회, 테스트 helper 이름 충돌, nested events list의 AttributeError traceback/fallback 누락은 현재 코드와 대응 검사에서 해소됐다. common은 새 directory entry와 재시도의 부모 barrier를 수행한다. registry 실패는 invalid_registry 503, 중앙 파일 barrier는 기존 MAX_STORE 64MiB를 사용한다. receiver는 집계 실패를 독립 metadata에 보존하고 renderer는 전달 metadata가 있을 때 손상 중앙 저장소를 관리 문제 화면으로 바꾼다.

원본 inbox·outbox는 보존되며 cap의 임시 write 정책은 코드에 명시돼 있다. 수신은 현재 registry로 매번 인증하고 immutable inbox 파일+directory barrier 뒤에 ACK한다. metadata 실패를 성공 snapshot으로 숨기지 않도록 먼저 durable marker를 남긴다. ACK는 inbox 영속만 뜻하며 집계는 저장 이벤트 identity와 canonical body를 대조한다. sender는 credential/endpoint 원문을 durable state에 넣지 않고 context+endpoint digest 결속, literal loopback endpoint, 무프록시·무redirect 경로를 사용한다.

## ELI20 설명과 최종 인수 경계

보고서는 원래 중앙 관리 목적, 관측과 선언, Kit와 중앙 PMS, ACK·집계·검사·인수, 연결 시각과 작업 시각, mirror와 원본 로그 해시를 구별한다. 본문 충돌 도해는 새/다른 전송함의 수신 충돌과 같은 전송함의 송신 전 차단 조건을 반영했다. 자유 텍스트의 모든 민감정보 제거를 보장하지 않고 실제 운영 B의 동의·목적지·권한·보관·실제 앱 훅 검증을 미완료로 남긴다. 진행 상태 문구의 최종 갱신과 보고서 상호작용/390px 관측은 부모 담당이다.

이 검토자는 부모 브라우저 인수를 수행하지 않았고 최종 acceptance-evidence가 아직 작성되기 전이므로 verify_transport 전체 최종 관문을 실행하지 않았다. gate 코드와 생성 연결을 읽기 검토했다. 부모는 현재 generation에 대해 목록→상세→원본·검색·heartbeat/빈등록·충돌·전달상태 불명·중앙 읽기 실패·390px·빈상태를 실제 확인하고 영수증 작성 후 최종 gate를 실행해야 한다. 부모 UI 선언과 hash는 관측 대상의 일관성을 확인하며 독립성이나 관측의 진실성을 자동 증명하지 않는다.

검토 결과는 로컬 합성 파일럿의 코드·검사 범위에 한정한다. 실제 두 참여자의 앱 훅→로그→자동 전송→중앙 근거, 외부 HTTPS·인증/관리자 권한 운영·배포·실사용 평가를 증명하거나 승인하지 않는다. `actual_multi_user_delivery_verified=false`, `product_complete=false`.

## 검토 시점 코드 SHA-256

- common.py: faf1c0aebb0ddbce0f17019cf3d837984ab91fe887b4bcdba1d9753f5859f657
- receiver.py: 2aed7dbb597be0a47c11d17ec817926bfa0f49af311b188f716f1616b90ac099
- sender.py: 49b580312fe5227301cb4e14a36b3fe15de9fb24200126c5a24bf926a0e4a44d
- test_receiver.py: 7dd36c30d7da1d1ba581faa4deb437bb0578723bb9deafd31a2a99ca55a46315
- test_sender.py: 546dc011c3dbcb6cd4518fef9ebde632b62067891da8fbdbde341ce12dce38c2
- test_delivery_view.py: 6c4239b4653859c2eaf06b9f7ba7d6f0b8c42d39545fe8aa17ec5a5515f8f87c
- exercise_transport.py: c1fe7cb655c0822acc417cc645d9cd4306140dac29f3fc2a81cb7c748b623192
- verify_transport.py: 161706d3e9dbe0173195b34c7c9524414f1cfb675587565b910133326fa3aa05
- central.py: a55a2f59a681633324bf9b182e9e7dc36e179d329e54cfd9a21140f37787e904
- test_central.py: a7fc012ce578c89831f5391d64f2fb3aba6d71cc94934a6513e1322c3eaf17a1
