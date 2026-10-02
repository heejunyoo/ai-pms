#!/usr/bin/env python3
"""Bounded self-hosted live PMS; durable atomic state, no external deployment."""
import argparse
import base64
import copy
import hashlib
import hmac
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import ipaddress
import json
from pathlib import Path
import re
import secrets
import ssl
import sys
import threading
from urllib.parse import parse_qs, urlsplit

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
common=load('live_common',HERE.parent/'ai-pms-transport/common.py')
portfolio=load('live_portfolio',HERE.parent/'ai-pms-dashboard/portfolio.py')
operations=load('live_operations_service',HERE.parent/'ai-pms-dashboard/operations.py')
MAX_STATE=64*1024*1024
KINDS={'hook','project','session','north_star','contribution','capture'}


def deny(condition,code='invalid_record',status=400):
    if not condition:raise common.TransportError(code,status)


def safeint(value):return type(value) is int and 0<=value<=operations.SAFE_INTEGER


def validate_registry(registry):
    portfolio.keys(registry,('manager','writers'),'registry')
    portfolio.keys(registry['manager'],('actor_id','token_sha256'),'manager')
    entries=[registry['manager']]+portfolio.array(registry['writers']);identities=set();hashes=set()
    for i,r in enumerate(entries):
        if i:
            portfolio.keys(r,('actor_id','environment_id','project_ids','token_sha256'),'writer');portfolio.ident(r['environment_id'])
            ids=portfolio.array(r['project_ids']);deny(bool(ids) and len(ids)==len(set(ids)) and all(common.central.uid(x) for x in ids),'invalid_registry')
            pair=(r['actor_id'],r['environment_id']);deny(pair not in identities,'invalid_registry');identities.add(pair)
        portfolio.ident(r['actor_id']);deny(isinstance(r['token_sha256'],str) and re.fullmatch('[0-9a-f]{64}',r['token_sha256']),'invalid_registry')
        deny(r['token_sha256'] not in hashes,'invalid_registry');hashes.add(r['token_sha256'])
    return registry


def empty_state():
    return dict(version=1,cursor=0,catalog={'version':3,'projects':[]},store={'version':1,'sources':{}},operations=dict(version=1,sessions=[],north_stars=[],contributions=[],capture=[]),receipts={},revisions={},history=[],project_signatures={},operations_signature=None)


class LiveStore:
    # ponytail: bounded serialized atomic state; use a transactional DB when measured load needs it.
    def __init__(self,data_dir,registry,clock=common.now,evidence_mode='local-execution'):
        self.root=Path(data_dir);common.private_dir(self.root)
        deny(evidence_mode in portfolio.MODES,'evidence_mode');self.evidence_mode=evidence_mode
        self.registry=validate_registry(copy.deepcopy(registry));self.clock=clock;self.mutex=threading.RLock();self.cookies={}
        self.path=self.root/'state.json'
        with common.locked(self.root,'live.lock'):
            if not self.path.exists():self.save(empty_state())
            self.read()
    def read(self):
        state=common.strict_json(common.read_private(self.path,MAX_STATE),MAX_STATE)
        deny(isinstance(state,dict) and set(state)==set(empty_state()) and state['version']==1 and safeint(state['cursor']),'invalid_state',503)
        portfolio.build_model(state['store'],state['catalog'],self.clock(),operations=state['operations'])
        return state
    def save(self,state):
        raw=common.encode(state);deny(len(raw)<=MAX_STATE,'storage_full',503);common.write_private(self.path,raw)
    def authenticate(self,token):
        if not isinstance(token,str) or not 16<=len(token)<=512:return None
        signature=hashlib.sha256(token.encode()).hexdigest()
        for role,rows in [('manager',[self.registry['manager']]),('writer',self.registry['writers'])]:
            for row in rows:
                if hmac.compare_digest(signature,row['token_sha256']):return dict(row,role=role)
        return None
    def admitted(self,ref):
        return any((ref['actor_id'],ref['environment_id'])==(w['actor_id'],w['environment_id']) and ref['project_id'] in w['project_ids'] for w in self.registry['writers'])
    def model(self,state):return portfolio.build_model(state['store'],state['catalog'],self.clock(),operations=state['operations'])
    def advance(self,state,model):
        signatures={p['id']:common.digest(common.encode(p)) for p in model['projects']};ops=common.digest(common.encode(model['operations']))
        changed=sorted(pid for pid,sig in signatures.items() if state['project_signatures'].get(pid)!=sig)
        ops_changed=state['operations_signature']!=ops
        if changed or ops_changed:
            deny(state['cursor']<operations.SAFE_INTEGER,'cursor_full',503);state['cursor']+=1
            removed=bool(set(state['project_signatures'])-set(signatures))
            state['history'].append(dict(cursor=state['cursor'],project_ids=changed,operations=ops_changed,reset=removed));state['history']=state['history'][-200:]
            state['project_signatures']=signatures;state['operations_signature']=ops
        return state['cursor']
    def authorize_project(self,p,old,actor):
        deny(all(self.admitted(r) for r in p['source_refs']),'unregistered_source',403)
        if actor['role']=='manager':return
        pair=(actor['actor_id'],actor['environment_id']);aid=actor['actor_id']
        deny(any((r['actor_id'],r['environment_id'])==pair and r['project_id'] in actor['project_ids'] for r in p['source_refs']),'wrong_source',403)
        if old is None:
            deny(all((r['actor_id'],r['environment_id'])==pair for r in p['source_refs']),'source_admission',403)
        else:deny(p['source_refs']==old['source_refs'],'source_admission',403)
        old=old or {'documents':[],'management':{}};before=old.get('management') or {};after=p['management']
        def protected(new,previous,owner):
            deny(sorted((portfolio.canonical(r) for r in new if owner(r)!=aid))==sorted((portfolio.canonical(r) for r in previous if owner(r)!=aid)),'peer_history',403)
        def protected_source(new, previous, prefix=''):
            owner=lambda r:(r.get(prefix+'actor_id'),r.get(prefix+'environment_id'))
            deny(sorted(portfolio.canonical(r) for r in new if owner(r)!=pair)==sorted(portfolio.canonical(r) for r in previous if owner(r)!=pair),'peer_source_history',403)
        protected_source(p['documents'],old['documents'])
        protected_source(after['attempts'],before.get('attempts',[]))
        protected(after['blockers'],before.get('blockers',[]),lambda r:r['owner'])
        for field in ('checkpoints','decisions','capture','handoffs'):
            protected_source(after.get('traceability',{}).get(field,[]),before.get('traceability',{}).get(field,[]),'from_' if field=='handoffs' else '')
        bw=before.get('work') or {};aw=after.get('work') or {};oldtasks={t['id']:t for t in bw.get('tasks',[])}
        protected(aw.get('tasks',[]),bw.get('tasks',[]),lambda r:r['owner'])
        protected(aw.get('reviews',[]),bw.get('reviews',[]),lambda r:r['reviewer'])
        for u in aw.get('updates',[]):
            owner=oldtasks.get(u['task_id'],next((t for t in aw.get('tasks',[]) if t['id']==u['task_id']),{})).get('owner')
            if owner!=aid:deny(u in bw.get('updates',[]),'peer_task_update',403)
        for u in bw.get('updates',[]):
            if oldtasks[u['task_id']]['owner']!=aid:deny(u in aw.get('updates',[]),'peer_task_update',403)
        # New own evidence must match authenticated environment, too.
        for new,previous in [(p['documents'],old['documents']),(after['attempts'],before.get('attempts',[]))]:
            for row in new:
                if row not in previous:deny(row['actor_id']==aid and row['environment_id']==actor['environment_id'],'wrong_evidence_actor',403)
    def apply(self,envelope,actor):
        try:
            portfolio.keys(envelope,('version','event_id','kind','base_revision','payload'),'envelope')
            deny(type(envelope['version']) is int and envelope['version']==1 and common.central.identifier(envelope['event_id']) and envelope['kind'] in KINDS and safeint(envelope['base_revision']))
            portfolio.validate_tree(envelope);deny(len(common.encode(envelope))<=common.MAX_BODY,'body_too_large',413)
            signature=common.digest(common.encode(envelope));eid=envelope['event_id'];kind=envelope['kind'];p=envelope['payload']
            with self.mutex,common.locked(self.root,'live.lock'):
                state=self.read();receipt_key=common.digest(common.encode([actor['role'],actor['actor_id'],actor.get('environment_id'),[p.get('event',{}).get('project_id'),p.get('event',{}).get('source')] if kind=='hook' and isinstance(p,dict) and isinstance(p.get('event'),dict) else None,eid]));receipt=state['receipts'].get(receipt_key)
                if receipt:
                    deny(receipt['sha256']==signature and receipt['actor_id']==actor['actor_id'] and receipt['role']==actor['role'] and receipt['environment_id']==actor.get('environment_id'),'event_conflict',409)
                    return receipt['ack']
                deny(len(state['receipts'])<10000,'state_full',503)
                if kind=='hook':
                    portfolio.keys(p,('actor_id','environment_id','event'),'hook');e=p['event']
                    deny(actor['role']=='writer' and (p['actor_id'],p['environment_id'])==(actor['actor_id'],actor['environment_id']),'wrong_source',403)
                    deny(isinstance(e,dict) and e.get('project_id') in actor['project_ids'] and common.central.valid_event(e,e['project_id']),'invalid_hook')
                    key=common.central.source_key(dict(actor_id=p['actor_id'],environment_id=p['environment_id'],project_id=e['project_id']))
                    entity='hook:'+common.digest(common.encode([key,e['source'],e['event_id']]))
                    existing=state['store']['sources'].get(key,{}).get('events',{}).get(e['event_id'])
                    deny(existing is None or existing['event']==e,'native_event_conflict',409)
                else:
                    deny(isinstance(p,dict) and common.central.identifier(p.get('id')))
                    entity=kind+':'+p['id']
                revision=state['revisions'].get(entity,0)
                if kind=='hook' and revision:
                    source=state['store']['sources'][key];deny(source['events'][e['event_id']]['event']==e,'native_event_conflict',409)
                else:deny(envelope['base_revision']==revision,'revision_conflict',409)
                if kind=='hook':
                    source=state['store']['sources'].setdefault(key,dict(actor_id=p['actor_id'],environment_id=p['environment_id'],project_id=e['project_id'],label='등록 출처',evidence_mode=self.evidence_mode,events={}))
                    if e['event_id'] not in source['events']:
                        source['events'][e['event_id']]=dict(event=e,received_at=self.clock(),file_sha256=common.digest(common.encode(e)),line=len(source['events'])+1)
                elif kind=='project':
                    old=next((r for r in state['catalog']['projects'] if r['id']==p['id']),None)
                    self.authorize_project(p,old,actor)
                    state['catalog']['projects']=[r for r in state['catalog']['projects'] if r['id']!=p['id']]+[copy.deepcopy(p)]
                else:
                    field={'session':'sessions','north_star':'north_stars','contribution':'contributions','capture':'capture'}[kind]
                    old=next((r for r in state['operations'][field] if r['id']==p['id']),None)
                    if kind in ('session','capture'):
                        deny(actor['role']=='writer' and (p.get('actor_id'),p.get('environment_id'))==(actor['actor_id'],actor['environment_id']),'wrong_source',403)
                        native=p.get('source_project_id') if kind=='session' else p.get('project_id');deny(native in actor['project_ids'],'wrong_project',403)
                        if old:deny((old['actor_id'],old['environment_id'])==(actor['actor_id'],actor['environment_id']),'entity_owner',403)
                        if kind=='session' and p.get('acceptance') is not None and (old is None or p['acceptance']!=old['acceptance']):deny(p['acceptance']['actor_id']==actor['actor_id'],'acceptance_actor',403)
                    elif kind=='north_star':deny(actor['role']=='manager','manager_required',403)
                    elif kind=='contribution':
                        if p.get('status')=='confirmed':deny(actor['role']=='manager' and p.get('confirmed_by')==actor['actor_id'],'confirmation_actor',403)
                        elif actor['role']=='writer':
                            session=next((s for s in state['operations']['sessions'] if s['id']==p.get('session_record_id')),None)
                            deny(session and (session['actor_id'],session['environment_id'])==(actor['actor_id'],actor['environment_id']),'contribution_owner',403)
                            deny(old is None or old['status']=='proposed' and old['session_record_id']==p['session_record_id'],'confirmed_protection',403)
                    state['operations'][field]=[r for r in state['operations'][field] if r['id']!=p['id']]+[copy.deepcopy(p)]
                model=self.model(state);before=state['cursor'];cursor=self.advance(state,model)
                if cursor==before:
                    deny(cursor<operations.SAFE_INTEGER,'cursor_full',503);state['cursor']+=1;cursor=state['cursor'];state['history'].append(dict(cursor=cursor,project_ids=[],operations=False));state['history']=state['history'][-200:]
                # Equal native hook retransmissions get a durable receipt but no inflated entity revision.
                new_revision=revision if kind=='hook' and revision else revision+1;state['revisions'][entity]=new_revision
                ack=dict(event_id=eid,cursor=cursor,entity_revision=new_revision,status='applied')
                state['receipts'][receipt_key]=dict(sha256=signature,actor_id=actor['actor_id'],environment_id=actor.get('environment_id'),role=actor['role'],ack=ack,envelope=copy.deepcopy(envelope))
                self.save(state);return ack
        except (ValueError,KeyError,TypeError,RecursionError) as error:raise common.TransportError('invalid_record',400) from error
    def changes(self,after):
        deny(safeint(after),'invalid_cursor')
        with self.mutex,common.locked(self.root,'live.lock'):
            state=self.read();model=self.model(state);before=state['cursor'];self.advance(state,model)
            if before!=state['cursor']:self.save(state)
            deny(after<=state['cursor'],'future_cursor',409)
            history=state['history'];reset=after==0 or bool(history) and after<history[0]['cursor']-1 or any(row.get('reset',False) for row in history if row['cursor']>after)
            updates={pid for row in history if row['cursor']>after for pid in row['project_ids']}
            ops_changed=reset or any(row['operations'] for row in history if row['cursor']>after)
            return dict(cursor=state['cursor'],reset=reset,project_updates=[p for p in model['projects'] if reset or p['id'] in updates],operations=model['operations'] if ops_changed else None,generated_at=model['generated_at'])
    def history(self,after):
        deny(safeint(after),'invalid_cursor')
        with self.mutex,common.locked(self.root,'live.lock'):
            state=self.read();rows=[]
            for receipt_id,r in state['receipts'].items():
                if r['ack']['cursor']<=after:continue
                e=r['envelope'];rows.append(dict(receipt_id=receipt_id,event_id=e['event_id'],kind=e['kind'],payload=e['payload'],entity_revision=r['ack']['entity_revision'],cursor=r['ack']['cursor'],actor_id=r['actor_id'],environment_id=r['environment_id']))
            rows.sort(key=lambda r:(r['cursor'],r['receipt_id']))
            return dict(cursor=state['cursor'],records=rows[:100],next_after=rows[99]['cursor'] if len(rows)>100 else state['cursor'])
    def status(self):
        with self.mutex,common.locked(self.root,'live.lock'):
            s=self.read();return dict(cursor=s['cursor'],storage='durable',sources=len(s['store']['sources']),projects=len(s['catalog']['projects']),capture_states={k:sum(c['status']==k for c in s['operations']['capture']) for k in ('observed','degraded','unknown')})


class Handler(BaseHTTPRequestHandler):
    server_version='LivePMS/1'
    def log_message(self,*args):pass
    def send_json(self,status,value,headers=None):self.send_content(status,common.encode(value),'application/json',headers)
    def send_content(self,status,body,content_type,headers=None):
        self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
        for k,v in (headers or {}).items():self.send_header(k,v)
        self.end_headers();self.wfile.write(body)
    def send_html(self,html):
        hashes=["'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',html,re.S)]
        csp="default-src 'none'; script-src "+' '.join(hashes)+"; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'"
        self.send_content(200,html.encode(),'text/html; charset=utf-8',{'Content-Security-Policy':csp,'X-Frame-Options':'DENY'})
    def origin(self):
        host=self.headers.get('Host');deny(host==self.server.authority,'invalid_host',403)
        origin=self.headers.get('Origin');expected=('https' if self.server.tls else 'http')+'://'+host
        if origin is not None:deny(origin==expected,'invalid_origin',403)
        return expected
    def actor(self):
        self.origin();authorization=self.headers.get('Authorization')
        if authorization:
            deny(authorization.startswith('Bearer '),'unauthorized',401);actor=self.server.store.authenticate(authorization[7:])
        else:
            try:
                cookie=SimpleCookie();cookie.load(self.headers.get('Cookie',''));sid=cookie['pms_session'].value if 'pms_session' in cookie else None
            except Exception:sid=None
            entry=self.server.store.cookies.get(sid);actor=entry['actor'] if entry and entry['expires']>portfolio.time(self.server.store.clock()).timestamp() else None
            if self.command=='POST':deny(self.headers.get('Origin') is not None,'origin_required',403)
        deny(actor is not None,'unauthorized',401);return actor
    def body(self):
        deny(self.headers.get('Transfer-Encoding') is None,'invalid_body')
        length=self.headers.get('Content-Length','');deny(length.isdigit() and int(length)<=common.MAX_BODY,'body_too_large',413)
        raw=self.rfile.read(int(length));deny(len(raw)==int(length),'incomplete_body');return common.strict_json(raw)
    def dispatch(self):
        path=urlsplit(self.path);deny(not path.fragment,'invalid_path')
        if self.command=='POST' and path.path=='/api/login':
            self.origin();deny(self.headers.get('Origin') is not None,'origin_required',403);body=self.body();portfolio.keys(body,('token',),'login')
            actor=self.server.store.authenticate(body['token']);deny(actor and actor['role']=='manager','unauthorized',401)
            now=portfolio.time(self.server.store.clock()).timestamp();cookies=self.server.store.cookies
            for key in list(cookies):
                if cookies[key]['expires']<=now:del cookies[key]
            deny(len(cookies)<100,'login_limit',429);sid=secrets.token_urlsafe(32);cookies[sid]=dict(actor=actor,expires=now+3600)
            self.send_json(200,{'status':'authenticated'},{'Set-Cookie':'pms_session='+sid+'; Path=/; HttpOnly; SameSite=Strict; Max-Age=3600'+('; Secure' if self.server.tls else '')});return
        if self.command=='GET' and path.path=='/':
            self.origin()
            try:actor=self.actor()
            except common.TransportError as error:
                if error.status!=401:raise
                model=dict(schema_version=3,generated_at=self.server.store.clock(),evidence_mode=self.server.store.evidence_mode,projects=[],operations=operations.derive(dict(version=1,sessions=[],north_stars=[],contributions=[],capture=[]),[],{'version':1,'sources':{}},self.server.store.clock()))
                html=portfolio.render_html(model).replace('<body>','<body data-live="true">',1)
                self.send_html(html);return
        else:actor=self.actor()
        if self.command=='POST' and path.path=='/api/records':self.send_json(200,self.server.store.apply(self.body(),actor));return
        deny(actor['role']=='manager','manager_required',403)
        if self.command=='GET' and path.path=='/api/changes':
            query=parse_qs(path.query,strict_parsing=True);deny(set(query)=={'after'} and len(query['after'])==1 and query['after'][0].isdigit(),'invalid_cursor')
            self.send_json(200,self.server.store.changes(int(query['after'][0])));return
        if self.command=='GET' and path.path=='/api/history':
            query=parse_qs(path.query,strict_parsing=True);deny(set(query)=={'after'} and len(query['after'])==1 and query['after'][0].isdigit(),'invalid_cursor')
            self.send_json(200,self.server.store.history(int(query['after'][0])));return
        if self.command=='GET' and path.path=='/api/status':self.send_json(200,self.server.store.status());return
        if self.command=='GET' and path.path=='/':
            changes=self.server.store.changes(0);modes={s['evidence_mode'] for p in changes['project_updates'] for s in p['sources']};model=dict(schema_version=3,generated_at=changes['generated_at'],evidence_mode='mixed' if len(modes)>1 else next(iter(modes),'declared'),projects=changes['project_updates'],operations=changes['operations'])
            html=portfolio.render_html(model).replace('<body>','<body data-live="true">',1)
            self.send_html(html);return
        raise common.TransportError('not_found',404)
    def handle_request(self):
        try:self.dispatch()
        except common.TransportError as e:self.send_json(e.status,{'error':e.code})
        except (ValueError,TypeError,KeyError,RecursionError):self.send_json(400,{'error':'invalid_request'})
        except OSError:self.send_json(503,{'error':'storage_failed'})
    do_GET=handle_request
    do_POST=handle_request


def make_server(store,host='127.0.0.1',port=0,tls_cert=None,tls_key=None):
    try:loopback=ipaddress.ip_address(host).is_loopback
    except ValueError:loopback=host=='localhost'
    deny(bool(tls_cert)==bool(tls_key),'tls_pair')
    deny(loopback or tls_cert is not None,'tls_required')
    server=ThreadingHTTPServer((host,port),Handler);server.daemon_threads=True;server.store=store;server.tls=tls_cert is not None
    server.authority=('[%s]'%host if ':' in host else host)+':'+str(server.server_address[1])
    if tls_cert:
        # owner-only credential checks before OpenSSL accesses keys.
        common.read_private(Path(tls_key),common.MAX_BODY);context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2;context.load_cert_chain(tls_cert,tls_key);server.socket=context.wrap_socket(server.socket,server_side=True)
    return server


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--registry',type=Path,required=True);p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8765);p.add_argument('--tls-cert',type=Path);p.add_argument('--tls-key',type=Path);p.add_argument('--synthetic-demo',action='store_true');args=p.parse_args()
    try:
        registry=common.strict_json(common.read_private(args.registry,common.MAX_BODY));server=make_server(LiveStore(args.data_dir,registry,evidence_mode='synthetic' if args.synthetic_demo else 'local-execution'),args.host,args.port,args.tls_cert,args.tls_key)
        print('live-service ready port='+str(server.server_address[1]),flush=True);server.serve_forever();return 0
    except (common.TransportError,OSError,ValueError):print('live-service: configuration or storage unavailable',file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
