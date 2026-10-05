#!/usr/bin/env python3
"""Human question/result/action regressions. Synthetic DOM; no visual/provider claim."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / 'specs/ai-pms-visual-management/check_visual.py'
spec = importlib.util.spec_from_file_location('readable_visual', path)
visual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visual)

COMMON = r'''
const has=(n,c)=>String(n.className||'').split(' ').includes(c);
function visible(n){if(n.hidden)return '';if(n.tagName==='details'&&!n.open)return n.children.filter(c=>c.tagName==='summary').map(visible).join(' ');return n._text+' '+n.children.map(visible).join(' ');}
function displayed(n){for(let p=n;p;p=p.parentElement){if(p.hidden)return false;if(p!==n&&p.tagName==='details'&&!p.open&&!p.children.filter(c=>c.tagName==='summary').some(s=>all(s).includes(n)))return false;}return true;}
const links=n=>all(n).filter(n=>n.tagName==='a');
function noRaw(n,p){const text=visible(n);for(const c of p.criteria||[])for(const token of [c.command,c.id])if(token)assert(!text.includes(token),'Raw criterion/command leaked: '+token);for(const r of p.runs||[])if(r.criterion_signature)assert(!text.includes(r.criterion_signature),'Raw signature leaked');assert(!/mock-|phase-exit|\brunner\b/.test(text),'Raw execution fields leaked');}
model=validateModel(FIXTURE);renderPortfolio();renderDetail();
'''

RESULTS = COMMON + r'''
const before=JSON.stringify(model),p=model.projects[0];
navigate(p);assert($('human-project-summary'));assert(visible($('human-project-summary')).includes(p.goal));
const nav=$('human-project-nav');assert(nav);for(const title of ['계획','확인 결과','실행 이력','참고 자료'])assert(nav.textContent.includes(title));
assert.deepEqual(all($('detailPanel')).filter(n=>has(n,'human-wbs-task')).map(n=>n.dataset.taskId).sort(),p.work.tasks.map(t=>t.id).sort());
navigate(p,{view:'evidence'});assert.equal(activeTab,'work');assert.equal($('human-question-work').getAttribute('aria-pressed'),'true');
const cards=all($('detailPanel')).filter(n=>has(n,'human-result-card'));assert(cards.length,'Evidence must explain results before technical records');
assert.equal(all($('detail')).filter(n=>n.id==='human-project-nav'&&displayed(n)).length,1,'Project evidence has a single visible navigation');
assert(!visible($('human-evidence-questions')).trim(),'Repeated visible question row duplicates project navigation');
for(const t of p.work.tasks){assert.equal(cards.filter(n=>displayed(n)&&n.dataset.checkTarget===t.id).length,1,'Each task needs one main explanation, with checker detail closed');}
for(const t of p.work.tasks.filter(t=>t.completed)){const card=cards.find(n=>displayed(n)&&n.dataset.checkTarget===t.id);assert(/남은.*없|추가.*없|필수.*없|완료 조건.*충족/.test(visible(card)),'Completed task must explain that no required action remains');assert(!visible(card).includes('담당자가 다음 행동과 요청사항을 기록해야 합니다.'),'Completed task cannot invent new work');}
for(const card of cards){const text=visible(card);assert(/확인|목표|내용/.test(text));assert(/결과/.test(text));assert(/다음|할 일|남은/.test(text));assert(links(card).length,'Result must lead to task/phase/final action');}
for(const t of p.work.tasks){assert(visible($('detailPanel')).includes(t.title),'Every actual task result remains explained');}
assert(visible($('detailPanel')).includes(humanStatus('review_pending')),'Passing technical check cannot hide required human review');
assert(/미확인|확인되지|미기록|미지정/.test(visible($('detailPanel'))),'Unknown work cannot become complete');
noRaw($('detailPanel'),p);assert.equal($('human-technical-evidence').open,false);
for(const tab of ['connections','management','tests']){activeTab=tab;renderTab(p);assert($($('detailPanel').getAttribute('aria-labelledby')),'Technical evidence needs an existing accessible heading');}activeTab='work';renderTab(p);
const disclosed=all($('detailPanel')).filter(n=>n.tagName==='details');assert(disclosed.some(n=>n.textContent.includes(p.criteria[0].command)),'Raw command remains available behind disclosure');
assert(disclosed.some(n=>n.textContent.includes(p.runs[0].criterion_signature)),'Raw signature remains available behind disclosure');
for(const [state,pattern] of [['failed',/실패/],['revalidation',/재검증|현재.*다시|현재.*검사/]]){const q=model.projects.find(q=>q.work.tasks.some(t=>t.state===state));assert(q,'Synthetic counterexample missing');navigate(q,{view:'evidence'});assert(pattern.test(visible($('detailPanel'))),'Failed/stale evidence must retain conservative result');noRaw($('detailPanel'),q);}
const unknown=structuredClone(p);unknown.criteria=[];unknown.runs=[];unknown.work.tasks=unknown.work.tasks.map(t=>({...t,state:'unknown',completed:false,technical_complete:false,criterion_ids:[],done_when:[],title:''}));
const missing=new Element('div');humanRenderResults(missing,unknown);assert(/미기록|미확인|확인되지/.test(visible(missing)),'Missing purpose cannot be fabricated');
const unsafe=structuredClone(p);unsafe.work.tasks[0].title='<img src=x onerror=alert(1)>';const safe=new Element('div');humanRenderResults(safe,unsafe);assert(safe.textContent.includes(unsafe.work.tasks[0].title));assert(!all(safe).some(n=>n.tagName==='img'));
assert.equal(JSON.stringify(model),before,'Question/result projection changed source identity or completion');
console.log('Readable results PASS: question/result/action, default selection, whole plan, review/unknown/failed/stale, closed raw, safe text, unchanged model');
'''

FRESHNESS = COMMON + r'''
const p=model.projects[0],before=JSON.stringify(model),c=p.criteria.find(c=>c.scope==='task'),base=p.runs.find(r=>r.criterion_id===c.id);assert(base);
for(const [name,mutate] of [
 ['signature mismatch',q=>{q.runs.find(r=>r.criterion_id===c.id).criterion_signature='0'.repeat(64);}],
 ['future execution',q=>{q.runs.find(r=>r.criterion_id===c.id).at='2099-01-01T00:00:00Z';}],
 ['conflicting executions',q=>{q.runs.push({...q.runs.find(r=>r.criterion_id===c.id),status:'fail',exit_code:1});}],
 ['unknown canonical execution',q=>{q.runs.find(r=>r.criterion_id===c.id).status='unknown';}]
]){const q=structuredClone(p);mutate(q);const box=new Element('div');humanRenderResults(box,q);const result=all(box).filter(n=>has(n,'human-result-card')&&n.dataset.checkTarget===c.target_id).find(n=>all(n).some(x=>x.tagName==='details'));assert(result);assert(!visible(result).includes('현재 버전 검사 통과'),name+' must not be presented as a current pass');assert(/미확인|미관측|확인되지|재검증|현재.*다시/.test(visible(result)),name+' must explain remaining verification');}
const q=structuredClone(p);q.work.tasks=q.work.tasks.map(t=>({...t,required:false,completed:false}));q.work.summary.required=0;q.work.summary.completed=0;q.status='complete';const summary=humanProjectSummary(q);assert(!visible(summary).includes('계획 작업 '+q.work.tasks.length+'개가 완료 조건을 충족하지 않았습니다.'),'Optional work must not inflate required remaining completion');assert(!/단계 종료 검사와 최종 인수 조건을 확인하세요/.test(visible(summary)),'Complete project cannot claim mandatory conditions remain');
assert.equal(JSON.stringify(model),before,'Freshness/optional projection modified model');
console.log('Readable freshness PASS: signature/future/conflict/unknown cannot become current pass; required versus optional and complete summaries');
'''

HISTORY = COMMON + r'''
const before=JSON.stringify(model);
for(const p of model.projects){navigate(p,{view:'evidence'});$('human-nav-sessions').click();const panel=$('detailPanel');assert.equal($('human-question-sessions').getAttribute('aria-pressed'),'true');for(const s of model.operations.sessions.filter(s=>s.project_id===p.id)){if(s.goal)assert(visible(panel).includes(s.goal));else assert(/목표.*미입력|목표.*미관측|목표.*미확인/.test(visible(panel)));assert(visible(panel).includes(lifeLabels[s.lifecycle]));assert(visible(panel).includes(completionLabels[s.completion]));assert(!visible(panel).includes(s.id),'Compound/internal session ID must be closed');assert(!visible(panel).includes(s.session_id),'Native session ID must be closed');assert(/다음|이어|연결 작업|보완/.test(visible(panel)));}assert(all(panel).some(n=>n.tagName==='details')||/기록 없음/.test(panel.textContent));
$('human-nav-documents').click();assert.equal($('human-question-documents').getAttribute('aria-pressed'),'true');const select=$('documentSelect');if(p.documents.length){assert(select);assert.equal(select.options.length,p.documents.length);for(let i=0;i<select.options.length;i++){select.value=String(i);select.onchange();const d=[...p.documents].sort((a,b)=>Date.parse(b.at)-Date.parse(a.at))[i];assert(visible(panel).includes(d.title));assert(visible(panel).includes(d.version));assert(panel.textContent.includes(d.content),'Document source remains accessible');assert(!visible(panel).includes(d.content),'Selected source text belongs in disclosure');}}assert(/실행|현재.*검증/.test(visible(panel)),'Documents cannot substitute for current checks');}
assert.equal(JSON.stringify(model),before,'History/documents modified immutable source model');
console.log('Readable history/documents PASS: goals, lifecycle versus completion, missing next evidence, raw identity disclosure, contextual dated documents, unchanged model');
'''

DOCUMENTARY = COMMON + r'''
const before=JSON.stringify(model),p=model.projects[0];navigate(p,{view:'evidence'});
const panel=$('detailPanel');assert.equal(activeTab,'work');assert(visible(panel).includes('문서'));assert(visible(panel).includes('2026-10-01'));
assert(/현재.*미확인/.test(visible(panel)),'Documentary completion must keep current execution unconfirmed');
assert(visible(panel).includes('Synthetic documented task'));assert(visible(panel).includes('Synthetic unknown task'));
const unknown=all(panel).find(n=>has(n,'human-result-card')&&n.textContent.includes('Synthetic unknown task'));assert(unknown);assert(/미확인|미기록|미지정|확인되지/.test(visible(unknown)));assert(!/검증 완료|검사 통과/.test(visible(unknown)),'Unknown documentary state cannot be promoted');
assert(links(panel).some(n=>n.href==='source-synthetic-source.html'),'Documentary source identity must remain available');
navigate(p,{phase:p.work.phases[0].id});assert(!/검증 완료/.test(visible($('detailPanel'))),'Documentary phase cannot become verified completion');assert(/문서/.test(visible($('detailPanel')))&&/미확인/.test(visible($('detailPanel'))));
const other=model.projects.find(q=>q.id!==p.id);navigate(other);navigate(p,{task:'doc-complete'});assert($('human-project-nav')&&!$('human-project-nav').hidden,'Document-only direct task needs project navigation');for(const a of links($('human-project-nav')))assert.equal(new URLSearchParams(a.href.slice(1)).get('project'),p.id,'Document-only task must not retain another project navigation');navigate(p,{view:'evidence'});
$('human-nav-sessions').click();assert(/기록 없음|미관측/.test(visible(panel)),'Documentary progress must not fabricate collected sessions');
assert.equal(JSON.stringify(model),before,'Documentary source cannot change current completion');
console.log('Readable documentary PASS: declared dated results, unknown not completed, current verification unconfirmed, source identity and no collection promotion');
'''


def main():
    visual.runtime(RESULTS)
    visual.runtime(FRESHNESS)
    visual.runtime(HISTORY)
    fixture = json.loads((ROOT / 'apps/dashboard/public/snapshot.json').read_text())
    p = fixture['projects'][0]
    documentary = {'projects': {p['id']: {'docdate': '2026-10-01', 'origin': 'synthetic-doc.md', 'tasks': {
        'doc-complete': {'id': 'doc-complete', 'title': 'Synthetic documented task', 'phase': p['work']['phases'][0]['id'], 'owner': 'Alice', 'status': 'documented', 'summary': 'Declared only in a document', 'next_action': '', 'source': 'synthetic-source', 'done': ['Synthetic documentary condition']},
        'doc-unknown': {'id': 'doc-unknown', 'title': 'Synthetic unknown task', 'phase': p['work']['phases'][1]['id'], 'status': 'unknown', 'summary': 'No current runner evidence', 'next_action': '', 'source': 'synthetic-source', 'done': []}}}},
        'sources': {'synthetic-source': {'project': p['id'], 'path': 'synthetic/doc.md', 'lines': [2, 8], 'sha256': 'synthetic', 'excerpt': 'Synthetic excerpt', 'checked_at': '2026-10-01'}}}
    visual.runtime(DOCUMENTARY, documentary)
    for relative in ['specs/ai-pms-human-projection/check_human_view.py',
                     'specs/ai-pms-rensei-experience/check_experience.py',
                     'specs/ai-pms-visual-management/check_visual.py',
                     'specs/ai-pms-toss-ia/check_ia.py',
                     'specs/ai-pms-action-detail/check_action_detail.py']:
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print('Readable project acceptance PASS: synthetic semantic regressions only; parent desktop Chrome acceptance separate, mobile excluded, no deployment/provider/model success.')


if __name__ == '__main__':
    main()
