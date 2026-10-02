#!/usr/bin/env python3
"""Explicit session goals and measured north stars; native events never prove goals."""
import copy
import datetime as dt
import hashlib
import importlib.util
from pathlib import Path
import re
import sys

SESSION_FIELDS = {'id','project_id','source_project_id','actor_id','environment_id','source','session_id','goal','goal_version','project_revision','task_ids','acceptance'}
GOAL_FIELDS = SESSION_FIELDS - {'acceptance'}
STAR_FIELDS = {'id','scope','scope_id','name','metric','unit','period_start','period_end','baseline','target','direction','owner','observations'}
CONTRIBUTION_FIELDS = {'id','session_record_id','north_star_id','status','rationale','evidence','confirmed_by','goal_sha256','north_star_sha256','at'}
CAPTURE_FIELDS = {'id','project_id','actor_id','environment_id','source','last_event_id','last_recorded_at','errors','last_failure_at','status','at'}
SOURCES = {'codex','claude','cursor','gemini','unknown'}
SAFE_INTEGER = 9007199254740991
_helpers = None


def helpers():
    global _helpers
    if _helpers is None:
        name = 'operations_portfolio_helpers'
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name('portfolio.py'))
        _helpers = importlib.util.module_from_spec(spec)
        sys.modules[name] = _helpers
        spec.loader.exec_module(_helpers)
    return _helpers


def digest(value):
    return hashlib.sha256(helpers().canonical(value).encode()).hexdigest()


def goal_digest(session):
    return digest({k: session[k] for k in sorted(GOAL_FIELDS)})


def north_star_digest(star):
    return digest({k: star[k] for k in sorted(STAR_FIELDS - {'observations'})})


def verification_digest(session, project):
    h = helpers()
    h.require(session['project_id'] == project['id'], 'verification project reference')
    management = project.get('management') or {}
    raw = {k: copy.deepcopy(management.get(k)) for k in ('artifact','plans','test_plans','attempts','blockers','work')}
    for field, derived in (('test_plans', ('criterion_signature','test_plan_sha256')), ('attempts', ('status',)), ('blockers', ('verification',))):
        for row in raw[field] or []:
            for key in derived:
                row.pop(key, None)
    return digest(dict(project_id=project['id'], current_revision=project['current_revision'], criteria=project['criteria'], management=raw))


def identity(s):
    return tuple(s[k] for k in ('project_id','source_project_id','actor_id','environment_id','source','session_id'))


def validate(records, projects):
    h = helpers()
    h.validate_tree(records)
    h.require(len(h.canonical(records).encode()) <= h.MAX_FILE, 'operations file limit')
    h.keys(records, ('version','sessions','north_stars','contributions','capture'), 'operations')
    h.require(type(records['version']) is int and records['version'] == 1, 'operations version')
    def numeric_tree(v):
        if type(v) is int: h.require(abs(v) <= SAFE_INTEGER, 'safe integer')
        elif isinstance(v, dict):
            for x in v.values(): numeric_tree(x)
        elif isinstance(v, list):
            for x in v: numeric_tree(x)
    numeric_tree(records)
    def rows(field, fields):
        values = h.array(records[field])
        for r in values: h.keys(r, fields, field); h.ident(r['id'])
        h.unique(values)
        return values
    def sha(v): h.require(isinstance(v,str) and re.fullmatch('[a-f0-9]{64}',v), 'digest')
    ps = {p['id']:p for p in projects}
    sessions = rows('sessions', SESSION_FIELDS)
    h.require(len({identity(s) for s in sessions}) == len(sessions), 'duplicate native session identity')
    for s in sessions:
        for k in ('project_id','actor_id','environment_id','session_id','goal_version','project_revision'): h.ident(s[k])
        h.require(s['project_id'] in ps, 'session project')
        h.require(h.central.uid(s['source_project_id']) and s['source'] in SOURCES, 'session source')
        p=ps[s['project_id']]
        h.require(any((r['actor_id'],r['environment_id'],r['project_id']) == (s['actor_id'],s['environment_id'],s['source_project_id']) for r in p['sources']), 'session exact source reference')
        h.text(s['goal'], nonempty=False)
        tasks={t['id']:t for t in (p.get('work') or {}).get('tasks',[])}
        ids=h.array(s['task_ids']); h.require(len(ids)==len(set(ids)), 'duplicate task')
        for tid in ids:
            h.ident(tid); h.require(tid in tasks and tasks[tid]['owner'] in (None,s['actor_id']), 'task ownership/reference')
        a=s['acceptance']
        if a is not None:
            h.keys(a, ('goal_version','goal_sha256','verification_sha256','decision','actor_id','at'),'acceptance')
            h.ident(a['goal_version']); h.ident(a['actor_id']); sha(a['goal_sha256']); sha(a['verification_sha256']); h.time(a['at'])
            h.require(a['decision'] in ('accepted','rejected') and a['actor_id'] in p['owners'], 'acceptance actor/decision')
    stars=rows('north_stars',STAR_FIELDS)
    for s in stars:
        for k in ('scope_id','owner'): h.ident(s[k])
        for k in ('name','metric','unit'): h.text(s[k])
        h.require(s['scope'] in ('company','team') and s['direction'] in ('increase','decrease'), 'north star scope/direction')
        h.require(h.time(s['period_start'])<=h.time(s['period_end']), 'metric period')
        h.require(type(s['baseline']) is int and type(s['target']) is int, 'integer metric')
        obs=h.array(s['observations'])
        for o in obs:
            h.keys(o, ('id','at','value','evidence','provenance'),'observation'); h.ident(o['id']); h.time(o['at']);h.text(o['evidence'])
            h.require(type(o['value']) is int and o['provenance'] in ('measured','declared'),'measured integer')
        h.unique(obs)
    for c in rows('contributions', CONTRIBUTION_FIELDS):
        h.require(c['session_record_id'] in {s['id'] for s in sessions} and c['north_star_id'] in {s['id'] for s in stars},'contribution reference')
        h.require(c['status'] in ('proposed','confirmed'),'contribution status')
        h.text(c['rationale']);h.text(c['evidence']);h.time(c['at']);sha(c['goal_sha256']);sha(c['north_star_sha256'])
        h.require(c['confirmed_by'] is None if c['status']=='proposed' else h.central.identifier(c['confirmed_by']), 'contribution confirmation')
    for c in rows('capture',CAPTURE_FIELDS):
        for k in ('actor_id','environment_id'):h.ident(c[k])
        h.require(h.central.uid(c['project_id']) and c['source'] in SOURCES,'capture source')
        h.require(c['last_event_id'] is None or h.central.uid(c['last_event_id']), 'capture event UUID')
        for k in ('last_recorded_at','last_failure_at','at'):
            if c[k] is not None:h.time(c[k])
        h.require(type(c['errors']) is int and c['errors']>=0 and c['status'] in ('observed','degraded','unknown'),'capture status')
    return records


def derive(records, projects, store, now):
    h=helpers();validate(records,projects)
    now=h.time(now) if isinstance(now,str) else now
    h.require(isinstance(now,dt.datetime) and now.utcoffset()==dt.timedelta(0),'current UTC time')
    ps={p['id']:p for p in projects}; event_groups={}
    for p in projects:
        for ref in p['sources']:
            source=store['sources'].get(h.central.source_key({k:ref[k] for k in ('actor_id','environment_id','project_id')}))
            for r in (source or {}).get('events',{}).values():
                e=r['event'];at=e['occurred_at'] or e['observed_at']
                if not e['session_id'] or h.time(at)>now:continue
                key=(p['id'],ref['project_id'],ref['actor_id'],ref['environment_id'],e['source'],e['session_id'])
                event_groups.setdefault(key,[]).append((at,e))
    rows=copy.deepcopy(records['sessions']); known={identity(s) for s in rows}
    for key in sorted(set(event_groups)-known):
        pid,raw,actor,env,source,sid=key
        rows.append(dict(id='auto-'+digest(list(key))[:32],project_id=pid,source_project_id=raw,actor_id=actor,environment_id=env,source=source,session_id=sid,goal='',goal_version='unknown',project_revision=ps[pid]['current_revision'],task_ids=[],acceptance=None))
    sessions=[]
    for s in sorted(rows,key=lambda s:(s['actor_id'],s['project_id'],s['environment_id'],s['source_project_id'],s['source'],s['session_id'],s['id'])):
        events=sorted(event_groups.get(identity(s),[]),key=lambda x:(h.time(x[0]),x[1]['event_id']))
        starts=[at for at,e in events if e['kind']=='session.start'];ends=[at for at,e in events if e['kind']=='session.end']
        start=max(starts,key=h.time,default=None);end=max(ends,key=h.time,default=None)
        lifecycle='ended' if end and (not start or h.time(end)>=h.time(start)) else 'active' if events and (not start or any(h.time(at)>=h.time(start) and e['kind']!='session.start' for at,e in events)) else 'started' if start else 'unknown'
        tasks={t['id']:t for t in (ps[s['project_id']].get('work') or {}).get('tasks',[])}
        linked=[tasks[t] for t in s['task_ids']];states={t['state'] for t in linked}
        if not s['goal'].strip() or not linked:completion='unknown'
        elif s['project_revision']!=ps[s['project_id']]['current_revision']:completion='revalidation'
        elif 'failed' in states:completion='failed'
        elif 'revalidation' in states:completion='revalidation'
        elif all(t['completed'] for t in linked):completion='verified'
        elif states=={'unknown'}:completion='unknown'
        else:completion='in_progress'
        a=s['acceptance'];valid=a and a['goal_version']==s['goal_version'] and a['goal_sha256']==goal_digest(s) and a['verification_sha256']==verification_digest(s, ps[s['project_id']]) and h.time(a['at'])<=now
        if valid and (completion=='verified' or completion=='in_progress' and a['decision']=='rejected'):completion=a['decision']
        reason={'unknown':'목표 또는 연결 작업의 현재 검증 근거가 없습니다.','revalidation':'현재 revision·작업·산출물로 재검증이 필요합니다.','failed':'연결된 현재 작업 검사가 실패했습니다.','in_progress':'연결 작업의 검사·막힘·사람 검토가 충족되지 않았습니다.','verified':'연결 작업의 현재 완료 근거를 확인했습니다. 목표 적절성은 사람 판단입니다.','accepted':'현재 목표 정의에 대한 인수 선언과 연결 작업 검증을 확인했습니다.','rejected':'현재 목표 정의에 대한 거절 선언이 있습니다.'}[completion]
        if lifecycle=='active' and not start:reason+=' 활동은 관측했으나 시작·종료는 불명입니다.'
        if a and not valid:reason+=' 이전·변경·미래 목표 인수 선언은 무효입니다.'
        sessions.append(dict(s,lifecycle=lifecycle,last_activity_at=events[-1][0] if events else None,started_at=start,ended_at=end,completion=completion,reason=reason,event_ids=[e['event_id'] for _,e in events]))
    people=[]
    for actor in sorted({s['actor_id'] for s in sessions}):
        own=[s for s in sessions if s['actor_id']==actor]
        people.append(dict(actor_id=actor,session_ids=[s['id'] for s in own],project_ids=sorted({s['project_id'] for s in own}),attention_session_ids=[s['id'] for s in own if s['completion'] not in ('verified','accepted')]))
    stars=[]
    for s in sorted(records['north_stars'],key=lambda r:r['id']):
        candidates=[o for o in s['observations'] if o['provenance']=='measured' and h.time(s['period_start'])<=h.time(o['at'])<=min(now,h.time(s['period_end']))]
        latest=max((o['at'] for o in candidates),key=h.time,default=None);values={o['value'] for o in candidates if latest and h.time(o['at'])==h.time(latest)}
        value=next(iter(values)) if len(values)==1 else None
        state='unobserved' if value is None else 'target_met' if (value>=s['target'] if s['direction']=='increase' else value<=s['target']) else 'below_target'
        stars.append(dict(copy.deepcopy(s),current_value=value,current_at=latest if value is not None else None,measurement_state=state))
    ss={s['id']:s for s in records['sessions']};ns={s['id']:s for s in records['north_stars']};contributions=[]
    for c in sorted(records['contributions'],key=lambda r:r['id']):
        state='proposed' if c['status']=='proposed' else 'confirmed' if c['goal_sha256']==goal_digest(ss[c['session_record_id']]) and c['north_star_sha256']==north_star_digest(ns[c['north_star_id']]) and h.time(c['at'])<=now else 'reconfirmation'
        contributions.append(dict(copy.deepcopy(c),confirmation_state=state,reason={'proposed':'기여 제안이며 연결·인과 확인이 아닙니다.','confirmed':'현재 정의에 대한 기여 연결 확인 선언입니다. 인과·기여율 증명이 아닙니다.','reconfirmation':'정의 변경 또는 미래 확인으로 다시 확인해야 합니다.'}[state]))
    capture=[]
    for c in sorted(records['capture'],key=lambda r:r['id']):
        at=c['last_recorded_at'];fresh='unknown' if not at or h.time(at)>now or c['at'] is None or h.time(c['at'])>now or c['status']!='observed' else 'recent' if (now-h.time(at)).total_seconds()<=60 else 'stale'
        reason={'unknown':'수집 건강을 확인할 수 없거나 오류가 기록되었습니다.','recent':'최근 로컬 기록 관측입니다. 모든 실제 훅 호출의 커버리지 증명은 아닙니다.','stale':'마지막 정상 기록이 60초보다 오래되었습니다. 미사용 또는 수집 지연을 확인하세요.'}[fresh]
        if not any((r['actor_id'],r['environment_id'],r['project_id'])==(c['actor_id'],c['environment_id'],c['project_id']) for p in projects for r in p['sources']):reason+=' 출처 미연결 상태입니다.'
        capture.append(dict(copy.deepcopy(c),freshness=fresh,reason=reason))
    return dict(version=1,records=copy.deepcopy(records),sessions=sessions,people=people,north_stars=stars,contributions=contributions,capture=capture)
