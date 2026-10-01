#!/usr/bin/env python3
"""Read-only inventory of known local hook declarations; never tests delivery."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[2]
MAX_CONFIG = 1_048_576
EVENTS = frozenset(('SessionStart', 'SessionEnd', 'UserPromptSubmit', 'PreToolUse',
                    'PostToolUse', 'PostToolUseFailure', 'SubagentStart', 'SubagentStop', 'Stop'))
LOGGER = re.compile(r'(?:harness-activity|harness/activity)/logger\.py\b')
HOOK = re.compile(r'(?<![\w-])hook(?![\w-])')
SCOPE_FILES = (
    ('codex_global_hooks_json', '.codex/hooks.json', 'home', 'json'),
    ('codex_project_hooks_json', '.codex/hooks.json', 'project', 'json'),
    ('codex_global_config_toml', '.codex/config.toml', 'home', 'toml'),
    ('codex_project_config_toml', '.codex/config.toml', 'project', 'toml'),
    ('claude_global_settings_json', '.claude/settings.json', 'home', 'json'),
    ('claude_global_local_json', '.claude/settings.local.json', 'home', 'json'),
    ('claude_project_settings_json', '.claude/settings.json', 'project', 'json'),
    ('claude_project_local_json', '.claude/settings.local.json', 'project', 'json'),
)


def read_config(path, kind):
    if not path.exists() and not path.is_symlink():
        return 'missing', None
    if path.is_symlink() or path.parent.is_symlink():
        return 'unsafe', None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as source:
            info = os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                return 'unsafe', None
            if info.st_size > MAX_CONFIG:
                return 'oversized', None
            raw = source.read(MAX_CONFIG + 1)
        if len(raw) > MAX_CONFIG:
            return 'oversized', None
        value = json.loads(raw) if kind == 'json' else tomllib.loads(raw.decode('utf-8'))
        if not isinstance(value, dict):
            return 'invalid', None
        return 'readable', value
    except (OSError, UnicodeError, ValueError, RecursionError):
        return 'invalid', None


def command_objects(value):
    """Only inspect command slots of known hook groups, never arbitrary settings."""
    if not isinstance(value, list):
        return []
    objects = []
    for group in value:
        if not isinstance(group, dict):
            continue
        hooks = group.get('hooks')
        if isinstance(hooks, list):
            objects.extend(item for item in hooks if isinstance(item, dict))
        elif group.get('type') == 'command':
            objects.append(group)
    return objects


def valid_groups(value):
    if not isinstance(value, list):
        return False
    for group in value:
        if not isinstance(group, dict):
            return False
        if 'hooks' in group:
            items = group['hooks']
            if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
                return False
        elif 'type' in group:
            items = [group]
        else:
            return False
        for item in items:
            if item.get('type') == 'command':
                command = item.get('command')
                if not (isinstance(command, str) or
                        isinstance(command, list) and all(isinstance(part, str) for part in command)):
                    return False
    return True


def logger_declaration(item):
    if item.get('type') != 'command':
        return False
    command = item.get('command')
    if isinstance(command, str):
        text = command
    elif isinstance(command, list) and all(isinstance(part, str) for part in command):
        text = ' '.join(command)
    else:
        return False
    return len(text) <= MAX_CONFIG and bool(LOGGER.search(text) and HOOK.search(text))


def collect_inventory(project_root=ROOT, home_root=None):
    home_root = home_root or Path.home()
    scopes = []
    for alias, relative, origin, kind in SCOPE_FILES:
        base = home_root if origin == 'home' else project_root
        state, config = read_config(base / relative, kind)
        counts = {}
        unknown = 0
        if config is not None:
            hooks = config.get('hooks')
            if hooks is None:
                hooks = {}
            if not isinstance(hooks, dict):
                state = 'invalid'
            else:
                for event, groups in hooks.items():
                    if event in EVENTS:
                        if not valid_groups(groups):
                            state = 'invalid'
                            continue
                        count = sum(logger_declaration(item) for item in command_objects(groups))
                        if count:
                            counts[event] = count
                    elif command_objects(groups):
                        unknown += 1
        scopes.append({'scope_alias': alias, 'state': state, 'logger_hook_counts': counts,
                       'unknown_event_keys': unknown})
    return {'scope': 'approval-preparation', 'inventory_kind': 'known_config_declarations_only',
            'detection': 'known_path_and_hook_token_heuristic',
            'actual_delivery_verified': False, 'product_complete': False,
            'api_implementation_approved': False,
            'unexamined': ['plugins', 'managed_settings', 'other_configuration_layers',
                           'hook_trust', 'effective_runtime', 'live_app_events'],
            'scopes': scopes,
            'logger_declaration_count': sum(sum(s['logger_hook_counts'].values()) for s in scopes)}


def write_new_report(path, report):
    if path.suffix != '.json' or path.is_symlink() or path.parent.is_symlink():
        raise ValueError('unsafe report target')
    parent = path.parent
    if not parent.is_dir() or parent.stat().st_uid != os.getuid():
        raise ValueError('unsafe report directory')
    payload = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())


def selftest():
    def require(condition):
        if not condition:
            raise ValueError('selftest assertion failed')

    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        home, project = temp / 'home', temp / 'project'
        for base in (home, project):
            (base / '.codex').mkdir(parents=True)
            (base / '.claude').mkdir()
        marker = 'PRIVATE-MARKER-DO-NOT-REPORT'
        valid = {'hooks': {'PostToolUse': [{'hooks': [{'type': 'command',
                 'command': 'python3 "$HOME/.agents/harness-activity/logger.py" hook --source codex ' + marker},
                 {'type': 'prompt'}]}],
                 'unknown_' + marker: [{'hooks': [{'type': 'command',
                 'command': 'python3 logger.py hook'}]}]}}
        (home / '.codex/hooks.json').write_text(json.dumps(valid))
        (home / '.codex/config.toml').write_text('[hooks]\nSessionStart = [{hooks = [{type = "command", command = "python3 ~/.agents/harness-activity/logger.py hook --source codex"}]}]\n')
        (home / '.claude/settings.json').write_text('{')
        (project / '.codex/hooks.json').write_bytes(b'x' * (MAX_CONFIG + 1))
        (project / '.claude/settings.json').symlink_to(home / '.codex/hooks.json')
        (project / '.claude/settings.local.json').write_text('{"hooks":{"PostToolUse":"not-a-list"}}')
        report = collect_inventory(project, home)
        indexed = {s['scope_alias']: s for s in report['scopes']}
        require(indexed['codex_global_hooks_json']['logger_hook_counts'] == {'PostToolUse': 1})
        require(indexed['codex_global_hooks_json']['unknown_event_keys'] == 1)
        require(indexed['codex_global_config_toml']['logger_hook_counts'] == {'SessionStart': 1})
        require(indexed['codex_project_config_toml']['state'] == 'missing')
        require(indexed['claude_global_settings_json']['state'] == 'invalid')
        require(indexed['codex_project_hooks_json']['state'] == 'oversized')
        require(indexed['claude_project_settings_json']['state'] == 'unsafe')
        require(indexed['claude_project_local_json']['state'] == 'invalid')
        require(marker not in json.dumps(report))
        require(report['actual_delivery_verified'] is False)
        require(report['product_complete'] is False)
        require(report['api_implementation_approved'] is False)
        target = temp / 'report.json'
        write_new_report(target, report)
        try:
            write_new_report(target, report)
        except FileExistsError:
            pass
        else:
            raise AssertionError('existing report overwritten')
    print('preparation selftest OK')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.selftest:
            if args.output:
                raise ValueError('selftest output not supported')
            selftest()
        else:
            report = collect_inventory()
            if args.output:
                write_new_report(args.output.absolute(), report)
            else:
                print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, AssertionError):
        # Never echo an input path, command, setting, or secret.
        print('preparation: local check failed', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
