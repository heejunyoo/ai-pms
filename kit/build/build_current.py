#!/usr/bin/env python3
"""Build every current and legacy Harness Kit route from reviewed bilingual content."""
import argparse
import ast
import hashlib
import html
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from current_content import PAGES, SCENES, RELEASE

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent / 'site'
ORIGIN = 'https://harness-kit.vercel.app'
LEGACY = {
 'codex-harness-2026-08': 'codex', 'harness-kit-2026-08': 'claude',
 'shared-skills-2026-08': 'skills', 'agent-harness-eli5-2026-08': 'guide',
 'handoff-skill-2026-08': 'handoff', 'expert-panel-2026-08': 'expert-panel',
 'eli5-skill-2026-08': 'eli5', 'codex-harness-eli5-2026-08': 'guide',
}
LABELS = {
 'ko': {'ste':'이해하기 · 한국어 STE','ai-pms':'AI PMS','index':'시작하기','codex':'Codex','claude':'Claude','skills':'스킬','guide':'이해하기 · ELI20','maintenance':'적용 확인','handoff':'Handoff','expert-panel':'전문가 분석','eli5':'ELI20 설명'},
 'en': {'ste':'Understand · English STE','ai-pms':'AI PMS','index':'Start','codex':'Codex','claude':'Claude','skills':'Skills','guide':'Understand · ELI20','maintenance':'Verify','handoff':'Handoff','expert-panel':'Expert analysis','eli5':'ELI20 explanations'},
}
CSS = '''
:root{--bg:#f5f4ef;--paper:#fffefa;--ink:#162b38;--muted:#596871;--line:#d6ddd9;--accent:#006b60;--pale:#dcece5;--blue:#214d78;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--bg)}
*{box-sizing:border-box}body{margin:0}a{color:inherit;text-underline-offset:4px}a:hover{color:var(--accent)}button{font:inherit;cursor:pointer}a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #ce7230;outline-offset:4px}.skip{position:absolute;top:-80px;left:20px}.skip:focus{top:10px;background:white;z-index:10;padding:12px}.wrap{max-width:1160px;margin:auto;padding:0 32px}
header{border-bottom:1px solid var(--line);background:var(--paper)}.top{display:flex;align-items:center;justify-content:space-between;min-height:84px;gap:24px}.brand{text-decoration:none;font-size:19px;font-weight:750;letter-spacing:-.5px}.brand span{color:var(--accent)}.edition{color:var(--muted);font-size:12px;letter-spacing:1px}.lang{display:flex;align-items:center;gap:12px;font-size:13px}.lang a{min-height:44px;display:flex;align-items:center}.nav{display:flex;gap:25px;flex-wrap:wrap;padding:4px 0 16px}.nav a{display:flex;align-items:center;min-height:44px;text-decoration:none;color:var(--muted);font-size:14px}.nav a[aria-current=page]{color:var(--accent);font-weight:750;border-bottom:2px solid var(--accent)}
.hero{padding:72px 0 48px;max-width:860px}.eyebrow{font-size:12px;font-weight:700;letter-spacing:1.5px;color:var(--accent);text-transform:uppercase}.hero h1{font-size:clamp(36px,5vw,62px);line-height:1.2;letter-spacing:-2px;font-weight:720;margin:20px 0 24px;word-break:keep-all}.hero p{max-width:680px;font-size:19px;line-height:1.7;color:var(--muted);margin:0}.layout{display:grid;grid-template-columns:190px 1fr;gap:48px;padding-bottom:64px}.aside{font-size:13px;align-self:start;position:sticky;top:20px}.aside p{font-size:11px;letter-spacing:1px;color:var(--muted)}.aside a{display:block;text-decoration:none;padding:12px 0;line-height:1.5}.sections{min-width:0}section{scroll-margin-top:24px;margin-bottom:42px}section h2{font-size:24px;letter-spacing:-.7px;line-height:1.4;margin:0 0 20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:14px}.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:24px;min-width:0}.card .num{font-size:12px;font-weight:750;color:var(--accent);display:block;margin-bottom:26px}.card h3{font-size:17px;line-height:1.45;margin:0 0 12px;word-break:keep-all}.card p{font-size:15px;line-height:1.85;color:var(--muted);margin:0;overflow-wrap:anywhere}.card a{display:inline-block;margin-top:18px;font-size:13px;min-height:36px}.evidence{padding:23px 26px;background:var(--pale);border-radius:12px;margin:0 0 36px;display:flex;gap:24px;flex-wrap:wrap}.evidence strong{display:block;font-size:24px;margin-bottom:5px}.evidence span{font-size:12px;line-height:1.6}.note{padding:22px 26px;border-left:3px solid var(--accent);background:#eaf0ea;font-size:14px;line-height:1.8}.sources{display:flex;flex-wrap:wrap;gap:14px;margin-top:18px;font-size:12px}.downloads{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}.button{border:1px solid var(--accent);border-radius:7px;padding:14px 18px;text-decoration:none;min-height:48px;display:inline-flex;align-items:center;font-size:14px;font-weight:650}.button.primary{background:var(--accent);color:white}.button.primary:hover{background:#005449}footer{border-top:1px solid var(--line);padding:28px 0 40px;font-size:12px;line-height:1.9;color:var(--muted)}.foot{display:flex;gap:24px;justify-content:space-between;flex-wrap:wrap}.tabs{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px}.tabs button{border:1px solid var(--line);border-radius:30px;padding:12px 20px;min-height:48px;background:var(--paper);color:var(--ink)}.tabs button[aria-pressed=true]{background:var(--ink);border-color:var(--ink);color:white}.explorer{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:28px;margin-bottom:28px}.explorer svg{width:100%;height:auto;display:block;margin:10px 0 24px}.explorer h2{margin-top:6px}.explorer .diagram-caption{color:var(--accent);font-weight:650;font-size:14px;line-height:1.8}.explain-cols{display:grid;grid-template-columns:1fr 1fr;gap:26px}.explain-cols h3{font-size:13px;color:var(--accent);margin:12px 0}.explain-cols p{font-size:15px;line-height:1.8;color:var(--muted);margin:0}.scene{display:none}.scene.active{display:block}svg text{font-family:inherit;fill:var(--ink);font-size:14px}svg .node{fill:var(--pale);stroke:#a1beb1}svg .edge{stroke:var(--accent);stroke-width:2;fill:none}details{border-top:1px solid var(--line);padding:16px 0}summary{cursor:pointer;line-height:1.6}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;line-height:1.7;background:#edf0eb;padding:18px;border-radius:8px}
@media(max-width:700px){.wrap{padding:0 20px}.top{min-height:74px;gap:12px}.edition{display:none}.nav{gap:6px 18px}.nav a{font-size:13px}.hero{padding:44px 0 34px}.hero h1{letter-spacing:-1.3px}.hero p{font-size:17px}.layout{display:block;padding-bottom:32px}.aside{position:static;border-bottom:1px solid var(--line);margin-bottom:26px;display:flex;flex-wrap:wrap;gap:4px 18px}.aside p{width:100%;margin:0}.aside a{font-size:12px}.grid{grid-template-columns:1fr}.card{padding:22px}.card .num{margin-bottom:14px}.evidence{padding:20px;gap:20px}.explorer{padding:20px}.explain-cols{grid-template-columns:1fr;gap:10px}.tabs button{padding:12px 17px;font-size:14px}.foot{gap:12px}}
@media(prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}.card{transition:border-color .15s}.card:hover{border-color:#9cb5a8}}@media print{header,.aside,.tabs,.downloads{display:none}.layout{display:block}.hero{padding-top:10px}.card{break-inside:avoid}body{background:white}}
'''
CSS += '\n@media(max-width:700px){svg text{font-size:22px}}\n'
CSS += '\n.hero{padding:40px 0 32px}.hero h1{font-size:clamp(32px,4vw,48px);margin:16px 0}.card p{font-size:16px}.card pre{margin-bottom:0}#apply .grid{grid-template-columns:1fr}.aside a{font-size:14px}.foot{font-size:14px}@media(max-width:700px){.hero{padding:28px 0}.hero p{font-size:16px}}\n'
CSS += '''
.architecture{list-style:none;counter-reset:stage;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;padding:0;margin:0}
.architecture li{counter-increment:stage;position:relative;background:var(--paper);border:1px solid var(--line);border-top:4px solid var(--accent);border-radius:12px;padding:20px;min-width:0}
.architecture li::before{content:counter(stage,decimal-leading-zero);display:block;color:var(--accent);font-weight:750;margin-bottom:18px}
.architecture li:not(:last-child)::after{content:'→';position:absolute;right:-16px;top:48%;z-index:1;color:var(--accent);font-size:20px;font-weight:750}
.architecture h3,.flow-panel h3{margin:0 0 10px;font-size:17px;line-height:1.45}.architecture p,.flow-panel p{margin:0;color:var(--muted);font-size:15px;line-height:1.8;overflow-wrap:anywhere}
.flow-rail{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin:0 0 14px}.flow-step{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:14px 10px;min-height:66px;text-align:left;color:var(--ink);line-height:1.4}.flow-step[aria-pressed=true]{background:var(--pale);border:2px solid var(--accent);font-weight:750}.flow-panel{padding:24px;background:var(--paper);border:1px solid var(--line);border-radius:12px;min-height:160px}.flow-panel[hidden]{display:none}
@media(max-width:700px){.aside{flex-wrap:nowrap;overflow-x:auto;gap:18px;scrollbar-width:thin}.aside p{display:none}.aside a{flex:none;white-space:nowrap}.architecture{grid-template-columns:1fr;gap:22px}.architecture li{padding:18px}.architecture li::before{margin-bottom:8px}.architecture li:not(:last-child)::after{content:'↓';right:auto;left:50%;top:auto;bottom:-23px}.flow-rail{grid-template-columns:repeat(2,minmax(0,1fr))}.flow-step{min-height:54px}.flow-panel{min-height:0}}
'''

def filename(key, lang):
    return key + ('-en' if lang == 'en' else '') + '.html'

def snapshot():
    home = Path.home()
    checks = {}
    for label, path in {
        'codex_configuration': '.codex/skills/codex-harness-audit/scripts/check_harness.py',
        'codex_script_regressions': '.codex/harness/verify.py',
        'claude_script_regressions': '.claude/harness/verify.py',
        'activity_logger_regressions': '.claude/harness/activity/test_logger.py',
        'activity_management_regressions': '.claude/harness/activity/test_management_recorder.py',
        'activity_workflow_regressions': '.claude/harness/activity/test_workflow.py',
        'handoff_regressions': '.agents/skills/handoff/validate.py',
        'claude_handoff_regressions': '.claude/skills/handoff/validate.py',
    }.items():
        args = [sys.executable, str(home / path)] + (['selftest'] if label.endswith('handoff_regressions') else [])
        run = subprocess.run(args, text=True, capture_output=True, timeout=40)
        if run.returncode:
            raise RuntimeError(label + '\n' + run.stdout[-2500:] + run.stderr[-1000:])
        checks[label] = 'passed'
    tree = ast.parse((home / '.codex/harness/verify.py').read_text())
    cases = next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'cases' for t in n.targets))
    return {'release': RELEASE, 'checks': checks, 'codex_safety_cases': len(cases), 'application_hook_delivery': 'not_verified', 'performance_comparison': 'not_measured'}

def guide_data(lang):
    if lang == 'ko':
        return ('코딩 에이전트의 하네스는\n어떻게 실제 일을 끝내나요?',
                '처음 보는 사람을 위한 ELI20: 필요한 용어를 정의하고, 파일을 바꾸는 흐름과 검증의 경계까지 따라갑니다.', [
            ('start', '먼저 풀어야 할 문제', [
                ('새 PC에서 같은 에이전트를 쓴다면', '모델이 같아도 어떤 지침을 읽고, 어떤 도구를 쓰며, 무엇을 실행 전에 막고, 완료를 어떻게 확인하는지에 따라 결과가 달라집니다. Harness Kit은 이 주변 운영 구성을 다른 환경에 옮기기 위한 참고 자료입니다.'),
                ('에이전트와 하네스', '에이전트는 요청을 해석하고 도구를 호출해 일합니다. 하네스는 에이전트 주위의 지침·스킬·훅·검증 절차입니다. 킷 자체가 모델이나 독립 실행 프로그램은 아닙니다.'),
                ('읽는 순서', '아래에서 용어와 각 구성요소의 책임을 확인한 뒤, 가상의 CSV 내보내기 요청을 처음부터 끝까지 따라가세요. 마지막에 포함 범위와 실제 확인이 필요한 부분을 구분합니다.')]),
            ('terms', '기본 용어를 먼저 맞춥니다', [
                ('지침 · AGENTS.md / CLAUDE.md', '에이전트가 매 작업에서 참고할 환경·프로젝트 규칙입니다. 어떤 작업에 승인이 필요한지와 프로젝트 명령을 적습니다.'),
                ('스킬 · SKILL.md', '특정 종류의 일을 할 때 읽는 절차와 판단 기준입니다. 설치돼 있어도 모든 작업에서 자동으로 실행되는 프로그램은 아닙니다.'),
                ('훅', '도구 호출이나 세션 이벤트에 연결된 자동 검사입니다. 지정된 위험 동작을 막을 수 있지만 결과의 의미나 품질을 대신 판단하지는 않습니다.'),
                ('도구와 검증', '도구는 파일·셸·외부 서비스의 실제 상태를 바꿉니다. 테스트·화면 확인은 그 결과를 관찰합니다. 검사 통과와 사용자에게 보이는 문제 해결은 별도로 확인해야 합니다.')]),
            ('parts', '누가 무엇을 맡나요?', [
                ('사용자 요청과 에이전트', '요청이 목표와 승인 범위를 정합니다. 에이전트는 필요한 파일을 읽고 작업을 계획·실행합니다.'),
                ('지침과 스킬', '지침은 이 환경의 지속 규칙, 스킬은 해당 작업에 필요한 전문 절차를 제공합니다. 둘 다 직접 파일을 수정하지 않습니다.'),
                ('훅과 도구', '훅은 정의된 도구 호출 경계에서 검사합니다. 통과한 도구가 실제 파일이나 외부 시스템의 상태를 바꿉니다.'),
                ('검증과 보고', '테스트와 실제 화면으로 바뀐 결과를 확인하고, 확인된 것과 아직 확인되지 않은 것을 구분해 보고합니다.')]),
            ('flow', '가상 사례 · CSV 내보내기 버튼을 추가한다면', [
                ('1 · 요청 이해', '사용자가 기존 목록 화면에 CSV 내보내기를 요청합니다. 에이전트는 데이터 형식과 완료 조건을 확인하고, DB·API 계약 변경이 필요한지 먼저 판단합니다.'),
                ('2 · 코드 찾기', '프로젝트 지침을 읽고 화면과 내보내기 관련 소스를 찾습니다. Graphify 그래프가 있으면 탐색에 쓸 수 있지만, 변경 후 그래프가 낡았는지 확인하고 실제 소스를 다시 읽습니다.'),
                ('3 · 구현과 경계', '필요한 스킬을 적용해 파일을 수정합니다. Ponytail은 불필요한 구현을 줄이는 판단을 돕습니다. 훅은 비밀정보 기록이나 기존 테스트 삭제처럼 정의된 동작을 차단할 수 있습니다.'),
                ('4 · 결과 검증', 'CSV 내용과 화면의 버튼 동작을 확인합니다. 테스트 통과만으로 다운로드 파일의 실제 내용이나 모바일 화면이 올바르다고 단정하지 않습니다.'),
                ('5 · 완료 판단', '확인된 결과와 남은 한계를 보고합니다. 진행 중 DB 스키마나 API 계약 변경이 필요해지면 기존 요청의 승인 범위인지 확인하고, 범위 밖이면 실행 전에 묻습니다.')]),
            ('concepts', '반복해서 쓰는 장치를 구분합니다', [
                ('아래 선택기', '철칙은 승인 경계, 하네스는 운영 구성, 루프는 검증 후 재시도, 그래프는 관계 지도, 스킬은 필요할 때 읽는 절차입니다. 이름이 비슷해도 맡는 일이 다릅니다.')]),
            ('boundary', '이 킷이 옮기는 것과 남는 것', [
                ('포함', 'Codex·Claude용 지침·훅·스킬의 공개 가능한 구현 파일과 적용 안내를 제공합니다. 압축 파일은 자동 설치 프로그램이 아닙니다.'),
                ('별도 설치·설정', 'Ponytail·Graphify는 외부 선택 도구입니다. 모델, 로그인, API 키, MCP 연결, 개인 메모리와 프로젝트 권한은 이 킷에 포함되지 않습니다.'),
                ('검증의 단계', '파일 배치 → 새 세션에서 로드 확인 → 실제 훅 호출과 사용자 화면 확인 순으로 검증합니다. 정적 검사 결과만으로 앱의 훅 전달, 절감 효과, 최종 작업 품질을 증명하지 않습니다.')]),
            ('next', '이제 사용하는 도구에 적용하기', [
                ('Codex 구성', '지침, 안전 훅, 스킬을 현재 설정과 비교해 병합하고 검증합니다.'),
                ('Claude 구성', '지침, 안전·Stop 훅, 스킬을 현재 설정과 비교해 병합하고 검증합니다.'),
                ('스킬 설치', 'ELI20과 선택 설치 도구의 위치·확인 방법을 봅니다.')])])
    return ('How does an agent harness\nfinish real work?',
            'ELI20 for newcomers: define the terms, follow one file change, and see what the checks do and do not prove.', [
        ('start', 'The problem this solves', [
            ('The same agent on another computer', 'Even with the same model, results depend on which instructions it reads, which tools it can use, what is blocked before execution, and how completion is checked. Harness Kit is a reference for transferring that surrounding setup.'),
            ('Agent and harness', 'The agent interprets requests and calls tools. The harness is the instructions, skills, hooks, and verification around it. The kit is neither a model nor a standalone operating program.'),
            ('Reading path', 'Learn the terms and responsibilities below, then follow a fictional CSV export request end to end. Finally distinguish what ships in the kit from what needs separate setup or live verification.')]),
        ('terms', 'Start with the terms', [
            ('Instructions · AGENTS.md / CLAUDE.md', 'Environment and project guidance read by the agent. They state approval boundaries and project commands.'),
            ('Skill · SKILL.md', 'A procedure and criteria for a particular kind of task. Being installed does not make it an automatically executing program for every task.'),
            ('Hook', 'An automatic check at a tool or session event. It can block defined risky actions but cannot judge the meaning or quality of the final result.'),
            ('Tools and verification', 'Tools change files or external systems. Tests and browser checks observe the result. Passing a check is different from resolving the user-visible problem.')]),
        ('parts', 'Who is responsible for what?', [
            ('User request and agent', 'The request sets the goal and authorization scope. The agent reads relevant files, plans, and executes the work.'),
            ('Instructions and skills', 'Instructions provide durable local rules; skills provide task-specific procedures. Neither edits files on its own.'),
            ('Hooks and tools', 'Hooks check specified tool-call boundaries. A permitted tool then changes a file or external system.'),
            ('Verification and report', 'Tests and the real interface help confirm the result. The agent reports what was observed and what remains unverified.')]),
        ('flow', 'Fictional example · add a CSV export button', [
            ('1 · Understand', 'The user requests CSV export from an existing list. The agent checks the data format and completion criteria, then asks whether a database or API contract change is needed.'),
            ('2 · Find the code', 'The agent reads project instructions and relevant source. An existing Graphify graph can aid navigation, but it may be stale; inspect the current source.'),
            ('3 · Implement within boundaries', 'The agent applies a relevant skill and edits files. Ponytail helps avoid unnecessary code. A hook may block a defined risky action such as recording a secret or deleting an existing test.'),
            ('4 · Verify the result', 'Check the CSV content and the button in the real interface. Passing tests alone does not prove the download contents or mobile layout are correct.'),
            ('5 · Decide completion', 'Report confirmed behavior and limits. If a database schema or API contract change becomes necessary, check the existing authorization scope and ask before an out-of-scope action.')]),
        ('concepts', 'Distinguish the recurring mechanisms', [
            ('Use the selector below', 'Rules define approval boundaries; a harness is the operating setup; a loop is verification and retry; a graph maps relationships; a skill is a procedure used when relevant. Similar names do not mean identical jobs.')]),
        ('boundary', 'What the kit transfers and what remains', [
            ('Included', 'Publicly shareable Codex and Claude instructions, hook code, skills, and setup guides. The ZIP is not an automatic installer.'),
            ('Separate setup', 'Ponytail and Graphify are optional external tools. Models, logins, API keys, MCP connections, personal memory, and project permissions are outside the kit.'),
            ('Levels of evidence', 'Verify file placement, then loading in a new session, then real hook delivery and the user interface. Static checks do not prove hook delivery, savings, or final task quality.')]),
        ('next', 'Apply this to your agent', [
            ('Codex configuration', 'Compare and merge instructions, the safety hook, and skills with the current setup, then verify.'),
            ('Claude configuration', 'Compare and merge instructions, safety and Stop hooks, and skills with the current setup, then verify.'),
            ('Skill installation', 'Find locations and checks for ELI20 and optional tools.')])])

def explorer(lang):
    scenes = SCENES[lang]
    buttons = ''.join(f'<button type="button" data-scene="{s[0]}" aria-pressed="{str(i == 0).lower()}" aria-controls="scene-panel">{html.escape(s[1])}</button>' for i,s in enumerate(scenes))
    drawing = ''
    for i, scene in enumerate(scenes):
        labels = scene[3].split(' → ')
        # Graph has a parallel branch to make its dependency structure visible.
        if scene[0] == 'graph':
            drawing += f'<g class="scene" data-scene="graph"><rect class="node" x="25" y="15" width="170" height="55" rx="9"/><rect class="node" x="25" y="105" width="170" height="55" rx="9"/><rect class="node" x="335" y="60" width="200" height="55" rx="9"/><path class="edge" d="M195 42L315 87M195 132L315 87M315 87H335"/><text x="110" y="49" text-anchor="middle">A</text><text x="110" y="139" text-anchor="middle">B</text><text x="435" y="94" text-anchor="middle">{html.escape("통합 검증" if lang == "ko" else "Integration check")}</text></g>'
        else:
            short = {'rules': ('경계','범위','실행') if lang=='ko' else ('Boundary','Scope','Action'), 'harness': ('지침','도구','결과') if lang=='ko' else ('Instructions','Tools','Results'), 'loop': ('변경','검증','판단') if lang=='ko' else ('Change','Verify','Decide'), 'skill': ('요청','절차','확인') if lang=='ko' else ('Request','Procedure','Check')}[scene[0]]
            drawing += f'<g class="scene{" active" if i == 0 else ""}" data-scene="{scene[0]}">'
            for j,label in enumerate(short):
                x=20+j*185
                drawing += f'<rect class="node" x="{x}" y="55" width="150" height="64" rx="9"/><text x="{x+75}" y="93" text-anchor="middle">{html.escape(label)}</text>'
                if j<2: drawing += f'<path class="edge" d="M{x+150} 87h30m-7 -5l7 5-7 5"/>'
            if scene[0]=='loop': drawing += '<path class="edge" d="M465 119v30H95v-24m-5 7l5-7 5 7"/>'
            drawing += '</g>'
    condition = '적용 조건 · 메커니즘' if lang=='ko' else 'Conditions · mechanism'
    limits = '예외·한계 · 트레이드오프' if lang=='ko' else 'Exceptions · limits · trade-offs'
    first=scenes[0]
    result=f'<div class="tabs" aria-label="{"개념 선택" if lang=="ko" else "Choose a concept"}">{buttons}</div><div class="explorer" id="scene-panel" aria-live="polite"><h2 id="scene-title">{first[2]}</h2><svg viewBox="0 0 560 180" role="img" aria-label="{html.escape(first[3])}">{drawing}</svg><p class="diagram-caption" id="scene-flow">{first[3]}</p><div class="explain-cols"><div><h3>{condition}</h3><p id="scene-condition">{first[4]}</p></div><div><h3>{limits}</h3><p id="scene-limit">{first[5]}</p></div></div></div>'
    script='''const scenes=SCENES_DATA;document.querySelectorAll('button[data-scene]').forEach(button=>button.addEventListener('click',()=>{const item=scenes.find(x=>x[0]===button.dataset.scene);document.querySelectorAll('button[data-scene]').forEach(x=>x.setAttribute('aria-pressed',String(x===button)));document.querySelectorAll('g.scene').forEach(x=>x.classList.toggle('active',x.dataset.scene===item[0]));document.getElementById('scene-title').textContent=item[2];document.getElementById('scene-flow').textContent=item[3];document.getElementById('scene-condition').textContent=item[4];document.getElementById('scene-limit').textContent=item[5];document.querySelector('.explorer svg').setAttribute('aria-label',item[3]);}));'''.replace('SCENES_DATA',json.dumps(scenes,ensure_ascii=False).replace('</','<\\/'))
    return result,script

def render(key, lang, evidence):
    title, intro, sections = guide_data(lang) if key=='guide' else PAGES[key][lang]
    e=html.escape
    other='en' if lang=='ko' else 'ko'
    nav=''.join(f'<a href="./{filename(k,lang)}"'+(' aria-current="page"' if k==key else '')+f'>{LABELS[lang][k]}</a>' for k in ('index','guide','ste','ai-pms','codex','claude','skills','maintenance'))
    aside=''.join(f'<a href="#{sid}">{e(heading)}</a>' for sid,heading,_ in sections)
    explore_html,script=explorer(lang) if key=='guide' else ('','')
    cards=''
    for sid,heading,items in sections:
        if key in ('guide','ste') and sid=='parts':
            body=''.join(f'<li><h3>{e(label)}</h3><p>{e(text)}</p></li>' for label,text in items)
            cards+=f'<section id="{sid}"><h2>{e(heading)}</h2><ol class="architecture">{body}</ol></section>'
        elif key in ('guide','ste') and sid=='flow':
            controls=''.join(f'<button type="button" class="flow-step" data-flow-step="{i}" aria-pressed="{str(i==0).lower()}" aria-controls="flow-panel-{i}">{e(label)}</button>' for i,(label,_) in enumerate(items))
            panels=''.join(f'<article class="flow-panel" id="flow-panel-{i}"'+('' if i==0 else ' hidden')+f'><h3>{e(label)}</h3><p>{e(text)}</p></article>' for i,(label,text) in enumerate(items))
            cards+=f'<section id="{sid}"><h2>{e(heading)}</h2><div class="flow-rail" role="group" aria-label="{e(heading,quote=True)}">{controls}</div><div class="flow-panels" aria-live="polite">{panels}</div></section>'
        else:
            body=''
            for i,(label,text) in enumerate(items):
                target={'AI PMS 중앙 프로젝트':'ai-pms','AI PMS central projects':'ai-pms','Codex 구성':'codex','Claude 구성':'claude','공용 스킬':'skills','스킬 설치':'skills','Codex configuration':'codex','Claude configuration':'claude','Shared skills':'skills','Skill installation':'skills'}.get(label)
                link=f'<a href="./{filename(target,lang)}">'+('살펴보기 →' if lang=='ko' else 'Explore →')+'</a>' if target else ''
                content = '<pre><code>'+e('\n'.join(text.splitlines()[1:-1]))+'</code></pre>' if text.startswith('```') else '<p>'+e(text)+'</p>'
                body+=f'<article class="card"><h3>{e(label)}</h3>{content}{link}</article>'
            cards+=f'<section id="{sid}"><h2>{e(heading)}</h2><div class="grid">{body}</div></section>'
        if key=='guide' and sid=='concepts': cards+=explore_html
    if key in ('guide','ste'):
        script+='''document.querySelectorAll('button[data-flow-step]').forEach(button=>button.addEventListener('click',()=>{const step=button.dataset.flowStep;document.querySelectorAll('button[data-flow-step]').forEach(x=>x.setAttribute('aria-pressed',String(x===button)));document.querySelectorAll('.flow-panel').forEach(x=>x.hidden=x.id!=='flow-panel-'+step);}));'''
    if key in ('guide', 'ste'):
        switch = '<div class="downloads" aria-label="'+('설명 방식 선택' if lang=='ko' else 'Choose a writing approach')+'">'
        for route, label in (('guide', 'ELI20'), ('ste', '한국어 STE' if lang=='ko' else 'English STE')):
            switch += f'<a class="button'+(' primary' if key==route else '')+f'" href="./{filename(route,lang)}"'+(' aria-current="page"' if key==route else '')+f'>{label}</a>'
        cards = switch+'</div>'+cards
    if key=='skills':
        cards+='<div class="downloads">'+''.join(f'<a class="button" href="./{filename(k,lang)}">{LABELS[lang][k]} →</a>' for k in ('handoff','expert-panel','eli5','ste'))+'</div>'
    if key=='ai-pms':
        cards='<div class="downloads">'+''.join(f'<a class="button" href="{url}" rel="noreferrer">{html.escape(label)} ↗</a>' for label,url in [(('GitHub 전체 도입 가이드' if lang=='ko' else 'Full GitHub adoption guide'),'https://github.com/heejunyoo/ai-pms/blob/main/docs/adoption.md'),(('JSON 템플릿' if lang=='ko' else 'JSON template'),'https://github.com/heejunyoo/ai-pms/blob/main/templates/catalog-work.template.json'),(('전체 필드 설명' if lang=='ko' else 'Complete field guide'),'https://github.com/heejunyoo/ai-pms/blob/main/docs/json-contracts.md'),(('기록기 사용 안내' if lang=='ko' else 'Recorder instructions'),'https://github.com/heejunyoo/ai-pms/blob/main/kit/activity/README.md'),(('구현 소스 ZIP' if lang=='ko' else 'Implementation ZIP'),'./implementation.zip')])+'</div>'+cards
        cards+='<div class="downloads">'+''.join(f'<a class="button" href="{url}" rel="noreferrer">{html.escape(label)} ↗</a>' for label,url in [(('Kit와 PMS 전체 설명' if lang=='ko' else 'Kit and PMS overview (Korean)'),'https://ai-pms-dashboard.vercel.app/overview.html'),(('프로젝트 도입 예시' if lang=='ko' else 'Project adoption example'),'https://ai-pms-dashboard.vercel.app'),(('ELI20 보고서' if lang=='ko' else 'ELI20 report'),'https://ai-pms-dashboard.vercel.app/report.html'),(('공개 소스' if lang=='ko' else 'Public source'),'https://github.com/heejunyoo/ai-pms')])+'</div>'
    trust='기존 설정을 백업한 뒤 필요한 항목을 병합하세요.' if lang=='ko' else 'Back up existing settings, then merge the entries you need.'
    if key=='ste':
        trust += ' 한국어 STE는 자체 명료성 가이드이며 공식 한국어 표준이나 인증이 아닙니다.' if lang=='ko' else ' This is STE-oriented writing; approved dictionary usage and full compliance are not verified.'
    stats=''
    download=f'<div class="downloads"><a class="button primary" href="./'+filename('guide',lang)+'">'+('먼저 이해하기 · ELI20 →' if lang=='ko' else 'Understand first · ELI20 →')+'</a><a class="button" href="./implementation.zip" download>'+('구현 소스 받기' if lang=='ko' else 'Download implementation')+'</a><a class="button" href="./reference-'+lang+'.zip" download>'+('안내 문서 받기' if lang=='ko' else 'Download guides')+'</a></div>' if key=='index' else ''
    sources = [('AGENTS.md','https://learn.chatgpt.com/docs/agent-configuration/agents-md'),('Hooks','https://learn.chatgpt.com/docs/hooks')] if key=='codex' else [('Claude hooks','https://code.claude.com/docs/en/hooks')] if key=='claude' else [('Ponytail','https://github.com/DietrichGebert/ponytail'),('Graphify','https://pypi.org/project/graphifyy/')] if key=='skills' else []
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{e(intro,quote=True)}"><meta name="harness-kit-release" content="{RELEASE}"><link rel="canonical" href="{ORIGIN}/{filename(key,lang)}"><link rel="alternate" hreflang="{other}" href="{ORIGIN}/{filename(key,other)}"><title>{e(title.replace(chr(10),' '))} · Harness Kit</title><style>{CSS}</style></head>
<body data-page="{key}" data-explain-level="20"><a class="skip" href="#main">{'본문으로' if lang=='ko' else 'Skip to content'}</a><header><div class="wrap"><div class="top"><a class="brand" href="./{filename('index',lang)}">Harness<span> Kit</span></a><span class="edition">SETUP GUIDE / {RELEASE}</span><div class="lang"><span>{'한국어' if lang=='ko' else 'English'}</span><span aria-hidden="true">/</span><a href="./{filename(key,other)}" lang="{other}" aria-label="{'Switch to English' if lang=='ko' else '한국어로 전환'}">{'English' if lang=='ko' else '한국어'}</a></div></div><nav class="nav" aria-label="{'주 메뉴' if lang=='ko' else 'Main navigation'}">{nav}</nav></div></header>
<main class="wrap" id="main"><div class="hero"><div class="eyebrow">{LABELS[lang][key]} / {RELEASE}</div><h1>{e(title).replace(chr(10),'<br>')}</h1><p>{e(intro)}</p>{download}</div><div class="layout"><aside class="aside" aria-label="{'이 페이지에서' if lang=='ko' else 'On this page'}"><p>{'이 페이지에서' if lang=='ko' else 'ON THIS PAGE'}</p>{aside}</aside><div class="sections">{stats}{cards}<div class="note" id="reference-boundary">{trust}</div><div class="sources">{''.join(f'<a href="{url}" rel="noreferrer">{label} ↗</a>' for label,url in sources)}</div></div></div></main><footer><div class="wrap foot"><div>Harness Kit · {RELEASE}<br>{'Codex · Claude 환경 적용 안내' if lang=='ko' else 'Codex · Claude setup guide'}</div><div>{'한국어 / English' if lang=='ko' else 'English / Korean'}</div></div></footer>{'<script>'+script+'</script>' if script else ''}</body></html>'''

def build(output):
    output.mkdir(parents=True,exist_ok=True)
    evidence=snapshot()
    routes={}
    for key in [*PAGES,'guide']:
        for lang in ('ko','en'):
            name=filename(key,lang)
            (output/name).write_text(render(key,lang,evidence))
            routes[name]={'page':key,'lang':lang,'canonical':name}
    for legacy,key in LEGACY.items():
        for lang in ('ko','en'):
            name=filename(legacy,lang);canonical=filename(key,lang)
            (output/name).write_bytes((output/canonical).read_bytes())
            routes[name]={'page':key,'lang':lang,'canonical':canonical}
    for lang in ('ko','en'):
        with zipfile.ZipFile(output/f'reference-{lang}.zip','w',zipfile.ZIP_DEFLATED) as bundle:
            for key in [*PAGES,'guide']:
                title,intro,sections=guide_data(lang) if key=='guide' else PAGES[key][lang]
                text='# '+title.replace('\n',' ')+'\n\n'+intro+'\n\n'
                for sid,heading,items in sections:
                    text+='## '+heading+'\n\n'+''.join('### '+label+'\n\n'+body+'\n\n' for label,body in items)
                text+='\nReference edition: '+RELEASE+'\n'+ORIGIN+'/'+filename(key,lang)+'\n'
                info=zipfile.ZipInfo(key+'.md',(2026,9,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
                bundle.writestr(info,text)
    # Explicitly selected, path-neutral implementation sources only. Never export config,
    # memories, permissions, user data, or an automatically executed installer.
    implementation={
        'codex/safety_gate.py': '.codex/hooks/safety_gate.py',
        'claude/safety_gate.py': '.claude/hooks/safety_gate.py',
        'claude/session_gate.py': '.claude/hooks/session_gate.py',
        'claude/test_session_gate.py': '.claude/hooks/test_session_gate.py',
    }
    for name in ('logger.py', 'connectivity.py', 'management.py', 'work.py', 'management_recorder.py', 'test_management_recorder.py', 'catalog-v3.template.json', 'catalog-work.template.json', 'operations.template.json', 'json-contracts.md', 'test_logger.py', 'viewer.html', 'README.md', 'example-project.jsonl'):
        implementation['activity/'+name] = '.claude/harness/activity/'+name
    # Only these authored skill packages are exportable; never walk all user settings.
    skill_roots = {
        'handoff': '.agents/skills/handoff',
        'claude-handoff': '.claude/skills/handoff',
        **{'skills/'+n: '.agents/skills/'+n for n in ('expert-panel','independent-panel','eli5')},
        **{'codex/skills/'+n: '.codex/skills/'+n for n in ('codex-harness-audit','codex-improvement-loop')},
        **{'claude/skills/'+n: '.claude/skills/'+n for n in ('expert-panel','eli5')},
    }
    # Only reviewed STE resources: keep a complete, portable package in the shared bundle.
    for name in ('SKILL.md', 'references/asd-ste100-model.md', 'references/korean-writing.md',
                 'assets/asd-ste100-explorer.html', 'assets/korean-writing-explorer.html'):
        implementation['skills/asd-ste100-interactive/'+name] = '.codex/skills/asd-ste100-interactive/'+name
    for target, source in skill_roots.items():
        root = Path.home()/source
        for item in sorted(root.rglob('*')):
            if item.is_file() and '__pycache__' not in item.parts and item.suffix in {'.md','.py','.json','.yaml','.html','.sh'}:
                implementation[target+'/'+item.relative_to(root).as_posix()] = item.relative_to(Path.home()).as_posix()
    for tool, names in {'codex': ('confidence_rating','autonomous_coding','memory_curation','graph_usage'), 'claude': ('confidence_rating','autonomous_coding','memory_curation')}.items():
        for name in names:
            implementation[f'{tool}/docs/{name}.md'] = f'.{tool}/docs/{name}.md'
    with zipfile.ZipFile(output/'implementation.zip','w',zipfile.ZIP_DEFLATED) as bundle:
        for target,source in implementation.items():
            body=(Path.home()/source).read_bytes()
            if b'/Users/' in body: raise ValueError('Personal path in implementation export: '+target)
            info=zipfile.ZipInfo(target,(2026,9,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            bundle.writestr(info,body)
        info=zipfile.ZipInfo('REFERENCE.md',(2026,9,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        bundle.writestr(info,'# Harness Kit implementation / 구현 소스\n\nStart with codex.md or claude.md in the guide ZIP. Copy complete skill folders, including SKILL.md and supporting files. Back up and merge existing settings. These files do not install themselves. Python 3.11+; default macOS/Linux home paths. Windows paths and shell commands need adaptation. Source comments retain their original language. Ponytail and Graphify are optional third-party tools and are not included; use the skills guide for installation and verification.\n\n안내 ZIP의 codex.md 또는 claude.md를 따라 배치합니다. 스킬은 SKILL.md와 보조 파일을 포함해 폴더 단위로 옮기세요. 기존 설정은 백업 후 병합합니다. Python 3.11 이상, macOS·Linux 기본 홈 경로 기준입니다. Windows에서는 경로와 셸 명령을 조정해야 합니다. Ponytail·Graphify는 포함되지 않는 선택 설치 도구입니다. 설치·검증 절차는 스킬 안내를 참고하세요.\n\nFor hook capture, use ai-pms.md in the guide ZIP. For full central multi-user dashboard adoption, use https://github.com/heejunyoo/ai-pms/blob/main/docs/adoption.md and https://ai-pms-dashboard.vercel.app (synthetic offline sample); source: https://github.com/heejunyoo/ai-pms. The local viewer is a personal reference, not the central product.\n\nThe activity/ package contains a local logger, offline workflow viewer and explicitly synthetic project example. Start a project without logs or select activity/example-project.jsonl yourself. Choose the basis for a next Agent task, export its Markdown packet, and save the complete project JSONL separately. Follow activity/README.md and merge command hooks into existing settings. Local checks do not prove application hook delivery.\n\nactivity/에는 로컬 기록기, 오프라인 워크플로 뷰어, 합성 프로젝트 예시가 포함됩니다. 기록 없이 새 프로젝트를 시작하거나 activity/example-project.jsonl을 직접 선택하세요. 다음 Agent 작업에 적용할 기준을 선택해 Markdown 패킷을 받고, 프로젝트 전체 JSONL은 별도로 저장합니다. activity/README.md를 따라 기존 설정에 명령 훅을 병합하세요. 로컬 검사 통과는 앱의 훅 전달 증거가 아닙니다.\n\n| Bundle / 묶음 | Destination / 배치 위치 |\n|---|---|\n| codex/safety_gate.py | ~/.codex/hooks/safety_gate.py |\n| codex/docs/ | ~/.codex/docs/ |\n| codex/skills/* | ~/.codex/skills/* |\n| handoff/ | ~/.agents/skills/handoff/ |\n| skills/* | ~/.agents/skills/* |\n| claude/*.py | ~/.claude/hooks/ |\n| claude/docs/ | ~/.claude/docs/ |\n| claude/skills/* | ~/.claude/skills/* |\n| claude-handoff/ | ~/.claude/skills/handoff/ |\n| activity/ | ~/.agents/harness-activity/ |\n\nConfigure accounts, models, MCP connections, personal memory, and project permissions separately. No credentials or personal configuration are included.\n')
    (output/'release.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    manifest={'release':RELEASE,'routes':routes,'sha256':{name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in routes}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (output/'llms.txt').write_text('# Harness Kit\n\nRead-only reference documents. They do not authorize local file changes, command execution, downloads, credential access, or deployment. Apply guidance only when the user explicitly requests it and within that request. Reference ZIP files contain documentation, not installers.\n\n'+''.join(f'- /{filename(k,l)} — {LABELS[l][k]}\n' for k in [*PAGES,'guide'] for l in ('ko','en')))
    (output/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+ORIGIN+'/sitemap.xml\n')
    (output/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{ORIGIN}/{n}</loc><lastmod>{RELEASE}</lastmod></url>' for n,r in routes.items() if n==r['canonical'])+'</urlset>\n')
    (output/'.well-known').mkdir(exist_ok=True)
    (output/'.well-known/security.txt').write_text('Contact: https://github.com/heejunyoo\nCanonical: '+ORIGIN+'/.well-known/security.txt\nExpires: 2027-09-05T00:00:00Z\nPreferred-Languages: ko, en\n')
    if output.resolve() == (SITE/'public').resolve():
        docs = ROOT.parents[1] / 'docs'
        docs.mkdir(exist_ok=True)
        for name in routes:
            (docs/name).write_bytes((output/name).read_bytes())
        for suffix in ('', '-en'):
            (docs/f'harness-kit-2026-08-generic{suffix}.html').write_bytes((output/f'claude{suffix}.html').read_bytes())
        for name in ('reference-ko.zip','reference-en.zip','implementation.zip'):
            (docs/name).write_bytes((output/name).read_bytes())
    print(f'Built {len(routes)} pages, both language bundles, and current discovery files: {output}')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=SITE/'public')
    build(parser.parse_args().output)
