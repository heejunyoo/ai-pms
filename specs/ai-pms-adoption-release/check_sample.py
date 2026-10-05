#!/usr/bin/env python3
"""Public fictional adoption semantics. Simulated DOM is not production browser proof."""
import ast
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'apps/dashboard/public'

def payload(body,name):
    match=re.search(r'<script\b[^>]*id=["\']'+re.escape(name)+r'["\'][^>]*>(.*?)</script>',body,re.S)
    assert match, 'Missing '+name
    return json.loads(match[1])

def main():
    subprocess.run(['python3',str(ROOT/'scripts/build_dashboard_app.py')],check=True)
    fixture=json.loads((ROOT/'specs/ai-pms-adoption-release/sample-documentary.json').read_text())
    body=(OUT/'index.html').read_text()
    model=payload(body,'pms-data')
    doc=payload(body,'documentary-data')
    assert model==json.loads((OUT/'adoption-snapshot.json').read_text())
    assert doc==fixture['documentary']
    assert set(doc['projects'])=={p['id'] for p in model['projects']}
    assert '실제 프로젝트 · 기존 문서 기준' not in body
    assert (OUT/'sample-documentary.json').read_bytes()==(ROOT/'specs/ai-pms-adoption-release/sample-documentary.json').read_bytes()
    for label in ['가상 프로젝트 · 문서 기반 도입 예시','sampleBoundary','recorded-example.html','adoption-snapshot.json','href="sample-documentary.json" download','수집 모델 JSON · 문서 작업 제외','전체 가상 문서 입력 JSON','이 입력은 빌더용 자료입니다','스냅샷 가져오기만으로 문서 작업 화면이 재현되지는 않습니다']:
        assert label in body,label
    assert 'id="sampleSchedule"' not in body
    assert model['evidence_mode']=='synthetic'
    for p in model['projects']:
        assert p['status']!='complete'
        assert not p['runs'] and not p['sessions'] and not p['criteria']
        assert all(s['event_count']==0 and s['evidence_mode']=='synthetic' for s in p['sources'])
        for t in doc['projects'][p['id']]['tasks'].values():
            source=doc['sources'][t['source']]
            assert source['project']==p['id'] and source['path'].startswith('fictional/')
            page=(OUT/('source-'+t['source']+'.html')).read_text()
            assert '가상 문서' in page and '최종 인수' in page
    assert {t['status'] for p in doc['projects'].values() for t in p['tasks'].values()}=={'documented','in_progress','blocked','unknown'}
    recorded=(OUT/'recorded-example.html').read_text()
    legacy=json.loads((OUT/'snapshot.json').read_text())
    assert payload(recorded,'pms-data')==legacy
    assert '합성 실행 기록 예시' in recorded and 'recordedBoundary' in recorded
    assert 'documentary-data' not in recorded.split('<script>')[0]
    assert 'id="sampleSchedule"' in recorded
    states={t['state'] for p in legacy['projects'] for t in (p.get('work') or {}).get('tasks',[])}
    assert {'failed','revalidation','review_pending'}<=states,'Keep failed, stale and review counterexamples'
    assert any(p['status']=='unknown' for p in legacy['projects']) or 'unknown' in states
    # Exercise actual emitted public JS and model with the existing synthetic DOM harness.
    source=ROOT/'specs/ai-pms-toss-ia/check_ia.py'
    spec=importlib.util.spec_from_file_location('sample_ia',source)
    ia=importlib.util.module_from_spec(spec);spec.loader.exec_module(ia)
    harness=next(n.value.value for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='harness' for t in n.targets))
    harness=harness.replace("||(key==='data-task-id'&&Object.hasOwn(n.dataset,'taskId'))","||(key.startsWith('data-')&&Object.hasOwn(n.dataset,key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())))")
    harness=harness.replace(' get isConnected(){'," get options(){return this.children.filter(n=>n.tagName==='option');}\n get isConnected(){")
    page=ia.Structure();page.feed(body)
    checks=r'''
model=validateModel(FIXTURE);renderPortfolio();renderDetail();
const before=JSON.stringify(model),has=(n,c)=>String(n.className||'').split(' ').includes(c);
assert($('dataNotice').textContent.includes('가상 프로젝트'));
for(const p of model.projects){
 navigate(p);const map=$('human-component-map');assert(map);
 assert.equal(all(map).filter(n=>has(n,'human-map-task')).length,Object.keys(humanDocumentary.projects[p.id].tasks).length);
 assert(map.textContent.includes('현재 실행 검증')&&map.textContent.includes('미확인'));
 for(const t of humanTasks(p)){navigate(p,{task:t.id});assert($('detailName').textContent.includes(t.title));assert($('detailPanel').textContent.includes(t.summary));}
 navigate(p,{view:'evidence'});assert($('detailPanel').textContent.includes('현재 실행 검사와 최종 인수는 미확인'));
 $('human-nav-sessions').click();assert(/기록 없음|미관측/.test($('detailPanel').textContent));
 navigate(p,{final:'1'});assert(!/검증 완료/.test($('detailPanel').textContent));
}
$('ownerFilter').value='Bob';humanSetPersonRoute();assert(location.hash.includes('person=Bob'));
assert.equal(JSON.stringify(model),before,'Documentary projection must not change completion');
console.log('Public adoption DOM PASS: fictional notice, plans/component map, task and source routes, no sessions/current completion, person URL, immutable model');
'''
    with tempfile.TemporaryDirectory() as td:
        js=Path(td)/'sample.js'
        js.write_text('const PAGE='+json.dumps(page.root)+';const FIXTURE='+json.dumps(model)+';\n'+harness+body.split('<script>')[1].split('</script>')[0]+'\n'+checks)
        subprocess.run(['node',str(js)],check=True)
    print('Sample acceptance PASS: fictional document-first default; separate recorded model and counterexamples preserved; zero app/provider/current verification claims. Simulated DOM only; parent browser/release verification remains separate.')

if __name__=='__main__':main()
