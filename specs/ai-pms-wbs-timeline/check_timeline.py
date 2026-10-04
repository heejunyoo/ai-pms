#!/usr/bin/env python3
"""Runnable WBS/date-binding/native interaction contracts; browser quality is separate."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'specs/ai-pms-dashboard'))
import portfolio
from evidence_render_tests import evidence_render_script


def main():
    html = (ROOT / 'specs/ai-pms-dashboard/dashboard.html').read_text()
    script = evidence_render_script(html.split('<script>')[1].split('</script>')[0])
    ia_path = ROOT / 'specs/ai-pms-toss-ia/check_ia.py'
    spec = importlib.util.spec_from_file_location('timeline_ia', ia_path)
    ia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ia)
    page = ia.Structure()
    page.feed(html)
    tree = ast.parse(ia_path.read_text())
    harness = next(n.value.value for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'harness' for t in n.targets))
    harness = harness.replace(' get isConnected(){', " get options(){return this.children.filter(n=>n.tagName==='option');}\n get isConnected(){")
    harness = harness.replace("||(key==='data-task-id'&&Object.hasOwn(n.dataset,'taskId'))", "||(key.startsWith('data-')&&Object.hasOwn(n.dataset,key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())))")
    # Browsers clamp detached chart scrollLeft to zero: do not let the DOM mock
    # hide a restore-before-attachment regression. Geometry still needs browser QA.
    harness = harness.replace(' get isConnected(){', " get scrollLeft(){return this._scrollLeft||0;}\n set scrollLeft(value){this._scrollLeft=this.className==='wbs-scroll'&&!this.isConnected?0:value;}\n get isConnected(){")
    catalog = json.loads((ROOT / 'specs/ai-pms-work-management/sample/catalog-work.json').read_text())
    store = portfolio.read_json(ROOT / 'specs/ai-pms-dashboard/sample/central.json')
    for project in catalog['projects']:
        for ref in project['source_refs']:
            key = portfolio.central.source_key(ref)
            if key not in store['sources']:
                store['sources'][key] = dict(ref, label='합성 예시', evidence_mode='synthetic', events={})
    fixture = portfolio.build_model(store, catalog, now='2026-10-02T12:00:00Z')
    schedule = json.loads((ROOT / 'specs/ai-pms-wbs-timeline/sample-schedule.json').read_text())
    assert '.wbs-scroll{overflow-x:auto' in html and 'position:sticky;left:0' in html
    assert 'wbs-row wbs-task' in script and 'wbs-diamond' in script and '.innerHTML' not in script
    assertions = r'''
model=validateModel(FIXTURE);renderPortfolio();
const p=model.projects[0],card=()=>$('detailPanel'),rows=()=>card().querySelectorAll('[data-wbs-task]'),phases=()=>card().querySelectorAll('[data-flow-node]');
assert.equal(rows().length,0);navigate(p);assert.equal(rows().length,p.work.tasks.length);assert.equal(phases().length,p.work.phases.length+1);
assert(card().textContent.includes('일정 미입력 · Phase축'));assert(!all(card()).some(n=>n.className==='flow-step'));assert(!all(card()).some(n=>n.className==='flow-arrow'));
const phase=p.work.phases[0],task=p.work.tasks.find(t=>t.phase_id===phase.id),first=rows().find(r=>r.dataset.wbsTask===task.id);
assert.equal(first.tagName,'button');assert(first.getAttribute('aria-label').includes(task.owner));first.click();assert.equal(flowSelection.get(p.id),'task:'+task.id);assert.equal(route().kind,'task');assert.equal(focused.dataset.taskId,task.id);assert(card().textContent.includes('완료로 바꾸려면'));assert(card().textContent.includes('선행 작업:'));assert.equal(rows().length,0);
$('closeDetail').click();assert.equal(focused.dataset.wbsTask,task.id);
const collapseId='flow-'+encodeURIComponent(p.id)+'-'+encodeURIComponent('collapse:'+phase.id),groupId='flow-'+encodeURIComponent(p.id)+'-'+encodeURIComponent('tasks:'+phase.id);
$(collapseId).click();assert.equal($(groupId).hidden,true);assert.equal($(collapseId).getAttribute('aria-expanded'),'false');assert.equal(focused.id,collapseId);
const before=p.work.phases.map(x=>x.state),projectState=p.status;
$('peopleList').children.find(b=>b.dataset.person==='Bob').click();renderDetail();assert.equal(rows().length,p.work.tasks.length);assert.equal(phases().length,p.work.phases.length+1);assert.equal($(groupId).hidden,true);assert.deepEqual(p.work.phases.map(x=>x.state),before);assert.equal(p.status,projectState);
for(const row of rows())assert.equal(row.parentElement.parentElement.className.includes(' scoped'),p.work.tasks.find(t=>t.id===row.dataset.wbsTask).owner==='Bob');
$(collapseId).focus();applyChanges({cursor:1,reset:false,project_updates:[],operations:null,generated_at:model.generated_at});assert.equal($(groupId).hidden,true);assert.equal(focused.id,collapseId);assert(focused.isConnected);$(collapseId).click();assert.equal($(groupId).hidden,false);
rows().find(b=>b.dataset.wbsTask===task.id).click();applyChanges({cursor:2,reset:true,project_updates:FIXTURE.projects,operations:null,generated_at:FIXTURE.generated_at});assert.equal(flowSelection.get(p.id),'task:'+task.id);assert.equal(route().t.id,task.id);assert.equal(focused.dataset.taskId,task.id);$('closeDetail').click();
const source=new Element('script');source.id='sampleSchedule';source.textContent=JSON.stringify(SCHEDULE);document.body.append(source);
assert.equal(model.evidence_mode,'synthetic');assert.equal(sampleTimeline(model.projects[0]).count,12);renderDetail();assert(card().textContent.includes('가상 계획 일정'));assert(card().textContent.includes('예시 기준일 2026-10-02'));assert(card().textContent.includes('로그 날짜 아님'));assert(all(card()).some(n=>n.className==='wbs-chart date-axis'));
assert.equal(all(card()).filter(n=>n.className?.startsWith('wbs-bar')&&!n.className.includes('summary')).length,p.work.tasks.length);assert.equal(all(card()).filter(n=>n.className?.startsWith('wbs-diamond')).length,1);
const scroll=()=>all(card()).find(n=>n.className==='wbs-scroll');scroll().scrollLeft=300;scroll().onscroll();
let bars=card().querySelectorAll('[data-wbs-bar]');assert.equal(bars.length,p.work.phases.length+p.work.tasks.length+1);const taskBar=bars.find(n=>n.dataset.wbsBar==='task:'+task.id);assert.equal(taskBar.tagName,'button');taskBar.click();assert.equal(flowSelection.get(p.id),'task:'+task.id);assert.equal(route().t.id,task.id);assert.equal(scroll(),undefined);$('closeDetail').click();assert.equal(scroll().scrollLeft,300);assert.equal(focused.dataset.wbsBar,'task:'+task.id);
$(collapseId).click();assert.equal($(groupId).hidden,true);assert.equal(scroll().scrollLeft,300);$(collapseId).click();assert.equal($(groupId).hidden,false);assert.equal(scroll().scrollLeft,300);
card().querySelectorAll('[data-wbs-bar]').find(n=>n.dataset.wbsBar==='phase:'+phase.id).click();assert.equal(flowSelection.get(p.id),'phase:'+phase.id);assert.equal(route().kind,'phase');assert.equal(card().querySelectorAll('[data-task-id]').length,0);$('closeDetail').click();assert.equal(scroll().scrollLeft,300);
card().querySelectorAll('[data-wbs-bar]').find(n=>n.dataset.wbsBar==='project').click();assert.equal(flowSelection.get(p.id),'project');assert.equal(route().kind,'final');assert(card().textContent.includes('전체 검사'));$('closeDetail').click();assert.equal(scroll().scrollLeft,300);
applyChanges({cursor:3,reset:false,project_updates:[],operations:null,generated_at:model.generated_at});assert.equal(scroll().scrollLeft,300);assert.equal(flowSelection.get(p.id),'project');
// A live render can run synchronously before the browser emits its scroll event.
scroll().scrollLeft=200;applyChanges({cursor:4,reset:false,project_updates:[],operations:null,generated_at:model.generated_at});assert.equal(scroll().scrollLeft,200);
flowOrigin.set(p.id,'bar-removed-by-live-schedule');navigate(p,{final:'1'});$('closeDetail').click();assert.equal(route().kind,'plan');assert.equal(focused.id,'detailName');assert(focused.isConnected);
const hint=all(card()).find(n=>n.className==='wbs-mobile-hint');assert(hint.parentElement.children.indexOf(hint)<hint.parentElement.children.indexOf(scroll()));
const mutate=(change)=>{const x=structuredClone(SCHEDULE);change(x);source.textContent=JSON.stringify(x);assert.equal(sampleTimeline(model.projects[0]),null);renderDetail();assert(card().textContent.includes('일정 미입력 · Phase축'));assert(!card().textContent.includes('가상 계획 일정'));};
for(const key of ['project_id','plan_id','plan_version','revision'])mutate(x=>x.projects[0][key]='stale');
mutate(x=>x.projects.push(structuredClone(x.projects[0])));mutate(x=>x.projects[0].tasks[0].task_id='missing');mutate(x=>x.projects[0].tasks.push(structuredClone(x.projects[0].tasks[0])));mutate(x=>x.projects[0].tasks.pop());mutate(x=>x.projects[0].tasks[0].start='2026-02-30');mutate(x=>x.projects[0].tasks[0].end='2026-09-01');mutate(x=>x.as_of='today');mutate(x=>x.kind='live-schedule');
source.textContent='{broken';assert.equal(sampleTimeline(model.projects[0]),null);source.textContent=JSON.stringify(SCHEDULE);model.evidence_mode='private';assert.equal(sampleTimeline(model.projects[0]),null);model.evidence_mode='synthetic';
const oldState=model.projects[0].status;assert.equal(sampleTimeline({...model.projects[0],current_revision:'stale'}),null);assert.equal(model.projects[0].status,oldState);
const unsafe=structuredClone(model.projects[0]);unsafe.work.tasks[0].title='<img src=x onerror=alert(1)>';const host=new Element('div');renderPhaseFlow(host,unsafe);assert(host.textContent.includes(unsafe.work.tasks[0].title));assert(!all(host).some(n=>n.tagName==='img'));
console.log('WBS timeline PASS: hierarchy, task detail/focus, collapse/scope/live preservation, strict authored fixture binding/invalid fallback, no fabricated date axis, safe DOM. Actual browser/render unverified.');
'''
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'timeline-dom.js'
        path.write_text('const PAGE=' + json.dumps(page.root) + ';const FIXTURE=' + json.dumps(fixture) + ';const SCHEDULE=' + json.dumps(schedule) + ';\n' + harness + script + '\n' + assertions)
        subprocess.run(['node', str(path)], check=True)


if __name__ == '__main__':
    main()
