# 작업 지시: workflow-ui
# 목표(전체): Implement practical AI PMS first work cycle: chosen phase and scope -> decision/evidence -> concrete next Agent work packet
# 근거 문서: $HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/ai-pms-workflow/spec.md  ← 필요한 부분만 읽는다
# 디스패치 설정: fork_turns="none", 모델·reasoning_effort 옵션 생략(부모 설정 상속; 사용자 override 우선)

아래 패킷대로만 작업한다. 패킷 밖의 파일을 만들거나 고치지 않는다.

```json
{
  "task_id": "workflow-ui",
  "kind": "implement",
  "phase": "p1",
  "depends_on": [],
  "objective": "Implement scope-to-next-Agent offline work cycle with first-visit clarity",
  "done_when": [
    "New project and scope decision forms generate privacy-safe v1 records without CLI",
    "Selected baseline, exact evidence and user next task generate concrete Markdown packet",
    "Offline plain-text artifact review and full-project record save preserve declared status"
  ],
  "acceptance": {
    "command": "python3 .claude/harness/activity/check_viewer.py",
    "expect_exit_code": 0
  },
  "edit_points": [
    {
      "path": ".claude/harness/activity/viewer.html",
      "symbol": "validate/renderReview/projects",
      "what": "Implement scope-to-next-Agent offline work cycle with first-visit clarity"
    },
    {
      "path": ".claude/harness/activity/check_viewer.py",
      "symbol": "main",
      "what": "Implement scope-to-next-Agent offline work cycle with first-visit clarity"
    }
  ],
  "files_to_create": [],
  "reference_impl": {
    "path": ".claude/harness/activity/viewer.html",
    "why": "Use existing inline offline UI or canonical stdlib build pattern"
  },
  "already_tried": [
    {
      "what": "Read current sources and ran check_viewer.py",
      "result": "Existing offline import/practitioner checks passed; no project authoring or executable next-work context UI"
    }
  ],
  "context": {
    "spec_ref": "$HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/ai-pms-workflow/spec.md",
    "facts": [
      "User wants continued product implementation through lower model handoff; no lengthy reports. Only assigned files may change."
    ],
    "conventions": [
      "Self-contained offline Korean UI; stdlib; v1 JSONL unchanged; no external resources"
    ],
    "files": [
      ".claude/harness/activity/viewer.html",
      ".claude/harness/activity/check_viewer.py",
      ".claude/harness/activity/logger.py"
    ],
    "excluded": "Live hooks/accounts, backend/API, DB, deployment, unrelated files"
  },
  "constraints": {
    "must": [
      "Read full spec and write result-schema conforming $HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/ai-pms-workflow/workflow-ui-result.json"
    ],
    "must_not": [
      "Do not modify files outside assigned scope, change logger schema, install deps or bypass browser URL rejection"
    ]
  },
  "tools_allowed": [
    "exec_command",
    "apply_patch"
  ],
  "budget": {
    "max_turns": 35
  },
  "on_failure": {
    "retry": 1,
    "partial_ok": false,
    "escalate_to": "main"
  }
}
```

반드시 아래 JSON 하나만 출력한다(설명 금지). done_when_check 는 위 done_when 과 1:1 개수로 맞춘다. acceptance.command 를 실제로 실행하고 그 exit_code 와 마지막 출력을 acceptance_run 에 담는다. 지키지 못한 제약은 unmet_constraints 에 적는다 — 비어 있다고 거짓말하지 않는다.
{"task_id":"workflow-ui","status":"complete|partial|failed","files_changed":[{"path":"","action":"modified","summary":""}],"acceptance_run":{"command":"","exit_code":0,"output_tail":""},"done_when_check":[{"condition":"","met":true,"evidence":""}],"unmet_constraints":[],"confidence":0.0,"notes_for_orchestrator":""}
