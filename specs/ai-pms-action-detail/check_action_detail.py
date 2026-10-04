#!/usr/bin/env python3
"""Addressable minimal page DOM contracts; actual browser QA belongs to parent."""
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
    path = ROOT / 'specs/ai-pms-toss-ia/check_ia.py'
    spec = importlib.util.spec_from_file_location('action_ia', path)
    ia = importlib.util.module_from_spec(spec); spec.loader.exec_module(ia)
    page = ia.Structure(); page.feed(html)
    harness = next(n.value.value for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'harness' for t in n.targets))
    harness = harness.replace(' get isConnected(){', " get options(){return this.children.filter(n=>n.tagName==='option');}\n get isConnected(){")
    harness = harness.replace("||(key==='data-task-id'&&Object.hasOwn(n.dataset,'taskId'))", "||(key.startsWith('data-')&&Object.hasOwn(n.dataset,key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())))")
    catalog = json.loads((ROOT / 'specs/ai-pms-work-management/sample/catalog-work.json').read_text())
    fixture = portfolio.build_model(catalog=catalog, now='2026-10-02T12:00:00Z')
    assertions = r'''
model=validateModel(FIXTURE);renderPortfolio();renderDetail();
const p=model.projects[0],task=p.work.tasks.find(t=>t.id==='action-3'),charts=()=>all($('detailPanel')).filter(n=>n.className?.startsWith('wbs-chart'));
assert.equal(route().kind,'list');assert.equal($('portfolio').hidden,false);assert.equal(all($('projectList')).filter(n=>n.className?.startsWith('wbs-chart')).length,0);
const card=$('projectList').children.find(c=>c.dataset.flowProject===p.id);assert(card.textContent.includes('공동 프로젝트 · 2명'));assert(card.textContent.includes('Alice · Bob'));assert.equal(card.children.filter(n=>n.tagName==='a'&&n.dataset.project===p.id).length,1);assert(!card.children.some(n=>n.tagName==='details'));
card.children.find(n=>n.tagName==='a'&&n.dataset.project===p.id).click();assert.equal(route().kind,'plan');assert.equal(charts().length,1);assert($('detailPanel').textContent.includes('하나의 목표와 계획'));assert($('detailPanel').textContent.includes('목표 위임 담당'));assert($('detailPanel').textContent.includes('Bob'));assert.equal($('portfolio').hidden,true);
const state=p.status,phaseStates=p.work.phases.map(ph=>ph.state);$('ownerFilter').value='Bob';navigate(p);assert($('detailPanel').textContent.includes('Bob 담당 범위 강조'));assert.equal(charts().length,1);assert.equal(p.status,state);assert.deepEqual(p.work.phases.map(ph=>ph.state),phaseStates);
const b=$('detailPanel').querySelectorAll('[data-wbs-task]').find(b=>b.dataset.wbsTask===task.id);b.click();assert.equal(route().kind,'task');assert.equal(route().t.id,task.id);assert(location.hash.includes('&task='+task.id));assert.equal(charts().length,0);assert.equal($('portfolio').hidden,true);assert.equal(focused,$('detailPanel'));
const groups=$('detailPanel').children.filter(n=>n.className==='action-group');assert.equal(groups.length,4);assert(groups[0].textContent.includes(task.latest_update.next_action));assert(groups[1].textContent.includes('Bob'));assert(groups[2].textContent.includes(task.latest_update.summary));for(const done of task.done_when)assert(groups[3].textContent.includes(done));const evidence=$('detailPanel').children.find(n=>n.tagName==='details');assert(evidence&&!evidence.open);assert(evidence.textContent.includes('작업 ID:'));assert.equal($('tab-work').parentElement.hidden,true);
evidence.open=true;const nested=all(evidence).filter(n=>n.tagName==='details'&&n!==evidence)[0];nested.open=true;nested.children[0].focus();const nestedFocus=nested.children[0].id;renderDetail();assert($(nested.id).open);assert.equal(focused.id,nestedFocus);evidence.children[0].focus();renderDetail();assert.equal(route().kind,'task');assert($('detailPanel').children.find(n=>n.tagName==='details').open);assert.equal(focused.id,evidence.id+'-summary');assert.equal($('detailPanel').children.filter(n=>n.className==='action-group').length,4); // reload rendering reconstructs one page
applyChanges({cursor:1,reset:false,project_updates:[],operations:null,generated_at:model.generated_at});assert.equal(route().kind,'task');assert.equal($('ownerFilter').value,'Bob');assert.equal(focused.id,evidence.id+'-summary');assert($('detailPanel').children.find(n=>n.tagName==='details').open);
applyChanges({cursor:2,reset:true,project_updates:FIXTURE.projects,operations:null,generated_at:FIXTURE.generated_at});assert.equal(route().t.id,task.id);assert.equal($('ownerFilter').value,'Bob');$('closeDetail').click();assert.equal(route().kind,'plan');assert.equal(charts().length,1);assert.equal(focused.dataset.wbsTask,task.id);
// Native hash state is also the sole source for Back/Forward/direct navigation.
location.hash=routeHash(p,{task:task.id});renderDetail();assert.equal(route().kind,'task');location.hash=routeHash(p);renderDetail();assert.equal(route().kind,'plan');location.hash='';renderDetail();assert.equal(route().kind,'list');location.hash=routeHash(p,{phase:p.work.phases[1].id});renderDetail();assert.equal(route().kind,'phase');assert.equal(charts().length,0);assert.equal($('detailPanel').querySelectorAll('[data-task-id]').length,0);assert(all($('detailPanel')).some(n=>n.tagName==='a'&&n.href.includes('&task=')));
for(const hash of ['#project=missing',routeHash(p,{task:'missing'}),routeHash(p,{phase:'missing'}),routeHash(p,{task:task.id,phase:p.work.phases[0].id}),routeHash(p)+'&project=duplicate',routeHash(p,{view:'unknown'}),'#project=%ZZ']){location.hash=hash;renderDetail();assert.equal(route().kind,'invalid');assert.equal($('detail').hidden,false);assert($('detailPanel').textContent.includes('住所')||$('detailPanel').textContent.includes('주소'));assert.equal(charts().length,0);}
const missing=structuredClone(task);missing.owner=null;missing.latest_update=null;missing.done_when=[];missing.criterion_ids=[];missing.waiting_on=[];const host=new Element('div');renderAction(host,p,missing);assert(host.textContent.includes('담당 미지정'));assert(host.textContent.includes('구체적인 막힘 사유 미입력'));assert(host.textContent.includes('완료 조건 미입력'));assert(host.textContent.includes('검사 실행 근거 미관측'));assert(!host.textContent.includes('Bob가'));
for(const state of ['review_pending','failed','unknown','complete']){const t={...missing,state,reason:'현재 확인 상태',completed:state==='complete'};const box=new Element('div');renderAction(box,p,t);assert.equal(box.children.filter(n=>n.className==='action-group').length,4);assert(box.textContent.includes('현재 확인 상태'));}
const stale={...task,review_required:true,completed:false,state:'review_pending',latest_review:{decision:'approved'}};const pending=new Element('div');renderAction(pending,p,stale);assert(pending.textContent.includes('현재 승인 확인 필요'));
const unsafe={...task,title:'<img src=x onerror=alert(1)>',latest_update:{...task.latest_update,next_action:'<script>alert(1)</script>'}};model.projects[0].work.tasks[model.projects[0].work.tasks.findIndex(t=>t.id===task.id)]=unsafe;location.hash=routeHash(p,{task:task.id});renderDetail();assert($('detailName').textContent.includes('<img'));assert($('detailPanel').textContent.includes('<script>'));assert(!all($('detail')).some(n=>n.tagName==='img'||n.tagName==='script'));
console.log('Action detail PASS: list/plan/task addresses, strict invalid routes, one shared plan, actual owners/action/blocker/exit facts, missing states, closed evidence, scope/focus/live/reset and text safety. Browser reload/history/layout require parent QA.');
'''
    script = evidence_render_script(html.split('<script>')[1].split('</script>')[0])
    assert '.innerHTML' not in script and "window.addEventListener('hashchange',()=>renderDetail())" in script
    assert 'flow-inspector\');inspector' not in script
    with tempfile.TemporaryDirectory() as td:
        output = Path(td) / 'action-dom.js'
        output.write_text('const PAGE=' + json.dumps(page.root) + ';const FIXTURE=' + json.dumps(fixture) + ';\n' + harness + script + '\n' + assertions)
        subprocess.run(['node', str(output)], check=True)


if __name__ == '__main__':
    main()
