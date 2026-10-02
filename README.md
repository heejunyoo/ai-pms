# AI PMS

**문서 업데이트: 2026-10-02 · 사람·목표·Phase·원자화 작업 관리**

관리의 기준은 각 사람의 책임 작업입니다. 사람을 선택하면 여러 프로젝트의 목적과 담당 작업을 보고, 프로젝트에서 Phase·작업·의존성·완료 조건·검증 근거를 확인합니다. 첫 화면의 관리 개입 목록은 검증 실패·선행 작업 대기·검토 요청·담당자/기준 누락을 다음 행동과 연결합니다. 한 프로젝트에 여러 사람이 참여할 수 있습니다.

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

각 PC에서 자동 수집하는 연결은 후속 과제입니다. 공개 앱은 합성 샘플을 보여주는 정적 앱이며 실제 다중 PC 전송·앱 훅 전달의 증거로 사용하지 않습니다. 수신·재시도 구현은 `specs/ai-pms-transport`에 포함되며 현재 샘플 앱에는 연결하지 않았습니다.

## 관리 화면 정보 구조

사람 범위를 선택한 뒤 판단이 필요한 작업과 프로젝트 목표를 확인하고, 단계별 책임 작업에서 검증 근거를 펼치는 구조입니다. 토스 공개 디자인 원칙을 PMS에 맞게 적용했습니다. [정보 구조와 적용 범위](specs/ai-pms-toss-ia/README.md)를 참고하세요.
