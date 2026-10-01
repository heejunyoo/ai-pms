#!/usr/bin/env python3
"""Real subprocess/storage checks; run directly with Python 3."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

LOGGER = Path(__file__).with_name('logger.py')


class LoggerChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.logs = self.root / 'logs'
        self.project = self.root / 'project'
        self.project.mkdir()
        (self.project / '.git').mkdir()

    def run_hook(self, payload, source='codex', extra=()):
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run([sys.executable, str(LOGGER), 'hook', '--source', source,
                               '--log-dir', str(self.logs), *extra], input=raw,
                              text=True, capture_output=True)

    def events(self):
        return [json.loads(line) for path in self.logs.glob('*.jsonl') for line in path.read_text().splitlines()]

    def record(self, kind, data, links, extra=()):
        return subprocess.run([sys.executable, str(LOGGER), 'record', '--kind', kind,
                               '--project-id', '11111111-1111-4111-8111-111111111111',
                               '--log-dir', str(self.logs), '--data', json.dumps(data),
                               '--links', json.dumps(links), *extra], capture_output=True, text=True)

    def test_native_privacy_identity_and_correlation(self):
        secret = 'sk-secretCredential123456789'
        payload = {'cwd': str(self.project), 'hook_event_name': 'PreToolUse', 'session_id': 'session-1',
                   'tool_call_id': 'call-1', 'tool_name': 'Bash', 'prompt': secret,
                   'tool_input': {'command': 'cat ' + str(self.project)}, 'tool_response': secret,
                   'model': 'must-not-be-agent-id'}
        result = self.run_hook(payload)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        child = self.project / 'src'
        child.mkdir()
        self.run_hook({**payload, 'cwd': str(child)}, 'claude')
        first, second = self.events()
        self.assertEqual(first['project_id'], second['project_id'])
        self.assertEqual(first['kind'], 'tool.requested')
        self.assertEqual(first['session_id'], 'session-1')
        self.assertIsNone(first['agent_id'])
        self.assertIsNone(first['occurred_at'])
        self.assertEqual(first['data'], {})
        for event in (first, second):
            text = json.dumps(event)
            self.assertNotIn(secret, text)
            self.assertNotIn(str(self.project), text)
            uuid.UUID(event['event_id'])
        self.assertEqual(self.logs.stat().st_mode & 0o777, 0o700)
        for path in self.logs.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_unknown_and_sanitized_native_metadata(self):
        self.run_hook({'cwd': str(self.project), 'hook_event_name': '/home/private/event',
                       'tool_name': 'sk-doNotRecordCredential1234', 'agent_id': '/home/private/agent'})
        event = self.events()[0]
        self.assertEqual((event['native_event'], event['kind']), ('unknown', 'unknown'))
        self.assertIsNone(event['tool_name'])
        self.assertIsNone(event['agent_id'])
        self.assertIn('native_event', event['missing_fields'])

    def test_malformed_size_and_storage_failures_are_visible_nonblocking(self):
        for raw in ('{bad sensitive payload', '[]', '{"cwd": NaN}', 'x' * 1_048_577):
            result = self.run_hook(raw)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')
            self.assertIn('event not recorded', result.stderr)
            self.assertNotIn('sensitive payload', result.stderr)
        self.assertEqual(self.events(), [])
        self.logs.rmdir()
        target = self.root / 'target'
        target.mkdir()
        self.logs.symlink_to(target)
        result = self.run_hook({'cwd': str(self.project), 'hook_event_name': 'Stop'})
        self.assertEqual(result.returncode, 0)
        self.assertIn('event not recorded', result.stderr)
        self.assertEqual(list(target.iterdir()), [])

    def test_concurrent_append_and_index_are_consistent(self):
        payload = {'cwd': str(self.project), 'hook_event_name': 'Stop'}
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.run_hook(payload), range(24)))
        self.assertTrue(all(r.returncode == 0 and r.stderr == '' for r in results))
        events = self.events()
        self.assertEqual(len(events), 24)
        self.assertEqual(len({e['event_id'] for e in events}), 24)
        self.assertEqual(len({e['project_id'] for e in events}), 1)
        self.assertTrue(all(e['kind'] == 'turn.stopped' for e in events))

    def test_manual_exact_links_and_declared_authority(self):
        artifact = {'artifact_id': 'artifact-1', 'artifact_version': 'v1'}
        baseline = {'phase_id': 'p1', 'baseline_version': 'b1'}
        cases = [('project.baseline', {'goal': 'Local evidence', 'scope': 'Offline logger and viewer'}, baseline),
                 ('decision.recorded', {'summary': 'Use offline logs', 'reason': 'Local privacy',
                                        'scope_added': 'Offline viewer', 'scope_removed': 'Remote upload'},
                  {**baseline, 'decision_id': 'd1'}),
                 ('artifact.recorded', {'summary': 'Viewer'}, artifact),
                 ('check.recorded', {'status': 'pass', 'environment': 'local'}, {**artifact, 'check_id': 'c1'}),
                 ('acceptance.recorded', {'status': 'pending'}, artifact)]
        for kind, data, links in cases:
            result = self.record(kind, data, links)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        events = self.events()
        self.assertTrue(all(e['authority'] == 'declared' and e['source'] == 'manual' for e in events))
        self.assertEqual(events[-1]['data']['status'], 'pending')
        self.assertIsNone(events[3]['session_id'])
        self.assertEqual(events[3]['links']['artifact_version'], 'v1')
        self.assertEqual(events[0]['links']['baseline_version'], 'b1')
        self.assertEqual(events[1]['data']['reason'], 'Local privacy')

    def test_baseline_and_decision_require_revision_and_nonempty_content(self):
        baseline = {'phase_id': 'p1', 'baseline_version': 'b1'}
        cases = [('project.baseline', {'goal': 'Goal', 'scope': 'Scope'}, {'phase_id': 'p1'}),
                 ('project.baseline', {'goal': 'Goal', 'scope': '   '}, baseline),
                 ('project.baseline', {'scope': 'Scope'}, baseline),
                 ('decision.recorded', {'summary': 'Decision', 'reason': 'Reason'}, {'decision_id': 'd1'}),
                 ('decision.recorded', {'summary': 'Decision'}, {**baseline, 'decision_id': 'd1'}),
                 ('decision.recorded', {'summary': '\n', 'reason': 'Reason'}, {**baseline, 'decision_id': 'd1'})]
        for kind, data, links in cases:
            self.assertNotEqual(self.record(kind, data, links).returncode, 0)
        self.assertEqual(self.events(), [])

    def test_manual_correlation_is_declared_and_validated(self):
        links = {'artifact_id': 'a', 'artifact_version': 'v1'}
        result = self.record('artifact.recorded', {}, links,
                             ('--agent-id', 'worker-1', '--parent-agent-id', 'root-1',
                              '--session-id', 'session-1', '--turn-id', 'turn-1', '--tool-call-id', 'call-1'))
        self.assertEqual(result.returncode, 0)
        event = self.events()[0]
        self.assertEqual(event['authority'], 'declared')
        self.assertEqual(event['agent_id'], 'worker-1')
        self.assertEqual(event['parent_agent_id'], 'root-1')
        self.assertEqual(event['turn_id'], 'turn-1')
        self.assertEqual(event['tool_call_id'], 'call-1')
        for flag in ('--agent-id', '--parent-agent-id', '--session-id', '--turn-id', '--tool-call-id'):
            self.assertNotEqual(self.record('artifact.recorded', {}, links, (flag, '/home/private/id')).returncode, 0)
        self.assertEqual(len(self.events()), 1)

    def test_manual_rejects_credentials_paths_keys_and_unversioned_checks(self):
        links = {'artifact_id': 'a', 'artifact_version': 'v1', 'check_id': 'c'}
        bad = [({'summary': 'Bearer SYNTHETIC_FIXTURE', 'status': 'pass'}, links),
               ({'summary': 'api_key=secret123', 'status': 'pass'}, links),
               ({'summary': '/home/person/private.txt', 'status': 'pass'}, links),
               ({'summary': 'x' * 2001, 'status': 'pass'}, links),
               ({'status': 'pass', 'output': 'raw'}, links),
               ({'status': 'complete'}, links), ({'summary': 'missing status'}, links),
               ({'status': 'pass'}, {'check_id': 'c', 'artifact_id': 'a'})]
        for data, binding in bad:
            result = self.record('check.recorded', data, binding)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('secret123', result.stderr)
        self.assertEqual(self.events(), [])

    def test_override_and_native_time(self):
        alias = '22222222-2222-4222-8222-222222222222'
        self.run_hook({'hook_event_name': 'SessionStart', 'occurred_at': '2026-09-30T10:00:00+09:00'},
                      extra=('--project-id', alias))
        event = self.events()[0]
        self.assertEqual(event['project_id'], alias)
        self.assertEqual(event['occurred_at'], '2026-09-30T01:00:00Z')
        self.assertIn('cwd', event['missing_fields'])

    def test_provider_tool_use_correlation_and_mcp_category(self):
        for source in ('codex', 'claude'):
            for native in ('PreToolUse', 'PostToolUse'):
                self.run_hook({'cwd': str(self.project), 'hook_event_name': native,
                               'tool_use_id': 'native-use-1', 'tool_name': 'mcp__private_server__private_tool'}, source)
        events = self.events()
        self.assertTrue(all(e['tool_call_id'] == 'native-use-1' and e['tool_name'] == 'MCP' for e in events))
        self.assertTrue(all(e['data']['connection']['server'] == 'private_server' for e in events))
        self.assertTrue(all(e['data']['connection']['operation'] == 'unknown' and not e['data']['connection']['resources'] for e in events))


    def test_connectivity_stdin_metadata_and_map(self):
        metadata=dict(operation='read',resources=[dict(id='customers',kind='database',label='Synthetic customers',evidence='input')],artifact_refs=[dict(id='report',version='v1')])
        payload=dict(cwd=str(self.project),hook_event_name='PostToolUse',tool_name='mcp__crm__lookup',duration_ms=12,pms_metadata=metadata,tool_input={'sql':'SELECT private FROM secret'},tool_response='sk-secretCredential123456789')
        self.assertEqual(self.run_hook(payload).stderr,'')
        e=self.events()[-1]
        self.assertEqual(e['schema_version'],2)
        self.assertEqual((e['data']['connection']['server'],e['data']['connection']['tool']),('crm','lookup'))
        self.assertEqual(e['data']['connection']['resources'],metadata['resources'])
        self.assertNotIn('SELECT',json.dumps(e))
        mapping=self.root/'map.json';mapping.write_text(json.dumps({'mcp__crm__lookup':metadata}))
        del payload['pms_metadata']
        self.run_hook(payload,extra=('--resource-map',str(mapping)))
        self.assertEqual(self.events()[-1]['data']['connection']['resources'][0]['evidence'],'declared')
        payload['pms_metadata']={**metadata,'resources':[dict(id='customers',kind='database',label='https://secret.example',evidence='output')]}
        self.run_hook(payload)
        self.assertIn('connection.metadata',self.events()[-1]['missing_fields'])
        self.assertEqual(self.events()[-1]['data']['connection']['resources'],[])

if __name__ == '__main__':
    unittest.main(verbosity=2)
