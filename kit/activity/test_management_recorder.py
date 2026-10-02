#!/usr/bin/env python3
"""Actual local runner, declaration, preservation and graph-boundary checks."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import management
import management_recorder as recorder

AT = '2026-09-30T01:00:00Z'
CHECK = "from pathlib import Path\nprint('RAW_OUTPUT_NOT_FOR_STORAGE')\nraise SystemExit(0 if Path('control.txt').read_text()=='pass' else 1)\n"


def fixture(root, code=CHECK, command='python3 check.py'):
    (root/'check.py').write_text(code)
    (root/'control.txt').write_text('fail')
    files = recorder.actual_manifest(root, [{'path':'check.py'}, {'path':'control.txt'}])
    criterion = {'id':'acceptance','label':'Local project acceptance','scope':'project','target_id':'demo',
                 'command':command,'expected_exit_code':0}
    plan = {'id':'test','version':'v1','plan_id':'plan','plan_version':'v1','criterion_id':'acceptance',
            'requirement_ids':['req'],'reason':'Verify explicitly required behavior.', 'excluded':'No provider or production test.',
            'at':AT,'definition':criterion,'test_files':[next(f for f in files if f['path']=='check.py')]}
    m = {'objectives':[], 'assignment':None, 'requirements':[{'id':'req','text':'Pass the local check.','source':'source.md'}],
         'plans':[{'id':'plan','version':'v1','at':AT,'summary':'Implement local behavior.',
                   'reason':'Required local acceptance.','requirement_ids':['req'],'handoff_ref':None}],
         'test_plans':[plan], 'artifact':{'revision':'v1','sha256':management.artifact_sha256(files),'files':files},
         'attempts':[], 'blockers':[], 'improvements':[], 'harness':[], 'graphs':[]}
    return {'id':'demo','name':'Synthetic local runner fixture','goal':'Verify explicit behavior.','current_revision':'v1',
            'current_phase':None,'source_refs':[{'actor_id':'Alice','environment_id':'local','project_id':'11111111-1111-4111-8111-111111111111'}],
            'phases':[],'documents':[],'criteria':[criterion],'runs':[],'connections':[],'management':m}


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='management-recorder-')
        self.root = Path(self.temporary.name)
        self.p = fixture(self.root)
        self.target = self.root/'management.json'
        recorder.atomic_json(self.target,self.p)

    def tearDown(self):
        self.temporary.cleanup()

    def invoke(self, *action):
        return subprocess.run([sys.executable,str(Path(recorder.__file__)), '--project',str(self.root),
                               '--management','management.json',*action], capture_output=True,text=True)

    def run_args(self, *extra):
        return ('run','--test-plan','test','--actor-id','Alice','--environment-id','local','--session-id','session-1',*extra)

    def test_actual_failure_then_pass_stale_and_no_output(self):
        failed=self.invoke(*self.run_args()); self.assertEqual(failed.returncode,1,failed.stdout)
        (self.root/'control.txt').write_text('pass')
        passed=self.invoke(*self.run_args()); self.assertEqual(passed.returncode,0,passed.stdout)
        p=recorder.read_json(self.target); attempts=p['management']['attempts']
        self.assertEqual([a['exit_code'] for a in attempts],[1,0])
        self.assertEqual([a['provenance'] for a in attempts],['runner','runner'])
        runs,view=management.derive(p,recorder.now())
        self.assertEqual([a['status'] for a in view['attempts']],['unknown','pass'])
        self.assertNotIn('RAW_OUTPUT_NOT_FOR_STORAGE',self.target.read_text()+failed.stdout+passed.stdout)
        self.assertEqual(len(runs),2)

    def test_shell_false_and_post_run_mutation(self):
        p=fixture(self.root, "from pathlib import Path\nPath('control.txt').write_text('pass')\n", 'python3 check.py ; touch injected')
        recorder.atomic_json(self.target,p)
        run=self.invoke(*self.run_args());self.assertEqual(run.returncode,0,run.stdout)
        self.assertFalse((self.root/'injected').exists())
        p=recorder.read_json(self.target)
        self.assertNotEqual(p['management']['artifact']['sha256'],p['management']['attempts'][0]['artifact_sha256'])
        self.assertEqual(management.derive(p,recorder.now())[1]['attempts'][0]['status'],'unknown')

    def test_disappearing_manifest_preserves_original_and_safe_receipt(self):
        p=fixture(self.root, "from pathlib import Path\nPath('control.txt').unlink()\nprint('RAW_OUTPUT_NOT_FOR_STORAGE')\n")
        recorder.atomic_json(self.target,p);before=self.target.read_bytes()
        run=self.invoke(*self.run_args());self.assertEqual(run.returncode,2)
        self.assertEqual(self.target.read_bytes(),before)
        receipts=list((self.root/'.ai-pms').glob('receipt-*.json'));self.assertEqual(len(receipts),1)
        safe=recorder.read_json(receipts[0]);self.assertEqual(safe['attempt']['provenance'],'runner')
        self.assertNotIn('RAW_OUTPUT_NOT_FOR_STORAGE',receipts[0].read_text()+run.stdout+run.stderr)

    def test_changed_test_and_bad_session_rejected_before_execution(self):
        before=self.target.read_bytes()
        (self.root/'check.py').write_text("from pathlib import Path\nPath('executed').touch()\n")
        run=self.invoke(*self.run_args());self.assertEqual(run.returncode,2)
        self.assertEqual(self.target.read_bytes(),before);self.assertFalse((self.root/'executed').exists())
        p=fixture(self.root,"from pathlib import Path\nPath('executed').touch()\n");recorder.atomic_json(self.target,p)
        before=self.target.read_bytes()
        run=self.invoke('run','--test-plan','test','--actor-id','Alice','--environment-id','local','--session-id','bad/session')
        self.assertEqual(run.returncode,2);self.assertFalse((self.root/'executed').exists());self.assertEqual(self.target.read_bytes(),before)

    def test_handoff_is_declared_and_catalog_preserved(self):
        task={'task_id':'work','requirement_ids':['req'],'acceptance':{'command':'python3 check.py','expect_exit_code':0},
              'context':{'excluded':'Provider tests excluded.'}}
        plan={'goal':'Implement explicit local requirement.','spec_ref':'source.md',
              'intent_guard':{'source_ref':'source.md','requirements':[{'id':'req','quote':'Pass the local check.'}]},'tasks':[task]}
        result={'task_id':'work','status':'complete','acceptance_run':{'command':'python3 check.py','exit_code':0,'output_tail':'RAW_OUTPUT_NOT_FOR_STORAGE'}}
        recorder.atomic_json(self.root/'handoff-plan.json',plan);recorder.atomic_json(self.root/'handoff-result.json',result)
        other=copy.deepcopy(self.p);other['id']='other'
        document={'version':3,'projects':[self.p,other]};recorder.atomic_json(self.target,document)
        run=subprocess.run([sys.executable,str(Path(recorder.__file__)),'--project',str(self.root),'--management','management.json',
                            '--project-id','demo','handoff','--plan','handoff-plan.json','--result','handoff-result.json',
                            '--plan-id','handoff-plan','--version','v2','--reason','Explicit acceptance import.', '--test-file','check.py',
                            '--actor-id','Alice','--environment-id','local','--session-id','session-1'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        doc=recorder.read_json(self.target);self.assertEqual(doc['projects'][1],other)
        p=doc['projects'][0];runs,view=management.derive(p,recorder.now())
        self.assertEqual(runs,[]);self.assertEqual(view['attempts'][0]['status'],'unknown')
        self.assertEqual(view['attempts'][0]['provenance'],'declared')
        self.assertNotIn('RAW_OUTPUT_NOT_FOR_STORAGE',self.target.read_text())

    def test_timeout_and_start_failure_have_no_completed_exit_code(self):
        for command, expected in [('python3 check.py',124),('missing-pms-test-executable',127)]:
            p=fixture(self.root,'import time\ntime.sleep(2)\n',command)
            p['criteria'][0]['expected_exit_code']=expected
            p['management']['test_plans'][0]['definition']['expected_exit_code']=expected
            recorder.atomic_json(self.target,p)
            run=self.invoke(*self.run_args('--timeout','1'))
            self.assertEqual(run.returncode,1,run.stdout)
            p=recorder.read_json(self.target)
            self.assertIsNone(p['management']['attempts'][0]['exit_code'])
            self.assertEqual(management.derive(p,recorder.now())[1]['attempts'][0]['status'],'unknown')

    def test_supplied_template_bootstrap_without_manual_hashes(self):
        template=Path(recorder.__file__).with_name('catalog-v3.template.json')
        document=recorder.read_json(template)
        (self.root/'app.py').write_text('# Synthetic artifact only\n')
        (self.root/'checks').mkdir()
        (self.root/'checks/acceptance.py').write_text('assert sum((1,2))==3\n')
        recorder.atomic_json(self.target,document)
        plan={'goal':'Synthetic smoke check only','spec_ref':'smoke-source.md',
              'intent_guard':{'source_ref':'smoke-source.md','requirements':[{'id':'smoke-req','quote':'Verify synthetic local behavior.'}]},
              'tasks':[{'task_id':'smoke','requirement_ids':['smoke-req'],
                        'acceptance':{'command':'python3 checks/acceptance.py','expect_exit_code':0}}]}
        recorder.atomic_json(self.root/'handoff-plan.json',plan)
        run=self.invoke('handoff','--plan','handoff-plan.json','--plan-id','implementation','--version','v2',
                        '--reason','Synthetic template bootstrap.','--test-file','checks/acceptance.py',
                        '--actor-id','ExampleUser','--environment-id','example-laptop','--session-id','smoke-session')
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        run=self.invoke('run','--test-plan','handoff-smoke','--version','v2',
                        '--actor-id','ExampleUser','--environment-id','example-laptop','--session-id','smoke-session')
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        p=recorder.read_json(self.target)['projects'][0]
        self.assertEqual(management.derive(p,recorder.now())[1]['attempts'][0]['status'],'pass')

    def test_relative_symlink_home_and_home_git_root_guard(self):
        with tempfile.TemporaryDirectory(prefix='management-outside-') as outside:
            (self.root/'escape').symlink_to(outside,target_is_directory=True)
            for path in ('../outside','/absolute','a/../b','./check.py','escape/new.json'):
                with self.assertRaises((ValueError,OSError)):recorder.local_path(self.root,path,must_exist=False)
            (self.root/'graphify-out').symlink_to(outside,target_is_directory=True)
            with self.assertRaises(ValueError):recorder.graph_record(self.root,self.p)
        with self.assertRaises(ValueError):recorder.project_root(Path.home())
        with patch.object(recorder.subprocess,'run',return_value=subprocess.CompletedProcess([],0,str(Path.home())+'\n')):
            with self.assertRaises(ValueError):recorder.graph_record(self.root,self.p)

    def test_graph_failure_nonblocking_and_cache(self):
        tools=self.root/'tools';tools.mkdir()
        fake=tools/'graphify'
        fake.write_text("#!/usr/bin/env python3\nimport sys\nif '--version' in sys.argv: print('graphify 1.2.3');raise SystemExit(0)\nraise SystemExit(1)\n");fake.chmod(0o700)
        (self.root/'control.txt').write_text('pass')
        with patch.dict(os.environ,{'PATH':str(tools)+os.pathsep+os.environ['PATH']}):
            run=self.invoke(*self.run_args('--graph'))
        self.assertEqual(run.returncode,0,run.stdout)
        p=recorder.read_json(self.target);graph=p['management']['graphs'][0]
        self.assertEqual((graph['status'],graph['version']),('failed','1.2.3'))
        self.assertEqual(management.derive(p,recorder.now())[1]['graphs'][0]['freshness'],'unknown')
        log=recorder.read_json(self.root/'.ai-pms/graphs.jsonl');self.assertEqual(log,graph)
        fake.write_text("#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\nif '--version' in sys.argv: print('graphify 1.2.3');raise SystemExit(0)\nout=Path('graphify-out');out.mkdir(exist_ok=True);(out/'graph.json').write_text('{\"nodes\":[],\"edges\":[]}')\n");fake.chmod(0o700)
        with patch.dict(os.environ,{'PATH':str(tools)+os.pathsep+os.environ['PATH']}):
            graph=recorder.graph_record(self.root,p)
            self.assertEqual(graph['status'],'generated')
            count=len(p['management']['graphs'])
            self.assertEqual(recorder.graph_record(self.root,p),graph)
            self.assertEqual(len(p['management']['graphs']),count)
        (self.root/'graphify-out/graph.json').write_text('not JSON')
        fake.write_text('#!/usr/bin/env python3\nraise SystemExit(0)\n')
        with patch.dict(os.environ,{'PATH':str(tools)+os.pathsep+os.environ['PATH']}):
            self.assertEqual(recorder.graph_record(self.root,p)['status'],'failed')
        (self.root/'graphify-out/graph.json').unlink()
        with patch.dict(os.environ,{'PATH':str(tools)+os.pathsep+os.environ['PATH']}):
            self.assertEqual(recorder.graph_record(self.root,p)['status'],'failed')
        (self.root/'control.txt').write_text('changed');recorder.refresh_artifact(self.root,p)
        self.assertEqual(next(g for g in management.derive(p,recorder.now())[1]['graphs'] if g['id']==graph['id'])['freshness'],'stale')


if __name__=='__main__':
    unittest.main()
