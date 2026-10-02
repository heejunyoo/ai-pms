#!/usr/bin/env python3
"""IA structure and runnable native DOM contract simulation; not browser/render QA."""
from html.parser import HTMLParser
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / 'specs/ai-pms-dashboard'
sys.path.insert(0, str(DASH))
import portfolio

class Structure(HTMLParser):
    def __init__(self):
        super().__init__(); self.root = {'tag': 'body', 'attrs': {}, 'children': []}; self.stack = [self.root]; self.ids = {}
    def handle_starttag(self, tag, attrs):
        node = {'tag': tag, 'attrs': dict(attrs), 'children': []}
        self.stack[-1]['children'].append(node)
        if node['attrs'].get('id'): self.ids[node['attrs']['id']] = node
        if tag not in {'meta', 'input', 'br', 'hr', 'link', 'img'}: self.stack.append(node)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i]['tag'] == tag:
                del self.stack[i:]; break
    def handle_data(self, text):
        self.stack[-1]['children'].append(text)

def main():
    html = (DASH/'dashboard.html').read_text()
    page = Structure(); page.feed(html)
    def descendants(node):
        return [node] + [n for c in node['children'] if isinstance(c, dict) for n in descendants(c)]
    def under(id, ancestor):
        assert page.ids[id] in descendants(page.ids[ancestor]), (id, ancestor)
    for id in ['dataTools', 'advancedFilters', 'connectionTools', 'portfolioEvidence', 'moreEvidence']:
        assert page.ids[id]['tag'] == 'details' and 'open' not in page.ids[id]['attrs'], id
    for id in ['importButton', 'pasteButton', 'exportButton', 'importFile']: under(id, 'dataTools')
    for id in ['statusFilter', 'phaseFilter', 'managementFilter']: under(id, 'advancedFilters')
    for id in ['stats', 'connectionTools']: under(id, 'portfolioEvidence')
    for id in ['serverFilter', 'resourceFilter']: under(id, 'connectionTools')
    # The user replaced the intervention-first layout with primary WBS/Phase flow.
    assert html.index('id="peopleList"') < html.index('id="projectList"') < html.index('id="interventionList"')
    under('projectList', 'flowArea')
    under('resetFilters', 'scopeTools')
    for id in ['search', 'ownerFilter', 'resetFilters']:
        assert page.ids[id] not in descendants(page.ids['advancedFilters'])
    for tab in ['overview', 'tests', 'traceability', 'sessions', 'timeline', 'connections']: under('tab-'+tab, 'moreEvidence')
    for tab in ['work', 'management', 'documents']:
        assert page.ids['tab-'+tab] not in descendants(page.ids['moreEvidence'])
    assert '--accent:#3182f6' in html and '.row:focus-visible' in html
    def luminance(color):
        channels=[int(color[i:i+2],16)/255 for i in (0,2,4)]
        linear=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in channels]
        return sum(c*w for c,w in zip(linear,(.2126,.7152,.0722)))
    primary=re.findall(r'\.primary\{background:#([0-9a-f]{6})',html)[-1]
    eyebrow=re.findall(r'\.eyebrow\{color:#([0-9a-f]{6})',html)[-1]
    for color in (primary,eyebrow):assert 1.05/(luminance(color)+.05)>=4.5, 'Small text contrast on white'
    catalog = json.loads((ROOT/'specs/ai-pms-work-management/sample/catalog-work.json').read_text())
    model = portfolio.build_model(catalog=catalog, now='2026-10-02T12:00:00Z')
    script = html.split('<script>')[1].split('</script>')[0]
    harness = r'''
const assert=require('node:assert/strict');
let focused=null,scrolled=null;
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.attributes={};this.dataset={};this.value='';this.open=false;this.hidden=false;this.parentElement=null;this.classList={add(){},remove(){}};this._text='';}
 set textContent(t){this._text=String(t);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent).join(' ');}
 setAttribute(k,v){this.attributes[k]=String(v);if(k==='id')this.id=v;if(k==='hidden')this.hidden=true;if(k==='open')this.open=true;if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=v;}
 getAttribute(k){return this.attributes[k];}
 append(...nodes){for(const n of nodes){n.parentElement=this;this.children.push(n);}}
 replaceChildren(...nodes){for(const c of this.children)c.parentElement=null;this.children=[];this._text='';this.append(...nodes);}
 add(n){this.append(n);}
 addEventListener(){}
 focus(){focused=this;}
 scrollIntoView(){scrolled=this;}
 click(){if(this.onclick)this.onclick();}
 closest(tag){let n=this;while(n){if(n.tagName===tag)return n;n=n.parentElement;}return null;}
 querySelectorAll(selector){const key=selector.slice(1,-1);return all(this).filter(n=>Object.hasOwn(n.attributes,key)||(key==='data-task-id'&&Object.hasOwn(n.dataset,'taskId')));}
 get isConnected(){return all(body).includes(this);}
}
function all(n){return [n,...n.children.flatMap(all)];}
function make(n){if(typeof n==='string'){const e=new Element('text');e.textContent=n;return e;}const e=new Element(n.tag);for(const [k,v] of Object.entries(n.attrs))e.setAttribute(k,v??'');for(const c of n.children)e.append(make(c));return e;}
const body=make(PAGE);
global.document={body,get activeElement(){return focused;},createElement:tag=>new Element(tag),getElementById:id=>all(body).find(n=>n.id===id),querySelectorAll:s=>body.querySelectorAll(s)};
global.Option=function(text,value){const n=new Element('option');n.textContent=text;n.value=value;return n;};
global.window={addEventListener(){}};let hash='';global.location={get hash(){return hash;},set hash(v){hash=v&&!v.startsWith('#')?'#'+v:v;},pathname:'/',search:''};global.history={pushState(){location.hash='';}};
'''
    assertions = r'''
model=validateModel(FIXTURE);renderPortfolio();
const shared=model.projects[0];
assert.equal($('resetFilters').closest('details'),null);$('statusFilter').value='failed';$('phaseFilter').value=phaseName(shared);$('managementFilter').value=managementCategory(shared);$('serverFilter').value='missing-server';$('resourceFilter').value='missing-resource';renderCards();assert.equal($('advancedFilters').open,false);assert.equal($('connectionTools').open,false);assert.equal($('portfolioEvidence').open,false);assert($('advancedFilterSummary').textContent.includes('3개 적용'));assert($('connectionFilterSummary').textContent.includes('2개 적용'));assert($('portfolioEvidenceSummary').textContent.includes('필터 2개 적용'));assert.equal($('resultCount').textContent.split(' / ')[0],'0');$('resetFilters').click();for(const id of ['search','ownerFilter','statusFilter','phaseFilter','managementFilter','serverFilter','resourceFilter'])assert.equal($(id).value,'');assert(!$('advancedFilterSummary').textContent.includes('개 적용'));assert(!$('connectionFilterSummary').textContent.includes('개 적용'));assert(!$('portfolioEvidenceSummary').textContent.includes('개 적용'));assert.equal($('resultCount').textContent.split(' / ')[0],String(model.projects.length));
assert($('interventionList').querySelectorAll('[data-task-id]').length===0);
const rows=all($('interventionList')).filter(n=>n.className==='row intervention');
assert(rows.length>3);assert.equal($('interventionList').children.filter(n=>n.className==='row intervention').length,3);
assert.equal($('moreInterventions').open,false);assert.equal($('moreInterventions').children.length-1,rows.length-3);
assert($('interventionList').children[0].textContent.includes('개 판단'));
for(const row of rows){assert(row.textContent.includes('프로젝트: '));assert(row.textContent.includes('책임자: '));assert(row.textContent.includes('다음 행동: '));}
const bobButton=$('peopleList').children.find(b=>b.dataset.person==='Bob');assert(bobButton);bobButton.focus();bobButton.click();assert.equal(focused.dataset.person,'Bob');assert.notEqual(focused,bobButton);assert.equal(focused.isConnected,true);assert.equal(focused.getAttribute('aria-pressed'),'true');assert.equal($('ownerFilter').value,'Bob');
assert($('peopleScope').textContent.includes('Bob'));
const bob=shared.work.tasks.find(t=>t.owner==='Bob');assert(bob);const scopedRows=all($('interventionList')).filter(n=>n.className==='row intervention');const expectedCount=model.projects.filter(p=>p.owners.includes('Bob')||p.work?.tasks.some(t=>t.owner==='Bob')).reduce((n,p)=>n+(p.work?p.work.interventions.filter(i=>i.owner==='Bob'||i.task_id===null).length:1),0);assert.equal(scopedRows.length,expectedCount);const bobRow=scopedRows.find(r=>r.textContent.includes(bob.title)&&r.textContent.includes('프로젝트: '+shared.name));assert(bobRow);all(bobRow).find(n=>n.tagName==='button').click();assert.equal(focused.dataset.taskId,bob.id);
const opener=new Element('button');$('interventionList').append(opener);
openWork(shared,opener,bob.id);
assert.equal(focused.dataset.taskId,bob.id);assert.equal(scrolled,focused);assert.equal(focused.tabIndex,-1);
assert.equal($('detailPanel').querySelectorAll('[data-task-id]').length,shared.work.tasks.filter(t=>t.owner==='Bob').length);
assert(focused.textContent.includes('완료 조건:'));
const evidence=focused.children.find(n=>n.tagName==='details');assert(evidence&&!evidence.open);assert(evidence.textContent.includes('선행 작업:'));assert(evidence.textContent.includes('작업 ID:'));
renderDetail();assert.equal(focused.dataset.taskId,bob.id); // delayed hashchange must retain exact focus
$('ownerFilter').value='';renderCards();$('interventionList').append(opener);
const other=shared.work.tasks.find(t=>t.id!==bob.id);openWork(shared,opener,other.id);assert.equal(focused.dataset.taskId,other.id);
$('moreEvidence').open=false;$('tab-work').click();
$('tab-work').onkeydown({key:'End',preventDefault(){}});assert.equal(focused.id,'tab-documents'); // skip collapsed evidence tabs
$('moreEvidence').open=true;$('tab-work').onkeydown({key:'End',preventDefault(){}});assert.equal(focused.id,'tab-connections');
assert.equal($('tab-connections').getAttribute('aria-selected'),'true');$('moreEvidence').open=false;$('moreEvidence').ontoggle();assert.equal(activeTab,'work');assert.equal(focused.id,'tab-work');assert.equal($('detailPanel').getAttribute('aria-labelledby'),'tab-work');
$('moreEvidence').open=false;activeTab='tests';renderTab(shared);assert.equal($('moreEvidence').open,true);
$('closeDetail').click();assert.equal(focused,opener);assert.equal($('portfolio').hidden,false);
console.log('IA DOM contract PASS: precise task focus/scroll, owner scope, full filtered intervention disclosure, preserved tools, visible keyboard tabs and focus return (simulation; no layout/browser claim)');
'''
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'ia-dom.js'
        path.write_text('const PAGE='+json.dumps(page.root)+';const FIXTURE='+json.dumps(model)+';\n'+harness+script+'\n'+assertions)
        subprocess.run(['node',str(path)],check=True)
    subprocess.run([sys.executable,str(ROOT/'specs/ai-pms-work-management/check_ui_work.py')],check=True)
    print('IA structure and DOM simulation + existing work UI regressions PASS; browser/mobile rendering unverified')

if __name__=='__main__': main()
