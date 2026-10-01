#!/usr/bin/env python3
"""Static UI and executable import-validator checks; does not claim browser QA."""
from html.parser import HTMLParser
from pathlib import Path
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.scripts = []
        self.script = None
        self.external = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, 'Duplicate DOM id'
            self.ids.add(a['id'])
        if tag == 'script':
            self.script = [a, '']
        if a.get('src') or tag == 'link' and a.get('href'):
            self.external.append(a)
    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            self.scripts.append(self.script)
            self.script = None
    def handle_data(self, data):
        if self.script is not None:
            self.script[1] += data


def main():
    html = (ROOT / 'dashboard.html').read_text()
    page = Page()
    page.feed(html)
    assert not page.external, 'UI must not require external resources'
    assert {'pms-data', 'portfolio', 'detail', 'search', 'ownerFilter', 'statusFilter', 'phaseFilter', 'importFile', 'exportButton', 'error', 'detailPanel', 'documentSelect'} - page.ids == {'documentSelect'}
    assert "failed:'호출 실패'" in html and "completed:'호출 완료'" in html
    assert 'role="alert"' in html and 'role="tablist"' in html and 'aria-selected=' in html
    data = next(body for attrs, body in page.scripts if attrs.get('id') == 'pms-data')
    assert json.loads(data)['projects'] == []
    script = next(body for attrs, body in page.scripts if attrs.get('type') != 'application/json')
    assert '.innerHTML' not in script and 'fetch(' not in script and 'eval(' not in script
    assert '사용자 제공 기록 · 실행 출처 미관측' in script
    assert 'JSON.stringify(model,null,2)' not in script and 'JSON.stringify(model)' in script
    assert 'file.size>8000000' in script and 'applySnapshot(await file.text())' in script
    assert "applySnapshot($('pasteJson').value)" in script
    assert 'const candidate=validateModel(parsed);model=candidate' in script
    assert {'pasteButton','pasteDialog','pasteJson','pasteError','applyPaste','cancelPaste'} <= page.ids
    assert 'aria-labelledby="pasteTitle"' in html and 'for="pasteJson"' in html
    assert {'serverFilter','resourceFilter','connectivitySummary','tab-connections'} <= page.ids
    assert 'resourceKey(c,r)' in script and '실제 DB 접근' in script
    assert 'hashchange' in script and 'popstate' in script and 'ArrowRight' in script
    assert 'background:white;color:#172532;padding:9px 13px' in html
    assert '@media(max-width:760px)' in html and 'min-height:44px' in html
    import_logic = script[script.index('function applySnapshot('):script.index('function importError(')]
    validator = script[:script.index('function el(')] + '\n' + script[script.index('function versionLabel('):script.index('function badge(')]
    fixture = {'schema_version': 1, 'generated_at': '2026-10-01T00:00:00Z', 'evidence_mode': 'synthetic', 'projects': []}
    project = dict(id='p1', name='Example', goal='Goal', owners=[], current_revision='r1', current_phase=None, status='unknown', status_reason='No criteria', phases=[], documents=[], criteria=[], runs=[], sessions=[], timeline=[], sources=[], alerts=[], last_updated=None)
    checks = r'''
const assert=require('node:assert/strict');
validateModel(base);
const full=structuredClone(base);full.projects=[project];validateModel(full);
const declared=structuredClone(full);declared.evidence_mode='declared';declared.projects[0].owners=['Alice'];declared.projects[0].sources=[{actor_id:'Alice',environment_id:'e',project_id:'source',evidence_mode:'declared',event_count:0}];validateModel(declared);
function bad(edit){const m=structuredClone(full);edit(m);assert.throws(()=>validateModel(m));}
bad(m=>m.projects[0].runs=null);
bad(m=>m.projects[0].phases=[{id:'a',name:'A',status:'complete'},{id:'a',name:'A',status:'complete'}]);
bad(m=>m.projects[0].current_phase='missing');
bad(m=>m.projects[0].status='success');
bad(m=>m.projects[0].goal='/Users/private/file');
bad(m=>m.projects[0].goal='Bearer abc123');
for(const value of ['ghp_abcdefgh12345678','github_pat_abcdefgh12345678','xoxb-abcdefgh12345678','AIzaabcdefgh123456789012345678','-----BEGIN RSA PRIVATE KEY','password=redacted','/etc/config/private.conf','C:\\data\\private','~/private','bad\u0000control'])bad(m=>m.projects[0].goal=value);
bad(m=>m.projects[0].sessions=[{id:'s',actor_id:'Alice',environment_id:'e',event_count:1}]);
bad(m=>m.projects[0].criteria=[{id:'c',label:'C',scope:'project',target_id:'other',command:'echo ok',expected_exit_code:0}]);
bad(m=>m.projects[0].documents=[{id:'d'}]);
bad(m=>m.generated_at='not-time');
bad(m=>m.generated_at='2026-02-31T00:00:00Z');
bad(m=>m.projects[0].secret='hidden');
bad(m=>m.projects[0].timeline=[{at:'2026-10-01T00:00:00Z',kind:'event',title:'x',detail:'x',session_id:null,source_ref:{bad:1}}]);
const unknownRun=structuredClone(full);unknownRun.projects[0].criteria=[{id:'c',label:'C',scope:'project',target_id:'p1',command:'echo ok',expected_exit_code:0}];unknownRun.projects[0].runs=[{criterion_id:'c',revision:'r1',at:'2026-10-01T00:00:00Z',exit_code:null,session_id:'s',evidence:'No exit code',criterion_signature:'a'.repeat(64),status:'unknown',source_ref:'catalog.projects[0].runs[0]'}];validateModel(unknownRun);
assert.equal(versionLabel('v1'),'v1');assert.equal(versionLabel('V2'),'V2');assert.equal(versionLabel('2'),'v2');assert.equal(versionLabel(3),'v3');
for(const edit of [d=>d.session_id='',d=>d.actor_id='Other',d=>d.phase_id='']){const m=structuredClone(declared);m.projects[0].phases=[{id:'phase',name:'Phase',status:'unknown'}];m.projects[0].sessions=[{id:'s',actor_id:'Alice',environment_id:'e',event_count:0}];const d={id:'doc',title:'Doc',kind:'prd',version:'v1',phase_id:'phase',at:'2026-10-01T00:00:00Z',session_id:'s',actor_id:'Alice',environment_id:'e',summary:'',content:'',source_ref:'catalog.projects[0].documents[0]'};edit(d);m.projects[0].documents=[d];assert.throws(()=>validateModel(m));}

const v2=structuredClone(declared);v2.schema_version=2;v2.projects[0].connections=[];validateModel(v2);
const connection={id:'event1',server:'docs',tool:'search',status:'completed',duration_ms:120,operation:'read',resources:[{id:'shared',kind:'document',label:'Team handbook',evidence:'input'}],artifact_refs:[{id:'doc',version:'v1'}],actor_id:'Alice',environment_id:'e',session_id:null,agent_id:null,tool_call_id:null,at:'2026-10-01T00:00:00Z',authority:'observed',source_ref:'store.events[0]'};
v2.projects[0].connections=[connection];validateModel(v2);
for(const status of ['requested','completed','failed','unknown']){const m=structuredClone(v2);m.projects[0].connections[0].status=status;validateModel(m);}
const configured=structuredClone(v2);Object.assign(configured.projects[0].connections[0],{status:'configured',authority:'declared',at:null});configured.projects[0].connections[0].resources[0].evidence='declared';validateModel(configured);
const declaredUnknown=structuredClone(configured);Object.assign(declaredUnknown.projects[0].connections[0],{status:'unknown',at:'2026-10-01T00:00:00Z'});validateModel(declaredUnknown);
for(const status of ['configured','unknown'])for(const evidence of ['input','output']){const m=structuredClone(status==='configured'?configured:declaredUnknown);m.projects[0].connections[0].resources[0].evidence=evidence;assert.throws(()=>validateModel(m));}
const nullUnknown=structuredClone(declaredUnknown);nullUnknown.projects[0].connections[0].at=null;assert.throws(()=>validateModel(nullUnknown));
for(const edit of [c=>c.actor_id='Other',c=>c.environment_id='other',c=>c.status='configured',c=>c.authority='declared',c=>c.at=null,c=>c.at='2026-10-01T09:00:00+09:00',c=>c.duration_ms=-1,c=>c.duration_ms=86400001,c=>c.duration_ms=1.5,c=>c.operation='query',c=>c.server='https://private.example',c=>c.tool='bad/name',c=>c.raw_input='private',c=>c.resources[0].extra='secret',c=>c.resources[0].evidence='verified',c=>c.resources[0].label='https://private.example',c=>c.resources[0].label='ftp://synthetic.invalid',c=>c.resources[0].label='folder/file',c=>c.resources[0].label='folder\\file',c=>c.resources[0].label='select name from customers',c=>c.resources[0].label='token=secret',c=>c.resources[0].label='/Users/private',c=>c.resources=Array(33).fill(c.resources[0]),c=>c.artifact_refs[0].version='../v1',c=>c.artifact_refs[0].extra='private']){const m=structuredClone(v2);edit(m.projects[0].connections[0]);assert.throws(()=>validateModel(m));}
const missing=structuredClone(v2);delete missing.projects[0].connections;assert.throws(()=>validateModel(missing));
const extraV1=structuredClone(declared);extraV1.projects[0].connections=[];assert.throws(()=>validateModel(extraV1));
const scoped=structuredClone(v2);scoped.projects[0].owners.push('Bob');scoped.projects[0].sources.push({actor_id:'Bob',environment_id:'e',project_id:'source',evidence_mode:'declared',event_count:0});scoped.projects[0].connections.push({...structuredClone(connection),actor_id:'Bob'});validateModel(scoped);
assert.notEqual(resourceKey(scoped.projects[0].connections[0],connection.resources[0]),resourceKey(scoped.projects[0].connections[1],connection.resources[0]));
console.log('v2 exact contract, scoped resources, configured/observed separation and malformed connectivity/declared-provenance/null-time cases PASS');
const safe=structuredClone(full);safe.projects[0].goal='</script><img src=x onerror=alert(1)>';validateModel(safe);
let model=full,activeTab='sessions',selectedDocument='1',renders=0;function renderPortfolio(){renders++;}function renderDetail(){renders++;}const err={textContent:'old error'};global.document={getElementById:()=>err};
assert.throws(()=>applySnapshot('{invalid'));assert.strictEqual(model,full);assert.equal(renders,0);
applySnapshot(JSON.stringify(base));assert.equal(model.projects.length,0);assert.equal(renders,2);assert.equal(err.textContent,'');assert.equal(activeTab,'overview');
applySnapshot(JSON.stringify(declared));assert.equal(model.projects.length,1);assert.equal(renders,4);
console.log('Validator: empty/full/declared/null-run model, 26 malformed nested cases, injection preserved as text; version labels PASS');
'''
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'ui.js'
        path.write_text(script)
        subprocess.run(['node', '--check', str(path)], check=True)
        path.write_text(validator + '\n' + script[script.index('function connections('):script.index('function renderPortfolio(')] + '\nconst base=' + json.dumps(fixture) + ';const project=' + json.dumps(project) + ';\n' + import_logic + '\n' + checks)
        subprocess.run(['node', str(path)], check=True)
    print('UI static structure + JavaScript syntax + import validator: PASS (browser QA is separate)')

if __name__ == '__main__':
    main()
