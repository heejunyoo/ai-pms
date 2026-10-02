#!/usr/bin/env python3
"""Declared atomic plans with conservative imported verification evidence."""
import copy
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location('work_management',Path(__file__).with_name('management.py'))
management=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(management)
TASK_FIELDS={'id','title','phase_id','owner','required','depends_on','requirement_ids','done_when','criterion_ids','document_ids','review_required'}

def validate(p):
    m=p['management']; w=m['work']; h=management
    h.keys(w,('plan_id','plan_version','at','tasks','phase_gates','updates','reviews'),'work')
    h.ident(w['plan_id']); h.ident(w['plan_version']); h.time(w['at'])
    h.require((w['plan_id'],w['plan_version']) in {(r['id'],r['version']) for r in m['plans']},'work plan')
    tasks=h.records(w,'tasks',TASK_FIELDS); ids={t['id'] for t in tasks}; owners={r['actor_id'] for r in p['source_refs']}
    phases={r['id'] for r in p['phases']}; criteria={c['id']:c for c in p['criteria']}
    for t in tasks:
        h.text(t['title']); h.require(t['phase_id'] in phases,'task phase'); h.require(t['owner'] is None or t['owner'] in owners,'task owner')
        h.require(type(t['required']) is bool and type(t['review_required']) is bool,'task boolean')
        h.refs(t['depends_on'],ids); h.require(t['id'] not in t['depends_on'],'self dependency')
        h.refs(t['requirement_ids'],{r['id'] for r in m['requirements']}); h.refs(t['document_ids'],{r['id'] for r in p['documents']})
        h.require(bool(h.arr(t['done_when'])),'done when'); [h.text(x) for x in t['done_when']]
        h.refs(t['criterion_ids'],criteria)
        h.require(all(criteria[c]['scope']=='task' and criteria[c]['target_id']==t['id'] for c in t['criterion_ids']),'task criterion scope')
    h.require(all(c['scope']!='task' or c['target_id'] in ids for c in p['criteria']),'unknown task criterion')
    byid={t['id']:t for t in tasks}; pending={t['id']:len(t['depends_on']) for t in tasks}; children={tid:[] for tid in ids}
    for t in tasks:
        for dep in t['depends_on']:children[dep].append(t['id'])
    queue=[tid for tid in ids if pending[tid]==0]; visited=0
    while queue:
        tid=queue.pop();visited+=1
        for child in children[tid]:
            pending[child]-=1
            if pending[child]==0:queue.append(child)
    h.require(visited==len(ids),'dependency cycle')
    seen=set()
    for g in h.arr(w['phase_gates']):
        h.keys(g,('phase_id','criterion_ids'),'phase gate'); h.require(g['phase_id'] in phases and g['phase_id'] not in seen,'phase gate id');seen.add(g['phase_id']);h.refs(g['criterion_ids'],criteria)
        h.require(all(criteria[c]['scope']=='phase' and criteria[c]['target_id']==g['phase_id'] for c in g['criterion_ids']),'phase gate scope')
    for u in h.records(w,'updates',('id','task_id','at','state','summary','next_action')):
        h.require(u['task_id'] in ids and u['state'] in ('not_started','in_progress','blocked'),'update state');h.time(u['at']);h.text(u['summary']);h.text(u['next_action'])
    for r in h.records(w,'reviews',('id','task_id','at','reviewer','decision','summary','artifact_sha256','task_sha256')):
        h.require(r['task_id'] in ids and r['reviewer'] in owners and r['decision'] in ('approved','changes_requested'),'review');h.time(r['at']);h.text(r['summary']);h.sha(r['artifact_sha256']);h.sha(r['task_sha256'])
    return w

def task_digest(p,t):
    w=p['management']['work']; criteria={c['id']:c for c in p['criteria']}; latest={}
    for tp in p['management']['test_plans']:
        cid=tp['criterion_id']
        if cid in t['criterion_ids'] and (cid not in latest or management.time(tp['at'])>management.time(latest[cid]['at'])):latest[cid]=tp
    return management.digest(dict(plan_id=w['plan_id'],plan_version=w['plan_version'],at=w['at'],task=t,criteria=[criteria[c] for c in sorted(t['criterion_ids'])],test_plans=[latest[c] for c in sorted(latest)]))

def latest(records,fields,now):
    h=management
    rows=[r for r in records if h.time(r['at'])<=now]
    if not rows:return None,False
    at=max(h.time(r['at']) for r in rows); rows=sorted((r for r in rows if h.time(r['at'])==at),key=lambda r:r['id'])
    return copy.deepcopy(rows[0]),len({h.canonical({f:r[f] for f in fields}) for r in rows})>1

def check_state(p,observed,m,ids):
    h=management;w=p['management']['work'];now=h.time(observed) if isinstance(observed,str) else observed
    future=h.time(w['at'])>now;tps={(t['id'],t['version']):t for t in m['test_plans']}
    if future or not ids:return 'unknown'
    states=[]
    for cid in ids:
        rows=[a for a in m['attempts'] if tps[(a['test_plan_id'],a['test_plan_version'])]['criterion_id']==cid]
        a,conflict=latest(rows,('exit_code','criterion_signature','artifact_sha256','revision','provenance','test_plan_sha256'),now)
        if not a or conflict:states.append('unknown');continue
        current=a['revision']==p['current_revision'] and a['artifact_sha256']==m['artifact']['sha256'] and h.time(a['at'])>=max(h.time(w['at']),h.time(tps[(a['test_plan_id'],a['test_plan_version'])]['at']))
        if current and a['status']=='pass':states.append('complete')
        elif current and a['status']=='fail':states.append('failed')
        elif a['provenance']=='runner' and a['exit_code']==tps[(a['test_plan_id'],a['test_plan_version'])]['definition']['expected_exit_code']:states.append('revalidation')
        else:states.append('in_progress')
    return 'failed' if 'failed' in states else 'complete' if all(s=='complete' for s in states) else 'revalidation' if 'revalidation' in states else 'in_progress' if 'in_progress' in states else 'unknown'

def relevant_blockers(m,criterion_ids):
    tpmap={(t['id'],t['version']):t for t in m['test_plans']}
    attempts={a['id']:a for a in m['attempts']}
    return [b for b in m['blockers'] if (b['status']=='open' or b['verification']!='current') and any(tpmap[(attempts[aid]['test_plan_id'],attempts[aid]['test_plan_version'])]['criterion_id'] in criterion_ids for aid in b['attempt_ids'])]


def project_status(p,observed,m,view):
    gate=check_state(p,observed,m,[c['id'] for c in p['criteria'] if c['scope']=='project'])
    states={t['state'] for t in view['tasks']}|{ph['state'] for ph in view['phases']}
    if gate=='failed' or 'failed' in states:return 'failed'
    if gate=='revalidation' or 'revalidation' in states:return 'revalidation'
    if not view['summary']['required']:return 'unknown'
    if any(b['status']=='open' or b['verification']!='current' for b in m['blockers']):return 'in_progress'
    if all(ph['state']=='complete' for ph in view['phases']):return gate
    return 'in_progress'


def derive(p,observed,management_view=None):
    h=management;w=validate(p);now=h.time(observed) if isinstance(observed,str) else observed
    if management_view is None:_,management_view=h.derive(p,now)
    m=management_view; tps={(t['id'],t['version']):t for t in m['test_plans']}; future=h.time(w['at'])>now
    def latest_at(records,fields):return latest(records,fields,now)
    def checks(ids):return check_state(p,now,m,ids)
    tasks={}; interventions=[]
    def intervene(kind,t,summary,next_action,phase_id=None):
        interventions.append(dict(id=kind+'-'+(t['id'] if t else phase_id or 'plan'),kind=kind,task_id=t['id'] if t else None,phase_id=t['phase_id'] if t else phase_id,owner=t['owner'] if t else None,summary=summary,next_action=next_action))
    declared={t['id']:t for t in w['tasks']}
    reasons={'unknown':'담당자·완료 기준 또는 현재 계획 관측이 부족합니다.','not_started':'담당자가 아직 시작하지 않았다고 기록했습니다.','ready':'의존 작업이 충족되어 시작할 수 있습니다.','in_progress':'작업 진행 선언 또는 미완료 검사 근거가 있습니다.','blocked':'의존 작업 또는 명시적 막힘을 해결해야 합니다.','failed':'현재 작업 검사에 실패가 있습니다.','revalidation':'현재 계획·기준·산출물로 검사를 다시 실행해야 합니다.','review_pending':'현재 작업과 산출물에 대한 사람의 승인이 필요합니다.','changes_requested':'검토자가 수정을 요청했습니다.','complete':'현재 작업 검사·의존성·필요 승인이 충족되었습니다.'}
    def task(tid):
        if tid in tasks:return tasks[tid]
        t=declared[tid]; deps=[tasks[d] for d in t['depends_on']]; waiting=[d['id'] for d in deps if not d['completed']]
        u,uc=latest_at([r for r in w['updates'] if r['task_id']==tid],('state',));r,rc=latest_at([r for r in w['reviews'] if r['task_id']==tid],('decision','artifact_sha256','task_sha256'))
        check=checks(t['criterion_ids']); technical=check=='complete'; blockers=[b for b in m['blockers'] if (b['status']=='open' or b['verification']!='current') and any(tps[(a['test_plan_id'],a['test_plan_version'])]['criterion_id'] in t['criterion_ids'] for a in m['attempts'] if a['id'] in b['attempt_ids'])]
        if future or t['owner'] is None or not t['criterion_ids'] or uc:state='unknown'
        elif check=='failed':state='failed'
        elif blockers or u and u['state']=='blocked' or waiting:state='blocked'
        elif check=='revalidation':state='revalidation'
        elif technical:
            latest_tp=[tp for tp in m['test_plans'] if tp['criterion_id'] in t['criterion_ids']]
            fresh=r and not rc and r['task_sha256']==task_digest(p,t) and r['artifact_sha256']==m['artifact']['sha256'] and h.time(r['at'])>=max([h.time(w['at'])]+[h.time(tp['at']) for tp in latest_tp])
            state=('changes_requested' if fresh and r['decision']=='changes_requested' else 'complete' if fresh and r['decision']=='approved' else 'review_pending') if t['review_required'] else 'complete'
        else:state=u['state'] if u else 'in_progress' if check=='in_progress' else 'ready'
        out=dict(copy.deepcopy(t),state=state,reason=reasons[state],technical_complete=technical,completed=state=='complete',latest_update=u,latest_review=r,waiting_on=waiting);tasks[tid]=out
        if t['owner'] is None:intervene('missing_owner',t,'작업 담당자가 없습니다.','작업을 책임질 사람을 지정하세요.')
        if not t['criterion_ids']:intervene('missing_acceptance',t,'작업 완료 검사가 없습니다.','done_when을 확인하고 작업 범위 검사와 test plan을 등록하세요.')
        if state in ('blocked','failed','review_pending','changes_requested','revalidation'):
            kind='review' if state in ('review_pending','changes_requested') else state
            action=blockers[0]['next_action'] if blockers else u['next_action'] if u else {'blocked':'대기 중인 의존 작업을 완료하고 막힘을 해소하세요.','failed':'실패 검사 원인을 확인하고 수정 후 다시 실행하세요.','review':'현재 산출물과 작업 기준을 검토하고 승인 또는 수정 요청을 기록하세요.','revalidation':'현재 계획과 산출물로 작업 검사를 다시 실행하세요.'}[kind]
            intervene(kind,t,reasons[state],action)
        return out
    # ponytail: bounded topological batches scan O(n²) for long chains; use indegree queue if large plans need throughput.
    pending=set(declared)
    while pending:
        ready=[tid for tid in declared if tid in pending and all(d in tasks for d in declared[tid]['depends_on'])]
        for tid in ready:task(tid);pending.remove(tid)
    required=[tasks[t['id']] for t in w['tasks'] if t['required']]
    summary=dict(total=len(tasks),required=len(required),completed=sum(t['completed'] for t in required),technical_complete=sum(t['technical_complete'] for t in required),**{s:sum(t['state']==s for t in required) for s in ('blocked','failed','review_pending','ready','unknown','revalidation')})
    phases=[];gates={g['phase_id']:g['criterion_ids'] for g in w['phase_gates']}
    for phase in p['phases']:
        rows=[t for t in required if t['phase_id']==phase['id']]; gate=checks(gates.get(phase['id'],[]))
        if not rows or not gates.get(phase['id']) or future:state='unknown'
        elif relevant_blockers(m,gates.get(phase['id'],[])):state='blocked'
        elif all(t['completed'] for t in rows) and gate=='complete':state='complete'
        elif gate=='failed' or any(t['state']=='failed' for t in rows):state='failed'
        elif any(t['state']=='blocked' for t in rows):state='blocked'
        elif any(t['state'] in ('review_pending','changes_requested') for t in rows):state='review_pending'
        elif gate=='revalidation' or any(t['state']=='revalidation' for t in rows):state='revalidation'
        else:state='in_progress'
        phases.append(dict(id=phase['id'],name=phase['name'],state=state,required=len(rows),completed=sum(t['completed'] for t in rows),technical_complete=sum(t['technical_complete'] for t in rows),gate_state=gate))
        if not rows or gate!='complete':intervene('phase_gate',None,'Phase 완료 근거가 부족합니다.','필수 작업과 Phase exit 검사를 등록하고 현재 산출물로 실행하세요.',phase['id'])
    linked_criteria={cid for t in w['tasks'] for cid in t['criterion_ids']}
    for b in m['blockers']:
        if (b['status']=='open' or b['verification']!='current') and not any(tps[(a['test_plan_id'],a['test_plan_version'])]['criterion_id'] in linked_criteria for a in m['attempts'] if a['id'] in b['attempt_ids']):
            interventions.append(dict(id='blocked-'+b['id'],kind='blocked',task_id=None,phase_id=None,owner=None,summary=b['summary'],next_action=b['next_action']))
    if future:intervene('plan_unknown',None,'현재 시각보다 미래인 작업 계획입니다.','작업 계획 시각과 현재 관측 시각을 확인하세요.')
    return dict(plan_id=w['plan_id'],plan_version=w['plan_version'],at=w['at'],tasks=[tasks[t['id']] for t in w['tasks']],phases=phases,summary=summary,interventions=interventions)
