# AI PMS

여러 사람이 에이전트로 만드는 프로젝트의 목표·문서·Phase·작업·검증을 한곳에서 살펴보는 중앙 관리 프로토타입입니다. 공개 화면은 가상 자료로 만든 정적 도입 예시입니다. 실제 앱 수집과 인증된 중앙 서비스는 별도로 연결해야 합니다.

**처음 다운로드했다면 [도입 가이드](docs/adoption.md)를 따라 시작하세요.** GitHub Code → Download ZIP으로 압축을 풀고 README.md가 있는 최상위 폴더에서 실행합니다. Python 3.11+와 Node.js, macOS/Linux가 필요하며 Python 외부 패키지는 없습니다.

```sh
python3 scripts/verify_adoption.py
python3 scripts/build_dashboard_app.py
python3 -m http.server 21932 --directory apps/dashboard/public --bind 127.0.0.1
```

`http://127.0.0.1:21932/`에서 샘플을 봅니다. `verify_adoption.py`는 임시 합성 자료로 다운로드의 링크·훅 stdin/health·문서 화면·인증 Live 파일럿을 검사합니다. 실제 앱 hook/trust나 원격 사용자 전달은 검증하지 않습니다. 전체 기존 회귀 검사는 `python3 scripts/verify_public.py`입니다.

| 원하는 도입 | 시작 위치 |
|---|---|
| 문서와 계획으로 내 프로젝트 보기 | [private catalog → HTML/snapshot](docs/adoption.md#2-문서만으로-내-프로젝트-보기) |
| Codex/Claude 훅 추가·수집 상태 확인 | [kit/activity와 기존 설정 병합](docs/adoption.md#3-선택한-앱의-훅-수집-연결) |
| 인증된 중앙 서비스와 sender 실행 | [루트 specs/ai-pms-live 안내](specs/ai-pms-live/README.md) |

Harness Kit의 PMS 범위는 훅 수집 안내와 `activity/` 파일입니다. GitHub에는 `kit/activity/`와 중앙 대시보드·Live 실행 소스가 함께 있습니다. Kit ZIP의 `pms/`에서 시작하지 않습니다. 기본 공개 예시는 문서를 먼저 넣은 도입 상태이며 실행·현재 검증 미관측을 유지합니다. 기존 합성 실행 기록은 [별도 실행 이력 예시](https://ai-pms-dashboard.vercel.app/recorded-example.html)에서 구분합니다. 실제 private 자료를 공개 샘플에 보내지 마세요.

**문서 업데이트: 2026-10-05 · 구성요소와 연결 도표**

전체 계획의 구성요소 도표 정렬·디자인을 보완했습니다. [최신 디자인 검증](specs/ai-pms-component-map/design-proof.json): 실제 Chrome1440×1000의 Paper/Knowledge 정렬·목표 표시·키보드 이동과 회귀 검사 통과. 공개 배포에는 아직 반영하지 않았습니다.

2026-10-04 로컬 리팩터링은 [프로젝트 화면 안내](docs/readable-project.md)와 [검증 기록](specs/ai-pms-readable-project/integration-proof.json)에 있습니다. 확인 결과는 확인한 내용·결과·다음 행동을 먼저 표시하고 원본 기록을 펼쳐 봅니다. 전체 회귀 검사와 Chrome 데스크톱 확인을 통과했으며 공개 배포는 아직 반영하지 않았습니다.

[Harness Kit와 AI PMS ELI20 전체 설명](https://ai-pms-dashboard.vercel.app/overview.html) — Kit 범위, PMS 목적·구성, 공동 작업 흐름, 구현/검증과 다음 방향을 한 주제씩 읽을 수 있습니다. [정본 및 검증](reports/harness-pms-eli20/README.md).

기본 화면은 **사람 선택 → 프로젝트 목표 → 각 Phase의 목표·달성 상태 → 참고한 API·MCP**입니다. 한 프로젝트/단계는 별도 주소에서 읽습니다. 프로젝트 상세는 모든 Phase와 원자 작업을 계층형 WBS로 보여줍니다. 검사·문서·세션 원문은 필요한 근거에서 엽니다. 단계 달성과 최종 인수는 구분합니다. 공동 프로젝트는 같은 카드에 참여자를 표시합니다.

[공동 WBS와 실행 이력](docs/visual-management.md) · [프로젝트 구조](docs/project-architecture.md). 일정 없는 계획은 단계축이며 의존성·날짜를 추측하지 않습니다. 별도 처리함에는 담당자·요청 이유·선언된 다음 행동과 출처를 표시합니다. 최신 검증 범위는 [통합 영수증](specs/ai-pms-visual-management/integration-proof.json)에서 확인합니다.

[화면과 AI 분석의 구분](docs/human-view-and-analysis.md)에는 로그별 의미, 목표 중복 제안, 반복 막힘·검증 누락·규칙 개선의 활용을 명시했습니다. 목표 비교 입력 생성기는 준비했으며 모델 분석/경고 저장은 아직 구현하지 않았습니다.

2026-10-04 변경의 공개 반영·실제 응답 일치 여부는 [공개 검증 기록](specs/ai-pms-visual-management/release-proof.json)에서 확인합니다. 실제 프로젝트 자료는 비공개 로컬에 유지합니다. 사용자 지시에 따라 모바일 검증은 이번 인수 범위에서 제외합니다.

[실행 가능한 Live Kit](specs/ai-pms-live/README.md) · [세션·북극성 JSON 템플릿](templates/operations.template.json) · [채워진 합성 예시](specs/ai-pms-live/sample/operations.json) · [최신 공개/검증 범위](specs/ai-pms-live/release-proof.json)

로컬 훅은 이벤트별 JSONL과 fsync 이후 수집 상태를 생성합니다. opt-in sender는 이벤트·프로젝트·세션 목표·지표·기여·수집 상태를 내구 outbox에서 하나씩 중앙에 전달합니다. 자체 호스팅 서비스는 인증·원문 이력·cursor 증분 조회를 제공하고 연결 화면은2초 주기로 갱신합니다. 공개 Vercel은 합성 정적 샘플입니다.

[작업 관리 안내](specs/ai-pms-work-management/README.md) · [작업 계획 포함 JSON 템플릿](templates/catalog-work.template.json) · [전체 필드 설명](docs/json-contracts.md)

기존 실행/추적 자료는 증거로 보존합니다. 이전 릴리스의 “완료”는 해당 기록 기능의 검증 범위이며, 사람 중심 관리 흐름의 인수 근거로 재사용하지 않습니다.

회사 목표·개인 위임 → 요구사항 → 계획·테스트 설계 이유 → 실제 실패·수정·통과 → 현재 산출물 검증을 연결했습니다. 막힘의 원인·도움 담당자·다음 행동, 철칙·하네스·검증 루프·스킬·MCP 개선 근거와 선택적 Graphify 최신성도 기록하고 표시합니다.

- [v3 JSON 템플릿](templates/catalog-v3.template.json): 직접 입력할 기본 구조
- [전체 JSON 필드 설명](docs/json-contracts.md): 수집·선언 항목과 근거·완료 판정의 한계
- [관리 기록기 사용법](kit/activity/README.md): Handoff 계획 가져오기, 실제 검사 실행, 선택적 Graphify
- [중앙 관리 v3 안내](specs/ai-pms-management/README.md): 입력에서 대시보드까지의 사용 순서

Kit 구현 소스 ZIP에도 `activity/catalog-v3.template.json`, `activity/json-contracts.md`, `activity/README.md`가 포함됩니다. 목표와 판단 이유는 문서·명시적 기록으로 남기며, 훅 호출 기록에서 자동으로 추측하지 않습니다.

여러 사용자가 각자 에이전트로 만드는 솔루션을 프로젝트 목표부터 문서·단계·검증·MCP와 데이터 참조까지 한곳에서 살펴보는 중앙 관리 프로토타입입니다.

- [대시보드 샘플](https://ai-pms-dashboard.vercel.app)
- [ELI20 보고서](https://ai-pms-dashboard.vercel.app/report.html)
- [Harness Kit 안내](https://harness-kit.vercel.app/ai-pms.html)

샘플은 합성 사용자와 프로젝트를 사용하며, 한 사람의 여러 프로젝트와 공동 프로젝트를 포함합니다. 같은 프로젝트의 여러 세션과 환경은 명시적으로 연결하며, 다른 사용자의 동일 ID나 MCP 별칭은 자동으로 합치지 않습니다. 작업 계획이 있는 프로젝트는 모든 선언 Phase의 필수 작업·단계 종료 검사·필요한 사람 승인·프로젝트 전체 검사가 현재 근거로 충족되어야 완료로 표시합니다. 작업 수 비율은 업무 성과나 소요 노력의 비율이 아닙니다.

MCP 화면은 설정·요청·성공·실패와 데이터 참조의 선언·입력·출력 근거를 구분합니다. 서버 성공은 내부 DB 접근 증명이 아닙니다. 훅 기록기는 입력·응답 원문, SQL, URL, 개인 파일 경로, 자격 증명을 저장하지 않습니다. 검토한 로컬 resource map과 명시적인 메타데이터만 선택적으로 반영합니다.

## 실행

Python 3.11+와 Node.js가 필요합니다. 별도 Python 패키지는 없습니다.

```sh
python3 scripts/build_dashboard_app.py
python3 -m http.server 21932 --directory apps/dashboard/public
```

브라우저에서 `http://localhost:21932`를 엽니다. 정규화된 snapshot JSON을 파일 또는 붙여넣기로 가져오고 내보낼 수 있습니다. 원격 API나 검사 명령을 실행하지 않습니다.

공개 소스 검사:

```sh
python3 scripts/verify_public.py
```

입력 모델·완료 기준은 [대시보드 안내](specs/ai-pms-dashboard/README.md), 연결 로그 계약은 [연결 명세](specs/ai-pms-connectivity/spec.md), 로컬 기록기는 [Kit 활동 기록 안내](kit/activity/README.md)를 참고하세요. [공개 경계](PUBLIC_SNAPSHOT.md)에는 제외된 개인 자료와 역사적 검증 영수증의 한계를 설명합니다.

7개 합성 writer의 실제 로컬 HTTP 전달, logger CLI→중앙 갱신, 관리 변경·손상·중복·재시작 검사를 통과했습니다. 실제 Codex/Claude 앱 훅 설치·trust, 원격 실제 두 사용자 전달과 현재 데스크톱 렌더는 별도 인수이며 모바일은 사용자 지시로 제외합니다. Cursor/Gemini native 훅 어댑터도 미지원입니다. private 중앙 서버·참여자·자격은 운영자가 정하며 실제 로그를 공개 샘플로 보내지 않습니다.

## 관리 화면 정보 구조

사람·세션 / 회사·팀 북극성 / 프로젝트 근거를 분리하고, 사람을 선택한 뒤 세션의 목표·완료 판단에서 해당 책임 작업의 검증 근거를 펼칩니다. 토스 공개 디자인 원칙을 PMS에 맞게 적용했습니다. [정보 구조와 적용 범위](specs/ai-pms-toss-ia/README.md)를 참고하세요.
