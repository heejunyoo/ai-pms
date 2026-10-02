#!/usr/bin/env python3
"""Actual subprocess + Kit Handoff import + task/phase/review projection. Synthetic identities."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[2]
KIT=ROOT/'kit/activity' if (ROOT/'kit/activity').exists() else Path.home()/'.claude/harness/activity'
sys.path.insert(0,str(KIT))
import management_recorder as recorder
import management
spec=importlib.util.spec_from_file_location('exercise_work_portfolio',ROOT/'specs/ai-pms-dashboard/portfolio.py')
portfolio=importlib.util.module_from_spec(spec);spec.loader.exec_module(portfolio)

def main():
    with tempfile.TemporaryDirectory(prefix='pms-work-flow-') as directory:
        root=Path(directory)
        (root/'control.txt').write_text('fail')
        (root/'check.py').write_text("from pathlib import Path\nprint('RAW_WORK_OUTPUT_NOT_RETAINED')\nraise SystemExit(0 if Path('control.txt').read_text()=='pass' else 1)\n")
        commands={key:'python3 check.py --'+key for key in ('first','second','phase','project')}
        p={'id':'work-example','name':'합성 담당자의 실제 로컬 검증','goal':'두 원자화 작업과 단계/전체 인수 조건을 충족한다','current_revision':'r1','current_phase':'build','source_refs':[{'actor_id':'Alice','environment_id':'local','project_id':'11111111-1111-4111-8111-111111111111'}],'phases':[{'id':'build','name':'검증 구현 단계'}],'documents':[],'criteria':[],'runs':[],'connections':[],'management':{'objectives':[],'assignment':None,'requirements':[],'plans':[],'test_plans':[],'artifact':{'revision':'r1','files':[],'sha256':management.artifact_sha256([])},'attempts':[],'blockers':[],'improvements':[],'harness':[],'graphs':[]}}
        handoff={'goal':p['goal'],'spec_ref':'declared-local-example','intent_guard':{'source_ref':'declared-local-example','requirements':[{'id':'local-goal','quote':p['goal'],'outcome':p['goal']}],'acceptance':{'command':commands['project'],'expect_exit_code':0}},'phases':[{'id':'build','name':'검증 구현 단계','exit_check':{'command':commands['phase'],'expect_exit_code':0}}],'tasks':[{'task_id':key,'phase':'build','objective':'실제 검사로 '+key+' 작업 완료 조건을 확인한다','done_when':['현재 검사 대상 파일과 완료 기준이 일치한다'],'depends_on':[] if key=='first' else ['first'],'requirement_ids':['local-goal'],'acceptance':{'command':commands[key],'expect_exit_code':0}} for key in ('first','second')]}
        recorder.import_handoff(root,p,handoff,None,'local-plan','v1','Explicit test of work management flow',['check.py'],'Alice','local','local-session')
        assert len(p['management']['work']['tasks'])==2
        p['management']['artifact']['files'].append({'path':'control.txt','sha256':recorder.file_sha256(root/'control.txt')})
        recorder.refresh_artifact(root,p)
        p['management']['work']['tasks'][1]['review_required']=True
        target=root/'project.json';recorder.atomic_json(target,p)
        def model():
            project=recorder.read_json(target)
            return portfolio.build_model(catalog={'version':3,'projects':[project]},now=recorder.now())['projects'][0]
        def run(scope,target_id):
            project=recorder.read_json(target)
            candidates=[tp for tp in project['management']['test_plans'] if tp['definition']['scope']==scope and tp['definition']['target_id']==target_id]
            tp=max(candidates,key=lambda x:management.time(x['at']))
            cmd=[sys.executable,str(KIT/'management_recorder.py'),'--project',directory,'--management','project.json','run','--test-plan',tp['id'],'--version',tp['version'],'--actor-id','Alice','--environment-id','local','--session-id','local-session']
            return subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
        assert run('task','first')==1
        before=model();assert before['work']['tasks'][0]['state']=='failed'
        assert before['work']['tasks'][1]['state']=='blocked'
        (root/'control.txt').write_text('pass')
        assert run('task','first')==0
        assert run('task','second')==0
        pending=model();assert pending['work']['tasks'][1]['state']=='review_pending'
        p=recorder.read_json(target)
        ws=importlib.util.spec_from_file_location('exercise_work_digest',KIT/'work.py');work=importlib.util.module_from_spec(ws);ws.loader.exec_module(work)
        task=p['management']['work']['tasks'][1]
        review={'id':'explicit-review','task_id':task['id'],'at':recorder.now(),'reviewer':'Alice','decision':'approved','summary':'Synthetic human-review workflow check; no real user approval claimed.','artifact_sha256':p['management']['artifact']['sha256'],'task_sha256':work.task_digest(p,task)}
        recorder.atomic_json(root/'review.json',review)
        code=subprocess.run([sys.executable,str(KIT/'management_recorder.py'),'--project',directory,'--management','project.json','record','--kind','review','--record','review.json'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
        assert code==0,'explicit review CLI'
        assert run('phase','build')==0
        assert run('project','work-example')==0
        done=model();assert done['status']=='complete' and done['work']['summary']['completed']==2
        assert 'RAW_WORK_OUTPUT_NOT_RETAINED' not in json.dumps(done)
        (root/'control.txt').write_text('changed')
        p=recorder.read_json(target);recorder.refresh_artifact(root,p);recorder.atomic_json(target,p)
        changed=model();assert changed['status']=='revalidation' and changed['work']['summary']['completed']==0
        proof={'evidence':'actual-local-subprocess-and-kit-cli-with-synthetic-identities','handoff_structure_preserved':True,'stages':['task_failed','dependent_blocked','review_pending','complete','revalidation'],'required_tasks':2,'completed_before_change':2,'completed_after_change':0,'raw_output_retained':False,'actual_multi_user_delivery_verified':False,'real_human_approval_verified':False}
        (ROOT/'specs/ai-pms-work-management/local-execution-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
        print('PASS: actual Handoff -> task fail -> dependent wait -> pass -> recorded review -> phase/project pass -> file change revalidation')
if __name__=='__main__':main()
