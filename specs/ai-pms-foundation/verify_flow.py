"""Parent local CLI-to-JSONL verification; provider payloads here are synthetic."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import uuid

HOME = Path.home()
PACKAGE = HOME / '.claude/harness/activity'
OUT = Path(__file__).resolve().parent

def main():
    subprocess.run([sys.executable, str(PACKAGE/'test_logger.py')], check=True)
    subprocess.run([sys.executable, str(PACKAGE/'check_viewer.py')], check=True)
    project = str(uuid.uuid4())
    version = hashlib.sha256((PACKAGE/'logger.py').read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='pms-parent-') as temp:
        root = str(Path(temp).resolve()/'logs')
        prefix = [sys.executable, str(PACKAGE/'logger.py')]
        def record(kind,data,links):
            subprocess.run(prefix+['record','--kind',kind,'--project-id',project,'--session-id','parent-local-review','--data',json.dumps(data,ensure_ascii=False),'--links',json.dumps(links),'--log-dir',root],check=True)
        record('project.baseline',{'goal':'Kit 공통 로그와 로컬 근거 화면 구현','scope':'Codex·Claude 로컬 기록, JSONL 가져오기, Kit 묶음','summary':'Phase 1: 로컬 수집과 시각화'}, {'phase_id':'p1','baseline_version':'b1'})
        record('decision.recorded',{'summary':'자동 실행 관찰과 명시적 판단을 구별합니다.','reason':'로컬 수집 가치를 먼저 검증하고 외부 전송은 후속 단계로 둡니다.','scope_removed':'중앙 서버 자동 수집'},{'phase_id':'p1','baseline_version':'b1','decision_id':'decision-local-first'})
        record('artifact.recorded',{'summary':'공통 기록기 Python 소스'},{'phase_id':'p1','artifact_id':'activity-logger','artifact_version':version})
        record('check.recorded',{'summary':'부모가 로컬 기록기 검사와 화면 정적 검사를 재실행했습니다. 앱의 실제 훅 전달은 미검증입니다.','status':'pass','environment':'local-cli'},{'phase_id':'p1','check_id':'parent-local-check','artifact_id':'activity-logger','artifact_version':version})
        record('acceptance.recorded',{'summary':'사용자의 최종 수락은 아직 기록되지 않았습니다.','status':'pending','environment':'local-review'},{'phase_id':'p1','artifact_id':'activity-logger','artifact_version':version})
        for native in ('PreToolUse','PostToolUse','Stop'):
            payload={'cwd':str(PACKAGE),'hook_event_name':native,'session_id':'synthetic-delivery-test','turn_id':'test-turn','tool_name':'Bash','tool_use_id':'test-call','tool_input':{'command':'not retained'}}
            subprocess.run(prefix+['hook','--source','codex','--project-id',project,'--log-dir',root],input=json.dumps(payload),text=True,check=True,capture_output=True)
        lines=''.join(p.read_text() for p in sorted(Path(root).glob('*.jsonl')))
        events=[json.loads(line) for line in lines.splitlines()]
        assert len(events)==8
        calls=[e for e in events if e['kind'].startswith('tool.')]
        assert len(calls)==2 and all(e['tool_call_id']=='test-call' for e in calls)
        assert 'not retained' not in lines and str(PACKAGE) not in lines
        (OUT/'local-verification-log.jsonl').write_text(lines)
        (OUT/'import-edge-cases.jsonl').write_text(lines+'{invalid json}\n'+json.dumps(events[0],ensure_ascii=False)+'\n')
    script = re.search(r'<script>(.*?)</script>', (PACKAGE/'viewer.html').read_text(), re.S).group(1)
    script += '\nconst fs=require("node:fs"), assert=require("node:assert/strict");\n'
    script += 'const imported=new Map(), stats=importText(fs.readFileSync('+json.dumps(str(OUT/'local-verification-log.jsonl'))+',"utf8"),imported);\n'
    script += 'assert.equal(stats.valid,8);assert.equal(stats.invalid,0);assert.equal(filtered(imported,"","manual").length,5);console.log("PASS actual logger output accepted by viewer importer");'
    subprocess.run(['node','-'], input=script, text=True, check=True)
    print('PASS parent local CLI flow: 5 real declarations + 3 synthetic hook inputs; provider delivery NOT verified')

if __name__=='__main__':
    main()
