#!/usr/bin/env python3
"""Two authenticated local HTTP writers; synthetic records, never remote proof."""
import copy
from http.cookies import SimpleCookie
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import uuid
import generate_sample as sample
import live_service as service
import live_sender as sender
common=service.common
TOKENS={'manager':'manager-demo-secret-0123456789','Alice':'alice-demo-secret-0123456789','Bob':'bob-demo-secret-0123456789'}

class LiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.catalog,self.events,self.records=sample.make_sample();self.project=self.catalog['projects'][0]
        a=next(r for r in self.project['source_refs'] if r['actor_id']=='Alice');b=next(r for r in self.project['source_refs'] if r['actor_id']=='Bob');self.refs={'Alice':a,'Bob':b}
        self.registry=dict(manager=dict(actor_id='Alice',token_sha256=common.digest(TOKENS['manager'].encode())),writers=[dict(actor_id=name,environment_id=ref['environment_id'],project_ids=[ref['project_id']],token_sha256=common.digest(TOKENS[name].encode())) for name,ref in self.refs.items()])
        self.registry['writers'].append(dict(actor_id='Alice',environment_id='desktop',project_ids=[self.refs['Alice']['project_id']],token_sha256=common.digest(b'alice-desktop-secret-0123456789')))
        self.clock=sample.NOW;self.store=service.LiveStore(self.root/'central',self.registry,clock=lambda:self.clock,evidence_mode='synthetic');self.server=service.make_server(self.store);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.url='http://127.0.0.1:'+str(self.server.server_address[1])
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def call(self,path,body=None,token=None,headers=None):
        headers=dict(headers or {});
        if token:headers['Authorization']='Bearer '+token
        request=Request(self.url+path,data=common.encode(body) if body is not None else None,headers=headers)
        try:
            with urlopen(request,timeout=4) as response:return response.status,dict(response.headers),response.read()
        except HTTPError as error:return error.code,dict(error.headers),error.read()
    def record(self,kind,payload,who='Alice',revision=0,eid=None):
        envelope=dict(version=1,event_id=eid or str(uuid.uuid4()),kind=kind,base_revision=revision,payload=payload)
        code,headers,raw=self.call('/api/records',envelope,TOKENS[who]);return code,json.loads(raw),envelope
    def seed(self):self.assertEqual(self.record('project',self.project,'manager')[0],200)
    def hook(self,name='Alice'):
        ref=self.refs[name];source=self.events['sources'][service.portfolio.central.source_key(ref)]
        return copy.deepcopy(next(iter(source['events'].values()))['event'])
    def changes(self,after=0):
        code,_,raw=self.call('/api/changes?after='+str(after),token=TOKENS['manager']);self.assertEqual(code,200);return json.loads(raw)
    def test_two_writer_http_management_changes(self):
        self.seed();self.assertEqual(self.record('hook',dict(actor_id='Alice',environment_id=self.refs['Alice']['environment_id'],event=self.hook()))[0],200)
        self.assertEqual(self.record('hook',dict(actor_id='Bob',environment_id=self.refs['Bob']['environment_id'],event=self.hook('Bob')),'Bob')[0],200)
        change=self.changes();self.assertEqual(len(change['project_updates']),1);self.assertEqual({s['actor_id'] for s in change['operations']['sessions']},{'Alice','Bob'})
        p=copy.deepcopy(self.project);p['goal']='업데이트된 합성 목표';self.assertEqual(self.record('project',p,revision=1)[0],200)
        nextchange=self.changes(change['cursor']);self.assertFalse(nextchange['reset']);self.assertEqual(nextchange['project_updates'][0]['goal'],p['goal'])
        self.assertIsNone(self.changes(nextchange['cursor'])['operations'])
    def test_hook_before_project_unmapped_reprojection(self):
        event=self.hook();self.assertEqual(self.record('hook',dict(actor_id='Alice',environment_id=self.refs['Alice']['environment_id'],event=event))[0],200)
        before=self.changes();self.assertTrue(before['project_updates'][0]['id'].startswith('unmapped-'));self.seed();after=self.changes(before['cursor']);self.assertTrue(after['reset']);self.assertFalse(any(p['id'].startswith('unmapped-') for p in after['project_updates']));self.assertEqual(after['operations']['sessions'][0]['source_project_id'],event['project_id']);self.assertEqual(after['operations']['sessions'][0]['project_id'],self.project['id'])
    def test_idempotency_and_restart(self):
        self.seed();event=self.hook();code,ack,envelope=self.record('hook',dict(actor_id='Alice',environment_id=self.refs['Alice']['environment_id'],event=event));self.assertEqual(code,200)
        restarted=service.LiveStore(self.root/'central',self.registry,clock=lambda:self.clock)
        self.assertEqual(restarted.apply(envelope,restarted.authenticate(TOKENS['Alice'])),ack)
        self.assertEqual(self.call('/api/records',envelope,TOKENS['Alice'])[2],common.encode(ack))
        changes=self.changes();self.assertEqual(len(changes['operations']['sessions'][0]['event_ids']),1)
    def test_event_id_content_collision(self):
        self.seed();code,_,envelope=self.record('project',dict(self.project,goal='new'),revision=1);self.assertEqual(code,200);envelope['payload']['goal']='other'
        self.assertEqual(self.call('/api/records',envelope,TOKENS['Alice'])[0],409)
    def test_native_event_dedup_and_collision(self):
        event=self.hook();payload=dict(actor_id='Alice',environment_id=self.refs['Alice']['environment_id'],event=event)
        self.assertEqual(self.record('hook',payload)[0],200);self.assertEqual(self.record('hook',payload)[0],200)
        payload=copy.deepcopy(payload);payload['event']['observed_at']='2026-10-02T10:00:00Z';self.assertEqual(self.record('hook',payload)[0],409)
    def test_stale_revision(self):self.seed();self.assertEqual(self.record('project',dict(self.project,goal='stale'),revision=0)[0],409)
    def test_wrong_source_token(self):
        event=self.hook('Bob');self.assertEqual(self.record('hook',dict(actor_id='Bob',environment_id=self.refs['Bob']['environment_id'],event=event))[0],403)
    def test_unauthorized_reads(self):
        self.assertEqual(self.call('/api/status')[0],401);self.assertEqual(self.call('/api/changes?after=0',token=TOKENS['Alice'])[0],403);self.assertEqual(self.call('/api/status',token='wrong-token-0123456789')[0],401)
    def test_login_cookie_and_csrf(self):
        self.assertEqual(self.call('/api/login',dict(token=TOKENS['manager']))[0],403)
        code,headers,_=self.call('/api/login',dict(token=TOKENS['manager']),headers={'Origin':self.url});self.assertEqual(code,200);cookie=headers['Set-Cookie'];self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=Strict',cookie)
        cookie=cookie.split(';')[0];self.assertEqual(self.call('/api/status',headers={'Cookie':cookie})[0],200)
        self.assertEqual(self.call('/api/records',{},headers={'Cookie':cookie,'Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.call('/api/changes?after=0',token=TOKENS['manager'],headers={'Origin':'https://evil.example'})[0],403)
    def test_nonloopback_without_tls(self):
        with self.assertRaises(common.TransportError):service.make_server(self.store,'0.0.0.0',0)
    def test_storage_failure_previous_state_preserved(self):
        self.seed();before=common.read_private(self.store.path,service.MAX_STATE)
        with patch.object(common,'write_private',side_effect=common.TransportError('storage_failed',503)):
            self.assertEqual(self.record('project',dict(self.project,goal='fail'),revision=1)[0],503)
        self.assertEqual(common.read_private(self.store.path,service.MAX_STATE),before)
    def test_corrupt_private_state_fails_restart(self):
        common.write_private(self.store.path,b'{"version":1')
        with self.assertRaises(common.TransportError):service.LiveStore(self.root/'central',self.registry)
    def test_peer_task_owner_mutation_and_update(self):
        self.seed();p=copy.deepcopy(self.project);t=next(t for t in p['management']['work']['tasks'] if t['owner']=='Bob');t['owner']='Alice'
        p['management']['work']['updates'].append(dict(id='steal-update',task_id=t['id'],at=sample.NOW,state='in_progress',summary='steal',next_action='steal'))
        self.assertEqual(self.record('project',p,revision=1)[0],403)
    def test_peer_documents_and_attempts_protected(self):
        self.seed();p=copy.deepcopy(self.project);bob=self.refs['Bob'];attempt=copy.deepcopy(p['management']['attempts'][0]);attempt.update(id='bob-evidence',actor_id='Bob',environment_id=bob['environment_id']);p['management']['attempts'].append(attempt)
        self.assertEqual(self.record('project',p,'manager',1)[0],200);q=copy.deepcopy(p);q['management']['attempts']=[a for a in q['management']['attempts'] if a['id']!='bob-evidence'];self.assertEqual(self.record('project',q,revision=2)[0],403)
    def test_source_refs_immutable_writer(self):
        self.seed();p=copy.deepcopy(self.project);p['source_refs']=[self.refs['Alice']];self.assertEqual(self.record('project',p,revision=1)[0],403)
    def test_unregistered_source_manager(self):
        p=copy.deepcopy(self.project);p['source_refs'].append(dict(actor_id='Eve',environment_id='eve',project_id='99999999-9999-4999-8999-999999999999'));self.assertEqual(self.record('project',p,'manager')[0],403)
    def test_writer_first_shared_project_denied(self):self.assertEqual(self.record('project',self.project)[0],403)
    def test_manager_only_metric(self):self.seed();self.assertEqual(self.record('north_star',self.records['north_stars'][0])[0],403);self.assertEqual(self.record('north_star',self.records['north_stars'][0],'manager')[0],200)
    def test_session_acceptance_actor(self):
        self.seed();s=copy.deepcopy(self.records['sessions'][0]);s['acceptance']['actor_id']='Bob';self.assertEqual(self.record('session',s)[0],403)
    def test_capture_clock_freshness_changes(self):
        self.seed();capture=copy.deepcopy(self.records['capture'][0]);self.assertEqual(self.record('capture',capture)[0],200);before=self.changes();self.assertEqual(before['operations']['capture'][0]['freshness'],'recent');self.clock='2026-10-02T12:01:00Z';after=self.changes(before['cursor']);self.assertGreater(after['cursor'],before['cursor']);self.assertEqual(after['operations']['capture'][0]['freshness'],'stale')
    def test_manager_confirmation_matches_actor(self):
        self.seed();self.assertEqual(self.record('session',self.records['sessions'][0])[0],200);self.assertEqual(self.record('north_star',self.records['north_stars'][1],'manager')[0],200)
        c=copy.deepcopy(self.records['contributions'][1]);c['confirmed_by']='Bob';self.assertEqual(self.record('contribution',c,'manager')[0],403);c['confirmed_by']='Alice';self.assertEqual(self.record('contribution',c,'manager')[0],200)
    def test_duplicate_json_utf8(self):
        headers={'Authorization':'Bearer '+TOKENS['Alice']}
        for raw in [b'{"version":1,"version":1}',b'\xff']:
            req=Request(self.url+'/api/records',data=raw,headers=headers)
            with self.assertRaises(HTTPError) as error:urlopen(req)
            self.assertEqual(error.exception.code,400)
    def sender_config(self,name='Alice',url=None):
        root=self.root/name;root.mkdir(mode=0o700);logs=root/'logs';logs.mkdir(mode=0o700);token=root/'token';common.write_private(token,TOKENS[name].encode())
        return dict(version=1,url=url or self.url,actor_id=name,environment_id=self.refs[name]['environment_id'],project_ids=[self.refs[name]['project_id']],token_file=str(token),logdir=str(logs),catalog=None,operations=None,outbox=str(root/'outbox'),loopback_test=True)
    def test_sender_offline_restart_and_partial_line(self):
        config=self.sender_config(url='http://127.0.0.1:1');logs=Path(config['logdir']);event=self.hook();common.write_private(logs/'events.jsonl',common.encode(event)+b'\n'+b'{"unfinished":')
        first=sender.Sender(config);state=first.tick();self.assertEqual(sum(q['envelope']['kind']=='hook' for q in first.read()['queue']),1);self.assertEqual(state['pending'],2);config['url']=self.url
        restarted=sender.Sender(config);self.assertEqual(restarted.tick()['pending'],0);self.assertEqual(len(self.changes()['operations']['sessions']),1)
    def test_sender_two_writer_delivery(self):
        self.seed()
        for name in ('Alice','Bob'):
            config=self.sender_config(name);common.write_private(Path(config['logdir'])/'events.jsonl',common.encode(self.hook(name))+b'\n');self.assertEqual(sender.Sender(config).tick()['pending'],0)
        self.assertEqual({s['actor_id'] for s in self.changes()['operations']['sessions']},{'Alice','Bob'})
    def test_sender_project_diff_conflict_and_deletion(self):
        self.seed();config=self.sender_config();catalog=Path(config['logdir']).parent/'catalog.json';common.write_private(catalog,common.encode({'version':3,'projects':[self.project]}));config['catalog']=str(catalog);watch=sender.Sender(config)
        self.assertEqual(watch.tick()['conflicts'],1);self.assertEqual(watch.tick()['conflicts'],1)
        common.write_private(catalog,common.encode({'version':3,'projects':[]}));self.assertTrue(any(e['code']=='deletion_unsupported' for e in watch.tick()['errors']))
    def test_sender_project_diff_success_restarted(self):
        self.seed();config=self.sender_config();catalog=Path(config['logdir']).parent/'catalog.json';common.write_private(catalog,common.encode({'version':3,'projects':[self.project]}));config['catalog']=str(catalog);config['base_revisions']={'project:'+self.project['id']:1};watch=sender.Sender(config);self.assertEqual(watch.tick()['pending'],0)
        p=copy.deepcopy(self.project);p['goal']='new incremental';common.write_private(catalog,common.encode({'version':3,'projects':[p]}));watch=sender.Sender(config);self.assertEqual(watch.tick()['pending'],0);self.assertEqual(self.changes()['project_updates'][0]['goal'],p['goal']);self.assertEqual(watch.read()['revisions']['project:'+p['id']],3)
    def test_sender_health_context(self):
        config=self.sender_config();event=self.hook();logs=Path(config['logdir']);common.write_private(logs/'events.jsonl',common.encode(event)+b'\n');health=dict(version=1,last_event_id=event['event_id'],last_recorded_at=event['observed_at'],errors=0,last_failure_at=None,status='observed',at=sample.NOW);common.write_private(logs/'capture-health.json',common.encode(health));watch=sender.Sender(config);self.assertEqual(watch.tick()['pending'],0);self.assertEqual(len(self.changes()['operations']['capture']),1)
        health['last_event_id']='99999999-9999-4999-8999-999999999999';common.write_private(logs/'capture-health.json',common.encode(health));self.assertTrue(any(e['code']=='health_context_unmapped' for e in watch.tick()['errors']))
    def test_source_uuid_collision_two_writers(self):
        alice=self.hook();bob=self.hook('Bob');bob['event_id']=alice['event_id']
        for name,event in [('Alice',alice),('Bob',bob)]:
            config=self.sender_config(name);common.write_private(Path(config['logdir'])/'events.jsonl',common.encode(event)+b'\n');self.assertEqual(sender.Sender(config).tick()['pending'],0)
        self.assertEqual(len(self.changes()['operations']['sessions']),2)
    def test_same_writer_raw_uuid_collision_and_health_ambiguity(self):
        config=self.sender_config();raw='99999999-9999-4999-8999-999999999999';config['project_ids'].append(raw);self.store.registry['writers'][0]['project_ids'].append(raw)
        a=self.hook();b=copy.deepcopy(a);b['project_id']=raw;common.write_private(Path(config['logdir'])/'events.jsonl',common.encode(a)+b'\n'+common.encode(b)+b'\n')
        health=dict(version=1,last_event_id=a['event_id'],last_recorded_at=a['observed_at'],errors=0,last_failure_at=None,status='observed',at=sample.NOW);common.write_private(Path(config['logdir'])/'capture-health.json',common.encode(health))
        watcher=sender.Sender(config);self.assertEqual(watcher.tick()['pending'],0);view=self.changes()['operations'];self.assertEqual(len(view['sessions']),2);self.assertEqual(len(view['capture']),2);self.assertTrue(all(c['status']=='unknown' for c in view['capture']))
    def test_baseline_noop_shared_project_two_writers(self):
        self.seed()
        for name in ('Alice','Bob'):
            config=self.sender_config(name);catalog=Path(config['logdir']).parent/'catalog.json';common.write_private(catalog,common.encode({'version':3,'projects':[self.project]}));config.update(catalog=str(catalog),base_revisions={'project:'+self.project['id']:1},base_hashes={'project:'+self.project['id']:common.digest(common.encode(self.project))})
            self.assertEqual(sender.Sender(config).tick()['pending'],0)
        self.assertEqual(self.store.read()['revisions']['project:'+self.project['id']],1)
    def test_conflict_isolated_other_entities_delivered(self):
        self.seed();config=self.sender_config();catalog=Path(config['logdir']).parent/'catalog.json';common.write_private(catalog,common.encode({'version':3,'projects':[self.project]}));config['catalog']=str(catalog)
        report=sender.Sender(config).tick();self.assertEqual(report['conflicts'],1);self.assertEqual(len(self.changes()['operations']['capture']),1)
    def test_missing_corrupt_health_central_projection(self):
        config=self.sender_config();logs=Path(config['logdir']);common.write_private(logs/'events.jsonl',common.encode(self.hook())+b'\n');watcher=sender.Sender(config);self.assertEqual(watcher.tick()['pending'],0);self.assertEqual(self.changes()['operations']['capture'][0]['status'],'unknown')
        event=self.hook();health=dict(version=1,last_event_id=event['event_id'],last_recorded_at=event['observed_at'],errors=0,last_failure_at=None,status='observed',at=event['observed_at']);common.write_private(logs/'capture-health.json',common.encode(health));self.assertEqual(watcher.tick()['pending'],0);self.assertEqual(self.changes()['operations']['capture'][0]['status'],'observed')
        common.write_private(logs/'capture-health.json',b'{bad');self.assertEqual(watcher.tick()['pending'],0);self.assertEqual(self.changes()['operations']['capture'][0]['status'],'degraded')
        (logs/'events.jsonl').unlink();(logs/'capture-health.json').unlink();self.assertEqual(sender.Sender(config).tick()['pending'],0);capture=self.changes()['operations']['capture'];self.assertTrue(any(c['source']==event['source'] and c['status']=='unknown' for c in capture));self.assertFalse(any(c['status']=='observed' for c in capture))
    def test_peer_same_actor_other_environment_history(self):
        self.seed();p=copy.deepcopy(self.project);a=copy.deepcopy(p['management']['attempts'][0]);a.update(id='desktop-proof',environment_id='desktop');p['management']['attempts'].append(a);self.assertEqual(self.record('project',p,'manager',1)[0],200)
        p['management']['attempts']=[a for a in p['management']['attempts'] if a['id']!='desktop-proof'];self.assertEqual(self.record('project',p,revision=2)[0],403)
    def test_anon_shell_empty_login_only(self):
        self.seed();code,headers,raw=self.call('/');self.assertEqual(code,200);self.assertIn(b'data-live="true"',raw);model=json.loads(raw.decode().split('id="pms-data" type="application/json">')[1].split('</script>')[0]);self.assertEqual(model['projects'],[]);self.assertEqual(model['operations']['sessions'],[]);self.assertEqual(model['evidence_mode'],'synthetic');self.assertIn("connect-src 'self'",headers['Content-Security-Policy'])
    def test_semantic_history_survives_replacement_restart(self):
        self.seed();p=copy.deepcopy(self.project);p['goal']='새 목표';self.assertEqual(self.record('project',p,revision=1)[0],200)
        restarted=service.LiveStore(self.root/'central',self.registry,clock=lambda:self.clock);history=restarted.history(0);self.assertEqual([r['payload']['goal'] for r in history['records']],[self.project['goal'],'새 목표'])
        self.assertEqual(self.call('/api/history?after=0',token=TOKENS['Alice'])[0],403);self.assertEqual(self.call('/api/history?after=0',token=TOKENS['manager'])[0],200)
    def test_sender_url_security(self):
        config=self.sender_config()
        for url in ['http://example.com','https://alice:secret@example.com','https://example.com?token=secret']:
            config['url']=url
            with self.assertRaises(common.TransportError):sender.Sender(config)
    def test_sender_no_redirect(self):
        with self.assertRaises(sender.common.TransportError):sender.NoRedirect().redirect_request(None,None,None,None,None,None)
    def test_sender_symlink_preserved(self):
        config=self.sender_config();target=self.root/'outside';target.write_text('secret');Path(config['logdir'],'events.jsonl').symlink_to(target);watch=sender.Sender(config);self.assertTrue(any(e['code']=='log_unavailable' for e in watch.tick()['errors']));self.assertEqual(target.read_text(),'secret')

if __name__=='__main__':unittest.main()
