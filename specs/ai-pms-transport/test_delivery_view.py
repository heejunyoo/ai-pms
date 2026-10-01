#!/usr/bin/env python3
"""Bounded delivery metadata and render integration checks; no browser claim."""
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import uuid

import common as c
import receiver

central = c.central
HERE = Path(__file__).resolve().parent


class DeliveryView(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'receiver'
        self.store = self.base / 'store'
        c.private_dir(self.root)
        self.project = str(uuid.uuid4())
        self.contexts = [{'actor_id': actor, 'environment_id': 'desktop', 'project_id': self.project,
                          'label': '합성 ' + actor} for actor in ('alice', 'bob')]
        self.state_path = self.root / 'delivery-state.json'
        self.state = {'version': 1, 'registered_contexts': self.contexts, 'batches': []}
        self.registry = self.base / 'registry.json'
        self.tokens = ['temporary-synthetic-a', 'temporary-synthetic-b']
        c.write_private(self.registry, c.encode({'version': 1, 'environments': [
            {'actor_id': v['actor_id'], 'environment_id': v['environment_id'],
             'token_sha256': c.digest(token.encode()), 'projects': [{'project_id': v['project_id'], 'label': v['label']}]}
            for v, token in zip(self.contexts, self.tokens)]}))

    def save(self, state=None):
        c.write_private(self.state_path, c.encode(self.state if state is None else state))

    def batch(self, context=0, state='aggregated', count=0, reason='none'):
        return {'context_key': central.source_key(self.contexts[context]), 'batch_id': str(uuid.uuid4()),
                'payload_sha256': '0' * 64, 'received_at': '2026-09-30T12:00:00Z', 'event_count': count,
                'state': state, 'reason_code': reason, 'updated_at': '2026-09-30T12:00:01Z'}

    def page_data(self, path):
        return json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', path.read_text()).group(1))

    def test_registration_heartbeat_and_failure_contexts(self):
        self.save()
        registered_only = central.summarize({'sources': {}}, central.load_delivery_state(self.state_path))
        self.assertEqual(len(registered_only), 2)
        self.assertIn('연결 확인 없음', registered_only[0]['issues'])
        self.assertIsNone(registered_only[0]['delivery']['last_received'])
        self.assertEqual(registered_only[0]['delivery']['counts']['aggregated'], 0)
        self.state['batches'] = [self.batch(), self.batch(state='queued', count=2),
                                 self.batch(1, 'failed', 1, 'import_failed'),
                                 self.batch(1, 'conflict', 1, 'event_conflict')]
        self.save()
        state = central.load_delivery_state(self.state_path)
        self.assertNotIn('error', state)
        projects = central.summarize({'sources': {}}, state)
        a, b = projects
        self.assertEqual(len(projects), 2)
        self.assertNotEqual(a['key'], b['key'])
        self.assertEqual(a['project_id'], b['project_id'])
        for p in projects:
            self.assertIsNone(p['goal'])
            self.assertIsNone(p['phase'])
            self.assertIsNone(p['last_observed'])
            self.assertEqual(p['agent_count'], 0)
            self.assertIn('작업 관측 없음', p['issues'])
        self.assertEqual(a['delivery']['heartbeat_count'], 1)
        self.assertEqual(a['delivery']['counts']['queued'], 1)
        self.assertEqual(b['delivery']['counts']['failed'], 1)
        self.assertIn('전달 실패', b['issues'])
        self.assertIn('전달 충돌', b['issues'])
        removed = self.batch(1, 'failed', 1, 'registration_changed')
        self.state['registered_contexts'] = self.contexts[:1]
        self.state['batches'] = [removed]
        self.save()
        state = central.load_delivery_state(self.state_path)
        self.assertNotIn('error', state)
        self.assertTrue(any('등록 불일치' in issue for issue in central.delivery_issues(state)))
        p = central.summarize({'sources': {}}, state)[0]
        self.assertTrue(any('등록 불일치' in issue for issue in p['issues']))

    def test_strict_metadata_and_fail_safe(self):
        self.assertEqual(central.load_delivery_state(self.state_path)['error'], 'delivery_state_unknown')
        variants = []
        for field, value in [('version', True), ('version', 2), ('batches', {}), ('extra', 1)]:
            state = copy.deepcopy(self.state); state[field] = value; variants.append(state)
        state = copy.deepcopy(self.state); state['registered_contexts'].append(state['registered_contexts'][0]); variants.append(state)
        for field, value in [('actor_id', 'bad/id'), ('project_id', 'bad'), ('label', 'token=hidden-secret')]:
            state = copy.deepcopy(self.state); state['registered_contexts'][0][field] = value; variants.append(state)
        for field, value in [('context_key', '["alice", "desktop", "bad"]'), ('batch_id', 'bad'),
                             ('payload_sha256', 'bad'), ('event_count', True), ('event_count', 101),
                             ('received_at', 'tomorrow'), ('updated_at', '2026-09-30T11:00:00Z'),
                             ('state', []), ('reason_code', 'event_conflict')]:
            state = copy.deepcopy(self.state); batch = self.batch(); batch[field] = value; state['batches'] = [batch]; variants.append(state)
        state = copy.deepcopy(self.state); batch = self.batch(); state['batches'] = [batch, batch]; variants.append(state)
        for state in variants:
            self.save(state)
            self.assertEqual(central.load_delivery_state(self.state_path)['error'], 'delivery_state_unknown')
        for raw in (b'{"version":1,"version":1}', b'{"version":NaN}', b'{', b'[' * 1000):
            c.write_private(self.state_path, raw)
            self.assertIn('error', central.load_delivery_state(self.state_path))
        self.save()
        self.state_path.chmod(0o644)
        self.assertIn('error', central.load_delivery_state(self.state_path))
        self.assertEqual(self.state_path.stat().st_mode & 0o777, 0o644)
        self.state_path.chmod(0o600)
        alias = self.root / 'alias.json'; alias.symlink_to(self.state_path)
        self.assertIn('error', central.load_delivery_state(alias))
        link = self.root / 'hardlink.json'; link.hardlink_to(self.state_path)
        self.assertIn('error', central.load_delivery_state(link)); link.unlink()
        with self.state_path.open('r+b') as f:
            f.truncate(c.MAX_STATE + 1)
        self.assertIn('error', central.load_delivery_state(self.state_path))
        self.save()
        c.write_private(self.root / 'delivery-state.error', b'delivery_state_unknown\n')
        state = central.load_delivery_state(self.state_path)
        self.assertIn('error', state)
        self.assertEqual(len(state['registered_contexts']), 2)
        p = central.summarize({'sources': {}}, state)[0]
        self.assertIsNone(p['delivery']['counts'])
        self.assertIsNone(p['delivery']['last_received'])
        self.assertIn('전달상태 불명', p['issues'])

    def test_receive_aggregate_and_original_provenance(self):
        # Genuine receiver storage/aggregate code, in-process synthetic test.
        event = {'schema_version': 1, 'adapter_version': '1', 'event_id': str(uuid.uuid4()),
                 'observed_at': '2026-09-30T12:00:00Z', 'occurred_at': None, 'source': 'codex',
                 'native_event': 'SessionStart', 'kind': 'session.start', 'authority': 'observed',
                 'project_id': self.project, 'tool_name': None, 'links': dict.fromkeys(central.LINKS),
                 'data': {}, 'missing_fields': [], **dict.fromkeys(central.IDS)}
        for token, events in zip(self.tokens, ([event], [])):
            receiver.receive(c.encode({'protocol_version': 1, 'batch_id': str(uuid.uuid4()),
                                       'project_id': self.project, 'events': events}), token, self.registry, self.root)
        queued = central.load_delivery_state(self.state_path)
        self.assertEqual(sum(b['state'] == 'queued' for b in queued['batches']), 2)
        receiver.aggregate(self.registry, self.root, self.store)
        state = central.load_delivery_state(self.state_path)
        store = central.load_store(self.store)
        projects = central.summarize(store, state)
        a, b = projects
        self.assertEqual(a['last_observed'], event['observed_at'])
        self.assertIsNone(b['last_observed'])
        self.assertEqual(a['events'][0]['event']['event_id'], event['event_id'])
        self.assertEqual(a['events'][0]['line'], 1)
        mirror = next(path for path in (self.root / 'mirrors').glob('*.jsonl') if path.stat().st_size)
        self.assertEqual(a['events'][0]['file_sha256'], c.digest(mirror.read_bytes()))
        self.assertIn('서버 mirror', a['source_provenance'])
        output = self.base / 'report.html'
        central.render(store, output, state)
        data = self.page_data(output)
        self.assertEqual(data[0]['events'], a['events'])
        page = output.read_text()
        self.assertIn('전달 집계 경로', data[0]['source_provenance'])
        self.assertIn('showOriginal(r,p)', page)
        self.assertIn('location.hash=encodeURIComponent(p.key)', page)
        self.assertNotIn(str(self.base), page)
        self.assertNotIn('token_sha256', page)
        for token in self.tokens:
            self.assertNotIn(token, page)

    def test_cli_corrupt_store_and_escaped_label(self):
        self.contexts[0]['label'] = '</script><img src=x onerror=alert(1)>'
        self.save()
        c.private_dir(self.store)
        c.write_private(self.store / 'central.json', b'{')
        output = self.base / 'fallback.html'
        args = [sys.executable, str(central.__file__), 'render', '--store', str(self.store), '--output', str(output)]
        plain = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(plain.returncode, 1)
        rendered = subprocess.run([*args, '--delivery-state', str(self.state_path)], capture_output=True, text=True)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        page = output.read_text()
        info = json.loads(re.search(r'<script id="delivery-data" type="application/json">(.*?)</script>', page).group(1))
        self.assertIn('중앙 저장 읽기 실패', info['issues'])
        self.assertIn('\\u003c/script\\u003e', page)
        self.assertNotIn(self.contexts[0]['label'], page)
        self.assertIn('textContent=String(value)', page)
        self.assertNotIn('.innerHTML', page)
        self.assertIn('role="status"', page)
        self.assertIn('minmax(min(230px,100%),1fr)', page)
        self.assertIn('@media(max-width:600px)', page)
        self.assertEqual(len(self.page_data(output)), 2)
        self.assertIn('중앙 저장 읽기 실패', self.page_data(output)[0]['issues'])
        # Malformed parsed source data also falls back only in delivery mode.
        c.write_private(self.store / 'central.json', c.encode({'version': 1, 'sources': {'bad': {}}}))
        rendered = subprocess.run([*args, '--delivery-state', str(self.state_path)], capture_output=True, text=True)
        self.assertEqual(rendered.returncode, 0)
        self.assertIn('중앙 저장 읽기 실패', self.page_data(output)[0]['issues'])
        # A list in the nested events slot raises AttributeError in summarize;
        # fail-safe must still produce the management banner without a traceback.
        c.write_private(self.store / 'central.json', c.encode({'version': 1, 'sources': {'bad': {'events': []}}}))
        rendered = subprocess.run([*args, '--delivery-state', str(self.state_path)], capture_output=True, text=True)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertIn('중앙 저장 읽기 실패', self.page_data(output)[0]['issues'])
        self.assertNotIn('Traceback', rendered.stderr)
        plain = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(plain.returncode, 1)
        self.assertEqual(plain.stderr.strip(), 'central: invalid input or storage failure')


if __name__ == '__main__':
    unittest.main(verbosity=2)
