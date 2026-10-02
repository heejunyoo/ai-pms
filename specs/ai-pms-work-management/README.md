# 사람·목표·Phase·작업 관리

관리자는 사람을 선택해 담당 프로젝트 목적과 책임 작업을 확인하고, Phase별 남은 작업과 구체적인 개입 요청으로 내려갑니다. 실행·MCP·문서 기록은 해당 작업을 설명하는 근거입니다. 공개 화면은 합성 샘플이며 실제 PC 자동 수집은 후속 범위입니다.

## 입력과 사용 순서

1. Kit ZIP의 `activity/catalog-work.template.json`에 프로젝트 ID·사용자/환경·목표·명시적인 검사 대상 파일을 설정합니다. 기존 no-work v3도 읽지만 원자화 작업 진척은 미관측으로 표시합니다.
2. 기존 Kit Handoff `plan.json`을 로컬 `management_recorder.py ... handoff`로 가져옵니다. Phase·작업·의존성·완료 조건과 task/phase/project 검사 계획을 보존합니다. 결과 파일의 complete/pass는 선언 근거입니다.
3. `run --test-plan <id>`로 계획에 연결된 명령을 실행합니다. 실행 대상 manifest와 종료 코드를 영수증에 남깁니다. 작업 시작/막힘·사람의 판단은 명시적 기록을 사용합니다.
4. `portfolio.py`로 catalog와 중앙 로그를 읽어 정규화 snapshot 또는 자기완결 HTML을 만듭니다. 중앙 생성기와 브라우저는 검사 명령을 실행하지 않습니다.
5. JSON을 대시보드에 붙여넣습니다. 사람 → 담당 프로젝트 → Phase → 작업 → 완료 조건·검사·산출물·판단 근거를 확인합니다. 관리 개입에서 결정할 항목과 다음 행동을 확인합니다.

```sh
python3 specs/ai-pms-dashboard/portfolio.py --help
python3 scripts/build_dashboard_app.py
python3 specs/ai-pms-work-management/verify_work.py
```

Kit의 정확한 명령은 [activity README](../../kit/activity/README.md), 필드는 [JSON 설명](../../docs/json-contracts.md), 동작 정의는 [구현 명세](spec.md)에 있습니다. research 원본에는 Kit 별도 폴더가 없으며 canonical은 `~/.claude/harness/activity/`입니다.

## 완료와 분모

필수 작업 수는 현재 선언한 계획 기준입니다. 추가/변경된 계획의 버전과 이유를 기록합니다. 선택 작업은 총 작업에 표시하되 필수 완료 분모에 포함하지 않습니다. 선행 작업으로 참조된 선택 작업도 그 후속 작업의 착수·완료를 막을 수 있습니다. 필수 작업 완료 수는 노력·생산성·사업 성과의 비율이 아닙니다.

작업 완료는 현재 계획 이후의 해당 인수 검사, 현재 파일 manifest, 충족된 선행 작업과 필요한 사람 승인을 함께 확인합니다. 모든 선언 Phase가 필수 작업과 단계 종료 검사를 충족하고 프로젝트 전체 검사가 통과해야 프로젝트를 닫습니다. 작업 누락 Phase, 담당자/완료 기준 누락, 선언 결과, 미래 기록, 충돌, 오래된 검증이나 승인은 완료 근거가 아닙니다.

사람 필터는 담당 작업 수와 프로젝트 전체 수를 구분합니다. 같은 공동 프로젝트가 사람별로 복제되지 않습니다. 사람 승인은 가져온 기록이며 로그인된 승인자의 신원을 인증하는 기능은 아닙니다. manifest에 포함하지 않은 파일, 목표 분해의 적절성, 실제 사업 성과는 사람이 검토해야 합니다.

## 검증 범위

`verify_work.py`는 모델·UI import parity·Kit·실제 로컬 subprocess 흐름을 검사합니다. 브라우저/공개 경로는 별도 관측 기록입니다. `--release`는 현재 소스와 최종 독립 검토·공개 릴리스 영수증을 대조합니다. 저장된 해시는 새 브라우저 검증이 아닙니다. 이전 릴리스 문서는 당시 기능의 이력입니다.

외부 설계 참고: [Atlassian WBS](https://www.atlassian.com/work-management/project-management/work-breakdown-structure), [Linear milestones](https://linear.app/docs/project-milestones), [Paperclip core concepts](https://github.com/paperclipai/paperclip/blob/master/docs/start/core-concepts.md). 구조를 참고했으며 이 제품들의 운영·성능을 검증한 것은 아닙니다.
