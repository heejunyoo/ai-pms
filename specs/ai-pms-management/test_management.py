#!/usr/bin/env python3
"""Meaningful mutation checks for offline management and legacy compatibility."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('portfolio',ROOT/'ai-pms-dashboard'/'portfolio.py');portfolio=importlib.util.module_from_spec(s);s.loader.exec_module(portfolio)
management=portfolio.management
s=importlib.util.spec_from_file_location('generate_sample',Path(__file__).with_name('generate_sample.py'));generator=importlib.util.module_from_spec(s);s.loader.exec_module(generator)
NOW='2026-10-01T00:00:00Z'

class Contract(unittest.TestCase):
    def setUp(self): self.catalog=generator.make_catalog(); self.p=self.catalog['projects'][0]; self.m=self.p['management']
    def model(self): return portfolio.build_model(catalog=self.catalog,now=NOW)
    def reject(self):
        with self.assertRaises(ValueError): self.model()
    def test_sample_purpose(self):
        model=self.model(); a,b,c=model['projects'][:3]
        self.assertEqual(model['schema_version'],3);self.assertEqual((a['status'],b['status'],c['status']),('complete','failed','revalidation'))
        self.assertEqual(a['management']['assignment']['kind'],'outcome');self.assertEqual(b['management']['assignment']['kind'],'task');self.assertIsNone(c['management']['assignment'])
        self.assertEqual(a['management']['blockers'][0]['verification'],'current');self.assertEqual(c['management']['graphs'][0]['freshness'],'stale')
        self.assertTrue(all(t['test_files'] for t in a['management']['test_plans']))
    def test_synthetic_sample_reproducible(self):
        self.assertEqual(self.catalog,json.loads((Path(__file__).parent/'sample'/'catalog-v3.json').read_text()))
    def test_objective_cycle(self): self.m['objectives'][0]['parent_id']=self.m['objectives'][0]['id'];self.reject()
    def test_parent_stable_across_versions(self):
        a=self.m['objectives'][0];b=copy.deepcopy(a);b['version']='v2';b['parent_id']=a['id'];self.m['objectives'].append(b);self.reject()
    def test_assignee_owner(self): self.m['assignment']['assignee']='Unknown';self.reject()
    def test_assignment_version(self): self.m['assignment']['objective_version']='v7';self.reject()
    def test_plan_requirement_reference(self): self.m['plans'][0]['requirement_ids']=['missing'];self.reject()
    def test_latest_criterion_coverage(self): self.m['test_plans'].pop();self.reject()
    def test_definition_changed_without_plan(self): self.p['criteria'][0]['command']='python3 changed.py';self.reject()
    def test_hash_command_signature_reject(self):
        for field,value in [('command','python3 invalid.py'),('test_plan_sha256','0'*64),('criterion_signature','0'*64)]:
            with self.subTest(field=field):
                a=self.m['attempts'][0];old=a[field];a[field]=value;self.reject();a[field]=old
    def test_current_artifact_stale(self):
        self.m['artifact']['files'][0]['sha256']='0'*64;self.m['artifact']['sha256']=management.artifact_sha256(self.m['artifact']['files'])
        model=self.model()['projects'][0];self.assertEqual(model['status'],'revalidation');self.assertEqual(model['management']['blockers'][0]['verification'],'revalidation');self.assertTrue(all(a['status']=='unknown' for a in model['management']['attempts']))
    def test_test_file_hash_stale_even_current_attempt_manifest(self):
        self.m['artifact']['files'][0]['sha256']='0'*64;self.m['artifact']['sha256']=management.artifact_sha256(self.m['artifact']['files'])
        for a in self.m['attempts']: a['artifact_sha256']=self.m['artifact']['sha256']
        self.assertEqual(self.model()['projects'][0]['status'],'revalidation')
    def test_new_plan_version_same_definition_requires_revalidation(self):
        tp=copy.deepcopy(self.m['test_plans'][0]);tp['version']='v2';tp['at']='2026-09-30T00:00:00Z';tp['reason']='추가 실패 원인을 반영하여 검사 계획 개정';self.m['test_plans'].append(tp)
        p=self.model()['projects'][0]
        self.assertEqual(p['status'],'revalidation');self.assertEqual(p['management']['blockers'][0]['verification'],'revalidation')
        self.assertTrue(all(a['status']=='unknown' for a in p['management']['attempts'] if a['test_plan_id']==tp['id']))
    def test_declared_not_complete(self):
        self.m['blockers']=[]
        for a in self.m['attempts']: a['provenance']='declared'
        p=self.model()['projects'][0];self.assertNotEqual(p['status'],'complete');self.assertEqual(p['runs'],[]);self.assertTrue(all(a['status']=='unknown' for a in p['management']['attempts']))
    def test_future_unknown(self):
        for a in self.m['attempts']: a['at']='2027-01-01T00:00:00Z'
        p=self.model()['projects'][0];self.assertNotEqual(p['status'],'complete');self.assertEqual(p['management']['blockers'][0]['verification'],'unknown')
    def test_historical_revision_does_not_complete_current(self):
        for a in self.m['attempts']: a['revision']='old'
        p=self.model()['projects'][0];self.assertEqual(p['status'],'revalidation');self.assertEqual(p['management']['attempts'][-1]['status'],'pass')
    def test_resolved_needs_runner_pass(self): self.m['blockers'][0]['resolved_by']=self.m['attempts'][0]['id'];self.reject()
    def test_unrelated_pass_does_not_resolve(self):
        self.m['blockers'][0]['resolved_by']=self.m['attempts'][-1]['id'];self.reject()
    def test_source_and_time_order(self):
        a=self.m['attempts'][0];a['actor_id']='Unknown';self.reject();a['actor_id']='Alice';a['started_at']='2027-01-01T00:00:00Z';self.reject()
    def test_manifest_and_relative_paths(self):
        for path in ['../outside.py','foo/../test.py','/absolute.py','./test.py','C:test.py','test\\bad.py']:
            with self.subTest(path=path):
                old=self.m['artifact']['files'][0]['path'];self.m['artifact']['files'][0]['path']=path;self.reject();self.m['artifact']['files'][0]['path']=old
        self.m['artifact']['files']=[];self.m['artifact']['sha256']=management.artifact_sha256([]);self.reject()
    def test_graph_states(self):
        g=self.m['graphs'][0]
        for status,at,expected in [('failed',NOW,'unknown'),('unknown',NOW,'unknown'),('generated','2027-01-01T00:00:00Z','unknown'),('generated',NOW,'current')]:
            g['status']=status;g['at']=at;self.assertEqual(self.model()['projects'][0]['management']['graphs'][0]['freshness'],expected)
    def test_v3_legacy_runs_rejected(self):
        self.p['runs']=[dict(criterion_id=self.p['criteria'][0]['id'],revision='v1',at=NOW,exit_code=0,session_id='x',evidence='declared',criterion_signature=management.criterion_signature(self.p['criteria'][0]))];self.reject()
    def test_extra_keys_and_private_text(self):
        self.m['goals']=[];self.reject();del self.m['goals'];self.m['plans'][0]['reason']='Bearer hidden';self.reject()
    def test_conflicting_attempts_unknown(self):
        a=copy.deepcopy(self.m['attempts'][1]);a['id']='conflict';a['exit_code']=1;self.m['attempts'].append(a)
        self.assertEqual(self.model()['projects'][0]['status'],'revalidation')
    def test_unmapped_null_and_v2(self):
        store=json.loads((ROOT/'ai-pms-dashboard'/'sample'/'central.json').read_text());model=portfolio.build_model(store,self.catalog,NOW)
        self.assertIsNone(next(p for p in model['projects'] if p['id'].startswith('unmapped-'))['management'])
        legacy=json.loads((ROOT/'ai-pms-dashboard'/'sample'/'catalog.json').read_text());old=portfolio.build_model(store,legacy,NOW)
        self.assertEqual(old['schema_version'],2);self.assertTrue(all('management' not in p for p in old['projects']))
    def test_standalone_and_shared_helpers(self):
        self.assertEqual(management.validate(self.p),management.validate(self.p,portfolio))

if __name__=='__main__': unittest.main()
