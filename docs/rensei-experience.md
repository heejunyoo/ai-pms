# 사람 중심의 Phase 흐름과 판단 필요 처리함

이번 개선은 사람이 여러 사용자의 프로젝트를 읽고 다음 판단으로 이동하는 화면에 집중합니다. [제품 목적](../PRODUCT-INTENT.md)의 중앙 다중 사용자 관리 범위를 유지하면서, [Rensei 조사](../reports/rensei-research/assessment.md)의 후보 중 전체 Phase 흐름과 별도 처리함, 간결한 상세와 안정적인 탐색을 채택합니다. 20개 제안 전체를 구현하거나 Rensei 실행기를 연결하는 작업은 아닙니다.

## 기본 화면과 별도 경로

사람 선택 → 참여 프로젝트 → 전체 Phase 흐름 → 별도 Phase 상세로 이동합니다. 공동 프로젝트는 하나의 카드에 참여자를 표시합니다. 기본 정보는 프로젝트 목표, Phase 목표, 달성 상태, 참고한 API·MCP입니다. 목표·담당에서 전체 단계를 거쳐 최종 인수로 이어지는 계획을 읽고, 단계와 작업의 세부 근거는 필요한 때 별도 화면에서 엽니다.

흐름의 연결선은 계획상의 순서를 표현합니다. 실제 선언이 없는 의존성이나 날짜·기간·ETA를 생성하지 않습니다. 달성·미달성·근거 없음은 기존 모델 판정을 투영하며 단계 달성과 프로젝트 최종 인수를 구분합니다. 흰 배경, 절제된 색, 이름과 상태의 서체 위계로 읽는 순서를 정리하고, 모바일에서는 같은 흐름을 세로로 배치합니다. 색 이외의 상태 텍스트와 native focus, 최소44px 이동 대상을 유지합니다.

Phase 상세에는 목표·달성 상태·API/MCP 세 항목을 유지합니다. 실제 판단 항목이 있을 때 짧은 다음 판단 요약과 처리함 링크를 추가합니다. raw 작업 목록을 기본 상세에 쌓지 않으며 작업 WBS·Gantt, 검사 명령, 문서 버전, 세션과 원본은 기존 분석 근거 경로에서 확인합니다. 프로젝트 참조를 특정 Phase의 참조로 추측하지 않습니다.

## 읽기 전용 판단 필요 처리함

기본 화면은 판단 필요 수와 링크를 표시합니다. 전체 처리함과 프로젝트별 처리함은 독립 hash 주소 `view=attention`으로 이동합니다. 전체 처리함은 선택한 사람 필터를 유지합니다. 처리함에는 현재 `work.interventions`의 담당자, 요청 이유, 다음 행동과 관련 task/phase 상세 링크를 투영합니다.

정상 `ready`/`in_progress`를 모두 긴급 요청으로 취급하지 않습니다. 담당자가 없거나 Phase gate만 있는 항목은 프로젝트 범위로 표시하며 특정 사람의 작업 요청으로 잘못 귀속하지 않습니다. 같은 Phase·같은 이유의 반복 항목은 고유 근거를 보존해 묶고 상세 근거에서 펼칩니다. 최신 snapshot을 기준으로 다시 계산하며 선언된 다음 행동이 없으면 추측하지 않습니다.

문서상의 막힘·선언된 다음 행동은 문서 날짜와 발췌 출처를 함께 표시합니다. 각 항목에서 문서 기준과 현재 검사 근거를 구분하고 문서 기록을 현재 runner 검사·인수로 승격하지 않습니다. 현재 검사·인수가 확인되지 않은 상태는 유지합니다. 비공개 실제 자료를 공개 샘플로 옮기지 않습니다.

처리함은 읽기 전용입니다. 승인, 권한 부여, 원격 실행, 모델 경고 생성 버튼을 추가하지 않습니다. 기존 actionable 작업 상세로 이동해 기록을 읽는 것과 실제 변경·실행을 수행하는 것은 별개입니다.

## 채택 범위

| 구분 | 이번 반영과 보존 | 남은 경계 |
|---|---|---|
| A1/A2/A4/A5 | 전체 Phase 흐름, 간결한 기본 상세, 별도 처리함, 탐색 안정성 | 날짜 없는 일정·ETA, 자동 긴급도·완료 점수 생성 없음 |
| A3/A6와 B | 기존 검사 판정, 현재 승인 유효성, 세션→작업→Phase 근거 경로 보존 | 화면이 승인하거나 현재 완료 조건을 완화하지 않음 |
| C와 갱신 | 기존 snapshot·증분 갱신에서 위치·필터·포커스 보존 | 이 화면 개선이 원격 두 환경 운영 인수를 증명하지 않음 |
| 분석 준비 | 기존 목표 비교 입력과 분석 목적 문서 유지 | 실제 모델 실행·근거 검증·경고 수락/기각 저장 미구현 |
| 운영·공개 | 합성 정적 샘플과 선택적 자체 호스팅 중앙 구현의 역할 구분 | 실제 provider 훅 trust·원격 사용자 전달은 별도 인수 |

이 문서의 상대 링크와 탐색 명령은 전체 소스 checkout 기준입니다. 경량 Kit runtime은 실행에 필요한 파일만 포함하며, 전체 소스는 https://github.com/heejunyoo/ai-pms 에서 확인합니다. 공개 반영 여부는 specs/ai-pms-rensei-experience/release-proof.json에서 확인합니다.

## 소스 역할과 Graphify

[프로젝트 구조 안내](project-architecture.md)가 정본 파일과 생성본의 역할을 설명합니다. 이번 화면 책임은 다음과 같습니다.

| 책임 | 소스 |
|---|---|
| 사람 필터·프로젝트·Phase·처리함 투영 | [human-view.js](../specs/ai-pms-dashboard/human-view.js) |
| 흐름의 위계·연결·모바일·focus 스타일 | [human-view.css](../specs/ai-pms-dashboard/human-view.css) |
| 원본 근거·WBS·기존 라우팅과 내장 화면 | [dashboard.html](../specs/ai-pms-dashboard/dashboard.html) |
| 현재 작업·검사·승인·개입 판정 | [work.py](../specs/ai-pms-dashboard/work.py), [management.py](../specs/ai-pms-dashboard/management.py) |
| 세션 생명주기와 달성·조직 측정 | [operations.py](../specs/ai-pms-dashboard/operations.py) |
| 정규화·중앙 전달·증분 조회 | [portfolio.py](../specs/ai-pms-dashboard/portfolio.py), [live_service.py](../specs/ai-pms-live/live_service.py), [live_sender.py](../specs/ai-pms-live/live_sender.py) |
| 통합·정적 앱·Kit runtime 생성 | 부모가 [build_dashboard_app.py](../scripts/build_dashboard_app.py), [package_live_kit.py](../scripts/package_live_kit.py)로 갱신 |

부모가 [refresh_project_graph.py](../scripts/refresh_project_graph.py)로 이 프로젝트의 코드만 로컬 추출하고 endpoint를 확인합니다. `graphify-out/graph.json`과 검증·구조 보고서는 로컬 탐색 자료입니다. 홈·개인 프로젝트·원문 로그를 함께 인덱싱하지 않고 `code-only/no-cluster` AST 추출을 사용합니다. 의미 분석·외부 모델 API는 사용하지 않습니다.

```sh
python3 scripts/refresh_project_graph.py
graphify query "humanPhase renderPhaseFlow attention" --budget 1500
```

AST의 파일·심볼 연결은 실제 런타임 통합, 사용자 전달, 커버리지나 기능 완성도의 증거가 아닙니다. 동적 import·JS override는 현재 정본 소스와 실행 검사를 함께 확인해야 합니다. 갱신 시각과 출처는 부모가 생성한 로컬 graph 검증 자료를 기준으로 확인하며 이 문서는 추출 성공이나 최신성을 자체 인증하지 않습니다.

## 검증과 인수

문서의 정적 컴파일 검사, simulated DOM 회귀검사, 실제 브라우저 인수를 구분합니다. 데스크톱 인수 대상은 공동 두 사람 필터, 프로젝트/Phase/처리함/근거 이동, 뒤로·앞으로·reload, 증분 갱신 시 위치·필터·focus와 문서 기준 표시입니다. 사용자의 2026-10-04 지시에 따라 모바일 검증은 이번 범위에서 제외합니다. 완료 보고에는 실제 실행한 검사와 실제 화면 관측 범위를 남겨야 합니다.

이번 패킷은 한·영 Kit 정본과 이 문서를 수정합니다. 부모가 runtime·ZIP·정적 앱과 비공개 로컬 미리보기를 통합하고 검증합니다. 이 패킷에서 commit/push/배포, 새 외부 API·DB, 글로벌 훅·trust 변경을 수행하지 않습니다.
