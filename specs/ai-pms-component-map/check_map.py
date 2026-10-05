#!/usr/bin/env python3
"""Declared component/connection regressions. Simulated DOM is not browser proof."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / 'specs/ai-pms-readable-project/check_readable.py'
spec = importlib.util.spec_from_file_location('readable_map', path)
readable = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readable)

MAP = readable.COMMON + r'''
const p=model.projects.find(p=>p.owners.includes('Alice')&&p.owners.includes('Bob')),before=JSON.stringify(model);
$('ownerFilter').value='Bob';navigate(p);
const map=$('human-component-map'),panel=$('detailPanel');assert(map);assert.equal(all(panel).filter(n=>has(n,'human-component-map')).length,1);
assert.equal(panel.children[0].id,'human-project-summary');assert.equal(panel.children[1],map);assert(has(panel.children[2],'human-wbs'),'Diagram belongs between summary and existing WBS');
assert(visible(map).includes(p.goal));assert(visible(map).includes('소속'));assert(visible(map).includes('참고'));assert(visible(map).includes('실행 의존성을 뜻하지 않습니다'));
const columns=all(map).filter(n=>has(n,'human-map-phase'));assert.deepEqual(columns.map(n=>n.dataset.phaseId),p.work.phases.map(ph=>ph.id));
assert.deepEqual(all(map).filter(n=>has(n,'human-map-task')).map(n=>n.dataset.taskId).sort(),p.work.tasks.map(t=>t.id).sort(),'All shared owner and unassigned tasks remain in the diagram');
for(const ph of p.work.phases){const col=columns.find(n=>n.dataset.phaseId===ph.id);assert(col.textContent.includes(humanPhase(p,ph).goal));assert(col.textContent.includes(humanStatus(humanPhase(p,ph).state)));const a=links(col).find(a=>new URLSearchParams(a.href.slice(1)).get('phase')===ph.id);assert(a);assert.equal(new URLSearchParams(a.href.slice(1)).get('person'),'Bob');assert.equal(all(col).filter(n=>has(n,'human-map-reference')&&n.dataset.referenceName).length,0,'Unlinked project resources cannot become phase edges');for(const t of humanTasks(p,ph.id)){const n=all(col).find(n=>has(n,'human-map-task')&&n.dataset.taskId===t.id);assert(n);assert(n.textContent.includes(t.owner||'미지정'));assert(n.textContent.includes(humanStatus(t.state)));assert.equal(has(n,'human-owner-selected'),t.owner==='Bob');}}
const common=all(map).find(n=>has(n,'human-map-common'));for(const r of humanReferences(p))assert(common.textContent.includes(r.name));
for(const d of p.documents){const col=columns.find(n=>n.dataset.phaseId===d.phase_id)||common;assert(all(col).some(n=>n.dataset.documentId===d.id),'Document edge must follow its declared phase only');}
const phaseLink=links(columns[0]).find(a=>new URLSearchParams(a.href.slice(1)).has('phase'));phaseLink.click();assert.equal(route().kind,'phase');assert.equal(route().phase.id,p.work.phases[0].id);assert.equal($('ownerFilter').value,'Bob');$('closeDetail').click();assert.equal(route().kind,'plan');
const task=humanTasks(p)[0],taskLink=links($('human-component-map')).find(a=>new URLSearchParams(a.href.slice(1)).get('task')===task.id);taskLink.focus();taskLink.click();assert.equal(route().kind,'task');assert.equal(route().t.id,task.id);assert.equal($('ownerFilter').value,'Bob');$('closeDetail').click();const sameHash=location.hash;renderDetail();assert.equal(location.hash,sameHash);assert($('human-component-map'),'Route reload must restore map');
const documentLink=links($('human-component-map')).find(a=>all($('human-component-map')).some(n=>n.dataset.documentId===p.documents[0]?.id&&all(n).includes(a)));if(documentLink){documentLink.click();assert.equal(route().kind,'evidence');assert.equal(activeTab,'documents');const d=[...p.documents].sort((a,b)=>Date.parse(b.at)-Date.parse(a.at))[Number(selectedDocument)];assert.equal(d.id,p.documents[0].id);assert($('detailPanel').textContent.includes(d.content));}
for(const d of p.documents){navigate(p);const entry=all($('human-component-map')).find(n=>n.dataset.documentId===d.id&&n.dataset.documentVersion===(d.version||''));assert(entry,'Each document version retains a map entry');assert(entry.textContent.includes(versionLabel(d.version)));assert(entry.textContent.includes(when(d.at)));links(entry)[0].click();assert.equal(activeTab,'documents');assert.equal(Number(selectedDocument),[...p.documents].sort((a,b)=>Date.parse(b.at)-Date.parse(a.at)).indexOf(d),'Duplicate document IDs must retain exact version identity');assert($('detailPanel').textContent.includes(d.content),'Map reference must show original selected version content');}
const missing=structuredClone(p);missing.work=null;missing.phases=[];missing.documents=[];const empty=humanComponentMap(missing);assert(/단계 구성 미기록/.test(empty.textContent));assert(!all(empty).some(n=>has(n,'human-map-task')));
const unsafe=structuredClone(p);unsafe.goal='<img src=x onerror=alert(1)>';unsafe.work.tasks[0].title='<script>evil</script>';unsafe.documents[0].title='<svg onload=evil>';const safe=humanComponentMap(unsafe);for(const token of [unsafe.goal,unsafe.work.tasks[0].title,unsafe.documents[0].title])assert(safe.textContent.includes(token));assert(!all(safe).some(n=>['img','script','svg'].includes(n.tagName)));
const key=p.id,original=humanAnnotations[key];humanAnnotations[key]={references:[{name:'Declared phase MCP',basis:'설정 기록',phase_ids:[p.work.phases[0].id]},{name:'Declared common API',basis:'입력 기록',phase_ids:[]},{name:'Unresolved phase API',basis:'입력 기록',phase_ids:['not-in-plan']}]};
const authored=humanComponentMap(p),first=all(authored).find(n=>n.dataset.phaseId===p.work.phases[0].id),second=all(authored).find(n=>n.dataset.phaseId===p.work.phases[1].id),commonAuthored=all(authored).find(n=>has(n,'human-map-common'));assert(first.textContent.includes('Declared phase MCP'));assert(!second.textContent.includes('Declared phase MCP'));assert(!commonAuthored.textContent.includes('Declared phase MCP'));for(const name of ['Declared common API','Unresolved phase API']){assert(commonAuthored.textContent.includes(name));assert(!first.textContent.includes(name));}assert(!links(first).some(a=>/^https?:/.test(a.href)),'Reference without a declared URL remains text');if(original===undefined)delete humanAnnotations[key];else humanAnnotations[key]=original;
assert.equal(JSON.stringify(model),before,'Diagram cannot mutate completion or source model');
console.log('Component map PASS: declared containment/reference edges, all shared tasks, scoped phase/task routes, document selection, missing data, safe text, immutable model; simulated DOM only');
'''

DOCUMENTARY = readable.COMMON + r'''
const p=model.projects[0],before=JSON.stringify(model);navigate(p);const map=$('human-component-map');assert(map);assert(visible(map).includes('2026-10-01'));assert(/현재.*미확인/.test(visible(map)));assert(!visible(map).includes('검증 완료'),'Documentary completion cannot become execution proof');
assert.deepEqual(all(map).filter(n=>has(n,'human-map-task')).map(n=>n.dataset.taskId).sort(),['doc-complete','doc-unknown']);const columns=all(map).filter(n=>has(n,'human-map-phase'));const first=columns.find(n=>n.dataset.phaseId===p.work.phases[0].id),second=columns.find(n=>n.dataset.phaseId===p.work.phases[1].id);assert(first.textContent.includes('문서상 완료'));assert(first.textContent.includes('synthetic/complete.md'));assert(!second.textContent.includes('synthetic/complete.md'));assert(second.textContent.includes('synthetic/plan.md'));assert(second.textContent.includes('연결된 문서 출처 미기록'));assert(links(first).some(a=>a.href==='source-complete-source.html'));assert(links(second).some(a=>a.href==='source-plan-source.html'));const missing=all(map).find(n=>n.dataset.taskId==='doc-unknown');assert(/미지정/.test(missing.textContent));assert(/확인되지/.test(missing.textContent));
assert.equal(JSON.stringify(model),before);console.log('Component map documentary PASS: source and plan_source phase edges, dated completion separate from current execution, missing sources and unknown owner/state');
'''


def main():
    readable.visual.runtime(MAP)
    fixture=json.loads((ROOT/'apps/dashboard/public/snapshot.json').read_text())
    p=fixture['projects'][0]
    documentary={'projects':{p['id']:{'docdate':'2026-10-01','tasks':{
        'doc-complete':{'id':'doc-complete','title':'Documentary complete','phase':p['work']['phases'][0]['id'],'owner':'Alice','status':'documented','source':'complete-source'},
        'doc-unknown':{'id':'doc-unknown','title':'Unknown documentary','phase':p['work']['phases'][1]['id'],'status':'unknown','plan_source':'plan-source','source':'missing-source'}}}},
        'sources':{'complete-source':{'project':p['id'],'path':'synthetic/complete.md'},'plan-source':{'project':p['id'],'path':'synthetic/plan.md'}}}
    readable.visual.runtime(DOCUMENTARY,documentary)
    css=(ROOT/'specs/ai-pms-dashboard/human-view.css').read_text()
    for token in ['.human-map-columns:before','left:130px;right:130px','.human-map-phase:before','border-left:2px solid','.human-map-references','border-left:1px dashed','overflow-x:auto','a:focus-visible']:
        assert token in css, f'Map structure/focus/overflow CSS missing: {token}'
    print('Component map acceptance PASS: synthetic DOM and structure only. Actual desktop rendering/history/keyboard remains parent browser acceptance; mobile excluded; no deployment.')


if __name__=='__main__':
    main()
