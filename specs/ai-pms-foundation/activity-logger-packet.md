# 작업 지시: activity-logger
# 목표(전체): Ship common Kit event logger plus offline evidence viewer with validated local flow
# 근거 문서: $HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/ai-pms-foundation/spec.md  ← 필요한 부분만 읽는다
# 디스패치 설정: fork_turns="none", 모델·reasoning_effort 옵션 생략(부모 설정 상속; 사용자 override 우선)

아래 패킷대로만 작업한다. 패킷 밖의 파일을 만들거나 고치지 않는다.

```json
{
  "task_id": "activity-logger",
  "kind": "implement",
  "phase": "p1",
  "depends_on": [],
  "objective": "Implement portable secure common event logger and runnable integration checks",
  "done_when": [
    "Hook input produces versioned privacy-safe JSONL with stable project identity and correlation fields",
    "Explicit decisions/artifact/check records validate and never imply observed acceptance",
    "Malformed input/concurrency/privacy and failure behavior checks pass"
  ],
  "acceptance": {
    "command": "python3 .claude/harness/activity/test_logger.py",
    "expect_exit_code": 0
  },
  "edit_points": [],
  "files_to_create": [
    ".claude/harness/activity/logger.py",
    ".claude/harness/activity/test_logger.py",
    ".claude/harness/activity/README.md"
  ],
  "reference_impl": {
    "path": ".codex/hooks/safety_gate.py",
    "why": "Reuse canonical Python stdlib and Kit conventions; read spec contract before editing"
  },
  "already_tried": [
    {
      "what": "Inspected canonical build and baseline harness verify",
      "result": "Baseline passed; activity files absent so new acceptance initially fails"
    }
  ],
  "context": {
    "spec_ref": "$HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/ai-pms-foundation/spec.md",
    "facts": [
      "Shared workspace; only edit assigned files. Logger/viewer contract fully fixed in spec."
    ],
    "conventions": [
      "Python stdlib; no new packages; Korean polite UI; preserve existing Kit ko/en parity"
    ],
    "files": [
      ".codex/hooks/safety_gate.py",
      ".claude/harness/build/build_current.py"
    ],
    "excluded": "Live configs, external APIs, DB, deployment, other task files"
  },
  "constraints": {
    "must": [
      "Read spec; implement contract; return result.schema.json conforming JSON to $HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/ai-pms-foundation/activity-logger-result.json"
    ],
    "must_not": [
      "Do not edit outside assigned files or deploy/install/change live settings"
    ]
  },
  "tools_allowed": [
    "exec_command",
    "apply_patch"
  ],
  "budget": {
    "max_turns": 30
  },
  "on_failure": {
    "retry": 1,
    "partial_ok": false,
    "escalate_to": "main"
  }
}
```

반드시 아래 JSON 하나만 출력한다(설명 금지). done_when_check 는 위 done_when 과 1:1 개수로 맞춘다. acceptance.command 를 실제로 실행하고 그 exit_code 와 마지막 출력을 acceptance_run 에 담는다. 지키지 못한 제약은 unmet_constraints 에 적는다 — 비어 있다고 거짓말하지 않는다.
{"task_id":"activity-logger","status":"complete|partial|failed","files_changed":[{"path":"","action":"modified","summary":""}],"acceptance_run":{"command":"","exit_code":0,"output_tail":""},"done_when_check":[{"condition":"","met":true,"evidence":""}],"unmet_constraints":[],"confidence":0.0,"notes_for_orchestrator":""}
