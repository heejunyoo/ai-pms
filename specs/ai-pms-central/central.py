#!/usr/bin/env python3
"""Local, offline central import and manager report for logger v1 JSONL."""
import argparse
import datetime as dt
import fcntl
import hashlib
import html
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import uuid
import importlib.util
_connectivity_spec = importlib.util.spec_from_file_location("pms_connectivity", Path(__file__).with_name("connectivity.py"))
connectivity = importlib.util.module_from_spec(_connectivity_spec)
_connectivity_spec.loader.exec_module(connectivity)

MAX_FILE = 8 * 1024 * 1024
MAX_LINE = 65536
MAX_EVENTS = 10000
MAX_STORE = 64 * 1024 * 1024
STALE_HOURS = 24
LINKS = ('phase_id', 'baseline_version', 'task_id', 'decision_id', 'artifact_id', 'artifact_version', 'check_id')
IDS = ('session_id', 'agent_id', 'parent_agent_id', 'turn_id', 'tool_call_id')
KEYS = {'schema_version', 'adapter_version', 'event_id', 'observed_at', 'occurred_at', 'source',
        'native_event', 'kind', 'authority', 'project_id', 'tool_name', 'links', 'data',
        'missing_fields', *IDS}
NATIVE = {'SessionStart': 'session.start', 'SessionEnd': 'session.end',
          'UserPromptSubmit': 'prompt.observed', 'PreToolUse': 'tool.requested',
          'PostToolUse': 'tool.completed', 'PostToolUseFailure': 'tool.failed',
          'SubagentStart': 'agent.start', 'SubagentStop': 'agent.end', 'Stop': 'turn.stopped',
          'unknown': 'unknown'}
TOOLS = set('MCP Bash Read Write Edit MultiEdit Glob Grep Task Agent WebFetch WebSearch NotebookEdit TodoWrite Skill ToolSearch AskUserQuestion exec_command write_stdin apply_patch spawn_agent send_message wait_agent view_image'.split())
DATA = {'project.baseline': {'summary', 'scope', 'goal'},
        'decision.recorded': {'summary', 'reason', 'scope_added', 'scope_removed'},
        'artifact.recorded': {'summary'}, 'check.recorded': {'summary', 'status', 'environment'},
        'acceptance.recorded': {'summary', 'status', 'environment'}}
REQUIRED = {'project.baseline': ('phase_id', 'baseline_version'),
            'decision.recorded': ('phase_id', 'baseline_version', 'decision_id'),
            'artifact.recorded': ('artifact_id', 'artifact_version'),
            'check.recorded': ('check_id', 'artifact_id', 'artifact_version'),
            'acceptance.recorded': ('artifact_id', 'artifact_version')}
PRIVATE = re.compile(r'(?i)(?:\bBearer\s+\S+|\b(?:sk|ghp|github_pat|AIza|xox[baprs])[-_][A-Za-z0-9_-]{8,}|\bAIza[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY|\b(?:password|secret|token|api[_ -]?key)\s*[:=]\s*\S+|(?:/' + 'Users/' + r'|/home/|/private/|/tmp/|/root/|[A-Z]:[\\/]|~/)[^\s]*)')
IDENT = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}\Z')
TIME = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)\Z')


def parse_json(raw):
    return json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def uid(value):
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False


def identifier(value):
    return isinstance(value, str) and IDENT.fullmatch(value) is not None and not PRIVATE.search(value)


def safe_text(value, limit):
    return (isinstance(value, str) and len(value) <= limit and not PRIVATE.search(value)
            and not any(ord(c) < 32 and c not in '\n\t' for c in value))


def timestamp(value):
    if not isinstance(value, str) or len(value) > 40 or not TIME.fullmatch(value):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.utcoffset() == dt.timedelta(0):
            return parsed
    except ValueError:
        pass
    return None


def valid_event(e, project):
    if not isinstance(e, dict) or set(e) != KEYS:
        return False
    if type(e['schema_version']) is not int or e['schema_version'] not in (1, 2) or e['adapter_version'] != str(e['schema_version']) or not uid(e['event_id']) or e['project_id'] != project:
        return False
    if not timestamp(e['observed_at']) or (e['occurred_at'] is not None and not timestamp(e['occurred_at'])):
        return False
    if not isinstance(e['source'], str) or e['source'] not in ('codex', 'claude', 'manual') or not identifier(e['native_event']):
        return False
    if not isinstance(e['kind'], str) or e['kind'] not in (*DATA, *NATIVE.values()):
        return False
    manual = e['kind'] in DATA
    if manual:
        if e['source'] != 'manual' or e['authority'] != 'declared' or e['native_event'] != e['kind']:
            return False
    elif e['source'] == 'manual' or e['authority'] != 'observed' or NATIVE.get(e['native_event']) != e['kind']:
        return False
    if any(e[key] is not None and not identifier(e[key]) for key in IDS):
        return False
    if e['tool_name'] is not None and (not isinstance(e['tool_name'], str) or e['tool_name'] not in TOOLS):
        return False
    if not isinstance(e['links'], dict) or set(e['links']) != set(LINKS):
        return False
    if any(value is not None and not identifier(value) for value in e['links'].values()):
        return False
    allowed_data = DATA[e['kind']] if manual else {'connection'} if e['schema_version'] == 2 and e['kind'].startswith('tool.') else set()
    if not isinstance(e['data'], dict) or not set(e['data']) <= allowed_data:
        return False
    if 'connection' in e['data'] and (not connectivity.valid(e['data']['connection']) or e['data']['connection']['status'] != e['kind'].removeprefix('tool.')):
        return False
    if manual:
        if any(not e['links'][key] for key in REQUIRED[e['kind']]):
            return False
        if any(not safe_text(value, 80 if key == 'environment' else 2000) for key, value in e['data'].items()):
            return False
        if e['kind'] == 'project.baseline' and any(not e['data'].get(key, '').strip() for key in ('goal', 'scope')):
            return False
        if e['kind'] == 'decision.recorded' and any(not e['data'].get(key, '').strip() for key in ('summary', 'reason')):
            return False
        if e['kind'] == 'check.recorded' and e['data'].get('status') not in ('pass', 'fail', 'unknown'):
            return False
        if e['kind'] == 'acceptance.recorded' and e['data'].get('status') not in ('accepted', 'rejected', 'pending'):
            return False
    missing = e['missing_fields']
    return (isinstance(missing, list) and len(missing) <= 30 and
            all(isinstance(v, str) and 0 < len(v) <= 100 and re.fullmatch(r'[A-Za-z0-9_.:-]+', v) for v in missing))


def private_dir(path):
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('symlink storage directory')
    info = path.stat()
    if info.st_uid != os.getuid() or not stat.S_ISDIR(info.st_mode):
        raise ValueError('unsafe storage directory')
    path.chmod(0o700)


def checked_file(path):
    if path.is_symlink():
        raise ValueError('symlink storage file')
    info = path.stat()
    if info.st_uid != os.getuid() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError('unsafe storage file')
    path.chmod(0o600)


def atomic_write(path, contents):
    if path.exists() or path.is_symlink():
        checked_file(path)
    fd, name = tempfile.mkstemp(prefix='.central-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            os.fchmod(out.fileno(), 0o600)
            out.write(contents)
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load_store(root):
    path = root / 'central.json'
    if not path.exists() and not path.is_symlink():
        return {'version': 1, 'sources': {}}
    checked_file(path)
    raw = path.read_bytes()
    if len(raw) > MAX_STORE:
        raise ValueError('storage limit')
    store = parse_json(raw)
    if not isinstance(store, dict) or set(store) != {'version', 'sources'} or store['version'] != 1 or not isinstance(store['sources'], dict):
        raise ValueError('invalid storage')
    return store


def source_key(source):
    return json.dumps([source[key] for key in ('actor_id', 'environment_id', 'project_id')], ensure_ascii=True)


def read_manifest(path):
    raw = path.read_bytes()
    if len(raw) > 1024 * 1024:
        raise ValueError('manifest limit')
    doc = parse_json(raw)
    if not isinstance(doc, dict) or set(doc) != {'sources'} or not isinstance(doc['sources'], list) or len(doc['sources']) > 100:
        raise ValueError('invalid manifest')
    seen = set()
    for source in doc['sources']:
        if not isinstance(source, dict) or set(source) != {'actor_id', 'environment_id', 'project_id', 'label', 'evidence_mode', 'files'}:
            raise ValueError('invalid source declaration')
        if not all(identifier(source[key]) for key in ('actor_id', 'environment_id')) or not uid(source['project_id']):
            raise ValueError('invalid source identity')
        if not safe_text(source['label'], 80) or not source['label'].strip() or source['evidence_mode'] not in ('synthetic', 'local-execution'):
            raise ValueError('invalid source label or evidence mode')
        if not isinstance(source['files'], list) or len(source['files']) > 100 or not all(isinstance(v, str) and v and len(v) <= 255 for v in source['files']):
            raise ValueError('invalid files')
        key = source_key(source)
        if key in seen:
            raise ValueError('duplicate source declaration')
        seen.add(key)
    return doc


def file_path(base, value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or path == Path('.'):
        raise ValueError('unsafe relative file')
    candidate = base / path
    if any(part.is_symlink() for part in (candidate, *list(candidate.parents)[:len(path.parts)])):
        raise ValueError('symlink input file')
    return candidate


def canonical(event):
    return json.dumps(event, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)


def import_sources(manifest, root):
    private_dir(root)
    lock_path = root / 'central.lock'
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'r+') as lock:
        info = os.fstat(lock.fileno())
        if info.st_uid != os.getuid() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('unsafe lock file')
        os.fchmod(lock.fileno(), 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        store = load_store(root)
        now = dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
        for declaration in read_manifest(manifest)['sources']:
            key = source_key(declaration)
            previous = store['sources'].get(key)
            if previous and (previous['label'], previous['evidence_mode']) != (declaration['label'], declaration['evidence_mode']):
                raise ValueError('source declaration changed')
            entry = previous or {k: declaration[k] for k in ('actor_id', 'environment_id', 'project_id', 'label', 'evidence_mode')}
            entry.setdefault('events', {})
            stats = {'new': 0, 'duplicates': 0, 'conflicts': 0, 'invalid': 0, 'missing_files': 0, 'empty_files': 0, 'read_failures': 0, 'limited': 0}
            for name in declaration['files']:
                try:
                    path = file_path(manifest.parent, name)
                    if not path.is_file():
                        stats['missing_files'] += 1
                        continue
                    if path.stat().st_size > MAX_FILE:
                        stats['limited'] += 1
                        continue
                    raw = path.read_bytes()
                    if not raw.strip():
                        stats['empty_files'] += 1
                        continue
                    digest = hashlib.sha256(raw).hexdigest()
                    for line_no, line in enumerate(raw.splitlines(), 1):
                        if not line.strip():
                            continue
                        if len(line) > MAX_LINE:
                            stats['limited'] += 1
                            continue
                        try:
                            event = parse_json(line)
                            if not valid_event(event, declaration['project_id']):
                                raise ValueError('invalid event')
                        except (ValueError, UnicodeDecodeError, TypeError, KeyError):
                            stats['invalid'] += 1
                            continue
                        existing = entry['events'].get(event['event_id'])
                        if existing:
                            if canonical(existing['event']) == canonical(event):
                                stats['duplicates'] += 1
                            else:
                                stats['conflicts'] += 1
                            continue
                        if len(entry['events']) >= MAX_EVENTS:
                            stats['limited'] += 1
                            continue
                        entry['events'][event['event_id']] = {'event': event, 'received_at': now,
                                                               'file_sha256': digest, 'line': line_no}
                        stats['new'] += 1
                except (OSError, ValueError):
                    stats['read_failures'] += 1
            if not declaration['files']:
                stats['missing_files'] += 1
            entry['last_import'] = {'at': now, **stats}
            entry['totals'] = {k: entry.get('totals', {}).get(k, 0) + v for k, v in stats.items()}
            store['sources'][key] = entry
        payload = json.dumps(store, ensure_ascii=True, allow_nan=False).encode()
        if len(payload) > MAX_STORE:
            raise ValueError('storage limit')
        atomic_write(root / 'central.json', payload)
    return store


def load_delivery_state(path):
    """Read untrusted transport metadata without changing permissions or exposing input."""
    path = Path(path)
    unknown = {'error': 'delivery_state_unknown', 'registered_contexts': [], 'batches': []}
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('duplicate metadata key')
            value[key] = item
        return value
    try:
        marker = path.parent / 'delivery-state.error'
        marked = marker.exists() or marker.is_symlink()
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as source:
            info = os.fstat(source.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                    info.st_nlink != 1 or info.st_mode & 0o077 or info.st_size > MAX_FILE):
                raise ValueError('unsafe metadata')
            raw = source.read(MAX_FILE + 1)
        if len(raw) > MAX_FILE:
            raise ValueError('metadata limit')
        doc = json.loads(raw, object_pairs_hook=pairs,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
        if (not isinstance(doc, dict) or set(doc) != {'version', 'registered_contexts', 'batches'} or
                type(doc['version']) is not int or doc['version'] != 1 or
                not isinstance(doc['registered_contexts'], list) or len(doc['registered_contexts']) > 100 or
                not isinstance(doc['batches'], list)):
            raise ValueError('metadata schema')
        contexts, batches = set(), set()
        for context in doc['registered_contexts']:
            if (not isinstance(context, dict) or set(context) != {'actor_id', 'environment_id', 'project_id', 'label'} or
                    not all(identifier(context[k]) for k in ('actor_id', 'environment_id')) or
                    not uid(context['project_id']) or not safe_text(context['label'], 80) or not context['label'].strip()):
                raise ValueError('metadata context')
            key = source_key(context)
            if key in contexts:
                raise ValueError('duplicate metadata context')
            contexts.add(key)
        reasons = {'queued': {'none'}, 'aggregated': {'none'}, 'conflict': {'event_conflict'},
                   'failed': {'import_failed', 'registration_changed', 'inbox_invalid'}}
        for batch in doc['batches']:
            if (not isinstance(batch, dict) or set(batch) != {'context_key', 'batch_id', 'payload_sha256',
                    'received_at', 'event_count', 'state', 'reason_code', 'updated_at'}):
                raise ValueError('metadata batch')
            key = batch['context_key']
            if not isinstance(key, str) or len(key) > 400:
                raise ValueError('metadata key')
            parts = json.loads(key, object_pairs_hook=pairs)
            if (not isinstance(parts, list) or len(parts) != 3 or
                    not all(identifier(v) for v in parts[:2]) or not uid(parts[2]) or
                    key != source_key(dict(zip(('actor_id', 'environment_id', 'project_id'), parts)))):
                raise ValueError('metadata key')
            if (not uid(batch['batch_id']) or not isinstance(batch['payload_sha256'], str) or
                    not re.fullmatch('[a-f0-9]{64}', batch['payload_sha256']) or
                    type(batch['event_count']) is not int or not 0 <= batch['event_count'] <= 100 or
                    not isinstance(batch['state'], str) or batch['state'] not in reasons or
                    not isinstance(batch['reason_code'], str) or batch['reason_code'] not in reasons[batch['state']] or
                    timestamp(batch['received_at']) is None or timestamp(batch['updated_at']) is None or
                    timestamp(batch['updated_at']) < timestamp(batch['received_at'])):
                raise ValueError('metadata batch values')
            identity = (key, batch['batch_id'])
            if identity in batches:
                raise ValueError('duplicate metadata batch')
            batches.add(identity)
        if marked or marker.exists() or marker.is_symlink():
            doc['error'] = 'delivery_state_unknown'
        return doc
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        return unknown


def delivery_issues(delivery_state):
    if delivery_state is None:
        return []
    issues = []
    if delivery_state.get('error'):
        issues.append('전달상태 불명')
    if delivery_state.get('central_error'):
        issues.append('중앙 저장 읽기 실패')
    keys = {source_key(c) for c in delivery_state['registered_contexts']}
    if any(b['context_key'] not in keys or b['reason_code'] == 'registration_changed'
           for b in delivery_state['batches']):
        issues.append('등록 불일치: 제거·변경된 환경의 전달 기록 확인 필요')
    return issues


def summarize(store, delivery_state=None):
    now = dt.datetime.now(dt.timezone.utc)
    projects = []
    sources = dict(store['sources'])
    if delivery_state is not None:
        for context in delivery_state['registered_contexts']:
            key = source_key(context)
            if key not in sources:
                sources[key] = {**context, 'evidence_mode': 'synthetic', 'events': {},
                                'last_import': {'at': None, **{k: 0 for k in ('new', 'duplicates', 'conflicts', 'invalid',
                                    'missing_files', 'empty_files', 'read_failures', 'limited')}}, 'totals': {}}
    for key, source in sorted(sources.items()):
        records = sorted(source['events'].values(), key=lambda r: (timestamp(r['event']['observed_at']), r['event']['event_id']))
        events = [record['event'] for record in records]
        by_kind = lambda kind: [e for e in events if e['kind'] == kind]
        baselines = by_kind('project.baseline')
        baseline_keys = {(e['links']['phase_id'], e['links']['baseline_version']) for e in baselines}
        decisions = by_kind('decision.recorded')
        connected_decisions = [e for e in decisions if (e['links']['phase_id'], e['links']['baseline_version']) in baseline_keys]
        artifacts = by_kind('artifact.recorded')
        artifact_keys = {(e['links']['artifact_id'], e['links']['artifact_version']) for e in artifacts}
        checks = by_kind('check.recorded')
        connected_checks = [e for e in checks if (e['links']['artifact_id'], e['links']['artifact_version']) in artifact_keys]
        acceptances = by_kind('acceptance.recorded')
        connected_acceptances = [e for e in acceptances if (e['links']['artifact_id'], e['links']['artifact_version']) in artifact_keys]
        observed_agents = {(e['source'], e['session_id'], e['agent_id']) for e in events if e['authority'] == 'observed' and e['agent_id'] and e['session_id']}
        declarations = [e for e in events if e['authority'] == 'declared' and e['agent_id']]
        def candidates(e):
            return sorted(source_name for source_name, session, agent in observed_agents if session == e['session_id'] and agent == e['agent_id']) if e['session_id'] else []
        unlinked_agents = [e for e in declarations if not candidates(e)]
        ambiguous_agents = [e for e in declarations if len(candidates(e)) > 1]
        relations = []
        for artifact in artifacts:
            artifact_id, version = artifact['links']['artifact_id'], artifact['links']['artifact_version']
            artifact_checks = [e for e in connected_checks if (e['links']['artifact_id'], e['links']['artifact_version']) == (artifact_id, version)]
            artifact_acceptances = [e for e in connected_acceptances if (e['links']['artifact_id'], e['links']['artifact_version']) == (artifact_id, version)]
            agent_candidates = candidates(artifact) if artifact['agent_id'] else []
            relations.append({'artifact_id': artifact_id, 'version': version, 'artifact_event_id': artifact['event_id'],
                              'agent_id': artifact['agent_id'], 'agent_status': '모호함' if len(agent_candidates) > 1 else '관측 후보' if agent_candidates else '미연결 선언' if artifact['agent_id'] else 'Agent 선언 없음',
                              'agent_sources': agent_candidates, 'checks': [{'event_id': e['event_id'], 'status': e['data']['status']} for e in artifact_checks],
                              'acceptances': [{'event_id': e['event_id'], 'status': e['data']['status']} for e in artifact_acceptances]})
        latest = events[-1]['observed_at'] if events else None
        issues = []
        if not baselines:
            issues.append('목표 없음')
            issues.append('Phase 불명')
        if len(decisions) != len(connected_decisions):
            issues.append('기준선 미연결 결정')
        if len(checks) != len(connected_checks):
            issues.append('산출물 검증 불일치')
        if len(acceptances) != len(connected_acceptances):
            issues.append('산출물 인수 미연결')
        if any(e['data']['status'] in ('fail', 'unknown') for e in connected_checks):
            issues.append('검사 실패·미확인')
        if any(e['data']['status'] in ('rejected', 'pending') for e in connected_acceptances):
            issues.append('인수 거절·대기')
        if unlinked_agents:
            issues.append('미연결 Agent 선언')
        if ambiguous_agents:
            issues.append('Agent 출처 모호함')
        stats = source['last_import']
        if stats['missing_files'] or stats['empty_files'] or stats['read_failures'] or not events:
            issues.append('연결 실패·입력 없음')
        if stats['invalid'] or stats['limited']:
            issues.append('수집 오류·한도')
        if stats['conflicts']:
            issues.append('event_id 충돌')
        totals = source.get('totals', {})
        if any(totals.get(k, 0) > stats.get(k, 0) for k in ('conflicts', 'invalid', 'limited', 'read_failures', 'missing_files', 'empty_files')):
            issues.append('과거 수집 오류 기록')
        if latest:
            observed = timestamp(latest)
            if observed > now:
                issues.append('미래 관측 시각')
            elif now - observed > dt.timedelta(hours=STALE_HOURS):
                issues.append('수집 지연')
        baseline = baselines[-1] if baselines else None
        decision = connected_decisions[-1] if connected_decisions else None
        projects.append({'key': key, 'actor_id': source['actor_id'], 'environment_id': source['environment_id'],
                         'project_id': source['project_id'], 'label': source['label'], 'evidence_mode': source['evidence_mode'],
                         'goal': baseline['data']['goal'] if baseline else None,
                         'phase': baseline['links']['phase_id'] if baseline else None,
                         'baseline_version': baseline['links']['baseline_version'] if baseline else None,
                         'scope': baseline['data']['scope'] if baseline else None,
                         'change': decision['data']['summary'] if decision else None,
                         'agent_count': len(observed_agents), 'unlinked_agent_count': len(unlinked_agents),
                         'ambiguous_agent_count': len(ambiguous_agents), 'artifact_count': len(artifacts),
                         'check_count': len(connected_checks), 'acceptance_count': len(connected_acceptances),
                         'relations': relations, 'issues': issues, 'last_observed': latest, 'last_import': stats, 'totals': totals,
                         'events': records})
    if delivery_state is not None:
        registered = {source_key(c): c for c in delivery_state['registered_contexts']}
        grouped = {}
        for batch in delivery_state['batches']:
            grouped.setdefault(batch['context_key'], []).append(batch)
        for project in projects:
            batches = grouped.get(project['key'], [])
            known = not delivery_state.get('error')
            counts = {state: sum(b['state'] == state for b in batches) for state in ('queued', 'aggregated', 'conflict', 'failed')}
            connected = max((b['received_at'] for b in batches), key=timestamp, default=None) if known else None
            project['delivery'] = {'known': known, 'registered': project['key'] in registered,
                                   'last_received': connected, 'counts': counts if known else None,
                                   'heartbeat_count': sum(b['event_count'] == 0 for b in batches) if known else None,
                                   'batches': batches if known else []}
            project['source_provenance'] = ('전달 집계 경로: 서버 mirror. SHA-256·행은 최초 중앙 수집 파일 기준이며 송신 로그 원파일과 다를 수 있습니다.'
                                            if batches else '최초 중앙 수집 파일의 SHA-256·행 기준')
            project['issues'].extend(delivery_issues(delivery_state))
            if project['key'] not in registered:
                project['issues'].append('현재 등록 없음')
            if known:
                for state, label in (('queued', '전달 대기'), ('failed', '전달 실패'), ('conflict', '전달 충돌')):
                    if counts[state]:
                        project['issues'].append(label)
                if not batches:
                    project['issues'].append('연결 확인 없음')
                if connected and now - timestamp(connected) > dt.timedelta(hours=STALE_HOURS):
                    project['issues'].append('전달 지연')
                if connected and timestamp(connected) > now:
                    project['issues'].append('미래 연결 시각')
            if not project['events']:
                project['issues'].append('작업 관측 없음')
    return projects


HTML = '''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI PMS 중앙 관리</title><style>
:root{font-family:system-ui,sans-serif;color:#172334;background:#f5f7fa}*{box-sizing:border-box}body{max-width:1320px;margin:auto;padding:24px;overflow-wrap:anywhere}h1,h2{margin:.2em 0 .6em}p{line-height:1.5}.banner{padding:12px 16px;background:#fff0d5;border-left:4px solid #ad6500}.muted{color:#526175}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}input,select,button{font:inherit;padding:9px;border:1px solid #8293a5;border-radius:6px;background:white}button{cursor:pointer;color:#174b83}button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #005fcc;outline-offset:2px}.tablewrap{overflow:auto;background:white;border:1px solid #d7dee5;border-radius:8px}table{border-collapse:collapse;width:100%;min-width:950px}th,td{text-align:left;padding:12px;border-bottom:1px solid #e0e6eb;vertical-align:top}th{background:#e8eef4}.tag{display:inline-block;margin:2px;padding:2px 6px;border-radius:4px;background:#e6edf7}.issue{background:#ffeadf;color:#813500}.card{background:white;border:1px solid #d7dee5;border-radius:8px;padding:18px;margin:18px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(230px,100%),1fr));gap:12px}.grid>div{background:#f5f7fa;padding:12px;border-radius:6px;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#101b2d;color:#eef4ff;padding:14px;border-radius:6px;max-height:500px;overflow:auto}.events{list-style:none;padding:0}.events li{border-bottom:1px solid #d7dee5;padding:10px 0;overflow-wrap:anywhere}.events button{display:block;text-align:left;width:100%;white-space:normal;overflow-wrap:anywhere}#provenance{overflow-wrap:anywhere}[hidden]{display:none!important}@media(max-width:600px){body{padding:12px}h1{font-size:1.5rem}.toolbar>*{width:100%}.card{padding:12px}table{min-width:0}#list-view thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}#list-view tbody tr{display:block;margin:10px;border:1px solid #d7dee5;border-radius:6px}#list-view td{display:block;overflow-wrap:anywhere;padding:8px 12px}#list-view td::before{display:block;font-weight:700;color:#526175;margin-bottom:3px}#list-view td:nth-child(1)::before{content:'출처 / 프로젝트'}#list-view td:nth-child(2)::before{content:'목표 / Phase'}#list-view td:nth-child(3)::before{content:'최근 범위 변경'}#list-view td:nth-child(4)::before{content:'Agent / 산출물 / 검사'}#list-view td:nth-child(5)::before{content:'관측 시각'}#list-view td:nth-child(6)::before{content:'관리 필요'}}
</style></head><body><header><h1>AI PMS 중앙 관리</h1><p>여러 출처의 로컬 기록을 비교하고 프로젝트에서 원본 이벤트까지 확인합니다.</p><p class="banner" id="mode"></p><p class="banner" id="delivery-banner" role="status" hidden></p></header><main><section id="list-view" aria-labelledby="list-heading"><h2 id="list-heading">프로젝트 목록</h2><div class="toolbar"><label>검색 <input id="query" type="search" placeholder="사용자, 환경, 목표, 프로젝트" autocomplete="off"></label><label>증거 유형 <select id="mode-filter"><option value="">전체</option><option value="synthetic">합성</option><option value="local-execution">로컬 실행</option></select></label></div><p id="count" role="status"></p><div class="tablewrap"><table><thead><tr><th scope="col">출처 / 프로젝트</th><th scope="col">목표 / Phase</th><th scope="col">최근 범위 변경</th><th scope="col">Agent / 산출물 / 검사</th><th scope="col">관측 시각</th><th scope="col">관리 필요</th></tr></thead><tbody id="rows"></tbody></table></div><div id="empty" class="card" hidden><h2>수집된 프로젝트가 없습니다</h2><p>manifest의 sources에 actor_id, environment_id, project_id, label, evidence_mode, 상대 JSONL files를 선언하세요.</p><pre>python3 specs/ai-pms-central/central.py import --manifest manifest.json --store STORE_DIR
python3 specs/ai-pms-central/central.py render --store STORE_DIR --output report.html</pre></div></section><section id="detail-view" hidden aria-labelledby="detail-heading"><button id="back" type="button">← 프로젝트 목록</button><h2 id="detail-heading">프로젝트</h2><div id="detail" class="card"></div><h3>관계 목록</h3><p class="muted">선언된 Agent ID는 관측 출처의 후보만 표시합니다. 산출물·검사·인수는 정확한 ID와 버전으로 연결합니다.</p><ul id="relations" class="events"></ul><h3>원본 근거</h3><p class="muted">이벤트 ID, 파일 SHA-256, 행 번호는 최초 수집 근거입니다. 파일 경로와 명령은 표시하지 않습니다.</p><ul id="events" class="events"></ul><section id="original" class="card" hidden aria-labelledby="original-heading"><h3 id="original-heading">원본 이벤트</h3><p id="provenance"></p><pre id="event-json"></pre></section></section></main><script id="data" type="application/json">__DATA__</script><script id="delivery-data" type="application/json">__DELIVERY__</script><script>
const projects=JSON.parse(document.getElementById('data').textContent);
const deliveryInfo=JSON.parse(document.getElementById('delivery-data').textContent);
const el=id=>document.getElementById(id);
function node(tag,value){const n=document.createElement(tag);if(value!==undefined)n.textContent=String(value);return n}
function cell(row,value){const td=node('td',value);row.append(td);return td}
function deliveryText(p){if(!p.delivery)return '';const d=p.delivery;if(!d.known)return '전달상태 불명';const c=d.counts;return `대기 ${c.queued} · 집계 ${c.aggregated} · 실패 ${c.failed} · 충돌 ${c.conflict} · heartbeat ${d.heartbeat_count} (업무 관측 증거 아님)`}
function showList(){el('detail-view').hidden=true;el('list-view').hidden=false;el('original').hidden=true;location.hash='';renderList()}
function renderList(){const q=el('query').value.toLocaleLowerCase(),mode=el('mode-filter').value;el('rows').replaceChildren();let count=0;for(const p of projects){if(mode&&p.evidence_mode!==mode)continue;if(q&&!([p.actor_id,p.environment_id,p.project_id,p.label,p.goal||'',p.phase||''].join(' ').toLocaleLowerCase().includes(q)))continue;count++;const tr=node('tr');const first=cell(tr,'');const b=node('button',p.label+' · '+p.actor_id+' / '+p.environment_id);b.type='button';b.addEventListener('click',()=>showProject(p));first.append(b,node('div',p.project_id),node('small',p.evidence_mode==='synthetic'?'합성':'로컬 실행'));cell(tr,(p.goal||'목표 없음')+' / '+(p.phase||'Phase 불명')+(p.baseline_version?' · '+p.baseline_version:''));cell(tr,p.change||'변경 선언 없음');cell(tr,`${p.agent_count} 관측 · ${p.unlinked_agent_count} 미연결 / ${p.artifact_count} 산출물 / ${p.check_count} 검사 / ${p.acceptance_count} 인수`);const times=cell(tr,p.last_observed||'관측 없음');if(p.delivery)times.append(node('div','마지막 연결 확인: '+(p.delivery.last_received||'없음')),node('small',deliveryText(p)));const issues=cell(tr,'');for(const issue of p.issues){const t=node('span',issue);t.className='tag issue';issues.append(t)}if(!p.issues.length)issues.textContent='표시된 항목 없음';el('rows').append(tr)}el('count').textContent=`${count}개 프로젝트`;el('empty').hidden=projects.length!==0}
function showProject(p){
 el('list-view').hidden=true;el('detail-view').hidden=false;el('original').hidden=true;
 el('detail-heading').textContent=p.label+' · '+p.actor_id+' / '+p.environment_id;location.hash=encodeURIComponent(p.key);
 const box=el('detail');box.replaceChildren();const grid=node('div');grid.className='grid';
 for(const [name,value] of [['출처 유형',p.evidence_mode==='synthetic'?'합성 데이터':'로컬 실행'],['프로젝트 ID',p.project_id],['목표',p.goal||'누락'],['Phase / 기준 버전',(p.phase||'불명')+' / '+(p.baseline_version||'없음')],['범위',p.scope||'누락'],['최근 범위 변경',p.change||'선언 없음'],['Agent',`${p.agent_count} 출처별 관측, ${p.unlinked_agent_count} 선언 미연결, ${p.ambiguous_agent_count} 출처 모호`],['산출물 / 연결 검사 / 인수',`${p.artifact_count} / ${p.check_count} / ${p.acceptance_count}`],['최근 관측',p.last_observed||'없음'],...(p.delivery?[['전달 상태',deliveryText(p)],['마지막 연결 확인',p.delivery.last_received||'없음'],['등록 상태',p.delivery.registered?'등록됨':'현재 등록 없음'],...p.delivery.batches.map(b=>['전달 배치',b.batch_id+' · '+({queued:'대기',aggregated:'집계',failed:'실패',conflict:'충돌'}[b.state])+' · '+b.reason_code+' · 수신 이벤트 '+b.event_count+' · '+b.received_at])]:[]),['최근 수집',p.last_import.at],['이번 수집 상태',JSON.stringify(p.last_import)],['누적 수집 기록',JSON.stringify(p.totals)],['관리 필요',p.issues.join(', ')||'표시된 항목 없음']]){const d=node('div');const strong=node('strong',name);d.append(strong,node('br'),node('span',value));grid.append(d)}box.append(grid);
 el('relations').replaceChildren();for(const r of p.relations){const li=node('li');li.append(node('strong',r.artifact_id+' / '+r.version),node('div','산출물 이벤트: '+r.artifact_event_id),node('div','Agent: '+(r.agent_id||'없음')+' · '+r.agent_status+(r.agent_sources.length?' ('+r.agent_sources.join(', ')+')':'')),node('div','검사: '+(r.checks.map(x=>x.status+' ['+x.event_id+']').join(', ')||'연결 없음')),node('div','인수: '+(r.acceptances.map(x=>x.status+' ['+x.event_id+']').join(', ')||'연결 없음')));el('relations').append(li)}if(!p.relations.length)el('relations').append(node('li','선언된 산출물이 없습니다.'));
 el('events').replaceChildren();for(const r of p.events){const e=r.event,li=node('li'),button=node('button',e.observed_at+' · '+e.kind+' · '+e.event_id);button.type='button';button.addEventListener('click',()=>showOriginal(r,p));li.append(button);if(e.kind==='decision.recorded')li.append(node('small','기준선 '+(p.events.some(x=>x.event.kind==='project.baseline'&&x.event.links.phase_id===e.links.phase_id&&x.event.links.baseline_version===e.links.baseline_version)?'연결':'미연결')));if(e.kind==='check.recorded'||e.kind==='acceptance.recorded')li.append(node('small','산출물 '+(p.events.some(x=>x.event.kind==='artifact.recorded'&&x.event.links.artifact_id===e.links.artifact_id&&x.event.links.artifact_version===e.links.artifact_version)?'연결':'미연결')));el('events').append(li)}
}
function showOriginal(r,p){el('original').hidden=false;el('provenance').textContent='event_id: '+r.event.event_id+' · SHA-256: '+r.file_sha256+' · 행: '+r.line+' · 최초 수집: '+r.received_at+(p.source_provenance?' · '+p.source_provenance:'');el('event-json').textContent=JSON.stringify(r.event,null,2);el('original').scrollIntoView({behavior:'smooth',block:'start'})}
el('back').addEventListener('click',showList);el('query').addEventListener('input',renderList);el('mode-filter').addEventListener('change',renderList);el('mode').textContent=projects.some(p=>p.evidence_mode==='synthetic')?'합성 데이터 포함 · 실제 사용자 환경의 자동 전달을 검증한 화면이 아닙니다.':'로컬 파일 가져오기 결과 · 실제 사용자 환경의 자동 전달은 별도 검증이 필요합니다.';if(deliveryInfo!==null){el('mode').textContent='합성 loopback 자동 전달 · 실제 여러 사용자 환경 전달 및 제품 완료는 검증하지 않았습니다.';el('delivery-banner').hidden=false;el('delivery-banner').textContent=['전달 영수증은 inbox 보존 확인이며 업무 완료가 아닙니다.',...deliveryInfo.issues].join(' · ')}renderList();
</script></body></html>'''


def render(store, output, delivery_state=None):
    projects = summarize(store, delivery_state)
    payload = json.dumps(projects, ensure_ascii=True, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    info = None if delivery_state is None else {'issues': delivery_issues(delivery_state)}
    delivery_payload = json.dumps(info, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    content = HTML.replace('__DATA__', payload).replace('__DELIVERY__', delivery_payload).encode('utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(output, content)
    return projects


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    importer = commands.add_parser('import')
    importer.add_argument('--manifest', required=True, type=Path)
    renderer = commands.add_parser('render')
    renderer.add_argument('--output', required=True, type=Path)
    renderer.add_argument('--delivery-state', type=Path)
    for command in (importer, renderer):
        command.add_argument('--store', required=True, type=Path)
    args = parser.parse_args()
    try:
        requested = args.store.absolute()
        root = requested.parent.resolve() / requested.name
        if args.command == 'import':
            store = import_sources(args.manifest.absolute(), root)
            print(f"sources={len(store['sources'])} events={sum(len(v['events']) for v in store['sources'].values())}")
        else:
            delivery_state = load_delivery_state(args.delivery_state) if args.delivery_state is not None else None
            try:
                store = load_store(root)
                projects = render(store, args.output.absolute(), delivery_state)
            except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
                if delivery_state is None:
                    raise
                delivery_state = {**delivery_state, 'central_error': 'central_read_failed'}
                projects = render({'version': 1, 'sources': {}}, args.output.absolute(), delivery_state)
            print(f'projects={len(projects)}')
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
        # Do not echo an input path or rejected event content.
        print('central: invalid input or storage failure', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
