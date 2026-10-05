# 프로젝트 구성요소와 연결 도표

현재 읽을 수 있는 전체 화면을 유지하며 전체 계획 상단 요약과 WBS 사이에 도표 하나를 추가한다. 재리팩터링·새 모델/API/데이터 계약·배포는 범위 밖이다.

사용자가 답할 질문: 프로젝트 목표 아래 어떤 단계·작업이 있고, 각 단계는 어떤 API/MCP·문서와 연결되어 있는가? humanPhases/humanPhase/humanTasks/humanReferences, p.documents.phase_id와 humanDocumentary.tasks의 phase/source/plan_source가 근거이다. 구현된 소프트웨어 모듈이나 실제 실행 의존성을 추론하지 않는다.

도표는 '프로젝트 목표 → 단계별 구성'의 포함 관계를 선으로 연결한다. 단계별 열에 단계 제목·목표·현 상태, 모든 담당자 작업과 담당자/상태, 명시적으로 그 단계에 연결된 API/MCP와 문서 근거를 둔다. 단계끼리 화살표를 그어 선행 의존성으로 오해시키지 않는다. 선의 의미는 '소속', 참조 연결은 '참고'라 표시한다. 단계 연결이 없는 프로젝트 참조는 프로젝트 공통 참조 영역에 분리하고 임의로 각 단계에 배정하지 않는다. 데이터가 없는 단계/참조는 미기록을 표시한다.

각 단계/작업 노드는 기존 pageLink로 상세 이동하여 사람 scope·Back/reload를 보존한다. 참고 자료는 기존 확인/참고 탐색으로 이동하며 출처 신원을 보존한다. 링크 없는 참조는 텍스트이며 임의 외부 주소를 만들지 않는다. CSS와 native DOM으로 선·노드를 표현하고 큰 graph library/외부 API를 도입하지 않는다. 프로젝트 수·계획 단계 수를 고정하지 않으며 desktop 열 폭과 overflow를 처리한다. native links keyboard, headings/list labels와 textContent 안전성 유지.

변경점 specs/ai-pms-dashboard/human-view.js: human component map function + renderDetail plan insertion; human-view.css: component map desktop layout; dashboard.html HUMAN VIEW blocks exact embed. 본보기 humanTaskRow, humanProjectSummary, humanReferences와 pageLink. 이전 전체 UI 및 판단/완료/검증 의미를 수정하지 않는다.

인수: new check_map.py meaningful DOM regressions verify actual declared phase/task/ref edges, all shared owners despite person filter, missing/unlinked references, documentary-only completion/current-unconfirmed, safe labels, unchanged model; run existing check_readable.py. Parent actual Chrome local synthetic/private project checks diagram readability, stage/task keyboard/click navigation, Back/reload. Mobile excluded as prior instruction. Private source payload blocks unchanged; no deployment/push.

원문 → 질문 → 선언된 단계/작업/참조 → 계획에 하나의 연결 도표와 상세 경로 → DOM regressions and actual Chrome. Missing component architecture data is not evidence to invent implementation call flows.
