#!/usr/bin/env python3
"""Deterministic synthetic source logs and offline catalog; no checks are executed."""
import hashlib
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from portfolio import central, criterion_signature

NOW = '2026-10-01T00:00:00Z'
PROJECT_UUID = '11111111-1111-4111-8111-111111111111'


def sample_data(connectivity=False):
    declarations, store, logs = [], {'version': 1, 'sources': {}}, {}
    def source(actor, environment, project, sessions):
        declaration = dict(actor_id=actor, environment_id=environment, project_id=project, label=actor + ' 합성 환경', evidence_mode='synthetic', files=[actor + '-' + environment + '.jsonl'])
        declarations.append(declaration)
        records, events = {}, []
        for n, session in enumerate(sessions):
            for native in ('SessionStart', 'Stop'):
                event = dict(schema_version=1, adapter_version='1', event_id=str(uuid.uuid5(uuid.NAMESPACE_URL, actor + environment + session + native)), observed_at=f'2026-09-30T0{n+1}:00:00Z', occurred_at=None, source='codex', native_event=native, kind=central.NATIVE[native], authority='observed', project_id=project, tool_name=None, links={k: None for k in central.LINKS}, data={}, missing_fields=[], **{k: None for k in central.IDS})
                event['session_id'] = session
                assert central.valid_event(event, project)
                events.append(event)
        raw = ''.join(json.dumps(e, sort_keys=True) + '\n' for e in events)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        for n, e in enumerate(events, 1):
            records[e['event_id']] = dict(event=e, received_at=NOW, file_sha256=digest, line=n)
        store['sources'][central.source_key(declaration)] = {k: declaration[k] for k in ('actor_id', 'environment_id', 'project_id', 'label', 'evidence_mode')}
        store['sources'][central.source_key(declaration)]['events'] = records
        logs[declaration['files'][0]] = raw
        return {k: declaration[k] for k in ('actor_id', 'environment_id', 'project_id')}
    alice1 = source('Alice', 'laptop', PROJECT_UUID, ['alice-1', 'alice-2'])
    alice2 = source('Alice', 'desktop', PROJECT_UUID, ['alice-3'])
    bob = source('Bob', 'laptop', PROJECT_UUID, ['bob-1'])
    carol = source('Carol', 'desktop', '22222222-2222-4222-8222-222222222222', ['carol-1'])
    dana = source('Dana', 'laptop', '33333333-3333-4333-8333-333333333333', ['dana-1'])
    # A source intentionally absent from catalog remains visible as a fallback.
    source('Eve', 'unmapped', '44444444-4444-4444-8444-444444444444', ['eve-1'])
    def project(pid, name, goal, refs, revision='v1'):
        return dict(id=pid, name=name, goal=goal, current_revision=revision, current_phase='build', source_refs=refs, phases=[dict(id='plan', name='기획'), dict(id='design', name='설계'), dict(id='build', name='구현')], documents=[], criteria=[], runs=[])
    def criterion(p, cid, scope='project', target=None):
        c = dict(id=cid, label={'project': '전체 인수 검사', 'phase': '설계 단계 검사', 'task': '개별 작업 검사'}[scope], scope=scope, target_id=target or p['id'], command='python3 checks/' + cid + '.py', expected_exit_code=0)
        p['criteria'].append(c)
        return c
    def run(p, c, revision, at, exit_code, session):
        p['runs'].append(dict(criterion_id=c['id'], revision=revision, at=at, exit_code=exit_code, session_id=session, evidence='합성으로 입력한 검사 기록 · 명령은 실행하지 않았습니다.', criterion_signature=criterion_signature(c)))
    a = project('alice-recall', 'Recall 학습 도우미', '자료를 읽고 배운 내용을 회상 문제로 확인합니다.', [alice1, alice2])
    ac = criterion(a, 'recall-acceptance')
    pc = criterion(a, 'design-review', 'phase', 'design')
    tc = criterion(a, 'single-task', 'task', 'quiz-component')
    run(a, ac, 'v1', '2026-09-30T04:00:00Z', 1, 'alice-2')
    run(a, ac, 'v1', '2026-09-30T08:00:00Z', 0, 'alice-3')
    run(a, pc, 'v1', '2026-09-30T03:00:00Z', 0, 'alice-1')
    run(a, tc, 'v1', '2026-09-30T05:00:00Z', 0, 'alice-2')
    for did, title, kind, version, phase, at, session, environment, summary, content in [
        ('prd', '제품 요구사항', 'prd', 'v1', 'plan', '2026-09-29T01:00:00Z', 'alice-1', 'laptop', '첫 요구사항', '사용자는 자료를 넣고 회상 문제를 풉니다. 출처를 함께 표시합니다.'),
        ('design', '회상 흐름 설계', 'design', 'v1', 'design', '2026-09-29T03:00:00Z', 'alice-1', 'laptop', '설계 초안', '자료 입력 → 요약 → 문제 풀이. 실패 시 오류를 보여줍니다.'),
        ('design', '회상 흐름 설계', 'design', 'v2', 'design', '2026-09-30T03:00:00Z', 'alice-2', 'laptop', '부분 결과 안내 추가', '자료 입력 → 출처 확인 → 문제 풀이. 부분 결과는 누락 범위를 표시하고 재시도합니다.'),
        ('implementation', '구현 결과', 'implementation', 'v1', 'build', '2026-09-30T08:00:00Z', 'alice-3', 'desktop', '인수 기준 충족', '출처 표시, 문제 풀이, 부분 결과 안내를 구현했습니다. 이 내용과 검사는 모두 합성 시연 입력입니다.')]:
        a['documents'].append(dict(id=did, title=title, kind=kind, version=version, phase_id=phase, at=at, session_id=session, actor_id='Alice', environment_id=environment, summary=summary, content=content))
    b = project('bob-payments', '지급 내역 검토', '지급 내역의 오류를 확인하는 화면을 만듭니다.', [bob])
    bc = criterion(b, 'payments-acceptance')
    bp = criterion(b, 'payment-design', 'phase', 'design')
    run(b, bc, 'v1', '2026-09-30T05:00:00Z', 1, 'bob-1')
    run(b, bp, 'v1', '2026-09-30T03:00:00Z', 0, 'bob-1')
    c = project('carol-dashboard', '운영 대시보드', '운영 상태와 변경 이력을 함께 봅니다.', [carol], 'v2')
    cc = criterion(c, 'dashboard-acceptance')
    run(c, cc, 'v1', '2026-09-29T08:00:00Z', 0, 'carol-1')
    d = project('dana-discovery', '고객 인터뷰 정리', '고객 요구를 정리하고 다음 실험을 정합니다.', [dana])
    if connectivity:
        for p in (a,b,c,d): p['connections'] = []
        def connection(status, evidence='declared', server='sample-crm', tool='lookup'):
            return dict(server=server,tool=tool,status=status,duration_ms=42 if status=='completed' else None,operation='read',resources=[dict(id='customers',kind='database',label='합성 고객 자료',evidence=evidence)],artifact_refs=[dict(id='design',version='v2')])
        d['connections'].append(dict(connection('configured'),id='configured-crm',actor_id='Dana',environment_id='laptop',session_id=None,agent_id=None,tool_call_id=None,at=None))
        for ref, status, evidence in ((alice1,'requested','declared'),(alice1,'completed','output'),(bob,'failed','input'),(alice2,'unknown','declared')):
            source_record=store['sources'][central.source_key(ref)]
            e=dict(next(iter(source_record['events'].values()))['event'])
            native={'requested':'PreToolUse','completed':'PostToolUse','failed':'PostToolUseFailure','unknown':'unknown'}[status]
            e.update(schema_version=2,adapter_version='2',event_id=str(uuid.uuid5(uuid.NAMESPACE_URL,ref['actor_id']+ref['environment_id']+status)),native_event=native,kind=central.NATIVE[native],tool_name='MCP',tool_call_id='synthetic-call',data={'connection':connection(status,evidence)})
            if status=='unknown':
                e.update(native_event='PostToolUse',kind='tool.completed',tool_call_id=None)
                e['data']['connection'].update(server=None,tool=None,status='completed',operation='unknown',resources=[],artifact_refs=[])
            assert central.valid_event(e,ref['project_id'])
            filename=ref['actor_id']+'-'+ref['environment_id']+'.jsonl'
            logs[filename]+=json.dumps(e,sort_keys=True)+'\n'
            digest=hashlib.sha256(logs[filename].encode()).hexdigest()
            source_record['events'][e['event_id']]=dict(event=e,received_at=NOW,file_sha256=digest,line=len(logs[filename].splitlines()))
            for record in source_record['events'].values():record['file_sha256']=digest
    return store, dict(version=2 if connectivity else 1, projects=[a, b, c, d]), dict(sources=declarations), logs


def generate(output=None):
    root = Path(output) if output else Path(__file__).parent
    root.mkdir(parents=True, exist_ok=True)
    store, catalog, manifest, logs = sample_data(connectivity=True)
    for name, value in [('central.json', store), ('catalog.json', catalog), ('manifest.json', manifest)]:
        (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2))
    for name, raw in logs.items():
        (root / name).write_text(raw)
    return store, catalog


if __name__ == '__main__':
    generate(sys.argv[1] if len(sys.argv) > 1 else None)
    print('synthetic sample generated; declared checks were not executed')
