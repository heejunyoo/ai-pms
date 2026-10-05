#!/usr/bin/env python3
"""Clean-download gate. Synthetic local execution never proves app/remote adoption."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def verify(root):
    def run(path, *args, stdin=None):
        result = subprocess.run([sys.executable, str(root / path), *map(str, args)],
                                cwd=root, input=stdin, text=True, capture_output=True, timeout=180)
        # Never echo child output: credentials and private fixture paths stay local.
        if result.returncode:
            raise ValueError(f'{path} failed (exit {result.returncode}); run it locally for details')
        return result.stdout

    required = ['README.md', 'docs/adoption.md', 'kit/activity/logger.py',
                'kit/activity/connectivity.py', 'kit/activity/README.md',
                'templates/catalog-work.template.json', 'templates/operations.template.json',
                'docs/json-contracts.md', 'specs/ai-pms-live/README.md']
    for relative in required:
        if not (root / relative).is_file():
            raise ValueError(f'missing download file: {relative}')
    for relative in ('README.md', 'docs/adoption.md', 'specs/ai-pms-live/README.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', (root / relative).read_text()):
            if '://' in target or target.startswith('#'):
                continue
            if not ((root / relative).parent / target.split('#')[0]).exists():
                raise ValueError(f'broken local documentation link in {relative}: {target}')
    live = 'specs/ai-pms-live/'
    # Retains executable Kit runtime coverage after central runtime leaves its ZIP.
    for name in ('live_service.py', 'live_sender.py', 'session_goal.py', 'demo_setup.py'):
        run(live + name, '--help')
    with tempfile.TemporaryDirectory(prefix='pms-adoption-') as temporary:
        work = Path(temporary).resolve()
        pilot = work / 'pilot'
        output = run(live + 'demo_setup.py', '--directory', pilot)
        if '7 writer environments' not in output:
            raise ValueError('expected all 7 synthetic writer environments')
        credentials = list(pilot.rglob('*.credential'))
        if len(credentials) != 8 or any(p.stat().st_mode & 0o777 != 0o600 for p in credentials):
            raise ValueError('manager and seven writer credentials must be owner-only 0600')
        for source in ('codex', 'claude'):
            logdir = work / source
            output = run('kit/activity/logger.py', 'health', '--log-dir', logdir)
            if json.loads(output)['status'] != 'unknown':
                raise ValueError('empty capture must remain unknown')
            run('kit/activity/logger.py', 'hook', '--source', source, '--project-id',
                '11111111-1111-4111-8111-111111111111', '--log-dir', logdir,
                stdin=json.dumps(dict(hook_event_name='SessionStart', session_id='synthetic-download-session')))
            health = json.loads(run('kit/activity/logger.py', 'health', '--log-dir', logdir))
            events = [json.loads(row) for path in logdir.glob('*.jsonl') for row in path.read_text().splitlines()]
            if health['status'] != 'observed' or len(events) != 1 or health['last_event_id'] != events[0]['event_id']:
                raise ValueError('hook stdin/health event linkage failed')
        html, snapshot = work / 'documents.html', work / 'snapshot.json'
        run('specs/ai-pms-dashboard/portfolio.py', '--catalog', root / 'templates/catalog-work.template.json',
            '--out', html, '--json-out', snapshot)
        model = json.loads(snapshot.read_text())
        if not model['projects'] or any(s['event_count'] for p in model['projects'] for s in p['sources']):
            raise ValueError('document-only projection must have projects without observed events')
        if '<html' not in html.read_text():
            raise ValueError('document-only HTML not rendered')
    # Existing adverse-case tests, login cookies, durable ACK, seven writers, restart/dedup.
    for path in ('kit/activity/test_logger.py', live + 'test_kit_live.py',
                 live + 'test_live.py', live + 'test_demo.py'):
        run(path)
    print('PASS: clean-download links; runtime --help; 7 writers / 8 credential0600; Codex/Claude synthetic stdin + health; document-only HTML/snapshot; retained logger/live/auth/durable-ACK/dedup tests')
    print('Boundary: disposable synthetic loopback only. Actual app hooks/trust, remote users, browser rendering and production release require separate evidence.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1],
                        help='downloaded public repo root; no home-file fallback')
    args = parser.parse_args()
    try:
        verify(args.root.resolve())
        return 0
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
