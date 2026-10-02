#!/usr/bin/env python3
"""Portable Kit work import and original-file preservation counterexamples."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
KIT=ROOT/'kit/activity' if (ROOT/'kit/activity').exists() else Path.home()/'.claude/harness/activity'
sys.path.insert(0,str(KIT))
import management_recorder as recorder
import test_management_recorder as legacy
import management,work

class KitWork(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.p=legacy.fixture(self.root)
        self.plan={'goal':'Preserve two atomic actions and phase acceptance.','spec_ref':'source.md','intent_guard':{'source_ref':'source.md','requirements':[{'id':'req','quote':'Pass the local check.'}],'acceptance':{'command':'python3 check.py','expect_exit_code':0}},'phases':[{'id':'build','name':'Build verified work','exit_check':{'command':'python3 check.py --phase','expect_exit_code':0}}],'tasks':[{'task_id':key,'phase':'build','objective':'Implement '+key+' with explicit verification.','done_when':['Explicit task acceptance condition.'],'depends_on':[] if key=='first' else ['first'],'requirement_ids':['req'],'acceptance':{'command':'python3 check.py --'+key,'expect_exit_code':0}} for key in ('first','second')]}
    def tearDown(self):self.tmp.cleanup()
    def ingest(self,result=None):recorder.import_handoff(self.root,self.p,self.plan,result,'full-plan','v2','Explicit work import.',['check.py'],'Alice','local','session-1')
    def test_full_structure_and_declared_result(self):
        self.ingest({'task_id':'first','acceptance_run':{'command':'python3 check.py --first','exit_code':0}})
        w=self.p['management']['work'];self.assertEqual(w['tasks'][1]['depends_on'],['first']);self.assertEqual(w['tasks'][0]['done_when'],self.plan['tasks'][0]['done_when']);self.assertEqual(self.p['goal'],self.plan['goal'])
        self.assertEqual(self.p['management']['attempts'][0]['provenance'],'declared');self.assertFalse(work.derive(self.p,recorder.now())['tasks'][0]['completed']);self.assertEqual(len(w['phase_gates']),1)
        self.assertEqual({c['scope'] for c in self.p['criteria']},{'task','phase','project'})
    def test_output_conditions_require_review(self):
        self.plan['tasks'][0]['acceptance']['expect_contains']=['expected public output'];self.ingest();t=self.p['management']['work']['tasks'][0]
        self.assertTrue(t['review_required']);self.assertIn('expected public output',t['done_when'][-1])
    def test_unsupported_gate_and_cwd_preserve_original(self):
        original_p=copy.deepcopy(self.p);original_plan=copy.deepcopy(self.plan)
        for field in ('gate','cwd','cycle'):
            self.p=copy.deepcopy(original_p);self.plan=copy.deepcopy(original_plan);before=copy.deepcopy(self.p)
            if field=='gate':self.plan['phases'][0]['exit_check']['expect_contains']=['not supported by exit-only criterion']
            if field=='cwd':self.plan['tasks'][0]['acceptance']['cwd']='other-project'
            if field=='cycle':self.plan['tasks'][0]['depends_on']=['second']
            with self.assertRaises(ValueError):self.ingest()
            self.assertEqual(self.p,before)
    def test_work_record_rejects_forged_completion_transactionally(self):
        self.ingest();before=copy.deepcopy(self.p)
        with self.assertRaises(ValueError):recorder.import_work_record(self.p,'update',{'id':'bad','task_id':'first','at':recorder.now(),'state':'complete','summary':'forged','next_action':'forged'})
        self.assertEqual(self.p,before)
    def test_template_no_fabricated_completion(self):
        document=recorder.read_json(KIT/'catalog-work.template.json');p=document['projects'][0];management.validate(p)
        self.assertEqual(p['management']['attempts'],[]);self.assertEqual(work.derive(p,recorder.now())['summary']['completed'],0)
    def test_cli_record_failure_and_explicit_update(self):
        self.ingest();target=self.root/'project.json';recorder.atomic_json(target,self.p);before=target.read_bytes()
        cmd=[sys.executable,str(KIT/'management_recorder.py'),'--project',str(self.root),'--management','project.json','update','--task','first','--state','blocked','--summary','Explicit blocker','--next-action','Request missing source']
        self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
        updated=target.read_bytes();self.assertNotEqual(updated,before)
        cmd[cmd.index('first')]='missing'
        self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2);self.assertEqual(target.read_bytes(),updated)
if __name__=='__main__':unittest.main()
