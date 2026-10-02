#!/usr/bin/env python3
"""Deterministic public SYNTHETIC examples, never real provider executions."""
import copy
import importlib.util
import json
from pathlib import Path
import uuid
ROOT=Path(__file__).resolve().parent.parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
base=load('live_base_sample',ROOT/'ai-pms-work-management/generate_sample.py')
operations=load('live_operations',ROOT/'ai-pms-dashboard/operations.py')
NOW='2026-10-02T12:00:00Z'

def make_sample():
    catalog=base.make_catalog(multiple_phases=True)
    store={'version':1,'sources':{}};sessions=[]
    template=json.loads((ROOT/'ai-pms-dashboard/sample/central.json').read_text())
    original=next(iter(next(iter(template['sources'].values()))['events'].values()))['event']
    def event(ref,sid,source,kind,at,native):
        source_key=operations.helpers().central.source_key(ref)
        entry=store['sources'].setdefault(source_key,dict(ref,label=ref['actor_id']+' 합성 예시',evidence_mode='synthetic',events={}))
        eid=str(uuid.uuid5(uuid.NAMESPACE_URL,json.dumps([ref,sid,source,kind,at],sort_keys=True)))
        e=copy.deepcopy(original);e.update(event_id=eid,observed_at=at,occurred_at=None,source=source,native_event=native,kind=kind,project_id=ref['project_id'],session_id=sid)
        entry['events'][eid]=dict(event=e,received_at=at,file_sha256='a'*64,line=len(entry['events'])+1)
        return eid
    for index,p in enumerate(catalog['projects']):
        ref=p['source_refs'][0];sid='same-native-session' if index in (0,len(catalog['projects'])-1) else 'session-'+str(index)
        task=p['management']['work']['tasks'][0]
        s=dict(id='goal-'+str(index),project_id=p['id'],source_project_id=ref['project_id'],actor_id=ref['actor_id'],environment_id=ref['environment_id'],source='codex',session_id=sid,goal='합성 목표: '+task['title'],goal_version='v1',project_revision=p['current_revision'],task_ids=[task['id']],acceptance=None)
        event(ref,sid,'codex','session.start','2026-10-02T11:00:00Z','SessionStart')
        event(ref,sid,'codex','turn.stopped','2026-10-02T11:05:00Z','Stop')
        if index==1:event(ref,sid,'codex','session.end','2026-10-02T11:10:00Z','SessionEnd')
        if index==0:s['acceptance']=dict(goal_version='v1',goal_sha256=operations.goal_digest(s),verification_sha256='0'*64,decision='accepted',actor_id=ref['actor_id'],at='2026-10-02T11:30:00Z')
        sessions.append(s)
    shared=catalog['projects'][0];bob=next(r for r in shared['source_refs'] if r['actor_id']=='Bob')
    event(bob,'unlinked-goal','claude','session.start','2026-10-02T11:40:00Z','SessionStart')
    stars=[]
    for sid,scope in [('company-quality','company'),('team-usage','team')]:
        stars.append(dict(id=sid,scope=scope,scope_id='sample-'+scope,name='합성 '+scope+' 북극성',metric='근거 확인 사용자',unit='명',period_start='2026-10-01T00:00:00Z',period_end='2026-10-31T23:59:59Z',baseline=10,target=30,direction='increase',owner='Alice',observations=[dict(id='measured',at='2026-10-02T11:00:00Z',value=20,evidence='합성 사업 관측; 실제 측정 아님',provenance='measured'),dict(id='declared',at='2026-10-02T11:50:00Z',value=100,evidence='합성 담당자 선언',provenance='declared')]))
    contributions=[]
    for i,status in enumerate(('proposed','confirmed')):
        contributions.append(dict(id='link-'+str(i),session_record_id=sessions[0]['id'],north_star_id=stars[i]['id'],status=status,rationale='합성 기여 연결; 인과 증명 아님',evidence='합성 검토 메모',confirmed_by='Alice' if status=='confirmed' else None,goal_sha256=operations.goal_digest(sessions[0]),north_star_sha256=operations.north_star_digest(stars[i]),at='2026-10-02T11:30:00Z'))
    ref=shared['source_refs'][0];source=store['sources'][operations.helpers().central.source_key(ref)]
    capture=[dict(id='capture-alice',project_id=ref['project_id'],actor_id=ref['actor_id'],environment_id=ref['environment_id'],source='codex',last_event_id=next(iter(source['events'])),last_recorded_at='2026-10-02T11:59:30Z',errors=0,last_failure_at=None,status='observed',at='2026-10-02T11:59:30Z')]
    projected=operations.helpers().build_model(store,catalog,NOW)
    sessions[0]['acceptance']['verification_sha256']=operations.verification_digest(sessions[0],projected['projects'][0])
    return catalog,store,dict(version=1,sessions=sessions,north_stars=stars,contributions=contributions,capture=capture)

if __name__=='__main__':
    out=Path(__file__).parent/'sample';out.mkdir(exist_ok=True)
    for filename,value in zip(('catalog.json','central.json','operations.json'),make_sample()):
        (out/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print('synthetic live sample generated; generated_at='+NOW)
