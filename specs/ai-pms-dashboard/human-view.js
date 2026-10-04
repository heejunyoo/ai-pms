/* Human management projection: goals, phase goals, references, achieved state.
   Completion computation and raw evidence are preserved in the original model. */
const humanDocumentary=document.getElementById('documentary-data')?JSON.parse(document.getElementById('documentary-data').textContent):null;
const humanAnnotations=document.getElementById('human-annotations')?JSON.parse(document.getElementById('human-annotations').textContent):{};
function humanPhases(p){return p.work?.phases||p.phases||[];}
function humanPhase(p,ph){
 const authored=humanAnnotations[p.id]?.phases?.[ph.id],d=humanDocumentary?.projects[p.id],tasks=d?Object.values(d.tasks).filter(t=>t.phase===ph.id):[];
 let state=ph.state||ph.status||'unknown',basis='현재 검증';
 if(d){basis='문서 기록';state=tasks.length&&tasks.every(t=>t.status==='documented')?'complete':tasks.length&&tasks.every(t=>['documented','local'].includes(t.status))?'local':tasks.some(t=>t.status==='blocked')?'blocked':tasks.some(t=>t.status==='in_progress')?'in_progress':'planned';}
 const goal=authored?.goal||ph.name;
 return {id:ph.id,title:authored?.title||ph.name,goal,state,basis};
}
function humanBasis(p){const d=humanDocumentary?.projects[p.id];return d?' · 문서 기준 '+d.docdate:'';}
function humanStatus(x){return ({complete:'달성',local:'로컬 검증까지',blocked:'확인 필요',planned:'예정',in_progress:'진행 중',failed:'검사 실패',review_pending:'검토 대기',revalidation:'재검증 필요',unknown:'확인되지 않음'})[x]||'확인되지 않음';}
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
 if(q.has('task')){const t=p.work?.tasks.find(t=>t.id===q.get('task'));return t?{kind:'task',p,t}:{kind:'invalid',p};}
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
 for(const sid of entry.source_ids){const source=humanDocumentary.sources?.[sid];if(!source||source.project!==p.id)continue;const a=el('a',source.path+' · 발췌 '+(source.lines||[]).join('–')+'행','human-source-link');a.href='source-'+sid+'.html';panel.append(a);}
 if(!entry.source_ids.some(sid=>humanDocumentary.sources?.[sid]?.project===p.id))panel.append(el('small','요청에 연결된 발췌 출처 미기록','muted'));
}
function humanRenderAttention(panel,p=null){
 const projects=p?[p]:humanAttentionProjects();let total=0;
 panel.className='panel human-attention-page';panel.setAttribute('aria-labelledby','detailName');
 for(const project of projects){const entries=humanAttention(project);if(!entries.length)continue;total+=entries.length;const section=el('section',undefined,'human-attention-project');section.append(pageLink(project.name+' · '+entries.length+'건',project));
 for(const [index,g] of entries.entries()){const row=el('article',undefined,'human-attention-item');row.id='human-request-'+encodeURIComponent(project.id)+'-'+encodeURIComponent(g.key);const ph=humanPhases(project).find(ph=>ph.id===g.phase_id);row.append(el('small',(g.owner?'담당 '+g.owner:'프로젝트 공통 · 담당 미지정')+(ph?' · '+humanPhase(project,ph).title:''),'human-request-meta'),el('h3',g.summary));if(!g.owner&&$('ownerFilter').value)row.append(el('small','선택한 사람에게 귀속한 작업 요청이 아닙니다.','muted'));row.append(el('p',g.next_action?'다음 행동: '+g.next_action:'선언된 다음 행동 없음','human-request-action'));humanSourceLines(row,project,g);
 const links=el('div',undefined,'human-request-links');if(ph)links.append(pageLink('단계 상세 →',project,{phase:ph.id}));links.append(pageLink('최종 인수 →',project,{final:'1'}));row.append(links);
 const evidence=el('details');evidence.id=row.id+'-evidence';evidence.dataset.detailEvidence=evidence.id;const summary=el('summary','관련 근거 '+g.items.length+'건');summary.id=evidence.id+'-summary';evidence.append(summary);
 for(const tid of g.task_ids){const task=project.work?.tasks?.find(t=>t.id===tid),doc=humanDocumentary?.projects[project.id]?.tasks?.[tid];if(!g.documentary&&task){const a=pageLink(task.title+' · 작업 상세 →',project,{task:tid});a.id=row.id+'-task-'+encodeURIComponent(tid);evidence.append(a);}else if(doc)evidence.append(el('p',doc.title+' · 문서상의 '+humanStatus(doc.status)));}
 if(!g.task_ids.length)evidence.append(pageLink('프로젝트 분석 근거 →',project,{view:'evidence'}));row.append(evidence);section.append(row);
 }panel.append(section);}
 if(!total)panel.append(el('p','현재 범위에 기록된 판단 요청이 없습니다.','human-empty'));
}
const humanBasePeople=renderPeople;
renderPeople=function(){humanBasePeople();for(const b of $('peopleList').children){const n=model.projects.filter(p=>!b.dataset.person||p.owners.includes(b.dataset.person)||(p.work?.tasks||[]).some(t=>t.owner===b.dataset.person)).length;[...b.children].find(n=>n.tagName.toLowerCase()==='small').textContent=n+'개 프로젝트';b.setAttribute('aria-label',(b.dataset.person||'전체 사람')+' · '+n+'개 프로젝트');const select=b.onclick;b.onclick=()=>{select();humanSetPersonRoute();[...$('peopleList').children].find(button=>button.dataset.person===b.dataset.person)?.focus({preventScroll:true});};}const scope=$('peopleScope');scope.hidden=false;scope.replaceChildren(humanAttentionLink(null,($('ownerFilter').value?$('ownerFilter').value+' 참여 프로젝트 · ':'전체 프로젝트 · ')+'판단 필요 '+humanAttentionProjects().reduce((n,p)=>n+humanAttention(p).length,0)+'건 →'));};
const humanBaseCards=renderCards;
renderCards=function(){humanBaseCards();for(const card of $('projectList').children){const p=model.projects.find(p=>p.id===card.dataset.flowProject);if(!p)continue;const phases=humanPhases(p).map(ph=>humanPhase(p,ph)),done=phases.filter(ph=>ph.state==='complete');[...card.children].find(n=>n.dataset.project).textContent='목표와 단계 보기 →';const count=el('p',done.length+' / '+phases.length+' 단계 달성'+humanBasis(p),'human-achieved'),strip=el('div',undefined,'human-mini-flow');for(const ph of phases){const item=el('span',undefined,'human-mini-node '+ph.state);item.title=ph.title+' · '+humanStatus(ph.state);strip.append(item);}const nodes=[...card.children],link=nodes.pop();card.replaceChildren(...nodes,count,strip,humanAttentionLink(p),link);if(humanDocumentary?.projects[p.id])card.children[0].children[1].textContent=done.length===phases.length&&phases.length?'달성 기록':'진행 중';}
 $('dataNotice').textContent=humanDocumentary?'실제 프로젝트 · 기존 문서 기준':'샘플 · 합성 데이터';
};
const humanBasePhaseFlow=renderPhaseFlow;
renderPhaseFlow=function(panel,p){panel.replaceChildren();const phases=humanPhases(p).map(ph=>humanPhase(p,ph)),done=phases.filter(ph=>ph.state==='complete').length;panel.append(el('h3',done+' / '+phases.length+' 단계 달성'+humanBasis(p)),el('p','계획에 기록된 순서입니다. 연결선은 선행조건이나 기간을 뜻하지 않습니다.','human-flow-caption'));const flow=el('ol',undefined,'human-phase-flow');for(const [i,ph] of phases.entries()){const item=el('li',undefined,'human-phase-step'),link=pageLink('',p,{phase:ph.id});link.id='human-phase-'+encodeURIComponent(p.id)+'-'+encodeURIComponent(ph.id);link.className='human-phase-node '+ph.state;link.dataset.humanPhase=ph.id;link.append(el('small',String(i+1).padStart(2,'0'),'human-phase-number'),el('strong',ph.title),el('span',humanStatus(ph.state),'human-phase-status'));if(ph.goal!==ph.title)link.append(el('p',ph.goal));item.append(link);flow.append(item);}panel.append(flow);const final=pageLink(humanDocumentary?.projects[p.id]?'최종 인수 · 현재 검증 미확인 →':'최종 인수 · '+humanStatus(p.status)+' →',p,{final:'1'});final.className='human-final';final.id='human-final-'+encodeURIComponent(p.id);panel.append(final,humanAttentionLink(p));humanReferenceLine(panel,p);};
const humanBaseShared=renderShared;
renderShared=function(panel,p){panel.append(el('small','담당 '+p.owners.join(' · '),'muted'));};
const humanBaseDetail=renderDetail;
renderDetail=function(){
 const r=route(),oldFocus=document.activeElement?.id,same=renderedDetailRoute===location.hash,panel=$('detailPanel');
 if(r.kind==='attention'){
 for(const node of panel.querySelectorAll('[data-detail-evidence]'))detailDisclosure.set(node.id,!!node.open);renderedDetailRoute=location.hash;
 document.body.dataset.page='attention';$('portfolio').hidden=true;$('detail').hidden=false;$('detail').dataset.page='attention';panel.replaceChildren();delete panel.dataset.taskId;
 $('closeDetail').href=r.p?routeHash(r.p):humanScopeHash('#');$('closeDetail').textContent=r.p?'← 계획으로 돌아가기':'← 프로젝트 목록';$('detailName').textContent=r.p?r.p.name+' · 판단 필요':'판단 필요';$('detailGoal').textContent=r.p?r.p.goal:($('ownerFilter').value?$('ownerFilter').value+' 참여 프로젝트':'전체 프로젝트');$('detailStatus').replaceChildren();$('detailSource').hidden=true;$('tab-work').parentElement.hidden=true;
 humanRenderAttention(panel,r.p);for(const node of panel.querySelectorAll('[data-detail-evidence]'))node.open=detailDisclosure.get(node.id)||false;
 if(same&&oldFocus&&$(oldFocus))$(oldFocus).focus({preventScroll:true});else $('detailName').focus({preventScroll:true});return;
 }
 humanBaseDetail();if(r.kind==='list')renderCards();if(!r.p||r.kind==='plan')$('closeDetail').href=humanScopeHash('#');if(!r.p)return;
 if(r.kind==='phase'){const ph=humanPhase(r.p,r.phase);panel.replaceChildren();panel.className='panel human-phase-detail';panel.setAttribute('aria-labelledby','detailName');panel.append(el('h3','이 단계의 목표'),el('p',ph.goal),el('h3','달성 상태'),el('p',humanStatus(ph.state)+humanBasis(r.p)));humanReferenceLine(panel,r.p,ph.id);$('detailName').textContent=ph.title;$('detailStatus').replaceChildren();
 const entries=humanAttention(r.p,ph.id);if(entries.length){const next=el('section',undefined,'human-next-decision');next.append(el('strong','다음 판단 · '+entries.length+'건'),el('p',entries[0].summary));if(entries[0].next_action)next.append(el('p','다음 행동: '+entries[0].next_action));humanSourceLines(next,r.p,entries[0]);next.append(humanAttentionLink(r.p,'처리함에서 판단 근거 보기 →'));panel.append(next);}
 panel.append(pageLink('분석 근거 보기 →',r.p,{view:'evidence'}));}
 if(r.kind==='plan'){if(humanDocumentary?.projects[r.p.id])$('detailStatus').replaceChildren(el('span','문서 기준 진척','muted'));const link=[...panel.children].filter(n=>n.tagName.toLowerCase()==='a').find(a=>a.textContent==='검증·문서·기록 근거 보기 →');if(link)link.textContent='분석 근거 보기 →';}
 if(same&&oldFocus&&$(oldFocus))$(oldFocus).focus({preventScroll:true});
};

$('evidenceFooterText').textContent=humanDocumentary?'문서상 진척입니다. 현재 검증 결과는 분석 근거에서 확인하세요.':'단계 달성과 최종 인수를 구분합니다. 원본 기록은 분석 근거에서 확인하세요.';

// Session end and goal acceptance remain independent evidence values.
function humanRenderSessions(panel,p){
 const section=el('section',undefined,'rows human-session-evidence'),owner=$('ownerFilter').value,sessions=(model.operations?.sessions||[]).filter(s=>s.project_id===p.id&&(!owner||s.actor_id===owner));section.append(el('h3','세션 목표 · 연결 작업'),el('p','세션 생명주기와 목표 검증·인수는 별개입니다.','muted'));
 if(!sessions.length)section.append(el('p','현재 범위의 세션 목표·인수 근거 미관측','muted'));
 for(const s of sessions){const details=el('details',undefined,'row');details.id='human-operation-session-'+encodeURIComponent(s.id);details.dataset.detailEvidence=details.id;details.dataset.operationSession=s.id;const summary=el('summary',(s.goal||'목표 미입력')+' · '+(completionLabels[s.completion]||s.completion));summary.id=details.id+'-summary';details.append(summary,el('p',s.actor_id+' / '+s.environment_id+' / '+s.source+' / '+s.session_id),el('p','생명주기: '+(lifeLabels[s.lifecycle]||s.lifecycle)+' · 목표: '+(completionLabels[s.completion]||s.completion)),el('p',s.reason),el('small','시작 '+when(s.started_at)+' · 종료 '+when(s.ended_at)+' · 목표 버전 '+s.goal_version+' · revision '+s.project_revision),el('small','출처 프로젝트 '+s.source_project_id+' · 중앙 프로젝트 '+s.project_id));
 if(s.acceptance)details.append(el('p','인수 판단 '+s.acceptance.decision+' · '+s.acceptance.actor_id+' · '+when(s.acceptance.at)+' (선언 기록)'));
 if(!s.task_ids.length)details.append(el('p','연결 작업 미입력 · 활동/종료만으로 목표 완료를 판단하지 않습니다.','muted'));
 for(const tid of s.task_ids){const t=p.work?.tasks.find(t=>t.id===tid);if(!t)continue;const row=el('div',undefined,'human-request-links');row.append(pageLink(t.title+' · 작업과 현재 검사 근거 →',p,{task:t.id}));const ph=humanPhases(p).find(ph=>ph.id===t.phase_id);if(ph)row.append(pageLink(ph.name+' · Phase →',p,{phase:ph.id}));details.append(row);}
 details.append(pageLink('프로젝트 목표 · 전체 Phase 흐름 →',p));section.append(details);
 }panel.append(section);
}
// Dense WBS stays available only within the separate evidence view.
const humanBaseTab=renderTab;
renderTab=function(p){humanBaseTab(p);if(activeTab==='sessions')humanRenderSessions($('detailPanel'),p);if(activeTab==='work'){const details=el('details'),summary=el('summary','WBS · 상세 작업 계획');details.append(summary);const chart=el('div');humanBasePhaseFlow(chart,p);details.append(chart);$('detailPanel').append(details);}if(humanDocumentary){const sources=el('details');sources.append(el('summary','문서상 진척의 출처'));for(const [id,source] of Object.entries(humanDocumentary.sources)){if(source.project!==p.id)continue;const link=el('a',source.path);link.href='source-'+id+'.html';sources.append(link,el('p','발췌 '+source.lines.join('–')+'행','muted'));}$('detailPanel').append(sources);}};
