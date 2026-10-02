#!/usr/bin/env python3
"""Strict portable management contract. Hashes identify input, not trusted execution."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import PurePosixPath
import re

CRITERION_KEYS = {'id','label','scope','target_id','command','expected_exit_code'}
FIELDS = {'objectives','assignment','requirements','plans','test_plans','artifact','attempts','blockers','improvements','harness','graphs'}
PRIVATE = re.compile(r'(?i)(?:\bBearer\s+\S+|\b(?:sk|ghp|github_pat|AIza|xox[baprs])[-_][A-Za-z0-9_-]{8,}|\bAIza[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY|\b(?:password|secret|token|api[_ -]?key|access[_-]?token)\s*[:=]\s*\S+|(?:/' + 'Users/' + r'|/home/|/private/|/tmp/|/root/|[A-Z]:[\\/]|~/)[^\s]*)')
ABSOLUTE = re.compile(r'(?:^|[\s\"\'=])/(?!/)[A-Za-z0-9_.-]+(?:/[^\s<>]*)?')

def require(ok, message):
    if not ok: raise ValueError(message)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)

def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()
def criterion_signature(c): return digest({k:c[k] for k in sorted(CRITERION_KEYS)})
def test_plan_sha256(tp): return digest(tp)
def artifact_sha256(files): return digest(sorted(files,key=lambda f:f['path']))
def keys(v, fields, context='management'): require(isinstance(v,dict) and set(v)==set(fields),context+' fields')
def ident(v): require(isinstance(v,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}',v) and not PRIVATE.search(v),'identifier')
def text(v): require(isinstance(v,str) and bool(v.strip()) and len(v)<=20000,'text')
def sha(v): require(isinstance(v,str) and re.fullmatch('[a-f0-9]{64}',v),'sha256')
def time(v):
    require(isinstance(v,str) and len(v)<=40 and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z',v),'UTC Z time')
    try: return dt.datetime.fromisoformat(v.replace('Z','+00:00'))
    except ValueError: raise ValueError('UTC time') from None

def validate_tree(v, depth=0):
    require(depth<25,'depth limit')
    if isinstance(v,str): require(len(v)<=20000 and not PRIVATE.search(v) and not ABSOLUTE.search(v) and not any(ord(c)<32 and c not in '\n\t' for c in v),'private text')
    elif isinstance(v,(list,dict)):
        require(len(v)<=10000,'array limit')
        for child in (list(v.keys())+list(v.values()) if isinstance(v,dict) else v): validate_tree(child,depth+1)
    else: require(v is None or type(v) in (int,bool),'JSON value')

def arr(v): require(isinstance(v,list) and len(v)<=10000,'array'); return v

def records(m,field,fields,versioned=False):
    seen=set()
    for r in arr(m[field]):
        keys(r,fields,field); ident(r['id'])
        if versioned: ident(r['version'])
        key=(r['id'],r['version']) if versioned else r['id']
        require(key not in seen,'duplicate '+field); seen.add(key)
    return m[field]

def refs(values, allowed):
    for v in arr(values): ident(v); require(v in allowed,'missing reference')
    require(len(values)==len(set(values)),'duplicate references')

def file_list(files):
    paths=set()
    for f in arr(files):
        keys(f,('path','sha256'),'file'); text(f['path']); sha(f['sha256'])
        path=PurePosixPath(f['path'])
        require(not path.is_absolute() and '\\' not in f['path'] and str(path)==f['path'] and all(part not in ('.','..') for part in path.parts) and bool(path.parts) and not re.match(r'^[A-Za-z]:',f['path']),'relative file path')
        require(f['path'] not in paths,'duplicate file'); paths.add(f['path'])
    return paths

def criterion(c,p):
    keys(c,CRITERION_KEYS,'criterion')
    ident(c['id']); ident(c['target_id']); text(c['label']); text(c['command'])
    require(c['scope'] in ('project','phase','task'),'scope')
    require(type(c['expected_exit_code']) is int and -255<=c['expected_exit_code']<=255,'exit code')
    require(c['scope']!='project' or c['target_id']==p['id'],'project target')
    require(c['scope']!='phase' or c['target_id'] in {x['id'] for x in p['phases']},'phase target')

def validate_traceability(t,pairs,reqids,attemptmap):
    keys(t,('checkpoints','decisions','handoffs','capture'),'traceability')
    decisions=records(t,'decisions',('id','at','actor_id','environment_id','session_id','summary','alternatives','reason','requirement_ids','supersedes','provenance'))
    decisionmap={r['id']:r for r in decisions}
    def source(r,prefix=''):
        for k in ('actor_id','environment_id','session_id'): ident(r[prefix+k])
        require((r[prefix+'actor_id'],r[prefix+'environment_id']) in pairs,'trace source')
    for r in decisions:
        source(r); time(r['at']); text(r['summary']); text(r['reason']); refs(r['requirement_ids'],reqids)
        require(bool(arr(r['alternatives'])),'decision alternatives')
        for alternative in r['alternatives']: text(alternative)
        require(r['provenance']=='declared','decision provenance')
        if r['supersedes'] is not None: ident(r['supersedes'])
        require(r['supersedes'] is None or r['supersedes'] in decisionmap,'supersedes reference')
    for r in decisions:
        seen=set(); cur=r['id']
        while cur is not None:
            require(cur not in seen,'decision cycle'); seen.add(cur); cur=decisionmap[cur]['supersedes']
    def commit(v): require(isinstance(v,str) and re.fullmatch(r'(?:[a-f0-9]{40}|[a-f0-9]{64})',v),'git commit')
    for r in records(t,'checkpoints',('id','at','actor_id','environment_id','session_id','agent_id','revision','artifact_sha256','commit','parent_commits','dirty','worktree_sha256','attempt_ids','decision_ids','provenance','summary')):
        source(r); time(r['at']); ident(r['revision']); sha(r['artifact_sha256']); text(r['summary'])
        if r['agent_id'] is not None: ident(r['agent_id'])
        require(r['provenance'] in ('observed','declared','inferred'),'checkpoint provenance')
        refs(r['attempt_ids'],attemptmap); refs(r['decision_ids'],decisionmap)
        for aid in r['attempt_ids']:
            a=attemptmap[aid]; require(a['revision']==r['revision'] and a['artifact_sha256']==r['artifact_sha256'],'checkpoint attempt identity')
        parents=arr(r['parent_commits'])
        for parent in parents: commit(parent)
        require(len(parents)==len(set(parents)),'duplicate parent commits')
        require(r['dirty'] is None or type(r['dirty']) is bool,'git dirty')
        if r['worktree_sha256'] is not None: sha(r['worktree_sha256'])
        if r['commit'] is None:
            require(not parents and r['dirty'] is None and r['worktree_sha256'] is None,'no git checkpoint')
        else: commit(r['commit'])
    for r in records(t,'handoffs',('id','at','from_actor_id','from_environment_id','from_session_id','to_actor_id','to_environment_id','to_session_id','summary','requirement_ids','decision_ids','attempt_ids','packet_sha256','usage','usage_at','usage_evidence')):
        source(r,'from_'); source(r,'to_'); at=time(r['at']); text(r['summary']); sha(r['packet_sha256'])
        require(tuple(r['from_'+k] for k in ('actor_id','environment_id','session_id'))!=tuple(r['to_'+k] for k in ('actor_id','environment_id','session_id')),'handoff same session')
        refs(r['requirement_ids'],reqids); refs(r['decision_ids'],decisionmap); refs(r['attempt_ids'],attemptmap)
        require(r['usage'] in ('not_observed','declared','observed'),'handoff usage')
        if r['usage']=='not_observed': require(r['usage_at'] is None and r['usage_evidence'] is None,'unobserved usage evidence')
        else:
            require(r['usage_at'] is not None and r['usage_evidence'] is not None,'usage evidence missing')
            require(time(r['usage_at'])>=at,'usage time order'); text(r['usage_evidence'])
    for r in records(t,'capture',('id','actor_id','environment_id','tool','capabilities','status','last_observed_at','at','reason','provenance')):
        for k in ('actor_id','environment_id','tool'): ident(r[k])
        require((r['actor_id'],r['environment_id']) in pairs,'capture source'); at=time(r['at']); text(r['reason'])
        refs(r['capabilities'],{'events','tests','git','handoff','memory','mcp'})
        require(r['status'] in ('active','paused','degraded','stopped','unsupported','unknown'),'capture status')
        require(r['provenance'] in ('observed','declared'),'capture provenance')
        require(r['status']!='unsupported' or not r['capabilities'],'unsupported capabilities')
        if r['last_observed_at'] is not None: require(time(r['last_observed_at'])<=at,'capture time order')

def validate(p,helpers=None):
    m=p['management']; keys(m,FIELDS | ({'traceability'} if 'traceability' in m else set()))
    require(len(canonical(m).encode())<=16*1024*1024,'size limit')
    (helpers.validate_tree if helpers else validate_tree)(m)
    owners={r['actor_id'] for r in p['source_refs']}; pairs={(r['actor_id'],r['environment_id']) for r in p['source_refs']}
    objs=records(m,'objectives',('id','version','kind','parent_id','title','success_condition','source','at'),True)
    objkeys={(r['id'],r['version']) for r in objs}; parents={}
    for r in objs:
        require(r['kind'] in ('company','personal'),'objective kind')
        for k in ('title','success_condition','source'): text(r[k])
        time(r['at']); parent=r['parent_id']
        require(parent is None or parent in {x['id'] for x in objs},'objective parent')
        require(r['id'] not in parents or parents[r['id']]==parent,'parent versions differ'); parents[r['id']]=parent
    for oid in parents:
        seen=set(); cur=oid
        while cur is not None:
            require(cur not in seen,'objective cycle'); seen.add(cur); cur=parents[cur]
    a=m['assignment']
    if a is not None:
        keys(a,('objective_id','objective_version','kind','issuer','assignee','at','acceptance'),'assignment')
        require((a['objective_id'],a['objective_version']) in objkeys,'assignment objective')
        require(a['kind'] in ('outcome','task') and a['assignee'] in owners,'assignment owner'); ident(a['issuer']); time(a['at']); text(a['acceptance'])
    reqs=records(m,'requirements',('id','text','source'))
    for r in reqs: text(r['text']); text(r['source'])
    reqids={r['id'] for r in reqs}
    plans=records(m,'plans',('id','version','at','summary','reason','requirement_ids','handoff_ref'),True)
    for r in plans:
        time(r['at']); text(r['summary']); text(r['reason']); refs(r['requirement_ids'],reqids)
        require(r['handoff_ref'] is None or isinstance(r['handoff_ref'],str),'handoff ref')
        if r['handoff_ref'] is not None: text(r['handoff_ref'])
    plankeys={(r['id'],r['version']) for r in plans}
    tps=records(m,'test_plans',('id','version','plan_id','plan_version','criterion_id','requirement_ids','reason','excluded','at','definition','test_files'),True)
    latest={}; tpmap={}
    keys(m['artifact'],('revision','sha256','files'),'artifact'); require(m['artifact']['revision']==p['current_revision'],'artifact revision'); sha(m['artifact']['sha256'])
    files=file_list(m['artifact']['files']); require(not p['criteria'] or bool(files),'artifact files required'); require(artifact_sha256(m['artifact']['files'])==m['artifact']['sha256'],'artifact digest')
    for r in tps:
        require((r['plan_id'],r['plan_version']) in plankeys,'test plan reference'); refs(r['requirement_ids'],reqids)
        text(r['reason']); require(isinstance(r['excluded'],str),'excluded'); time(r['at']); criterion(r['definition'],p)
        require(r['criterion_id']==r['definition']['id'],'criterion id'); require(file_list(r['test_files'])<=files,'test file missing from artifact')
        tpmap[(r['id'],r['version'])]=r
        cid=r['criterion_id']
        if cid in latest: require(time(r['at'])!=time(latest[cid]['at']),'ambiguous latest test plan')
        if cid not in latest or time(r['at'])>time(latest[cid]['at']): latest[cid]=r
    require(set(latest)=={c['id'] for c in p['criteria']},'criterion coverage')
    for c in p['criteria']: require(latest[c['id']]['definition']==c,'current criterion definition')
    attempts=records(m,'attempts',('id','test_plan_id','test_plan_version','test_plan_sha256','criterion_signature','revision','artifact_sha256','command','started_at','at','exit_code','actor_id','environment_id','session_id','environment','runner','summary','provenance'))
    for r in attempts:
        require((r['test_plan_id'],r['test_plan_version']) in tpmap,'attempt test plan'); tp=tpmap[(r['test_plan_id'],r['test_plan_version'])]
        for k in ('test_plan_sha256','criterion_signature','artifact_sha256'): sha(r[k])
        require(r['test_plan_sha256']==test_plan_sha256(tp) and r['criterion_signature']==criterion_signature(tp['definition']) and r['command']==tp['definition']['command'],'attempt definition mismatch')
        require(time(r['started_at'])<=time(r['at']),'attempt order')
        require(r['exit_code'] is None or type(r['exit_code']) is int and -255<=r['exit_code']<=255,'attempt exit code')
        for k in ('revision','actor_id','environment_id','session_id','runner'): ident(r[k])
        require((r['actor_id'],r['environment_id']) in pairs,'attempt source'); text(r['summary'])
        require(r['environment'] in ('unit','mock','local','browser','live-provider','production') and r['provenance'] in ('runner','declared'),'attempt provenance')
    attemptmap={r['id']:r for r in attempts}
    blockers=records(m,'blockers',('id','status','summary','cause_state','cause','attempt_ids','owner','next_action','resolved_by'))
    for r in blockers:
        require(r['status'] in ('open','resolved') and r['cause_state'] in ('hypothesis','confirmed') and r['owner'] in owners,'blocker owner/state')
        for k in ('summary','cause','next_action'): text(r[k])
        refs(r['attempt_ids'],attemptmap)
        require(r['resolved_by'] is None or r['resolved_by'] in attemptmap,'resolution reference')
        if r['status']=='resolved':
            require(r['resolved_by'] is not None,'resolution missing'); a=attemptmap[r['resolved_by']]; tp=tpmap[(a['test_plan_id'],a['test_plan_version'])]
            require(a['provenance']=='runner' and a['exit_code']==tp['definition']['expected_exit_code'],'resolution needs runner pass')
            require(any(tpmap[(attemptmap[aid]['test_plan_id'],attemptmap[aid]['test_plan_version'])]['criterion_id']==tp['criterion_id'] for aid in r['attempt_ids']),'resolution must address blocked criterion')
        else: require(r['resolved_by'] is None,'open resolution')
    improvements=records(m,'improvements',('id','area','version','hypothesis','change','evidence_attempt_ids','validation_attempt_ids','decision'))
    for r in improvements:
        ident(r['version']); require(r['area'] in ('rule','harness','loop','skill','mcp') and r['decision'] in ('proposed','trial','adopt','hold'),'improvement')
        text(r['hypothesis']); text(r['change']); refs(r['evidence_attempt_ids'],attemptmap); refs(r['validation_attempt_ids'],attemptmap)
    for r in records(m,'harness',('id','version','source','at'),True): text(r['source']); time(r['at'])
    for r in records(m,'graphs',('id','generator','version','mode','source_revision','source_sha256','at','status')):
        for k in ('generator','version','source_revision'): ident(r[k])
        sha(r['source_sha256']); time(r['at']); require(r['mode']=='code-only' and r['status'] in ('generated','failed','unknown'),'graph')
    if 'traceability' in m: validate_traceability(m['traceability'],pairs,reqids,attemptmap)
    return m

def derive(p,observed,helpers=None):
    validate(p,helpers)
    observed=time(observed) if isinstance(observed,str) else observed
    m=copy.deepcopy(p['management']); tps={(r['id'],r['version']):r for r in m['test_plans']}; runs=[]
    current={c['id']:c for c in p['criteria']}
    manifest={f['path']:f['sha256'] for f in m['artifact']['files']}
    latest={}
    for tp in m['test_plans']:
        cid=tp['criterion_id']
        if cid not in latest or time(tp['at'])>time(latest[cid]['at']): latest[cid]=tp
    for a in m['attempts']:
        tp=tps[(a['test_plan_id'],a['test_plan_version'])]; cid=tp['criterion_id']
        status='pass' if a['exit_code']==tp['definition']['expected_exit_code'] else 'fail'
        if a['exit_code'] is None or a['provenance']!='runner' or time(a['at'])>observed or (a['revision']==p['current_revision'] and (tp!=latest[cid] or a['artifact_sha256']!=m['artifact']['sha256'] or any(manifest[f['path']]!=f['sha256'] for f in tp['test_files']))): status='unknown'
        a['status']=status
        if a['provenance']=='runner': runs.append(dict(criterion_id=cid,revision=a['revision'],at=a['at'],exit_code=a['exit_code'] if status!='unknown' else None,session_id=a['session_id'],evidence='management attempt '+a['id']+' · '+a['provenance']+' · '+a['summary'],criterion_signature=a['criterion_signature']))
    groups={}
    for a in m['attempts']:
        cid=tps[(a['test_plan_id'],a['test_plan_version'])]['criterion_id']; groups.setdefault((cid,a['revision'],time(a['at'])),set()).add((a['exit_code'],a['criterion_signature'],a['artifact_sha256'],a['provenance']))
    for a in m['attempts']:
        cid=tps[(a['test_plan_id'],a['test_plan_version'])]['criterion_id']
        if len(groups[(cid,a['revision'],time(a['at']))])>1: a['status']='unknown'
    for run in runs:
        if len(groups[(run['criterion_id'],run['revision'],time(run['at']))])>1: run['exit_code']=None
    amap={a['id']:a for a in m['attempts']}
    for b in m['blockers']:
        a=amap.get(b['resolved_by'])
        b['verification']='current' if a and a['status']=='pass' and a['revision']==p['current_revision'] else 'revalidation' if a and a['provenance']=='runner' and time(a['at'])<=observed else 'unknown'
    for g in m['graphs']:
        g['freshness']='unknown' if g['status']!='generated' or time(g['at'])>observed else 'current' if g['source_revision']==p['current_revision'] and g['source_sha256']==m['artifact']['sha256'] else 'stale'
    return runs,m
