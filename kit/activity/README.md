# Harness Activity / AI PMS workflow kit

Local tools for carrying one explicit work cycle from a chosen phase and scope, through evidence and a review decision, into a concrete next Agent task. Python 3 standard library only; the viewer works offline.

## Try the workflow / 작업 흐름 시작

Open `viewer.html`. Choose **New project** to start without existing logs, or explicitly select `example-project.jsonl` to inspect the synthetic example. The example is fictional; it is not a log from a real account or project.

1. **Set the basis:** write the goal, included and excluded scope, phase name, and finish conditions. The viewer creates opaque project, phase, and baseline IDs while retaining the human text.
2. **Record changes and evidence:** add decisions with reasons, then register artifact versions and their checks or acceptance status. A decision records an addition or removal; it does not silently rewrite the selected baseline. Create a new baseline revision when the approved scope changes.
3. **Choose what carries forward:** explicitly select the baseline for the next task and confirm that it applies. Review the linked decision reasons and exact artifact versions. A recorded check or acceptance is a declared record, not independent proof that the artifact works.
4. **Hand off:** enter the next task and its acceptance conditions, then download the Markdown Agent packet. It contains the selected goal, scope, phase, finish conditions and only the relevant linked evidence. It is not sent to an Agent automatically.
5. **Save the project record:** download the project's full JSONL separately. New entries stay in browser memory until saved; unsaved changes are lost when the page closes. Reimport the saved JSONL to continue later.

The packet is a task brief, while project JSONL is the durable event record. Keep both when the next Agent needs context and future review needs history. Select artifact files only when you want a plain-text preview; previewed content is not uploaded, stored, or verified as the registered artifact version.

## Install the logger / 기록기 설치

Copy the exported `activity/` files to `~/.agents/harness-activity/`. Keep `logger.py`, `test_logger.py`, `viewer.html`, `README.md`, and `example-project.jsonl` together. Merge the command entries from your provider's setup guide into its existing hook configuration; preserve existing safety checks and settings. No account, hook configuration, or project log is included in this package.

```sh
python3 "$HOME/.agents/harness-activity/logger.py" hook --source codex
python3 "$HOME/.agents/harness-activity/logger.py" hook --source claude
python3 "$HOME/.agents/harness-activity/test_logger.py"
```

These commands consume provider JSON on stdin. Supported native names are SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop, SessionEnd; Claude also supplies PostToolUseFailure, SubagentStart, SubagentStop. Codex SubagentStop installation is deferred until its required stdout response is supported. Cursor/Gemini adapters are deferred. A passing stdin test does not prove that an installed app delivered a hook.

## Schema v1 / 스키마 v1

The logger schema is unchanged. Each JSONL event has the same fixed top-level fields, nullable correlation IDs, allowlisted `data`, and explicit `links`. `project.baseline` needs `phase_id` and `baseline_version`; `decision.recorded` also needs `decision_id`; artifact, check and acceptance records retain exact artifact/version links. The synthetic example uses only schema-v1 fields and labels its declared events as synthetic. Do not add workflow fields to the event contract; the viewer derives its workflow from the existing records.

An automatically logged project uses the logger's local cwd index, while a project created in the viewer gets its own UUID. To link them, either import the existing hook JSONL before adding baselines, or deliberately pass the viewer project's saved `project_id` to the logger's `hook --project-id` option. They do not join automatically.

An event's source and authority matter: native hook observations are observed; manually authored records are declared. Missing native IDs stay missing. Stop, successful tool calls, checks, and declared acceptance never imply that a project is complete.

## Privacy and limits / 개인정보와 한계

Default logs are daily JSONL files under `~/.local/state/harness-activity`; the local project index contains paths and is private. Share only project records you selected and reviewed. Never add private logs, credentials, local configuration, or personal paths to a public export. Explicit text is screened for common secrets and absolute paths, but the heuristic cannot detect every sensitive phrase.

The current kit provides local project authoring, explicit baseline selection, declared decisions and evidence, version-linked review, a downloadable next-task packet, and a separate full-record export. The viewer has no server or external transmission. Closing it discards unsaved edits.

Planned product work includes central sync, reliable automatic capture of decision semantics, and frame-specific planning views such as WBS, Gantt, and wireframes. These are future boundaries, not current capabilities. No semantic inference, project synchronization, or automatic task execution is claimed.

## 실무 흐름

`viewer.html`에서 기록 없이 새 프로젝트를 시작하거나 예시 파일을 직접 선택할 수 있습니다. 목표·포함/제외 범위·단계·완료 조건을 입력하고, 변경 판단은 이유와 함께 별도 기록합니다. 결과물은 버전별 검사·수락 상태와 연결해 검토합니다. 다음 Agent 작업에 적용할 기준을 직접 선택하고 확인한 뒤, 다음 작업 및 수락 조건을 입력해 Markdown 패킷을 받습니다. 프로젝트 JSONL 저장은 별도 동작입니다.

기준 변경 결정은 기존 기준을 자동 수정하지 않습니다. 변경된 범위가 승인되면 새 기준 버전을 기록하세요. 결정·검사·수락은 선언된 기록이며 실제 산출물 검증과 구분됩니다. 선택한 파일 미리보기 역시 등록된 버전과 일치함을 증명하지 않습니다. 패킷은 자동 전송되지 않습니다.


## MCP 연결 근거 v2 (오프라인)
MCP `mcp__server__tool` hook은 v2 `data.connection`에 안전한 이름과 호출 상태만 기록합니다. 일반 hook/명시 기록 v1은 그대로 지원합니다. Pre/Post는 각각 관측이며 완료 실행 두 건을 뜻하지 않습니다. 실제 데이터베이스 접근이나 산출물 활용을 추론하지 않습니다.

선택 `pms_metadata`는 정확히 `operation`, `resources`, `artifact_refs`만 받습니다. operation은 read/write/delete/unknown; resources는 최대32개 `{id,kind,label,evidence}`, kind는 database/document/repository/api/file/unknown, evidence는 declared/input/output입니다. artifact_refs는 최대32개 `{id,version}`의 명시적 참조입니다. URL·경로·SQL·비밀정보·원본 입력/출력은 금지합니다. 잘못된 메타데이터는 누락 표시와 함께 버립니다.

`hook --resource-map reviewed-map.json`은 로컬 검토한 raw tool name → 위 metadata 객체를 사용하며 모든 resource evidence를 declared로 강제합니다. 기본은 미설치이며 외부 통신은 없습니다. 도구 성공은 데이터 감사 증거가 아닙니다. duration_ms는 hook이 제공한 0..86400000 정수만 기록합니다. actor/environment 귀속은 중앙 manifest에서 유지합니다.
