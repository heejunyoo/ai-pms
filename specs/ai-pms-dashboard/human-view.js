/* Human management projection: goals, phase goals, references, achieved state.
   Completion computation and raw evidence are preserved in the original model. */
const humanDocumentary=document.getElementById('documentary-data')?JSON.parse(document.getElementById('documentary-data').textContent):null;
const humanAnnotations=document.getElementById('human-annotations')?JSON.parse(document.getElementById('human-annotations').textContent):{};
function humanPhases(p){return p.work?.phases||p.phases||[];}
function humanPhase(p,ph){
 const authored=humanAnnotations[p.id]?.phases?.[ph.id],d=humanDocumentary?.projects[p.id],tasks=d?Object.values(d.tasks).filter(t=>t.phase===ph.id):[];
 let state=ph.state||ph.status||'unknown',basis='현재 검증';
 if(d){basis='문서 기록';state=tasks.length&&tasks.every(t=>t.status==='documented')?'complete':tasks.length&&tasks.every(t=>['documented','local'].includes(t.status))?'local':tasks.some(t=>t.status==='blocked')?'blocked':tasks.some(t=>t.status==='in_progress')?'in_progress':tasks.length&&tasks.every(t=>t.status==='planned')?'planned':'unknown';}
 const goal=authored?.goal||ph.name;
 return {id:ph.id,title:authored?.title||ph.name,goal,state,basis};
}
function humanBasis(p){const d=humanDocumentary?.projects[p.id];return d?' · 문서 기준 '+d.docdate:'';}
function humanStatus(x){return ({complete:'검증 완료',documented:'문서상 완료 · 현재 검증 미확인',ready:'시작 가능',not_started:'예정',changes_requested:'수정 요청',local:'로컬 검증까지',blocked:'확인 필요',planned:'예정',in_progress:'진행 중',failed:'검사 실패',review_pending:'검토 대기',revalidation:'재검증 필요',unknown:'확인되지 않음'})[x]||'확인되지 않음';}
function humanReferences(p,phaseId=null){
 const authored=humanAnnotations[p.id]?.references;if(authored)return authored.filter(r=>!phaseId||r.phase_ids.includes(phaseId));
 // Without an explicit phase link, project connections are not attributed to a phase.
 if(phaseId)return [];
 const result=new Map();for(const c of connections(p)){if(!c.server&&!c.tool)continue;const name=[c.server,c.tool].filter(Boolean).join(' / '),basis=c.authority==='observed'?'호출 관측':'설정·입력 기록';result.set(name+'|'+basis,{name,basis});}
 return [...result.values()];
}
function humanReferenceLine(panel,p,phaseId=null){const refs=humanReferences(p,phaseId);panel.append(el('h3','참고한 API · MCP'));if(!refs.length){panel.append(el('p',phaseId?'이 단계에 연결된 참조 기록 없음':'참조 기록 없음','muted'));return;}const list=el('div',undefined,'human-references');for(const r of refs)list.append(el('span',r.name+' · '+r.basis,'human-reference'));panel.append(list);}
// Read-only queue: existing requests, grouped without inventing work or completion.
function humanAttentionProjects(){const owner=$('ownerFilter').value;return model.projects.filter(p=>!owner||p.owners.includes(owner)||(p.work?.tasks||[]).some(t=>t.owner===owner));}
function humanAttention(p,phaseId=null){
 const owner=$('ownerFilter').value,d=humanDocumentary?.projects[p.id],groups=new Map();
 const rows=d?Object.values(d.tasks||{}).filter(t=>t.status==='blocked').map(t=>({id:t.id,kind:'documentary',task_id:t.id,phase_id:t.phase,owner:t.owner||null,summary:t.summary,next_action:t.next_action,source_ids:[t.source,t.plan_source].filter(Boolean)})):(p.work?.interventions||[]);
 for(const i of rows){if(phaseId&&i.phase_id!==phaseId)continue;if(owner&&i.owner&&i.owner!==owner)continue;if(['ready','in_progress','not_started'].includes(i.kind))continue;
  const key=JSON.stringify([i.phase_id||null,i.summary||'',i.next_action||'',i.owner||null]);
  if(!groups.has(key))groups.set(key,{key,summary:i.summary||'요청 사유 미기록',next_action:i.next_action||'',owner:i.owner||null,phase_id:i.phase_id||null,kind:i.kind,items:[],task_ids:[],source_ids:[],documentary:!!d});
  const g=groups.get(key);g.items.push(i);if(i.task_id&&!g.task_ids.includes(i.task_id))g.task_ids.push(i.task_id);for(const sid of i.source_ids||[])if(!g.source_ids.includes(sid))g.source_ids.push(sid);
 }
 return [...groups.values()];
}
function humanAttentionLink(p=null,text=null){const n=p?pageLink(text||('판단 필요 '+humanAttention(p).length+'건 →'),p,{view:'attention'}):el('a',text||'전체 판단 필요 →','page-link');if(!p)n.href=humanScopeHash('#view=attention');n.className='page-link human-attention-link';n.id='human-attention-link-'+encodeURIComponent(p?.id||'all');return n;}
function humanScopeHash(hash){const q=new URLSearchParams(hash.replace(/^#/,'')),person=$('ownerFilter').value;if(person)q.set('person',person);else q.delete('person');return '#'+q.toString();}
const humanBaseRouteHash=routeHash;
routeHash=function(p,extras={}){return humanScopeHash(humanBaseRouteHash(p,extras));};
route=function(){
 try{if(!location.hash||location.hash==='#'){$('ownerFilter').value='';return {kind:'list'};}const q=new URLSearchParams(location.hash.slice(1)),allowed=['project','task','phase','final','view','person'];if([...q.keys()].some(k=>!allowed.includes(k)||q.getAll(k).length!==1))return {kind:'invalid'};
 if(q.has('person')){const person=q.get('person'),people=new Set(model.projects.flatMap(p=>[...p.owners,...(p.work?.tasks||[]).map(t=>t.owner).filter(Boolean)]));if(person&&!people.has(person))return {kind:'invalid'};$('ownerFilter').value=person;}else $('ownerFilter').value='';
 if(!q.has('project'))return q.get('view')==='attention'&&[...q.keys()].every(k=>['view','person'].includes(k))?{kind:'attention',p:null}:[...q.keys()].every(k=>k==='person')?{kind:'list'}:{kind:'invalid'};
 const p=model.projects.find(p=>p.id===q.get('project'));if(!p)return {kind:'invalid'};const selectors=['task','phase','final','view'].filter(k=>q.has(k));if(selectors.length>1)return {kind:'invalid',p};
 if(q.has('task')){const t=p.work?.tasks.find(t=>t.id===q.get('task')),doc=humanDocumentary?.projects[p.id]?.tasks?.[q.get('task')];return t?{kind:'task',p,t,doc}:doc?{kind:'task',p,t:doc,doc}:{kind:'invalid',p};}
 if(q.has('phase')){const phase=humanPhases(p).find(ph=>ph.id===q.get('phase'));return phase?{kind:'phase',p,phase}:{kind:'invalid',p};}
 if(q.has('final'))return q.get('final')==='1'?{kind:'final',p}:{kind:'invalid',p};
 if(q.has('view'))return ['evidence','attention'].includes(q.get('view'))?{kind:q.get('view'),p}:{kind:'invalid',p};return {kind:'plan',p};
 }catch{return {kind:'invalid'};}
};
function humanSetPersonRoute(){location.hash=humanScopeHash(location.hash||'#');renderDetail();}
$('ownerFilter').addEventListener('change',humanSetPersonRoute);
const humanBaseResetFilters=$('resetFilters').onclick;
$('resetFilters').onclick=()=>{humanBaseResetFilters();humanSetPersonRoute();};
function humanSourceLines(panel,p,entry){
 if(!entry.documentary){panel.append(el('small','현재 검사 근거 · '+(p.work?.plan_id||'계획 미관측')+' / '+(p.work?.plan_version||'버전 미관측'),'human-basis'));return;}
 const d=humanDocumentary.projects[p.id];panel.append(el('small','문서 기준 '+d.docdate+' · 현재 runner 검사·최종 인수 미확인','human-basis'));
 for(const sid of entry.source_ids){const source=humanDocumentary.sources?.[sid];if(!source||source.project!==p.id||!/^[-a-zA-Z0-9_]+$/.test(sid))continue;const a=el('a',source.path+' · 발췌 '+(source.lines||[]).join('–')+'행','human-source-link');a.href='source-'+sid+'.html';panel.append(a);}
 if(!entry.source_ids.some(sid=>humanDocumentary.sources?.[sid]?.project===p.id))panel.append(el('small','요청에 연결된 발췌 출처 미기록','muted'));
}
function humanRenderAttention(panel,p=null){
 const projects=p?[p]:humanAttentionProjects();let total=0;
 panel.className='panel human-attention-page';panel.setAttribute('aria-labelledby','detailName');
 for(const project of projects){const entries=humanAttention(project);if(!entries.length)continue;total+=entries.length;const section=el('section',undefined,'human-attention-project');section.append(pageLink(project.name+' · '+entries.length+'건',project));
 for(const [index,g] of entries.entries()){const row=el('article',undefined,'human-attention-item');row.id='human-request-'+encodeURIComponent(project.id)+'-'+encodeURIComponent(g.key);const ph=humanPhases(project).find(ph=>ph.id===g.phase_id);row.append(el('small',(g.owner?'담당 '+g.owner:'프로젝트 공통 · 담당 미지정')+(ph?' · '+humanPhase(project,ph).title:''),'human-request-meta'),el('h3',g.summary));if(!g.owner&&$('ownerFilter').value)row.append(el('small','선택한 사람에게 귀속한 작업 요청이 아닙니다.','muted'));row.append(el('p',g.next_action?'다음 행동: '+g.next_action:'선언된 다음 행동 없음','human-request-action'));humanSourceLines(row,project,g);
 const links=el('div',undefined,'human-request-links');if(ph)links.append(pageLink('단계 상세 →',project,{phase:ph.id}));links.append(pageLink('최종 인수 →',project,{final:'1'}));row.append(links);
 const evidence=el('details');evidence.id=row.id+'-evidence';evidence.dataset.detailEvidence=evidence.id;const summary=el('summary','관련 근거 '+g.items.length+'건');summary.id=evidence.id+'-summary';evidence.append(summary);
 for(const tid of g.task_ids){const task=project.work?.tasks?.find(t=>t.id===tid),doc=humanDocumentary?.projects[project.id]?.tasks?.[tid];if(!g.documentary&&task){const a=pageLink(task.title+' · 작업 상세 →',project,{task:tid});a.id=row.id+'-task-'+encodeURIComponent(tid);evidence.append(a);}else if(doc)evidence.append(pageLink(doc.title+' · 문서 작업 상세 →',project,{task:doc.id}));}
 if(!g.task_ids.length)evidence.append(pageLink('프로젝트 분석 근거 →',project,{view:'evidence'}));row.append(evidence);section.append(row);
 }panel.append(section);}
 if(!total)panel.append(el('p','현재 범위에 기록된 판단 요청이 없습니다.','human-empty'));
}
const humanBasePeople=renderPeople;
renderPeople=function(){humanBasePeople();for(const b of $('peopleList').children){const n=model.projects.filter(p=>!b.dataset.person||p.owners.includes(b.dataset.person)||(p.work?.tasks||[]).some(t=>t.owner===b.dataset.person)).length;[...b.children].find(n=>n.tagName.toLowerCase()==='small').textContent=n+'개 프로젝트';b.setAttribute('aria-label',(b.dataset.person||'전체 사람')+' · '+n+'개 프로젝트');const select=b.onclick;b.onclick=()=>{select();humanSetPersonRoute();[...$('peopleList').children].find(button=>button.dataset.person===b.dataset.person)?.focus({preventScroll:true});};}const scope=$('peopleScope');scope.hidden=false;scope.replaceChildren(humanAttentionLink(null,($('ownerFilter').value?$('ownerFilter').value+' 참여 프로젝트 · ':'전체 프로젝트 · ')+'판단 필요 '+humanAttentionProjects().reduce((n,p)=>n+humanAttention(p).length,0)+'건 →'));};
const humanBaseCards=renderCards;
renderCards=function(){humanBaseCards();for(const card of $('projectList').children){const p=model.projects.find(p=>p.id===card.dataset.flowProject);if(!p)continue;const phases=humanPhases(p).map(ph=>humanPhase(p,ph)),done=phases.filter(ph=>ph.state==='complete');[...card.children].find(n=>n.dataset.project).textContent='목표와 단계 보기 →';const count=el('p',done.length+' / '+phases.length+' 단계 '+(humanDocumentary?.projects[p.id]?'문서상 완료':'검증 완료')+humanBasis(p),'human-achieved'),strip=el('div',undefined,'human-mini-flow');for(const ph of phases){const item=el('span',undefined,'human-mini-node '+ph.state);item.title=ph.title+' · '+humanStatus(ph.state);item.textContent=humanGlyph(ph.state)+' '+ph.title+' · '+(humanDocumentary?.projects[p.id]&&ph.state==='complete'?'문서상 완료':humanStatus(ph.state));strip.append(item);}const nodes=[...card.children],link=nodes.pop();card.replaceChildren(...nodes,count,strip,humanAttentionLink(p),link);if(humanDocumentary?.projects[p.id])card.children[0].children[1].textContent='문서 기준 · 현재 검증 미확인';}
 $('dataNotice').textContent=humanDocumentary?'실제 프로젝트 · 기존 문서 기준':({synthetic:'샘플 · 합성 데이터',declared:'사용자 제공 기록 · 실행 출처 미관측','local-execution':'로컬 실행 기록 · 실제 앱 전달은 별도 확인',mixed:'출처별 근거 유형 혼합'})[model.evidence_mode]||'기록 출처 유형 미관측';
};
function humanGlyph(state){return ({complete:'✓',documented:'▤',local:'◐',in_progress:'▶',ready:'▷',blocked:'!',failed:'×',review_pending:'◇',revalidation:'↻',planned:'○',not_started:'○'})[state]||'?';}
function humanStateNode(state,documentary=false){const effective=documentary&&state==='complete'?'documented':state;return el('span',humanGlyph(effective)+' '+humanStatus(effective),'human-status '+effective);}
function humanTasks(p,phaseId=null){const d=humanDocumentary?.projects[p.id];return (d?Object.values(d.tasks||{}):(p.work?.tasks||[])).filter(t=>!phaseId||(t.phase_id||t.phase)===phaseId);}
function humanTaskRow(p,t){
 const doc=!!humanDocumentary?.projects[p.id],state=doc?t.status:t.state,owner=t.owner||p.work?.tasks?.find(x=>x.id===t.id)?.owner||null,row=el('div',undefined,'human-wbs-task'+($('ownerFilter').value&&owner===$('ownerFilter').value?' human-owner-selected':''));row.dataset.taskId=t.id;
 const link=pageLink(t.title+' →',p,{task:t.id});link.id='human-task-'+encodeURIComponent(p.id)+'-'+encodeURIComponent(t.id);link.dataset.wbsTask=t.id;link.append(el('small','담당 '+(owner||'미지정'),'human-task-owner'));row.append(link,humanStateNode(state,doc));if(doc)row.append(el('small','문서 기준 '+humanDocumentary.projects[p.id].docdate+' · 현재 검증 미확인','human-basis'));return row;
}
const humanBasePhaseFlow=renderPhaseFlow;
renderPhaseFlow=function(panel,p){
 // A reviewed, bound synthetic schedule retains its explicit date-axis renderer.
 if(!humanDocumentary?.projects[p.id]&&sampleTimeline(p)){humanBasePhaseFlow(panel,p);panel.className='human-wbs human-date-wbs';for(const n of panel.querySelectorAll('[data-wbs-task]')){const t=p.work.tasks.find(t=>t.id===n.dataset.wbsTask);if(t)n.append(el('small','담당 '+(t.owner||'미지정')),humanStateNode(t.state));}return;}
 panel.replaceChildren();panel.className='human-wbs';const phases=humanPhases(p),views=phases.map(ph=>humanPhase(p,ph)),doc=!!humanDocumentary?.projects[p.id],done=views.filter(ph=>ph.state==='complete').length,tasks=humanTasks(p);
 panel.append(el('h3','전체 계획 · '+done+' / '+phases.length+' 단계 '+(doc?'달성 기록':'검증 완료')+humanBasis(p)),el('p','일정 미입력 · 단계 순서입니다. 기간·노력·의존성을 뜻하지 않습니다. 작업 완료 수는 계획 작업 개수입니다.','human-flow-caption'));
 if(!tasks.length)panel.append(el('p','원자 작업 계획 미입력 · 단계 검사와 최종 인수는 별도입니다.','muted'));
 if($('ownerFilter').value)panel.append(el('p',$('ownerFilter').value+' 담당 강조 · 공동 전체 계획과 다른 담당자 작업을 함께 표시합니다.','muted'));
 const flow=el('ol',undefined,'human-phase-flow');
 for(const [index,raw] of phases.entries()){
  const ph=humanPhase(p,raw),item=el('li',undefined,'human-phase-step'),details=el('details',undefined,'human-wbs-phase');details.id='human-wbs-phase-'+encodeURIComponent(p.id)+'-'+encodeURIComponent(ph.id);details.dataset.humanPhase=ph.id;details.dataset.detailEvidence=details.id;const current=['in_progress','blocked','failed','changes_requested','review_pending','revalidation'].includes(ph.state);details.dataset.humanDefaultOpen=String(current);details.open=detailDisclosure.has(details.id)?detailDisclosure.get(details.id):current;
  const summary=el('summary',undefined,'human-wbs-phase-heading');summary.id=details.id+'-summary';summary.append(el('span',String(index+1).padStart(2,'0'),'human-phase-number'),el('strong',ph.title+' · 작업 '+humanTasks(p,ph.id).length+'개'),humanStateNode(ph.state,doc));details.append(summary);
  const context=el('div',undefined,'human-phase-context'),link=pageLink('단계 목표 · 종료 조건 보기 →',p,{phase:ph.id});link.id='human-phase-'+encodeURIComponent(p.id)+'-'+encodeURIComponent(ph.id);link.className='human-phase-node';link.dataset.humanPhase=ph.id;context.append(el('p',ph.goal),link,el('small',doc?'문서 기록 · 현재 단계 종료 검사 미확인':'단계 종료 검사: '+humanStatus(raw.gate_state||raw.status||'unknown')));details.append(context);
  const group=el('div',undefined,'human-phase-tasks');for(const t of humanTasks(p,ph.id))group.append(humanTaskRow(p,t));if(!group.children.length)group.append(el('p','이 단계의 원자 작업 계획 미입력','muted'));details.append(group);item.append(details);flow.append(item);
 }
 panel.append(flow);const final=pageLink('◇ 최종 인수 · '+(doc?'현재 검증 미확인':humanStatus(p.status))+' →',p,{final:'1'});final.className='human-final';final.id='human-final-'+encodeURIComponent(p.id);panel.append(final,humanAttentionLink(p));
};
const humanBaseShared=renderShared;
renderShared=function(panel,p){
 const people=el('div',undefined,'human-shared-people');panel.append(el('h3',p.owners.length>1?'공동 프로젝트 · 하나의 목표와 전체 계획':'프로젝트 책임'));
 for(const owner of [...new Set([...p.owners,...humanTasks(p).map(t=>t.owner).filter(Boolean)])]){const rows=humanTasks(p).filter(t=>(t.owner||p.work?.tasks?.find(x=>x.id===t.id)?.owner)===owner),box=el('div',undefined,'human-shared-person'+($('ownerFilter').value===owner?' human-owner-selected':''));box.append(el('strong',owner),el('small',rows.length?'담당 작업 '+rows.length+'개 · 단계 '+new Set(rows.map(t=>t.phase_id||t.phase)).size+'개':'담당 작업 미입력'));if(rows.length){const ph=humanPhases(p).find(x=>x.id===(rows[0].phase_id||rows[0].phase));if(ph)box.append(pageLink('담당 단계 상세 →',p,{phase:ph.id}));}people.append(box);}panel.append(people);
 humanReferenceLine(panel,p);const toolsLink=pageLink('API · MCP 설정·호출 근거 →',p,{view:'evidence'});toolsLink.onclick=()=>{activeTab='connections';};panel.append(toolsLink);
 const linked=(model.operations?.contributions||[]).filter(c=>model.operations.sessions.some(s=>s.id===c.session_record_id&&s.project_id===p.id));if(linked.length||p.management?.assignment){const link=pageLink('목표 위임 · 회사·팀 기여 근거 →',p,{view:'evidence'});link.onclick=()=>{activeTab='management';};panel.append(link,el('p','기여 제안과 확인 선언은 별도입니다.','muted'));}
};
const humanBaseDetail=renderDetail;
renderDetail=function(){
 const r=route(),oldFocus=document.activeElement?.id,same=renderedDetailRoute===location.hash,panel=$('detailPanel');
 if(r.kind==='attention'){
 if($('human-evidence-shell'))$('human-evidence-shell').hidden=true;
 for(const node of panel.querySelectorAll('[data-detail-evidence]'))detailDisclosure.set(node.id,!!node.open);renderedDetailRoute=location.hash;
 document.body.dataset.page='attention';$('portfolio').hidden=true;$('detail').hidden=false;$('detail').dataset.page='attention';panel.replaceChildren();delete panel.dataset.taskId;
 $('closeDetail').href=r.p?routeHash(r.p):humanScopeHash('#');$('closeDetail').textContent=r.p?'← 계획으로 돌아가기':'← 프로젝트 목록';$('detailName').textContent=r.p?r.p.name+' · 판단 필요':'판단 필요';$('detailGoal').textContent=r.p?r.p.goal:($('ownerFilter').value?$('ownerFilter').value+' 참여 프로젝트':'전체 프로젝트');$('detailStatus').replaceChildren();$('detailSource').hidden=true;$('tab-work').parentElement.hidden=true;
 humanRenderAttention(panel,r.p);for(const node of panel.querySelectorAll('[data-detail-evidence]'))node.open=detailDisclosure.get(node.id)||false;
 if(same&&oldFocus&&$(oldFocus))$(oldFocus).focus({preventScroll:true});else $('detailName').focus({preventScroll:true});return;
 }
 if(r.kind==='task'&&r.doc&&!r.p.work?.tasks?.some(t=>t.id===r.t.id)){for(const node of panel.querySelectorAll('[data-detail-evidence]'))detailDisclosure.set(node.id,!!node.open);renderedDetailRoute=location.hash;document.body.dataset.page='task';$('portfolio').hidden=true;$('detail').hidden=false;$('detailName').textContent=r.doc.title;$('detailGoal').textContent=r.p.name;$('closeDetail').href=routeHash(r.p);$('tab-work').parentElement.hidden=true;if($('human-evidence-shell'))$('human-evidence-shell').hidden=true;humanRenderDocumentaryTask(panel,r.p,r.doc);$('detailStatus').replaceChildren(humanStateNode(r.doc.status,true));for(const node of panel.querySelectorAll('[data-detail-evidence]'))node.open=detailDisclosure.get(node.id)||false;if(same&&oldFocus&&$(oldFocus))$(oldFocus).focus({preventScroll:true});else panel.focus({preventScroll:true});return;}
 humanBaseDetail();if(r.kind==='list')renderCards();if(!r.p||r.kind==='plan')$('closeDetail').href=humanScopeHash('#');if(!r.p)return;
 if(r.kind==='phase'){const ph=humanPhase(r.p,r.phase);panel.replaceChildren();panel.className='panel human-phase-detail';panel.setAttribute('aria-labelledby','detailName');panel.append(el('h3','이 단계의 목표'),el('p',ph.goal),el('h3','달성 상태'),el('p',humanStatus(ph.state)+humanBasis(r.p)));humanReferenceLine(panel,r.p,ph.id);$('detailName').textContent=ph.title;$('detailStatus').replaceChildren();
 const entries=humanAttention(r.p,ph.id);if(entries.length){const next=el('section',undefined,'human-next-decision');next.append(el('strong','다음 판단 · '+entries.length+'건'),el('p',entries[0].summary));if(entries[0].next_action)next.append(el('p','다음 행동: '+entries[0].next_action));humanSourceLines(next,r.p,entries[0]);next.append(humanAttentionLink(r.p,'처리함에서 판단 근거 보기 →'));panel.append(next);}
 const taskBox=el('section',undefined,'human-phase-tasks');taskBox.append(el('strong','이 단계의 작업'));for(const t of humanTasks(r.p,ph.id))taskBox.append(humanTaskRow(r.p,t));if(!humanTasks(r.p,ph.id).length)taskBox.append(el('p','원자 작업 계획 미입력','muted'));panel.append(taskBox);const gate=el('details');gate.id='human-phase-checks-'+encodeURIComponent(r.p.id)+'-'+encodeURIComponent(ph.id);gate.dataset.detailEvidence=gate.id;gate.append(el('summary','단계 종료 검사 · 문서 근거'));if(!humanDocumentary?.projects[r.p.id])renderFlowChecks(gate,r.p,'phase',ph.id);else gate.append(el('p','문서상 진척 · 현재 단계 종료 검사 미확인'));panel.append(gate,pageLink('분석 근거 보기 →',r.p,{view:'evidence'}));}
 if(r.kind==='task'&&r.doc){humanRenderDocumentaryTask(panel,r.p,r.doc);$('detailStatus').replaceChildren(humanStateNode(r.doc.status,true));}
 if($('human-evidence-shell'))$('human-evidence-shell').hidden=r.kind!=='evidence';
 if(r.kind==='evidence')humanSetupEvidence(r.p);
 if(r.kind==='plan'){if(humanDocumentary?.projects[r.p.id])$('detailStatus').replaceChildren(el('span','문서 기준 진척','muted'));const link=[...panel.children].filter(n=>n.tagName.toLowerCase()==='a').find(a=>a.textContent==='검증·문서·기록 근거 보기 →');if(link)link.textContent='분석 근거 보기 →';}
 for(const node of panel.querySelectorAll('[data-detail-evidence]')){if(detailDisclosure.has(node.id))node.open=detailDisclosure.get(node.id);else if(node.dataset.humanDefaultOpen)node.open=node.dataset.humanDefaultOpen==='true';}
 if(same&&oldFocus&&$(oldFocus))$(oldFocus).focus({preventScroll:true});
};

$('evidenceFooterText').textContent=humanDocumentary?'문서상 진척입니다. 현재 검증 결과는 분석 근거에서 확인하세요.':'단계 달성과 최종 인수를 구분합니다. 원본 기록은 분석 근거에서 확인하세요.';

function humanRenderDocumentaryTask(panel,p,t){panel.replaceChildren();panel.className='panel action-page';panel.dataset.taskId=t.id;panel.setAttribute('tabindex','-1');panel.append(el('h3','담당과 현재 상태'),el('p','담당 '+(t.owner||p.work?.tasks?.find(x=>x.id===t.id)?.owner||'미지정')+' · '+humanStatus(t.status)),el('h3',t.status==='blocked'?'막힌 이유':'현재 상태'),el('p',t.summary||'사유 미기록'),el('h3','다음 행동'),el('p',t.next_action||'선언된 다음 행동 없음'),el('h3','완료 조건'));for(const line of t.done||[])panel.append(el('p',line));if(!t.done?.length)panel.append(el('p','완료 조건 미기록'));const evidence=el('details');evidence.id='human-documentary-task-'+encodeURIComponent(p.id)+'-'+encodeURIComponent(t.id);evidence.dataset.detailEvidence=evidence.id;evidence.append(el('summary','이 작업의 문서 근거'));humanSourceLines(evidence,p,{documentary:true,source_ids:[t.source,t.plan_source].filter(Boolean)});panel.append(evidence);}
// One history projection: operation goals first; unmatched legacy records retain identity.
function humanSessionIdentity(s){return JSON.stringify([s.project_id,s.actor_id,s.environment_id,s.source,s.source_project_id,s.session_id]);}
function humanRenderSessions(panel,p){
 const section=el('section',undefined,'rows human-session-evidence'),owner=$('ownerFilter').value,sessions=(model.operations?.sessions||[]).filter(s=>s.project_id===p.id&&(!owner||s.actor_id===owner));section.append(el('h3','실행 이력 · 목표와 연결 작업'),el('p','세션 실행 종료와 목표 검증·인수는 별개입니다. 실행 횟수는 생산성이 아닙니다.','muted'));
 for(const s of sessions){const row=el('article',undefined,'row human-operation-session');row.id='human-operation-session-'+encodeURIComponent(humanSessionIdentity(s));row.dataset.operationSession=s.id;row.append(el('h3',s.goal||'목표 미입력'),el('p','담당 '+s.actor_id+' · 실행 '+(lifeLabels[s.lifecycle]||s.lifecycle)+' · 목표 '+(completionLabels[s.completion]||s.completion)),el('small','시작 '+when(s.started_at)+' · 종료 '+when(s.ended_at)),el('p',s.reason||'판정 사유 미기록'));
 if(s.acceptance)row.append(el('p','인수 판단 '+s.acceptance.decision+' · '+s.acceptance.actor_id+' · '+when(s.acceptance.at)+' (선언 기록)'));
 if(!s.task_ids.length)row.append(el('p','연결 작업 미입력 · 활동/종료만으로 목표 완료를 판단하지 않습니다.','muted'));
 for(const tid of s.task_ids){const t=p.work?.tasks.find(t=>t.id===tid);if(!t)continue;const links=el('div',undefined,'human-request-links');links.append(pageLink(t.title+' · 작업과 현재 검사 근거 →',p,{task:t.id}));const ph=humanPhases(p).find(ph=>ph.id===t.phase_id);if(ph)links.append(pageLink(ph.name+' · Phase →',p,{phase:ph.id}));row.append(links);}
 const provenance=el('details');provenance.id=row.id+'-source';provenance.dataset.detailEvidence=provenance.id;const summary=el('summary','사용자 · 환경 · 출처 식별');summary.id=provenance.id+'-summary';provenance.append(summary,el('p',s.actor_id+' / '+s.environment_id+' / '+s.source+' / '+s.session_id),el('small','출처 프로젝트 '+s.source_project_id+' · 중앙 프로젝트 '+s.project_id+' · record '+s.id),el('small','목표 버전 '+s.goal_version+' · revision '+s.project_revision));row.append(provenance);section.append(row);
 }
 let legacyCount=0;for(const s of p.sessions||[]){if(owner&&s.actor_id!==owner)continue;
 // Legacy schema lacks provider/source linkage. Only a single exact candidate
 // with explicit provider and source project can be paired; ambiguous candidates remain.
 const sources=(p.sources||[]).filter(x=>x.actor_id===s.actor_id&&x.environment_id===s.environment_id),candidates=sessions.filter(x=>x.actor_id===s.actor_id&&x.environment_id===s.environment_id&&x.session_id===s.id&&x.source===s.source&&x.source_project_id===s.source_project_id);
 if(s.source&&s.source_project_id&&candidates.length===1&&candidates[0].source===s.source&&candidates[0].source_project_id===s.source_project_id)continue;legacyCount++;const row=el('article',undefined,'row human-legacy-session');row.id='human-legacy-session-'+encodeURIComponent(JSON.stringify([p.id,s.actor_id,s.environment_id,s.source||null,s.source_project_id||null,s.id]));row.append(el('h3','기존 실행 기록 · 목표 근거 부족'),el('p','담당 '+s.actor_id+' · 실행 상태 미관측 · 목표 검증 미관측'),el('small','시간 미관측 · 연결 작업 미입력'));const source=el('details');source.id=row.id+'-source';source.dataset.detailEvidence=source.id;source.append(el('summary','사용자 · 환경 · 기존 식별'),el('p',s.actor_id+' / '+s.environment_id+' / '+s.id),el('p','원본 프로젝트 '+(sources.map(x=>x.project_id).join(' / ')||'미관측')+' · provider/source 연결 미관측'),el('small',s.event_count+'개 이벤트 · 활동량은 완료율을 의미하지 않습니다.'));row.append(source);section.append(row);
 }
 if(!sessions.length&&!legacyCount)section.append(el('p','세션 기록 없음 · 현재 범위의 세션 목표·인수 근거 미관측','muted'));panel.append(section);
}
function humanSetupEvidence(p){
 const tabs=$('human-evidence-shell')||$('tab-work').parentElement;tabs.id='human-evidence-shell';tabs.classList.add('human-evidence-shell');let questions=$('human-evidence-questions');if(!questions){questions=el('div',undefined,'human-evidence-questions');questions.id='human-evidence-questions';tabs.replaceChildren(questions,...tabs.children);}questions.replaceChildren();
 for(const [question,tab] of [['작업 결과','work'],['실행 이력','sessions'],['참고 자료','documents']]){const button=el('button',question,'human-evidence-question');button.id='human-question-'+tab;button.setAttribute('aria-pressed',String(activeTab===tab));button.onclick=()=>{activeTab=tab;renderTab(p);$('human-question-'+tab)?.focus({preventScroll:true});};questions.append(button);}
 let technical=$('human-technical-evidence');if(!technical){technical=el('details',undefined,'human-technical-evidence');technical.id='human-technical-evidence';technical.append(el('summary','기술 근거 · 원본 분류로 찾기'));for(const child of [...tabs.children])if(child!==questions)technical.append(child);tabs.append(technical);}
}
const humanBaseTab=renderTab;
renderTab=function(p){
 if(!p)return;const technicalOpen=$('human-technical-evidence')?.open||false;if(activeTab==='sessions'){const panel=$('detailPanel');panel.replaceChildren();panel.setAttribute('aria-labelledby','human-question-sessions');humanRenderSessions(panel,p);}else humanBaseTab(p);
 humanSetupEvidence(p);$('human-technical-evidence').open=technicalOpen;
 if(activeTab==='work'){const details=el('details');details.id='human-evidence-wbs-'+encodeURIComponent(p.id);details.dataset.detailEvidence=details.id;details.append(el('summary','WBS · 상세 작업 계획'));const chart=el('div');humanBasePhaseFlow(chart,p);details.append(chart);$('detailPanel').append(details);}
 if(humanDocumentary){const sources=el('details');sources.id='human-documentary-sources-'+encodeURIComponent(p.id);sources.dataset.detailEvidence=sources.id;sources.append(el('summary','문서상 진척의 출처'));for(const [id,source] of Object.entries(humanDocumentary.sources||{})){if(source.project!==p.id||!/^[-a-zA-Z0-9_]+$/.test(id))continue;const link=el('a',source.path);link.href='source-'+id+'.html';sources.append(link,el('p','발췌 '+source.lines.join('–')+'행','muted'));}$('detailPanel').append(sources);}
};
// Contextual central management entry points retain existing operations and stars.
const humanBaseOperations=renderOperations;
renderOperations=function(){humanBaseOperations();const nav=$('view-people').parentElement;nav.classList.add('human-central-nav');$('view-stars').textContent='회사·팀 목표';$('view-projects').textContent='운영 · 수집 근거';$('northStarArea').classList.add('human-central-context');$('sessionArea').classList.add('human-central-context');$('evidenceArea').classList.add('human-central-context');};
