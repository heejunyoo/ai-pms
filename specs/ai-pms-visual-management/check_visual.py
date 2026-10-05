#!/usr/bin/env python3
"""Independent user-question regressions. Simulated DOM is not visual acceptance."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / 'specs/ai-pms-dashboard'


def runtime(assertions, documentary=None):
    html = (DASH / 'dashboard.html').read_text()
    assert (DASH / 'human-view.js').read_text() in html, 'Embedded JS drift'
    assert (DASH / 'human-view.css').read_text() in html, 'Embedded CSS drift'
    source = ROOT / 'specs/ai-pms-toss-ia/check_ia.py'
    spec = importlib.util.spec_from_file_location('visual_ia', source)
    ia = importlib.util.module_from_spec(spec); spec.loader.exec_module(ia)
    harness = next(n.value.value for n in ast.walk(ast.parse(source.read_text()))
                   if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'harness' for t in n.targets))
    harness = harness.replace("||(key==='data-task-id'&&Object.hasOwn(n.dataset,'taskId'))",
                              "||(key.startsWith('data-')&&Object.hasOwn(n.dataset,key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())))")
    harness = harness.replace(' get isConnected(){', " get options(){return this.children.filter(n=>n.tagName==='option');}\n get isConnected(){")
    if documentary:
        html = html.replace('<script>', '<script id="documentary-data" type="application/json">'+json.dumps(documentary)+'</script><script>', 1)
    page = ia.Structure(); page.feed(html)
    fixture = json.loads((ROOT / 'apps/dashboard/public/snapshot.json').read_text())
    with tempfile.TemporaryDirectory() as td:
        output = Path(td) / 'visual.js'
        output.write_text('const PAGE='+json.dumps(page.root)+';const FIXTURE='+json.dumps(fixture)+';\n'+harness+html.split('<script>')[1].split('</script>')[0]+'\n'+assertions)
        subprocess.run(['node', str(output)], check=True)


WBS = r'''
model=validateModel(FIXTURE);renderPortfolio();renderDetail();
const p=model.projects.find(p=>p.owners.includes('Alice')&&p.owners.includes('Bob'));
const before=JSON.stringify(model),has=(n,c)=>String(n.className||'').split(' ').includes(c);
const tasks=n=>all(n).filter(n=>has(n,'human-wbs-task'));
const links=n=>all(n).filter(n=>n.tagName==='a');
$('peopleList').children.find(n=>n.dataset.person==='Bob').click();navigate(p);
const panel=$('detailPanel'),wbs=all(panel).find(n=>has(n,'human-wbs'));assert(wbs,'Whole WBS must be the primary project plan');
assert.deepEqual(all(wbs).filter(n=>has(n,'human-wbs-phase')).map(n=>n.dataset.humanPhase),p.work.phases.map(ph=>ph.id));
for(const ph of p.work.phases){const row=all(wbs).find(n=>has(n,'human-wbs-phase')&&n.dataset.humanPhase===ph.id);if(ph.state==='complete')assert.equal(row.open,false,'Completed phase should be compact initially');if(['in_progress','blocked','failed','review_pending','revalidation'].includes(ph.state))assert.equal(row.open,true,'Current or actionable phase should expose tasks initially');}
assert.deepEqual(tasks(wbs).map(n=>n.dataset.taskId).sort(),p.work.tasks.map(t=>t.id).sort(),'Person selection cannot hide another owner or unknown-owner task');
for(const t of p.work.tasks){const row=tasks(wbs).find(n=>n.dataset.taskId===t.id);assert(row.textContent.includes(t.title));assert(row.textContent.includes(t.owner||'미지정'));assert.equal(has(row,'human-owner-selected'),t.owner==='Bob');assert(all(row).some(n=>has(n,'human-status')&&n.textContent.includes(humanStatus(t.state))));assert(links(row).some(a=>new URLSearchParams(a.href.slice(1)).get('task')===t.id));}
assert(links(panel).some(a=>new URLSearchParams(a.href.slice(1)).get('final')==='1'),'Final acceptance remains independent');
assert(panel.textContent.includes('참고한 API · MCP'),'Project plan should explain available resources');for(const ref of humanReferences(p)){assert(panel.textContent.includes(ref.name));assert(panel.textContent.includes(ref.basis),'Configured resources cannot masquerade as observed use');}
const resourceLink=links(panel).find(a=>a.textContent.includes('설정·호출 근거'));assert(resourceLink,'Project resources need a direct evidence path');resourceLink.click();assert.equal(route().kind,'evidence');assert.equal(activeTab,'connections');navigate(p);
assert(!all(wbs).some(n=>has(n,'date-axis')),'No schedule must not create dates');assert(!/ETA|납기|\d+%/.test(wbs.textContent),'Task counts are not effort or goal percentages');
for(const ph of p.work.phases){navigate(p,{phase:ph.id});const expected=p.work.tasks.filter(t=>t.phase_id===ph.id);const section=all($('detailPanel')).find(n=>has(n,'human-phase-tasks'));assert(section,'Phase must retain its action path');for(const t of expected)assert(links(section).some(a=>new URLSearchParams(a.href.slice(1)).get('task')===t.id));assert.equal(humanReferences(p,ph.id).length,0);}
navigate(p,{view:'evidence'});assert(all($('detail')).some(n=>has(n,'human-evidence-questions')),'Evidence should answer questions before raw categories');
assert.deepEqual(all($('human-evidence-questions')).filter(n=>n.tagName==='button').map(n=>n.textContent),['확인 결과','실행 이력','참고 자료'],'Default evidence choice stays compact');
const technical=all($('detail')).find(n=>has(n,'human-technical-evidence'));assert(technical&&technical.tagName==='details'&&!technical.open,'Technical categories belong behind explicit disclosure');
for(const tab of ['work','management','documents','overview','tests','traceability','sessions','timeline','connections'])assert(all(technical).includes($('tab-'+tab)),'Every original evidence category stays reachable behind disclosure');
navigate(p);const disclosure=all($('detailPanel')).find(n=>has(n,'human-wbs-phase'));disclosure.open=false;const heading=all(disclosure).find(n=>n.tagName==='summary');heading.focus();const headingId=heading.id,disclosureId=disclosure.id,hashBefore=location.hash;
applyChanges({cursor:1,reset:false,project_updates:[],operations:null,generated_at:model.generated_at});assert.equal(location.hash,hashBefore);assert.equal($(disclosureId).open,false,'Live updates must preserve collapsed WBS');assert.equal(focused.id,headingId);assert(focused.isConnected);assert.equal($('ownerFilter').value,'Bob');
applyChanges({cursor:2,reset:true,project_updates:structuredClone(FIXTURE.projects),operations:FIXTURE.operations||null,generated_at:FIXTURE.generated_at});assert.equal($(disclosureId).open,false,'Reset must preserve collapsed WBS');assert.equal(focused.id,headingId);assert(focused.isConnected);
assert.equal(JSON.stringify(model),before,'Reading the plan/evidence changed the conservative model');
const missing=structuredClone(p);missing.work=null;missing.phases=[];const box=new Element('div');renderPhaseFlow(box,missing);assert(/미입력|미관측|없음/.test(box.textContent));assert(!tasks(box).length,'Missing plans do not invent work');
const unsafe=structuredClone(p);unsafe.work.tasks[0].title='<img src=x onerror=alert(1)>';const safeBox=new Element('div');renderPhaseFlow(safeBox,unsafe);assert(safeBox.textContent.includes(unsafe.work.tasks[0].title));assert(!all(safeBox).some(n=>n.tagName==='img'),'WBS titles must remain native text');
console.log('Visual WBS PASS: all shared tasks, responsibility, status text, phase actions, final gate, no invented schedule, contextual evidence, unchanged model');
'''

SESSIONS = r'''
model=validateModel(FIXTURE);renderPortfolio();
const p=model.projects[0],base=structuredClone(model.operations.sessions.find(s=>s.project_id===p.id&&s.goal));assert(base);
const variants=[{...base,id:'collision',actor_id:'Alice',session_id:'collision',goal:'Alice codex goal',task_ids:p.work.tasks.slice(0,2).map(t=>t.id),lifecycle:'ended',completion:'failed'},
 {...base,id:'collision',actor_id:'Bob',session_id:'collision',goal:'Bob codex goal'},
 {...base,id:'collision',actor_id:'Alice',session_id:'collision',environment_id:'other-env',goal:'Other environment goal'},
 {...base,id:'collision',actor_id:'Alice',session_id:'collision',source:'claude',goal:'Other provider goal'},
 {...base,id:'collision',actor_id:'Alice',session_id:'collision',source_project_id:'other-source-project',goal:'Other source project goal'}];
model.operations.sessions=variants;
p.sessions=[{id:'collision',actor_id:'Alice',environment_id:base.environment_id,source:base.source,source_project_id:base.source_project_id,event_count:2},
 {id:'legacy-only',actor_id:'Alice',environment_id:'legacy-env',event_count:1},
 {id:'collision',actor_id:'Alice',environment_id:base.environment_id,event_count:1}];
const before=JSON.stringify(model),has=(n,c)=>String(n.className||'').split(' ').includes(c);
const box=new Element('div');humanRenderSessions(box,p);
const operations=all(box).filter(n=>n.dataset.operationSession),legacy=all(box).filter(n=>has(n,'human-legacy-session'));
assert.equal(operations.length,5,'Same native or operation ID across people/environment/provider/source project must stay distinct');
assert.equal(new Set(operations.map(n=>n.id)).size,5,'DOM IDs must preserve compound identity');
assert.equal(legacy.length,2,'Known matching raw identity renders once; unknown provider legacy is retained rather than inferred');
assert(box.textContent.includes('legacy-only'));assert(/목표.*미확인|목표.*미관측/.test(legacy.map(n=>n.textContent).join(' ')));
for(const s of variants)assert(box.textContent.includes(s.goal));
const ended=operations.find(n=>n.textContent.includes('Alice codex goal'));assert(ended.textContent.includes(lifeLabels.ended));assert(ended.textContent.includes(completionLabels.failed));
for(const tid of variants[0].task_ids)assert(all(ended).some(n=>n.tagName==='a'&&new URLSearchParams(n.href.slice(1)).get('task')===tid),'One session must preserve multiple actual tasks');
navigate(p,{view:'evidence'});$('tab-sessions').click();
const history=$('detailPanel');assert.equal(all(history).filter(n=>has(n,'human-session-evidence')).length,1,'Actual evidence entry must render one history');
assert.equal(all(history).filter(n=>has(n,'row')).length,7,'Raw session list cannot be appended before goal history');
$('ownerFilter').value='Bob';const scoped=new Element('div');humanRenderSessions(scoped,p);assert(scoped.textContent.includes('Bob codex goal'));assert(!scoped.textContent.includes('Alice codex goal'));
const empty=new Element('div');humanRenderSessions(empty,{...p,id:'unobserved',sessions:[]});assert(/미관측|기록 없음/.test(empty.textContent));assert(!/성공.*0|0.*성공/.test(empty.textContent));
assert.equal(JSON.stringify(model),before,'Single history cannot change acceptance or identity');
console.log('Visual sessions PASS: compound identities, one known raw/goal execution, ambiguous legacy retained, ended/failed distinction, multiple tasks, person scope and missing collection');
'''

DOCUMENTARY = r'''
model=validateModel(FIXTURE);renderPortfolio();const before=JSON.stringify(model),p=model.projects[0];navigate(p);
const panel=$('detailPanel'),has=(n,c)=>String(n.className||'').split(' ').includes(c);
assert(panel.textContent.includes('2026-10-01'),'Documentary progress needs its own date');
assert(panel.textContent.includes('문서'),'Documentary completion cannot masquerade as current runner pass');
assert(panel.textContent.includes('현재')&&panel.textContent.includes('미확인'),'Current acceptance stays unconfirmed');
const final=all(panel).find(n=>n.tagName==='a'&&new URLSearchParams(n.href.slice(1)).get('final')==='1');assert(final&&final.textContent.includes('미확인'));
const complete=all(panel).find(n=>has(n,'human-wbs-task')&&n.dataset.taskId==='doc-complete');assert(complete&&complete.textContent.includes('문서'),'Documentary green needs basis at the task');
const unknown=all(panel).find(n=>has(n,'human-wbs-task')&&n.dataset.taskId==='doc-unknown');assert(unknown&&unknown.textContent.includes('미지정'));assert(!unknown.textContent.includes('달성'),'Unknown document status cannot be promoted');
const docLink=all(complete).find(n=>n.tagName==='a');docLink.focus();docLink.click();assert.equal(route().kind,'task');assert.equal(route().t.id,'doc-complete');assert.equal(focused.dataset.taskId,'doc-complete','Document-only task should receive native focus');assert(focused.isConnected,'Document-only task cannot leave focus on removed link');
navigate(p,{phase:p.work.phases[0].id});assert($('detailPanel').textContent.includes('문서'));assert($('detailPanel').textContent.includes('미확인'));
const source=new Element('div');humanRenderSessions(source,{...p,id:'documentary-no-collection',sessions:[]});assert(/미관측|기록 없음/.test(source.textContent),'Documentary preview has no collected executions');
assert.equal(JSON.stringify(model),before,'Documentation cannot modify current checks or acceptance');
console.log('Documentary WBS PASS: dated document completion, unknown owner/state, separate current acceptance and no collection claim');
'''

DATES = r'''
model=validateModel(FIXTURE);renderPortfolio();const p=model.projects[0],before=JSON.stringify(model),evidenceMode=model.evidence_mode;
const source=new Element('script');source.id='sampleSchedule';document.body.append(source);
const bound={kind:'synthetic-demo-schedule',as_of:'2026-10-02',projects:[{project_id:p.id,plan_id:p.work.plan_id,plan_version:p.work.plan_version,revision:p.current_revision,tasks:p.work.tasks.map(t=>({task_id:t.id,start:'2026-10-01',end:'2026-10-03'}))}]};
source.textContent=JSON.stringify(bound);assert(sampleTimeline(p));navigate(p);assert(all($('detailPanel')).some(n=>n.className==='wbs-chart date-axis'));assert($('detailPanel').textContent.includes('가상 계획 일정'));assert($('detailPanel').textContent.includes('로그 날짜 아님'));
for(const key of ['project_id','plan_id','plan_version','revision']){const stale=structuredClone(bound);stale.projects[0][key]='stale';source.textContent=JSON.stringify(stale);renderDetail();assert.equal(sampleTimeline(p),null);assert(!all($('detailPanel')).some(n=>n.className==='wbs-chart date-axis'));assert($('detailPanel').textContent.includes('일정 미입력'));}
for(const mutate of [s=>s.projects[0].tasks.pop(),s=>s.projects[0].tasks[0].start='2026-02-30',s=>s.kind='live-schedule']){const invalid=structuredClone(bound);mutate(invalid);source.textContent=JSON.stringify(invalid);renderDetail();assert.equal(sampleTimeline(p),null);assert(!all($('detailPanel')).some(n=>n.className==='wbs-chart date-axis'));}
source.textContent=JSON.stringify(bound);model.evidence_mode='private';renderDetail();assert.equal(sampleTimeline(p),null);assert(!all($('detailPanel')).some(n=>n.className==='wbs-chart date-axis'));model.evidence_mode=evidenceMode;
assert.equal(JSON.stringify(model),before,'Schedule view cannot modify current completion');
console.log('Visual dates PASS: explicit bound synthetic dates only, stale/missing/invalid/private schedule fallback, unchanged completion');
'''


def main():
    runtime(WBS)
    runtime(SESSIONS)
    runtime(DATES)
    fixture = json.loads((ROOT / 'apps/dashboard/public/snapshot.json').read_text())
    p = fixture['projects'][0]
    documentary = {'projects': {p['id']: {'docdate': '2026-10-01', 'origin': 'synthetic-doc.md', 'tasks': {
        'doc-complete': {'id': 'doc-complete', 'title': 'Synthetic documentary completion', 'phase': p['work']['phases'][0]['id'], 'owner': 'Alice', 'status': 'documented', 'summary': 'Declared in a document', 'next_action': '', 'source': 'synthetic-source', 'done': ['Synthetic document done condition']},
        'doc-unknown': {'id': 'doc-unknown', 'title': 'Synthetic unknown record', 'phase': p['work']['phases'][1]['id'], 'status': 'unknown', 'summary': 'No current runner evidence', 'next_action': '', 'source': 'synthetic-source', 'done': []}}}},
        'sources': {'synthetic-source': {'project': p['id'], 'path': 'synthetic/doc.md', 'lines': [2, 8], 'sha256': 'synthetic', 'excerpt': 'Synthetic excerpt', 'checked_at': '2026-10-01'}}}
    runtime(DOCUMENTARY, documentary)
    print('Visual semantic regressions PASS. Simulated DOM only; desktop aesthetics/history/render acceptance is unverified; mobile excluded. No remote delivery evidence.')


if __name__ == '__main__':
    main()
