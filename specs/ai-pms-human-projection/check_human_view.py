#!/usr/bin/env python3
"""Default projection invariants; simulated DOM, not browser or live-delivery proof."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'specs/ai-pms-dashboard'))
import portfolio


def main():
    html = (ROOT / 'specs/ai-pms-dashboard/dashboard.html').read_text()
    js = (ROOT / 'specs/ai-pms-dashboard/human-view.js').read_text()
    css = (ROOT / 'specs/ai-pms-dashboard/human-view.css').read_text()
    assert js in html and css in html, 'Canonical embedded projection drifted'
    path = ROOT / 'specs/ai-pms-toss-ia/check_ia.py'
    spec = importlib.util.spec_from_file_location('human_ia', path)
    ia = importlib.util.module_from_spec(spec); spec.loader.exec_module(ia)
    page = ia.Structure(); page.feed(html)
    harness = next(n.value.value for n in ast.walk(ast.parse(path.read_text()))
                   if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'harness' for t in n.targets))
    harness = harness.replace("||(key==='data-task-id'&&Object.hasOwn(n.dataset,'taskId'))",
                              "||(key.startsWith('data-')&&Object.hasOwn(n.dataset,key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())))")
    harness = harness.replace(' get isConnected(){', " get options(){return this.children.filter(n=>n.tagName==='option');}\n get isConnected(){")
    fixture = json.loads((ROOT / 'apps/dashboard/public/snapshot.json').read_text())
    assertions = r'''
model=validateModel(FIXTURE);renderPortfolio();renderDetail();
const before=JSON.stringify(model),p=model.projects[0];
$('peopleList').children.find(b=>b.dataset.person==='Bob').click();
assert.equal($('projectList').children.length,2);
assert($('projectList').textContent.includes('Alice · Bob'));
navigate(p);assert.equal(route().kind,'plan');
assert.equal(all($('detailPanel')).filter(n=>n.className==='human-phase-node').length,p.work.phases.length);
assert(all($('detailPanel')).some(n=>n.className?.split(' ').includes('human-wbs')));
assert.deepEqual(all($('detailPanel')).filter(n=>n.className?.split(' ').includes('human-wbs-task')).map(n=>n.dataset.taskId).sort(),p.work.tasks.map(t=>t.id).sort());
assert(!$('detailPanel').textContent.includes('python3 synthetic-test.py'));
all($('detailPanel')).find(n=>n.className==='human-phase-node'&&n.dataset.humanPhase===p.work.phases[1].id).click();
assert.equal(route().kind,'phase');
for(const title of ['이 단계의 목표','달성 상태','참고한 API · MCP'])assert($('detailPanel').children.filter(n=>n.tagName==='h3').some(n=>n.textContent===title));
assert($('detailPanel').textContent.includes('이 단계에 연결된 참조 기록 없음'));
assert.equal(humanReferences(p,p.work.phases[1].id).length,0); // project connections do not imply phase usage
for(const t of p.work.tasks.filter(t=>t.phase_id===p.work.phases[1].id))assert(all($('detailPanel')).some(n=>n.tagName==='a'&&new URLSearchParams(n.href.slice(1)).get('task')===t.id));
assert.equal(JSON.stringify(model),before); // filtering and projection cannot promote completion
$('closeDetail').click();assert.equal(route().kind,'plan');
navigate(p,{view:'evidence'});$('tab-work').click();assert($('detailPanel').textContent.includes('WBS · 상세 작업 계획'));
assert(all($('detailPanel')).some(n=>n.className?.startsWith('wbs-chart')));
applyChanges({cursor:1,reset:false,project_updates:[],operations:null,generated_at:model.generated_at});
assert.equal(route().kind,'evidence');assert.equal($('ownerFilter').value,'Bob');
const box=new Element('div');renderPhaseFlow(box,{...p,work:null,phases:[]});assert(box.textContent.includes('0 / 0'));
console.log('Human projection PASS: person scope, shared goal, all phases and tasks, goal/status/reference detail with action path, reference non-inference, unchanged model, preserved WBS evidence and live route. Browser QA separate.');
'''
    with tempfile.TemporaryDirectory() as td:
        output = Path(td) / 'human-dom.js'
        output.write_text('const PAGE=' + json.dumps(page.root) + ';const FIXTURE=' + json.dumps(fixture) + ';\n' +
                          harness + html.split('<script>')[1].split('</script>')[0] + '\n' + assertions)
        subprocess.run(['node', str(output)], check=True)
    generator = ROOT / 'scripts/prepare_goal_analysis.py'
    spec = importlib.util.spec_from_file_location('goal_input', generator)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    packet = module.prepare(fixture)
    assert packet['model_analysis_executed'] is False and packet['findings'] == []
    assert len(packet['projects']) == len(fixture['projects'])
    assert packet['projects'][0]['success_criteria'][0]['description']
    assert 'command' not in json.dumps(packet) and 'tool_input' not in json.dumps(packet)
    print('Goal packet PASS: allowlisted input, source identity, no raw commands and no fake model findings')


if __name__ == '__main__':
    main()
