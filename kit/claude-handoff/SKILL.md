---
name: handoff
description: 사용자가 핸드오프·위임·Phase 실행을 요청할 때 현재 소스 근거를 작업 패킷으로 나누고 Claude 서브에이전트 결과를 재통합한다. 일반 단일 작업에는 적용하지 않는다.
---

# Handoff — 근거를 담은 작업 위임

## 근거와 합격 기준

대상 리포에서 기존 명령, 변경 파일·심볼, 참조 구현, 금지 범위를 확인합니다.
`spec.md`와 `plan.json`은 기존 specs 위치를 따르고 없으면 `.claude/specs/<작업>/`에 둡니다.
기존 기준선과 새 기능·버그의 합격 기준을 구분합니다. 구현 전 재현 테스트는 기대한 이유로 실패할 수 있습니다.
실행하지 않은 검증을 실행했다고 기록하지 않습니다. 구현 중 근거가 바뀌면 관련 부분을 갱신합니다.

## 작업 경계

태스크마다 목표·파일 소유권·검증 기준을 둡니다. 같은 파일의 병렬 편집을 피하고 선행조건은 `depends_on`으로 표현합니다.
모델과 추론 수준은 기본 상속합니다. `model_hint`는 생략하거나 `inherit`로 둡니다.
사용자가 모델을 지정하면 그 선택을 보존합니다. 패킷 완성도나 파일 수만으로 모델을 낮추지 않습니다.

## 원래 목표와 독립 검토

Keep the user's direction distinct from an analyst proposal. Preserve the original request in one authoritative source document; `spec.md` may make it concrete. The plan requires `author`, `intent_guard.source_ref`, `requirements[{id,quote,outcome}]`, `review_ref`, and plan-level `acceptance{command,expect_exit_code}`. Each quote must be an exact substring of the source.

Before dispatch:

1. An independent reviewer reads the raw source and spec.
2. The reviewer records `reviewer`, `verdict`, both SHA-256 hashes, `requirements_covered`, `unapproved_changes`, and `evidence` in a JSON receipt.
3. Do not dispatch if there is self-review, a `blocked` verdict, stale hashes, or missing requirement coverage.
4. Repeat the review after edits that change the purpose.

The validator checks file identity, hashes, and requirement links. These checks do not prove semantic alignment or actual reviewer independence.

Every task, including investigation, maps to original requirements through `requirement_ids`; the task union must cover them all. The plan also needs an end-to-end acceptance check for the original purpose. Validate the plan and use `emit` before dispatch. Standalone `packet` validation checks structure only and is not dispatch approval.

Changing the target user, problem, unit of management, or success condition requires a new explicit user request. Continue ordinary implementation decisions autonomously. Do not add this handoff process or a new approval ceremony to a small, reversible standalone change.

## 절차 문장을 명료하게 쓸 때

패킷을 읽고 누가 무엇을 해야 하는지 판단하기 어려우면, 행위자·선행조건·행동·확인할 결과·중단 조건을 나누어 쓴다. 원문 인용, JSON 키, 명령과 기대 exit code는 그대로 유지한다. 기술 문장 명료화가 필요하고 `asd-ste100-interactive`가 설치되어 있으면 병용할 수 있다. 문장을 다듬어도 독립 검토나 실제 인수 검증을 대신하지 않는다.

## 검증과 디스패치

`python3 ~/.claude/skills/handoff/validate.py plan <plan.json>`으로 구조를 확인하고,
`emit <plan.json> <task_id>`로 작업 프롬프트를 만듭니다. ERROR는 고치고 WARN은 근거를 읽고 판단합니다.
현재 Agent 도구의 계약에서 실제 도구 제한·동시 실행 한도·턴 제한을 확인합니다. 패킷의 목록만으로 강제된다고 보지 않습니다.
독립 작업에 필요한 근거를 제공하고 불필요한 전체 대화는 복제하지 않습니다.

기존 spec 인수 절에서 `요구 원문 → 사용자가 답할 질문 → 필요한 데이터·출처 → 결과물과 행동 → 확인 방법`을 연결합니다. UI는 실제 화면·상호작용, CLI/API는 해당 실행 경로로 확인합니다. 세부 작업 기준은 공통 자율 작업 절차를 따릅니다.

## 재통합

`result <result.json> --plan <plan.json>`으로 반환 계약을 검사합니다.
완료 주장 대신 실행 결과·변경 파일·미충족 기준을 확인하고, Phase의 `exit_check`와 통합 결과를 상위 작업자가 확인합니다.
상위 작업자는 하위의 검사 PASS를 범위 밖의 제품 인수로 승격하지 않으며, 통합 후 사용자가 실패를 지적한 경로를 직접 확인합니다. 검토자/상위 평가와 실제 사용자 수락을 구별합니다.
실패 원인에 맞춰 패킷·접근을 보강합니다. 같은 접근의 반복 제한을 가능한 독립 작업의 종료 이유로 쓰지 않습니다.
되돌리기 어려운 실행은 현재 요청에서 승인된 범위 안에서 처리합니다.

설치·변경 확인은 `validate.py selftest`로 수행합니다.
