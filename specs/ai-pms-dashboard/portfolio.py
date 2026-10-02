#!/usr/bin/env python3
"""Offline, explicit catalog + central event snapshot. Never executes declared checks."""
import argparse
from bisect import bisect_right
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

_spec = importlib.util.spec_from_file_location('portfolio_central', Path(__file__).parent.parent / 'ai-pms-central' / 'central.py')
central = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(central)
_management_spec = importlib.util.spec_from_file_location('portfolio_management', Path(__file__).with_name('management.py'))
management = importlib.util.module_from_spec(_management_spec)
_management_spec.loader.exec_module(management)
MAX_FILE = 16 * 1024 * 1024
MAX_ARRAY = 10000
CRITERION_KEYS = {'id', 'label', 'scope', 'target_id', 'command', 'expected_exit_code'}
MODES = {'synthetic', 'local-execution'}
BEARER = re.compile(r'(?i)\bBearer\s+\S+')
ABSOLUTE_PATH = re.compile(r'(?:^|[\s\"\'=])/(?!/)[A-Za-z0-9_.-]+(?:/[^\s<>]*)?')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def criterion_signature(criterion):
    """Re-enter runs after a definition changes; only the six criterion fields are signed."""
    return hashlib.sha256(canonical({k: criterion[k] for k in sorted(CRITERION_KEYS)}).encode()).hexdigest()


def validate_tree(value, depth=0):
    require(depth < 25, '입력 중첩 한도')
    if isinstance(value, str):
        require(central.safe_text(value, 20000) and not ABSOLUTE_PATH.search(value) and not BEARER.search(value), '텍스트 한도 또는 비공개 정보')
    elif isinstance(value, list):
        require(len(value) <= MAX_ARRAY, '배열 한도')
        for item in value:
            validate_tree(item, depth + 1)
    elif isinstance(value, dict):
        require(len(value) <= MAX_ARRAY, '객체 한도')
        for key, item in value.items():
            require(isinstance(key, str), '객체 키')
            validate_tree(key, depth + 1)
            validate_tree(item, depth + 1)
    else:
        require(value is None or type(value) in (int, bool), '지원하지 않는 JSON 값')


def keys(value, fields, context):
    require(isinstance(value, dict) and set(value) == set(fields), context + ' 필드')


def ident(value):
    require(central.identifier(value), '잘못된 식별자')


def text(value, limit=2000, nonempty=True):
    require(central.safe_text(value, limit) and (not nonempty or value.strip()), '잘못된 텍스트')


def time(value):
    parsed = central.timestamp(value)
    require(parsed is not None, 'UTC 시각 형식')
    return parsed


def array(value):
    require(isinstance(value, list) and len(value) <= MAX_ARRAY, '배열 형식 또는 한도')
    return value


def unique(items, field='id'):
    values = [item[field] for item in items]
    require(len(values) == len(set(values)), '중복 ' + field)


def source_identity(ref):
    keys(ref, ('actor_id', 'environment_id', 'project_id'), '출처')
    ident(ref['actor_id'])
    ident(ref['environment_id'])
    require(central.uid(ref['project_id']), '출처 프로젝트 UUID')
    return central.source_key(ref)


def validate_catalog(catalog):
    keys(catalog, ('version', 'projects'), 'catalog')
    require(type(catalog['version']) is int and catalog['version'] in (1, 2, 3), 'catalog 버전')
    projects = array(catalog['projects'])
    mapped = set()
    for p in projects:
        keys(p, ('id', 'name', 'goal', 'current_revision', 'current_phase', 'source_refs', 'phases', 'documents', 'criteria', 'runs', *(['connections'] if catalog['version'] >= 2 else []), *(['management'] if catalog['version'] == 3 else [])), '프로젝트')
        for field in ('id', 'current_revision'):
            ident(p[field])
        text(p['name'], 160)
        text(p['goal'])
        for ref in array(p['source_refs']):
            key = source_identity(ref)
            require(key not in mapped, '출처 중복 매핑')
            mapped.add(key)
        for phase in array(p['phases']):
            keys(phase, ('id', 'name'), '단계')
            ident(phase['id'])
            text(phase['name'], 160)
        unique(p['phases'])
        phase_ids = {phase['id'] for phase in p['phases']}
        require(p['current_phase'] is None or p['current_phase'] in phase_ids, '현재 단계 참조')
        ref_pairs = {(r['actor_id'], r['environment_id']) for r in p['source_refs']}
        for connection in array(p.get('connections', [])):
            keys(connection, (*central.connectivity.FIELDS, 'id','actor_id','environment_id','session_id','agent_id','tool_call_id','at'), '연결')
            ident(connection['id'])
            require(central.connectivity.valid({k:connection[k] for k in central.connectivity.FIELDS}, configured=True), '연결 계약')
            require((connection['actor_id'],connection['environment_id']) in ref_pairs, '연결 출처')
            require(all(connection[k] is None or central.identifier(connection[k]) for k in ('session_id','agent_id','tool_call_id')), '연결 식별자')
            require(connection['at'] is not None or connection['status'] == 'configured', '연결 시각 누락')
            if connection['at'] is not None: time(connection['at'])
            require(all(r['evidence']=='declared' for r in connection['resources']), '설정 참조 선언')
        unique(p.get('connections', []))
        for doc in array(p['documents']):
            keys(doc, ('id', 'title', 'kind', 'version', 'phase_id', 'at', 'session_id', 'actor_id', 'environment_id', 'summary', 'content'), '문서')
            for field in ('id', 'kind', 'version', 'session_id', 'actor_id', 'environment_id'):
                ident(doc[field])
            for field in ('title', 'summary', 'content'):
                text(doc[field], 20000 if field == 'content' else 2000)
            time(doc['at'])
            require(doc['phase_id'] in phase_ids, '문서 단계 참조')
            require((doc['actor_id'], doc['environment_id']) in ref_pairs, '문서 사용자 환경 참조')
        require(len({(d['id'], d['version']) for d in p['documents']}) == len(p['documents']), '중복 문서 버전')
        for c in array(p['criteria']):
            keys(c, CRITERION_KEYS, '검사 기준')
            ident(c['id'])
            ident(c['target_id'])
            text(c['label'])
            text(c['command'])
            require(c['scope'] in ('project', 'phase', 'task'), '검사 범위')
            require(type(c['expected_exit_code']) is int and -255 <= c['expected_exit_code'] <= 255, '예상 종료 코드')
            require(c['scope'] != 'project' or c['target_id'] == p['id'], '프로젝트 검사 대상')
            require(c['scope'] != 'phase' or c['target_id'] in phase_ids, '단계 검사 대상')
        unique(p['criteria'])
        if catalog['version'] == 3:
            require(p['runs'] == [], 'v3 legacy runs must be empty')
            management.validate(p, sys.modules[__name__] if __name__ in sys.modules else None)
        criterion_ids = {c['id'] for c in p['criteria']}
        for run in array(p['runs']):
            keys(run, ('criterion_id', 'revision', 'at', 'exit_code', 'session_id', 'evidence', 'criterion_signature'), '검사 기록')
            require(run['criterion_id'] in criterion_ids, '검사 기록 기준 참조')
            ident(run['revision'])
            ident(run['session_id'])
            time(run['at'])
            require(run['exit_code'] is None or type(run['exit_code']) is int and -255 <= run['exit_code'] <= 255, '종료 코드')
            text(run['evidence'])
            require(isinstance(run['criterion_signature'], str) and re.fullmatch('[a-f0-9]{64}', run['criterion_signature']), '검사 signature')
    unique(projects)


def validate_store(store):
    keys(store, ('version', 'sources'), 'central store')
    require(type(store['version']) is int and store['version'] == 1 and isinstance(store['sources'], dict), 'central store 버전')
    require(len(store['sources']) <= 1000, '출처 한도')
    for key, source in store['sources'].items():
        require(isinstance(source, dict) and {'actor_id', 'environment_id', 'project_id', 'label', 'evidence_mode', 'events'} <= set(source), 'central 출처 필드')
        identity = {k: source[k] for k in ('actor_id', 'environment_id', 'project_id')}
        require(source_identity(identity) == key, 'central 출처 키 불일치')
        text(source['label'], 160)
        require(source['evidence_mode'] in MODES and isinstance(source['events'], dict) and len(source['events']) <= MAX_ARRAY, 'central 출처 기록')
        for event_id, record in source['events'].items():
            keys(record, ('event', 'received_at', 'file_sha256', 'line'), 'central 이벤트 근거')
            require(central.valid_event(record['event'], source['project_id']) and record['event']['event_id'] == event_id, 'central 이벤트 형식')
            time(record['received_at'])
            require(isinstance(record['file_sha256'], str) and re.fullmatch('[a-f0-9]{64}', record['file_sha256']) and type(record['line']) is int and record['line'] > 0, 'central 파일 근거')


def build_model(store=None, catalog=None, now=None):
    store = {'version': 1, 'sources': {}} if store is None else store
    catalog = {'version': 1, 'projects': []} if catalog is None else catalog
    for value in (store, catalog):
        require(len(canonical(value).encode()) <= MAX_FILE, '입력 파일 한도')
        validate_tree(value)
    validate_store(store)
    validate_catalog(catalog)
    observed = dt.datetime.now(dt.timezone.utc) if now is None else time(now) if isinstance(now, str) else now
    require(isinstance(observed, dt.datetime) and observed.utcoffset() == dt.timedelta(0), '현재 UTC 시각')
    generated = observed.isoformat().replace('+00:00', 'Z')
    v3 = catalog['version'] == 3
    v2 = catalog['version'] >= 2 or any(r['event']['schema_version'] == 2 for source in store['sources'].values() for r in source['events'].values())
    projects, assigned, modes = [], set(), set()
    declarations = [(p, f'catalog.projects[{i}]') for i, p in enumerate(catalog['projects'])]
    for p in catalog['projects']:
        assigned.update(central.source_key(r) for r in p['source_refs'])
    for key, source in sorted(store['sources'].items()):
        if key not in assigned:
            declarations.append(({'id': 'unmapped-' + hashlib.sha256(key.encode()).hexdigest()[:16], 'name': source['label'], 'goal': '목표 미입력 · 출처 미연결', 'current_revision': 'unknown', 'current_phase': None, 'source_refs': [{k: source[k] for k in ('actor_id', 'environment_id', 'project_id')}], 'phases': [], 'documents': [], 'criteria': [], 'runs': []}, 'central.unmapped'))
    require(len(declarations) <= 1000, '프로젝트 한도')
    require(len({p['id'] for p, _ in declarations}) == len(declarations), 'fallback 프로젝트 ID 충돌')
    for p, ref in declarations:
        management_view = None
        if v3 and 'management' in p:
            derived_runs, management_view = management.derive(p, observed)
            p = dict(p, runs=derived_runs)
        alerts, timeline, sessions, sources = [], [], {}, []
        connections = [{**c, 'authority':'declared', 'source_ref':f'{ref}.connections[{i}]'} for i,c in enumerate(p.get('connections', []))]
        def add(at, kind, title, detail, session_id, source_ref):
            timeline.append(dict(at=at, kind=kind, title=title, detail=detail, session_id=session_id, source_ref=source_ref))
        for source_ref in p['source_refs']:
            source = store['sources'].get(central.source_key(source_ref))
            if source is None:
                alerts.append('연결 출처의 관측 기록 없음: ' + source_ref['actor_id'] + '/' + source_ref['environment_id'])
                modes.add('declared')
                sources.append({**source_ref, 'evidence_mode': 'declared', 'event_count': 0})
                continue
            modes.add(source['evidence_mode'])
            sources.append({**source_ref, 'evidence_mode': source['evidence_mode'], 'event_count': len(source['events'])})
            for event_id, record in sorted(source['events'].items()):
                e = record['event']
                session_id = e['session_id']
                if session_id:
                    identity = (session_id, source['actor_id'], source['environment_id'])
                    sessions.setdefault(identity, dict(id=session_id, actor_id=source['actor_id'], environment_id=source['environment_id'], event_count=0))['event_count'] += 1
                evidence = f"central {source['actor_id']}/{source['environment_id']} event_id={event_id} file_sha256={record['file_sha256']} line={record['line']}"
                if e['kind'].startswith('tool.') and (e['data'].get('connection') or e['tool_name']=='MCP'):
                    c = e['data'].get('connection', dict(server=None,tool=None,status=e['kind'].split('.')[1],duration_ms=None,operation='unknown',resources=[],artifact_refs=[]))
                    connections.append(dict(c, id='connection-' + hashlib.sha256((central.source_key(source_ref) + e['event_id']).encode()).hexdigest()[:32], actor_id=source['actor_id'], environment_id=source['environment_id'], session_id=session_id, agent_id=e['agent_id'], tool_call_id=e['tool_call_id'], at=e['observed_at'], authority='observed', source_ref=evidence))
                add(e['observed_at'], 'event', e['kind'], json.dumps(e, ensure_ascii=False, sort_keys=True, indent=2), session_id, evidence)
                if time(e['observed_at']) > observed:
                    alerts.append('미래 이벤트: ' + event_id)
        documents = []
        for i, doc in enumerate(p['documents']):
            dref = f'{ref}.documents[{i}]'
            documents.append({**doc, 'source_ref': dref})
            add(doc['at'], 'document', doc['title'] + ' · ' + doc['version'], doc['summary'], doc['session_id'], dref)
            identity = (doc['session_id'], doc['actor_id'], doc['environment_id'])
            sessions.setdefault(identity, dict(id=doc['session_id'], actor_id=doc['actor_id'], environment_id=doc['environment_id'], event_count=0))
            if time(doc['at']) > observed:
                alerts.append('미래 문서: ' + doc['id'])
        if management_view:
            for attempt in management_view['attempts']:
                identity = (attempt['session_id'], attempt['actor_id'], attempt['environment_id'])
                sessions.setdefault(identity, dict(id=attempt['session_id'], actor_id=attempt['actor_id'], environment_id=attempt['environment_id'], event_count=0))
            for field in ('objectives','plans','test_plans','harness','graphs'):
                for i, record in enumerate(management_view[field]):
                    add(record['at'], 'management', field + ' · ' + record['id'], str(record.get('reason',record.get('summary',record.get('source',record.get('title',record.get('generator','관리 기록'))))))[:2000], None, f'{ref}.management.{field}[{i}]')
            for i, attempt in enumerate(management_view['attempts']):
                if attempt['provenance']=='declared':
                    add(attempt['at'], 'management', '선언된 검사 · ' + attempt['id'], attempt['summary'], attempt['session_id'], f'{ref}.management.attempts[{i}]')
        criteria = {c['id']: c for c in p['criteria']}
        runs = []
        for i, run in enumerate(p['runs']):
            c = criteria[run['criterion_id']]
            status = 'pass' if run['exit_code'] == c['expected_exit_code'] else 'fail'
            if run['exit_code'] is None:
                status = 'unknown'
            if run['criterion_signature'] != criterion_signature(c):
                status = 'unknown'
                alerts.append('기준 변경 또는 signature 불일치: ' + c['id'] + ' · 검사 재입력 필요')
            if time(run['at']) > observed:
                status = 'unknown'
                alerts.append('미래 검사 기록: ' + c['id'])
            matching_sessions = [identity for identity in sessions if identity[0] == run['session_id']]
            if not matching_sessions:
                alerts.append('검사 세션 출처 미관측: ' + run['session_id'] + ' · 사용자/환경 귀속 불명')
            elif len(matching_sessions) > 1:
                alerts.append('검사 세션 출처 모호: ' + run['session_id'] + ' · 사용자/환경을 확인하세요')
            runs.append({**run, 'status': status, 'source_ref': f'{ref}.runs[{i}]'})
        peer_groups = {}
        for run in runs:
            peer_groups.setdefault((run['criterion_id'], run['revision'], time(run['at'])), set()).add((run['exit_code'], run['criterion_signature']))
        for run in runs:
            if len(peer_groups[(run['criterion_id'], run['revision'], time(run['at']))]) > 1:
                run['status'] = 'unknown'
                alerts.append('동일 시각 검사 충돌: ' + run['criterion_id'] + ' · ' + run['revision'])
            add(run['at'], 'check', criteria[run['criterion_id']]['label'] + ' · ' + run['status'], run['revision'] + ' · ' + criteria[run['criterion_id']]['command'] + '\n가져온 검사 기록 (실행하지 않음): ' + run['evidence'], run['session_id'], run['source_ref'])
        indexed_runs = {}
        for run in runs:
            indexed_runs.setdefault((run['criterion_id'], run['revision']), []).append(run)
        run_times = {}
        for key, records in indexed_runs.items():
            records.sort(key=lambda r: time(r['at']))
            run_times[key] = [time(r['at']) for r in records]
        def state(required, revision, cutoff=None):
            if not required:
                return 'unknown'
            statuses = []
            for c in required:
                key = (c['id'], revision)
                position = bisect_right(run_times.get(key, []), min(observed, cutoff) if cutoff else observed) - 1
                latest = indexed_runs[key][position] if position >= 0 else None
                statuses.append(latest['status'] if latest else 'unknown')
            return 'failed' if 'fail' in statuses else 'complete' if all(s == 'pass' for s in statuses) else 'in_progress'
        project_criteria = [c for c in p['criteria'] if c['scope'] == 'project']
        status = state(project_criteria, p['current_revision'])
        completed_revisions = set()
        for revision, instant in sorted({(r['revision'], r['at']) for r in runs}, key=lambda item: (item[0], time(item[1]))):
            if state(project_criteria, revision, time(instant)) == 'complete':
                if revision not in completed_revisions:
                    add(instant, 'milestone', '프로젝트 완료 기준 충족 · ' + revision, '당시 기준의 가져온 검사 기록이 모두 통과했습니다.', None, ref + '.runs')
                completed_revisions.add(revision)
        if status == 'in_progress' and management_view:
            test_plans = {(t['id'],t['version']):t for t in management_view['test_plans']}
            if any(a['provenance']=='runner' and time(a['at'])<=observed and a['exit_code']==test_plans[(a['test_plan_id'],a['test_plan_version'])]['definition']['expected_exit_code'] and (a['status']=='unknown' or a['criterion_signature'] != criterion_signature(criteria[test_plans[(a['test_plan_id'],a['test_plan_version'])]['criterion_id']])) for a in management_view['attempts']):
                status = 'revalidation'
        if status == 'in_progress' and completed_revisions - {p['current_revision']}:
            status = 'revalidation'
        reason = {'unknown': '프로젝트 범위 완료 기준이 없습니다.', 'complete': '현재 revision의 프로젝트 범위 최신 검사 기록이 모두 통과했습니다.', 'failed': '현재 revision의 프로젝트 범위 최신 검사 기록에 실패가 있습니다.', 'revalidation': '과거 revision 완료 후 현재 revision 검사 기록이 부족합니다.', 'in_progress': '현재 revision의 프로젝트 범위 검사 기록이 부족하거나 불명입니다.'}[status]
        phases = [{**phase, 'status': state([c for c in p['criteria'] if c['scope'] == 'phase' and c['target_id'] == phase['id']], p['current_revision'])} for phase in p['phases']]
        projects.append(dict(id=p['id'], name=p['name'], goal=p['goal'], owners=sorted({r['actor_id'] for r in p['source_refs']}), current_revision=p['current_revision'], current_phase=p['current_phase'], status=status, status_reason=reason + ' 목표/문서는 ' + ref + '의 명시적 입력입니다.', phases=phases, documents=documents, criteria=p['criteria'], runs=runs, sessions=sorted(sessions.values(), key=lambda s: (s['actor_id'], s['environment_id'], s['id'])), timeline=sorted(timeline, key=lambda t: (time(t['at']), t['kind'], t['source_ref'], t['title'])), sources=sources, alerts=sorted(set(alerts)), last_updated=max((t['at'] for t in timeline), key=time, default=None)))
        if v2: projects[-1]['connections'] = connections
        if v3: projects[-1]['management'] = management_view
    if catalog['projects'] and not modes:
        modes.add('declared')
    model = dict(schema_version=3 if v3 else 2 if v2 else 1, generated_at=generated, evidence_mode='mixed' if len(modes) > 1 else next(iter(modes), 'declared'), projects=projects)
    validate_tree(model)
    require(len(canonical(model).encode()) <= 6_000_000, '모델 출력 한도')
    return model


def render_html(model, template=None):
    template = (Path(__file__).parent / 'dashboard.html').read_text() if template is None else template
    pattern = r'(<script\b[^>]*\bid=["\x27]pms-data["\x27][^>]*>)(.*?)(</script\s*>)'
    payload = json.dumps(model, ensure_ascii=True, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    rendered, count = re.subn(pattern, lambda match: match[1] + payload + match[3], template, flags=re.S)
    require(count == 1, '템플릿 pms-data 영역')
    return rendered


def read_json(path):
    require(path.stat().st_size <= MAX_FILE, '입력 파일 한도')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, '중복 JSON 키')
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('잘못된 JSON 숫자')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('store', 'catalog', 'out', 'json-out'):
        parser.add_argument('--' + option, type=Path, required=option == 'out')
    args = parser.parse_args()
    try:
        outputs = [path.resolve() for path in (args.out, args.json_out) if path]
        inputs = [path.resolve() for path in (args.store, args.catalog) if path]
        require(len(outputs) == len(set(outputs)) and not set(outputs).intersection(inputs), '입력 파일 덮어쓰기 금지')
        model = build_model(read_json(args.store) if args.store else None, read_json(args.catalog) if args.catalog else None)
        content = render_html(model)
        args.out.write_text(content)
        if args.json_out:
            args.json_out.write_text(json.dumps(model, ensure_ascii=False, separators=(',', ':')))
        print('projects=' + str(len(model['projects'])))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print('portfolio: 입력 형식·참조·비공개 정보 또는 파일 오류', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
