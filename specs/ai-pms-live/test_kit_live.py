#!/usr/bin/env python3
"""Portable subprocess checks; synthetic stdin is not actual app-hook proof."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
# Public exports must check their own logger, never an unrelated home install.
LOGGER = REPO / 'kit/activity/logger.py'
if not LOGGER.is_file():
    LOGGER = Path.home() / '.claude/harness/activity/logger.py'
sys.path.insert(0, str(LOGGER.parent))
spec = importlib.util.spec_from_file_location('kit_logger', LOGGER)
logger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logger)


class KitLive(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.logs = self.root / 'logs'
        self.project = self.root / 'project'
        self.project.mkdir()

    def invoke(self, command='hook', payload=None, source='codex', logs=None):
        argv = [sys.executable, str(LOGGER), command, '--log-dir', str(logs or self.logs)]
        if command == 'hook': argv += ['--source', source]
        return subprocess.run(argv, input=json.dumps(payload or {'cwd': str(self.project), 'hook_event_name': 'Stop'}), text=True, capture_output=True)

    def health(self):
        return json.loads(self.invoke('health').stdout)

    def events(self):
        return [json.loads(line) for file in self.logs.glob('*.jsonl') for line in file.read_text().splitlines()]

    def test_success_stdout_health_permissions_and_privacy(self):
        for source in ('codex', 'claude'):
            for native in ('Stop', 'SubagentStop', 'PreToolUse'):
                result = self.invoke(payload={'cwd': str(self.project), 'hook_event_name': native, 'tool_name': 'Bash', 'prompt': 'SYNTHETIC_PRIVATE_INPUT'}, source=source)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, '')
                self.assertEqual(result.stdout, '{}\n' if source == 'codex' and native in ('Stop', 'SubagentStop') else '')
        health = self.health()
        self.assertEqual(set(health), {'version', 'last_event_id', 'last_recorded_at', 'errors', 'last_failure_at', 'status', 'at'})
        self.assertEqual(health['last_event_id'], self.events()[-1]['event_id'])
        self.assertEqual(health['last_recorded_at'], self.events()[-1]['observed_at'])
        self.assertEqual((health['status'], health['errors']), ('observed', 0))
        self.assertEqual(self.logs.stat().st_mode & 0o777, 0o700)
        for file in self.logs.iterdir(): self.assertEqual(file.stat().st_mode & 0o777, 0o600)
        raw = json.dumps(health)
        for private in (str(self.root), 'SYNTHETIC_PRIVATE_INPUT', 'actor_id', 'project_id', 'environment_id'):
            self.assertNotIn(private, raw)

    def test_failure_keeps_last_good_and_cumulative_errors(self):
        self.invoke()
        previous = self.health()
        for native in ('Stop', 'SubagentStop'):
            result = self.invoke(payload={'hook_event_name': native, 'cwd': 'invalid-relative'})
            self.assertEqual((result.returncode, result.stdout), (0, '{}\n'))
            self.assertIn('event not recorded', result.stderr)
            self.assertNotIn('invalid-relative', result.stderr)
        failed = self.health()
        self.assertEqual(failed['status'], 'degraded')
        self.assertEqual(failed['errors'], 2)
        self.assertIsNotNone(failed['last_failure_at'])
        for key in ('last_event_id', 'last_recorded_at'): self.assertEqual(failed[key], previous[key])
        self.invoke()
        recovered = self.health()
        self.assertEqual((recovered['status'], recovered['errors']), ('observed', 2))
        self.assertEqual(recovered['last_failure_at'], failed['last_failure_at'])

    def test_missing_corrupt_and_symlink_health_preserved(self):
        self.assertEqual(self.health()['status'], 'unknown')
        self.assertFalse(self.logs.exists())
        self.invoke()
        path = self.logs / 'capture-health.json'
        path.write_text('{corrupt SYNTHETIC_PRIVATE_INPUT')
        corrupt = path.read_bytes()
        result = self.invoke()
        self.assertIn('event recorded; capture health update failed', result.stderr)
        self.assertEqual(result.stdout, '{}\n')
        self.assertEqual(len(self.events()), 2)
        self.assertEqual(path.read_bytes(), corrupt)
        read = self.invoke('health')
        self.assertEqual(read.returncode, 1)
        self.assertEqual(json.loads(read.stdout)['status'], 'unknown')
        self.assertNotIn('SYNTHETIC_PRIVATE_INPUT', read.stderr)
        path.unlink()
        target = self.root / 'target.json'
        target.write_text('preserve target')
        path.symlink_to(target)
        self.assertIn('health update failed', self.invoke().stderr)
        self.assertTrue(path.is_symlink())
        self.assertEqual(target.read_text(), 'preserve target')
        self.assertEqual(self.health()['status'], 'unknown')

    def test_symlink_directory_is_not_written(self):
        target = self.root / 'target'
        target.mkdir()
        alias = self.root / 'alias'
        alias.symlink_to(target, target_is_directory=True)
        result = self.invoke(logs=alias / 'logs')
        self.assertEqual((result.returncode, result.stdout), (0, '{}\n'))
        self.assertIn('event not recorded', result.stderr)
        self.assertEqual(list(target.iterdir()), [])

    def test_concurrent_success_and_failure(self):
        self.invoke()
        def run(index):
            return self.invoke(payload={'hook_event_name': 'Stop', 'cwd': str(self.project) if index % 2 else 'bad'})
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(run, range(32)))
        self.assertTrue(all(r.returncode == 0 and r.stdout == '{}\n' for r in results))
        events = self.events()
        health = self.health()
        self.assertEqual(len(events), 17)
        self.assertEqual(len({e['event_id'] for e in events}), 17)
        self.assertEqual(health['errors'], 16)
        self.assertEqual(health['last_event_id'], events[-1]['event_id'])
        self.assertFalse(list(self.logs.glob('*.tmp')))

    def test_fsync_failure_preserves_health_and_atomic_file(self):
        self.invoke()
        previous = (self.logs / 'capture-health.json').read_bytes()
        with logger.locked_file(self.logs / '.capture-health.lock'):
            with patch.object(logger.os, 'fsync', side_effect=OSError('private path omitted')):
                with self.assertRaises(OSError): logger.health_write(self.logs, self.events()[0])
        self.assertEqual((self.logs / 'capture-health.json').read_bytes(), previous)
        self.assertFalse(list(self.logs.glob('*.tmp')))


if __name__ == '__main__':
    unittest.main(verbosity=2)
