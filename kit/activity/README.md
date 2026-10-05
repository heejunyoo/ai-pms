> **PMS 범위 / PMS scope:** Harness Kit은 로컬 훅 기록기를 제공합니다. 중앙 PMS 대시보드·수신기·송신기 도입은 [GitHub 도입 가이드](https://github.com/heejunyoo/ai-pms/blob/main/docs/adoption.md)를 따르세요. Kit ZIP에는 중앙 `pms/` runtime이 없습니다. 기존 오프라인 뷰어와 수동 기록 도구는 선택적 로컬 참고 도구입니다. / Kit provides local hook capture; full PMS adoption belongs to the GitHub guide. Optional offline reference tools do not install or operate a central service.

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

Copy the exported `activity/` files to `~/.agents/harness-activity/`. Keep `logger.py`, `connectivity.py`, `test_logger.py`, `viewer.html`, `README.md`, and `example-project.jsonl` together. Merge the command entries from your provider's setup guide into its existing hook configuration; preserve existing safety checks and settings. No account, hook configuration, or project log is included in this package.

```sh
python3 "$HOME/.agents/harness-activity/logger.py" hook --source codex
python3 "$HOME/.agents/harness-activity/logger.py" hook --source claude
python3 "$HOME/.agents/harness-activity/test_logger.py"
```

These commands consume provider JSON on stdin. Supported native names are SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop, SessionEnd; Claude also supplies PostToolUseFailure, SubagentStart, SubagentStop. Codex Stop/SubagentStop now return JSON `{}` on stdout on both success and fail-open failure, as required by the Codex hook response contract. Cursor/Gemini adapters are deferred. A passing stdin test does not prove that an installed app delivered a hook.

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

## Central management v3 / 중앙 관리 기록 v3

The central dashboard manages multiple users' persistent projects. The retained `viewer.html` is a personal offline reference. Local management JSON is separate from the logger's unchanged v1/v2 event contract. It is either one catalog project object with `management` or a v3 catalog (`version: 3`, `projects: [...]`); select exactly one catalog project with `--project-id`.

Copy `management_recorder.py`, `test_management_recorder.py`, and the identical portable `management.py` together. Start from the supplied v3 template and field guide, review the project identities and criteria, and explicitly list the artifact/test files. Python 3.11+ and POSIX file locking are required. These tools do not install hooks or send data.


For a runnable **synthetic smoke check** without manually calculating hashes, create a fresh project directory and copy the template as `management.json`. Leave its `example-project` criterion and identities intact for this smoke check; replace them with reviewed real requirements before using it for real work. The import creates a new test-plan version with actual file hashes. It does not execute the test.

```sh
mkdir -p ./my-project/checks
cp ~/.agents/harness-activity/catalog-v3.template.json ./my-project/management.json
printf '%s\n' '# Synthetic artifact only' > ./my-project/app.py
cat > ./my-project/checks/acceptance.py <<'PYTEST'
assert sum((1, 2)) == 3
PYTEST
cat > ./my-project/handoff-plan.json <<'JSONPLAN'
{"goal":"Synthetic smoke check only", "spec_ref":"smoke-source.md", "intent_guard":{"source_ref":"smoke-source.md","requirements":[{"id":"smoke-req","quote":"Verify synthetic local smoke behavior."}]}, "tasks":[{"task_id":"smoke","requirement_ids":["smoke-req"],"acceptance":{"command":"python3 checks/acceptance.py","expect_exit_code":0},"context":{"excluded":"Real product and provider behavior are not checked."}}]}
JSONPLAN
python3 ~/.agents/harness-activity/management_recorder.py \
  --project ./my-project --management management.json --project-id example-project \
  handoff --plan handoff-plan.json --plan-id implementation --version v2 \
  --reason 'Synthetic smoke-plan import; real behavior remains unverified.' \
  --test-file checks/acceptance.py \
  --actor-id ExampleUser --environment-id example-laptop --session-id smoke-session
python3 ~/.agents/harness-activity/management_recorder.py \
  --project ./my-project --management management.json --project-id example-project \
  run --test-plan handoff-smoke --version v2 \
  --actor-id ExampleUser --environment-id example-laptop --session-id smoke-session
```

The following commands show the same workflow after replacing the example identities and test-plan IDs with reviewed real ones:

```sh
python3 ~/.agents/harness-activity/management_recorder.py \
  --project ./my-project --management management.json --project-id my-project \
  run --test-plan acceptance --version v1 \
  --actor-id Alice --environment-id laptop --session-id session-1 \
  --environment local --timeout 300
python3 ~/.agents/harness-activity/test_management_recorder.py
```

`--project` must name a project directory, never HOME or the filesystem root. All management, Handoff and manifest filenames are normalized project-relative paths; `..`, absolute paths and symlinks escaping the project are rejected. The recorder validates mapped actor/environment and session identities before execution. It invokes the reviewed criterion command with `shlex` argv and `shell=False`, with stdin/stdout/stderr discarded and a timeout. Shell operators and environment expansion are not evaluated; use a checked project script for multi-step tests.

Only the explicitly listed artifact files are hashed. Coverage of that manifest is a user declaration, not proof that every relevant workspace file was included. Test-plan file hashes must match actual bytes before a test runs; changes require an explicit new test-plan version with a reason. The attempt retains the pre-run artifact hash. The management artifact gets actual post-run hashes. A changed artifact makes that receipt stale/unknown; it cannot establish current completion. Older attempts and signed plans are retained. If a file disappears after execution, the original management file is preserved and a safe separate `.ai-pms/receipt-*.json` is written. No raw output is stored. Runner provenance means this local process executed the command, not an external signature or assurance against fabricated JSON. Timeout/start failures retain exit_code=null and cannot pass even if a criterion expects124/127. The CLI returns the actual completed test exit code when available, `1` for interrupted/unstarted tests, `2` for recording errors; optional graph failure never replaces a test result.

```sh
python3 ~/.agents/harness-activity/management_recorder.py \
  --project ./my-project --management management.json --project-id my-project \
  handoff --plan handoff-plan.json --result handoff-result.json \
  --plan-id implementation --version v2 --reason 'Revised acceptance for the stated requirement.' \
  --test-file checks/acceptance.py \
  --actor-id Alice --environment-id laptop --session-id session-1
```

The helper seeds requirements from `intent_guard.requirements` with source references, plan/version/reason and versioned test plans from task acceptance. Each acceptance command/expected code must match exactly one existing project criterion; review the criteria first. Result `acceptance_run` is imported only as `provenance: declared`, even if it says complete or reports exit0. It never becomes an observed runner or current completion. Raw result `output_tail` is not copied. For real evidence, execute the matching test plan with `run`.

### Optional project Graphify wrapper / 선택적 프로젝트 그래프

Add `--graph` to `run`, or use the standalone `graph` subcommand after reviewing the project and installing Graphify separately. This is an opt-in project wrapper invocation suitable for an explicitly approved project-local hook; no global hook is installed or changed here.

```sh
python3 ~/.agents/harness-activity/management_recorder.py \
  --project ./my-project --management management.json --project-id my-project \
  graph --timeout 300
```

The wrapper invokes only `graphify extract <project> --code-only --no-cluster`, rejects HOME and a HOME git root, and rejects escaping output symlinks. It logs safe generator version when exposed, source revision/hash/time and generated/failed status into `management.graphs` and `.ai-pms/graphs.jsonl`. Failed generation does not block a test. A matching manifest/revision/version and validated graph file with a matching recorded digest can reuse a prior graph. Exit zero requires a newly written graph.json with valid nodes/edges and resolved endpoints; missing, corrupt or dangling artifacts are failed evidence. Freshness is current/stale/unknown; changed source hashes require revalidation. The hash covers the declared artifact manifest. An AST graph proves neither runtime integration nor test coverage. Semantic extraction, network APIs and automatic global installation are excluded.

회사 목표와 결과/작업 위임, 개인 프로젝트는 함께 관리하되 개인 프로젝트에 회사 목표 연결을 강제하지 않습니다. 테스트 계획에는 요구사항·계획 버전·설계 이유·제외 범위·파일 해시를 남깁니다. 실제 실행과 Handoff 결과 선언을 나누고, 산출물 또는 검사 정의가 바뀌면 과거 통과를 현재 완료로 승격하지 않습니다. 회사의 업무 성과는 기술 검사 통과와 별개로 **미관측**입니다.

막힘은 원인 가설/확정, 담당자, 다음 행동과 시도를 명시적으로 연결합니다. 개선 제안은 rule/harness/loop/skill/mcp 영역과 변경 버전, 근거/검증 시도를 기록하며 검증이 없으면 효과 미관측으로 남깁니다. 비활동 시간으로 막힘을 추정하거나 자동 생산성 점수를 만들지 않습니다. 그래프는 선택적 로컬 AST 근거입니다. 전역 훅·trust·원격 sender는 변경하지 않고, 공개 자료에는 합성 기록만 사용합니다. 실제 로그는 개인정보 검토 후 선택적으로 공유하세요.

Graphify 0.9.69의 실제 code-only 검사에서 외부 import를 가리키는 edge에 대응 node가 빠지는 경우를 확인했습니다. 이 경우 그래프를 성공으로 승격하지 않고 failed로 기록합니다. 검사 실행은 계속됩니다. 외부 의존성까지 분석하려면 생성기의 노드/edge 정합성을 보완한 뒤 다시 생성해야 합니다. 코드 구조의 부분 결과를 전체 런타임 근거로 사용하지 않습니다.

### 변경 체크포인트 · 판단 · 인계 · 기록 범위 / Traceability

Optional `management.traceability` connects code checkpoints, explicit decisions and alternatives, session handoff usage, and reported capture coverage. Existing v3 records without this object still work. It does not change technical completion criteria. Keep the four arrays `checkpoints`, `decisions`, `handoffs`, `capture`; the supplied field guide defines every field.

```sh
python3 ~/.agents/harness-activity/management_recorder.py \
  --project ./my-project --management management.json --project-id my-project \
  checkpoint --actor-id Alice --environment-id laptop --session-id session-1 \
  --agent-id codex --attempt-id attempt-reviewed --decision-id decision-reviewed \
  --summary 'Checkpoint for the reviewed requirement and matching test receipt.'
python3 ~/.agents/harness-activity/management_recorder.py \
  --project ./my-project --management management.json --project-id my-project \
  record --kind decision --record decision.json
python3 ~/.agents/harness-activity/management_recorder.py \
  --project ./my-project --management management.json --project-id my-project \
  record --kind handoff --record handoff-usage.json
python3 ~/.agents/harness-activity/management_recorder.py \
  --project ./my-project --management management.json --project-id my-project \
  record --kind capture --record capture-report.json
```

Omit optional `--attempt-id`/`--decision-id` when no matching evidence exists; repeat them for multiple references. A checkpoint reads Git HEAD, parent commits, NUL-delimited status, a binary diff against HEAD, and hashes of untracked regular files. It stores only commit identifiers and a worktree digest, never raw status/diff/file contents or commit messages. Git must cover exactly the explicit non-HOME project root; nested repositories outside that boundary and escaping/untracked symlinks are rejected. Git absent leaves commit/dirty/worktree fields null while the declared artifact manifest is still hashed. Git repositories without an initial HEAD commit are rejected; create and review the initial commit before using a Git checkpoint. The recorder compares Git fingerprints before and after observation and preserves the original JSON if they change. It never commits, stages, installs hooks, or calls a remote API.

The worktree digest covers Git's tracked diff/status and untracked regular project files; **ignored files and submodule contents are outside this coverage**. A checkpoint updates the explicitly listed artifact hashes; existing attempt links must match that exact revision and artifact hash. Git identity does not prove session authorship. Session/agent attribution is supplied by the operator and remains `provenance: declared`, even though the local command observed Git. Digests and imported JSON are not authenticated attestations.

`record` imports one exact decision, handoff, or capture object from a reviewed project-relative JSON file. Decisions preserve earlier decisions via `supersedes`, require explicit alternatives/reasons and reject cycles. Record the rationale you want to share, not private model reasoning. Handoff `usage: not_observed` stays unobserved; installing a skill, generating a packet or exporting a log never changes it to observed. Declared/observed usage requires a timestamp and concrete evidence; imported observed evidence is still not authenticated execution. Capture status is a historical source report with capabilities, observation time and reason, not a live heartbeat. Silence never establishes inactivity, completion, or unsupported tooling. All source tuples and referenced records must belong to the selected project; malformed imports preserve the original file.

변경 근거에서 목표·판단·세션·코드·검사를 이어 볼 수 있습니다. 판단 이유와 대안은 직접 작성하고, 인계 패킷을 만든 사실과 다음 세션이 실제로 사용한 근거를 구분합니다. 기록 중지·오류·미지원은 명시 보고로 남기며, 수집되지 않은 작업을 정체나 실패로 판단하지 않습니다. 자동 PC 수집·전역 훅 설치는 포함하지 않습니다.

## 사람·Phase·원자화 작업 관리 (2026-10-02)

`catalog-work.template.json`과 `json-contracts.md`를 사용합니다. `management.py`, `work.py`, `management_recorder.py`는 함께 배치합니다. 기존 v3 template의 작업 계획 생략도 지원하지만 작업 진척은 미관측입니다.

완전한 Kit Handoff 계획을 가져오면 목표·Phase·작업 ID·목적·완료 조건·의존성과 작업/단계/전체 인수 검사를 보존합니다. 담당자는 import 명령의 actor로 명시되며, 공동 작업은 catalog의 source_refs와 work.tasks.owner를 검토하여 배정합니다. 파일 범위와 인수 기준을 검토한 뒤 실제 runner를 실행하세요.

```sh
python3 management_recorder.py --project "$PMS_PROJECT" --management management.json handoff \
  --plan plan.json --plan-id implementation --version v2 --reason '검토한 현재 작업 계획' \
  --test-file checks/acceptance.py --actor-id ExampleUser --environment-id example-laptop --session-id session-1
python3 management_recorder.py --project "$PMS_PROJECT" --management management.json update \
  --task implement --state in_progress --summary '자료 연결 구현 시작' --next-action '인수 검사 실행'
python3 management_recorder.py --project "$PMS_PROJECT" --management management.json run \
  --test-plan handoff-implement --version v2 --actor-id ExampleUser --environment-id example-laptop --session-id session-1
python3 management_recorder.py --project "$PMS_PROJECT" --management management.json review \
  --task implement --reviewer ExampleUser --decision approved --summary '현재 산출물과 완료 조건을 검토했다'
```

`PMS_PROJECT`에는 실제 프로젝트 디렉터리를 지정합니다. HOME 자체는 금지합니다. 예시 task ID는 자신의 계획 ID로 바꾸세요. update는 진행 선언, review는 명시적인 판단 기록이며 사용자 신원을 인증하지 않습니다. review 명령은 현재 실제 manifest와 인수 기준/테스트 계획의 해시를 자동 연결합니다. 승인 뒤 파일·계획·기준이 바뀌면 과거 승인은 현재 완료에 사용할 수 없습니다. 원본이 잘못되거나 실행 중 파일이 바뀌면 기존 관리 파일을 보존합니다.

task의 `expect_contains`는 원문 조건을 done_when에 보존하고 사람 검토를 필수로 설정합니다. 출력 문자열을 자동 판정하는 runner는 현재 없습니다. phase/project의 출력 문자열 조건, 프로젝트 밖 cwd는 지원하지 않아 명확히 거부합니다. 명령은 shell=False이며 셸 파이프라인을 해석하지 않습니다. 필요한 검증은 프로젝트 내 명시적 스크립트로 감싸세요. 이것을 임의 종료 코드로 바꿔 성공으로 기록하지 않습니다.

기존 Phase의 문서/검사 근거가 있는 상태에서 Phase를 없애거나 기존 task 기준을 참조하는 작업을 제거하는 계획은 자동으로 마이그레이션하지 않습니다. 원본을 보존하고 명시적인 범위 정리를 요구합니다. 새 작업 계획 버전은 과거 실행을 보수적으로 재검증합니다. 완료 조건 산문의 의미와 전체 파일 범위가 충분한지는 별도 사람 검토가 필요합니다.

구형의 불완전한 Handoff 입력(Phase/원자화 작업이 없는 테스트 결과만 있는 자료)은 기존 선언 검사 import로 지원합니다. 완전한 작업 계획으로 꾸며 진행을 계산하지 않습니다. 자동 PC 전달·전역 훅·운영 인증은 설치하지 않습니다.


## Live capture health / 실시간 로컬 기록 상태

```sh
python3 ~/.agents/harness-activity/logger.py health --log-dir ~/.local/state/harness-activity
```

`capture-health.json`은 owner-only(파일0600/디렉터리0700) atomic replace로 저장합니다. 정확한 필드는 `{version:1,last_event_id,last_recorded_at,errors,last_failure_at,status,at}`이며 `status`는 observed/degraded/unknown입니다. 정상 이벤트의 append와 fsync 뒤에만 성공을 기록합니다. 오류수는 누적되고 마지막 정상 ID/시각은 실패 뒤에도 보존됩니다. 재성공은 observed로 회복하지만 오류 이력은 지우지 않습니다. 경로·actor·environment·project·raw input·비밀정보는 건강파일에 없습니다. 파일은 **logdir 기록기 전체**의 관측이며 프로젝트별 훅 건강 주장이 아닙니다. sender가 identity를 붙이는 것은 운영자의 출처 연결 선언입니다.

건강파일이 없으면 unknown입니다. 읽기 실패·손상·symlink·공유 권한은 unknown과 안전한 stderr/exit1로 표시합니다. 손상된 원본은 덮어쓰지 않습니다. 이벤트 저장은 성공했으나 건강 저장이 실패하면 `event recorded; capture health update failed`라고 stderr에 표시하며 이벤트가 소실됐다고 주장하지 않습니다. 최초 잘못된 JSON은 정상 관측이 없으므로 missing/unknown으로 남을 수 있습니다. Hook 오류는 에이전트를 막지 않도록 exit0이지만 정상 저장을 뜻하지 않습니다. manual record 실패는 exit1입니다.

지원은 [Codex hooks](https://developers.openai.com/codex/hooks), [Claude Code hooks](https://code.claude.com/docs/en/hooks)의 command-hook stdin 계약입니다. Cursor/Gemini adapter는 미지원입니다. 설정 파일·stdin 검사 통과는 실제 앱 호출 증명이 아닙니다. 실제 앱별 호출/건강파일/이벤트 ID를 확인하기 전에는 앱 커버리지와 원격 두 환경 전달은 미검증입니다. Stop은 턴 종료이며 목표 완료·SessionEnd와 구별합니다.

선택 설치 예시(기존 hooks에 검토하여 병합, 경로를 설치 위치로 변경):

```json
{"hooks":{"Stop":[{"hooks":[{"type":"command","command":"python3 ~/.agents/harness-activity/logger.py hook --source codex"}]}],"SubagentStop":[{"hooks":[{"type":"command","command":"python3 ~/.agents/harness-activity/logger.py hook --source codex"}]}]}}
```

Claude 설정에도 같은 구조에서 `--source claude`를 사용합니다. 지원 native 이름에 한하여 별도 이벤트 entry를 추가합니다. 사용자가 Codex `/hooks`에서 리뷰하고 trust를 승인합니다. 이 Kit는 전역 hooks를 설치하거나 trust를 대신 승인하지 않습니다. 중앙 sender는 별도 opt-in이며 `live/README.md`의 로컬 서비스 안내를 따릅니다. 오프라인 viewer는 자동 전달하지 않습니다.

## 사람·세션·실시간 중앙 운영

`operations.template.json`과 `json-contracts.md`에 세션 목표/인수·회사/팀 북극성·기여·수집 상태 입력을 안내합니다. [GitHub 도입 가이드](https://github.com/heejunyoo/ai-pms/blob/main/docs/adoption.md)와 저장소 루트의 `specs/ai-pms-live/README.md`에서 private 합성 파일럿과 opt-in sender를 시작하세요. Kit ZIP에는 중앙 runtime이 없습니다. 훅만으로 업무 목적을 추측하지 않으며 Handoff 관리 자료와 명시적인 session_goal 연결을 사용합니다. 전역 hook/trust 설정은 자동 변경하지 않습니다.
