#!/usr/bin/env python3
"""Actual Python work projections and adversarial offline-import checks; browser QA separate."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[2]
DASH=ROOT/'specs/ai-pms-dashboard'
sys.path.insert(0,str(DASH))
import portfolio,management,work

def main():
    html=(DASH/'dashboard.html').read_text();script=html.split('<script>')[1].split('</script>')[0]
    assert '.innerHTML' not in script and 'eval(' not in script
    for token in ['peopleList','peopleScope','interventionList','tab-work','담당 필수 작업','프로젝트 전체','다음 행동:','완료 조건:','선행 작업:','runner 근거:','사람 승인 선언']:
        assert token in html,token
    catalog=json.loads((Path(__file__).parent/'sample/catalog-work.json').read_text());now='2026-10-02T12:00:00Z'
    fixtures=[portfolio.build_model(catalog=catalog,now=now)]
    assert sum('Alice' in p['owners'] for p in fixtures[0]['projects'])>=2
    assert any({'Alice','Bob'}<=set(p['owners']) for p in fixtures[0]['projects'])
    for mutation in ['future','declared','artifact','deps','optional','noowner','nogate','emptyphase','approval','staleapproval','changes','conflictupdate','conflictreview','newunknown','newfailure','oldreceipt','microtime','unlinkedblocker']:
        c=copy.deepcopy(catalog);p=c['projects'][0];m=p['management'];w=m['work'];t=w['tasks'][1]
        if mutation=='future':w['at']='2026-10-03T00:00:00Z'
        if mutation=='declared':
            for a in m['attempts']:a['provenance']='declared'
        if mutation=='artifact':
            m['artifact']['files'][0]['sha256']='1'*64;m['artifact']['sha256']=management.artifact_sha256(m['artifact']['files'])
        if mutation=='deps':w['tasks'][0]['depends_on']=[w['tasks'][2]['id']]
        if mutation=='optional':
            for task in w['tasks']:task['required']=False
        if mutation=='noowner':
            for task in w['tasks']:task['owner']=None
        if mutation=='nogate':w['phase_gates']=[]
        if mutation=='emptyphase':p['phases'].append(dict(id='futurephase',name='후속 단계'))
        if mutation in ['approval','staleapproval','changes','conflictreview']:
            r=dict(id='review-one',task_id=t['id'],at='2026-09-29T05:00:00Z',reviewer='Bob',decision='approved',summary='합성 인수 검토 선언',artifact_sha256=m['artifact']['sha256'],task_sha256=work.task_digest(p,t));w['reviews']=[r]
            if mutation=='staleapproval':t['done_when'].append('변경된 인수 조건')
            if mutation=='changes':r['decision']='changes_requested'
            if mutation=='conflictreview':w['reviews'].append(dict(r,id='review-two',decision='changes_requested'))
        if mutation=='conflictupdate':w['updates'].append(dict(w['updates'][0],id='conflict',state='in_progress'))
        if mutation in ['newunknown','newfailure','oldreceipt','microtime','unlinkedblocker']:
            a=copy.deepcopy(m['attempts'][0]);a['id']='new-observation';a['at']=a['started_at']='2026-09-29T06:00:00Z';m['attempts'].append(a)
            if mutation=='newunknown':a['provenance']='declared'
            if mutation=='newfailure':a['exit_code']=1
            if mutation=='oldreceipt':w['at']='2026-09-29T07:00:00Z'
            if mutation=='microtime':a['at']=a['started_at']='2026-09-29T04:00:00.000001Z';a['exit_code']=1
        if mutation=='unlinkedblocker':m['blockers'].append(dict(id='project-help',status='open',summary='프로젝트 공통 담당자 판단',cause_state='hypothesis',cause='정책 결정 필요',attempt_ids=[],owner='Alice',next_action='공통 정책을 확인하세요.',resolved_by=None))
        fixtures.append(portfolio.build_model(catalog=c,now=now))
    # Independent-review regressions: upper gates and Python/JS identifier ordering.
    for mutation in ('projectdeclared','projectblocker','phaseblocker','asciiupdates','asciireviews'):
        c=copy.deepcopy(catalog);p=c['projects'][0];m=p['management'];w=m['work']
        w['tasks']=w['tasks'][:1];w['updates']=[];keep={'action-1-check','phase-exit','project-exit'}
        p['phases']=[ph for ph in p['phases'] if ph['id']==w['tasks'][0]['phase_id']];p['current_phase']=p['phases'][0]['id'];w['phase_gates']=[g for g in w['phase_gates'] if g['phase_id']==p['phases'][0]['id']]
        p['documents']=[d for d in p['documents'] if d['phase_id']==p['current_phase']]
        p['criteria']=[x for x in p['criteria'] if x['id'] in keep];m['test_plans']=[x for x in m['test_plans'] if x['criterion_id'] in keep]
        tpids={x['id'] for x in m['test_plans']};m['attempts']=[x for x in m['attempts'] if x['test_plan_id'] in tpids]
        if mutation=='projectdeclared':
            tp=next(x for x in m['test_plans'] if x['criterion_id']=='project-exit');a=copy.deepcopy(next(x for x in m['attempts'] if x['test_plan_id']==tp['id']));a.update(id='new-project-declared',at='2026-09-29T06:00:00Z',started_at='2026-09-29T06:00:00Z',provenance='declared',exit_code=None);m['attempts'].append(a)
        if mutation in ('projectblocker','phaseblocker'):
            tp=next(x for x in m['test_plans'] if x['definition']['scope']==('phase' if mutation=='phaseblocker' else 'project'));a=next(x for x in m['attempts'] if x['test_plan_id']==tp['id']);m['blockers'].append(dict(id='upper-help',status='open',summary='상위 판단 대기',cause_state='hypothesis',cause='정책 결정 필요',attempt_ids=[a['id']],owner='Alice',next_action='공통 정책을 확인하세요.',resolved_by=None))
        if mutation=='asciiupdates':w['updates']=[dict(id=key,task_id='action-1',at='2026-09-29T06:00:00Z',state='in_progress',summary='같은 상태 다른 ID '+key,next_action='진행 설명 확인') for key in ('A','a')]
        if mutation=='asciireviews':
            t=w['tasks'][0];t['review_required']=True;w['reviews']=[dict(id=key,task_id=t['id'],at='2026-09-29T06:00:00Z',reviewer='Alice',decision='approved',summary='동일 판단 다른 ID '+key,artifact_sha256=m['artifact']['sha256'],task_sha256=work.task_digest(p,t)) for key in ('A','a')]
        fixtures.append(portfolio.build_model(catalog=c,now=now))
    bad=[]
    def malformed(edit):
        model=copy.deepcopy(fixtures[0]);edit(model['projects'][0]);bad.append(model)
    malformed(lambda p:p['work']['summary'].update(completed=999))
    malformed(lambda p:p['work']['tasks'][2].update(state='complete',completed=True))
    malformed(lambda p:p['work']['phases'][1].update(state='complete'))
    malformed(lambda p:p.update(status='complete'))
    malformed(lambda p:p.update(status_reason='forged completion reason'))
    malformed(lambda p:p['work']['tasks'][1].update(latest_review=dict(decision='approved')))
    malformed(lambda p:p['management']['work'].update(reviews=[dict(id='forged',task_id='action-2',at='2026-09-29T05:00:00Z',reviewer='Unknown',decision='approved',summary='Invalid reviewer',artifact_sha256='1'*64,task_sha256='1'*64)]))
    malformed(lambda p:p['work']['interventions'][0].update(owner='Bob'))
    malformed(lambda p:p['management']['work']['tasks'][0].update(owner='Unknown'))
    malformed(lambda p:p['management']['work']['tasks'][0].update(required=1))
    malformed(lambda p:p['management']['work']['tasks'][0].update(depends_on=[p['management']['work']['tasks'][0]['id']]))
    malformed(lambda p:p['management']['work']['tasks'][0].update(done_when=[]))
    malformed(lambda p:p['management']['work']['tasks'][0].update(title='token=unsafe'))
    malformed(lambda p:p['management']['work']['tasks'][0].update(criterion_ids=['phase-exit']))
    malformed(lambda p:p['management']['work']['tasks'][0].update(document_ids=['missing']))
    malformed(lambda p:p['management']['work']['phase_gates'][0].update(criterion_ids=['action-1-check']))
    malformed(lambda p:p['management']['work']['updates'][0].update(state='complete'))
    malformed(lambda p:p['management']['work']['tasks'].append(copy.deepcopy(p['management']['work']['tasks'][0])))
    malformed(lambda p:p['management']['work'].update(extra='forged'))
    malformed(lambda p:p['work'].update(extra='forged'))
    for index in [1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17]:
        model=copy.deepcopy(fixtures[index]);model['projects'][0]['status']='complete';bad.append(model)
    js=script[:script.index('function el(')]+'\nconst assert=require("node:assert/strict");\n'
    js+='const fixtures='+json.dumps(fixtures)+';const bad='+json.dumps(bad)+';\n'
    js+='for(const [i,m] of fixtures.entries()){try{validateModel(m);}catch(e){e.message="fixture "+i+": "+e.message;throw e;}}for(const m of bad)assert.throws(()=>validateModel(m));\n'
    js+='let model=fixtures[0],activeTab="work",selectedDocument="",renders=0;function renderPortfolio(){renders++;}function renderDetail(){renders++;}global.document={getElementById:()=>({textContent:""})};\n'
    js+=script[script.index('function applySnapshot('):script.index('function importError(')]
    js+='for(const m of bad){assert.throws(()=>applySnapshot(JSON.stringify(m)));assert.strictEqual(model,fixtures[0]);}assert.equal(renders,0);\n'
    js+=script[script.index('function assignedTasks('):script.index('function renderPeople(')]
    js+='const shared=fixtures[0].projects[0];assert.equal(assignedTasks(shared,"Bob").length,1);assert.equal(assignedTasks(shared,"Alice").length,5);assert.equal(assignedTasks(shared,"").length,7);\n'
    js+='console.log("Work UI parity: "+fixtures.length+" Python snapshots, "+bad.length+" forged imports rejected, owner counts and prior-state preservation PASS");\n'
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'work-ui.js';path.write_text(js);subprocess.run(['node',str(path)],check=True)
    subprocess.run([sys.executable,str(ROOT/'specs/ai-pms-management/check_ui_v3.py')],check=True)
    print('Work UI contract and adversarial parity PASS; actual browser/mobile acceptance belongs to parent')
if __name__=='__main__':main()
