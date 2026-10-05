#!/usr/bin/env python3
"""Validate the public contract across every route, language, and reference bundle."""
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr','path','rect'}

class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.stack=[];self.errors=[];self.ids=[];self.links=[];self.text=[];self.attrs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.attrs.append((tag,a))
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a':self.links.append(a.get('href',''))
        if tag not in VOID:self.stack.append((tag,a))
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID:self.stack.pop()
    def handle_endtag(self,tag):
        if tag in VOID:return
        if not self.stack or self.stack[-1][0]!=tag:self.errors.append(tag)
        else:self.stack.pop()
    def handle_data(self,data):
        if not any(t in {'script','style'} or a.get('lang')=='ko' for t,a in self.stack):self.text.append(data)

def validate(public):
    manifest=json.loads((public/'manifest.json').read_text());routes=manifest['routes'];parsers={}
    required=['index','codex','claude','skills','guide','maintenance','handoff','expert-panel','eli5','ai-pms','ste']
    for key in required:
        for suffix in ('','-en'):assert key+suffix+'.html' in routes,key+suffix
    # Existing externally shared routes must remain reachable, not disappear in a redesign.
    for prefix in ('codex-harness-2026-08','harness-kit-2026-08','shared-skills-2026-08','agent-harness-eli5-2026-08','handoff-skill-2026-08','expert-panel-2026-08','eli5-skill-2026-08'):
        for suffix in ('','-en'):assert prefix+suffix+'.html' in routes,prefix+suffix
    assert 'codex-harness-eli5-2026-08.html' in routes
    assert set(p.name for p in public.glob('*.html'))==set(routes),'Unmanaged/stale HTML page'
    for name,entry in routes.items():
        raw=(public/name).read_text();p=Page();p.feed(raw);parsers[name]=p
        assert not p.errors and not p.stack,(name,p.errors,p.stack)
        assert len(p.ids)==len(set(p.ids)),(name,'duplicate IDs')
        assert '<html lang="'+entry['lang']+'">' in raw
        assert 'name="viewport"' in raw and 'name="harness-kit-release"' in raw
        assert '/Users/' not in raw and not re.search(r'\b(?:sk-[A-Za-z0-9]{20,}|eyJ[A-Za-z0-9_-]{30,}\.)',raw)
        assert 'coding-agent' not in raw and 'APPLICATION SPEC' not in raw
        assert 'reference-boundary' in p.ids
        assert hashlib.sha256((public/name).read_bytes()).hexdigest()==manifest['sha256'][name]
        assert (public/name).read_bytes()==(public/entry['canonical']).read_bytes(),(name,'stale alias')
        for tag,a in p.attrs:
            if tag in {'script','img','iframe','source','video','audio','embed','object','link'}:
                ref=a.get('src',a.get('data',a.get('href','')))
                if tag=='link' and a.get('rel') in {'canonical','alternate'}:continue
                assert not ref.startswith(('http:','https:','//')),(name,'external runtime resource')
        assert not re.search(r'@import|url\(\s*[\'"]?https?://',raw)
        if entry['lang']=='en':assert not re.search('[가-힣]',''.join(p.text)),(name,'untranslated Korean')
        for script in re.findall(r'<script>(.*?)</script>',raw,re.S):
            assert not re.search(r'\b(?:fetch|eval|XMLHttpRequest)\s*\(',script),(name,'network/executable input')
            r=subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,timeout=10)
            assert r.returncode==0,(name,r.stderr)
    for name,p in parsers.items():
        for link in p.links:
            if link.startswith(('https://','http://')):continue
            url=urlsplit(link);target=url.path.removeprefix('./') or name
            assert (public/target).exists(),(name,link)
            if url.fragment:assert target in parsers and url.fragment in parsers[target].ids,(name,link)
    for key in required:
        ko=parsers[key+'.html'];en=parsers[key+'-en.html']
        assert ko.ids==en.ids,(key,'language section parity')
        assert len(ko.attrs)==len(en.attrs),(key,'language structural parity')
        assert './'+key+'-en.html' in ko.links and './'+key+'.html' in en.links
    for lang in ('ko','en'):
        suffix='' if lang=='ko' else '-en';guide=(public/('guide'+suffix+'.html')).read_text()
        index=(public/('index'+suffix+'.html')).read_text()
        assert index.index('id="purpose"')<index.index('id="start"'),('index'+suffix,'ELI20 orientation missing')
        assert 'class="button primary" href="./guide'+suffix+'.html"' in index,('index'+suffix,'learning route is not primary')
        ids=('start','terms','parts','flow','concepts','boundary','next')
        assert [guide.index(f'id="{sid}"') for sid in ids]==sorted(guide.index(f'id="{sid}"') for sid in ids),('guide'+suffix,'learning sequence')
        assert 'class="architecture"' in guide and guide.count('class="flow-step"')==5 and 'CSV' in guide,('guide'+suffix,'component map or concrete flow missing')
        assert 'data-flow-step' in guide and 'flow-panel' in guide and 'aria-live="polite"' in guide,('guide'+suffix,'scenario interaction missing')
        for scene in ('rules','harness','loop','graph','skill'):
            assert f'<button type="button" data-scene="{scene}"' in guide
            assert f'data-scene="{scene}"' in guide
        assert 'aria-pressed' in guide and 'classList.toggle' in guide and 'data-explain-level="20"' in guide
        assert 'min-height:48px' in guide and '@media(max-width:700px)' in guide
        with zipfile.ZipFile(public/f'reference-{lang}.zip') as z:
            assert len(z.namelist())==len(required)
            for n in z.namelist():
                assert n.endswith('.md') and '/' not in n
                text=z.read(n).decode()
                assert '/Users/' not in text
                if lang=='en':assert not re.search('[가-힣]',text),(n,'untranslated reference document')
    with zipfile.ZipFile(public/'implementation.zip') as z:
        assert 'codex/safety_gate.py' in z.namelist() and 'handoff/validate.py' in z.namelist()
        def check_intent_example(prefix):
            names={prefix+name for name in ('intent_guard.py','example.plan.json','example-intent.md','example-spec.md','example-review.json')}
            assert names <= set(z.namelist()),(prefix,'missing intent guard or reviewed examples')
            with tempfile.TemporaryDirectory(prefix='handoff-intent-') as tmp:
                root=Path(tmp)
                for name in z.namelist():
                    if not name.startswith(prefix):continue
                    relative=Path(name[len(prefix):])
                    assert not relative.is_absolute() and '..' not in relative.parts,(prefix,name)
                    if not relative.parts:continue
                    target=root/relative
                    if name.endswith('/'):
                        target.mkdir(parents=True,exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(z.read(name))
                validator=root/'validate.py'
                for args in (('selftest',),('plan','example.plan.json')):
                    result=subprocess.run([sys.executable,str(validator),*args],cwd=root,text=True,
                                          capture_output=True,timeout=30)
                    assert result.returncode==0,(prefix,args,result.stdout,result.stderr)
        check_intent_example('handoff/')
        check_intent_example('claude-handoff/')
        activity = {'activity/'+name for name in ('logger.py','connectivity.py','management.py','work.py','management_recorder.py','test_management_recorder.py','catalog-v3.template.json','catalog-work.template.json','operations.template.json','json-contracts.md','test_logger.py','viewer.html','README.md','example-project.jsonl')}
        assert {name for name in z.namelist() if name.startswith('activity/')} == activity, 'Activity export must use the exact public allowlist'
        pms_files = ['docs/visual-management.md', 'docs/project-architecture.md', 'docs/rensei-experience.md', 'docs/human-view-and-analysis.md', 'scripts/prepare_goal_analysis.py', 'specs/ai-pms-live/live_service.py', 'specs/ai-pms-live/live_sender.py', 'specs/ai-pms-live/session_goal.py', 'specs/ai-pms-live/demo_setup.py', 'specs/ai-pms-live/README.md', 'specs/ai-pms-live/sample/catalog.json', 'specs/ai-pms-live/sample/operations.json', 'specs/ai-pms-live/sample/central.json', 'specs/ai-pms-dashboard/portfolio.py', 'specs/ai-pms-dashboard/management.py', 'specs/ai-pms-dashboard/work.py', 'specs/ai-pms-dashboard/operations.py', 'specs/ai-pms-dashboard/dashboard.html', 'specs/ai-pms-central/central.py', 'specs/ai-pms-central/connectivity.py', 'specs/ai-pms-transport/common.py', 'README.md']
        assert not any(name.startswith('pms/') for name in z.namelist()), 'Kit PMS scope is local hooks; central runtime belongs to GitHub'
        # Retain local executable runtime checks; downloaded GitHub repeats these in verify_adoption.py.
        with tempfile.TemporaryDirectory() as temporary:
            pilot_root=Path(temporary).resolve()/'pms'
            for name in pms_files:
                payload=(Path.home()/'.claude/harness/activity/pms'/name).read_bytes()
                assert payload, ('empty reviewed local runtime source', name)
                if name.endswith('.py'):compile(payload, name, 'exec')
                target=pilot_root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
            for name in ('live_service.py','live_sender.py','session_goal.py','demo_setup.py'):
                result=subprocess.run([sys.executable,str(pilot_root/'specs/ai-pms-live'/name),'--help'],cwd=pilot_root,text=True,capture_output=True,timeout=30)
                assert result.returncode==0,(name,result.stderr)
            result=subprocess.run([sys.executable,str(pilot_root/'specs/ai-pms-live/demo_setup.py'),'--directory',str(pilot_root/'private-pilot')],cwd=pilot_root,text=True,capture_output=True,timeout=30)
            assert result.returncode==0 and '7 writer environments' in result.stdout,result.stderr
            assert (pilot_root/'private-pilot/manager.credential').stat().st_mode & 0o777==0o600
        assert json.loads(z.read('activity/operations.template.json'))==dict(version=1,sessions=[],north_stars=[],contributions=[],capture=[])
        sample_bytes = z.read('activity/example-project.jsonl')
        assert b'/Users/' not in sample_bytes and b'BEGIN PRIVATE KEY' not in sample_bytes
        sample_path = Path.home()/'.claude/harness/activity/logger.py'
        spec = importlib.util.spec_from_file_location('harness_activity_logger', sample_path)
        logger = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(sample_path.parent))
        try:
            spec.loader.exec_module(logger)
        finally:
            sys.path.pop(0)
        sample = [json.loads(line) for line in sample_bytes.decode().splitlines()]
        required_fields = {'schema_version','adapter_version','event_id','observed_at','occurred_at','source','native_event','kind','authority','project_id','session_id','agent_id','parent_agent_id','turn_id','tool_call_id','tool_name','links','data','missing_fields'}
        for event in sample:
            assert set(event) == required_fields and event['schema_version'] == 1 and event['adapter_version'] == '1'
            assert event['source'] == 'manual' and event['authority'] == 'declared' and event['native_event'] == event['kind']
            assert event['kind'] in logger.DATA and set(event['data']) <= logger.DATA[event['kind']]
            assert set(event['links']) == set(logger.LINKS)
            assert all(isinstance(value,str) and len(value) <= (80 if key == 'environment' else 2000) and not logger.PRIVATE.search(value)
                       for key,value in event['data'].items())
            assert all(event['links'].get(key) for key in logger.REQUIRED[event['kind']])
            if event['kind'] in ('check.recorded','acceptance.recorded'):
                choices = {'pass','fail','unknown'} if event['kind'] == 'check.recorded' else {'accepted','rejected','pending'}
                assert event['data'].get('status') in choices
        assert len([e for e in sample if e['kind'] == 'project.baseline']) >= 1
        assert len([e for e in sample if e['kind'] == 'decision.recorded' and e['data'].get('reason')]) >= 2
        assert {e['links']['artifact_version'] for e in sample if e['kind'] == 'artifact.recorded'} >= {'v1','v2'}
        assert {e['data'].get('status') for e in sample if e['kind'] == 'check.recorded'} >= {'fail','pass'}
        assert {e['data'].get('status') for e in sample if e['kind'] == 'acceptance.recorded'} >= {'rejected','pending'}
        # Every package named by the setup guides must include its entry point.
        for name in ('claude/safety_gate.py','handoff/SKILL.md','claude-handoff/SKILL.md',
                     'skills/eli5/SKILL.md','skills/expert-panel/SKILL.md','skills/independent-panel/SKILL.md',
                     'claude/skills/eli5/SKILL.md','claude/skills/expert-panel/SKILL.md',
                     'codex/skills/codex-harness-audit/scripts/check_harness.py',
                     'codex/skills/codex-improvement-loop/SKILL.md',
                     'codex/docs/confidence_rating.md','claude/docs/autonomous_coding.md'):
            assert name in z.namelist(),('Missing setup source',name)
        for name in z.namelist():
            assert not name.startswith('/') and '..' not in Path(name).parts
            assert not any(t in name for t in ('config.toml','MEMORY','settings.json','hooks.json'))
            body=z.read(name).decode()
            assert '/Users/' not in body
            if name.endswith('.py'):compile(body,name,'exec')
        for name in ('skills/eli5/SKILL.md','claude/skills/eli5/SKILL.md'):
            skill=z.read(name).decode()
            assert 'ELI20' in skill and 'ELI15' not in skill and 'ELI10' not in skill,(name,'stale ELI depth')
        assert not any('ponytail' in n.lower() or 'graphify' in n.lower() for n in z.namelist()),'Optional tools bundled without setup contract'
    # Every advertised STE resource must match the installed, reviewed source.
    ste_files = ('SKILL.md', 'references/asd-ste100-model.md', 'references/korean-writing.md',
                 'assets/asd-ste100-explorer.html', 'assets/korean-writing-explorer.html')
    with zipfile.ZipFile(public/'implementation.zip') as bundle:
        prefix = 'skills/asd-ste100-interactive/'
        assert {n for n in bundle.namelist() if n.startswith(prefix)} == {prefix+n for n in ste_files}
        for name in ste_files:
            assert bundle.read(prefix+name) == (Path.home()/'.codex/skills/asd-ste100-interactive'/name).read_bytes(), (name, 'stale STE resource')
    for lang, suffix in (('ko', ''), ('en', '-en')):
        page = (public/('skills'+suffix+'.html')).read_text()
        assert 'id="asd-ste100-interactive"' in page
        for token in ('skills/asd-ste100-interactive/', 'korean-writing-explorer.html', 'asd-ste100-explorer.html', '$asd-ste100-interactive'):
            assert token in page, (lang, 'missing STE usage guidance', token)
        with zipfile.ZipFile(public/f'reference-{lang}.zip') as bundle:
            assert 'asd-ste100-interactive' in bundle.read('skills.md').decode()
    # Both understanding routes remain discoverable and compare the same task.
    for suffix, label in (('', '한국어 STE'), ('-en', 'English STE')):
        ste = (public/('ste'+suffix+'.html')).read_text()
        guide = (public/('guide'+suffix+'.html')).read_text()
        assert label in ste and 'CSV' in ste
        sections = ('start','terms','parts','flow','concepts','boundary','next')
        assert all(f'id="{sid}"' in ste and f'id="{sid}"' in guide for sid in sections)
        assert ste.count('class="flow-step"') == 5 and 'aria-live="polite"' in ste
        assert len(parsers['ste'+suffix+'.html'].ids) >= len(sections)
        assert './ste'+suffix+'.html' in guide and './guide'+suffix+'.html' in ste
        with zipfile.ZipFile(public/('reference-'+('en' if suffix else 'ko')+'.zip')) as bundle:
            assert 'ste.md' in bundle.namelist()
    # Narrow release invariants: current procedures and bilingual retry guidance,
    # not proof of semantic product acceptance or native hook execution.
    procedures = {
        'codex/docs/autonomous_coding.md': '.codex/docs/autonomous_coding.md',
        'claude/docs/autonomous_coding.md': '.claude/docs/autonomous_coding.md',
        'handoff/SKILL.md': '.agents/skills/handoff/SKILL.md',
        'claude-handoff/SKILL.md': '.claude/skills/handoff/SKILL.md',
        'codex/skills/codex-improvement-loop/SKILL.md': '.codex/skills/codex-improvement-loop/SKILL.md',
    }
    with zipfile.ZipFile(public/'implementation.zip') as bundle:
        for target, source in procedures.items():
            assert bundle.read(target) == (Path.home()/source).read_bytes(), (target, 'stale procedure export')
        for target in ('codex/docs/autonomous_coding.md', 'claude/docs/autonomous_coding.md'):
            body = bundle.read(target).decode()
            assert all(token in body for token in ('기능 검사·제품 인수·사용자 수락', '두 번 실패', '원래 경로는 미검증')), target
    for suffix, token, stale in (('', '두 번 실패', '기본 세 번 이내'), ('-en', 'After two failures', 'at most three retries')):
        assert token in (public/('guide'+suffix+'.html')).read_text()
        assert stale not in (public/('guide'+suffix+'.html')).read_text()
        assert 'id="product-acceptance"' in (public/('maintenance'+suffix+'.html')).read_text()
    # Assertions reflect current behavior, including removal of the previous forced-low policy.
    handoff=(public/'handoff-en.html').read_text()
    assert 'Inherit model and reasoning settings by default' in handoff
    assert 'may correctly fail before the fix' in handoff
    handoff_ko=(public/'handoff.html').read_text()
    for token in ('원문 근거 고정','검토 영수증','오래된 것이므로','요구사항 ID','원래 요청의 성공 조건'):
        assert token in handoff_ko,('handoff-ko','intent guard guidance missing',token)
    for token in ('Anchor the user purpose to source evidence','Independent review and freshness','makes the receipt stale',
                  'requirement IDs','original request through its user-facing flow'):
        assert token in handoff,('handoff-en','intent guard guidance missing',token)
    codex=(public/'codex.html').read_text();claude=(public/'claude-en.html').read_text()
    assert '문서에 적힌 셸 예시는 실행 명령으로 취급하지 않습니다' in codex
    assert 'latest observed code edit' in claude and 'at most once per session' in claude
    for tool in ('codex','claude'):
        for suffix in ('','-en'):
            page=(public/(tool+suffix+'.html')).read_text()
            assert 'id="activity"' in page
            for token in ('~/.agents/harness-activity/', 'viewer.html', 'README.md', 'test_logger.py', 'example-project.jsonl',
                          'SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'Stop', 'SessionEnd',
                          'hook --source '+tool, '--project-id'):
                assert token in page, (tool+suffix, 'missing logger hookup', token)
            if tool == 'claude':
                assert all(event in page for event in ('PostToolUseFailure','SubagentStart','SubagentStop'))
    for name in ('skills.html','skills-en.html'):
        page=(public/name).read_text()
        assert all(token in page for token in ('ELI20','Ponytail','Graphify','graphify --version','graphify install --platform codex','ponytail@ponytail')),(name,'optional tool or ELI20 guide missing')
        assert 'ELI5 · ELI10 · ELI15' not in page,(name,'stale depth choice')
    for suffix in ('','-en'):
        page=(public/('ai-pms'+suffix+'.html')).read_text()
        for token in ('https://ai-pms-dashboard.vercel.app', 'https://ai-pms-dashboard.vercel.app/report.html',
                      'https://github.com/heejunyoo/ai-pms', 'pms_metadata', '--resource-map',
                      'duration_ms', 'artifact_refs', 'declared', 'input/output', 'revision'):
            assert token in page, ('AI PMS contract missing', suffix, token)
        for sid in ('purpose','flow','connectivity','logging','boundary'):
            assert f'id="{sid}"' in page
        assert './ai-pms'+suffix+'.html' in (public/('index'+suffix+'.html')).read_text()
    release=json.loads((public/'release.json').read_text())
    assert release['application_hook_delivery']=='not_verified'
    assert all(x=='passed' for x in release['checks'].values())
    llms=(public/'llms.txt').read_text()
    assert 'do not authorize local file changes' in llms and 'user explicitly requests it' in llms
    for name in ('robots.txt','sitemap.xml','.well-known/security.txt'):assert (public/name).exists()
    cfg=json.loads((public.parent/'vercel.json').read_text())
    headers={h['key']:h['value'] for h in cfg['headers'][0]['headers']}
    for value in ("connect-src 'none'","object-src 'none'","form-action 'none'","frame-ancestors 'none'"):
        assert value in headers['Content-Security-Policy']
    assert headers['X-Content-Type-Options']=='nosniff' and headers['X-Frame-Options']=='DENY'
    print(f'ALL PASS — {len(routes)} pages; language parity, legacy routes, HTML/JS, privacy, offline resources, bundles, and headers.')

if __name__=='__main__':
    validate(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent.parent/'site/public')
