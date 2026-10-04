#!/usr/bin/env python3
"""Semantic experience regressions in a simulated DOM; browser/layout QA is separate.

Baseline: check_human_view.py passed before this feature. The previous projection
does not implement attention routing and must fail these new feature cases.
Fixtures are synthetic; documentary claims never become current verification.
"""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / 'specs/ai-pms-dashboard'


def main():
    html = (DASH / 'dashboard.html').read_text()
    assert (DASH / 'human-view.js').read_text() in html, 'Embedded JS drift'
    assert (DASH / 'human-view.css').read_text() in html, 'Embedded CSS drift'
    source = ROOT / 'specs/ai-pms-toss-ia/check_ia.py'
    spec = importlib.util.spec_from_file_location('experience_ia', source)
    ia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ia)
    harness = next(n.value.value for n in ast.walk(ast.parse(source.read_text()))
                   if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'harness' for t in n.targets))
    harness = harness.replace("||(key==='data-task-id'&&Object.hasOwn(n.dataset,'taskId'))",
                              "||(key.startsWith('data-')&&Object.hasOwn(n.dataset,key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())))")
    harness = harness.replace(' get isConnected(){', " get options(){return this.children.filter(n=>n.tagName==='option');}\n get isConnected(){")
    # Real HTMLAnchorElement.href resolves to an absolute URL. Keep the existing
    # harness cases and add independent native URL resolution/navigation cases.
    absolute_harness = harness.replace(' get options(){', " get href(){return Object.hasOwn(this.attributes,'href')?new URL(this.attributes.href,'https://pms.example.test/dashboard').href:'';}\n set href(value){this.attributes.href=String(value);}\n get options(){")
    absolute_harness = absolute_harness.replace('location.hash=this.href;renderDetail();', 'location.hash=new URL(this.href).hash;renderDetail();')
    fixture = json.loads((ROOT / 'apps/dashboard/public/snapshot.json').read_text())
    current = r'''
model=validateModel(FIXTURE);renderPortfolio();renderDetail();
const before=JSON.stringify(model),p=model.projects.find(p=>p.owners.includes('Alice')&&p.owners.includes('Bob'));
assert(p);const blocked=p.work.tasks.find(t=>t.owner==='Bob'&&t.state==='blocked');
const intervention=p.work.interventions.find(i=>i.task_id===blocked.id);
const rows=()=>all($('detailPanel')).filter(n=>n.className==='human-attention-item');
const links=box=>all(box).filter(n=>n.tagName==='a');
const taskLinks=box=>links(box).filter(n=>n.href.includes('&task='));
// Native routes have distinct project and overall addresses.
location.hash='#view=attention';renderDetail();assert.equal(route().kind,'attention');assert(!route().p);
const bob=$('peopleList').children.find(n=>n.dataset.person==='Bob');bob.click();renderDetail();
assert.equal($('ownerFilter').value,'Bob');assert(humanAttentionProjects().every(q=>q.owners.includes('Bob')||q.work?.tasks.some(t=>t.owner==='Bob')));
const scoped=humanAttention(p);assert(scoped.some(i=>i.task_ids.includes(blocked.id)));
assert(!scoped.some(i=>i.owner==='Alice'));assert(scoped.some(i=>i.owner===null));
assert(rows().some(n=>n.textContent.includes(intervention.next_action)));
navigate(p,{view:'attention'});assert.equal(route().kind,'attention');assert.equal(route().p.id,p.id);
const blockRow=rows().find(n=>n.textContent.includes(intervention.next_action));assert(blockRow);
const action=taskLinks(blockRow).find(n=>new URLSearchParams(n.href.slice(1)).get('task')===blocked.id);assert(action);
action.click();assert.equal(route().kind,'task');assert.equal(route().t.id,blocked.id);
assert($('detailPanel').textContent.includes(intervention.next_action));assert.equal(focused.dataset.taskId,blocked.id);
navigate(p,{phase:blocked.phase_id});
assert.equal($('detailPanel').children.filter(n=>n.tagName==='h3').length,3);
const summary=all($('detailPanel')).find(n=>n.className==='human-next-decision');assert(summary);
assert(summary.textContent.includes(intervention.next_action));assert(links(summary).some(n=>n.href.includes('view=attention')));
assert.equal(taskLinks($('detailPanel')).length,0,'Phase detail must not accumulate raw task lists');
assert.equal(humanReferences(p,blocked.phase_id).length,0,'Project API refs cannot imply phase usage');
// Ready and in-progress tasks are ordinary progress, not urgent requests.
$('ownerFilter').value='';
for(const t of p.work.tasks.filter(t=>['ready','in_progress','complete'].includes(t.state)))assert(!humanAttention(p).some(i=>i.task_ids.includes(t.id)));
for(const q of model.projects.filter(q=>q.work.tasks.every(t=>['ready','in_progress'].includes(t.state))))assert.equal(humanAttention(q).length,0);
assert.equal(JSON.stringify(model),before,'Navigation/filter projection changed completion or evidence');
// Missing/legacy work and unknown phase/API refs do not fabricate requests.
const legacy={...p,work:null};assert.equal(humanAttention(legacy).length,0);assert.equal(humanReferences(legacy,'missing-phase').length,0);
const missing={...p,work:{...p.work,interventions:[]}};assert.equal(humanAttention(missing).length,0);
for(const q of [legacy,missing]){const box=new Element('div');humanRenderAttention(box,q);assert.equal(taskLinks(box).length,0);assert.equal(all(box).filter(n=>n.className==='human-attention-item').length,0);}
// Group same phase/reason/action/owner, keeping all real task references.
const repeated=structuredClone(p);repeated.work.interventions=[{...intervention},{...intervention,id:'duplicate-evidence'}];
assert.equal(humanAttention(repeated).length,1);assert.deepEqual(humanAttention(repeated)[0].task_ids,[blocked.id]);
const gate={id:'phase-gate',kind:'phase_gate',owner:null,task_id:null,phase_id:blocked.phase_id,summary:'Synthetic gate evidence missing',next_action:'Check synthetic phase exit'};
const unowned={...p,work:{...p.work,interventions:[gate]}};$('ownerFilter').value='Bob';
assert.equal(humanAttention(unowned)[0].owner,null);assert.equal(humanAttention(unowned)[0].task_ids.length,0);
const gateBox=new Element('div');humanRenderAttention(gateBox,unowned);assert.equal(taskLinks(gateBox).length,0);assert(gateBox.textContent.includes(gate.next_action));
assert(links(gateBox).some(n=>n.href.includes('&phase='+gate.phase_id)));assert(links(gateBox).some(n=>n.href.includes('&final=1')));
const unknownRef={...p,work:{...p.work,interventions:[{...gate,task_id:'unknown-task',phase_id:'unknown-phase'}]}};
const unknownBox=new Element('div');humanRenderAttention(unknownBox,unknownRef);assert.equal(taskLinks(unknownBox).length,0);assert(!links(unknownBox).some(n=>n.href.includes('unknown-phase')));
// Delta and reset use the actual validation/applyChanges path, preserving a
// native link ID focus and filter, rather than directly assigning fresh models.
navigate(p,{view:'attention'});const focus=links($('detailPanel')).find(n=>n.id);assert(focus);focus.focus();
const focusId=focus.id,hashBefore=location.hash;window.scrollX=7;window.scrollY=123;let restored=null;window.scrollTo=(x,y)=>restored=[x,y];
applyChanges({cursor:1,reset:false,project_updates:[],operations:null,generated_at:model.generated_at});
assert.equal(location.hash,hashBefore);assert.equal($('ownerFilter').value,'Bob');assert.equal(focused.id,focusId);assert(focused.isConnected);assert.deepEqual(restored,[7,123]);
applyChanges({cursor:2,reset:true,project_updates:structuredClone(FIXTURE.projects),operations:FIXTURE.operations||null,generated_at:FIXTURE.generated_at});
assert.equal(location.hash,hashBefore);assert.equal(route().kind,'attention');assert.equal($('ownerFilter').value,'Bob');assert.equal(focused.id,focusId);assert(focused.isConnected);
assert.equal(JSON.stringify(model.projects),JSON.stringify(FIXTURE.projects));
// The URL is the durable person scope for reload/new tab, not the current DOM.
$('peopleList').children.find(n=>n.dataset.person==='Bob').click();
humanAttentionLink().click();assert.equal(route().kind,'attention');assert.equal($('ownerFilter').value,'Bob');
console.log('ATTENTION_BOOT_HASH='+JSON.stringify(location.hash));
console.log('Current DOM PASS: scoped attention, real blocker/task/phase route, ready exclusion, unknown/legacy/ref non-inference, grouping, unchanged completion, delta/reset filter/focus/scroll');
'''
    pid = fixture['projects'][0]['id']
    phase = fixture['projects'][0]['work']['phases'][0]['id']
    documentary = {'projects': {pid: {'docdate': '2026-10-01', 'origin': 'synthetic-doc.md', 'tasks': {
        'doc-blocked': {'id': 'doc-blocked', 'title': 'Synthetic documented blocker', 'phase': phase,
                        'status': 'blocked', 'summary': 'Synthetic policy decision', 'next_action': 'Read synthetic policy excerpt',
                        'source': 'synthetic-source', 'done': []},
        'doc-progress': {'id': 'doc-progress', 'title': 'Synthetic ordinary progress', 'phase': phase,
                         'status': 'in_progress', 'summary': 'Synthetic ongoing work', 'next_action': 'Keep synthetic work moving',
                         'source': 'synthetic-source', 'done': []},
        'doc-unspecified': {'id': 'doc-unspecified', 'title': 'Synthetic unspecified action', 'phase': phase,
                            'status': 'blocked', 'summary': 'Synthetic missing declaration', 'next_action': '',
                            'source': 'synthetic-source', 'done': []},
        'doc-alice': {'id': 'doc-alice', 'title': 'Synthetic Alice request', 'phase': phase, 'owner': 'Alice',
                      'status': 'blocked', 'summary': 'Synthetic Alice-only decision', 'next_action': 'Ask synthetic Alice',
                      'source': 'synthetic-source', 'done': []}}}},
        'sources': {'synthetic-source': {'project': pid, 'path': 'synthetic/doc.md', 'lines': [2, 8],
                                          'sha256': 'synthetic', 'excerpt': 'Synthetic excerpt', 'checked_at': '2026-10-01'}}}
    docs = r'''
model=validateModel(FIXTURE);renderPortfolio();const before=JSON.stringify(model),p=model.projects[0];
navigate(p,{view:'attention'});assert.equal(route().kind,'attention');
const groups=humanAttention(p);assert(groups.every(i=>i.documentary));assert(groups.some(i=>i.next_action==='Read synthetic policy excerpt'));
assert(!groups.some(i=>i.next_action==='Keep synthetic work moving'));
assert(!groups.some(i=>i.next_action===p.work.interventions[0].next_action),'Generated current checks must not be presented as documentary requests');
const panel=$('detailPanel');assert(panel.textContent.includes('2026-10-01'));assert(panel.textContent.includes('문서'));
assert(panel.textContent.includes('미확인'));assert(all(panel).some(n=>n.tagName==='a'&&n.href==='source-synthetic-source.html'));
assert(panel.textContent.includes('synthetic/doc.md'));assert(panel.textContent.includes('Synthetic missing declaration'));
assert(!all(panel).some(n=>['button','input'].includes(n.tagName)),'Documentary queue must be read-only');
navigate(p,{phase:humanPhases(p)[0].id});assert($('detailPanel').textContent.includes('2026-10-01'));assert($('detailPanel').textContent.includes('미확인'));
assert(all($('detailPanel')).some(n=>n.tagName==='a'&&n.href==='source-synthetic-source.html'));
assert.equal(JSON.stringify(model),before,'Documentary progress cannot promote current verification');
$('peopleList').children.find(n=>n.dataset.person==='Bob').click();navigate(p,{view:'attention'});
assert(humanAttention(p).some(i=>i.owner===null),'Project-scoped documentary requests remain visible');
assert(!humanAttention(p).some(i=>i.owner==='Alice'),'Alice documentary requests must respect Bob scope');
assert(!$('detailPanel').textContent.includes('Ask synthetic Alice'));
assert($('detailPanel').textContent.includes('Read synthetic policy excerpt'));
assert.equal(JSON.stringify(model),before,'Documentary person filtering cannot modify model');
console.log('Documentary DOM PASS: declared action only, ordinary progress excluded, dated source navigation, missing action preserved, current verification unconfirmed, unchanged model');
'''
    fresh = r'''
// BOOT_HASH was set before application JS ran; neither old DOM nor variables survive.
assert.equal(route().kind,'attention');assert.equal($('ownerFilter').value,'Bob');
assert.equal(JSON.stringify(model),JSON.stringify(FIXTURE));
assert(!all($('detailPanel')).some(n=>n.className==='human-attention-item'&&n.textContent.includes('담당 Alice')));
const expected=model.projects.filter(p=>p.owners.includes('Bob')||p.work?.tasks.some(t=>t.owner==='Bob')).reduce((n,p)=>n+humanAttention(p).length,0);
assert.equal(all($('detailPanel')).filter(n=>n.className==='human-attention-item').length,expected);
console.log('Fresh runtime PASS: actual initialization restores Bob attention URL scope with unchanged model');
'''
    absolute_return = fresh + r'''
const back=$('closeDetail');assert(back.href.startsWith('https://pms.example.test/'),'Harness must model absolute native anchor href');
const listHash=new URL(back.href).hash;assert.equal(new URLSearchParams(listHash.slice(1)).get('person'),'Bob','Global attention return URL must preserve Bob');
back.click();assert.equal(route().kind,'list');assert.equal($('ownerFilter').value,'Bob');assert.equal($('portfolio').hidden,false);
assert.equal($('projectList').children.length,model.projects.filter(p=>p.owners.includes('Bob')||p.work?.tasks.some(t=>t.owner==='Bob')).length);
assert.equal(JSON.stringify(model),JSON.stringify(FIXTURE));console.log('LIST_BOOT_HASH='+JSON.stringify(listHash));
console.log('Native anchor PASS: absolute href global attention return preserves person scope');
'''
    fresh_list = r'''
assert.equal(route().kind,'list');assert.equal($('ownerFilter').value,'Bob');assert.equal($('portfolio').hidden,false);
assert.equal($('projectList').children.length,model.projects.filter(p=>p.owners.includes('Bob')||p.work?.tasks.some(t=>t.owner==='Bob')).length);
assert(!$('projectList').children.some(n=>n.dataset.flowProject==='alice-personal'));
assert.equal(JSON.stringify(model),JSON.stringify(FIXTURE));
// List→project→list also handles absolute .href; '#' string comparison cannot
// discover the native return link correctly in real browser DOM.
const p=model.projects.find(p=>p.owners.includes('Bob'));navigate(p);const back=$('closeDetail');
assert(back.href.startsWith('https://pms.example.test/'));assert.equal(new URLSearchParams(new URL(back.href).hash.slice(1)).get('person'),'Bob');
back.click();assert.equal(route().kind,'list');assert.equal($('ownerFilter').value,'Bob');
console.log('Fresh list runtime PASS: generated return hash restores Bob on reload/new tab and project return');
'''
    sessions = r'''
model=validateModel(FIXTURE);renderPortfolio();const before=JSON.stringify(model);
for(const s of model.operations.sessions.filter(s=>s.goal)){
 const p=model.projects.find(p=>p.id===s.project_id);navigate(p,{view:'evidence'});$('tab-sessions').click();
 const panel=$('detailPanel');assert(panel.textContent.includes(s.goal),'Operations session goal missing from project evidence');
 assert(panel.textContent.includes(lifeLabels[s.lifecycle]));assert(panel.textContent.includes(completionLabels[s.completion]));
 assert(panel.textContent.includes(s.reason));
 for(const tid of s.task_ids){const a=all(panel).find(n=>n.tagName==='a'&&new URLSearchParams(n.href?.slice(1)).get('task')===tid);assert(a,'Session must link its actual task');a.click();assert.equal(route().kind,'task');assert.equal(route().t.id,tid);navigate(p,{view:'evidence'});$('tab-sessions').click();}
 const t=p.work.tasks.find(t=>s.task_ids.includes(t.id));if(t)assert(all($('detailPanel')).some(n=>n.tagName==='a'&&new URLSearchParams(n.href?.slice(1)).get('phase')===t.phase_id),'Session task must retain Phase path');
}
const failed=model.operations.sessions.find(s=>s.lifecycle==='ended'&&s.completion==='failed');assert(failed);
navigate(model.projects.find(p=>p.id===failed.project_id),{view:'evidence'});$('tab-sessions').click();
assert($('detailPanel').textContent.includes(lifeLabels.ended)&&$('detailPanel').textContent.includes(completionLabels.failed),'Ended session cannot imply completed goal');
$('peopleList').children.find(n=>n.dataset.person==='Bob').click();
const shared=model.projects.find(p=>p.owners.includes('Alice')&&p.owners.includes('Bob'));
navigate(shared,{view:'evidence'});$('tab-sessions').click();
const aliceSession=model.operations.sessions.find(s=>s.project_id===shared.id&&s.actor_id==='Alice'&&s.goal);
assert(!$('detailPanel').textContent.includes(aliceSession.goal),'Bob session evidence must not include Alice operations goals');
assert($('detailPanel').textContent.includes(completionLabels.unknown),'Unlinked Bob session retains unknown completion');
navigate(shared);assert(!$('detailPanel').textContent.includes(aliceSession.goal),'Operations sessions belong in evidence, leaving default plan minimal');
assert.equal(JSON.stringify(model),before);console.log('Session evidence PASS: operations goals, lifecycle/completion distinction, reasons, task/Phase links, unchanged model');
'''
    with tempfile.TemporaryDirectory() as td:
        boot_hash = None
        list_boot_hash = None
        for name, extra, assertions in [('current', '', current), ('fresh', '', fresh), ('absolute-return', '', absolute_return), ('fresh-list', '', fresh_list), ('sessions', '', sessions), ('documentary', '<script id="documentary-data" type="application/json">'+json.dumps(documentary)+'</script>', docs)]:
            page = ia.Structure(); page.feed(html.replace('<script>', extra+'<script>', 1))
            output = Path(td) / (name+'.js')
            initial_hash = list_boot_hash if name == 'fresh-list' else boot_hash
            boot = ('location.hash='+json.dumps(initial_hash)+";document.getElementById('pms-data').textContent=JSON.stringify(FIXTURE);\n") if name in ['fresh', 'absolute-return', 'fresh-list'] else ''
            native_harness = absolute_harness if name in ['absolute-return', 'fresh-list'] else harness
            output.write_text('const PAGE='+json.dumps(page.root)+';const FIXTURE='+json.dumps(fixture)+';\n'+native_harness+boot+html.split('<script>')[1].split('</script>')[0]+'\n'+assertions)
            run = subprocess.run(['node', str(output)], capture_output=True, text=True)
            print(run.stdout, end='')
            if run.returncode:
                print(run.stderr, end='')
                run.check_returncode()
            if name == 'current':
                boot_hash = json.loads(next(line.split('=', 1)[1] for line in run.stdout.splitlines() if line.startswith('ATTENTION_BOOT_HASH=')))
            if name == 'absolute-return':
                list_boot_hash = json.loads(next(line.split('=', 1)[1] for line in run.stdout.splitlines() if line.startswith('LIST_BOOT_HASH=')))
    print('Experience semantic regressions PASS. Simulated DOM only; real desktop/mobile rendering, history/reload and remote delivery remain separate acceptance boundaries.')


if __name__ == '__main__':
    main()
