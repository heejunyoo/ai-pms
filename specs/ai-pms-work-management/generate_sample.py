#!/usr/bin/env python3
"""Public synthetic examples only; runner records below are illustrative mocks."""
import copy
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('base_sample',ROOT/'ai-pms-management/generate_sample.py'); base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
m=base.management;work=m.work_module()
NOW='2026-10-02T12:00:00Z'

def make_catalog(multiple_phases=False):
    catalog=base.make_catalog()
    # One shared project plus Alice's separate project; existing owners remain explicit participants.
    p=catalog['projects'][0]; p['source_refs'].append(dict(actor_id='Bob',environment_id='bob-work',project_id='77777777-7777-4777-8777-777777777777'))
    second=copy.deepcopy(p);second['id']='alice-personal';second['name']='Alice 개인 자료 정리 · 합성 예시';second['goal']='여러 자료에서 찾아낸 근거를 다시 확인할 수 있게 정리한다';second['source_refs']=[dict(actor_id='Alice',environment_id='alice-personal',project_id='88888888-8888-4888-8888-888888888888')];second['documents']=[];second['connections']=[];second['management']['assignment']=None;second['management']['objectives']=[dict(second['management']['objectives'][0],kind='personal',parent_id=None,title=second['goal'],success_condition='자료 정리 결과를 확인한다',source='합성 Alice 개인 목표 노트')];catalog['projects'].append(second)
    patterns=[['complete','review','blocked','ready','in_progress','missing_owner','missing_acceptance'],['failed'],['revalidation'],['ready'],['in_progress']]
    for index,p in enumerate(catalog['projects']):
        owner=p['source_refs'][0]['actor_id']; env=p['source_refs'][0]['environment_id'];mg=p['management'];mg['traceability']={'checkpoints':[],'decisions':[],'handoffs':[],'capture':[]};mg['blockers']=[];mg['attempts']=[];mg['improvements']=[];mg['test_plans']=[];p['criteria']=[]
        phase=p['phases'][0]['id'] if p['phases'] else 'build';p['phases']=[dict(id=phase,name='구현과 검증')];p['current_phase']=phase
        for doc in p['documents']:doc['phase_id']=phase
        plan=mg['plans'][0];at='2026-09-29T01:00:00Z'; tasks=[];updates=[]
        def criterion(cid,scope,target):
            c=dict(id=cid,label='합성 기술 검사 · '+cid,scope=scope,target_id=target,command='python3 synthetic-test.py',expected_exit_code=0);p['criteria'].append(c)
            tp=dict(id='test-'+cid,version='v1',plan_id=plan['id'],plan_version=plan['version'],criterion_id=cid,requirement_ids=['req-core'],reason='합성 작업 기준을 확인',excluded='실제 실행·업무 성과는 미관측',at='2026-09-29T02:00:00Z',definition=copy.deepcopy(c),test_files=copy.deepcopy(mg['artifact']['files']));mg['test_plans'].append(tp);return tp
        def attempt(tp,state):
            at='2026-09-29T04:00:00Z';mg['attempts'].append(dict(id='mock-'+tp['criterion_id'],test_plan_id=tp['id'],test_plan_version=tp['version'],test_plan_sha256=m.test_plan_sha256(tp),criterion_signature=m.criterion_signature(tp['definition']),revision=p['current_revision'],artifact_sha256='0'*64 if state=='revalidation' else mg['artifact']['sha256'],command=tp['definition']['command'],started_at=at,at=at,exit_code=1 if state=='failed' else 0,actor_id=owner,environment_id=env,session_id='synthetic-work',environment='mock',runner='synthetic-example',summary='합성 예시; 실제 subprocess 실행 영수증 아님',provenance='runner'))
        for n,state in enumerate(patterns[index%len(patterns)]):
            tid='action-'+str(n+1);task_owner='Bob' if index==0 and state=='blocked' else None if state=='missing_owner' else owner
            t=dict(id=tid,title={'complete':'출처 누락 응답 차단','review':'인수 조건과 산출물 검토','blocked':'담당자와 중복 처리 정책 결정','ready':'문서 근거 확인 검사 추가','in_progress':'자료 연결 구현','missing_owner':'후속 책임자 지정','missing_acceptance':'자료 완료 기준 합의','failed':'실패 입력 처리 수정','revalidation':'변경 산출물 재검증'}[state],phase_id=phase,owner=task_owner,required=True,depends_on=[],requirement_ids=['req-core'],done_when=['선언된 기술 인수 조건의 검사 근거를 남긴다'],criterion_ids=[] if state=='missing_acceptance' else [tid+'-check'],document_ids=[],review_required=state=='review');tasks.append(t)
            if t['criterion_ids']:
                tp=criterion(t['criterion_ids'][0],'task',tid)
                if state in ('complete','review','failed','revalidation'):attempt(tp,state)
            if state in ('blocked','in_progress'):
                updates.append(dict(id='update-'+tid,task_id=tid,at='2026-09-29T03:00:00Z',state=state,summary='합성 담당자 진행 선언',next_action='중복 요청의 우선 처리 정책을 담당자와 결정하세요.' if state=='blocked' else '자료 연결 구현을 마치고 현재 작업 검사를 실행하세요.'))
        gate=criterion('phase-exit','phase',phase);attempt(gate,'complete');overall=criterion('project-exit','project',p['id']);attempt(overall,'complete')
        mg['work']=dict(plan_id=plan['id'],plan_version=plan['version'],at=at,tasks=tasks,phase_gates=[dict(phase_id=phase,criterion_ids=['phase-exit'])],updates=updates,reviews=[])
        m.validate(p)
    if multiple_phases:
        p=catalog['projects'][0];mg=p['management'];w=mg['work'];build='build'
        p['phases']=[dict(id='plan',name='목표와 인수 기준 확정'),dict(id=build,name='구현과 검증'),dict(id='release',name='인수와 후속 책임')]
        p['current_phase']=build
        for t in w['tasks']:t['phase_id']=build
        w['tasks'][0]['phase_id']='plan';w['tasks'][0]['title']='출처 검증 인수 기준 확정'
        for t in w['tasks']:
            if t['id'] in ('action-2','action-6','action-7'):t['phase_id']='release'
        conditions=['출처 없는 답변을 차단하는 인수 기준을 문서에 확정한다','현재 출처 표시 화면과 결과물을 사람이 검토한다','중복 요청의 우선 처리 정책을 담당자와 결정한다','출처가 있는 답변과 없는 답변의 검사 결과를 확인한다','자료에서 찾아낸 근거와 답변의 연결을 구현한다','후속 관리를 책임질 담당자를 정한다','회사 목표에 맞는 업무 성과 평가 기준을 합의한다']
        for t,condition in zip(w['tasks'],conditions):t['done_when']=[condition]
        for doc in p['documents']:doc['phase_id']='plan' if doc['kind'] in ('requirements','design') else build
        w['tasks'][0]['document_ids']=list(dict.fromkeys(d['id'] for d in p['documents'] if d['phase_id']=='plan'))
        w['tasks'][4]['document_ids']=list(dict.fromkeys(d['id'] for d in p['documents'] if d['phase_id']==build))
        gate=next(c for c in p['criteria'] if c['id']=='phase-exit');gate['target_id']='plan'
        tp=next(tp for tp in mg['test_plans'] if tp['criterion_id']=='phase-exit');tp['definition']=copy.deepcopy(gate)
        a=next(a for a in mg['attempts'] if a['test_plan_id']==tp['id']);a['test_plan_sha256']=m.test_plan_sha256(tp);a['criterion_signature']=m.criterion_signature(gate)
        w['phase_gates'][0]['phase_id']='plan'
        for phase_id in (build,'release'):
            c=dict(gate,id='phase-exit-'+phase_id,target_id=phase_id);p['criteria'].append(c)
            t=copy.deepcopy(tp);t.update(id='test-'+c['id'],criterion_id=c['id'],definition=copy.deepcopy(c));mg['test_plans'].append(t)
            a=copy.deepcopy(a);a.update(id='mock-'+c['id'],test_plan_id=t['id'],test_plan_sha256=m.test_plan_sha256(t),criterion_signature=m.criterion_signature(c));mg['attempts'].append(a)
            w['phase_gates'].append(dict(phase_id=phase_id,criterion_ids=[c['id']]))
        m.validate(p)
    return catalog

if __name__=='__main__':
    out=Path(__file__).parent/'sample/catalog-work.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(make_catalog(multiple_phases=True),ensure_ascii=False,indent=2)+'\n');print('synthetic work catalog generated')
