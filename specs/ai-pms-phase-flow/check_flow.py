#!/usr/bin/env python3
"""Phase flow native DOM contracts and existing regressions; no browser/layout claim."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'specs/ai-pms-dashboard'))
import portfolio


def main():
    html = (ROOT/'specs/ai-pms-dashboard/dashboard.html').read_text()
    script = html.split('<script>')[1].split('</script>')[0]
    ia_path = ROOT/'specs/ai-pms-toss-ia/check_ia.py'
    spec = importlib.util.spec_from_file_location('flow_ia', ia_path)
    ia = importlib.util.module_from_spec(spec); spec.loader.exec_module(ia)
    page = ia.Structure(); page.feed(html)
    tree = ast.parse(ia_path.read_text())
    harness = next(n.value.value for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'harness' for t in n.targets))
    harness = harness.replace(' get isConnected(){', " get options(){return this.children.filter(n=>n.tagName==='option');}\n get isConnected(){")
    harness = harness.replace("||(key==='data-task-id'&&Object.hasOwn(n.dataset,'taskId'))", "||(key.startsWith('data-')&&Object.hasOwn(n.dataset,key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())))")
    assert page.ids['sessionArea']['tag'] == 'details' and 'open' not in page.ids['sessionArea']['attrs']
    assert '#flowArea,#northStarArea{order:1}' in html and '#sessionArea{order:3}' in html
    assert '.phase-flow{flex-direction:column}' in html and 'aria-expanded' in script and '.innerHTML' not in script
    catalog = json.loads((ROOT/'specs/ai-pms-work-management/sample/catalog-work.json').read_text())
    now = '2026-10-02T12:00:00Z'
    fixture = portfolio.build_model(catalog=catalog, now=now)
    delta_catalog = copy.deepcopy(catalog)
    delta_catalog['projects'][0]['name'] = '갱신된 프로젝트'
    delta_catalog['projects'][0]['management']['work']['tasks'][0]['title'] = '갱신된 원자 작업'
    delta_fixture = portfolio.build_model(catalog=delta_catalog, now=now)
    gated = copy.deepcopy(catalog)
    p = gated['projects'][0]; m = p['management']; w = m['work']
    w['tasks'] = w['tasks'][:1]; w['updates'] = []
    keep = {'action-1-check', 'phase-exit', 'project-exit'}
    p['phases'] = [ph for ph in p['phases'] if ph['id'] == w['tasks'][0]['phase_id']]
    p['current_phase'] = p['phases'][0]['id']
    w['phase_gates'] = [g for g in w['phase_gates'] if g['phase_id'] == p['current_phase']]
    p['documents'] = [d for d in p['documents'] if d['phase_id'] == p['current_phase']]
    p['criteria'] = [c for c in p['criteria'] if c['id'] in keep]
    m['test_plans'] = [tp for tp in m['test_plans'] if tp['criterion_id'] in keep]
    tpids = {tp['id'] for tp in m['test_plans']}; m['attempts'] = [a for a in m['attempts'] if a['test_plan_id'] in tpids]
    tp = next(tp for tp in m['test_plans'] if tp['criterion_id'] == 'project-exit')
    a = copy.deepcopy(next(a for a in m['attempts'] if a['test_plan_id'] == tp['id']))
    a.update(id='project-declared-new', at='2026-09-29T06:00:00Z', started_at='2026-09-29T06:00:00Z', provenance='declared', exit_code=None)
    m['attempts'].append(a)
    gate_fixture = portfolio.build_model(catalog=gated, now=now)
    assert all(ph['state'] == 'complete' for ph in gate_fixture['projects'][0]['work']['phases'])
    assert gate_fixture['projects'][0]['status'] != 'complete'
    legacy = copy.deepcopy(catalog)
    for p in legacy['projects']: del p['management']['work']
    legacy_fixture = portfolio.build_model(catalog=legacy, now=now)
    assertions = r'''
model=validateModel(FIXTURE);renderPortfolio();
assert.equal(centralView,'people');assert.equal($('flowArea').hidden,false);assert.equal($('sessionArea').open,false);
const shared=model.projects[0],card=()=>[...$('projectList').children].find(c=>c.dataset.flowProject===shared.id),nodes=()=>card().querySelectorAll('[data-flow-node]');
assert.equal(nodes().length,shared.work.phases.length+1);assert(card().textContent.includes('목표: '+shared.goal));assert(card().textContent.includes('완료 '));assert(card().textContent.includes('남은 단계:'));
const states=new Set();for(const p of model.projects)for(const ph of p.work.phases)states.add(ph.state);for(const state of ['complete','failed','revalidation','in_progress'])assert(states.has(state),state);
for(const p of model.projects){const c=[...$('projectList').children].find(c=>c.dataset.flowProject===p.id),buttons=c.querySelectorAll('[data-flow-node]');p.work.phases.forEach((ph,i)=>{assert.equal(buttons[i].dataset.flowNode,'phase:'+ph.id);assert(buttons[i].className.includes(ph.state));assert(buttons[i].textContent.includes(ph.name));});assert(buttons.at(-1).className.includes(p.status));}
const first=nodes()[0];assert.equal(first.tagName,'button');first.click();assert.equal(first.getAttribute('aria-expanded'),'false'); // DOM was replaced
let selected=nodes()[0];assert.equal(selected.getAttribute('aria-pressed'),'true');assert.equal(selected.getAttribute('aria-expanded'),'true');assert.equal(focused.id,'flow-'+encodeURIComponent(shared.id)+'-title');assert.equal(scrolled,focused);
const phase=shared.work.phases[0];assert(card().textContent.includes('완료 조건:'));assert(card().textContent.includes('문서 · 기준 · runner · 사람 승인 근거'));assert(card().textContent.includes('선행 작업:'));
assert.equal(card().querySelectorAll('[data-task-id]').length,shared.work.tasks.filter(t=>t.phase_id===phase.id).length);
const phaseStates=shared.work.phases.map(ph=>ph.state),projectStatus=shared.status;
$('peopleList').children.find(b=>b.dataset.person==='Bob').click();assert.equal($('ownerFilter').value,'Bob');assert.equal(nodes().length,shared.work.phases.length+1);assert.deepEqual(shared.work.phases.map(ph=>ph.state),phaseStates);assert.equal(shared.status,projectStatus);
const rows=card().querySelectorAll('[data-task-id]');assert.equal(rows.length,shared.work.tasks.filter(t=>t.phase_id===phase.id).length);for(const row of rows){const task=shared.work.tasks.find(t=>t.id===row.dataset.taskId);assert.equal(row.className.includes('flow-task-scope'),task.owner==='Bob');}
const chosen=nodes()[0];chosen.focus();const changed=structuredClone(DELTA.projects[0]);applyChanges({cursor:1,reset:false,project_updates:[changed],operations:null,generated_at:model.generated_at});assert.equal(flowSelection.get(shared.id),'phase:'+phase.id);assert.equal(nodes()[0].getAttribute('aria-expanded'),'true');assert.equal(focused.id,chosen.id);assert.equal(focused.isConnected,true);assert(card().textContent.includes('갱신된 프로젝트'));assert(card().textContent.includes('갱신된 원자 작업'));
applyChanges({cursor:2,reset:true,project_updates:FIXTURE.projects,operations:null,generated_at:FIXTURE.generated_at});assert.equal(flowSelection.get(shared.id),'phase:'+phase.id);assert.equal(nodes()[0].getAttribute('aria-expanded'),'true');
const closeButton=all(card()).find(n=>n.tagName==='button'&&n.textContent==='상세 접기 · 단계로 돌아가기');closeButton.focus();applyChanges({cursor:2,reset:false,project_updates:[],operations:null,generated_at:FIXTURE.generated_at});assert.equal(focused.id,closeButton.id);assert.equal(focused.isConnected,true);all(card()).find(n=>n.tagName==='button'&&n.textContent==='상세 접기 · 단계로 돌아가기').click();assert(!flowSelection.has(shared.id));assert.equal(focused.dataset.flowNode,'phase:'+phase.id);assert.equal(scrolled,focused);assert.equal(nodes()[0].getAttribute('aria-expanded'),'false');
$('view-projects').click();assert.equal($('flowArea').hidden,false);$('view-stars').click();assert.equal($('flowArea').hidden,true);$('view-people').click();
model=validateModel(GATE);$('ownerFilter').value='';renderPortfolio();const gateProject=model.projects[0],gateCard=[...$('projectList').children].find(c=>c.dataset.flowProject===gateProject.id);assert(gateProject.work.phases.every(ph=>ph.state==='complete'));assert.notEqual(gateProject.status,'complete');const final=gateCard.querySelectorAll('[data-flow-node]').at(-1);assert(final.className.includes(gateProject.status));final.click();assert(gateCard.textContent.includes('최종 프로젝트 판정'));assert(gateCard.textContent.includes('완료 검사:'));assert(gateCard.textContent.includes('runner 근거:'));
model=validateModel(LEGACY);flowSelection.clear();renderPortfolio();const old=model.projects[0],oldCard=[...$('projectList').children].find(c=>c.dataset.flowProject===old.id);assert(oldCard.textContent.includes('기존 단계 검사'));assert(oldCard.textContent.includes('원자화 작업 계획 미관측'));oldCard.querySelectorAll('[data-flow-node]')[0].click();assert(oldCard.textContent.includes('완료 조건 계획 미입력'));
const empty=structuredClone(LEGACY);empty.projects=[];applyChanges({cursor:3,reset:true,project_updates:[],operations:null,generated_at:empty.generated_at});assert.equal(flowSelection.size,0);assert($('projectList').textContent.includes('중앙 현황을 가져오세요'));
model=validateModel(FIXTURE);model.projects[0].name='<img src=x onerror=alert(1)>';renderPortfolio();assert($('projectList').textContent.includes('<img src=x onerror=alert(1)>'));assert(!all($('projectList')).some(n=>n.tagName==='img'));
flowSelection.set(model.projects[0].id,'phase:removed');const removed=new Element('div');renderPhaseFlow(removed,model.projects[0]);assert(!flowSelection.has(model.projects[0].id));const noPlan=new Element('div');renderPhaseFlow(noPlan,{...model.projects[0],work:null,phases:[]});assert(noPlan.textContent.includes('계획 미입력'));assert.equal(noPlan.querySelectorAll('[data-flow-node]').length,1);
console.log('Phase flow DOM PASS: primary goal/full ordered phases, scope/full tasks, gates/evidence, native selection/focus return, live merge/reset/removal, legacy/empty/text safety. Browser/mobile render unverified.');
'''
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'flow-dom.js'
        path.write_text('const PAGE='+json.dumps(page.root)+';const FIXTURE='+json.dumps(fixture)+';const DELTA='+json.dumps(delta_fixture)+';const GATE='+json.dumps(gate_fixture)+';const LEGACY='+json.dumps(legacy_fixture)+';\n'+harness+script+'\n'+assertions)
        subprocess.run(['node', str(path)], check=True)
    subprocess.run([sys.executable, str(ROOT/'specs/ai-pms-live/check_ui_live.py')], check=True)
    print('Phase flow acceptance PASS; actual browser/390px rendering unverified')


if __name__ == '__main__': main()
