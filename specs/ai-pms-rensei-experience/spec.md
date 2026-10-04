# 사람이 사용하는 PMS 경험 개선

## 목적
여러 사람이 각 환경에서 진행하는 공동/개인 프로젝트의 목표, 전체 단계, 달성/미달성/근거 없음과 다음 판단을 구분한다. Rensei 보고서의 첫 화면 구현 묶음(A1/A2/A4/A5)을 구현하고 A3의 기존 검사 판정·A6의 세션→작업→Phase 근거 경로, B의 현재 승인 유효성 계산, C의 기존 갱신을 보존을 제품 목적에 맞게 구현한다. 20개 후보 전체 또는 실행 제어·AI 분석 구현을 주장하지 않는다.

## 근거와 기준선
- 정본 PRODUCT-INTENT.md, NEXT_SESSION.md, reports/rensei-research/assessment.md, docs/human-view-and-analysis.md.
- specs/ai-pms-dashboard/human-view.js: humanPhase/renderPhaseFlow/renderDetail가 기본 최소 화면. CSS는 현재 연결 없는 카드 grid. 기본 Phase 상세는 세 항목. dashboard.html에 두 원본을 내장한다.
- work.py derive는 state/reason/waiting_on/interventions(owner/task_id/phase_id/summary/next_action)을 이미 계산한다. operations.py는 lifecycle와completion을 분리. 기본 projection에 이를 새 완료 판정으로 재계산하지 않는다.
- route/pageLink/navigate는 hash 기반; 별도 evidence route. applyChanges는 필터/scroll/focus를 복구. unknown 참조는 추가하지 않는다.
- canonical Kit current_content.py 마지막 human-analysis/phase-flow 항목과 build_current.py allowlist.
- 기준선 python3 specs/ai-pms-human-projection/check_human_view.py 실제 exit0. 실제 브라우저 확인 별도.

## 확정 설계
1. 흰 배경, 절제된 색과 서체 위계, 한 영역 한 관리 질문. 제목은 프로젝트/단계 이름과 판단 필요. 상투적 질문형 설명 금지. 사람 필터와 공동 프로젝트 참여자를 유지.
2. 프로젝트 기본 계획: 목표/담당 → 전체 Phase를 연결한 가독성 있는 진행 흐름 → 최종 인수. 큰 숫자/상태/짧은 목표. 연결은 계획상 순서를 뜻함을 구분하고 의존성 없는 phase를 선행조건으로 주장하지 않음. 날짜가 없는 실제 자료에 기간/ETA를 생성하지 않음. WBS/Gantt는 기존 evidence 내부 경로 보존. 단계 수 증가/긴 한글/390px에서는 세로 흐름으로 자연스럽게 재배치; 가로 넘침 없음.
3. 기본 화면에 별도 판단 필요 링크와 수 표시. 프로젝트별 및 전체 처리함은 독립 hash 주소(view=attention). 전체 처리함은 현재 사람 필터를 존중. owner 미지정/Phase gate만 있는 항목은 프로젝트 scope로 표시하고 사람별 작업 요청으로 잘못 귀속하지 않음.
4. 처리함: 실제 현재 interventions의 담당자·요청/이유·다음 행동·관련 task/phase/최종 상세 링크. 정상 ready/in_progress를 모두 긴급 요청으로 취급하지 않음. 유사 항목은 고유 근거키로 묶고 최신 snapshot에서 재계산. documentary 화면은 문서상의 막힘·선언된 다음 행동·문서 날짜/발췌 출처로 별도 투영하고 현재 검사 요청으로 승격하지 않음. 일반 current interventions와 함께 사용하는 경우 각 항목에 문서 기준/현재 검사 근거 출처를 명시. 알 수 없는 현재 검사 조건을 반복 요청 수십 개로 늘어놓지 말고 같은 Phase·같은 이유는 묶어 근거에서 펼침. read-only: 권한 부여·승인·모델 경고 생성 버튼 없음.
5. Phase 상세는 기존 목표/달성 상태/API·MCP 세 항목 유지. 실제 개입이 있으면 제한된 하나의 다음 판단 요약+처리함 링크; 모든 raw 작업 목록은 기본 상세에 쌓지 않음. 별도 처리함에서 task의 기존 actionable 상세를 연결. 선언된 다음 행동이 없으면 추측해서 채우지 않음. documentary는 문서 기준의 진척임을 유지하고 현재 runner/원격 신뢰로 승격하지 않음.
6. 링크/버튼은 native focus/44px, 색 이외 상태 텍스트, no innerHTML. documentary 처리함/Phase 요약은 문서 기준 날짜·출처 경로가 있고 현재 검사/인수 미확인을 유지한다. 루트 목록/프로젝트/Phase/처리함/근거의 브라우저 뒤로·앞으로·reload와 delta 갱신 때 위치/필터/포커스 보존. UI 구현은 human-view.js/css와 내장 block 안에서만; 엄격한 모델/계약/원본 판정 수정 금지.
7. Kit 한영 문서와 runtime 패키지/ZIP/정적 app/실제 로컬 preview를 같은 원본으로 갱신. 공개용은 합성만. 기존 요청의 준비 상태를 유지하고 이번에는 push/배포/새 외부 API/DB/글로벌 훅·신뢰 변경하지 않음.
8. Graphify는 이 프로젝트 코드만 AST/code-only/no-cluster로 로컬 정리. query 가능한 graph.json과 사람이 읽는 구조/출처/갱신 명령 안내. 관계 추출과 실제 통합 증거를 구분, endpoint 검증. 홈/개인 프로젝트/원문 로그/의미 API 추출 금지.

## 요구→질문→근거→행동→검증
- 사람 입장의 디자인 → 누가 같은 목표에 참여하고 어디까지 달성했나 → owners/declared phases/current states → 프로젝트/Phase 별도 탐색 → desktop390px 실제 화면, 공동 두 사람 필터.
- 의미 있는 관리 → 왜 멈췄고 내가 무엇을 판단하나 → work.interventions 현재 근거 → 관련 작업/기준 확인 → ready제외/unknown 유지/귀속/원본 모델 불변 DOM 회귀+클릭 검증.
- 하위 작업 → 책임 범위와 통합이 명확한가 → plan/review/task result → 독립 검토 후 emit → validate plan/result+부모 phase exit 실행.
- Graphify 정리 → 어느 파일이 무엇을 맡나 → AST graph와 확인한 소스 → 구조/탐색/갱신 → graph endpoint/출처와 sample query.

## 경계
보이는 화면 개선 완료와 실제 원격 두 사용자 운영 인수는 별개. 원격 전달/provider hook trust/실제 AI 분석 false를 유지. 임의 일정/경고/완료/북극성 기여 생성 금지. 기존 실패 테스트 삭제/skip/완화 금지. 새로운 파일/명세를 제외한 기존 dirty 변경 보존.
