#!/usr/bin/env python3
"""Small subprocess check for two-source local central flow (synthetic inputs)."""
import copy
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parent
LOGGER = ROOT.parents[1] / 'kit/activity/logger.py'
if not LOGGER.exists():
    LOGGER = Path.home() / '.claude/harness/activity/logger.py'
SPEC = importlib.util.spec_from_file_location('central', ROOT / 'central.py')
central = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(central)


class CentralFlow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = str(uuid.uuid4())
        self.logs_a = self.base / 'logs-a'
        self.logs_b = self.base / 'logs-b'

    def logger(self, directory, kind, data, links, *extra):
        command = [sys.executable, str(LOGGER), 'record', '--log-dir', str(directory), '--kind', kind,
                   '--project-id', self.project, '--data', json.dumps(data), '--links', json.dumps(links), *extra]
        subprocess.run(command, check=True, capture_output=True, text=True)

    def hook(self, directory, source, **fields):
        payload = {'hook_event_name': 'SubagentStart', 'cwd': str(self.base), **fields}
        command = [sys.executable, str(LOGGER), 'hook', '--source', source, '--project-id', self.project,
                   '--log-dir', str(directory)]
        subprocess.run(command, input=json.dumps(payload), check=True, capture_output=True, text=True)

    def events(self, directory):
        return [json.loads(line) for path in sorted(directory.glob('*.jsonl')) for line in path.read_text().splitlines()]

    def write_jsonl(self, name, events):
        (self.base / name).write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in events))

    def manifest(self, sources):
        path = self.base / 'manifest.json'
        path.write_text(json.dumps({'sources': sources}, ensure_ascii=False))
        return path

    def source(self, actor, environment, filename):
        return {'actor_id': actor, 'environment_id': environment, 'project_id': self.project,
                'label': actor + ' 프로젝트', 'evidence_mode': 'synthetic', 'files': [filename]}

    def test_subprocess_import_identity_links_privacy_and_report(self):
        self.hook(self.logs_a, 'codex', session_id='s1', agent_id='same')
        self.hook(self.logs_a, 'claude', session_id='s1', agent_id='same')
        self.logger(self.logs_a, 'project.baseline', {'goal': '목표 </script><img src=x onerror=alert(1)>', 'scope': '기능 A'},
                    {'phase_id': 'phase1', 'baseline_version': 'v1'})
        self.logger(self.logs_a, 'decision.recorded', {'summary': '범위 추가', 'reason': '사용자 요청', 'scope_added': '기능 B'},
                    {'phase_id': 'phase1', 'baseline_version': 'v1', 'decision_id': 'd1'})
        self.logger(self.logs_a, 'artifact.recorded', {'summary': '산출물 A'},
                    {'artifact_id': 'art1', 'artifact_version': 'v1'}, '--session-id', 's1', '--agent-id', 'same')
        self.logger(self.logs_a, 'check.recorded', {'summary': '검사', 'status': 'pass', 'environment': 'local'},
                    {'check_id': 'c1', 'artifact_id': 'art1', 'artifact_version': 'v1'})
        self.logger(self.logs_a, 'acceptance.recorded', {'summary': '검토 대기', 'status': 'pending', 'environment': 'local'},
                    {'artifact_id': 'art1', 'artifact_version': 'v1'})
        a = self.events(self.logs_a)
        secret = copy.deepcopy(next(e for e in a if e['kind'] == 'project.baseline'))
        secret['event_id'] = str(uuid.uuid4())
        secret['data']['goal'] = 'token=' + 'abc123456789'
        wrong = copy.deepcopy(a[0])
        wrong['event_id'], wrong['project_id'] = str(uuid.uuid4()), str(uuid.uuid4())
        conflicting = copy.deepcopy(next(e for e in a if e['kind'] == 'project.baseline'))
        conflicting['data']['goal'] = '다른 목표'
        invalid_contract = copy.deepcopy(a[0])
        invalid_contract['event_id'], invalid_contract['schema_version'] = str(uuid.uuid4()), True
        invalid_kind = copy.deepcopy(a[0])
        invalid_kind['event_id'], invalid_kind['native_event'], invalid_kind['kind'] = str(uuid.uuid4()), 'arbitrary', None
        a.extend([secret, wrong, conflicting, invalid_contract, invalid_kind])
        self.write_jsonl('source-a.jsonl', a)

        self.logger(self.logs_b, 'project.baseline', {'goal': '별도 목표', 'scope': '범위 B'},
                    {'phase_id': 'phase2', 'baseline_version': 'v2'})
        self.logger(self.logs_b, 'check.recorded', {'summary': '다른 출처 산출물 검사', 'status': 'fail', 'environment': 'local'},
                    {'check_id': 'c2', 'artifact_id': 'art1', 'artifact_version': 'v1'})
        self.logger(self.logs_b, 'acceptance.recorded', {'summary': '다른 출처 인수', 'status': 'rejected', 'environment': 'local'},
                    {'artifact_id': 'art1', 'artifact_version': 'v1'})
        b = self.events(self.logs_b)
        old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=49)).isoformat().replace('+00:00', 'Z')
        for e in b:
            e['observed_at'] = old
        self.write_jsonl('source-b.jsonl', b)
        manifest = self.manifest([self.source('alice', 'desktop', 'source-a.jsonl'),
                                  self.source('bob', 'laptop', 'source-b.jsonl'),
                                  self.source('carol', 'offline', 'missing.jsonl')])
        store_dir = self.base / 'store'
        command = [sys.executable, str(ROOT / 'central.py'), 'import', '--manifest', str(manifest), '--store', str(store_dir)]
        subprocess.run(command, check=True, capture_output=True, text=True)
        stored = central.load_store(store_dir)
        self.assertEqual(len(stored['sources']), 3)
        summaries = {p['actor_id']: p for p in central.summarize(stored)}
        self.assertEqual(summaries['alice']['goal'], '목표 </script><img src=x onerror=alert(1)>')
        self.assertEqual(summaries['bob']['goal'], '별도 목표')
        self.assertEqual(summaries['alice']['agent_count'], 2)
        self.assertEqual(summaries['alice']['ambiguous_agent_count'], 1)
        self.assertEqual(summaries['alice']['relations'][0]['agent_status'], '모호함')
        self.assertEqual(summaries['alice']['check_count'], 1)
        self.assertEqual(summaries['alice']['acceptance_count'], 1)
        self.assertIn('인수 거절·대기', summaries['alice']['issues'])
        self.assertIn('산출물 검증 불일치', summaries['bob']['issues'])
        self.assertIn('산출물 인수 미연결', summaries['bob']['issues'])
        self.assertIn('수집 지연', summaries['bob']['issues'])
        self.assertIn('연결 실패·입력 없음', summaries['carol']['issues'])
        self.assertEqual(summaries['alice']['last_import']['invalid'], 4)
        self.assertEqual(summaries['alice']['last_import']['conflicts'], 1)
        self.assertNotIn('token=' + 'abc123456789', (store_dir / 'central.json').read_text())
        self.assertNotIn(str(self.base), (store_dir / 'central.json').read_text())
        self.assertEqual(stat.S_IMODE((store_dir / 'central.json').stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(store_dir.stat().st_mode), 0o700)
        first = next(iter(stored['sources'].values()))['events']
        first_received = {k: v['received_at'] for k, v in first.items()}
        subprocess.run(command, check=True, capture_output=True, text=True)
        stored_again = central.load_store(store_dir)
        self.assertEqual({k: v['received_at'] for k, v in next(iter(stored_again['sources'].values()))['events'].items()}, first_received)
        self.assertEqual(len(next(iter(stored_again['sources'].values()))['events']), len(first))
        self.assertGreater(next(iter(stored_again['sources'].values()))['last_import']['duplicates'], 0)
        report = self.base / 'report.html'
        subprocess.run([sys.executable, str(ROOT / 'central.py'), 'render', '--store', str(store_dir), '--output', str(report)], check=True)
        page = report.read_text()
        self.assertIn('프로젝트 목록', page)
        self.assertIn('원본 이벤트', page)
        self.assertIn('관계 목록', page)
        self.assertIn('\\u003c/script\\u003e', page)
        self.assertNotIn('token=' + 'abc123456789', page)
        self.assertNotIn(str(self.base), page)

    def test_connectivity_status_and_malformed_tools_fail_closed(self):
        self.hook(self.logs_a, 'codex', hook_event_name='PreToolUse', session_id='s', tool_name='mcp__crm__lookup')
        event=self.events(self.logs_a)[0]
        self.assertTrue(central.valid_event(event,self.project))
        mismatch=copy.deepcopy(event);mismatch['data']['connection']['status']='completed'
        self.assertFalse(central.valid_event(mismatch,self.project))
        for value in ([],{},3):
            bad=copy.deepcopy(event);bad['tool_name']=value
            self.assertFalse(central.valid_event(bad,self.project))
        manual=copy.deepcopy(event)
        manual.update(schema_version=1,adapter_version='1',source='manual',authority='declared',native_event='project.baseline',kind='project.baseline',tool_name=None,data={'goal':'Bearer SYNTHETIC_FIXTURE','scope':'test'})
        manual['links'].update(phase_id='p',baseline_version='v1')
        self.assertFalse(central.valid_event(manual,self.project))

    def test_time_order_future_and_past_errors(self):
        self.logger(self.logs_a, 'project.baseline', {'goal': '이전', 'scope': 'a'}, {'phase_id': 'p1', 'baseline_version': 'v1'})
        self.logger(self.logs_a, 'project.baseline', {'goal': '이후', 'scope': 'b'}, {'phase_id': 'p2', 'baseline_version': 'v2'})
        e1, e2 = self.events(self.logs_a)
        e1['observed_at'] = '2026-09-30T12:00:00Z'
        e2['observed_at'] = '2026-09-30T12:00:00.100000Z'
        # Lexically, Z sorts after '.', but the latter is later in time.
        records = {e['event_id']: {'event': e, 'received_at': e['observed_at'], 'file_sha256': '0' * 64, 'line': i}
                   for i, e in enumerate((e1, e2), 1)}
        source = self.source('alice', 'desktop', 'x.jsonl')
        source.update(events=records, last_import={'at': e2['observed_at'], **{k: 0 for k in ('new', 'duplicates', 'conflicts', 'invalid', 'missing_files', 'empty_files', 'read_failures', 'limited')}},
                      totals={'conflicts': 1, 'invalid': 1})
        result = central.summarize({'sources': {central.source_key(source): source}})[0]
        self.assertEqual(result['goal'], '이후')
        self.assertIn('과거 수집 오류 기록', result['issues'])
        for record in records.values():
            record['event']['observed_at'] = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat().replace('+00:00', 'Z')
        result = central.summarize({'sources': {central.source_key(source): source}})[0]
        self.assertIn('미래 관측 시각', result['issues'])
        self.assertNotIn('수집 지연', result['issues'])


    def test_v2_stdin_central_transport_and_strict_rejection(self):
        self.hook(self.logs_a,'claude',hook_event_name='PostToolUse',tool_name='mcp__crm__lookup',pms_metadata=dict(operation='read',resources=[dict(id='customers',kind='database',label='Synthetic customers',evidence='output')],artifact_refs=[dict(id='report',version='v1')]))
        e=self.events(self.logs_a)[0]
        self.assertTrue(central.valid_event(e,self.project))
        spec=importlib.util.spec_from_file_location('connectivity_transport',ROOT.parent/'ai-pms-transport/common.py')
        transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
        batch=dict(protocol_version=1,batch_id=str(uuid.uuid4()),project_id=self.project,events=[e])
        self.assertEqual(transport.validate_batch(transport.encode(batch)),batch)
        for field,value in [('server','https://private.example'),('duration_ms',True),('operation','SELECT secret FROM users'),('resources',[dict(id='customers',kind='database',label='Bearer credential',evidence='output')]),('artifact_refs',[dict(id='report',version='/private/report')])]:
            bad=copy.deepcopy(e);bad['data']['connection'][field]=value
            self.assertFalse(central.valid_event(bad,self.project))
        legacy=copy.deepcopy(e);legacy.update(schema_version=1,adapter_version='1',data={})
        self.assertTrue(central.valid_event(legacy,self.project))
        legacy['data']=e['data'];self.assertFalse(central.valid_event(legacy,self.project))

if __name__ == '__main__':
    unittest.main(verbosity=2)
