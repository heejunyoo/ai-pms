"""Bilingual setup guides and retained ELI explanations."""
import json
RELEASE = '2026-10-02'

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
                       ('목적 기준 수락', '원래 요청의 성공 조건을 실제 사용자 흐름에서 확인하는 acceptance 명령과 기대 종료 코드를 둡니다. 코드 검사 통과나 해시 일치만으로 의미 정렬, 독립성, 사용자 수락을 증명했다고 말하지 않습니다.')]),
                     ('dispatch',
                      '겹치지 않는 책임으로 배치',
                      [('의존성', '같은 파일을 동시에 수정하지 않도록 소유권을 정하고 depends_on으로 선행조건을 표현합니다.'),
                       ('추론과 컨텍스트',
                        '모델·추론 수준은 기본 상속합니다. 독립 태스크에는 필요한 근거만 담고 사용자 override를 보존합니다. 도구 목록과 예산은 실제 API 권한을 대신하지 '
                        '않습니다.')]),
                     ('integrate',
                      '상위 작업자가 통합 확인',
                      [('반환 증거', '실제로 실행한 명령·결과·변경 파일·미충족 기준을 받습니다. 하위 에이전트의 완료 주장만으로 닫지 않습니다.'),
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
                        'flow. Passing code checks or matching hashes alone does not prove semantic alignment, reviewer '
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
                        'completion claim is not sufficient.'),
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
         '새로운 실패 근거가 있고 해결 가능한 수정이 있을 때 반복합니다. 같은 접근의 반복은 기본 세 번 이내입니다.',
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
         'Repeat when a failure provides new evidence and an actionable fix. Default to at most three retries of the '
         'same approach.',
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
            '서비스는 아닙니다. 모르는 사용자 PC에서 자동 수집하는 단계는 후속 과제입니다.'),
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
            'automatic collection service. Automatic collection from unknown users’ PCs remains deferred.'),
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
