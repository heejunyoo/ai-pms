---
name: codex-improvement-loop
description: Run a scored, bounded improvement loop when the user explicitly requests an improvement loop, or when the same difficult task has already failed repeatedly and needs evidence-based retry decisions. Do not use for ordinary implementation or routine verification.
---

# Codex Improvement Loop

Use this as the control loop around a task; do not mistake it for a prompt template. Keep the task's acceptance criteria and its verifier observable.

## Loop contract

1. **Frame** — state the goal, risk boundary, acceptance criteria, and a bounded iteration budget. Follow the approach-change rule in `~/.codex/docs/autonomous_coding.md`; an iteration budget does not authorize repeating a failed approach or end independent authorized work that can still progress.
2. **Baseline** — inspect live state and run the narrowest existing verifier before changing anything.
3. **Act** — make one coherent, reversible change. Do not broaden permissions or scope merely to advance the score.
4. **Verify** — use deterministic checks first; then inspect the diff or result from an adversarial perspective. Record failures as concrete findings. Separate technical checks, product acceptance and user acceptance; follow the evidence-path boundaries in the autonomous coding procedure.
5. **Assess** — compare observed results with acceptance criteria. Use a score only when its dimensions have a meaningful measured basis; never turn file or keyword counts into a capability score.
6. **Decide** — retry only when a finding has an actionable, in-scope fix and iterations remain. Otherwise stop with a named terminal state.
7. **Record** — leave a short ledger entry: goal, iteration count, checks, observed results, findings, and terminal state.

## Terminal states

- `verified`: acceptance criteria pass and no unaddressed critical finding remains.
- `accepted-gap`: a known gap is documented with its owner or next action.
- `blocked`: progress requires missing authority, input, or an external state change.
- `iteration-limit`: the stated iteration budget ended without reaching the target; report the remaining findings.

## Harness assessment

For a Codex-harness assessment, run:

```sh
python3 ~/.codex/skills/codex-improvement-loop/scripts/score_harness_loop.py
```

The legacy command name is retained for compatibility. It now reports local configuration checks and unverified areas, without a maturity score. Absence of a global scheduler or project-specific tests is not a defect by itself.

## Scope discipline

- Put reusable control logic in this global skill; place project acceptance criteria, commands, and ledgers in the project.
- Use `codex-harness-audit` after altering global configuration or skills.
- Do not add an undocumented hook, scheduler, or plugin to simulate automation.
