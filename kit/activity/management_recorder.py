#!/usr/bin/env python3
"""Explicit project-local management receipts. No network, shell, or hook installation."""
import argparse
import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import tempfile
import uuid
from contextlib import contextmanager

import management

MAX_FILE = 16 * 1024 * 1024
ENVIRONMENTS = ('unit', 'mock', 'local', 'browser', 'live-provider', 'production')


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def project_root(value):
    root = Path(value).expanduser().resolve(strict=True)
    if not root.is_dir() or root == Path.home().resolve() or root == Path(root.anchor):
        raise ValueError('explicit project directory required')
    return root


def local_path(root, value, must_exist=True):
    root = Path(root).resolve(strict=True)
    value = str(value)
    parts = PurePosixPath(value)
    if (not value or parts.is_absolute() or '..' in parts.parts or '\\' in value
            or parts.as_posix() != value or value == '.'):
        raise ValueError('normalized project-relative path required')
    target = (root / value).resolve(strict=must_exist)
    if not target.is_relative_to(root) or target == root:
        raise ValueError('path escapes project')
    return target


def read_json(path):
    if path.stat().st_size > MAX_FILE:
        raise ValueError('JSON size limit')
    return json.loads(path.read_text(), parse_constant=lambda _: (_ for _ in ()).throw(ValueError('invalid number')))


def atomic_json(path, value):
    body = (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    if len(body) > MAX_FILE:
        raise ValueError('JSON size limit')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.management-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(body); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def locked(path):
    # ponytail: one project-file lock; split by project only if local contention matters.
    lock = path.with_name(path.name + '.lock')
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def select_project(document, project_id=None):
    if 'projects' not in document:
        if project_id is not None and document.get('id') != project_id:
            raise ValueError('project selection mismatch')
        return document
    if document.get('version') != 3:
        raise ValueError('v3 catalog required')
    candidates = [p for p in document['projects'] if project_id is None or p['id'] == project_id]
    if len(candidates) != 1:
        raise ValueError('select exactly one project with --project-id')
    return candidates[0]


def file_sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def actual_manifest(root, files):
    result = []
    for entry in files:
        target = local_path(root, entry['path'])
        if not target.is_file():
            raise ValueError('manifest file missing')
        result.append({'path': entry['path'], 'sha256': file_sha256(target)})
    return sorted(result, key=lambda item: item['path'])


def refresh_artifact(root, project):
    artifact = project['management']['artifact']
    artifact['files'] = actual_manifest(root, artifact['files'])
    artifact['sha256'] = management.artifact_sha256(artifact['files'])
    artifact['revision'] = project['current_revision']


def find_test_plan(project, plan_id, version=None):
    candidates = [p for p in project['management']['test_plans'] if p['id'] == plan_id and (version is None or p['version'] == version)]
    if not candidates:
        raise ValueError('test plan not found')
    return max(candidates, key=lambda p: p['at'])


def receipt(project, test_plan, actor, environment_id, session, environment, provenance, exit_code, started, ended, summary):
    return {'id': 'attempt-' + uuid.uuid4().hex, 'test_plan_id': test_plan['id'],
            'test_plan_version': test_plan['version'], 'test_plan_sha256': management.test_plan_sha256(test_plan),
            'criterion_signature': management.criterion_signature(test_plan['definition']),
            'revision': project['current_revision'], 'artifact_sha256': project['management']['artifact']['sha256'],
            'command': test_plan['definition']['command'], 'started_at': started, 'at': ended,
            'exit_code': exit_code, 'actor_id': actor, 'environment_id': environment_id, 'session_id': session,
            'environment': environment, 'runner': 'management-recorder-v1' if provenance == 'runner' else 'handoff-import',
            'summary': summary, 'provenance': provenance}


def safe_receipt(root, attempt, state):
    folder = local_path(root, '.ai-pms', must_exist=False)
    folder.mkdir(mode=0o700, exist_ok=True)
    target = local_path(root, '.ai-pms/receipt-' + attempt['id'] + '.json', must_exist=False)
    atomic_json(target, {'state': state, 'attempt': attempt})


def validate_actor(project, actor, environment_id):
    if (actor, environment_id) not in {(r['actor_id'], r['environment_id']) for r in project['source_refs']}:
        raise ValueError('actor/environment not mapped to project')


def run_plan(root, project, plan_id, version, actor, environment_id, session=None, environment='local', timeout=300):
    root = project_root(root)
    management.validate(project)
    validate_actor(project, actor, environment_id)
    if environment not in ENVIRONMENTS or not 0 < timeout <= 86400:
        raise ValueError('runner environment or timeout invalid')
    management.ident(session)
    test_plan = find_test_plan(project, plan_id, version)
    if actual_manifest(root, test_plan['test_files']) != sorted(test_plan['test_files'], key=lambda f: f['path']):
        raise ValueError('test file changed; record an explicit new test-plan version')
    argv = shlex.split(test_plan['definition']['command'])
    if not argv:
        raise ValueError('empty test command')
    refresh_artifact(root, project)
    started = now()
    # No shell evaluation and no raw output is retained, even on timeout/failure.
    try:
        completed = subprocess.run(argv, cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, shell=False, timeout=timeout)
        code, summary = completed.returncode, 'Runner completed; raw output omitted.'
    except subprocess.TimeoutExpired:
        code, summary = None, 'Runner timeout; raw output omitted.'
    except OSError:
        code, summary = None, 'Runner could not start; raw output omitted.'
    attempt = receipt(project, test_plan, actor, environment_id, session, environment, 'runner', code, started, now(), summary)
    project['management']['attempts'].append(attempt)
    try:
        refresh_artifact(root, project)
        management.validate(project)
    except (ValueError, OSError):
        safe_receipt(root, attempt, 'management-preserved-post-run-manifest-invalid')
        raise ValueError('post-run manifest invalid; original management preserved and receipt saved') from None
    return attempt


def graph_artifact(root):
    """Inspect actual local graph bytes; exit zero alone is not an artifact."""
    try:
        if (root / 'graphify-out/graph.json').is_symlink():
            return None
        path = local_path(root, 'graphify-out/graph.json')
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE:
            return None
        body = path.read_bytes()
        value = json.loads(body)
        if not isinstance(value, dict) or not isinstance(value.get('nodes'), list):
            return None
        edges = value.get('edges', value.get('links'))
        if not isinstance(edges, list):
            return None
        ids = [node.get('id') for node in value['nodes'] if isinstance(node, dict)]
        if len(ids) != len(value['nodes']) or any(not isinstance(i, (str, int)) for i in ids) or len(set(ids)) != len(ids):
            return None
        known = set(ids)
        if any(not isinstance(e, dict) or not isinstance(e.get('source'), (str, int)) or not isinstance(e.get('target'), (str, int)) or e['source'] not in known or e['target'] not in known for e in edges):
            return None
        stat = path.stat()
        return {'sha256': hashlib.sha256(body).hexdigest(), 'stamp': [stat.st_mtime_ns, stat.st_ino, stat.st_size]}
    except (ValueError, OSError, TypeError):
        return None


def graph_record(root, project, timeout=300):
    root = project_root(root)
    try:
        result = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
        if result.returncode == 0 and Path(result.stdout.strip()).resolve() == Path.home().resolve():
            raise ValueError('home git root cannot be graphed')
    except OSError:
        pass
    if not 0 < timeout <= 86400:
        raise ValueError('graph timeout invalid')
    output = local_path(root, 'graphify-out', must_exist=False)
    if output.exists():
        for item in output.rglob('*'):
            if item.is_symlink() and not item.resolve().is_relative_to(root):
                raise ValueError('graph output symlink escapes project')
    before = copy.deepcopy(project['management']['artifact'])
    refresh_artifact(root, project)
    source_hash = project['management']['artifact']['sha256']
    source_revision = project['current_revision']
    version = 'unobserved'
    try:
        version_run = subprocess.run(['graphify', '--version'], cwd=root, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, shell=False, timeout=10)
        if version_run.returncode == 0:
            import re
            match = re.fullmatch(r'(?:graphify\s+)?([0-9][A-Za-z0-9_.-]{0,63})\s*', version_run.stdout)
            if match:
                version = match[1]
    except (OSError, subprocess.TimeoutExpired):
        pass
    current = [g for g in project['management']['graphs'] if g['status']=='generated'
               and g['source_revision']==source_revision and g['source_sha256']==source_hash
               and g['version']==version and management.time(g['at'])<=management.time(now())]
    artifact_before = graph_artifact(root)
    cache_path = local_path(root, '.ai-pms/graph-cache.json', must_exist=False)
    try:
        cache = read_json(cache_path)
    except (OSError, ValueError):
        cache = {}
    if current and artifact_before and cache == {'record_id': max(current, key=lambda g:g['at'])['id'], 'graph_sha256': artifact_before['sha256']}:
        return max(current, key=lambda g:g['at'])
    try:
        outcome = subprocess.run(['graphify', 'extract', str(root), '--code-only', '--no-cluster'], cwd=root,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 shell=False, timeout=timeout)
        artifact_after = graph_artifact(root)
        changed = artifact_after and (artifact_before is None or artifact_after['stamp'] != artifact_before['stamp'])
        status = 'generated' if outcome.returncode == 0 and changed else 'failed'
    except (OSError, subprocess.TimeoutExpired):
        status = 'failed'
    graph = {'id': 'graph-' + uuid.uuid4().hex, 'generator': 'graphify', 'version': version,
             'mode': 'code-only', 'source_revision': source_revision, 'source_sha256': source_hash,
             'at': now(), 'status': status}
    project['management']['graphs'].append(graph)
    try:
        refresh_artifact(root, project)
        management.validate(project)
    except (ValueError, OSError):
        project['management']['artifact'] = before
        project['management']['graphs'].remove(graph)
        raise ValueError('graph post-run manifest invalid') from None
    folder = local_path(root, '.ai-pms', must_exist=False)
    folder.mkdir(mode=0o700, exist_ok=True)
    if status == 'generated':
        atomic_json(cache_path, {'record_id': graph['id'], 'graph_sha256': artifact_after['sha256']})
    log = local_path(root, '.ai-pms/graphs.jsonl', must_exist=False)
    fd = os.open(log, os.O_CREAT | os.O_APPEND | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as stream:
        stream.write(management.canonical(graph) + '\n'); stream.flush(); os.fsync(stream.fileno())
    return graph


def import_handoff(root, project, handoff, result, plan_id, version, reason, test_files, actor, environment_id, session=None):
    """Seed explicit requirements/plans/checks. Imported outcomes remain declarations."""
    root = project_root(root)
    management.validate(project)
    validate_actor(project, actor, environment_id)
    management.ident(session)
    if result is not None and result.get('task_id') not in {t.get('task_id') for t in handoff.get('tasks', [])}:
        raise ValueError('result task is absent from Handoff plan')
    m = project['management']
    stamp = now()
    requirements = handoff.get('intent_guard', {}).get('requirements', [])
    source = handoff.get('intent_guard', {}).get('source_ref', handoff.get('spec_ref', 'handoff'))
    existing = {r['id']: r for r in m['requirements']}
    for entry in requirements:
        requirement = {'id': entry['id'], 'text': entry['quote'], 'source': source}
        if entry['id'] in existing and existing[entry['id']] != requirement:
            raise ValueError('requirement changed; use explicit new ID')
        if entry['id'] not in existing:
            m['requirements'].append(requirement); existing[entry['id']] = requirement
    if any(p['id'] == plan_id and p['version'] == version for p in m['plans']):
        raise ValueError('plan version already recorded')
    requirement_ids = [r['id'] for r in requirements]
    m['plans'].append({'id': plan_id, 'version': version, 'at': stamp, 'summary': handoff['goal'],
                       'reason': reason, 'requirement_ids': requirement_ids, 'handoff_ref': plan_id})
    files = actual_manifest(root, [{'path': name} for name in test_files])
    if not files:
        raise ValueError('explicit test files required')
    for file in files:
        if file['path'] not in {item['path'] for item in m['artifact']['files']}:
            m['artifact']['files'].append(file)
    refresh_artifact(root, project)
    tasks = handoff.get('tasks', [])
    for task in tasks:
        acceptance = task.get('acceptance', task.get('acceptance_test'))
        if not isinstance(acceptance, dict) or 'command' not in acceptance:
            continue
        criteria = [c for c in project['criteria'] if c['command'] == acceptance['command']
                    and c['expected_exit_code'] == acceptance.get('expect_exit_code', 0)]
        if len(criteria) != 1:
            raise ValueError('handoff acceptance must match exactly one existing criterion')
        definition = copy.deepcopy(criteria[0])
        test_plan = {'id': 'handoff-' + task['task_id'], 'version': version, 'plan_id': plan_id,
                     'plan_version': version, 'criterion_id': definition['id'],
                     'requirement_ids': task.get('requirement_ids', requirement_ids), 'reason': reason,
                     'excluded': task.get('context', {}).get('excluded', 'No additional exclusions declared.'),
                     'at': stamp, 'definition': definition, 'test_files': files}
        if any(p['id'] == test_plan['id'] and p['version'] == version for p in m['test_plans']):
            raise ValueError('test plan version already recorded')
        m['test_plans'].append(test_plan)
        if result is not None and result.get('task_id') == task['task_id']:
            run = result.get('acceptance_run')
            if not isinstance(run, dict) or run.get('command') != definition['command'] or type(run.get('exit_code')) is not int:
                raise ValueError('handoff result acceptance mismatch')
            m['attempts'].append(receipt(project, test_plan, actor, environment_id, session, 'local', 'declared',
                                         run['exit_code'], stamp, stamp, 'Imported Handoff result; execution unobserved.'))
    management.validate(project)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, help='explicit project directory, never HOME')
    parser.add_argument('--management', required=True, help='project-relative project JSON or v3 catalog')
    parser.add_argument('--project-id', help='select one project in a catalog')
    commands = parser.add_subparsers(dest='action', required=True)
    run = commands.add_parser('run')
    run.add_argument('--test-plan', required=True); run.add_argument('--version')
    run.add_argument('--environment', choices=ENVIRONMENTS, default='local')
    run.add_argument('--timeout', type=int, default=300); run.add_argument('--graph', action='store_true')
    handoff = commands.add_parser('handoff')
    handoff.add_argument('--plan', required=True); handoff.add_argument('--result')
    handoff.add_argument('--plan-id', required=True); handoff.add_argument('--version', required=True)
    handoff.add_argument('--reason', required=True); handoff.add_argument('--test-file', action='append', required=True)
    for command in (run, handoff):
        command.add_argument('--actor-id', required=True); command.add_argument('--environment-id', required=True)
        command.add_argument('--session-id', required=True)
    graph = commands.add_parser('graph'); graph.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args(argv)
    try:
        root = project_root(args.project)
        target = local_path(root, args.management)
        with locked(target):
            original = target.read_bytes()
            document = read_json(target)
            project = select_project(document, args.project_id)
            if args.action == 'run':
                attempt = run_plan(root, project, args.test_plan, args.version, args.actor_id,
                                   args.environment_id, args.session_id, args.environment, args.timeout)
                if args.graph:
                    try:
                        graph_record(root, project, args.timeout)
                    except (ValueError, OSError, subprocess.TimeoutExpired):
                        pass  # Optional graph cannot block a recorded test receipt.
                code = attempt['exit_code'] if type(attempt['exit_code']) is int and 0 <= attempt['exit_code'] <= 125 else 1
            elif args.action == 'handoff':
                plan = read_json(local_path(root, args.plan))
                result = read_json(local_path(root, args.result)) if args.result else None
                import_handoff(root, project, plan, result, args.plan_id, args.version, args.reason,
                               args.test_file, args.actor_id, args.environment_id, args.session_id)
                code = 0
            else:
                management.validate(project)
                graph_record(root, project, args.timeout)
                code = 0
            target = local_path(root, args.management)
            if target.read_bytes() != original:
                raise ValueError('management changed during recording')
            atomic_json(target, document)
        print('Management receipt saved; raw output omitted.')
        return code
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired):
        print('Management recording failed; original file preserved. Review project and contract locally.')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
