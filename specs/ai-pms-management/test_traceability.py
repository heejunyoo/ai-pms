#!/usr/bin/env python3
"""Trace links validate identity but never change configured completion."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('trace_generator',Path(__file__).with_name('generate_sample.py'))
generator=importlib.util.module_from_spec(s);s.loader.exec_module(generator)
management=generator.management

class TraceContract(unittest.TestCase):
    def setUp(self):
        self.p=generator.make_catalog()['projects'][0];self.m=self.p['management'];self.t=self.m['traceability']
    def reject(self):
        with self.assertRaises(ValueError): management.validate(self.p)
    def test_optional_and_empty_compatible(self):
        original=management.derive(self.p,'2026-10-01T00:00:00Z')[0]
        self.m.pop('traceability');self.assertEqual(original,management.derive(self.p,'2026-10-01T00:00:00Z')[0])
        self.m['traceability']={k:[] for k in ('checkpoints','decisions','handoffs','capture')};management.validate(self.p)
    def test_preserved_without_promoting_future_evidence(self):
        for r in self.t['checkpoints']+self.t['decisions']+self.t['capture']:r['at']='2030-01-01T00:00:00Z'
        self.assertEqual(management.derive(self.p,'2026-10-01T00:00:00Z')[1]['traceability'],self.t)
    def test_checkpoint_artifact_revision_matches_attempt(self):
        for field,value in [('revision','different'),('artifact_sha256','0'*64)]:
            with self.subTest(field=field):
                c=self.t['checkpoints'][0];old=c[field];c[field]=value;self.reject();c[field]=old
    def test_checkpoint_does_not_require_current_revision(self):
        self.m['attempts'][0]['revision']='previous'
        c=self.t['checkpoints'][0];c['revision']='previous';c['attempt_ids']=[self.m['attempts'][0]['id']];management.validate(self.p)
    def test_missing_and_duplicate_references(self):
        for field in ('attempt_ids','decision_ids'):
            c=self.t['checkpoints'][0];old=c[field]
            for value in [['missing'],old+old]:
                c[field]=value;self.reject()
            c[field]=old
    def test_source_tuple_not_cross_project(self):
        for field,value in [('actor_id','Other'),('environment_id','Other')]:
            c=self.t['checkpoints'][0];old=c[field];c[field]=value;self.reject();c[field]=old
        self.t['handoffs'][0]['to_environment_id']='Other';self.reject()
    def test_identifier_agent_and_session(self):
        self.t['checkpoints'][0]['agent_id']=None;management.validate(self.p)
        self.t['checkpoints'][0]['session_id']='invalid session';self.reject()
    def test_git_hash_and_exact_types(self):
        c=self.t['checkpoints'][0]
        for field,value in [('commit','A'*40),('parent_commits',['0'*39]),('dirty',1),('worktree_sha256','bad')]:
            old=c[field];c[field]=value;self.reject();c[field]=old
        c['commit']='a'*64;management.validate(self.p)
    def test_no_git_invariants(self):
        c=self.t['checkpoints'][0];c.update(commit=None,parent_commits=[],dirty=None,worktree_sha256=None);management.validate(self.p)
        for field,value in [('parent_commits',['0'*40]),('dirty',False),('worktree_sha256','0'*64)]:
            c[field]=value;self.reject();c[field]=[] if field=='parent_commits' else None
    def test_decision_cycle_and_missing_parent(self):
        d=self.t['decisions'][0];d['supersedes']='missing';self.reject()
        d['supersedes']=d['id'];self.reject()
        d['supersedes']=None;second=copy.deepcopy(d);second['id']='next';second['supersedes']=d['id'];self.t['decisions'].append(second)
        management.validate(self.p);d['supersedes']='next';self.reject()
    def test_decision_explicit_rationale(self):
        d=self.t['decisions'][0]
        for field,value in [('alternatives',[]),('alternatives',[' ']),('reason',' '),('provenance','observed'),('requirement_ids',['missing'])]:
            old=d[field];d[field]=value;self.reject();d[field]=old
    def test_usage_requires_evidence_and_order(self):
        h=self.t['handoffs'][0]
        for field,value in [('usage_at',None),('usage_evidence',None),('usage_at','2026-09-29T05:00:00Z'),('usage','installed')]:
            old=h[field];h[field]=value;self.reject();h[field]=old
        h.update(usage='not_observed',usage_at=None,usage_evidence=None);management.validate(self.p)
        h['usage_evidence']='exported';self.reject()
    def test_same_session_handoff_rejected(self):
        self.t['handoffs'][0]['to_session_id']=self.t['handoffs'][0]['from_session_id'];self.reject()
    def test_capture_is_reported_not_live(self):
        c=self.t['capture'][0];c.update(status='unsupported',capabilities=[]);management.validate(self.p)
        c['capabilities']=['tests'];self.reject()
    def test_capture_capabilities_and_time(self):
        c=self.t['capture'][0]
        for field,value in [('capabilities',['memory','memory']),('capabilities',['secrets']),('last_observed_at','2030-01-01T00:00:00Z'),('status','connected'),('provenance','inferred')]:
            old=c[field];c[field]=value;self.reject();c[field]=old
    def test_private_text_and_unknown_fields_rejected(self):
        d=self.t['decisions'][0]
        for value in ['token=abcdefghijk','access_token=abcdefghijklmnopqrstuvwxyz','access-token=abcdefghijklmnopqrstuvwxyz','/home/example/private','Bearer abcdefghijkl']:
            d['reason']=value;self.reject()
        d['reason']='explicit reason';self.t['capture'][0]['extra']='unknown';self.reject()
    def test_record_duplicate_ids(self):
        for field in self.t:
            self.t[field].append(copy.deepcopy(self.t[field][0]));self.reject();self.t[field].pop()
    def test_trace_fields_exact(self):
        self.t['extra']=[];self.reject();self.t.pop('extra')
        self.t['decisions'][0].pop('reason');self.reject()
    def test_synthetic_three_paths(self):
        a,b,c=generator.make_catalog()['projects'][:3]
        self.assertEqual(a['management']['traceability']['handoffs'][0]['usage'],'observed')
        self.assertEqual(b['management']['traceability']['capture'][0]['status'],'degraded')
        self.assertIsNone(c['management']['traceability']['checkpoints'][0]['commit'])
        self.assertEqual(c['management']['traceability']['capture'][0]['status'],'paused')

if __name__=='__main__':unittest.main()
