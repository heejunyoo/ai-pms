#!/usr/bin/env python3
"""Opt-in entity watcher with durable bounded outbox and explicit conflicts."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
import uuid

HERE=Path(__file__).resolve().parent
import live_service as service
common=service.common;portfolio=service.portfolio;operations=service.operations
CONFIG_FIELDS={'version','url','actor_id','environment_id','project_ids','token_file','logdir','catalog','operations','outbox','loopback_test'}
OPTIONAL_FIELDS={'role','base_revisions','base_hashes'}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise common.TransportError('redirect_refused',409)


def validate_config(config):
    service.deny(isinstance(config,dict) and CONFIG_FIELDS<=set(config)<=CONFIG_FIELDS|OPTIONAL_FIELDS,'invalid_config')
    service.deny(type(config['version']) is int and config['version']==1 and type(config['loopback_test']) is bool,'invalid_config')
    portfolio.ident(config['actor_id']);portfolio.ident(config['environment_id'])
    ids=portfolio.array(config['project_ids']);service.deny(bool(ids) and all(common.central.uid(p) for p in ids) and len(ids)==len(set(ids)),'invalid_config')
    parsed=urlsplit(config['url']);service.deny(not parsed.username and not parsed.password and not parsed.query and not parsed.fragment and parsed.path in ('','/') and parsed.hostname,'invalid_url')
    service.deny(parsed.scheme=='https' or config['loopback_test'] and parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost','::1'),'https_required')
    service.deny(config.get('role','writer') in ('writer','manager'),'invalid_role')
    for field in ('token_file','logdir','outbox'):service.deny(isinstance(config[field],str) and bool(config[field]),'invalid_config')
    for field in ('catalog','operations'):service.deny(config[field] is None or isinstance(config[field],str) and bool(config[field]),'invalid_config')
    service.deny(isinstance(config.get('base_revisions',{}),dict) and all(isinstance(k,str) and service.safeint(v) for k,v in config.get('base_revisions',{}).items()),'invalid_revision')
    service.deny(isinstance(config.get('base_hashes',{}),dict) and all(isinstance(k,str) and isinstance(v,str) and re.fullmatch('[a-f0-9]{64}',v) for k,v in config.get('base_hashes',{}).items()),'invalid_baseline')
    return config


class Sender:
    def __init__(self,config):
        self.config=validate_config(copy.deepcopy(config));self.root=Path(config['outbox']);common.private_dir(self.root);self.path=self.root/'sender-state.json'
        self.opener=build_opener(ProxyHandler({}),NoRedirect());self.timeout=5
        with common.locked(self.root,'sender.lock'):
            if not self.path.exists():self.save(dict(version=1,queue=[],hashes=copy.deepcopy(config.get('base_hashes',{})),revisions=copy.deepcopy(config.get('base_revisions',{})),entities={},capture_contexts=[],errors=[],last_ack_at=None))
            self.read()
    def save(self,state):
        raw=common.encode(state);service.deny(len(raw)<=common.MAX_QUEUE,'outbox_full',503);common.write_private(self.path,raw)
    def read(self):
        state=common.strict_json(common.read_private(self.path,common.MAX_QUEUE),common.MAX_QUEUE)
        service.deny(isinstance(state,dict) and set(state)=={'version','queue','hashes','revisions','entities','capture_contexts','errors','last_ack_at'} and state['version']==1,'invalid_outbox',503)
        return state
    def file(self,path):return common.strict_json(common.read_private(Path(path),portfolio.MAX_FILE),portfolio.MAX_FILE)
    def record_error(self,state,entity,code):
        existing=next((e for e in state['errors'] if e['entity']==entity and e['code']==code),None)
        if existing:return existing['at']
        at=common.now();state['errors'].append(dict(entity=entity,code=code,at=at));state['errors']=state['errors'][-100:]
        return at
    def enqueue(self,state,kind,payload):
        entity=kind+':'+(operations.digest([payload['event']['project_id'],payload['event']['source'],payload['event']['event_id']]) if kind=='hook' else payload['id']);signature=common.digest(common.encode(payload))
        if state['hashes'].get(entity)==signature:return
        if kind=='hook' and entity in state['hashes']:self.record_error(state,entity,'native_id_conflict');return
        service.deny(len(state['queue'])<10000,'outbox_full',503)
        revision=0 if kind=='hook' else state['revisions'].get(entity,0)+sum(item['entity']==entity for item in state['queue'])
        eid=payload['event']['event_id'] if kind=='hook' else str(uuid.uuid4())
        state['queue'].append(dict(entity=entity,status='pending',envelope=dict(version=1,event_id=eid,kind=kind,base_revision=revision,payload=copy.deepcopy(payload))))
        state['hashes'][entity]=signature
    def scan(self,state):
        c=self.config;own=lambda r:(r.get('actor_id'),r.get('environment_id'))==(c['actor_id'],c['environment_id'])
        known_events={};root=Path(c['logdir'])
        try:
            service.deny(not any(p.is_symlink() for p in (root,*root.parents)),'unsafe_logdir')
            files=sorted(root.glob('*.jsonl'));service.deny(len(files)<=1000,'log_limit')
            for path in files:
                raw=common.read_private(path,portfolio.MAX_FILE)
                # A final partial append is left for the next scan, never acknowledged.
                for line in raw.splitlines(keepends=True):
                    if not line.endswith(b'\n'):continue
                    try:
                        event=common.strict_json(line,common.MAX_EVENT)
                        if not isinstance(event,dict) or event.get('project_id') not in c['project_ids']:continue
                        service.deny(common.central.valid_event(event,event['project_id']),'invalid_hook')
                        portfolio.validate_tree(event);known_events.setdefault(event['event_id'],{})[operations.digest([event['project_id'],event['source']])]=event
                        if c.get('role','writer')=='writer':self.enqueue(state,'hook',dict(actor_id=c['actor_id'],environment_id=c['environment_id'],event=event))
                    except (common.TransportError,ValueError,TypeError,KeyError):self.record_error(state,'hook','invalid_local_event')
        except (common.TransportError,OSError):self.record_error(state,'hook','log_unavailable')
        current={}
        if c['catalog']:
            try:
                catalog=self.file(c['catalog']);portfolio.validate_tree(catalog);portfolio.validate_catalog(catalog)
                for p in catalog['projects']:
                    if c.get('role','writer')=='manager' or any(own(r) and r['project_id'] in c['project_ids'] for r in p['source_refs']):
                        self.enqueue(state,'project',p);current['project:'+p['id']]=True
            except (common.TransportError,ValueError,OSError,KeyError,TypeError):self.record_error(state,'project','catalog_unavailable')
        if c['operations']:
            try:
                records=self.file(c['operations']);portfolio.keys(records,('version','sessions','north_stars','contributions','capture'),'operations');service.deny(records['version']==1,'invalid_operations');portfolio.validate_tree(records)
                own_sessions={s['id'] for s in records['sessions'] if own(s)}
                for kind,field in [('session','sessions'),('north_star','north_stars'),('contribution','contributions'),('capture','capture')]:
                    for p in portfolio.array(records[field]):
                        selected=own(p) if kind in ('session','capture') else c.get('role','writer')=='manager' if kind=='north_star' else c.get('role','writer')=='manager' or p['status']=='proposed' and p['session_record_id'] in own_sessions
                        if selected:self.enqueue(state,kind,p);current[kind+':'+p['id']]=True
            except (common.TransportError,ValueError,OSError,KeyError,TypeError):self.record_error(state,'operations','operations_unavailable')
        # Deletions do not silently leave a central entity presented as synchronized.
        for entity in state['entities']:
            if entity not in current:self.record_error(state,entity,'deletion_unsupported')
        state['entities']=current
        health_path=root/'capture-health.json'
        if c.get('role','writer')=='writer':
            contexts={tuple(row) for row in state['capture_contexts']}
            contexts.update((e['project_id'],e['source']) for group in known_events.values() for e in group.values())
            state['capture_contexts']=[list(row) for row in sorted(contexts)]
            problem=None;health=None;event=None
            try:
                health=self.file(health_path);portfolio.keys(health,('version','last_event_id','last_recorded_at','errors','last_failure_at','status','at'),'capture health')
                service.deny(type(health['version']) is int and health['version']==1 and service.safeint(health['errors']) and health['status'] in ('observed','degraded','unknown'),'invalid_health')
                candidates=known_events.get(health['last_event_id'],{})
                if len(candidates)==1:event=next(iter(candidates.values()))
                else:problem='health_context_unmapped'
            except (common.TransportError,ValueError,OSError,KeyError,TypeError):problem='health_unavailable'
            def capture_row(native,source,values):
                row=dict(values,id='capture-'+operations.digest([c['actor_id'],c['environment_id'],native,source])[:32],project_id=native,actor_id=c['actor_id'],environment_id=c['environment_id'],source=source)
                self.enqueue(state,'capture',row)
            if event and not problem:
                capture_row(event['project_id'],event['source'],{k:health[k] for k in ('last_event_id','last_recorded_at','errors','last_failure_at','status','at')})
            else:
                at=self.record_error(state,'capture',problem)
                if not contexts:contexts={(native,'unknown') for native in c['project_ids']}
                for native,source in sorted(contexts):
                    capture_row(native,source,dict(last_event_id=None,last_recorded_at=None,errors=0,last_failure_at=at,status='unknown' if not health_path.exists() or problem=='health_context_unmapped' else 'degraded',at=at))
    def request(self,envelope):
        token=common.read_private(Path(self.config['token_file']),1024).decode('utf-8').strip();service.deny(16<=len(token)<=512 and '\n' not in token and '\r' not in token,'invalid_token')
        req=Request(self.config['url'].rstrip('/')+'/api/records',data=common.encode(envelope),headers={'Content-Type':'application/json','Authorization':'Bearer '+token},method='POST')
        with self.opener.open(req,timeout=self.timeout) as response:
            service.deny(response.status==200,'invalid_ack');ack=common.strict_json(response.read(common.MAX_BODY+1))
        service.deny(isinstance(ack,dict) and set(ack)=={'event_id','cursor','entity_revision','status'} and ack['event_id']==envelope['event_id'] and ack['status']=='applied' and service.safeint(ack['cursor']) and service.safeint(ack['entity_revision']) and ack['entity_revision']>=1,'invalid_ack')
        if envelope['kind']!='hook':service.deny(ack['entity_revision']==envelope['base_revision']+1,'invalid_ack')
        return ack
    def tick(self):
        with common.locked(self.root,'sender.lock'):
            state=self.read();self.scan(state);self.save(state)
            while state['queue']:
                blocked={q['entity'] for q in state['queue'] if q['status']!='pending'}
                item=next((q for q in state['queue'] if q['status']=='pending' and q['entity'] not in blocked),None)
                if item is None:break
                try:
                    ack=self.request(item['envelope'])
                    state['revisions'][item['entity']]=ack['entity_revision'];state['last_ack_at']=common.now();state['queue'].remove(item)
                    self.save(state)
                except HTTPError as error:
                    if error.code==409:item['status']='conflict';self.record_error(state,item['entity'],'revision_conflict')
                    elif 400<=error.code<500:item['status']='quarantined';self.record_error(state,item['entity'],'authorization_or_record_rejected')
                    else:self.record_error(state,item['entity'],'delivery_retry')
                    self.save(state)
                    if item['status']=='pending':break
                except common.TransportError as error:
                    if error.code in ('invalid_ack','redirect_refused'):item['status']='quarantined'
                    self.record_error(state,item['entity'],error.code);self.save(state)
                    if item['status']=='pending':break
                except (OSError,URLError,UnicodeError):self.record_error(state,item['entity'],'delivery_retry');self.save(state);break
            return dict(pending=len(state['queue']),conflicts=sum(q['status']=='conflict' for q in state['queue']),quarantined=sum(q['status']=='quarantined' for q in state['queue']),errors=copy.deepcopy(state['errors']),last_ack_at=state['last_ack_at'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--once',action='store_true');mode.add_argument('--watch',action='store_true');args=p.parse_args()
    try:
        sender=Sender(common.strict_json(common.read_private(args.config,common.MAX_BODY)))
        while True:
            print(json.dumps(sender.tick(),ensure_ascii=False),flush=True)
            if args.once:return 0
            time.sleep(2)
    except (common.TransportError,OSError,ValueError,TypeError,KeyError):print('live-sender: configuration or storage unavailable',file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
