# 중앙 구현 초안 독립 검토

검토자: independent-central-reviewer. 대상: central.py 초안. 초안 판정: 수정 필요. 현재 재검토 판정은 아래에 기록한다. 구현자가 파일을 작성 중인 시점의 읽기 검토이며 최종 승인 및 구현 테스트 통과 판정이 아니다.

## 발견 사항

1. **높음 · central-2/4 — 사용자 인수 연결 검사가 없다.** valid_event는 acceptance.recorded에 artifact_id/artifact_version을 요구하지만 summarize와 showProject는 acceptance 이벤트를 조회하지 않는다. 존재하지 않는 산출물/다른 버전의 accepted 인수도 미연결 관리 항목으로 나타나지 않고 rejected/pending 상태도 원문 JSON 외에 보이지 않는다. 정확한 동일 프로젝트/산출물/버전 연결을 검사하고 미연결과 인수 상태를 사용자에게 보여야 한다. accepted 기록이 프로젝트 전체 완료를 의미하게 해서는 안 된다.
2. **높음 · central-1/2/4 — Agent의 런타임 source/session 귀속이 혼동될 수 있다.** observed_agents는 (session_id, agent_id)만 사용한다. 동일 중앙 출처 안의 codex/claude에서 ID 문자열이 같으면 같은 Agent로 합친다. manual 선언은 source=manual이므로 같은 session/agent만으로 한쪽 런타임 관측을 연결했다고 판정할 근거가 없다. 관측 Agent는 runtime source+session+agent로 구분하고 manual 선언에 런타임 귀속 정보가 없거나 두 런타임 후보가 있으면 미확인/모호함을 표시해야 한다. parent_agent_id 연결도 관리자가 탐색할 수 없다.
3. **높음 · central-2/3 — Agent/산출물 연결이 관리자 흐름에서 사실상 원문에만 있다.** 목록과 상세는 Agent/산출물/검사 개수를 보여준다. decision/check의 링크 상태는 일부 표기하지만 어떤 Agent가 어떤 산출물을 만들었으며 정확한 버전 검증과 인수가 무엇인지 연결된 관리자 표현이 없다. 원본 JSON 탐색 자체는 구현됐으나 핵심 비교 항목인 Agent/결과물 연결을 개수와 동일시하면 안 된다. 확정할 수 없는 Agent 귀속은 누락으로 남기고, 확정 가능한 링크의 ID/버전과 관련 이벤트로 내려갈 수 있어야 한다.
4. **중간 · central-4 — 과거 충돌/수집 오류가 정상 재수집 시 관리 화면에서 사라진다.** totals를 store에 보존하지만 summarize는 last_import만 검사하고 totals는 HTML payload에 전달하지 않는다. 한 번 event_id 충돌한 뒤 원래 정상 파일만 재수집하면 last_import.conflicts=0이 되어 충돌 경고가 사라진다. 기존 기록을 덮지 않더라도 해결 여부를 확인하지 않은 오류가 관리자의 시야에서 빠진다. 누적 과거 발생과 최근 수집 상태를 구분해 보여주거나 명시적인 해결 상태를 관리해야 한다.
5. **부모가 이미 전달한 중복 사항 · central-4:** schema_version=True가 1로 인정되는 타입 검증, 미등록 native_event+kind=null의 NATIVE.get 비교, observed_at 문자열 정렬로 .fraction/Z 및 +00:00 표현 간 최신 기준선/변경/관측 선택이 틀릴 수 있다. 최종 수정본에서 함께 확인한다.

## 정렬되는 부분과 남은 검증

- central-1: actor/environment/project context별 store key 및 event_id 멱등/충돌 보존은 중앙 격리 방향에 정렬된다. 실제 두 사용자 전달 완료 증거는 아니다.
- central-2: 중앙 다중 프로젝트 목록, 목표/Phase/최근 변경/관리 항목 구조는 갖췄다. 위 관계/인수 귀속 보완이 필요하다.
- central-3: 목록→프로젝트→원본 event JSON, 최초 파일 hash/행 번호/received_at 탐색 구조가 있다. textContent 및 script JSON의 <>& escaping은 사용자 입력 주입 방어에 정렬된다.
- central-4: 목표 없음/Phase 불명/없는 baseline decision/없는 artifact check/실패 검사/미래 시각/입력 실패를 관리 항목으로 처리한다. 시간 정렬, Agent/인수 연결, 과거 오류 상태는 보완 대상이다.
- central-5: 합성/로컬 가져오기 경계 배너와 기존 logger 계약 보존은 유지된다. 실제 브라우저/모바일/빈 상태 및 완성된 테스트는 아직 이 초안 검토에서 실행하지 않았다.

민감정보 allowlist와 PRIVATE 정규식은 제공된 제한 패턴의 차단이며 모든 형태의 비밀 탐지를 보장하지 않는다. raw input/path를 실패 출력에 echo하지 않고 비정상 이벤트 원문을 저장하지 않는 설계는 적절하다. owner-only 파일/원자 교체/import 잠금과 source 선언의 비인증 신뢰 경계는 제품 준비 범위에 맞는다.

## 핵심 수정본 재검토 — 로컬 준비 범위 수용

central.py/test_central.py의 현재 수정본을 직접 읽고 검사했다. 초안 지적 1~4 및 부모의 타입/시간 정렬 지적은 다음과 같이 해결되었다.

- acceptance.recorded를 정확한 artifact_id/artifact_version으로 연결하고 미연결/거절/대기를 표시한다. accepted를 프로젝트 전체 완료로 승격하지 않는다.
- 관측 Agent를 source+session+agent로 구분한다. manual 산출물의 runtime 후보가 하나면 관측 후보, 여러 개면 모호함, 없으면 미연결로 표시하며 인증된 귀속으로 표현하지 않는다.
- 상세 관계 목록에 산출물 ID/버전/이벤트, Agent 후보, 검사/인수 event ID와 상태가 보인다. 원본 이벤트 목록에서 해당 event ID를 찾아 원문까지 내려갈 수 있다.
- totals를 화면 payload에 보존하고 과거 수집 오류 기록을 이번 수집과 구분한다. 정상 재수집으로 과거 문제가 사라지지 않는다.
- schema_version의 실제 int 타입 및 kind allowlist를 검사하고 observed_at를 datetime으로 정렬한다. 전체 store 직렬화 크기 64MiB 초과 시 기존 파일을 원자 교체하기 전에 실패한다. CLI의 부모 resolve+최종 이름 방식은 /var 등 시스템 별칭을 해소하면서 최종 store 심볼릭 링크를 import에서 거부한다.

독립 실행: python3 specs/ai-pms-central/test_central.py exit 0, 2 tests OK. 추가 임시 logger subprocess 검사에서 baseline v1만 존재할 때 decision v2, artifact v1만 존재할 때 check/accepted v2를 모두 미연결로 표시하고 연결 검사/인수 개수 0을 확인했다. 이 추가 검사는 임시 파일만 만들었으며 제품 파일/테스트는 변경하지 않았다. 직접 import_sources 호출에서는 CLI와 같은 부모 경로 resolve가 필요하다는 API 경계를 확인했다.

남은 범위: 핵심 코드에서 새 차단 결함을 발견하지 않았다. 관계 항목은 event ID 텍스트이며 직접 원본 버튼이 아니어서 긴 이벤트 목록의 탐색 편의는 개선 여지가 있다. Agent 후보 정보에 session/parent_agent_id의 별도 관계 탐색은 없지만 원문에는 보존되며, 현재 코드가 확정 귀속을 주장하지 않아 로컬 최소 흐름의 차단 결함으로 판단하지 않는다. 전체 브라우저/390px/빈 상태 관측은 이 재검토에서 실행하지 않았다. sample/README와 최종 파일 변경 후 재검토, 부모 인수 게이트가 남는다. 실제 두 사용자 환경 전달과 인증/자동 전송은 미검증이며 제품 완료 승인도 아니다.

검토 시 central.py SHA-256: a9cbf463adfff0865a1b0d6a856d54e22f2718617b7c4dc99c99d284ed462f42

test_central.py SHA-256: a7fc012ce578c89831f5391d64f2fb3aba6d71cc94934a6513e1322c3eaf17a1

## sample/README 추가 검토 — 수용, 모바일 최종 인수 대기

README.md, sample/manifest.json, source-a.jsonl, source-b.jsonl을 직접 읽고 임시 디렉터리에서 현재 central.py의 import/render를 실행했다. 두 합성 출처가 동일 project UUID를 공유해도 actor/environment에 따라 별도 집계되며 alice 6개 이벤트(연결 검사 1, 인수 1), bob 2개 이벤트(연결 검사/인수 0)를 확인했다. invalid/read_failures는 0이다. alice에는 인수 대기, bob에는 산출물 검증 불일치와 수집 지연이 나타난다. sample 계약과 현재 validator는 일치한다.

README는 합성 데이터, logger subprocess 검사, 로컬 파일 가져오기와 실제 두 사용자 자동 전달/인증/서비스 운영/제품 완료의 차이를 분명히 남긴다. 한도, owner-only 파일, context별 UUID 격리, 정확한 artifact 버전 연결, manual Agent 후보 처리 설명도 코드와 일치한다. sample 시간은 고정된 합성 시각이므로 나중에 alice도 지연 표시가 생길 수 있으며 이 데모는 계속 최신인 실사용 흐름을 의미하지 않는다.

부모가 데스크톱 목록→alice 관계→artifact 원본, bob 지연/미연결, 검색 필터와 390px 목록을 관측했다고 전달했다. 이는 부모 보고이며 이 검토자가 브라우저로 독립 재현한 증거는 아니다. 부모는 390px 상세 원본의 긴 hash 때문에 문서 폭 590px을 발견해 CSS 수정 중이다. 해당 실제 UI 결함의 최종 수정/모바일 재관측이 아직 남아 있으므로 전체 UI 인수는 대기 상태다. sample/README 검토 자체에서는 추가 차단 결함을 발견하지 않았다.

## 최종 핵심 코드 검토 — 승인 (로컬 중앙 준비 단계)

현재 central.py/test_central.py를 재확인했다. body/이벤트 항목/버튼/provenance에 긴 문자열 줄바꿈을 보완한 CSS를 확인했고 핵심 입력 검증, source/session/agent 분리, baseline/artifact/version 연결, 인수 상태, 과거 오류 보존, store cap 및 안전한 JSON 렌더 처리가 유지된다. 최종 코드의 독립 test_central.py 재실행은 exit 0, 2 tests OK다. 이 해시의 로컬 중앙 최소 흐름 구현은 승인한다.

- central.py SHA-256: 7e5780995b2ae6cd2493efd5fbee19a14eb0425c02adbd39376f437a82e65cd5
- test_central.py SHA-256: a7fc012ce578c89831f5391d64f2fb3aba6d71cc94934a6513e1322c3eaf17a1

부모는 실제 Chrome 390px에서 목록→상세→원본과 빈 상태를 재실행해 document/body 폭 390px 및 console error/warn 0을 확인했다고 전달했다. 이 모바일 결함의 해결은 부모 관측 증거이며 본 검토자가 독립 UI 실행한 결과가 아니다. browser-observation.md/acceptance-evidence.json 작성 및 부모 최종 verify_acceptance.py 실행은 이 최종 코드 검토 이후 관문으로 남는다.

남은 한계: 범위는 합성/로컬 가져오기이고 실제 서로 다른 두 사용자 환경의 자동 전달, 사용자 인증, 중앙 서비스 운영/배포는 미검증이다. Agent 귀속은 관측 후보 또는 모호함으로만 표현하며 manual 선언의 runtime를 인증하지 않는다. 개인정보 정규식 검사는 제한된 패턴만 차단한다. 전체 UI 진실성과 인수 영수증의 관측 내용은 부모 책임으로 남는다. 제품 완료는 false이며 요구사항 central-1의 실제 전달은 미달이다. 향후 코드/테스트 해시가 바뀌면 이 최종 승인 범위를 재검토해야 한다.
