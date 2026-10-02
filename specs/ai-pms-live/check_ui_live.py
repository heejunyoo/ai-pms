#!/usr/bin/env python3
"""Executable Python/JS parity and DOM/polling simulation; no browser-layout claim."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import test_operations as cases


def main():
    snapshots = []
    for name in sorted(n for n in dir(cases.OperationsTests) if n.startswith('test_')):
        case = cases.OperationsTests(name)
        case.setUp()
        getattr(case, name)()
        try:
            snapshots.append(case.model())
        except ValueError:
            pass  # Invalid-input cases already assert rejection in their test.
    sample = cases.OperationsTests('test_sample_states');sample.setUp();fixture = sample.model()
    tied = cases.OperationsTests('test_sample_states');tied.setUp()
    star=tied.records['north_stars'][0]
    star['observations'].append(dict(star['observations'][0],id='same-instant-text',at=star['observations'][0]['at'].replace('Z','.000000Z')))
    snapshots.append(tied.model())
    html = (ROOT/'specs/ai-pms-dashboard/dashboard.html').read_text()
    script = html.split('<script>')[1].split('</script>')[0]
    validator = script[:script.index('function el(')]
    parity = '''
const assert=require('node:assert/strict');
for(const fixture of FIXTURES){validateModel(fixture);assert.deepEqual(deriveOperations(fixture.operations.records,fixture.projects,fixture.generated_at),fixture.operations);for(const s of fixture.operations.records.sessions){assert.equal(goalDigest(s),DIGESTS[goalDigest(s)]);}}
function bad(edit){const f=structuredClone(FIXTURE);edit(f);assert.throws(()=>validateModel(f));}
bad(f=>{f.operations.sessions.find(s=>s.completion==='failed').completion='accepted';});
bad(f=>{f.operations.capture[0].freshness='stale';});
for(const edit of [f=>f.operations.sessions[0].completion='accepted',f=>f.operations.sessions[0].lifecycle='ended',f=>f.operations.sessions[0].event_ids=[],f=>f.operations.people[0].session_ids=[],f=>f.operations.north_stars[0].current_value=999,f=>f.operations.north_stars[0].measurement_state='target_met',f=>f.operations.contributions[0].confirmation_state='confirmed',f=>f.operations.capture[0].freshness='recent']){const f=structuredClone(FIXTURE);edit(f);if(canonical(f)!==canonical(FIXTURE))assert.throws(()=>validateModel(f));}
for(const edit of [f=>f.operations.records.sessions[0].acceptance.verification_sha256='0'.repeat(64),f=>f.operations.records.sessions[0].source_project_id='99999999-9999-4999-8999-999999999999',f=>f.operations.records.sessions[0].task_ids=['action-3'],f=>f.operations.records.sessions[0].goal='/Users/private',f=>f.operations.records.sessions[0].acceptance.at='2026-10-03T00:00:00Z',f=>f.operations.records.north_stars[0].target=9007199254740992,f=>f.operations.records.capture[0].errors=true,f=>f.operations.records.sessions[0].extra=true,f=>delete f.operations.records.sessions[0].acceptance.verification_sha256,f=>f.operations.records.capture[0].status='healthy'])bad(edit);
const s=FIXTURE.operations.records.sessions[0],p=FIXTURE.projects.find(p=>p.id===s.project_id);assert.equal(verificationDigest(s,p),VERIFICATION);
const raw=structuredClone(p);for(const a of raw.management.attempts)delete a.status;for(const b of raw.management.blockers)delete b.verification;assert.equal(verificationDigest(s,raw),VERIFICATION);raw.management.attempts[0].status='future-derived';assert.equal(verificationDigest(s,raw),VERIFICATION);
console.log('Live parity PASS: '+FIXTURES.length+' Python snapshots, forged completion/lifecycle/hash/metric/capture and source/ownership/privacy cases rejected');
'''
    ia_path = ROOT/'specs/ai-pms-toss-ia/check_ia.py'
    ia_spec=importlib.util.spec_from_file_location('ia_structure',ia_path);ia=importlib.util.module_from_spec(ia_spec);ia_spec.loader.exec_module(ia)
    page=ia.Structure();page.feed(html)
    tree=ast.parse(ia_path.read_text())
    harness=next(n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='harness' for t in n.targets))
    harness=harness.replace(" get isConnected(){", " get options(){return this.children.filter(n=>n.tagName==='option');}\n get isConnected(){")
    harness=harness.replace("||(key==='data-task-id'&&Object.hasOwn(n.dataset,'taskId'))", "||(key.startsWith('data-')&&Object.hasOwn(n.dataset,key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())))")
    dom = r'''
(async()=>{
model=validateModel(FIXTURE);renderPortfolio();assert.equal($('sessionArea').hidden,false);assert.equal($('evidenceArea').hidden,true);assert.equal($('northStarArea').hidden,true);
const alice=$('peopleList').children.find(b=>b.dataset.person==='Alice');alice.click();assert.equal($('ownerFilter').value,'Alice');assert($('sessionList').textContent.includes('Alice'));assert(!$('sessionList').textContent.includes('Bob /'));
const first=$('sessionList').querySelectorAll('[data-session]').find(b=>b.dataset.session==='goal-0');assert(first);first.click();assert.equal(selectedSession,'goal-0');assert.equal(focused.id,'sessionDetailTitle');assert($('sessionDetail').textContent.includes('목표 인수 선언'));assert($('sessionDetail').textContent.includes('출처 프로젝트'));assert($('sessionDetail').textContent.includes('연결 작업'));
const proof=all($('sessionDetail')).find(b=>b.tagName==='button'&&b.textContent==='작업과 현재 검사 근거 보기');proof.click();assert.equal(activeTab,'work');assert.equal($('detail').hidden,false);assert.equal(focused.dataset.taskId,'action-1');assert($('closeDetail').textContent.includes('세션 목록'));$('closeDetail').click();assert.equal(selectedSession,'goal-0');assert.equal($('portfolio').hidden,false);
$('view-stars').click();assert.equal($('northStarArea').hidden,false);assert($('northStarList').textContent.includes('실측'));assert($('northStarList').textContent.includes('인과'));$('view-people').click();
const preserveSession=$('sessionList').querySelectorAll('[data-session]').find(b=>b.dataset.session==='goal-0');preserveSession.focus();window.scrollX=0;window.scrollY=321;window.scrollTo=(x,y)=>{window.scrollY=y;};$('search').value='';activeTab='documents';const before=structuredClone(model),cursorBefore=liveCursor;
const update=structuredClone(FIXTURE.projects[0]);update.name='변경된 프로젝트 이름';applyChanges({cursor:1,reset:false,project_updates:[update],operations:structuredClone(FIXTURE.operations),generated_at:FIXTURE.generated_at});assert.equal(model.projects.length,FIXTURE.projects.length);assert.equal(model.projects.find(p=>p.id===update.id).name,update.name);assert.equal($('ownerFilter').value,'Alice');assert.equal(selectedSession,'goal-0');assert.equal(activeTab,'documents');assert.equal(focused.dataset.session,'goal-0');assert.equal(window.scrollY,321);
const stable=model;assert.throws(()=>applyChanges({cursor:2,reset:false,project_updates:[],operations:{},generated_at:FIXTURE.generated_at}));assert.strictEqual(model,stable);assert.equal(liveCursor,1);
model.evidence_mode='declared';const reset=structuredClone(FIXTURE);for(const p of reset.projects)for(const s of p.sources)s.evidence_mode='synthetic';applyChanges({cursor:2,reset:true,project_updates:reset.projects,operations:reset.operations,generated_at:reset.generated_at});assert.equal(model.projects.length,reset.projects.length);assert.equal(liveCursor,2);assert.equal($('ownerFilter').value,'Alice');assert.equal(model.evidence_mode,'synthetic');assert($('dataNotice').textContent.includes('샘플'));
const mixed=structuredClone(reset.projects);mixed[0].sources[0].evidence_mode='local-execution';applyChanges({cursor:2,reset:true,project_updates:mixed,operations:reset.operations,generated_at:reset.generated_at});assert.equal(model.evidence_mode,'mixed');applyChanges({cursor:2,reset:true,project_updates:reset.projects,operations:reset.operations,generated_at:reset.generated_at});assert.equal(model.evidence_mode,'synthetic');
let calls=[];global.fetch=async(url,options)=>{calls.push([url,options]);return {ok:true,json:async()=>({cursor:3,reset:false,project_updates:[],operations:structuredClone(FIXTURE.operations),generated_at:FIXTURE.generated_at})};};document.body.dataset.live='false';await pollLive();assert.equal(calls.length,0);document.body.dataset.live='true';await pollLive();assert.equal(calls[0][0],'/api/changes?after=2');assert.equal(calls[0][1].credentials,'same-origin');assert.equal(liveCursor,3);
const unchanged=model;global.fetch=async()=>({ok:false,status:401});await pollLive();assert.strictEqual(model,unchanged);assert.equal($('liveLogin').hidden,false);assert($('liveStatus').textContent.includes('로그인'));
let loginBody;global.fetch=async(url,options)=>{if(url==='/api/login'){assert.equal($('liveToken').value,'');loginBody=JSON.parse(options.body);assert.equal(options.credentials,'same-origin');return {ok:true};}return {ok:true,json:async()=>({cursor:4,reset:false,project_updates:[],operations:structuredClone(FIXTURE.operations),generated_at:FIXTURE.generated_at})};};$('liveToken').value='synthetic-login-credential';await loginLive();assert.deepEqual(loginBody,{token:'synthetic-login-credential'});assert.equal($('liveToken').value,'');assert.equal(liveCursor,4);assert(!JSON.stringify(model).includes('synthetic-login-credential'));
let interval;global.setInterval=(fn,delay)=>{interval=delay;return 1;};initializeLive();assert($('evidenceFooterText').textContent.includes('중앙 연결'));assert.equal(interval,2000);await new Promise(resolve=>setTimeout(resolve,0));
console.log('Live DOM/poll mock PASS: person → sessions → task evidence, organization measurements, validated merge/reset, focus/filter/tab/scroll preservation, static no request, cookie login, failures retain state (no browser/layout claim)');
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
    digests={cases.op.goal_digest(s):cases.op.goal_digest(s) for f in snapshots for s in f['operations']['records']['sessions']}
    session=fixture['operations']['records']['sessions'][0]
    project=next(p for p in fixture['projects'] if p['id']==session['project_id'])
    prelude='const FIXTURE='+json.dumps(fixture)+';const FIXTURES='+json.dumps(snapshots)+';const DIGESTS='+json.dumps(digests)+';const VERIFICATION='+json.dumps(cases.op.verification_digest(session,project))+';\n'
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'parity.js';path.write_text(prelude+validator+parity);subprocess.run(['node',str(path)],check=True)
        path=Path(td)/'dom.js';path.write_text('const PAGE='+json.dumps(page.root)+';\n'+prelude+harness+script+'\n'+dom);subprocess.run(['node',str(path)],check=True)
    assert 'localStorage' not in script and '.innerHTML' not in script
    subprocess.run([sys.executable,str(ia_path)],check=True)
    print('Live UI acceptance PASS; actual browser and 390px rendering remain unverified')


if __name__=='__main__':main()
