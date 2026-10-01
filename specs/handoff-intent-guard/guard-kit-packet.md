# 작업 지시: guard-kit
# 목표(전체): Strengthen handoff against product goal drift, publish updated Kit and leave central AI PMS continuation
# 근거 문서: $HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/handoff-intent-guard/spec.md  ← 필요한 부분만 읽는다
# 디스패치 설정: fork_turns="none", 모델·reasoning_effort 옵션 생략(부모 설정 상속; 사용자 override 우선)

아래 패킷대로만 작업한다. 패킷 밖의 파일을 만들거나 고치지 않는다.

```json
{
  "task_id": "guard-kit",
  "kind": "implement",
  "phase": "p1",
  "depends_on": [],
  "objective": "Publish bilingual intent guard guidance and enforce Kit export coverage",
  "done_when": [
    "Both handoff guide languages explain source anchoring independent review and original-purpose acceptance",
    "Bundle checker requires guard module and valid example receipts for both platforms"
  ],
  "acceptance": {
    "command": "python3 -m py_compile .claude/harness/build/current_content.py .claude/harness/build/check_current.py",
    "expect_exit_code": 0
  },
  "edit_points": [
    {
      "path": "$HOME/.claude/harness/build/current_content.py",
      "symbol": "PAGES/validate",
      "what": "Publish bilingual intent guard guidance and enforce Kit export coverage"
    },
    {
      "path": "$HOME/.claude/harness/build/check_current.py",
      "symbol": "PAGES/validate",
      "what": "Publish bilingual intent guard guidance and enforce Kit export coverage"
    }
  ],
  "files_to_create": [],
  "reference_impl": {
    "path": ".agents/skills/handoff/validate.py",
    "why": "Preserve existing stdlib schema/selftest/emit pattern and tool-specific contracts"
  },
  "already_tried": [
    {
      "what": "Inspected current handoff validators, schemas, Kit canonical generator and global rules",
      "result": "Current validators do not anchor source intent, independent review or original-purpose acceptance"
    }
  ],
  "context": {
    "spec_ref": "$HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/handoff-intent-guard/spec.md",
    "facts": [
      "Stage protected global skill changes; do not edit live .agents or .codex paths. User explicitly authorized Kit deployment; parent executes after review."
    ],
    "files": [
      "$HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/handoff-intent-guard/requested-change.md",
      "$HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/handoff-intent-guard/spec.md",
      ".claude/harness/build/BUILD.md"
    ],
    "excluded": "Product UI expansion, live config/hooks, new DB/API/infra, existing tests deletion, deploy by subagents"
  },
  "constraints": {
    "must": [
      "Follow spec; preserve existing tests; write result-schema JSON $HOME/Documents/Codex/2026-09-30/ai-pms-research/specs/handoff-intent-guard/guard-kit-result.json"
    ],
    "must_not": [
      "No live protected package installs or deployment; only assigned staged/core or canonical doc files"
    ]
  },
  "tools_allowed": [
    "exec_command",
    "apply_patch"
  ],
  "budget": {
    "max_turns": 40
  },
  "on_failure": {
    "retry": 1,
    "partial_ok": false,
    "escalate_to": "main"
  }
}
```

반드시 아래 JSON 하나만 출력한다(설명 금지). done_when_check 는 위 done_when 과 1:1 개수로 맞춘다. acceptance.command 를 실제로 실행하고 그 exit_code 와 마지막 출력을 acceptance_run 에 담는다. 지키지 못한 제약은 unmet_constraints 에 적는다 — 비어 있다고 거짓말하지 않는다.
{"task_id":"guard-kit","status":"complete|partial|failed","files_changed":[{"path":"","action":"modified","summary":""}],"acceptance_run":{"command":"","exit_code":0,"output_tail":""},"done_when_check":[{"condition":"","met":true,"evidence":""}],"unmet_constraints":[],"confidence":0.0,"notes_for_orchestrator":""}
