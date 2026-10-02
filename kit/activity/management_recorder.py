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
import work

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


def _import_legacy_handoff(root, project, handoff, result, plan_id, version, reason, test_files, actor, environment_id, session=None):
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



def import_handoff(root, project, handoff, result, plan_id, version, reason, test_files, actor, environment_id, session=None):
    """Preserve full atomic plans; incomplete historical inputs retain their legacy evidence scope."""
    tasks = handoff.get('tasks', [])
    if not handoff.get('phases'):
        if any('phase' in task or 'depends_on' in task or 'done_when' in task for task in tasks):
            raise ValueError('full work plan requires explicit phases and phase exit checks')
        return _import_legacy_handoff(root, project, handoff, result, plan_id, version, reason, test_files, actor, environment_id, session)
    root = project_root(root)
    management.validate(project); validate_actor(project, actor, environment_id); management.ident(session)
    p = copy.deepcopy(project); m = p['management']; stamp = now()
    if not tasks or any(not all(k in t for k in ('task_id','phase','objective','done_when','depends_on','acceptance')) for t in tasks):
        raise ValueError('full work plan requires atomic tasks and completion conditions')
    if result is not None and result.get('task_id') not in {t['task_id'] for t in tasks}:
        raise ValueError('result task is absent from plan')
    if any(x['id']==plan_id and x['version']==version for x in m['plans']):
        raise ValueError('plan version already recorded')
    requirements = handoff.get('intent_guard',{}).get('requirements',[])
    source = handoff.get('intent_guard',{}).get('source_ref',handoff.get('spec_ref','handoff'))
    existing = {r['id']:r for r in m['requirements']}
    for r in requirements:
        entry={'id':r['id'],'text':r['quote'],'source':source}
        if r['id'] in existing and entry!=existing[r['id']]:raise ValueError('requirement changed; use a new ID')
        if r['id'] not in existing:m['requirements'].append(entry);existing[r['id']]=entry
    reqids=[r['id'] for r in requirements]
    m['plans'].append(dict(id=plan_id,version=version,at=stamp,summary=handoff['goal'],reason=reason,requirement_ids=reqids,handoff_ref=plan_id))
    phases=[{'id':phase['id'],'name':phase['name']} for phase in handoff['phases']]
    phaseids={phase['id'] for phase in phases}
    if any(d['phase_id'] not in phaseids for d in p['documents']) or any(c['scope']=='phase' and c['target_id'] not in phaseids for c in p['criteria']):
        raise ValueError('existing phase evidence needs explicit migration; original plan preserved')
    if any(c['scope']=='task' and c['target_id'] not in {t['task_id'] for t in tasks} for c in p['criteria']):
        raise ValueError('retired tasks need explicit scope treatment; original plan preserved')
    p['phases']=phases
    p['goal']=handoff['goal']
    if p['current_phase'] not in phaseids:p['current_phase']=None
    files=actual_manifest(root,[{'path':f} for f in test_files])
    if not files:raise ValueError('explicit test files required')
    manifest={f['path']:f for f in m['artifact']['files']};manifest.update({f['path']:f for f in files});m['artifact']['files']=list(manifest.values());refresh_artifact(root,p)
    m['work']={'plan_id':plan_id,'plan_version':version,'at':stamp,'tasks':[],'phase_gates':[],'updates':[],'reviews':[]}
    def check(acceptance, scope, target, label, test_id, requirement_ids):
        if not isinstance(acceptance,dict) or not {'command','expect_exit_code'}<=set(acceptance) or set(acceptance)-{'command','expect_exit_code','expect_contains','cwd'}:
            raise ValueError('unsupported acceptance definition')
        if acceptance.get('cwd') not in (None,'.'):raise ValueError('acceptance cwd must be the explicit project root')
        expected=acceptance.get('expect_contains',[])
        if not isinstance(expected,list) or any(not isinstance(x,str) or not x for x in expected):raise ValueError('output expectations must be nonempty strings')
        if expected and scope!='task':raise ValueError('phase/project output expectations require a supported verifier; exit-only completion refused')
        matches=[c for c in p['criteria'] if c['scope']==scope and c['target_id']==target and c['command']==acceptance['command'] and c['expected_exit_code']==acceptance['expect_exit_code']]
        if len(matches)>1:raise ValueError('ambiguous acceptance mapping')
        cid=matches[0]['id'] if matches else 'work-'+scope+'-'+management.digest(target)[:24]
        definition={'id':cid,'label':label,'scope':scope,'target_id':target,'command':acceptance['command'],'expected_exit_code':acceptance['expect_exit_code']}
        previous=next((c for c in p['criteria'] if c['id']==cid),None)
        if previous is not None:previous.update(definition)
        else:p['criteria'].append(definition)
        if len(test_id)>127:test_id='handoff-'+management.digest(test_id)[:32]
        tp=dict(id=test_id,version=version,plan_id=plan_id,plan_version=version,criterion_id=cid,requirement_ids=requirement_ids,reason=reason,excluded='Imported explicit Handoff scope; output expectations require human review when present.',at=stamp,definition=copy.deepcopy(definition),test_files=copy.deepcopy(files))
        m['test_plans'].append(tp)
        return cid,tp,expected
    for task in tasks:
        tid=task['task_id'];cid,tp,expected=check(task['acceptance'],'task',tid,task['objective'],'handoff-'+tid,task.get('requirement_ids',reqids))
        done=copy.deepcopy(task['done_when'])
        if expected:done.append('Review exact acceptance output expectations: '+json.dumps(expected,ensure_ascii=True))
        m['work']['tasks'].append(dict(id=tid,title=task['objective'],phase_id=task['phase'],owner=actor,required=True,depends_on=copy.deepcopy(task['depends_on']),requirement_ids=task.get('requirement_ids',reqids),done_when=done,criterion_ids=[cid],document_ids=[],review_required=bool(expected)))
        if result is not None and result.get('task_id')==tid:
            run=result.get('acceptance_run')
            if not isinstance(run,dict) or run.get('command')!=tp['definition']['command'] or type(run.get('exit_code')) is not int:raise ValueError('result acceptance mismatch')
            m['attempts'].append(receipt(p,tp,actor,environment_id,session,'local','declared',run['exit_code'],stamp,stamp,'Imported Handoff result; execution unobserved.'))
    for phase in handoff['phases']:
        cid,_,_=check(phase.get('exit_check'),'phase',phase['id'],phase['name']+' exit','handoff-phase-'+phase['id'],reqids)
        m['work']['phase_gates'].append({'phase_id':phase['id'],'criterion_ids':[cid]})
    overall=handoff.get('intent_guard',{}).get('acceptance')
    if overall is not None:check(overall,'project',p['id'],'Project acceptance','handoff-project-'+p['id'],reqids)
    management.validate(p)
    project.clear();project.update(p)


def import_work_record(project, kind, entry):
    p=copy.deepcopy(project)
    if 'work' not in p['management']:raise ValueError('explicit work plan required')
    p['management']['work']['updates' if kind=='update' else 'reviews'].append(copy.deepcopy(entry))
    management.validate(p)
    project.clear();project.update(p)


def trace_records(project):
    return project['management'].setdefault('traceability',
        {'checkpoints': [], 'decisions': [], 'handoffs': [], 'capture': []})


def git_bytes(root, *args, optional=False):
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS'] = '0'
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(root), *args],
                            env=env,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            shell=False, timeout=30)
    if len(result.stdout) > MAX_FILE or (result.returncode and not optional):
        raise ValueError('Git observation failed or exceeded limit')
    return result.returncode, result.stdout


def git_fingerprint(root):
    """Read Git identity and bounded dirty bytes; retain only digests, never diff text."""
    root = project_root(root)
    try:
        code, top = git_bytes(root, 'rev-parse', '--show-toplevel', optional=True)
    except FileNotFoundError:
        return {'commit': None, 'parent_commits': [], 'dirty': None, 'worktree_sha256': None}
    if code:
        return {'commit': None, 'parent_commits': [], 'dirty': None, 'worktree_sha256': None}
    git_root = Path(os.fsdecode(top).strip()).resolve(strict=True)
    if git_root == Path.home().resolve() or git_root != root:
        raise ValueError('checkpoint requires the explicit non-HOME Git root')
    code, head = git_bytes(root, 'rev-parse', '--verify', 'HEAD', optional=True)
    commit = head.decode('ascii').strip() if code == 0 else None
    if commit is None:
        raise ValueError('Git checkpoint requires an existing HEAD commit')
    parents = []
    if commit:
        _, lineage = git_bytes(root, 'rev-list', '--parents', '-n', '1', commit)
        parts = lineage.decode('ascii').split()
        if not parts or parts[0] != commit:
            raise ValueError('Git identity changed')
        parents = parts[1:]
    _, status = git_bytes(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    _, diff = git_bytes(root, 'diff', '--no-ext-diff', '--no-textconv', '--binary', 'HEAD')
    _, names = git_bytes(root, 'ls-files', '--others', '--exclude-standard', '-z')
    digest = hashlib.sha256()
    for body in (status, diff):
        digest.update(len(body).to_bytes(8, 'big')); digest.update(body)
    for name in sorted(n for n in names.split(b'\0') if n):
        path = local_path(root, os.fsdecode(name))
        if (root / os.fsdecode(name)).is_symlink() or not path.is_file():
            raise ValueError('untracked checkpoint file must be a regular project file')
        digest.update(len(name).to_bytes(8, 'big')); digest.update(name)
        digest.update(bytes.fromhex(file_sha256(path)))
    return {'commit': commit, 'parent_commits': parents, 'dirty': bool(status),
            'worktree_sha256': digest.hexdigest()}


def checkpoint_record(root, project, actor, environment_id, session, agent=None,
                      attempt_ids=(), decision_ids=(), summary='Explicit local Git checkpoint.'):
    root = project_root(root)
    management.validate(project)
    validate_actor(project, actor, environment_id)
    management.ident(session)
    if agent is not None:
        management.ident(agent)
    before = git_fingerprint(root)
    refresh_artifact(root, project)
    entry = {'id': 'checkpoint-' + uuid.uuid4().hex, 'at': now(), 'actor_id': actor,
             'environment_id': environment_id, 'session_id': session, 'agent_id': agent,
             'revision': project['current_revision'], 'artifact_sha256': project['management']['artifact']['sha256'],
             **before, 'attempt_ids': list(attempt_ids), 'decision_ids': list(decision_ids),
             'provenance': 'declared', 'summary': summary}
    trace_records(project)['checkpoints'].append(entry)
    management.validate(project)
    if git_fingerprint(root) != before:
        raise ValueError('Git changed during checkpoint observation')
    return entry


def import_trace_record(project, kind, entry):
    """Import explicit schema records without promoting their attribution or usage."""
    management.validate(project)
    array = {'decision': 'decisions', 'handoff': 'handoffs', 'capture': 'capture'}[kind]
    trace_records(project)[array].append(copy.deepcopy(entry))
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
    checkpoint = commands.add_parser('checkpoint')
    checkpoint.add_argument('--agent-id'); checkpoint.add_argument('--attempt-id', action='append', default=[])
    checkpoint.add_argument('--decision-id', action='append', default=[])
    checkpoint.add_argument('--summary', default='Explicit local Git checkpoint.')
    record = commands.add_parser('record')
    record.add_argument('--kind', required=True, choices=('decision', 'handoff', 'capture', 'update', 'review'))
    record.add_argument('--record', required=True, help='project-relative explicit record JSON')
    update = commands.add_parser('update')
    update.add_argument('--task',required=True);update.add_argument('--state',required=True,choices=('not_started','in_progress','blocked'))
    update.add_argument('--summary',required=True);update.add_argument('--next-action',required=True)
    review = commands.add_parser('review')
    review.add_argument('--task',required=True);review.add_argument('--reviewer',required=True)
    review.add_argument('--decision',required=True,choices=('approved','changes_requested'));review.add_argument('--summary',required=True)
    for command in (run, handoff, checkpoint):
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
            elif args.action in ('update','review'):
                management.validate(project)
                task=next((t for t in project['management'].get('work',{}).get('tasks',[]) if t['id']==args.task),None)
                if task is None:raise ValueError('unknown task')
                if args.action=='update':
                    entry=dict(id='update-'+uuid.uuid4().hex,task_id=args.task,at=now(),state=args.state,summary=args.summary,next_action=args.next_action)
                else:
                    refresh_artifact(root,project)
                    entry=dict(id='review-'+uuid.uuid4().hex,task_id=args.task,at=now(),reviewer=args.reviewer,decision=args.decision,summary=args.summary,artifact_sha256=project['management']['artifact']['sha256'],task_sha256=work.task_digest(project,task))
                import_work_record(project,args.action,entry)
                code=0
            elif args.action == 'checkpoint':
                checkpoint_record(root, project, args.actor_id, args.environment_id, args.session_id,
                                  args.agent_id, args.attempt_id, args.decision_id, args.summary)
                code = 0
            elif args.action == 'record':
                entry = read_json(local_path(root, args.record))
                if args.kind in ('update','review'): import_work_record(project,args.kind,entry)
                else: import_trace_record(project,args.kind,entry)
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
