#!/usr/bin/env python3
"""Offline DOM event-flow check for the self-contained activity viewer."""
import json
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path


VIEWER = Path(__file__).with_name('viewer.html')


class ViewerHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.controls = set()
        self.script_depth = 0
        self.script = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.controls.add(attrs['id'])
        if tag == 'script':
            assert 'src' not in attrs, 'external scripts are not allowed'
            self.script_depth += 1

    def handle_endtag(self, tag):
        if tag == 'script':
            self.script_depth -= 1

    def handle_data(self, data):
        if self.script_depth:
            self.script.append(data)


def main():
    page = VIEWER.read_text(encoding='utf-8')
    parsed = ViewerHTML()
    parsed.feed(page)
    assert parsed.script, 'viewer inline script is missing'
    assert 'innerHTML' not in ''.join(parsed.script) and 'fetch(' not in ''.join(parsed.script)
    required = {
        'project-start', 'baseline-form', 'goal-input', 'scope-included',
        'scope-excluded', 'phase-name', 'finish-conditions', 'decision-form',
        'basis-select', 'basis-confirm', 'next-task-form', 'next-task',
        'next-acceptance', 'artifact-version-select', 'artifact-file',
        'artifact-preview', 'save-project', 'files', 'status',
    }
    assert required <= parsed.controls, 'missing actual UI controls: ' + ', '.join(sorted(required - parsed.controls))
    controls = json.dumps(sorted(parsed.controls))
    script = ''.join(parsed.script)
    harness = r'''
const assert = require('node:assert/strict');
const vm = require('node:vm');
const controls = new Set(CONTROL_IDS);
const elements = new Map();
const downloads = [];
const blobs = new Map();
class Element {
  constructor(tag='div') { this.tagName=tag; this.children=[]; this.listeners={}; this.value=''; this.textContent=''; this.hidden=false; this.disabled=false; this.checked=false; this.files=[]; this.dataset={}; this.size=0; }
  set innerHTML(_) { throw Error('innerHTML must never be used'); }
  get firstChild() { return this.children[0] || null; }
  get childElementCount() { return this.children.length; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children=[...nodes]; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  async fire(type, event={}) { for (const fn of this.listeners[type]||[]) await fn({preventDefault(){}, ...event}); }
  focus() {} click() { if(this.download) downloads.push({name:this.download, blob:blobs.get(this.href)}); else for(const fn of this.listeners.click||[]) fn({preventDefault(){}}); }
  remove() {} scrollIntoView() {}
}
const document = {
  getElementById(id) { assert(controls.has(id), 'UI referenced missing HTML id: '+id); if(!elements.has(id)) elements.set(id,new Element()); return elements.get(id); },
  createElement(tag) { return new Element(tag); },
  body: new Element('body'),
};
for (const id of controls) elements.set(id,new Element());
let blobNo=0;
const URL = {createObjectURL(blob){const key='blob:'+ ++blobNo; blobs.set(key,blob); return key;}, revokeObjectURL(){}};
const context = vm.createContext({document, URL, Blob, TextDecoder, TextEncoder, Response, crypto:require('node:crypto').webcrypto, setTimeout, console});
vm.runInContext(VIEWER_SCRIPT, context, {filename:'viewer.html'});
const el=id=>elements.get(id);
const invoke=source=>vm.runInContext(source,context);
'''
    harness += r'''
async function complete(){
  await el('project-start').fire('click');
  el('goal-input').value='예약 흐름 검증'; el('scope-included').value='예약 생성';
  el('scope-excluded').value='결제'; el('phase-name').value='예약 MVP';
  el('finish-conditions').value='예약 확인 화면 표시';
  await el('baseline-form').fire('submit');
  assert.equal(el('baseline-form').hidden,true);
  assert.match(el('baseline-feedback').textContent,/메모리에 추가/);
  const project=el('project').value;
  assert.match(project,/^[0-9a-f-]{36}$/i);

  // Import one versioned artifact linked to the just-created baseline.
  const baseline=invoke('baselineRecord('+JSON.stringify(project)+','+JSON.stringify({goal:'예약 흐름 검증',included:'예약 생성',excluded:'결제',phaseName:'예약 MVP',finish:'예약 확인 화면 표시'})+')');
  const artifact=invoke('manualRecord("artifact.recorded",'+JSON.stringify(project)+','+
    JSON.stringify({phase_id:baseline.links.phase_id,baseline_version:baseline.links.baseline_version,artifact_id:'booking-ui',artifact_version:'v2'})+','+
    JSON.stringify({summary:'예약 화면 v2'})+')');
  const file={name:'evidence.jsonl',size:100,arrayBuffer:async()=>new TextEncoder().encode(invoke('projectJSONL('+JSON.stringify([baseline,artifact])+')')).buffer};
  el('files').files=[file]; await el('files').fire('change');
  assert.match(el('status').textContent,/추가 2개/);

  el('basis-select').value=baseline.event_id; await el('basis-select').fire('change');
  assert.equal(el('basis-confirm').checked,false);
  el('decision-summary').value='결제 제외'; el('decision-reason').value='이번 단계 검증 범위 밖';
  el('decision-added').value=''; el('decision-removed').value='결제';
  await el('decision-form').fire('submit');
  assert.match(el('decision-feedback').textContent,/연결했습니다/);
  assert.equal(el('basis-select').value,baseline.event_id);

  el('basis-confirm').checked=true;
  el('artifact-version-select').value=artifact.event_id;
  el('target-agent').value='구현 Agent'; el('next-task').value='예약 확인 화면 구현';
  el('next-acceptance').value='예약을 만들고 확인 화면을 본다';
  await el('next-task-form').fire('submit');
  const packet=el('packet-preview').value;
  assert.match(packet,/예약 확인 화면 구현/); assert.match(packet,/예약을 만들고 확인 화면을 본다/);
  assert.match(packet,/booking-ui \/ v2/); assert.match(packet,/결제 제외/);
  assert.equal(el('download-packet').disabled,false);

  await el('save-project').fire('click');
  const saved=downloads.at(-1); assert.match(saved.name,/\.jsonl$/);
  assert.match(el('dirty-status').textContent,/브라우저 메모리에만/);
  const savedText=await new Response(saved.blob).text();
  const rows=savedText.trim().split('\n').map(JSON.parse);
  assert.equal(rows.length,4); assert(rows.some(e=>e.event_id===baseline.event_id));
  const decision=rows.find(e=>e.kind==='decision.recorded');
  assert(decision); assert.equal(decision.links.baseline_version,baseline.links.baseline_version);
  const roundtrip=invoke('(()=>{const events=new Map();const result=importText('+JSON.stringify(savedText)+',events);return [result.valid,events.get('+JSON.stringify(baseline.event_id)+'),events.get('+JSON.stringify(decision.event_id)+')];})()');
  assert.equal(roundtrip[0],4);
  assert.equal(roundtrip[1].data.goal,'예약 흐름 검증');
  assert.equal(roundtrip[2].data.reason,'이번 단계 검증 범위 밖');

  // Unsaved follow-up changes must disappear with the project. Reimporting the
  // saved snapshot must not inherit old dirty state or task context.
  el('phase-mode').value='continue'; await el('add-baseline').fire('click');
  el('phase-name').value='예약 MVP 수정'; el('finish-conditions').value='수정된 완료 조건';
  await el('baseline-form').fire('submit');
  assert.match(el('dirty-status').textContent,/저장되지 않은/);
  el('packet-preview').value='stale packet'; el('next-task').value='stale task';
  // Exercise the actual file input importer after clearing the live event map.
  await el('clear').fire('click');
  assert.equal(el('dirty-status').textContent,'새 기록은 브라우저 메모리에만 있습니다. 프로젝트 기록 저장 전에는 탭을 닫으면 사라집니다.');
  assert.equal(el('packet-preview').value,''); assert.equal(el('next-task').value,'');
  el('files').files=[{name:saved.name,size:savedText.length,arrayBuffer:async()=>new TextEncoder().encode(savedText).buffer}];
  await el('files').fire('change');
  assert.match(el('status').textContent,/추가 4개/);
  assert.equal(el('project').value,project);
  assert.match(el('dirty-status').textContent,/브라우저 메모리에만/);
  assert.equal(el('packet-preview').value,''); assert.equal(el('next-task').value,'');

  const plain='<script>globalThis.__executed=true</script><img src=x onerror=alert(1)>';
  el('artifact-file').files=[{size:plain.length,arrayBuffer:async()=>new TextEncoder().encode(plain).buffer}];
  await el('artifact-file').fire('change');
  assert.equal(el('artifact-preview').textContent,plain);
  assert.equal(context.__executed,undefined);
  el('artifact-version-select').value='different-version'; await el('artifact-version-select').fire('change');
  assert.equal(el('artifact-preview').textContent,'파일을 직접 선택하면 평문으로 표시합니다.');
  el('artifact-file').files=[{size:plain.length,arrayBuffer:async()=>new TextEncoder().encode(plain).buffer}];
  await el('artifact-file').fire('change');
  const reviewButton=(function find(n){if(n.textContent==='검토하고 판단 기록')return n;for(const child of n.children||[]){const found=find(child);if(found)return found;}return null;})(el('review-content'));
  assert(reviewButton); reviewButton.click();
  assert.equal(el('artifact-preview').textContent,'파일을 직접 선택하면 평문으로 표시합니다.');
  el('artifact-file').files=[{size:1_048_577,arrayBuffer:async()=>new ArrayBuffer(0)}];
  await el('artifact-file').fire('change');
  assert.match(el('artifact-preview').textContent,/1 MiB/);
}
complete().then(()=>console.log('offline DOM workflow events, scoped packet, JSONL reimport, and plain-text artifact safety passed')).catch(error=>{console.error(error);process.exitCode=1;});
'''
    harness = harness.replace('CONTROL_IDS', controls).replace('VIEWER_SCRIPT', json.dumps(script))
    with tempfile.TemporaryDirectory(prefix='activity-workflow-') as tmp:
        path = Path(tmp) / 'workflow.cjs'
        path.write_text(harness, encoding='utf-8')
        subprocess.run(['node', '--check', str(path)], check=True)
        subprocess.run(['node', str(path)], check=True)


if __name__ == '__main__':
    main()
