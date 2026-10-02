#!/usr/bin/env python3
"""Executable management import checks against actual backend snapshots. Browser QA separate."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
DASH=ROOT/'specs/ai-pms-dashboard'
sys.path.insert(0,str(DASH))
import portfolio
import management


def main():
    subprocess.run([sys.executable,str(DASH/'check_ui.py')],check=True)
    html=(DASH/'dashboard.html').read_text()
    script=html.split('<script>')[1].split('</script>')[0]
    assert '.innerHTML' not in script and 'eval(' not in script
    assert 'tab-management' in html and 'tab-tests' in html
    for text in ['업무 성과 미관측','생성·개정 이유','도움 담당자','설치 선언','검증 미관측','런타임 호출','오래됨']:
        assert text in html,text
    catalog=json.loads((ROOT/'specs/ai-pms-management/sample/catalog-v3.json').read_text())
    observed='2026-10-01T00:00:00Z'
    base=portfolio.build_model(catalog=catalog,now=observed)
    fixtures=[base]
    # Real backend projection must remain valid after provenance, content, time and criterion changes.
    for mutation in ['declared','artifact','future','graphfailed','graphstale','conflict','oldrevision','testfilemismatch','planrevision']:
        c=copy.deepcopy(catalog);p=c['projects'][0];m=p['management'];m.pop('traceability',None)
        if mutation=='declared':
            for a in m['attempts']:a['provenance']='declared'
            for b in m['blockers']:b.update(status='open',resolved_by=None)
        if mutation=='artifact':
            m['artifact']['files'][0]['sha256']='1'*64;m['artifact']['sha256']=management.artifact_sha256(m['artifact']['files'])
        if mutation=='future':
            for a in m['attempts']:a['at']=a['started_at']='2026-10-02T00:00:00Z'
        if mutation=='graphfailed':m['graphs'][0]['status']='failed'
        if mutation=='graphstale':m['graphs'][0]['source_sha256']='1'*64
        if mutation=='conflict':
            a=copy.deepcopy(m['attempts'][0]);a['id']+='-conflict';a['exit_code']=0;m['attempts'].append(a)
        if mutation=='testfilemismatch':
            m['artifact']['files'][0]['sha256']='1'*64;m['artifact']['sha256']=management.artifact_sha256(m['artifact']['files'])
            for a in m['attempts']:a['artifact_sha256']=m['artifact']['sha256']
        if mutation=='planrevision':
            t=copy.deepcopy(m['test_plans'][0]);t.update(version='v2',reason='Explicit revised test rationale',at='2026-09-29T06:00:00Z');m['test_plans'].append(t)
        if mutation=='oldrevision':
            p['current_revision']='r-next';m['artifact']['revision']='r-next'
        fixtures.append(portfolio.build_model(catalog=c,now=observed))
    large=copy.deepcopy(catalog);mm=large['projects'][0]['management'];seed=mm['improvements'][0];mm['improvements']=[dict(seed,id='large-'+str(i),hypothesis='h'*16000,change='c'*16000) for i in range(100)];fixtures.append(portfolio.build_model(catalog=large,now=observed))
    malformed=[]
    def bad(edit):
        m=copy.deepcopy(base);edit(m['projects'][0]);malformed.append(m)
    bad(lambda p:p['management']['attempts'][0].update(command='echo unrelated'))
    bad(lambda p:p['management']['attempts'][0].update(test_plan_sha256='1'*64))
    bad(lambda p:p['management']['attempts'][0].update(criterion_signature='1'*64))
    bad(lambda p:p['management']['artifact'].update(sha256='1'*64))
    bad(lambda p:p['management']['attempts'][0].update(status='pass'))
    bad(lambda p:p['runs'][0].update(status='pass'))
    bad(lambda p:p.update(status='failed'))
    bad(lambda p:p['management']['assignment'].update(assignee='Other'))
    bad(lambda p:p['management']['objectives'][0].update(parent_id=p['management']['objectives'][0]['id']))
    bad(lambda p:p['management']['test_plans'][0].update(reason='token=unsafe'))
    bad(lambda p:p['management']['test_plans'][0]['test_files'][0].update(path='../escape'))
    bad(lambda p:p['management']['graphs'][0].update(freshness='stale'))
    bad(lambda p:p['management']['blockers'][0].update(verification='unknown'))
    bad(lambda p:p['management']['attempts'][0].update(artifact_sha256='1'*64,status='pass'))
    # A forged complete declared-only snapshot and forged stale/future status must be rejected.
    for idx in [1,2,3,7,8]:
        m=copy.deepcopy(fixtures[idx]);m['projects'][0]['status']='complete';malformed.append(m)
    m=copy.deepcopy(fixtures[1]);m['projects'][0]['management']['attempts'][0]['status']='pass';malformed.append(m)
    bad(lambda p:p['management']['artifact']['files'].clear())
    bad(lambda p:p['runs'][0].update(evidence='forged receipt'))
    def empty_historical(p):
        t=copy.deepcopy(p['management']['test_plans'][0]);t.update(version='old-empty',at='2020-01-01T00:00:00Z');t['definition'].update(label='',command='');p['management']['test_plans'].append(t)
    bad(empty_historical)
    if 'traceability' in base['projects'][0]['management']:
        bad(lambda p:p['management']['traceability']['checkpoints'][0].update(artifact_sha256='1'*64))
        bad(lambda p:p['management']['traceability']['handoffs'][0].update(at='2026-09-29T00:00:00.000002Z',usage='observed',usage_at='2026-09-29T00:00:00.000001Z',usage_evidence='Synthetic read'))
        bad(lambda p:p['management']['traceability']['capture'][0].update(at='2026-09-29T00:00:00.000001Z',last_observed_at='2026-09-29T00:00:00.000002Z'))
        bad(lambda p:p['management']['traceability']['decisions'][0].update(at='0000-01-01T00:00:00Z'))
        bad(lambda p:p['management']['traceability']['decisions'][0].update(alternatives=[]))
        bad(lambda p:p['management']['traceability']['decisions'][0].update(supersedes='missing'))
        bad(lambda p:p['management']['traceability']['decisions'][0].update(supersedes=p['management']['traceability']['decisions'][0]['id']))
        bad(lambda p:p['management']['traceability']['handoffs'][0].update(usage='not_observed',usage_at='2026-09-29T06:00:00Z'))
        bad(lambda p:p['management']['traceability']['capture'][0].update(status='unsupported'))
        bad(lambda p:p['management']['traceability']['checkpoints'][0].update(actor_id='Other'))
        bad(lambda p:p['management']['traceability']['decisions'][0].update(reason='token=unsafe'))
        bad(lambda p:p['management']['traceability']['handoffs'][0].update(decision_ids=['missing']))
    validate=script[:script.index('function el(')]
    js=validate+'\nconst assert=require("node:assert/strict");\n'
    js+='const fixtures='+json.dumps(fixtures)+';const malformed='+json.dumps(malformed)+';\n'
    js+='assert.equal(syncSHA256("abc"),"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");\n'
    js+='for(const m of fixtures)validateModel(m);for(const m of malformed)assert.throws(()=>validateModel(m));\n'
    js+='let model=fixtures[0],activeTab="tests",selectedDocument="",renders=0;function renderPortfolio(){renders++;}function renderDetail(){renders++;}global.document={getElementById:()=>({textContent:""})};\n'
    js+=script[script.index('function applySnapshot('):script.index('function importError(')]
    js+='for(const m of malformed){assert.throws(()=>applySnapshot(JSON.stringify(m)));assert.strictEqual(model,fixtures[0]);}assert.equal(renders,0);console.log("v3 backend parity: 11 valid snapshots, extended forged/malformed imports, prior-state preservation PASS");\n'
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'ui-v3.js';path.write_text(js)
        subprocess.run(['node',str(path)],check=True)
    print('Management UI exact contract + derivation checks PASS; browser/mobile QA belongs to parent')

if __name__=='__main__':main()
