#!/usr/bin/env python3
"""Counterexamples against false completion and stale approval; no live attestations."""
import copy
import importlib.util
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
sample=load('work_sample',HERE/'generate_sample.py');work=sample.work;m=sample.m
portfolio=load('work_portfolio',HERE.parent/'ai-pms-dashboard/portfolio.py')
NOW=sample.NOW

class WorkTests(unittest.TestCase):
    def setUp(self):self.p=sample.make_catalog()['projects'][0];self.w=self.p['management']['work'];self.m=self.p['management']
    def derive(self):return work.derive(self.p,NOW)
    def t(self,n=0):return self.derive()['tasks'][n]
    def approve(self):
        t=self.w['tasks'][1];self.w['reviews']=[dict(id='review-one',task_id=t['id'],at='2026-09-29T05:00:00Z',reviewer='Alice',decision='approved',summary='합성 사람 검토',artifact_sha256=self.m['artifact']['sha256'],task_sha256=work.task_digest(self.p,t))]
    def reject(self,mutate):
        mutate()
        with self.assertRaises(ValueError):m.validate(self.p)
    def test_shared_people_many_projects(self):
        model=portfolio.build_model(catalog=sample.make_catalog(),now=NOW)
        self.assertGreaterEqual(sum('Alice' in p['owners'] for p in model['projects']),2)
        self.assertEqual(model['projects'][0]['owners'],['Alice','Bob']);self.assertEqual(self.t(2)['owner'],'Bob')
        self.assertTrue(all(i['next_action'] for i in self.derive()['interventions']))
    def test_mixed_states(self):self.assertEqual([t['state'] for t in self.derive()['tasks']],['complete','review_pending','blocked','ready','in_progress','unknown','unknown'])
    def test_dependencies_even_pass(self):
        self.w['tasks'][0]['depends_on']=['action-3'];self.assertEqual(self.t()['state'],'blocked');self.assertTrue(self.t()['technical_complete']);self.assertFalse(self.t()['completed'])
    def test_missing_gate_taskless_optional_phase(self):
        self.w['phase_gates']=[];self.assertEqual(self.derive()['phases'][0]['state'],'unknown')
        self.p['phases'].append(dict(id='empty',name='미관측 단계'));self.assertEqual(self.derive()['phases'][1]['state'],'unknown')
        catalog=dict(version=3,projects=[self.p]);self.assertNotEqual(portfolio.build_model(catalog=catalog,now=NOW)['projects'][0]['status'],'complete')
    def test_optional_denominator(self):
        self.w['tasks'][0]['required']=False;self.assertEqual(self.derive()['summary']['required'],6);self.assertEqual(self.derive()['summary']['completed'],0)
    def test_future_plan(self):self.w['at']='2027-01-01T00:00:00Z';self.assertFalse(any(t['completed'] for t in self.derive()['tasks']));self.assertTrue(all(p['state']=='unknown' for p in self.derive()['phases']))
    def test_declared_receipt_cannot_pass(self):self.m['attempts'][0]['provenance']='declared';self.assertFalse(self.t()['completed'])
    def test_newer_unknown_does_not_hide_behind_pass(self):
        a=copy.deepcopy(self.m['attempts'][0]);a.update(id='newer',at='2026-09-29T06:00:00Z',exit_code=None);self.m['attempts'].append(a);self.assertFalse(self.t()['completed'])
    def test_conflicting_receipts(self):
        a=copy.deepcopy(self.m['attempts'][0]);a.update(id='conflict',exit_code=1);self.m['attempts'].append(a);self.assertFalse(self.t()['completed'])
    def test_future_receipt_ignored(self):self.m['attempts'][0]['at']='2027-01-01T00:00:00Z';self.assertFalse(self.t()['completed'])
    def test_stale_artifact_and_revision(self):
        self.m['attempts'][0]['artifact_sha256']='0'*64;self.assertEqual(self.t()['state'],'revalidation');self.m['attempts'][0]['revision']='old';self.assertFalse(self.t()['completed'])
    def test_receipt_before_plan(self):self.w['at']='2026-09-29T04:30:00Z';self.assertEqual(self.t()['state'],'revalidation')
    def test_review_fresh_and_changes(self):
        self.approve();self.assertEqual(self.t(1)['state'],'complete');self.w['reviews'][0]['decision']='changes_requested';self.assertEqual(self.t(1)['state'],'changes_requested')
    def test_review_changed_task(self):self.approve();self.w['tasks'][1]['done_when']=['개정된 조건'];self.assertEqual(self.t(1)['state'],'review_pending')
    def test_review_old_artifact(self):self.approve();self.w['reviews'][0]['artifact_sha256']='0'*64;self.assertEqual(self.t(1)['state'],'review_pending')
    def test_review_before_plan_or_testplan(self):self.approve();self.w['reviews'][0]['at']='2026-09-29T00:00:00Z';self.assertEqual(self.t(1)['state'],'review_pending')
    def test_same_time_review_conflict(self):
        self.approve();r=copy.deepcopy(self.w['reviews'][0]);r.update(id='conflict',decision='changes_requested');self.w['reviews'].append(r);self.assertEqual(self.t(1)['state'],'review_pending')
    def test_digest_binds_full_criterion_and_testplan(self):
        self.approve();old=self.w['reviews'][0]['task_sha256'];tp=self.m['test_plans'][1];tp['reason']='같은 ID 정의의 검사 이유 개정';self.assertNotEqual(old,work.task_digest(self.p,self.w['tasks'][1]))
        # Update receipt identity to valid new definition; old review still cannot approve.
        a=self.m['attempts'][1];a['test_plan_sha256']=m.test_plan_sha256(tp);self.assertEqual(self.t(1)['state'],'review_pending')
        self.p['criteria'][1]['label']='개정 기준';tp['definition']=copy.deepcopy(self.p['criteria'][1]);a['criterion_signature']=m.criterion_signature(tp['definition']);a['test_plan_sha256']=m.test_plan_sha256(tp);self.assertEqual(self.t(1)['state'],'review_pending')
    def test_equal_update_conflict(self):
        u=copy.deepcopy(self.w['updates'][0]);u.update(id='conflict',state='in_progress');self.w['updates'].append(u);self.assertEqual(self.t(2)['state'],'unknown')
    def test_missing_owner_acceptance(self):self.assertEqual(self.t(5)['state'],'unknown');self.assertEqual(self.t(6)['state'],'unknown')
    def test_bad_refs_cycle_and_exact_keys(self):
        for field,value in [('depends_on',['absent']),('owner','Stranger'),('document_ids',['absent']),('criterion_ids',['project-exit'])]:
            fresh=copy.deepcopy(self.p);fresh['management']['work']['tasks'][0][field]=value
            with self.assertRaises(ValueError):m.validate(fresh)
        self.reject(lambda:self.w['tasks'][0]['depends_on'].append('action-1'))
    def test_cycle(self):self.w['tasks'][0]['depends_on']=['action-2'];self.reject(lambda:self.w['tasks'][1]['depends_on'].append('action-1'))
    def test_unresolved_relevant_blocker(self):
        self.m['blockers']=[dict(id='block',status='open',summary='검사 해석 지원',cause_state='hypothesis',cause='검사 범위 확인 필요',attempt_ids=[self.m['attempts'][0]['id']],owner='Alice',next_action='검사 결과를 담당자와 해석하세요.',resolved_by=None)]
        self.assertEqual(self.t()['state'],'blocked');self.assertEqual(next(i for i in self.derive()['interventions'] if i['task_id']=='action-1')['next_action'],'검사 결과를 담당자와 해석하세요.')
    def test_project_blocker_not_misattributed(self):
        self.m['blockers']=[dict(id='project-block',status='open',summary='프로젝트 승인 범위 확인',cause_state='hypothesis',cause='범위 확인',attempt_ids=[self.m['attempts'][-1]['id']],owner='Alice',next_action='관리자가 프로젝트 범위를 확인하세요.',resolved_by=None)]
        i=next(i for i in self.derive()['interventions'] if i['id']=='blocked-project-block');self.assertIsNone(i['owner']);self.assertIsNone(i['task_id'])
    def complete_fixture(self):
        self.w['tasks']=self.w['tasks'][:1];self.w['updates']=[];keep={'action-1-check','phase-exit','project-exit'}
        self.p['criteria']=[c for c in self.p['criteria'] if c['id'] in keep];self.m['test_plans']=[t for t in self.m['test_plans'] if t['criterion_id'] in keep]
        tpids={t['id'] for t in self.m['test_plans']};self.m['attempts']=[a for a in self.m['attempts'] if a['test_plan_id'] in tpids]
    def project_model(self):return portfolio.build_model(catalog=dict(version=3,projects=[self.p]),now=NOW)['projects'][0]
    def test_new_project_declaration_masks_old_pass(self):
        self.complete_fixture();self.assertEqual(self.project_model()['status'],'complete')
        tp=next(tp for tp in self.m['test_plans'] if tp['criterion_id']=='project-exit');a=copy.deepcopy(next(a for a in self.m['attempts'] if a['test_plan_id']==tp['id']));a.update(id='new-declared',at='2026-09-29T06:00:00Z',started_at='2026-09-29T06:00:00Z',provenance='declared',exit_code=None);self.m['attempts'].append(a)
        self.assertNotEqual(self.project_model()['status'],'complete')
    def test_upper_scope_blockers_block_completion(self):
        for scope in ('project','phase'):
            self.setUp();self.complete_fixture()
            tp=next(tp for tp in self.m['test_plans'] if tp['definition']['scope']==scope);a=next(a for a in self.m['attempts'] if a['test_plan_id']==tp['id'])
            self.m['blockers'].append(dict(id='upper-block',status='open',summary='상위 인수 판단 대기',cause_state='hypothesis',cause='정책 확인',attempt_ids=[a['id']],owner='Alice',next_action='관리자가 정책을 확인하세요.',resolved_by=None))
            self.assertNotEqual(self.project_model()['status'],'complete')
            if scope=='phase':self.assertEqual(self.project_model()['work']['phases'][0]['state'],'blocked')
    def test_complete_requires_every_phase_and_project_gate(self):
        self.w['tasks']=self.w['tasks'][:1];self.w['updates']=[];keep={'action-1-check','phase-exit','project-exit'};self.p['criteria']=[c for c in self.p['criteria'] if c['id'] in keep];self.m['test_plans']=[t for t in self.m['test_plans'] if t['criterion_id'] in keep];tpids={t['id'] for t in self.m['test_plans']};self.m['attempts']=[a for a in self.m['attempts'] if a['test_plan_id'] in tpids]
        model=lambda:portfolio.build_model(catalog=dict(version=3,projects=[self.p]),now=NOW)['projects'][0]
        self.assertEqual(model()['status'],'complete');self.p['phases'].append(dict(id='optional-only',name='추가 단계'));self.assertNotEqual(model()['status'],'complete')

if __name__=='__main__':unittest.main()
