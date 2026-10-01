#!/usr/bin/env python3
"""Offline, privacy allowlisted command-hook logger (Python stdlib, POSIX)."""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid
import connectivity

MAX_INPUT = 1_048_576
LINKS = ('phase_id', 'baseline_version', 'task_id', 'decision_id', 'artifact_id', 'artifact_version', 'check_id')
IDS = ('session_id', 'agent_id', 'parent_agent_id', 'turn_id', 'tool_call_id')
EVENTS = {'SessionStart': 'session.start', 'SessionEnd': 'session.end',
          'UserPromptSubmit': 'prompt.observed', 'PreToolUse': 'tool.requested',
          'PostToolUse': 'tool.completed', 'PostToolUseFailure': 'tool.failed',
          'SubagentStart': 'agent.start', 'SubagentStop': 'agent.end', 'Stop': 'turn.stopped'}
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


def parse_json(value):
    return json.loads(value, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def identifier(value):
    if isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}', value) and not PRIVATE.search(value):
        return value
    return None


def project_uuid(value):
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ValueError('invalid project UUID')
    return value


def private_dir(path):
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Reject symlink components: an existing link must never redirect evidence.
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('symlink directory')
    info = path.stat()
    if info.st_uid != os.getuid() or not stat.S_ISDIR(info.st_mode):
        raise ValueError('unsafe directory')
    path.chmod(0o700)


def locked_file(path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    info = os.fstat(fd)
    if info.st_uid != os.getuid() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(fd)
        raise ValueError('unsafe file')
    os.fchmod(fd, 0o600)
    file = os.fdopen(fd, 'r+', encoding='utf-8')
    fcntl.flock(file, fcntl.LOCK_EX)
    return file


def project_id(root, cwd, override):
    if override:
        return project_uuid(override)
    if not isinstance(cwd, str) or not cwd or len(cwd) > 4096 or '\x00' in cwd or not os.path.isabs(cwd):
        raise ValueError('missing or invalid cwd')
    resolved = Path(os.path.realpath(cwd))
    identity = resolved
    for ancestor in (resolved, *resolved.parents):
        if (ancestor / '.git').exists():
            if ancestor != Path.home() or resolved == ancestor:
                identity = ancestor
            break
    normalized = os.path.normcase(str(identity))
    with locked_file(root / 'project-index.json') as file:
        raw = file.read()
        index = parse_json(raw) if raw else {}
        if not isinstance(index, dict):
            raise ValueError('invalid private index')
        if normalized not in index:
            index[normalized] = str(uuid.uuid4())
            file.seek(0)
            file.write(json.dumps(index, ensure_ascii=False))
            file.truncate()
            file.flush()
            os.fsync(file.fileno())
        return project_uuid(index[normalized])


def base_event(source, native, kind, project, payload):
    event = {'schema_version': 1, 'adapter_version': '1', 'event_id': str(uuid.uuid4()),
             'observed_at': dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z'),
             'occurred_at': None, 'source': source, 'native_event': native, 'kind': kind,
             'authority': 'declared' if source == 'manual' else 'observed', 'project_id': project,
             'tool_name': None, 'links': dict.fromkeys(LINKS), 'data': {}, 'missing_fields': []}
    for key in IDS:
        value = payload.get('tool_use_id', payload.get(key)) if key == 'tool_call_id' else payload.get(key)
        event[key] = identifier(value)
        if event[key] is None:
            event['missing_fields'].append(key)
    return event


def hook_event(args, root):
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise ValueError('input too large')
    payload = parse_json(raw)
    if not isinstance(payload, dict):
        raise ValueError('input must be object')
    native = payload.get('hook_event_name')
    native = native if isinstance(native, str) and native in EVENTS else 'unknown'
    event = base_event(args.source, native, EVENTS.get(native, 'unknown'),
                       project_id(root, payload.get('cwd'), args.project_id), payload)
    if native == 'unknown':
        event['missing_fields'].append('native_event')
    if not isinstance(payload.get('cwd'), str) or not payload.get('cwd'):
        event['missing_fields'].append('cwd')
    raw_tool = payload.get('tool_name')
    tool = raw_tool
    if isinstance(tool, str) and re.fullmatch(r'mcp__[A-Za-z0-9_-]{1,80}__[A-Za-z0-9_-]{1,80}', tool):
        tool = 'MCP'
    event['tool_name'] = tool if isinstance(tool, str) and tool in TOOLS else None
    if event['kind'].startswith('tool.') and event['tool_name'] is None:
        event['missing_fields'].append('tool_name')
    timestamp = payload.get('occurred_at')
    if isinstance(timestamp, str) and len(timestamp) <= 40:
        try:
            parsed = dt.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if parsed.tzinfo is not None:
                event['occurred_at'] = parsed.astimezone(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
        except ValueError:
            pass
    if event['occurred_at'] is None:
        event['missing_fields'].append('occurred_at')
    if event['kind'].startswith('tool.') and (event['tool_name'] == 'MCP' or 'pms_metadata' in payload or getattr(args, 'resource_map', None)):
        event.update(schema_version=2, adapter_version='2')
        match = re.fullmatch(r'mcp__([A-Za-z0-9_-]{1,80})__([A-Za-z0-9_-]{1,80})', raw_tool or '') if isinstance(raw_tool, str) else None
        c = dict(server=match[1] if match and connectivity.ident(match[1]) else None, tool=match[2] if match and connectivity.ident(match[2]) else None,
                 status=event['kind'].split('.')[1], duration_ms=None, operation='unknown', resources=[], artifact_refs=[])
        metadata = payload.get('pms_metadata')
        mapped = None
        if getattr(args, 'resource_map', None):
            try:
                raw_map = Path(args.resource_map).read_bytes()
                if len(raw_map) > MAX_INPUT: raise ValueError('map too large')
                mapping = parse_json(raw_map)
                if not isinstance(mapping, dict): raise ValueError('invalid resource map')
                mapped = mapping.get(raw_tool) if isinstance(raw_tool, str) else None
            except (OSError, ValueError):
                event['missing_fields'].append('connection.resource_map')
        for block, declared in ((mapped, True), (metadata, False)):
            if block is None: continue
            if not isinstance(block, dict) or set(block) != {'operation','resources','artifact_refs'}:
                event['missing_fields'].append('connection.metadata'); continue
            candidate = {**c, **block}
            if declared and isinstance(candidate['resources'], list):
                candidate['resources'] = [{**r, 'evidence':'declared'} if isinstance(r,dict) else r for r in candidate['resources']]
            if connectivity.valid(candidate): c = candidate
            else: event['missing_fields'].append('connection.metadata')
        duration = payload.get('duration_ms')
        if type(duration) is int and 0 <= duration <= 86400000: c['duration_ms'] = duration
        event['data'] = {'connection': c}
    return event


def record_event(args):
    data, links = parse_json(args.data), parse_json(args.links)
    if not isinstance(data, dict) or not set(data) <= DATA[args.kind]:
        raise ValueError('invalid data keys')
    if not isinstance(links, dict) or not set(links) <= set(LINKS):
        raise ValueError('invalid link keys')
    for key, value in data.items():
        limit = 80 if key == 'environment' else 2000
        if not isinstance(value, str) or len(value) > limit or PRIVATE.search(value) or any(ord(c) < 32 and c not in '\n\t' for c in value):
            raise ValueError('unsafe explicit content')
    for key, value in links.items():
        if value is not None and identifier(value) is None:
            raise ValueError('invalid link')
    if any(not links.get(key) for key in REQUIRED[args.kind]):
        raise ValueError('missing required link')
    required_data = {'project.baseline': ('goal', 'scope'), 'decision.recorded': ('summary', 'reason')}
    if any(not data.get(key, '').strip() for key in required_data.get(args.kind, ())):
        raise ValueError('missing required data')
    if args.kind in ('check.recorded', 'acceptance.recorded'):
        allowed = {'pass', 'fail', 'unknown'} if args.kind == 'check.recorded' else {'accepted', 'rejected', 'pending'}
        if data.get('status') not in allowed:
            raise ValueError('invalid or missing status')
    correlation = {key: getattr(args, key) for key in IDS}
    if any(value is not None and identifier(value) is None for value in correlation.values()):
        raise ValueError('invalid correlation ID')
    event = base_event('manual', args.kind, args.kind, project_uuid(args.project_id), correlation)
    event['data'] = data
    event['links'].update(links)
    event['missing_fields'].append('occurred_at')
    return event


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    hook = commands.add_parser('hook')
    hook.add_argument('--source', choices=('codex', 'claude'), required=True)
    hook.add_argument('--project-id')
    hook.add_argument('--resource-map', type=Path)
    record = commands.add_parser('record')
    record.add_argument('--kind', choices=tuple(DATA), required=True)
    record.add_argument('--project-id', required=True)
    for key in IDS:
        record.add_argument('--' + key.replace('_', '-'))
    record.add_argument('--data', required=True)
    record.add_argument('--links', default='{}')
    for command in (hook, record):
        command.add_argument('--log-dir', default='~/.local/state/harness-activity')
    args = parser.parse_args()
    try:
        requested = Path(os.path.abspath(os.path.expanduser(args.log_dir)))
        root = requested.parent.resolve() / requested.name
        # Validate explicit records before creating any local storage.
        event = record_event(args) if args.command == 'record' else None
        private_dir(root)
        event = event or hook_event(args, root)
        with locked_file(root / (event['observed_at'][:10] + '.jsonl')) as file:
            file.seek(0, os.SEEK_END)
            file.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + '\n')
            file.flush()
            os.fsync(file.fileno())
        return 0
    except Exception:
        # Never include exception text: it may contain a path or user payload.
        sys.stderr.write('[harness-activity] event not recorded: invalid input or storage failure\n')
        return 0 if args.command == 'hook' else 1


if __name__ == '__main__':
    sys.exit(main())
