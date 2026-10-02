# Phase 흐름 중심 화면

Primary view: 사람 필터 → 프로젝트 목표 → 전체 Phase 흐름 → 최종 프로젝트 완료 조건. 사람 선택 범위를 유지하며 프로젝트 전체의 모든 단계를 보여준다. 데이터/계약/완료 계산 변경 없음. 그래프는 이미 계산된 work.phases 상태와 work.tasks만 사용한다. 새 라이브러리 없이 HTML 버튼/연결선 + responsive CSS로 구현한다.

각 flow는 목표, 완료 Phase 수/전체 수, 첫 미완료 단계와 이후 남은 단계를 알 수 있어야 한다. 완료 초록·현재/진행 파랑·실패/막힘 강조·아직 남은 단계 회색 + 텍스트/아이콘. 배열상 첫 미완료는 '먼저 확인할 단계'이며 선언 current_phase나 다른 단계 병렬 작업을 숨기지 않는다. 작업 기술검사 통과만으로 Phase complete/프로젝트 complete로 승격하지 않는다. 화살표는 선언 계획 순서를 나타내며 의존성은 상세의 실제 task.depends_on으로 표시한다. 일정/기간/성과를 추정하지 않는다.

각 Phase와 마지막 '프로젝트 완료' 노드는 클릭 가능한 native button. 클릭 시 해당 프로젝트 chart 바로 아래 inline inspector에 단계의 전체 책임 작업(담당자 필터는 강조/내 작업 수로 표현하되 전체 완료 경계를 가리지 않음), 완료 조건, 막힘/다음 행동, 검사/문서/승인 근거를 펼친다. 평소에는 전체 작업 리스트/원본/긴 metadata를 숨긴다. 기존 renderWork(panel,p,phaseID optional) 또는 task helper 재사용; 기존 근거 상세 및 import/export 안전 검증 유지.

최종 노드는 p.status를 기준으로 표시한다. 모든 Phase 완료여도 프로젝트 전체 검사/인수가 미충족이면 마지막 노드 미완료. 프로젝트 검사/필수 Phase/미해결 조건을 inspector에서 확인 가능. work 없는 legacy에서는 기존 phases 검사상태의 제한을 명시하고 계획/진행을 만들지 않는다. Phase가 없으면 계획 미입력.

기본 사람 view와 프로젝트 view에서 flow를 전면에 표시한다. 세션·수집·MCP/원본은 secondary disclosure로 보존. 세션 상세에서도 프로젝트 흐름으로 직접 연결. 개인 필터를 바꾸거나 live delta/reset이 오면 visible graph/inspector 최신 상태 반영, 가능한 선택 유지; 삭제된 선택은 해제한다. DOM safe text 유지. 키보드 Enter/Space native button, aria-pressed/expanded, inspector 제목 focus와 버튼 복귀, mobile390px는 세로 flow로 모든 단계가 보이며 가로 넘침 없음.

인수: runnable DOM checks prove initial flow presence, people filter, complete/failed/revalidation/remaining states, phase click inspector/tasks/evidence, final project gate, live delta selection, empty/legacy/injection, plus existing IA/live/work validators. Actual browser/390px render separately and honestly recorded. Parent builds static+Kit portable HTML, public suite, existing aliases production byte checks. New report/doc explains primary chart rather than adding another navigation layer.
