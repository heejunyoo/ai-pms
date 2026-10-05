"""Bilingual setup guides and retained ELI explanations."""
import json
RELEASE = '2026-10-05'

PAGES = {'index': {'ko': ('이 운영 환경을\n다른 곳에서도.',
                  'Codex·Claude의 기본 하네스를 옮기고 적용 여부를 확인합니다. Ponytail·Graphify는 별도로 설치하고 검증합니다.',
                  [('purpose',
                    '먼저 이해하고, 그다음 옮깁니다',
                    [('무엇을 옮기나요?', '에이전트를 둘러싼 지침·스킬·훅·검증 절차입니다. 모델이나 계정 자체를 복제하는 일은 아닙니다.'),
                     ('어떤 순서로 읽나요?', 'ELI20 안내에서 용어와 실제 작업 흐름을 이해한 뒤, 사용하는 도구의 설치 안내로 이동하세요.'),
                     ('어디까지 확인하나요?', '파일 배치와 정적 검사 다음에 새 세션의 로드 상태와 실제 도구 호출·화면 결과를 확인합니다.')]),
                   ('start',
                    '적용 순서',
                    [('01 · 파일 받기',
                      '구현 소스 ZIP과 사용하는 언어의 안내 문서를 받습니다. macOS·Linux의 기본 홈 경로를 기준으로 하며 Python 3.11 이상이 필요합니다.'),
                     ('02 · 환경에 적용', 'Codex 또는 Claude 안내에 따라 파일을 배치하고 훅을 연결합니다. 기존 설정은 백업한 뒤 필요한 항목을 병합합니다.'),
                     ('03 · 새 세션에서 확인', '지침과 스킬이 로드되는지, 훅이 신뢰되고 호출되는지 확인합니다. 계정·모델·MCP 연결은 대상 환경에서 설정합니다.')]),
                   ('apply',
                    '에이전트에게 적용 요청',
                    [('아래 요청과 압축을 푼 폴더를 전달하세요',
                      '```text\n'
                      '이 폴더의 Harness Kit 안내를 읽고 현재 환경에 적용해줘.\n'
                      '사용 중인 Codex 또는 Claude의 기존 설정과 먼저 비교하고,\n'
                      '지침·훅·스킬을 백업 후 병합해줘. 계정과 프로젝트별 권한은 유지해줘.\n'
                      '포함된 검사를 실행하고 새 세션에서 확인할 항목을 알려줘.\n'
                      '적용된 항목과 추가 설정이 필요한 항목을 구분해줘.\n'
                      '```')]),
                   ('paths',
                    '도구별 안내',
                    [('Codex 구성', 'AGENTS.md, PreToolUse 훅, 스킬 경로와 확인 명령.'),
                     ('Claude 구성', 'CLAUDE.md, 안전·Stop 훅과 확인 명령.'),
                     ('공용 스킬', '스킬별 설치 위치와 호출 예시.')]),
                   ('scope',
                    '옮기는 범위',
                    [('포함', '공통 훅 코드, 스킬 정의와 보조 파일, 운영 지침 문서. ELI 설명 페이지에서 각 구성의 역할을 이해할 수 있습니다.'),
                     ('별도 설정',
                      'Ponytail·Graphify 같은 외부 도구, 로그인, API 키, MCP 연결, 모델 선택, 개인 메모리와 프로젝트 권한은 복사하지 않습니다. 같은 구성이라도 모델·도구·앱 버전에 따라 동작은 달라질 수 '
                      '있습니다.')])]),
           'en': ('Use this setup\nin another environment.',
                  'Transfer the core Codex and Claude harness, then verify it. Install and check Ponytail and Graphify separately.',
                  [('purpose',
                    'Understand first, then transfer',
                    [('What transfers?', 'The instructions, skills, hooks, and verification around an agent. This does not clone the model or account.'),
                     ('What should I read first?', 'Use the ELI20 guide to learn the terms and real workflow, then follow the setup guide for your agent.'),
                     ('What counts as verified?', 'After placing files and running static checks, inspect loading in a new session and real tool calls and interface results.')]),
                   ('start',
                    'Setup steps',
                    [('01 · Download',
                      'Get the implementation ZIP and the guide in your language. Paths assume the default home '
                      'directories on macOS or Linux. Python 3.11 or later is required.'),
                     ('02 · Apply',
                      'Follow the Codex or Claude guide to place files and connect hooks. Back up existing settings, '
                      'then merge the required entries.'),
                     ('03 · Check a new session',
                      'Confirm that instructions and skills load and hooks are trusted and invoked. Configure '
                      'accounts, models, and MCP connections in the target environment.')]),
                   ('apply',
                    'Ask your agent to apply it',
                    [('Provide this request and the extracted folder',
                      '```text\n'
                      'Read the Harness Kit guides in this folder and apply them to my environment.\n'
                      'Compare them with my existing Codex or Claude setup first.\n'
                      'Back up and merge instructions, hooks, and skills. Keep my accounts\n'
                      'and project permissions. Run the included checks and list what needs\n'
                      'verification in a new session. Separate applied items from items\n'
                      'that still need configuration.\n'
                      '```')]),
                   ('paths',
                    'Tool-specific guides',
                    [('Codex configuration', 'AGENTS.md, PreToolUse hooks, skill locations, and check commands.'),
                     ('Claude configuration', 'CLAUDE.md, safety and Stop hooks, and check commands.'),
                     ('Shared skills', 'Installation locations and example requests for each skill.')]),
                   ('scope',
                    'What transfers',
                    [('Included',
                      'Shared hook code, skill definitions and supporting files, and operating guidance. The ELI pages '
                      'explain how the components work.'),
                     ('Configure separately',
                      'External tools such as Ponytail and Graphify, logins, API keys, MCP connections, model selection, personal memories, and project permissions '
                      'are not copied. Behavior still depends on the model, tools, and application version.')])])},
 'codex': {'ko': ('Codex에 적용하기',
                  'Codex는 요청을 해석하고 도구를 호출하는 에이전트입니다. 이 페이지는 Codex 주변의 지침·안전 훅·스킬을 기존 설정과 병합하는 절차입니다. ~/.codex와 ~/.agents는 기본 경로입니다.',
                  [('agents',
                    '1. 지침과 문서 배치',
                    [('전역 지침',
                      '~/.codex/AGENTS.md에 언어, DB·배포·API 변경 등 사전 승인 범위, 검증 명령을 둡니다. 프로젝트 AGENTS.md에는 해당 리포의 실행 명령과 제약만 '
                      '둡니다.'),
                     ('운영 문서', 'codex/docs/를 ~/.codex/docs/로 옮깁니다. 확신도, 작업 절차, 메모리 정리와 그래프 사용 기준이 들어 있습니다.')]),
                   ('hooks',
                    '2. 안전 훅 연결',
                    [('파일 위치',
                      'codex/safety_gate.py를 ~/.codex/hooks/safety_gate.py로 옮깁니다. hooks.json의 PreToolUse에 matcher: '
                      'Bash|apply_patch와 해당 스크립트의 python3 실행 명령을 등록합니다.'),
                     ('검사 범위',
                      '보호 경로 기록과 테스트 삭제·무력화 패턴을 확인합니다. 문서에 적힌 셸 예시는 실행 명령으로 취급하지 않습니다. 샌드박스와 기존 승인 설정은 유지합니다.')]),
                   ('skills',
                    '3. 스킬 배치',
                    [('공용 스킬', 'handoff/와 skills/ 아래의 각 폴더를 ~/.agents/skills/로 옮깁니다. 폴더마다 SKILL.md와 보조 파일을 함께 둡니다.'),
                     ('Codex 전용',
                      'codex/skills/ 아래의 폴더를 ~/.codex/skills/로 옮깁니다. 모델과 추론 수준은 현재 세션 설정을 사용하고 Handoff는 이를 상속합니다.')]),
                   ('verification',
                    '4. 적용 확인',
                    [('구성과 Handoff 검사',
                      '```sh\n'
                      'python3 ~/.codex/skills/codex-harness-audit/scripts/check_harness.py\n'
                      'python3 ~/.agents/skills/handoff/validate.py selftest\n'
                      '```'),
                     ('새 세션',
                      '프로젝트 루트에서 세션을 열어 AGENTS.md와 스킬 목록을 확인합니다. /hooks에서 현재 훅 정의의 신뢰 상태를 확인하고, 실제 작업의 호출 기록을 '
                      '확인합니다.')])]),
           'en': ('Set up Codex',
                  'Codex is the agent that interprets requests and calls tools. This page explains how to merge instructions, a safety hook, and skills around it. ~/.codex and ~/.agents are default locations.',
                  [('agents',
                    '1. Place instructions and documents',
                    [('Global instructions',
                      'Put language preferences, approval boundaries for DB, deployment, and API changes, and check '
                      'commands in ~/.codex/AGENTS.md. Keep repository commands and constraints in the project '
                      'AGENTS.md.'),
                     ('Operating documents',
                      'Copy codex/docs/ to ~/.codex/docs/. It contains guidance for confidence, task execution, memory '
                      'curation, and graph usage.')]),
                   ('hooks',
                    '2. Connect the safety hook',
                    [('File location',
                      'Copy codex/safety_gate.py to ~/.codex/hooks/safety_gate.py. In hooks.json, add a PreToolUse '
                      'entry with matcher: Bash|apply_patch and a python3 command pointing to that script.'),
                     ('Coverage',
                      'The hook checks protected writes and test deletion or disabling patterns. Shell examples in '
                      'documentation are not treated as commands. Keep your sandbox and approval settings.')]),
                   ('skills',
                    '3. Place skills',
                    [('Shared skills',
                      'Copy handoff/ and each folder under skills/ into ~/.agents/skills/. Keep SKILL.md and '
                      'supporting files together.'),
                     ('Codex-specific skills',
                      'Copy the folders under codex/skills/ into ~/.codex/skills/. Use the current session model and '
                      'reasoning settings; Handoff inherits them.')]),
                   ('verification',
                    '4. Verify',
                    [('Configuration and Handoff checks',
                      '```sh\n'
                      'python3 ~/.codex/skills/codex-harness-audit/scripts/check_harness.py\n'
                      'python3 ~/.agents/skills/handoff/validate.py selftest\n'
                      '```'),
                     ('New session',
                      'Open a session at the project root and check AGENTS.md and the available skills. Use /hooks to '
                      'review trust for the current definition, then check invocation records during real work.')])])},
 'claude': {'ko': ('Claude에 적용하기',
                   'Claude Code는 요청을 해석하고 도구를 호출하는 에이전트입니다. 이 페이지는 Claude의 지침·안전/Stop 훅·스킬을 기존 설정과 병합하는 절차입니다. 구현 ZIP의 claude/와 claude-handoff/ 폴더를 사용합니다.',
                   [('agents',
                     '1. 지침과 문서 배치',
                     [('CLAUDE.md',
                       '~/.claude/CLAUDE.md에 언어, DB·배포·API 변경 등 사전 승인 범위, 검증 명령을 둡니다. 프로젝트 CLAUDE.md에는 리포별 정보만 둡니다.'),
                      ('운영 문서', 'claude/docs/를 ~/.claude/docs/로 옮깁니다. 기존 권한과 연결 설정은 필요한 항목만 병합합니다.')]),
                    ('hooks',
                     '2. 훅 연결',
                     [('안전 훅',
                       'claude/safety_gate.py를 ~/.claude/hooks/에 옮깁니다. settings.json의 hooks.PreToolUse에 matcher: '
                       'Bash|Edit|Write|MultiEdit와 스크립트의 python3 실행 명령을 등록합니다.'),
                      ('Stop 훅',
                       'claude/session_gate.py와 test_session_gate.py를 같은 hooks/ 폴더에 둡니다. hooks.Stop에 session_gate.py의 '
                       'python3 실행 명령을 등록합니다. 마지막 코드 편집 이후 검증 기록을 확인하며 세션당 최대 한 번 개입합니다.')]),
                    ('skills',
                     '3. 스킬 배치',
                     [('Claude 스킬',
                       'claude-handoff/를 ~/.claude/skills/handoff/로, claude/skills/의 각 폴더를 ~/.claude/skills/로 옮깁니다. 각 '
                       '폴더의 SKILL.md와 보조 파일을 함께 유지합니다.')]),
                    ('check',
                     '4. 적용 확인',
                     [('회귀 검사',
                       '```sh\n'
                       'python3 ~/.claude/hooks/test_session_gate.py\n'
                       'python3 ~/.claude/skills/handoff/validate.py selftest\n'
                       '```'),
                      ('새 세션',
                       'CLAUDE.md와 스킬이 로드되는지, /hooks에 등록한 명령이 보이는지 확인합니다. 실제 작업의 훅 호출도 확인합니다. Stop 검사는 커스텀 검증 명령이나 셸을 '
                       '통한 편집을 놓칠 수 있습니다.')])]),
            'en': ('Set up Claude',
                   'Claude Code is the agent that interprets requests and calls tools. This page explains how to merge its instructions, safety and Stop hooks, and skills with an existing setup. Use the claude/ and claude-handoff/ folders in the implementation ZIP.',
                   [('agents',
                     '1. Place instructions and documents',
                     [('CLAUDE.md',
                       'Put language preferences, approval boundaries for DB, deployment, and API changes, and check '
                       'commands in ~/.claude/CLAUDE.md. Keep repository-specific information in the project '
                       'CLAUDE.md.'),
                      ('Operating documents',
                       'Copy claude/docs/ to ~/.claude/docs/. Merge only the required entries into existing '
                       'permissions and connection settings.')]),
                    ('hooks',
                     '2. Connect hooks',
                     [('Safety hook',
                       'Copy claude/safety_gate.py into ~/.claude/hooks/. In settings.json, add hooks.PreToolUse with '
                       'matcher: Bash|Edit|Write|MultiEdit and a python3 command pointing to the script.'),
                      ('Stop hook',
                       'Place claude/session_gate.py and test_session_gate.py in the same hooks/ folder. Add a '
                       'hooks.Stop entry running session_gate.py with python3. It checks verification after the latest '
                       'observed code edit and intervenes at most once per session.')]),
                    ('skills',
                     '3. Place skills',
                     [('Claude skills',
                       'Copy claude-handoff/ to ~/.claude/skills/handoff/ and each folder under claude/skills/ into '
                       '~/.claude/skills/. Keep SKILL.md and supporting files together.')]),
                    ('check',
                     '4. Verify',
                     [('Regression checks',
                       '```sh\n'
                       'python3 ~/.claude/hooks/test_session_gate.py\n'
                       'python3 ~/.claude/skills/handoff/validate.py selftest\n'
                       '```'),
                      ('New session',
                       'Confirm that CLAUDE.md and skills load and /hooks lists the registered commands. Check hook '
                       'invocations during real work. The Stop check can miss custom verification commands and edits '
                       'made through shell.')])])},
 'skills': {'ko': ('스킬 설치와 사용',
                   '스킬은 특정 작업에 필요한 판단 기준과 절차입니다. 번들에 포함된 스킬과 별도로 설치해야 하는 도구를 구분한 뒤, 사용하는 에이전트에서 로드와 실제 동작을 확인합니다.',
                   [('handoff',
                     'Handoff',
                     [('사용할 때', '사용자가 위임·핸드오프·Phase 실행을 요청하고, 독립 검증 가능한 작업으로 나눌 수 있을 때 씁니다.'),
                      ('기본값', '부모 모델과 추론 수준을 상속합니다. 패킷 필드가 채워졌다는 이유로 low를 강제하지 않습니다.')]),
                    ('expert-panel',
                     '전문가 분석과 독립 패널',
                     [('expert-panel', '문제·가설·선택 기준을 구조화하는 단일 분석 절차입니다. 반드시 여러 에이전트를 쓰는 것은 아닙니다.'),
                      ('independent-panel', '중요한 결정에 서로 다른 책임을 가진 독립 초안과 한 번의 교차검토를 사용합니다. 다수결이나 직함으로 결론을 고르지 않습니다.')]),
                    ('eli5',
                     'ELI20 설명',
                     [('하나의 깊이',
                       '낯선 용어부터 구성요소별 책임, 연결, 실제 흐름, 조건·예외·한계와 근거까지 설명합니다. 기존 eli5 호출명은 호환을 위해 유지합니다.'),
                      ('결과 검증', '관계 탐색이 도움이 될 때 자기완결 HTML을 만듭니다. 모바일에서 상태 변화와 읽기 편한지를 확인합니다. 배포는 사용자가 요청·승인한 경우에만 합니다.')]),
                    ('asd-ste100-interactive',
                     'STE 기반 기술 문서 명료화 · 한국어와 영어',
                     [('역할', 'ELI20은 무엇을 어떤 순서로 충분히 설명할지, 이 스킬은 기술 문장을 어떻게 명확하게 쓸지 담당합니다. 별도 스킬로 필요할 때 함께 씁니다.'),
                      ('한국어 모드', '주체·지시어·용어·행동 순서를 명확히 하되 조건·예외·부정·수치와 의무의 강도를 유지합니다. 영어 단어 수와 승인 사전은 적용하지 않습니다. 공식 한국어 STE 표준이 아닌 자체 가이드입니다.'),
                      ('설치', '구현 ZIP의 skills/asd-ste100-interactive/ 폴더 전체를 Codex에서는 ~/.agents/skills/ 또는 ~/.codex/skills/에, Claude에서는 ~/.claude/skills/에 배치합니다. 같은 환경의 두 경로에 중복 설치하지 말고 기존 폴더는 백업 후 병합하세요.'),
                      ('호출 예시', '$asd-ste100-interactive로 이 한국어 문서를 의미와 예외를 유지하면서 다듬어줘. ELI20 병용: $eli5와 $asd-ste100-interactive를 함께 써서 원리와 조건을 충분히 설명해줘.'),
                      ('직접 탐색과 검증', '스킬의 assets/korean-writing-explorer.html은 한국어 유형별 예시와 검토 후보를, asd-ste100-explorer.html은 영어 STE 구조와 설정을 보여줍니다. HTML을 브라우저에서 여세요. 한국어 도구의 표현 탐지와 문장 길이는 참고용이며, 의미 보존·안전성·공식 준수를 자동 판정하지 않습니다. 영어 사전 승인도 공식 자료로 별도 확인합니다.')]),
                    ('optional-tools',
                     '선택 설치 · Ponytail과 Graphify',
                     [('Ponytail', '코딩 작업의 불필요한 구현을 줄이는 외부 플러그인입니다. ZIP에 포함되지 않습니다. Codex: codex plugin marketplace add DietrichGebert/ponytail → codex plugin add ponytail@ponytail. Claude Code: /plugin marketplace add DietrichGebert/ponytail → /plugin install ponytail@ponytail. /hooks에서 신뢰 상태를 확인하고 새 세션에서 동작을 확인합니다. Cursor·Gemini는 아래 원본 안내의 도구별 설치법을 따릅니다.'),
                      ('Graphify', '프로젝트 코드를 그래프로 탐색하는 별도 CLI/스킬입니다. ZIP에 포함되지 않습니다. uv tool install graphifyy → graphify --version → graphify install --platform codex(또는 claude, cursor, gemini) 순서로 설치합니다. 대상 에이전트마다 스킬 목록을 확인합니다. 프로젝트별 graphify-out/graph.json이 있을 때 graphify query "질문" --budget 1500으로 조회합니다. 그래프 생성은 명시적으로 선택한 프로젝트에서만 graphify extract <project> --code-only --no-cluster를 사용합니다. 기존 그래프는 변경 후 갱신해야 합니다.'),
                      ('검증의 경계', '설치 파일·검사 통과와 실제 앱에서의 훅 호출은 다릅니다. Ponytail의 절감 효과는 별도 측정이 필요하고, Graphify의 로컬 AST 그래프는 실행 중 동작이나 문서 의미를 자동으로 증명하지 않습니다.')]),
                    ('locations',
                     '설치와 사용은 환경에 맞게',
                     [('Codex', '공용 스킬은 ~/.agents/skills/, 개인 Codex 스킬은 ~/.codex/skills/를 확인합니다.'),
                      ('Claude', '~/.claude/skills/를 확인합니다. 같은 목적의 스킬도 도구명과 실행 계약은 환경마다 다를 수 있습니다.')])]),
            'en': ('Install and use skills',
                   'A skill supplies criteria and procedures for a relevant task. Distinguish bundled skills from separately installed tools, then verify loading and real behavior in your agent.',
                   [('handoff',
                     'Handoff',
                     [('When to use it',
                       'Use it when the user requests delegation, handoff, or phased execution and the work can be '
                       'divided into independently verifiable tasks.'),
                      ('Defaults',
                       'Inherit the parent model and reasoning effort. A complete packet is not a reason to force low '
                       'reasoning.')]),
                    ('expert-panel',
                     'Structured analysis and independent review',
                     [('expert-panel',
                       'A single-analyst procedure for framing problems, hypotheses, and decision criteria. It does '
                       'not inherently require multiple agents.'),
                      ('independent-panel',
                       'For consequential decisions, use independent drafts with distinct responsibilities and one '
                       'cross-review. Do not choose by vote or job title.')]),
                    ('eli5',
                     'ELI20 explanations',
                     [('One depth',
                       'Define unfamiliar terms, distinguish component responsibilities, trace connections and a concrete flow, and retain conditions, exceptions, limits, and evidence. The eli5 invocation name remains for compatibility.'),
                      ('Validate the result',
                       'Create self-contained HTML when exploring relationships helps. Check real state changes and readability on mobile. Publish only when requested or authorized.')]),
                    ('asd-ste100-interactive',
                     'STE-inspired technical writing · Korean and English',
                     [('Role', 'ELI20 determines what to explain and how deeply. This separate skill clarifies technical sentences and can be used with ELI20 when needed.'),
                      ('Korean mode', 'Clarify actors, references, terminology and action order while preserving conditions, exceptions, negation, quantities and obligation strength. English word limits and the approved dictionary do not apply. This is an adapted guide, not an official Korean STE standard.'),
                      ('Install', 'Copy the complete skills/asd-ste100-interactive/ folder from the implementation ZIP to ~/.agents/skills/ or ~/.codex/skills/ for Codex, or ~/.claude/skills/ for Claude. Avoid duplicate installation in both Codex locations. Back up and merge an existing folder.'),
                      ('Example requests', 'Use $asd-ste100-interactive to clarify this Korean technical document while preserving its meaning and exceptions. Combine it with $eli5 to explain the mechanisms and conditions fully, then clarify the wording.'),
                      ('Explore and verify', 'Open assets/korean-writing-explorer.html in the skill for Korean examples and review candidates, or asd-ste100-explorer.html for the English STE structure and settings. Korean expression flags and sentence lengths are advisory; the tool does not verify meaning preservation, safety or official compliance. English dictionary approval also requires authoritative data.')]),
                    ('optional-tools',
                     'Optional installs · Ponytail and Graphify',
                     [('Ponytail', 'An external plugin that helps avoid unnecessary code in coding tasks. It is not in this ZIP. For Codex, run codex plugin marketplace add DietrichGebert/ponytail, then codex plugin add ponytail@ponytail. For Claude Code, run /plugin marketplace add DietrichGebert/ponytail, then /plugin install ponytail@ponytail. Review trust in /hooks and verify behavior in a new session. Follow the upstream tool-specific instructions for Cursor and Gemini.'),
                      ('Graphify', 'A separate project-graph CLI and skill, not in this ZIP. Run uv tool install graphifyy, graphify --version, then graphify install --platform codex (or claude, cursor, gemini) for each target agent. Confirm the skill appears in each agent. When a project has graphify-out/graph.json, run graphify query "question" --budget 1500. To create a local code graph, explicitly select a project and run graphify extract <project> --code-only --no-cluster; refresh it after changes.'),
                      ('Verification boundary', 'Installed files and passing checks do not prove application hook delivery. Ponytail savings require measurement; a local Graphify AST graph does not prove runtime behavior or document meaning.')]),
                    ('locations',
                     'Adapt installation and use to the environment',
                     [('Codex',
                       'Check ~/.agents/skills/ for shared skills and ~/.codex/skills/ for personal Codex skills.'),
                      ('Claude',
                       'Check ~/.claude/skills/. Skills with the same purpose may use different tool names and '
                       'execution contracts.')])])},
 'handoff': {'ko': ('위임할 것은 작업.\n넘겨야 할 것은 근거.',
                    '독립적인 작업과 충분한 검증 경계가 있을 때 병렬화합니다.',
                    [('discover',
                      '먼저 현재 소스를 확인',
                      [('작업 패킷', '목표·변경 파일과 심볼·참조 구현·금지 범위·검증 기준을 명시합니다. 이미 아는 것을 반복 조사하지 않고 바뀐 부분을 갱신합니다.'),
                       ('기준선과 기대 실패', '현재 테스트 상태와 새 기능의 합격 기준을 구분합니다. 버그 재현이 구현 전에 실패하는 것은 정상일 수 있습니다.')]),
                     ('intent-guard',
                      '사용자 목적과 원문 근거 고정',
                      [('출처와 요구사항', '사용자 요청의 권위 있는 원문과 관련 명세를 지정하고, 각 요구사항은 원문에 실제로 있는 문장을 정확히 인용해 결과와 연결합니다. 키워드가 겹치는 인용만으로 의미가 맞다고 판단하지 않습니다.'),
                       ('독립 검토와 최신성', '작성자가 아닌 검토자가 원문과 명세를 직접 읽고 요구사항 전체, 범위 이탈, 목적 정렬을 확인합니다. 검토 영수증에는 두 문서의 SHA-256과 검토 범위를 남깁니다. 출처·명세가 바뀌면 검토는 오래된 것이므로 다시 검토하고 내보냅니다.'),
                       ('태스크 매핑', '각 구현·조사 태스크는 하나 이상의 요구사항 ID에 연결하고, 전체 태스크가 모든 요구사항을 다룹니다. 독립성은 파일 소유권과 의존성으로 별도 표현합니다.'),
                       ('목적 기준 수락', '원래 요청의 성공 조건을 실제 사용자 흐름에서 확인하는 acceptance 명령과 기대 종료 코드를 둡니다. 기존 spec에서 요구 원문 → 사용자가 답할 질문 → 필요한 데이터·출처 → 결과물과 행동 → 확인 방법을 연결합니다. 코드 검사 통과나 해시 일치만으로 의미 정렬, 독립성, 사용자 수락을 증명했다고 말하지 않습니다.')]),
                     ('dispatch',
                      '겹치지 않는 책임으로 배치',
                      [('의존성', '같은 파일을 동시에 수정하지 않도록 소유권을 정하고 depends_on으로 선행조건을 표현합니다.'),
                       ('추론과 컨텍스트',
                        '모델·추론 수준은 기본 상속합니다. 독립 태스크에는 필요한 근거만 담고 사용자 override를 보존합니다. 도구 목록과 예산은 실제 API 권한을 대신하지 '
                        '않습니다.')]),
                     ('integrate',
                      '상위 작업자가 통합 확인',
                      [('반환 증거', '실제로 실행한 명령·결과·변경 파일·미충족 기준을 받습니다. 하위 에이전트의 완료 주장만으로 닫지 않습니다. 상위는 검사 PASS를 범위 밖의 제품 인수로 승격하지 않고, 사용자가 실패를 지적한 경로를 직접 확인합니다.'),
                       ('Phase 종료', '합격 기준을 다시 확인하고 변경 간 충돌을 검토합니다. 배포·DB처럼 되돌리기 어려운 실행은 현재 승인 범위 안에서 처리합니다.')])]),
             'en': ('Delegate the work.\nTransfer the evidence.',
                    'Parallelize when tasks are independent and verification boundaries are clear.',
                    [('discover',
                      'Inspect current source first',
                     [('Task packet',
                        'Specify the goal, files and symbols, reference implementation, forbidden scope, and '
                        'acceptance criteria. Refresh changed evidence rather than repeating all discovery.'),
                       ('Baseline and expected failure',
                        'Separate the existing test state from new acceptance criteria. A regression reproduction may '
                        'correctly fail before the fix.')]),
                     ('intent-guard',
                      'Anchor the user purpose to source evidence',
                      [('Source and requirements',
                        'Name the authoritative user request and relevant specification. Quote each requirement exactly '
                        'from its source and connect it to an outcome. Matching keywords alone do not establish semantic alignment.'),
                       ('Independent review and freshness',
                        'A reviewer other than the author reads the raw source and specification, then checks every '
                        'requirement, scope changes, and alignment. Record both SHA-256 digests and review coverage. '
                        'Any source or specification change makes the receipt stale; review again before emitting.'),
                       ('Task mapping',
                        'Map every implementation and investigative task to requirement IDs, and cover every requirement '
                        'across the plan. Express file ownership and dependencies separately.'),
                       ('Acceptance against the original purpose',
                        'Define a command and expected exit code that check the original request through its user-facing '
                        'flow. In the existing spec, connect the source request to the question a user must answer, required data and sources, the result and action, and the verification method. Passing code checks or matching hashes alone does not prove semantic alignment, reviewer '
                        'independence, or user acceptance.')]),
                     ('dispatch',
                      'Assign distinct responsibilities',
                      [('Dependencies',
                        'Define ownership to avoid simultaneous edits to the same file. Express prerequisites with '
                        'depends_on.'),
                       ('Reasoning and context',
                        'Inherit model and reasoning settings by default. Provide only the evidence needed by an '
                        'independent task and preserve user overrides. Packet tool lists and budgets are not API '
                        'permission enforcement.')]),
                     ('integrate',
                      'The parent verifies integration',
                      [('Returned evidence',
                        'Require commands actually run, results, changed files, and unmet criteria. A subordinate '
                        'completion claim is not sufficient. The parent does not promote a check PASS to product acceptance outside its scope, and directly checks the path the user reported as failing.'),
                       ('Closing a phase',
                        'Check acceptance criteria and conflicts between changes. Handle consequential operations such '
                        'as deployment and database changes within the current authorization.')])])},
 'expert-panel': {'ko': ('구조는 결정을 돕고,\n근거가 결론을 정합니다.',
                         '사실과 가설, 아직 모르는 조건을 나눕니다.',
                         [('frame',
                           '문제를 먼저 정의',
                           [('선택 기준', '무엇을 결정하는지와 결과가 달라지는 조건을 정합니다. 중복된 평가 축과 근거 없는 가중치를 줄입니다.'),
                            ('반증', '가설이 맞으려면 무엇이 사실이어야 하는지 묻고 쉽게 깨지는 전제를 원문으로 확인합니다.')]),
                          ('independence',
                           '필요할 때 독립 관점 추가',
                           [('독립 초안', '서로의 결론을 보기 전에 다른 질문과 증거 범위를 맡습니다. 같은 모델의 역할극만으로 독립성이 생기지는 않습니다.'),
                            ('교차검토', '가장 강한 반론과 결론을 뒤집을 증거를 한 번 검토합니다. 투표·평균 점수보다 사실과 논리로 종합합니다.')]),
                          ('output',
                           '결정 가능한 결과',
                           [('불확실성', '조건이 확인되지 않으면 조건부 판단으로 남깁니다. 작은 점수 차이를 정밀한 우열로 표현하지 않습니다.'),
                            ('범위', '일회성 전문가 검토 요청을 이후 모든 계획의 의무로 저장하지 않습니다.')])]),
                  'en': ('Structure supports decisions.\nEvidence determines conclusions.',
                         'Separate facts, hypotheses, and conditions that remain unknown.',
                         [('frame',
                           'Define the decision first',
                           [('Criteria',
                             'State the decision and the conditions that change its outcome. Remove overlapping '
                             'dimensions and unsupported weights.'),
                            ('Falsification',
                             'Ask what must be true for a hypothesis to hold, then check its most fragile assumptions '
                             'against primary sources.')]),
                          ('independence',
                           'Add independent perspectives when useful',
                           [('Independent drafts',
                             'Assign different questions and evidence scopes before sharing conclusions. Role-play '
                             'alone does not create independence.'),
                            ('Cross-review',
                             'Review the strongest counterargument and evidence that would reverse the conclusion '
                             'once. Synthesize by facts and logic rather than votes or average scores.')]),
                          ('output',
                           'Make the result usable',
                           [('Uncertainty',
                             'Keep judgments conditional when key facts are unknown. Do not present small score '
                             'differences as precise rankings.'),
                            ('Scope',
                             'Do not turn a one-time request for expert review into an obligation for every future '
                             'plan.')])])},
 'eli5': {'ko': ('ELI20으로 이해하기.\n쉽게 읽히되 충분히 설명합니다.',
                 '처음 보는 제품도 용어, 구성요소, 연결, 실제 흐름, 조건과 한계까지 따라갑니다.',
                 [('depth',
                   '무엇을 설명하나요?',
                   [('용어와 책임', '제품·서비스·플랫폼·데이터·운영 주체를 구분하고, 각 구성요소가 맡은 일을 먼저 정의합니다.'),
                    ('연결과 흐름', '정보가 어디에 저장되고 어느 도구가 가져오며 실제 상태를 바꾸는지 동사로 연결합니다.'),
                    ('사례와 경계', '하나의 구체적 사례를 끝까지 따라간 뒤 기본 제공, 별도 설정, 외부 시스템, 아직 계획인 부분을 나눕니다.')]),
                  ('interaction',
                   '눌렀을 때 이해가 달라지게',
                   [('조작', '비교 전환, 단계 이동, 변수 변경처럼 관계를 직접 확인할 수 있는 조작을 고릅니다.'),
                    ('검증', '눈에 보이는 상태가 실제로 바뀌는지 확인합니다. 작은 화면의 글자·넘침·터치 영역도 확인합니다.')]),
                  ('example',
                   '예시 · 새로운 고객 문의',
                   [('입력', '상담원이 문의를 열면 고객 기록과 이전 대화가 조회됩니다. 기록이 없는 외부 채널은 연결 설정이 먼저 필요합니다.'),
                    ('처리', 'AI가 답변 초안을 만들 수 있지만, 실제 환불이나 계약 변경은 권한을 가진 업무 시스템의 별도 실행 단계가 필요합니다.'),
                    ('검증', '출처·권한·실행 로그를 확인합니다. 초안 생성 성공을 실제 업무 완료로 부르지 않습니다.')]),
                  ('publish',
                   '설명과 배포의 범위',
                   [('자기완결 HTML', '가능하면 외부 리소스에 의존하지 않는 아티팩트를 만듭니다. 설명을 읽는 데 로그인이 필요하지 않도록 합니다.'),
                    ('배포', '사용자가 요청·승인한 경우 배포합니다. 배포하지 않는 선택 자체에 별도 확인을 요구하지 않습니다.')])]),
          'en': ('Understand with ELI20.\nReadable and complete enough.',
                 'Start with terms, components, connections, a concrete flow, and the conditions and limits that matter.',
                 [('depth',
                   'What does it cover?',
                   [('Terms and responsibilities', 'Distinguish products, services, platforms, data, and operators. Define what each component does.'),
                    ('Connections and flow', 'Trace where information is stored, which tool retrieves it, and which tool changes the real state.'),
                    ('Example and boundaries', 'Follow one concrete case end to end. Separate built-in behavior, configuration, external systems, and plans.')]),
                  ('interaction',
                   'Make interaction reveal something',
                   [('Controls',
                     'Choose a comparison toggle, a step-through sequence, or a variable that lets readers inspect a '
                     'relationship.'),
                    ('Validation',
                     'Check that the visible state actually changes. Verify text, overflow, and touch targets on a '
                     'small screen.')]),
                  ('example',
                   'Example · a new customer inquiry',
                   [('Input', 'An agent opens an inquiry and retrieves the customer record and past conversation. An unconnected external channel requires configuration first.'),
                    ('Process', 'AI may draft a response, but a refund or contract change requires a separate authorized action in the business system.'),
                    ('Verify', 'Check sources, permissions, and execution logs. A successful draft is not proof that the business action completed.')]),
                  ('publish',
                   'Scope explanation and publication',
                   [('Self-contained HTML',
                     'Prefer an artifact that does not depend on external runtime resources. Avoid requiring login '
                     'simply to read the explanation.'),
                    ('Publication',
                     'Publish when the user requests or authorizes it. Choosing not to publish does not itself require '
                     'confirmation.')])])},
 'maintenance': {'ko': ('적용 후 확인',
                        '파일 배치, 새 세션 로드, 실제 실행 순서로 확인합니다.',
                        [('files',
                          '파일과 설정',
                          [('빠진 파일', '스킬 폴더에 SKILL.md와 참조 파일이 함께 있는지, 훅의 실행 경로에 스크립트가 있는지 확인합니다.'),
                           ('검사 실패', '도구별 안내의 검증 명령을 실행합니다. 오류에 나온 파일·설정부터 수정하고 해당 검사를 다시 실행합니다.')]),
                         ('session',
                          '새 세션',
                          [('지침·스킬', '대상 프로젝트 루트에서 새 세션을 시작합니다. 현재 로드된 전역·프로젝트 지침과 스킬 목록을 확인합니다.'),
                           ('훅·외부 연결',
                            '/hooks에서 등록·신뢰 상태를 확인하고 실제 작업의 호출 기록을 봅니다. MCP는 로그인 후 현재 세션에 필요한 도구가 보이는지 확인합니다.')]),
                         ('update',
                          '업데이트할 때',
                          [('변경만 병합', '기존 파일을 백업하고 새 묶음과 비교해 변경된 부분을 적용합니다. 개인 메모리와 프로젝트별 권한은 대상 환경에서 관리합니다.')])]),
                 'en': ('Check the setup',
                        'Verify files, loading in a new session, and actual execution in that order.',
                        [('files',
                          'Files and configuration',
                          [('Missing files',
                            'Check that every skill includes SKILL.md and its referenced files, and that each hook '
                            'command points to an existing script.'),
                           ('Failed checks',
                            'Run the commands in the tool-specific guide. Fix the file or setting named in the error, '
                            'then rerun the relevant check.')]),
                         ('session',
                          'New session',
                          [('Instructions and skills',
                            'Start a new session at the target project root. Check the loaded global and project '
                            'instructions and available skills.'),
                           ('Hooks and connections',
                            'Use /hooks to check registration and trust, then inspect invocations during real work. '
                            'After MCP login, confirm that the needed tools are available in the current session.')]),
                         ('update',
                          'When updating',
                          [('Merge changes',
                            'Back up existing files, compare the new bundle, and apply changes. Manage personal '
                            'memories and project permissions in the target environment.')])])}}

# Product acceptance supplements existing checks; it is not a semantic hook gate.
PAGES['maintenance']['ko'][2].append(('product-acceptance', '검사와 제품 인수', [
 ('목적에서 확인 방법까지', '기능 검사·제품 인수·사용자 수락을 구분합니다. 기존 spec에 요구 원문 → 사용자가 답할 질문 → 필요한 데이터·출처 → 결과물과 행동 → 확인 방법을 연결합니다. UI는 실제 화면과 상호작용으로 확인합니다.'),
 ('실패한 경로를 확인', '포인터 실패 뒤 키보드가 통과해도 포인터는 미검증입니다. 합성 검사·실제 로컬 전달·원격 전달·배포 파일 대조는 각각의 범위를 유지합니다. 증거의 대상 버전을 기록하고 영향을 받는 변경 뒤 재검증합니다.'),
 ('거절 뒤 접근 전환', '명백한 목적 불일치는 즉시 수정합니다. 같은 접근이 두 번 실패하면 세 번째 시도 전에 거절된 결과·원인가설·바꾸는 가정·인수 조건을 기존 명세에 기록합니다. 다른 진행 가능한 작업은 계속합니다. 공통 절차는 다운로드의 codex/docs/autonomous_coding.md 또는 claude/docs/autonomous_coding.md에서 확인하세요.')]))
PAGES['maintenance']['en'][2].append(('product-acceptance', 'Checks and product acceptance', [
 ('From purpose to verification', 'Separate technical checks, product acceptance and user acceptance. In the existing spec, connect the source request to the question a user must answer, required data and sources, the result and action, and the verification method. Check UI changes through actual rendering and interaction.'),
 ('Verify the failed path', 'A keyboard pass after a pointer failure leaves the pointer path unverified. Preserve the distinct scope of synthetic checks, actual local delivery, remote delivery and deployed file comparisons. Record the target version and recheck after relevant changes.'),
 ('Change the approach after rejection', 'Correct clear goal mismatches immediately. After two failures with the same approach, record the rejected result, cause hypothesis, changed assumption and acceptance condition before a third attempt. Continue other work that can still progress. The shared procedure is in codex/docs/autonomous_coding.md or claude/docs/autonomous_coding.md in the download.')]))

# These reference snippets add logger commands; they never replace safety gates.
for tool in ('codex', 'claude'):
    events = ['SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'Stop', 'SessionEnd']
    if tool == 'claude':
        events += ['PostToolUseFailure', 'SubagentStart', 'SubagentStop']
    command = 'python3 "$HOME/.agents/harness-activity/logger.py" hook --source ' + tool
    hooks = {}
    for event in events:
        entry = {'hooks': [{'type': 'command', 'command': command, 'timeout': 3}]}
        if event in ('PreToolUse', 'PostToolUse', 'PostToolUseFailure'):
            entry['matcher'] = '.*' if tool == 'codex' else '*'
        hooks[event] = [entry]
    snippet = '```json\n' + json.dumps({'hooks': hooks}, indent=2) + '\n```'
    location = '~/.codex/hooks.json' if tool == 'codex' else '~/.claude/settings.json'
    for lang in ('ko', 'en'):
        if lang == 'ko':
            section = ('activity', '5. 로컬 활동 기록과 근거 보기', [
                ('공통 패키지 배치', '구현 ZIP의 activity/ 폴더를 ~/.agents/harness-activity/로 옮깁니다. logger.py, test_logger.py, viewer.html, README.md, example-project.jsonl을 함께 유지합니다. 예시 JSONL은 합성 자료이며 직접 선택해 볼 수 있습니다. Python 표준 라이브러리만 사용하며 자동 설치는 하지 않습니다.'),
                ('기존 훅에 병합', location + '을 백업한 뒤 아래 hooks 항목의 명령을 각 이벤트의 기존 배열에 추가합니다. 기존 PreToolUse 안전 게이트와 Claude Stop 검사를 별도 명령으로 유지하세요. 설정 전체를 덮어쓰지 마세요. 설치된 앱 버전에서 지원하는 이벤트만 등록합니다.'),
                ('명령 훅 참고 JSON', snippet),
                ('첫 작업 흐름', '기록 없이 새 프로젝트를 만들거나 example-project.jsonl을 직접 선택합니다. 목표·포함/제외 범위·단계·완료 조건을 정한 뒤, 변경 이유와 결과물 버전별 검사·수락 상태를 기록하세요. 다음 작업에 쓸 기준을 직접 선택하고 다음 Agent 작업 및 수락 조건을 입력해 Markdown 패킷을 내려받습니다. 프로젝트 전체 JSONL 저장은 별도 동작입니다.'),
                ('기록과 확인', '기본 로그는 ~/.local/state/harness-activity/의 일별 JSONL입니다. python3 ~/.agents/harness-activity/test_logger.py로 로컬 검사를 실행한 뒤 새 세션에서 /hooks 등록·신뢰 상태와 실제 작업의 이벤트 기록을 확인하세요. 직접 stdin 검사 통과는 앱의 훅 전달 증거가 아닙니다. 수동 결정·검사·수락은 선언 기록이며 실제 산출물 검증을 대신하지 않습니다.'),
                ('개인정보와 제품 경계', '내보내기에는 선택된 코드와 합성 예시만 포함하고 개인 로그·계정 설정·비밀정보는 포함하지 않습니다. 로컬 인덱스는 다른 기기로 옮겨지지 않으므로 같은 프로젝트 ID를 유지하려면 --project-id를 명시하고 README.md를 따르세요. 미저장 화면 변경은 닫으면 사라집니다. 중앙 동기화, 결정 의미 자동 포착, WBS·간트·와이어프레임은 후속 제품 방향이며 현재 기능이 아닙니다. Cursor·Gemini 연결도 후속 범위입니다.')])
        else:
            section = ('activity', '5. Record local activity and review evidence', [
                ('Place the shared package', 'Copy activity/ from the implementation ZIP to ~/.agents/harness-activity/. Keep logger.py, test_logger.py, viewer.html, README.md, and example-project.jsonl together. The JSONL is synthetic and can be selected explicitly. It uses only the Python standard library and does not install itself.'),
                ('Merge with existing hooks', 'Back up ' + location + ', then append the commands below to each existing event array under hooks. Keep the existing PreToolUse safety gate and Claude Stop check as separate commands. Merge entries without overwriting the full configuration. Register only events supported by the installed application version.'),
                ('Reference command-hook JSON', snippet),
                ('First work cycle', 'Start a project without logs or explicitly select example-project.jsonl. Set the goal, included and excluded scope, phase, and finish conditions. Record decision reasons and artifact versions with their check or acceptance status. Explicitly choose the basis for the next task, enter that Agent task and its acceptance conditions, and download the Markdown packet. Saving the complete project JSONL is a separate action.'),
                ('Record and verify', 'Daily JSONL logs default to ~/.local/state/harness-activity/. Run python3 ~/.agents/harness-activity/test_logger.py for local checks, then open a new session, review registration and trust in /hooks, and verify actual work events. Direct stdin checks do not prove application hook delivery. Declared decisions, checks and acceptance do not replace verification of the actual artifact.'),
                ('Privacy and product limits', 'The export contains selected code and a synthetic example, not private logs, account settings, or secrets. The private project index does not transfer between devices; specify --project-id for a shared project identity and follow README.md. Unsaved viewer changes disappear on close. Central sync, automatic decision-semantic capture, and WBS, Gantt, or wireframe views are future product direction, not current features. Cursor and Gemini hookup is also deferred.')])
        PAGES[tool][lang][2].append(section)

SCENES = {'ko': [('rules',
         '철칙',
         '승인 경계',
         '환경 고유 경계 → 요청 범위 확인 → 실행',
         '이미 승인한 범위는 다시 묻지 않습니다. 새 DB 변경이나 외부 실행은 그 범위에 포함되는지 확인합니다.',
         '모든 행동을 허가받도록 만들면 작업이 멈춥니다. 일반적인 구현 판단은 에이전트에게 맡깁니다.'),
        ('harness',
         '하네스',
         '얇은 진입점',
         '지침 → 도구 → 관측된 결과',
         '환경 사실은 진입점에, 좁은 기계적 조건은 훅에, 절차는 스킬에 둡니다.',
         '파일이 있고 검사가 통과해도 실제 앱의 호출까지 입증된 것은 아닙니다.'),
        ('loop',
         '루프',
         '근거 있는 재시도',
         '기준선 → 변경 → 검증 → 판단',
         '사용자의 목적상 거절도 실패입니다. 명백한 목적 불일치는 즉시 수정하고, 같은 접근이 두 번 실패하면 세 번째 시도 전에 가정을 확인하거나 접근을 바꿉니다. 다른 진행 가능한 작업은 계속합니다.',
         '문서나 자동화 개수를 성숙도 점수로 세지 않습니다. 무한 반복과 너무 이른 포기를 모두 피합니다.'),
        ('graph',
         '그래프',
         '의존 관계',
         '독립 작업 A · B → 통합 검증',
         '독립적으로 검증할 노드가 여럿이거나 실패 후 돌아갈 경로가 있을 때 관계를 명시합니다.',
         '단순 순서에는 목록이면 충분합니다. 그래프를 유지하는 비용보다 얻는 설명력이 커야 합니다.'),
        ('skill',
         '스킬',
         '필요 시 절차',
         '요청 → 적합한 스킬 → 결과 확인',
         '반복되는 전문 작업에 필요한 기준을 제공합니다. 준비된 패킷도 부모 추론 수준을 기본 상속합니다.',
         '일회 요청을 모든 작업의 절차로 확대하지 않습니다. 스킬이 사용자의 현재 요청을 바꾸지 않아야 합니다.')],
 'en': [('rules',
         'Rules',
         'Approval boundaries',
         'Local boundary → request scope → action',
         'Do not ask again about work already authorized. Confirm that a new database change or external operation is '
         'within that scope.',
         'Requiring approval for every action stalls work. Leave ordinary implementation judgment to the agent.'),
        ('harness',
         'Harness',
         'A thin entry point',
         'Instructions → tools → observed results',
         'Put environment facts in the entry point, narrow mechanical conditions in hooks, and procedures in skills.',
         'Files and passing checks do not prove that the application invokes them correctly.'),
        ('loop',
         'Loop',
         'Evidence-led retries',
         'Baseline → change → verify → decide',
         'Treat a rejection of the intended outcome as failure. Correct clear goal mismatches immediately. After two failures with the same approach, check assumptions or change the approach before a third attempt. Continue other work that can still progress.',
         'Do not score maturity by document or automation counts. Avoid both endless repetition and premature '
         'abandonment.'),
        ('graph',
         'Graph',
         'Dependencies',
         'Independent tasks A · B → integration check',
         'Show relationships when several nodes can be verified independently or a failure introduces a return path.',
         'A list is enough for a simple sequence. The explanation gained should justify the graph’s maintenance cost.'),
        ('skill',
         'Skill',
         'A procedure on demand',
         'Request → suitable skill → verified result',
         'Provide useful criteria for recurring specialist work. Even a complete task packet inherits parent reasoning '
         'by default.',
         'Do not turn a one-time request into a procedure for every task. A skill must not replace the current user '
         'request.')]}


# Central project management, distinct from the retained local activity viewer.
PAGES['ai-pms'] = {'ko': ('여러 사용자의 프로젝트를\n중앙에서 이해하기.',
        'AI PMS는 다수 사용자·환경·세션의 작업을 지속되는 프로젝트에 연결합니다. 목표, 단계별 문서, 검사와 MCP·데이터 참조를 원본 근거로 확인합니다.',
        [('purpose',
          '무엇을 관리하나요?',
          [('프로젝트가 관리 단위입니다',
            '한 사람의 여러 세션을 넘어 여러 사용자의 여러 세션을 모읍니다. 세션이 끝나도 프로젝트 목표, 문서 버전, 단계, Agent와 결과물의 연결은 이어집니다. 같은 '
            '이름·UUID라도 사용자와 환경이 다르면 자동 병합하지 않습니다.'),
           ('Kit와 중앙 화면의 역할',
            'Kit의 로컬 훅은 공통 형식으로 관측을 남기고, 선언 기록은 목표·판단·문서·검사 기준을 보완합니다. 중앙 집계기는 명시적 프로젝트 연결을 적용하고 대시보드는 프로젝트 '
            '현황에서 문서·세션·원본 근거로 내려갑니다. activity/viewer.html은 개인용 오프라인 참고 도구이며 중앙 제품 화면은 아래 샘플입니다.')]),
         ('flow',
          '기록에서 완료 판정까지',
          [('한 프로젝트의 실제 흐름',
            '사용자/환경 → 세션/Agent → 공통 이벤트 → 중앙 집계 → 프로젝트 목표·단계별 문서 → 현재 revision 검사. 작업 검사·단계 검사·프로젝트 전체 검사는 '
            '구분합니다. 현재 프로젝트 버전과 설정된 전체 완료 기준을 충족한 검사만 완료 판정에 사용합니다.'),
           ('관측과 선언을 나눕니다',
            '훅은 호출 이름과 요청·완료·실패를 관측합니다. 목표와 판단 이유는 훅에서 추측하지 않고 문서·계획·명시적 기록으로 보완합니다. 연결 실패·수집 지연·재검증·미관측은 '
            '완료로 바꾸지 않습니다.')]),
         ('connectivity',
          'MCP와 데이터 참조 읽기',
          [('MCP란?',
            'MCP는 에이전트가 외부 도구를 호출하는 연결 방식입니다. 서버는 도구 묶음, tool은 개별 기능입니다. 관계는 프로젝트 → 사용자/환경/세션 → 서버/tool → '
            '사용자·환경에 귀속된 논리 데이터 참조 → 명시적 결과물 참조로 읽습니다.'),
           ('근거의 강도',
            'configured와 reviewed resource-map은 declared입니다. requested/completed/failed/unknown은 도구 이벤트 관측이며 '
            'duration_ms는 어댑터가 제공한 값만 기록합니다. resources의 declared/input/output은 참조가 나온 위치이지 실제 DB 접근 감사 증거가 '
            '아닙니다. 성공한 도구 호출도 하위 데이터 접근이나 프로젝트 완료를 증명하지 않습니다.'),
           ('빈칸과 충돌',
            '서버·tool 식별이 없으면 unknown/null로 남깁니다. 같은 서버 별칭이나 데이터 label이 다른 사용자 환경의 자원을 합치지 않습니다. Pre/Post를 두 '
            '번의 완료 실행으로 세지 않으며, 알 수 없는 결과물 ID도 명시적 참조로만 표시합니다.')]),
         ('logging',
          '로컬 기록 예시와 안전 계약',
          [('합성 훅 stdin 확인',
            '```sh\n'
            "printf '%s\\n' "
            '\'{"hook_event_name":"PostToolUse","tool_name":"mcp__demo__lookup","pms_metadata":{"operation":"read","resources":[{"id":"demo-doc","kind":"document","label":"Synthetic '
            'document","evidence":"input"}],"artifact_refs":[{"id":"demo-result","version":"v1"}]}}\' | '
            'python3 ~/.agents/harness-activity/logger.py hook --source claude --project-id 11111111-1111-4111-8111-111111111111 '
            '--log-dir ./synthetic-logs\n'
            '```'),
           ('로컬 선언 map',
            '```json\n'
            '{"mcp__demo__lookup":{"operation":"read","resources":[{"id":"demo-doc","kind":"document","label":"Synthetic '
            'document","evidence":"declared"}],"artifact_refs":[{"id":"demo-result","version":"v1"}]}}\n'
            '```'),
           ('map 적용과 검사',
            '검토한 JSON을 synthetic-resource-map.json으로 저장하고 위 hook 명령에 --resource-map '
            './synthetic-resource-map.json을 추가합니다. 매핑 자원 근거는 declared로 고정됩니다. python3 '
            '~/.agents/harness-activity/test_logger.py를 실행하세요. stdin 검사는 실제 앱 훅 전달·신뢰의 증거가 아닙니다. 기존 설정 병합과 '
            '실제 새 세션 확인은 도구별 안내를 따릅니다.'),
           ('저장 허용 범위',
            'v1 이벤트는 유지하며 v2 connection은 server, tool, status, duration_ms, operation, resources, '
            'artifact_refs만 허용합니다. resources는 id/kind/label/evidence, artifact_refs는 id/version이며 각각 '
            '최대32개입니다. URL·경로·쿼리·토큰·raw input/output은 저장하지 않습니다. 잘못된 선택 메타데이터는 누락 표시와 함께 제외하고 잘못된 가져오기 데이터는 '
            '거절합니다.')]),
         ('boundary',
          '샘플과 운영의 경계',
          [('공개 샘플',
            '새 앱은 합성 데이터로 만든 정적 오프라인 대시보드입니다. JSON 가져오기·내보내기와 MCP · 데이터 탭을 살펴보세요. 운영 서버·관리자 인증·실시간 자동 수집 '
            '서비스는 아닙니다. 아래 Live Kit로 자체 호스팅·opt-in sender를 실행할 수 있습니다. 실제 앱 훅과 원격 운영 검증은 별도입니다.'),
           ('배포와 권한',
            '이 페이지와 ZIP은 참고 자료입니다. 원격 sender 설치, 계정·키·MCP trust 변경을 자동 실행하지 않습니다. 실제 다중 사용자 앱 전달, 수집 지연, 원본 '
            '결과물과 현재 버전 검사는 별도 운영 근거가 필요합니다.')])]),
 'en': ('Understand multiple users’ projects\nin one central view.',
        'AI PMS connects work across users, environments and sessions to persistent projects. Inspect goals, '
        'documents by step, checks, and MCP/data references with original evidence.',
        [('purpose',
          'What does AI PMS manage?',
          [('The project is the management unit',
            'Go beyond one user’s sessions to multiple users and sessions. Goals, document versions, steps, '
            'Agents and artifacts persist after a session ends. Identical names or UUIDs in different user '
            'environments are not automatically merged.'),
           ('Kit and central responsibilities',
            'Local Kit hooks record observations in a common format. Declared records add goals, rationale, '
            'documents and check criteria. Central aggregation uses explicit project links; the dashboard '
            'leads from portfolio to documents, sessions and original evidence. activity/viewer.html is a '
            'personal offline reference tool; the central product sample is linked below.')]),
         ('flow',
          'From records to completion',
          [('A project’s flow',
            'User/environment → session/Agent → common events → central aggregation → project goal and '
            'documents by step → checks for the current revision. Task, phase and whole-project checks have '
            'separate scope. Only checks for the current project revision satisfying configured '
            'whole-project criteria govern completion.'),
           ('Separate observations and declarations',
            'Hooks observe call identities and requested/completed/failed states. Goals and rationale come '
            'from documents, plans and explicit records rather than guesses. Connection failures, collection '
            'delay, revalidation and missing observations never become completion.')]),
         ('connectivity',
          'Read MCP and data references',
          [('What is MCP?',
            'MCP connects an agent to external tools. A server groups tools; a tool is one function. Read '
            'the path as project → user/environment/session → server/tool → scoped logical data reference → '
            'explicit artifact reference.'),
           ('Evidence strength',
            'Configured catalog rows and reviewed resource maps are declared. '
            'requested/completed/failed/unknown are tool-event observations; duration_ms is recorded only '
            'when an adapter provides it. Resource evidence declared/input/output identifies where a '
            'reference came from, not a downstream database audit. Tool success proves neither actual data '
            'access nor project completion.'),
           ('Missing identities and collisions',
            'Missing server/tool identities remain unknown/null. Shared aliases or resource labels never '
            'merge different user environments. Pre/Post observations are not two completed executions. '
            'Unknown artifact IDs remain explicit references, not verified artifact use.')]),
         ('logging',
          'Local examples and safe contract',
          [('Synthetic hook stdin check',
            '```sh\n'
            "printf '%s\\n' "
            '\'{"hook_event_name":"PostToolUse","tool_name":"mcp__demo__lookup","pms_metadata":{"operation":"read","resources":[{"id":"demo-doc","kind":"document","label":"Synthetic '
            'document","evidence":"input"}],"artifact_refs":[{"id":"demo-result","version":"v1"}]}}\' | '
            'python3 ~/.agents/harness-activity/logger.py hook --source claude --project-id 11111111-1111-4111-8111-111111111111 '
            '--log-dir ./synthetic-logs\n'
            '```'),
           ('Locally declared map',
            '```json\n'
            '{"mcp__demo__lookup":{"operation":"read","resources":[{"id":"demo-doc","kind":"document","label":"Synthetic '
            'document","evidence":"declared"}],"artifact_refs":[{"id":"demo-result","version":"v1"}]}}\n'
            '```'),
           ('Apply a map and check',
            'Save reviewed JSON as synthetic-resource-map.json and append --resource-map '
            './synthetic-resource-map.json to the hook command above. Mapped resource evidence is forced to '
            'declared. Run python3 ~/.agents/harness-activity/test_logger.py. Stdin checks do not prove '
            'application hook delivery or trust. Follow the tool guides for merging existing settings and '
            'verifying a real new session.'),
           ('Allowed storage',
            'v1 events remain valid. A v2 connection allows only server, tool, status, duration_ms, '
            'operation, resources and artifact_refs. Resources have id/kind/label/evidence; artifact_refs '
            'have id/version, with at most32 of each. URLs, paths, queries, tokens and raw inputs/outputs '
            'are excluded. Invalid optional metadata is dropped with missing-field markers; invalid imports '
            'are rejected.')]),
         ('boundary',
          'Sample and operational limits',
          [('Public sample',
            'The new app is a static offline dashboard with synthetic data. Explore JSON import/export and '
            'the MCP · data tab. It provides no operational backend, administrator authentication or live '
            'automatic collection service. Use the Live Kit below for a self-hosted service and opt-in sender. Actual provider hook trust and remote operational delivery need separate verification.'),
           ('Deployment and permissions',
            'Pages and ZIPs are references. They do not automatically install a remote sender or change '
            'accounts, keys or MCP trust. Real multi-user application delivery, collection delay, original '
            'artifacts and current-revision checks need separate operational evidence.')])])}

for lang, label, text in [('ko', 'AI PMS 중앙 프로젝트', '여러 사용자의 목표·단계별 문서·현재 버전 검사와 MCP·데이터 참조를 중앙에서 확인합니다.'), ('en', 'AI PMS central projects', 'Review multiple users’ goals, step documents, current-revision checks and MCP/data references centrally.')]:
    PAGES['index'][lang][2][3][2].append((label, text))


# Management v3 retains explicit intent and actual execution separately.
for lang in ('ko', 'en'):
    PAGES['ai-pms'][lang][2].insert(0, ('release', '2026-10-02 업데이트 · 중앙 관리 v3' if lang=='ko' else '2026-10-02 update · Central management v3', [
        ('이번에 추가된 내용' if lang=='ko' else 'What changed', '회사 목표·개인 위임 → 요구사항 → 계획과 테스트 설계 이유 → 실패·수정·통과 → 현재 산출물 검증을 연결했습니다. 막힘의 담당자·다음 조치, 철칙·하네스·검증 루프·스킬·MCP 개선 근거와 선택적 Graphify 최신성도 확인할 수 있습니다.' if lang=='ko' else 'Connect company goals and delegation to requirements, plan and test-design reasons, fail/fix/pass attempts and current artifact checks. Inspect blocker owners/next actions, evidence for rule/harness/loop/skill/MCP improvements and optional Graphify freshness.'),
        ('JSON 템플릿과 설명 위치' if lang=='ko' else 'Where to find the JSON template and guide', '아래 직접 링크에서 전체 필드 설명과 v3 JSON 템플릿을 볼 수 있습니다. 구현 소스 ZIP의 activity/catalog-v3.template.json, activity/json-contracts.md, activity/README.md에도 포함됩니다. 목표·판단·검사 이유는 명시적으로 기록하고, runner는 실제 실행 결과를 남깁니다.' if lang=='ko' else 'Use the direct links below for the complete field guide and v3 JSON template. The implementation ZIP also contains activity/catalog-v3.template.json, activity/json-contracts.md and activity/README.md. Goals, decisions and test reasons are explicit records; the runner records actual execution results.')]))
PAGES['ai-pms']['ko'][2].insert(2, ('management', '목표·위임·검사 설계와 개선 근거', [
    ('회사 목표와 개인 프로젝트', '회사 목표를 결과 달성(outcome) 또는 작업 지시(task)로 개인에게 넘기고 담당자·수락 기준·원문을 연결합니다. 개인 프로젝트도 독립적으로 관리하며 회사 목표 연결을 강제하지 않습니다. 회사의 업무 성과는 기술 검사 통과와 별도로 미관측입니다.'),
    ('왜 이 검사를 만들었나요?', 'requirements → plans의 버전·이유 → test_plans의 정의·설계 이유·제외 범위·파일 해시 → attempts의 실제 실행 영수증으로 연결합니다. 과거 계획과 시도를 보존하며 현재 revision·실제 산출물 해시·현재 검사 정의에 맞는 runner 기록만 완료 판정에 사용합니다. Handoff 결과 가져오기는 declared이며 실행 증거가 아닙니다.'),
    ('막힘과 개선을 검토합니다', '막힘은 원인 가설/확정·담당자·다음 행동·연결 시도를 명시적으로 기록합니다. 철칙(rule), harness, 검증루프(loop), skill, mcp 개선은 변경 버전·근거 시도·검증 시도와 제안/시험/채택/보류 결정을 연결합니다. 검증 없는 개선 효과는 미관측이며 비활동 시간이나 자동 점수로 추측하지 않습니다.'),
    ('선택적 Graphify 근거', '프로젝트 wrapper의 --graph 또는 graph 명령은 code-only/no-cluster AST 그래프를 만들고 버전·source revision/hash·시각·generated/failed와 최신성을 남깁니다. 동일한 선언 manifest와 실제 graph 파일이면 재사용할 수 있습니다. 생성 실패는 검사를 막지 않습니다. HOME 및 HOME Git 루트·프로젝트 밖 symlink는 거절합니다. 전역 훅은 설치하지 않으며 AST는 runtime 연결·검사 커버리지 증거가 아닙니다.')]))
PAGES['ai-pms']['en'][2].insert(2, ('management', 'Goals, delegation, test design and improvement evidence', [
    ('Company goals and personal projects', 'Delegate a company goal as an outcome or a task with owner, acceptance and source. Personal projects remain independently managed without a required company link. Business outcomes remain unobserved separately from technical check results.'),
    ('Why was this test designed?', 'Connect requirements → versioned plans/reasons → test-plan definitions/design reasons/exclusions/file hashes → actual execution attempts. Preserve history. Only runner receipts matching the current revision, actual artifact hash and current check definition can govern completion. Imported Handoff results are declared, not execution evidence.'),
    ('Review blockers and improvements', 'Record blocker hypotheses or confirmed causes, owners, next actions and attempts explicitly. Improvements to rule, harness, loop, skill or mcp connect change versions, evidence and validation attempts with proposed/trial/adopt/hold decisions. Effects without validation remain unobserved; inactivity and automatic productivity scores do not establish a cause.'),
    ('Optional Graphify evidence', 'The project wrapper --graph option or graph command produces code-only/no-cluster AST evidence with generator version, source revision/hash, time, generated/failed status and freshness. Matching declared manifests with an existing graph file can be reused. Graph failure never blocks tests. HOME, a HOME git root and escaping symlinks are rejected. No global hooks are installed; AST graphs do not establish runtime integration or test coverage.')]))
for lang in ('ko', 'en'):
    PAGES['ai-pms'][lang][2].append(('recorder', '관리 기록기 실행' if lang=='ko' else 'Run the management recorder', [
        ('실제 검사 실행' if lang=='ko' else 'Execute an actual check', '```sh\npython3 ~/.agents/harness-activity/management_recorder.py --project ./my-project --management management.json --project-id my-project run --test-plan acceptance --version v1 --actor-id Alice --environment-id laptop --session-id session-1 --environment local --timeout 300\npython3 ~/.agents/harness-activity/test_management_recorder.py\n```'),
        ('파일·영수증 경계' if lang=='ko' else 'Files and receipt boundaries', 'v3 template과 field guide를 먼저 읽고 management.json의 사용자·환경·기준·manifest를 검토합니다. management_recorder.py, management.py, test_management_recorder.py를 함께 배치합니다. shlex argv/shell=False로 실행하고 raw stdout/stderr는 저장하지 않습니다. test file 변경은 명시적 새 계획 버전이 필요하며 사후 산출물 변경은 stale/unknown입니다. 파일이 사라지면 관리 파일 원본을 유지하고 안전한 별도 receipt를 남깁니다. manifest 포괄성 및 runner JSON은 외부 신뢰 보증이 아닙니다.' if lang=='ko' else 'Read the v3 template and field guide, then review management.json identities, criteria and manifest. Keep management_recorder.py, management.py and test_management_recorder.py together. Commands use shlex argv/shell=False; raw stdout/stderr is omitted. Changed test files require an explicit new plan version; post-run artifact changes make receipts stale/unknown. Missing files preserve the original management file and a safe separate receipt. Manifest coverage and runner JSON provide no external trust guarantee.'),
        ('Handoff·그래프 사용' if lang=='ko' else 'Handoff and graph use', 'README.md의 handoff helper는 원문 요구사항·계획·검사 설계 이유와 결과 declared를 연결합니다. 검토한 기존 criterion과 명령·기대 exit code가 정확히 맞아야 합니다. 선택 graph helper는 프로젝트에만 실행하며 실제 훅 설치·원격 전송을 자동 실행하지 않습니다.' if lang=='ko' else 'The README handoff helper links source requirements, plans, test-design reasons and declared results. Commands and expected exit codes must exactly match reviewed existing criteria. Optional graph helpers run only on the selected project; they do not automatically install hooks or remote delivery.')]))

# Explicit traceability, optional for existing v3 catalogs.
for lang in ('ko', 'en'):
    PAGES['ai-pms'][lang][2].insert(1, ('traceability', '추가 반영 · 변경·판단·인계·기록 상태' if lang=='ko' else 'Added · Changes, decisions, handoffs and capture', [
        ('변경과 검사 연결' if lang=='ko' else 'Changes and checks', 'checkpoint 명령은 실제 Git 커밋·부모·미커밋 변경 해시를 읽고 세션·에이전트 선언 및 같은 산출물 검사를 연결합니다. 판단은 대안·선택 이유·원문·대체 이력을 남깁니다. Git 전체 tree 검사나 작성자 인증으로 해석하지 않습니다.' if lang=='ko' else 'The checkpoint command reads Git commits, parents and dirty-worktree digests and links explicit session/agent attribution and matching artifact checks. Decisions retain alternatives, reasons, requirements and superseded entries. These do not authenticate authors or prove whole-tree testing.'),
        ('인계 활용과 기록 상태' if lang=='ko' else 'Handoff use and capture status', '인계 packet hash와 이전·다음 세션을 연결합니다. 생성·전달은 활용 증거가 아니므로 미관측/선언/조회 근거를 구분합니다. 도구별 지원 범위·중지·오류·마지막 관측은 가져온 시점의 보고이며 실시간 heartbeat가 아닙니다. 기존 v3도 호환됩니다. activity/README.md의 checkpoint 및 record 명령과 전체 필드 설명을 참고하세요.' if lang=='ko' else 'Link handoff packet hashes and source/destination sessions. Creation or delivery does not prove use: separate unobserved, declared and observed read evidence. Capture support, pauses, errors and last observations are historical reports, not live heartbeats. Existing v3 remains compatible. See checkpoint/record commands in activity/README.md and the complete field guide.')]))

# Work management is the primary manager flow; execution records remain evidence.
for lang in ('ko','en'):
    PAGES['ai-pms'][lang][2].insert(0, ('work-management', '2026-10-02 · 사람·목표·Phase·작업 관리' if lang=='ko' else '2026-10-02 · People, goals, phases and tasks', [
        ('사람별 책임 작업' if lang=='ko' else 'Responsible work by person', '사람을 선택하면 참여 프로젝트의 목표와 단계 달성을 봅니다. 공동 프로젝트는 하나로 유지하고 참여자를 함께 표시합니다. 책임 작업·의존성·완료 조건·검증은 별도 분석 근거에서 확인합니다.' if lang=='ko' else 'Select a person to see project goals and phase achievements. Shared projects remain one record with all participants. Inspect assigned tasks, dependencies, acceptance conditions and verification in separate evidence.'),
        ('관리자가 판단할 다음 행동' if lang=='ko' else 'Concrete manager actions', '분석 근거에서 검사 실패·사람 검토·담당자/기준 누락·명시적 막힘과 다음 행동을 확인합니다. 일반 선행 작업 대기는 진행 대기로 구분합니다. 세션·MCP 호출 수로 진척이나 생산성을 계산하지 않습니다.' if lang=='ko' else 'The evidence view contains failed checks, human reviews, missing owners or acceptance conditions, explicit blockers and next actions. Ordinary dependency waits are distinguished from decisions. Session and MCP counts are not progress or productivity scores.'),
        ('Kit 계획과 완료 판정' if lang=='ko' else 'Kit plans and completion', '완전한 Handoff 계획의 Phase·작업·의존성·완료 조건을 보존합니다. 필수 작업·모든 Phase 종료 검사·필요한 사람 승인·프로젝트 인수가 충족되어야 완료입니다. 기준이나 파일 변경은 과거 검증/승인을 재검토합니다. ZIP activity/catalog-work.template.json, work.py와 README에서 시작하세요.' if lang=='ko' else 'Full Handoff imports preserve phases, tasks, dependencies and acceptance conditions. Completion requires required tasks, every phase gate, required human reviews and project acceptance. Changed criteria or files invalidate old evidence. Start with activity/catalog-work.template.json, work.py and README in the ZIP.'),
        ('명시적 기록과 지원 경계' if lang=='ko' else 'Explicit records and boundaries', 'update로 시작/막힘, review로 현재 파일·기준에 묶인 판단을 기록합니다. 결과 파일의 통과는 선언이며 runner 관측과 구분합니다. 작업 출력 문자열 조건은 사람 검토로 보존하며 단계/전체 출력 조건은 미지원으로 거부합니다. 새 live kit는 opt-in 증분 전송과 관리자 인증을 제공합니다. 실제 앱 훅·원격 두 환경 운영 인수는 별도입니다.' if lang=='ko' else 'Use update for declared work or blockers and review for decisions bound to current files and criteria. Imported passes remain declarations. Task output conditions require human review; unsupported phase/project output conditions are rejected. The new live kit supplies opt-in incremental delivery and manager authentication. Actual provider hooks and remote two-environment acceptance require separate evidence.')]))

# Current primary flow; public sample and opt-in self-hosted runtime are separate.
for lang in ('ko','en'):
    PAGES['ai-pms'][lang][2].insert(0, ('live-sessions', '세션·북극성과 실시간 근거' if lang=='ko' else 'People → sessions → goals → company and team north stars', [
        ('사람의 세션에서 시작하기' if lang=='ko' else 'Start with a person’s sessions', '사람을 선택해 여러 환경과 프로젝트에 걸친 세션의 목표, 실행 생명주기와 목표 검증·인수를 확인합니다. 종료된 세션의 목표가 실패할 수도 있고, 열린 세션의 연결 작업 검증이 끝날 수도 있습니다. 연결 작업에서 계획·검사·문서 근거로 내려갑니다.' if lang=='ko' else 'Select a person to inspect session goals across environments and projects. Execution lifecycle and goal verification or acceptance are separate. An ended session can have failed goals; an open session can have verified work. Follow linked tasks to plans, checks and documents.'),
        ('북극성과 기여 근거' if lang=='ko' else 'North stars and contribution evidence', '회사·팀 지표의 단위·기간·기준값·목표값과 실측을 봅니다. 선언·미래·기간 밖 관측은 성과 판정에서 제외합니다. 기여 제안·연결 확인·정의 변경 후 재확인을 구별하며 기술 검사 통과를 사업 성과로 바꾸지 않습니다. 개인 목표는 독립적으로 유지할 수 있습니다.' if lang=='ko' else 'Compare metric units, periods, baselines, targets and measurements. Declared, future or out-of-period observations do not prove outcomes. Separate proposed links, confirmed declarations and reconfirmation after changes. Technical checks do not prove business impact. Personal goals may remain independent.'),
        ('개별 로그와 관리 변경 동기화' if lang=='ko' else 'Incremental logs and management changes', '선택 실행하는 송신기가 로컬 JSONL과 목표·작업·검사·승인 파일의 개별 변경을 감시합니다. 자체 호스팅 중앙 서비스는 인증·영속 저장·중복 방지·충돌 표시와 cursor 조회를 제공합니다. 연결 화면은 2초마다 변경을 조회하며 JSON 전체 재가져오기에 의존하지 않습니다. 실제 PC에서 중앙으로 보내는 외부 방향 연결을 사용합니다.' if lang=='ko' else 'The opt-in sender watches local JSONL and individual changes to goals, work, checks and approvals. The self-hosted central service provides authentication, durable storage, deduplication, visible conflicts and cursor queries. Connected dashboards poll every two seconds without full JSON reimport. Participants connect outbound from their environments.'),
        ('Kit와 실제 검증 경계' if lang=='ko' else 'Kit and validation boundaries', 'activity/logger.py health 명령은 마지막 기록·오류를 확인합니다. 오류에서도 에이전트를 막지 않는 훅 종료코드를 기록 성공으로 간주하지 않습니다. ZIP의 pms/README와 pms/specs/ai-pms-live/README.md에서 합성 로컬 중앙 실행을 시작하세요. 공개 Vercel은 합성 정적 예시입니다. 실제 앱 훅 설치·trust·원격 두 환경 전달은 별도 확인하며 설정이나 실제 로그를 자동 공개하지 않습니다.' if lang=='ko' else 'The activity/logger.py health command reports last writes and errors. Nonblocking hook exit codes do not prove capture success. Start the synthetic local central pilot with pms/README and pms/specs/ai-pms-live/README.md in the ZIP. Public Vercel remains a static synthetic example. Actual provider hook installation, trust and remote two-environment delivery need separate validation. Configuration and real logs are not published automatically.')]))
    title = '전체 계획에서\n현재 위치를 확인하기.' if lang=='ko' else 'See the whole plan\nand where work stands.'
    summary = '사람별 프로젝트 목표·각 Phase의 목표·참고한 API/MCP·달성 상태를 먼저 보고, 세부 기록은 별도 분석 근거에서 확인합니다.' if lang=='ko' else 'Start with each person’s project goals, phase goals, API/MCP references and achieved states; inspect detailed records in a separate evidence view.'
    PAGES['ai-pms'][lang] = (title, summary, PAGES['ai-pms'][lang][2])

# Human overview and evidence have different audiences; runtime contracts stay intact.
for lang in ('ko','en'):
    PAGES['ai-pms'][lang][2].insert(0, ('phase-flow', '목표와 단계 흐름' if lang=='ko' else 'Goals and phase flow', [
        ('기본 화면' if lang=='ko' else 'Default view', '사람 선택 → 프로젝트 목표 → 각 Phase의 목표·달성 상태 → 참고한 API·MCP 순서로 봅니다. 공동 프로젝트는 같은 카드에 참여자를 표시합니다. 프로젝트와 단계는 별도 주소에서 읽습니다.' if lang=='ko' else 'Select a person, then inspect project goals, phase goals and achieved states, and API/MCP references. Shared projects list participants on one card. Projects and phases have separate addresses.'),
        ('분석 근거는 별도 화면' if lang=='ko' else 'Evidence is separate', '세부 작업 WBS·검사 명령·문서 버전·세션·조직 지표는 기본 화면에 나열하지 않고 분석 근거에 보존합니다. 화면을 줄여도 수집·증분 전달·완료 조건을 줄이지 않습니다.' if lang=='ko' else 'Keep task WBS, check commands, document revisions, sessions and organizational metrics in a separate evidence view. A smaller default view does not reduce capture, incremental delivery or completion conditions.'),
        ('달성과 참조의 기준' if lang=='ko' else 'Achievement and reference basis', '단계 달성과 프로젝트 최종 인수는 별도입니다. 설정·선언·호출 관측·데이터 획득을 구별하며 Phase 연결이 없는 참조를 추정하지 않습니다. 실제 문서상 이력은 현재 runner 통과로 바꾸지 않습니다.' if lang=='ko' else 'Phase achievement and final project acceptance are separate. Distinguish configuration, declarations, observed calls and acquired data. Do not infer phase references or convert documentary history into current runner passes.')]))
    PAGES['ai-pms'][lang][2].insert(0, ('human-analysis', '로그를 분석과 행동으로 연결하기' if lang=='ko' else 'Turn logs into analysis and action', [
        ('목표 중복은 제안만' if lang=='ko' else 'Goal overlap is a proposal', '목표·대상·성공 기준·범위를 비교해 중복 후보와 이유를 제안합니다. 같은 기술이나 공동 목표만으로 중복이라고 하지 않습니다. 사람이 협업·독립 유지·기각을 판단하며 모델이 자동 합치기나 완료 판단을 하지 않습니다.' if lang=='ko' else 'Compare intended outcomes, audiences, success criteria and scope to propose overlap with reasons. Shared technology or team goals alone do not imply duplication. People choose collaboration, independent work or dismissal; models never merge projects or change completion.'),
        ('그 외 로그의 쓰임' if lang=='ko' else 'Uses for other logs', '실패→수정→재검사 이력은 반복 막힘, 현재 계획·검사는 검증 누락, 스킬·규칙·MCP 기록은 개선 후보를 찾는 근거입니다. 관리자에게는 근거와 권장 행동이 있는 결과만 보여줍니다. 로그 수를 생산성으로 환산하지 않습니다.' if lang=='ko' else 'Failure→fix→rerun histories support recurring-blocker analysis, current plans and checks reveal verification gaps, and skill/rule/MCP records support improvement proposals. Surface findings with evidence and recommended actions; counts are not productivity.'),
        ('현재 준비 범위' if lang=='ko' else 'Current preparation boundary', 'ZIP의 pms/docs/human-view-and-analysis.md에 구분 기준이 있고 pms/scripts/prepare_goal_analysis.py는 목표 비교 입력을 생성합니다. 모델은 호출하지 않습니다. 실제 AI 분석·경고 검증·수락/기각 저장은 아직 미구현입니다. 실제 자료는 비공개로 유지하고 공개 Vercel은 합성 샘플로 사용합니다.' if lang=='ko' else 'The ZIP contains pms/docs/human-view-and-analysis.md and pms/scripts/prepare_goal_analysis.py to prepare comparison input without model calls. Model execution, validated findings and acceptance/dismissal storage remain unimplemented. Keep actual data private; public Vercel uses synthetic examples.')]))

# Shareable portfolio-level ELI20 page lives in the existing PMS sample app.
for lang, heading, text in [
    ('ko', 'Kit와 AI PMS의 전체 그림', 'Kit의 범위, PMS의 목적·구성, 실제 작업 흐름, 구현/검증과 다음 운영 인수를 ELI20 전체 설명 페이지에서 한 주제씩 읽을 수 있습니다.'),
    ('en', 'The full picture of Kit and AI PMS', 'The Korean ELI20 overview explains Kit coverage, PMS purpose and architecture, a concrete workflow, implementation evidence and the next operational acceptance.')]:
    PAGES['ai-pms'][lang][2].insert(0, ('overview', heading, [(heading, text)]))


# Rensei-inspired experience: a minimal human view and a separate read-only queue.
for lang in ('ko', 'en'):
    sections = PAGES['ai-pms'][lang][2]
    phase_items = [
        ('사람과 전체 계획' if lang=='ko' else 'People and the whole plan',
         '사람 선택 → 참여 프로젝트 → 전체 Phase 흐름 → 별도 Phase 상세로 이동합니다. 공동 프로젝트는 같은 카드에 참여자를 표시합니다. 기본 정보는 프로젝트 목표, Phase 목표, 달성 상태, 참고한 API·MCP입니다. 전체 흐름은 목표·담당에서 최종 인수까지 이어집니다.' if lang=='ko' else
         'Select a person → participating projects → the whole phase flow → a separate phase detail. Shared projects list participants on one card. The basic information is project goals, phase goals, achievement states and API/MCP references. The flow connects goals and owners to final acceptance.'),
        ('흐름과 상태의 의미' if lang=='ko' else 'Flow and state meaning',
         '연결선은 계획에 적힌 순서입니다. 선언되지 않은 의존성이나 날짜·기간·ETA를 만들지 않습니다. 단계 달성과 프로젝트 최종 인수는 구분하고, 달성·미달성·근거 없음은 기존 판정 결과를 그대로 표시합니다. 모바일에서는 같은 내용을 세로 흐름으로 읽습니다.' if lang=='ko' else
         'Connectors show the order in the plan. They do not invent dependencies, dates, durations or ETAs. Phase achievement and final project acceptance remain separate. Achieved, unmet and no-evidence states come from existing decisions. Mobile presents the same meaning in a vertical flow.'),
        ('상세와 분석 근거' if lang=='ko' else 'Detail and evidence',
         'Phase 상세는 목표·달성 상태·API/MCP 세 항목을 유지합니다. 실제 판단 항목이 있으면 짧은 다음 판단 요약과 별도 처리함 링크를 보여줍니다. 작업 WBS·Gantt, 검사 명령·문서·세션·원본은 분석 근거에 보존하며 기본 상세에 전부 쌓지 않습니다.' if lang=='ko' else
         'Phase detail keeps goals, achievement and API/MCP references. When real attention items exist, it adds a short next-decision summary and a separate queue link. Task WBS/Gantt, check commands, documents, sessions and original records remain in the evidence view instead of filling the basic detail.'),
        ('참조와 문서상의 이력' if lang=='ko' else 'References and documentary history',
         '설정·선언·호출 관측·데이터 획득을 구분합니다. 프로젝트 참조를 특정 Phase의 참조로 추정하지 않습니다. 문서상의 진척은 문서 날짜·발췌 출처를 보여주며 현재 runner 검사·인수는 미확인으로 유지합니다.' if lang=='ko' else
         'Distinguish configuration, declarations, observed calls and acquired data. Project references are not inferred as phase references. Documentary progress shows document dates and excerpt sources while current runner checks and acceptance remain unverified.')]
    for i, (sid, heading, items) in enumerate(sections):
        if sid == 'phase-flow':
            sections[i] = (sid, '목표와 전체 단계 흐름' if lang=='ko' else 'Goals and the whole phase flow', phase_items)
    sections.insert(2, ('attention-queue', '판단 필요 처리함' if lang=='ko' else 'Attention queue', [
        ('기본 화면과 별도 처리함' if lang=='ko' else 'Overview and separate queue',
         '기본 화면에서는 판단 필요 수와 링크만 표시합니다. 전체 처리함과 프로젝트 처리함은 별도 주소에서 열며 전체 처리함은 선택한 사람 필터를 유지합니다. 현재 work.interventions의 담당자·요청 이유·다음 행동과 관련 작업/단계 상세를 연결합니다.' if lang=='ko' else
         'The overview shows an attention count and link. Portfolio and project queues have separate addresses; the portfolio queue retains the selected person filter. Items connect current work.interventions owners, reasons and next actions to related task or phase detail.'),
        ('귀속과 현재 근거' if lang=='ko' else 'Ownership and current evidence',
         '정상 ready/in_progress를 모두 긴급 요청으로 바꾸지 않습니다. 담당자가 없거나 Phase gate만 있는 항목은 프로젝트 범위로 표시합니다. 같은 Phase·같은 이유는 근거별로 묶어 펼치고 최신 snapshot에서 다시 계산합니다. 선언된 다음 행동이 없으면 추측하지 않습니다.' if lang=='ko' else
         'Ordinary ready/in_progress states do not all become urgent requests. Items without an owner, or with only a phase gate, stay at project scope. Repeated phase/reason items are grouped with expandable evidence and recalculated from the latest snapshot. Missing declared next actions are not guessed.'),
        ('읽기와 실행의 경계' if lang=='ko' else 'Reading and execution boundaries',
         '처리함은 읽기 전용입니다. 문서 기준의 막힘·다음 행동과 현재 검사 근거를 항목마다 구분하며 문서 기록을 현재 검사 요청으로 승격하지 않습니다. 권한 부여·승인·원격 실행·AI 경고 생성 기능은 추가하지 않습니다.' if lang=='ko' else
         'The queue is read-only. Each item distinguishes documentary blockers or next actions from current check evidence; documentary records never become current check requests. The queue adds no permission grants, approvals, remote execution or AI-warning generation.')]))
    sections.append(('experience-boundary', '이번 개선과 남은 인수' if lang=='ko' else 'This improvement and remaining acceptance', [
        ('채택한 범위' if lang=='ko' else 'Adopted scope',
         'Rensei 조사에서 전체 Phase 흐름, 별도 판단 필요 처리함, 기본 상세 분리와 탐색 안정성을 이번 화면 개선에 적용합니다. 기존 검사 판정·현재 승인 유효성·세션→작업→Phase 근거·증분 갱신을 유지합니다. 20개 제안 전체나 실행 제어·AI 분석을 구현한 것은 아닙니다.' if lang=='ko' else
         'This experience applies whole-phase flow, a separate attention queue, compact detail and stable navigation from the Rensei assessment. It retains existing check decisions, current approval validity, session→task→phase evidence and incremental updates. It does not implement all20 proposals, execution control or AI analysis.'),
        ('코드 구조와 확인' if lang=='ko' else 'Architecture and verification',
         'ZIP의 pms/docs/rensei-experience.md는 채택 범위와 검증 경계를, pms/docs/project-architecture.md는 정본 파일의 역할을 설명합니다. 프로젝트만 추출한 Graphify AST는 소스 탐색 자료이며 실제 통합·원격 전달·검사 커버리지의 증거가 아닙니다. 데스크톱 사용을 우선합니다. DOM 회귀검사와 실제 데스크톱 화면·이동·갱신 검증을 구분하며, 모바일 검증은 이번 인수 범위에서 제외합니다.' if lang=='ko' else
         'The ZIP includes pms/docs/rensei-experience.md for adoption and verification boundaries and pms/docs/project-architecture.md for canonical source responsibilities. Project-only Graphify AST output helps source navigation; it does not prove runtime integration, remote delivery or test coverage. Desktop use is the priority. DOM regressions and actual desktop rendering, navigation and update acceptance remain separate; mobile verification is excluded from this acceptance scope.')]))


# Latest visual management: primary WBS and a single meaningful session history.
for lang in ('ko', 'en'):
    sections = PAGES['ai-pms'][lang][2]
    for i, (sid, heading, items) in enumerate(sections):
        if sid == 'phase-flow':
            sections[i] = (sid, '목표와 전체 작업 계획' if lang == 'ko' else 'Goals and the full work plan', [
                ('기본은 계층형 WBS' if lang == 'ko' else 'Hierarchical WBS first', '프로젝트의 Phase 목표·원자 작업·담당·상태·단계 종료 검사·최종 인수를 같은 계획판에서 읽습니다. 사람을 선택해도 공동 전체 계획을 유지하고 해당 책임을 강조합니다. Phase 작업을 펼쳐 하나의 작업 상세로 이동합니다.' if lang == 'ko' else 'Read phase goals, atomic tasks, owners, states, phase exit checks and final acceptance on one project plan. Selecting a person keeps the whole shared plan and emphasizes their responsibility. Expand phase tasks and open one task detail.'),
                ('기간과 검증을 추측하지 않기' if lang == 'ko' else 'Do not infer duration or verification', '유효하게 연결된 명시 일정만 날짜축으로 표시하고, 없는 계획은 단계축으로 표시합니다. 상태는 텍스트·기호·색으로 읽으며 문서상 완료와 현재 검사 통과를 구분합니다. 완료 수를 노력·생산성 비율로 환산하지 않습니다.' if lang == 'ko' else 'Only valid explicitly bound schedules use a date axis; otherwise the plan uses a phase axis. Text, symbols and color communicate state, distinguishing documentary completion from current check success. Completion counts are not effort or productivity percentages.'),
                ('질문에서 근거로' if lang == 'ko' else 'From questions to evidence', '작업 결과·실행 이력·참고 자료에서 필요한 근거를 엽니다. 기존 검사·문서·판단·인계·MCP 원문은 보존하되 9개 기술 분류 탭을 기본 경험으로 강요하지 않습니다. 회사·팀 목표의 확인된 연결과 개인 목표의 독립성을 유지합니다.' if lang == 'ko' else 'Open relevant evidence from work results, execution history and references. Existing checks, documents, decisions, handoffs and MCP records remain available without forcing nine technical categories as the default experience. Confirmed organization links and independent personal goals remain distinct.')])
    sections.append(('visual-session-history', '세션을 읽는 방법' if lang == 'ko' else 'Reading session history', [
        ('한 실행을 한 번 표시' if lang == 'ko' else 'One entry per observed execution', '목표·담당·실행 상태·목표 검사·시각과 연결 작업을 한 이력에서 읽고 내부 ID는 접습니다. 사용자·환경·출처 귀속을 보존하며 중복 raw 목록을 덧붙이지 않습니다. 세션 종료는 목표 달성을 뜻하지 않고 수집이 없으면 기록 없음으로 표시합니다.' if lang == 'ko' else 'Read the goal, owner, execution state, goal checks, time and linked tasks in one history, with internal IDs collapsed. User, environment and source identity are preserved without appending a duplicate raw list. Session termination is not goal achievement; absent capture is shown as no record.'),
        ('실제 화면 검증은 별도' if lang == 'ko' else 'Rendered acceptance is separate', 'ZIP의 pms/docs/visual-management.md에 화면 역할과 검증 범위를 설명합니다. AI 전문가 소스 의견과 DOM 회귀는 실제 사람의 수락이나 데스크톱 가독성 확인이 아닙니다. 데스크톱 이동·선택·새로고침은 실제 브라우저에서 확인하며 모바일 검증은 이번 인수에서 제외합니다.' if lang == 'ko' else 'The ZIP includes pms/docs/visual-management.md for screen responsibilities and verification scope. AI source reviews and DOM regressions are neither human acceptance nor proof of desktop readability. Desktop navigation, selection and reload need a real browser; mobile verification is excluded from this acceptance.')]))

# Full STE editions of the Kit understanding guide; section identities match ELI20.
PAGES['ste'] = {
 'ko': ('Harness Kit은\n어떻게 작업을 지원하나요?',
        'Harness Kit의 목적, 기본 용어, 구성요소와 작업 흐름을 한국어 STE 방식으로 설명합니다. 각 구성요소의 책임과 적용·검증 범위를 확인하세요.', [
  ('start', '다른 환경에 같은 운영 구성을 옮깁니다', [
   ('모델이 같아도 결과는 달라질 수 있습니다', '에이전트는 지침을 읽고 도구를 사용합니다. 실행 전 검사와 완료 확인 방법도 작업에 영향을 줍니다. 같은 모델을 써도 이 구성이 다르면 결과가 달라질 수 있습니다. Harness Kit은 이 운영 구성을 다른 환경에 옮기기 위한 참고 자료입니다.'),
   ('에이전트와 하네스의 역할은 다릅니다', '에이전트는 사용자 요청을 해석합니다. 도구를 호출해 작업을 실행합니다. 하네스는 에이전트 주위의 지침·스킬·훅·검증 절차입니다. Harness Kit은 하네스를 구성하는 파일과 적용 안내를 제공합니다. Kit 자체는 모델이나 독립 실행 프로그램이 아닙니다.'),
   ('아래 순서로 읽으세요', '기본 용어를 먼저 확인하세요. 각 구성요소의 책임과 연결을 확인하세요. 가상의 CSV 내보내기 작업을 따라가세요. 마지막으로 Kit의 포함 범위와 실제로 확인할 항목을 구분하세요.')]),
  ('terms', '기본 용어를 확인합니다', [
   ('지침 · AGENTS.md / CLAUDE.md', '지침은 환경과 프로젝트의 규칙을 담습니다. 에이전트는 작업할 때 이 규칙을 참고합니다. 지침에는 승인 경계와 프로젝트 명령을 적습니다.'),
   ('스킬 · SKILL.md', '스킬은 특정 작업의 절차와 판단 기준을 담습니다. 에이전트는 작업에 필요한 스킬을 읽습니다. 설치된 스킬이 모든 작업에서 자동 실행되는 것은 아닙니다.'),
   ('훅', '훅은 도구 호출이나 세션 이벤트에 연결된 자동 검사입니다. 훅은 지정된 위험 행동을 차단할 수 있습니다. 훅이 결과의 의미나 품질을 대신 판단하지는 않습니다.'),
   ('도구와 검증', '도구는 파일·셸·외부 서비스의 실제 상태를 바꿉니다. 테스트와 화면 확인은 바뀐 결과를 관찰합니다. 검사 통과와 사용자 문제 해결은 따로 확인해야 합니다.')]),
  ('parts', '요청에서 결과까지 책임을 연결합니다', [
   ('사용자 요청 → 에이전트', '사용자 요청이 목표와 허용 범위를 정합니다. 에이전트는 필요한 파일을 읽습니다. 에이전트는 작업을 계획하고 실행합니다.'),
   ('지침·스킬 → 작업 방법', '지침은 환경의 지속 규칙을 제공합니다. 스킬은 해당 작업의 전문 절차를 제공합니다. 지침과 스킬은 스스로 파일을 수정하지 않습니다.'),
   ('훅 → 도구 실행', '훅은 정의된 도구 호출 경계에서 검사합니다. 검사에 걸리면 도구 호출을 차단할 수 있습니다. 허용된 도구가 파일이나 외부 시스템의 상태를 바꿉니다.'),
   ('검증 → 보고', '에이전트는 테스트와 실제 화면으로 결과를 확인합니다. 확인한 결과를 보고합니다. 아직 확인하지 못한 범위도 함께 보고합니다.')]),
  ('flow', '가상 작업 · CSV 내보내기 버튼을 추가합니다', [
   ('1 · 요청을 확인합니다', '사용자가 기존 목록 화면의 CSV 내보내기를 요청합니다. 에이전트는 데이터 형식을 확인합니다. 완료 조건을 확인합니다. DB나 API 계약 변경이 필요한지도 먼저 판단합니다.'),
   ('2 · 관련 코드를 찾습니다', '에이전트는 프로젝트 지침을 읽습니다. 목록 화면과 내보내기 관련 소스를 찾습니다. Graphify 그래프가 있으면 탐색에 사용할 수 있습니다. 그래프가 최신인지 확인합니다. 그래프를 참고한 뒤에도 현재 소스를 읽습니다.'),
   ('3 · 허용 범위에서 구현합니다', '에이전트는 필요한 스킬을 적용합니다. 파일을 수정합니다. Ponytail은 불필요한 구현을 줄이는 판단을 돕습니다. 훅은 비밀정보 기록이나 기존 테스트 삭제처럼 정의된 행동을 차단할 수 있습니다.'),
   ('4 · 실제 결과를 확인합니다', '에이전트는 CSV의 내용을 확인합니다. 실제 화면에서 버튼을 누릅니다. 다운로드 파일과 모바일 화면을 확인합니다. 테스트가 통과해도 파일 내용이나 모바일 화면이 올바르다고 단정하지 않습니다.'),
   ('5 · 완료 범위를 판단합니다', '에이전트는 확인한 결과와 남은 한계를 보고합니다. 작업 중 DB 스키마나 API 계약 변경이 필요해지면 기존 허용 범위를 확인합니다. 변경이 그 범위를 벗어나면 실행 전에 승인을 받습니다.')]),
  ('concepts', '반복해서 쓰는 다섯 장치를 구분합니다', [
   ('철칙 · 승인 경계', '철칙은 환경 고유의 실행 경계입니다. 에이전트는 행동이 사용자 요청의 허용 범위에 포함되는지 확인합니다. 이미 허용된 범위는 다시 묻지 않습니다. 새 DB 변경이나 외부 실행이 필요하면 기존 범위에 포함되는지 확인합니다. 일반적인 구현 판단은 에이전트에게 맡깁니다. 모든 행동에 승인을 요구하면 작업이 멈춥니다.'),
   ('하네스 · 운영 구성', '하네스는 지침에서 도구 실행과 결과 확인까지 연결하는 운영 구성입니다. 환경 사실은 진입점에 둡니다. 좁은 기계적 조건은 훅에 둡니다. 작업 절차는 스킬에 둡니다. 파일 배치와 로컬 검사 통과만으로 실제 앱의 호출을 입증하지는 못합니다.'),
   ('루프 · 변경과 재검증', '루프는 기준선 확인 → 변경 → 검증 → 판단의 반복입니다. 사용자 목적에 맞지 않아 거절된 결과도 실패로 봅니다. 목적이 분명히 어긋나면 바로 수정합니다. 같은 접근이 두 번 실패하면 세 번째 시도 전에 가정을 확인하거나 접근을 바꿉니다. 진행할 수 있는 다른 작업은 계속합니다. 문서나 자동화 수로 성숙도를 판단하지 않습니다. 근거 없이 같은 시도를 반복하거나 너무 일찍 포기하지 않습니다.'),
   ('그래프 · 관계와 의존성', '그래프는 작업이나 구성요소의 관계를 보여줍니다. 작업 A와 B를 각각 검증할 수 있으면 독립된 가지로 표시합니다. 두 작업을 합친 뒤 통합 결과를 검증합니다. 실패 후 돌아가는 경로도 표시할 수 있습니다. 단순한 순서에는 목록이면 충분합니다. 관계를 더 잘 이해할 수 있을 때 그래프의 유지 비용을 감수합니다.'),
   ('스킬 · 필요할 때 읽는 절차', '스킬은 반복되는 전문 작업에 쓸 절차와 기준입니다. 에이전트는 현재 요청에 맞는 스킬을 선택합니다. 절차를 적용한 뒤 결과를 확인합니다. 작업 패킷이 완성되어 있어도 부모의 모델과 추론 설정을 기본으로 상속합니다. 한 번의 요청을 모든 작업의 의무 절차로 확대하지 않습니다. 스킬이 현재 사용자 요청을 바꾸어서는 안 됩니다.')]),
  ('boundary', '포함 범위와 검증 범위를 구분합니다', [
   ('Kit에 포함됩니다', 'Kit은 Codex·Claude용 지침·훅·스킬의 공개 가능한 구현 파일을 제공합니다. 적용 안내도 제공합니다. 압축 파일은 자동 설치 프로그램이 아닙니다.'),
   ('별도로 설치하거나 설정합니다', 'Ponytail과 Graphify는 외부 선택 도구입니다. 별도로 설치합니다. 모델, 로그인, API 키, MCP 연결, 개인 메모리와 프로젝트 권한은 Kit에 포함되지 않습니다. 대상 환경에서 각각 설정합니다.'),
   ('세 단계로 확인합니다', '파일을 배치합니다. 새 세션에서 지침과 스킬이 로드되는지 확인합니다. 실제 작업에서 훅 호출과 사용자 화면을 확인합니다. 정적 검사만으로 앱의 훅 전달, 비용·시간 절감, 최종 작업 품질을 증명하지 않습니다.')]),
  ('next', '사용하는 에이전트에 적용합니다', [
   ('Codex 구성', '현재 지침·안전 훅·스킬을 백업하세요. Kit의 파일과 현재 설정을 비교하세요. 필요한 항목을 병합하세요. 로드와 실제 동작을 확인하세요.'),
   ('Claude 구성', '현재 지침·안전 훅·Stop 훅·스킬을 백업하세요. Kit의 파일과 현재 설정을 비교하세요. 필요한 항목을 병합하세요. 로드와 실제 동작을 확인하세요.'),
   ('스킬 설치', '스킬 안내에서 ELI20·STE 스킬의 위치와 사용 방법을 확인하세요. Ponytail과 Graphify의 별도 설치·확인 방법도 확인하세요.')])]),
 'en': ('How does Harness Kit\nsupport agent work?',
        'This STE-oriented guide explains the purpose, terms, components, work flow and verification limits of Harness Kit.', [
  ('start', 'Transfer the operating setup to another environment', [
   ('The same model can give different results', 'An agent reads instructions and uses tools. Checks before execution and checks for completion also affect the work. Results can differ if this setup changes, even with the same model. Harness Kit provides references for transferring this operating setup.'),
   ('The agent and harness have different jobs', 'The agent interprets the user request. It calls tools to do the work. The harness contains instructions, skills, hooks and verification procedures around the agent. Harness Kit provides setup files and guides. The kit is not a model or an independent program.'),
   ('Follow this reading order', 'Read the terms first. Identify each component and its connections. Follow the fictional CSV export task. Then distinguish the kit contents from the checks that need real execution.')]),
  ('terms', 'Identify the basic terms', [
   ('Instructions · AGENTS.md / CLAUDE.md', 'Instructions contain environment and project rules. The agent reads these rules during its work. They identify approval boundaries and project commands.'),
   ('Skill · SKILL.md', 'A skill contains procedures and criteria for a particular task. The agent reads a skill when the task needs it. An installed skill does not run automatically for every task.'),
   ('Hook', 'A hook is an automatic check at a tool call or session event. It can block defined risky actions. It does not judge the meaning or quality of the result.'),
   ('Tools and verification', 'Tools change the actual state of files, shells or external services. Tests and interface checks observe those changes. A passing check does not establish that the user problem is solved.')]),
  ('parts', 'Connect responsibilities from request to result', [
   ('User request → agent', 'The user request defines the goal and authorization scope. The agent reads the necessary files. The agent plans and executes the work.'),
   ('Instructions and skills → work method', 'Instructions provide durable environment rules. Skills provide specialist procedures for the task. Instructions and skills do not edit files by themselves.'),
   ('Hooks → tool execution', 'Hooks check defined tool-call boundaries. A matching condition can block a call. A permitted tool changes files or external systems.'),
   ('Verification → report', 'The agent uses tests and the actual interface to check the result. It reports confirmed results. It also reports the scope that remains unverified.')]),
  ('flow', 'Fictional task · add a CSV export button', [
   ('1 · Confirm the request', 'The user requests CSV export from an existing list. The agent checks the data format. It checks the completion criteria. It first determines whether a database or API contract change is necessary.'),
   ('2 · Find the code', 'The agent reads project instructions. It finds the list interface and export code. An existing Graphify graph can help navigation. The agent checks if that graph is current. The agent still reads the current source after it uses the graph.'),
   ('3 · Implement within scope', 'The agent applies the necessary skill. It edits the files. Ponytail helps avoid unnecessary code. A hook can block defined actions, such as recording secrets or deleting existing tests.'),
   ('4 · Check the actual result', 'The agent checks the CSV content. It clicks the actual button. It checks the downloaded file and the mobile interface. Passing tests alone do not establish that the file content or mobile interface is correct.'),
   ('5 · Decide completion scope', 'The agent reports confirmed results and remaining limits. If a database schema or API contract change becomes necessary, it checks existing authorization. If the change is outside that scope, it obtains approval before execution.')]),
  ('concepts', 'Distinguish five recurring mechanisms', [
   ('Rules · approval boundaries', 'Rules define environment-specific execution boundaries. The agent checks if an action is within the user authorization. It does not ask again about authorized work. It checks whether a new database change or external operation is within that scope. Leave ordinary implementation decisions to the agent. Requiring approval for every action stops progress.'),
   ('Harness · operating setup', 'The harness connects instructions to tools and observed results. Put environment facts in the entry point. Put narrow mechanical conditions in hooks. Put work procedures in skills. Files and local checks do not prove that the application calls the hooks correctly.'),
   ('Loop · change and verify again', 'A loop repeats the baseline check, change, verification and decision. A result rejected for missing the user purpose is also a failure. Correct a clear purpose mismatch immediately. After two failures with the same approach, check assumptions or change the approach before a third attempt. Continue other work that can progress. Document counts and automation counts do not establish maturity. Do not repeat without evidence or stop too early.'),
   ('Graph · relationships and dependencies', 'A graph shows relationships between tasks or components. If tasks A and B can be checked separately, show them as independent branches. Check the integrated result after the tasks are combined. A graph can also show a return path after failure. A list is sufficient for a simple sequence. Use a graph when its explanatory value justifies its maintenance cost.'),
   ('Skill · procedure when needed', 'A skill provides procedures and criteria for recurring specialist work. The agent selects a skill for the current request. It checks the result after it applies the procedure. A complete task packet still inherits the parent model and reasoning settings by default. Do not make a one-time request mandatory for every task. A skill must not replace the current user request.')]),
  ('boundary', 'Distinguish contents and verification limits', [
   ('Included in the kit', 'The kit provides public implementation files for Codex and Claude instructions, hooks and skills. It also provides setup guides. The ZIP is not an automatic installer.'),
   ('Install or configure separately', 'Ponytail and Graphify are optional external tools. Install them separately. Models, logins, API keys, MCP connections, personal memory and project permissions are not in the kit. Configure these in the target environment.'),
   ('Check three levels', 'Place the files. Check instruction and skill loading in a new session. Check actual hook calls and the user interface during real work. Static checks do not prove application hook delivery, cost or time savings, or final work quality.')]),
  ('next', 'Apply the kit to your agent', [
   ('Codex configuration', 'Back up the current instructions, safety hook and skills. Compare the kit files with the current setup. Merge the necessary entries. Check loading and actual behavior.'),
   ('Claude configuration', 'Back up the current instructions, safety hook, Stop hook and skills. Compare the kit files with the current setup. Merge the necessary entries. Check loading and actual behavior.'),
   ('Skill installation', 'Read the skills guide for ELI20 and STE installation locations and usage. Read the separate installation and check steps for Ponytail and Graphify.')])])
}

# Current PMS packaging scope: local hooks in Kit, full adoption in GitHub.
PAGES['ai-pms'] = {'ko': ('AI PMS 훅 추가', '로컬 기록을 확인한 다음 중앙 대시보드 도입으로 이어갑니다.', [('purpose', 'Kit에서 훅을 추가하고 GitHub에서 PMS를 도입합니다', [('포함 범위', 'Kit의 PMS 구성은 로컬 훅 기록기입니다. 기존 Codex·Claude 구성과 안전 훅에 기록 명령을 병합합니다. 중앙 대시보드·수신기·송신기는 GitHub에서 별도로 도입합니다. Kit은 자동 설치 프로그램이 아닙니다.'), ('도입 가이드', 'https://github.com/heejunyoo/ai-pms/blob/main/docs/adoption.md 에서 다운로드 → 훅 확인 → 프로젝트 등록 → 대시보드 → 인증된 로컬 파일럿 순서를 따르세요.')]), ('flow', '설치와 관측을 차례로 확인합니다', [('1 · 파일 배치', 'implementation.zip의 activity/를 ~/.agents/harness-activity/에 복사합니다. logger.py와 connectivity.py를 함께 유지합니다. python3 ~/.agents/harness-activity/test_logger.py 로 로컬 검사를 실행합니다.'), ('2 · 기존 설정 병합', 'Codex 또는 Claude 안내에 따라 기존 훅 설정을 백업하고 hook --source codex 또는 hook --source claude 명령을 병합합니다. SessionStart·PreToolUse·PostToolUse·Stop 등 실제 앱 이벤트를 새 세션에서 확인합니다. 기존 안전 훅을 보존합니다.'), ('3 · GitHub로 이어갑니다', '프로젝트 ID·사용자·환경을 검토해 등록하고 목표·단계·작업을 명시합니다. 정적 프로젝트 화면과 인증된 Live 파일럿은 별도 절차입니다. 원격 운영에는 추가 보안·운영 검증이 필요합니다.')]), ('connectivity', '연결 기록이 의미하는 범위를 확인합니다', [('메타데이터', '선택 pms_metadata는 operation·resources·artifact_refs만 받습니다. --resource-map은 검토한 로컬 매핑을 사용하며 evidence를 declared로 표시합니다. input/output 근거, artifact revision은 명시적으로 구분합니다.'), ('관측 한계', 'duration_ms는 이벤트가 제공한 값만 기록합니다. 도구 호출 성공은 데이터 활용·사용자 목적 달성·프로젝트 완료를 증명하지 않습니다. 원본 input/output, URL·SQL·비밀정보는 공유하지 않습니다.')]), ('logging', '훅 기록과 사람이 입력한 근거를 구분합니다', [('기록 위치', '기본 기록은 ~/.local/state/harness-activity 아래의 로컬 JSONL입니다. 프로젝트 경로 인덱스는 개인 정보입니다. 선택해 검토한 기록만 공유하세요. 누락된 ID는 누락 상태로 남깁니다.'), ('확인 수준', 'stdin 테스트 통과 → 실제 앱 훅 호출 확인 → 중앙 송수신 확인은 각각 다른 증거입니다. 이 Kit 빌드는 실제 앱의 훅 신뢰 승인이나 원격 다중 사용자 전달을 설치·증명하지 않습니다.')]), ('boundary', '샘플과 실제 적용의 경계를 확인합니다', [('기본 도입 예시', 'https://ai-pms-dashboard.vercel.app 은 가상 프로젝트를 실제 도입과 같은 문서 기반 화면으로 보여줍니다. 계획이 있어도 현재 실행은 미확인입니다. recorded-example.html은 기록이 채워진 별도 합성 예제입니다.'), ('전체 자료', 'https://ai-pms-dashboard.vercel.app/report.html 에서 제품 설명을 읽고 https://github.com/heejunyoo/ai-pms 에서 전체 소스와 검증 명령을 받으세요. Kit ZIP에는 중앙 pms/ runtime이 없습니다. 기존 오프라인 뷰어와 수동 기록 도구는 선택적 로컬 참고 자료입니다.')])]), 'en': ('Add AI PMS hooks', 'Verify local capture, then continue to central dashboard adoption.', [('purpose', 'Add hooks with Kit; adopt PMS through GitHub', [('Scope', 'The PMS part of Kit provides local hook capture. Merge logging commands into existing Codex or Claude settings and retain safety hooks. Adopt the central dashboard, receiver and sender separately from GitHub. The ZIP is not an installer.'), ('Adoption guide', 'Follow https://github.com/heejunyoo/ai-pms/blob/main/docs/adoption.md : download, verify hooks, register projects, render the dashboard, then try the authenticated local pilot.')]), ('flow', 'Check setup and observations in order', [('1 · Place files', 'Copy activity/ from implementation.zip to ~/.agents/harness-activity/. Keep logger.py and connectivity.py together. Run python3 ~/.agents/harness-activity/test_logger.py.'), ('2 · Merge existing settings', 'Follow the Codex or Claude guide. Back up existing settings and merge hook --source codex or hook --source claude. Verify actual SessionStart, PreToolUse, PostToolUse and Stop events in a new session. Preserve safety hooks.'), ('3 · Continue in GitHub', 'Review project, actor and environment identities; explicitly author goals, phases and tasks. Static views and authenticated Live pilots have separate instructions. Remote operation requires further security and operating validation.')]), ('connectivity', 'Understand connection evidence', [('Metadata', 'Optional pms_metadata accepts operation, resources and artifact_refs only. --resource-map uses reviewed local mappings with declared evidence. Distinguish explicit input/output evidence and artifact revision.'), ('Limits', 'duration_ms is recorded only when supplied by the event. Successful tool calls do not prove data usage, user acceptance or project completion. Never share raw input/output, URLs, SQL or secrets.')]), ('logging', 'Separate observed hooks from authored evidence', [('Local storage', 'Default JSONL records are under ~/.local/state/harness-activity. The local path index is private. Share only selected, reviewed records. Missing native IDs remain missing.'), ('Verification levels', 'Passing stdin tests, observing native application hooks, and verifying central transport are separate evidence. This build does not install or prove native hook trust or remote multi-user delivery.')]), ('boundary', 'Understand the sample and deployment boundary', [('Default example', 'https://ai-pms-dashboard.vercel.app displays fictional projects in the same document-first view used for adoption. Plans do not confirm current execution. recorded-example.html separately retains synthetic recorded operations.'), ('Full project', 'Read https://ai-pms-dashboard.vercel.app/report.html and get the full source from https://github.com/heejunyoo/ai-pms. Kit ZIP has no central pms/ runtime. Existing offline viewers and manual recorders remain optional local references.')])])}


# Selective STE composition: retain workflow contracts and bilingual section parity.
_ste_applications = {
    'ko': ('기존 스킬과 프로젝트에 적용하기', [
        ('AI PMS 안내', '도입 안내는 사전 조건 → 실행 → 확인 근거 → 실패 시 행동으로 나눕니다. 화면은 진행 막힘·확인되지 않음·문서상 완료·현재 검증 완료를 구분합니다. 원인·담당자·다음 행동은 기존 기록만 사용합니다. 중앙 PMS의 도입 절차는 GitHub 안내를 따릅니다.'),
        ('Handoff 절차', '작업 패킷의 행위자·선행조건·행동·확인할 결과·중단 조건을 드러냅니다. 원문 인용, JSON 키, 명령과 기대 exit code는 유지합니다. 문장 수정은 독립 검토나 실제 인수 검증을 대신하지 않습니다.'),
        ('ELI20 전체 설명', '전체 설명을 먼저 구성한 뒤 필요한 문장을 다듬습니다. STE 판본도 같은 제품 범위의 용어·책임·연결·흐름·사례·조건·예외·근거와 한계를 담습니다. 비교 사례 하나로 전체 설명을 대신하지 않습니다.'),
        ('분석과 검증 결과', 'expert-panel·independent-panel·improvement-loop의 최종 결과에서 사실·추론·미검증, 다음 행동과 완료 근거를 구분합니다. 독립 패널은 초안과 교차검토를 마친 뒤 문장을 다듬습니다. 반증·소수의견·결론이 뒤집히는 조건과 판정 규칙을 유지합니다.'),
        ('선택 적용', '모든 작업에 STE를 강제하지 않습니다. 설치된 스킬을 기술 문장 명료화가 필요할 때 사용합니다. 자연스러운 문체도 요청한 경우에만 추가로 다듬고 조건·부정·의무·범위를 다시 확인합니다. 영어 승인 사전은 별도 확인하며 한국어는 자체 가이드입니다.')]),
    'en': ('Apply STE with existing skills and projects', [
        ('AI PMS guidance', 'Separate prerequisites, actions, verification evidence and failure handling. Distinguish blocked work, unknown status, documentary completion and current verification. Use recorded causes, owners and next actions only. Follow the GitHub guide for central PMS adoption.'),
        ('Handoff procedures', 'Identify the actor, prerequisite, action, expected result and stopping condition. Preserve source quotations, JSON keys, commands and expected exit codes. Clear wording does not replace independent review or acceptance checks.'),
        ('Complete ELI20 explanations', 'Build the complete explanation first. Then clarify the wording. The STE edition retains the same product scope: terms, responsibilities, connections, flow, examples, conditions, exceptions, evidence and limits. One comparison example cannot replace the explanation.'),
        ('Analysis and verification results', 'Separate facts, inferences, unverified behavior, next actions and completion evidence in final reports. In independent panels, finish drafts and cross-review before editing final wording. Preserve counterevidence, minority views, reversal conditions and decision rules.'),
        ('Selective use', 'Do not require STE for every task. Use the installed skill when technical wording needs clarification. Edit for natural style only when requested, then recheck conditions, negation, obligations and scope. Dictionary approval needs separate verification. Korean guidance is an adaptation.')]),
}
for _lang, (_title, _cards) in _ste_applications.items():
    PAGES['skills'][_lang][2].insert(4, ('ste-applications', _title, _cards))
    PAGES['handoff'][_lang][2].append(('clear-procedures', _title, [_cards[1]]))
    PAGES['expert-panel'][_lang][2].append(('clear-results', _title, [_cards[3]]))
    PAGES['eli5'][_lang][2].append(('ste-composition', _title, [_cards[2], _cards[4]]))
    PAGES['ai-pms'][_lang][2].append(('clear-guidance', _title, [_cards[0]]))
