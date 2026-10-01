#!/usr/bin/env python3
"""Runnable semantic checks: trusted completion comes only from scoped fresh records."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import portfolio
from sample.generate import sample_data, generate, NOW


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.store, self.catalog, _, _ = sample_data()

    def model(self):
        return portfolio.build_model(self.store, self.catalog, NOW)

    def test_sample_purpose(self):
        model = self.model()
        projects = {p['id']: p for p in model['projects']}
        alice = projects['alice-recall']
        self.assertEqual(alice['owners'], ['Alice'])
        self.assertEqual(len(alice['sources']), 2)
        self.assertEqual(len(alice['sessions']), 3)
        self.assertEqual(alice['status'], 'complete')
        self.assertEqual(projects['bob-payments']['owners'], ['Bob'])
        self.assertEqual(projects['bob-payments']['status'], 'failed')
        self.assertEqual(projects['bob-payments']['phases'][1]['status'], 'complete')
        self.assertEqual(projects['carol-dashboard']['status'], 'revalidation')
        self.assertEqual(projects['dana-discovery']['status'], 'unknown')
        self.assertTrue(any(p['id'].startswith('unmapped-') for p in model['projects']))
        self.assertEqual([d['version'] for d in alice['documents'] if d['id'] == 'design'], ['v1', 'v2'])
        original = next(t for t in alice['timeline'] if t['kind'] == 'event')
        self.assertEqual(json.loads(original['detail'])['project_id'], self.catalog['projects'][0]['source_refs'][0]['project_id'])
        self.assertIn('file_sha256=', original['source_ref'])
        self.assertTrue(any(t['kind'] == 'milestone' for t in projects['carol-dashboard']['timeline']))
        self.assertEqual(model['evidence_mode'], 'synthetic')

    def test_revision_freshness(self):
        p = self.catalog['projects'][0]
        p['current_revision'] = 'v2'
        self.assertEqual(self.model()['projects'][0]['status'], 'revalidation')
        run = copy.deepcopy(p['runs'][1])
        run.update(revision='v2', exit_code=1)
        p['runs'].append(run)
        self.assertEqual(self.model()['projects'][0]['status'], 'failed')

    def test_milestone_time_order(self):
        p = self.catalog['projects'][0]
        run = copy.deepcopy(p['runs'][1])
        run['at'] = '2026-09-30T08:00:00.1Z'
        p['runs'].append(run)
        milestones = [t for t in self.model()['projects'][0]['timeline'] if t['kind'] == 'milestone']
        self.assertEqual(milestones[0]['at'], '2026-09-30T08:00:00Z')

    def test_orphan_run_session(self):
        self.catalog['projects'][0]['runs'][1]['session_id'] = 'orphan-check'
        p = self.model()['projects'][0]
        self.assertTrue(any('검사 세션 출처 미관측: orphan-check' in a for a in p['alerts']))
        self.assertFalse(any(s['id'] == 'orphan-check' for s in p['sessions']))

    def test_catalog_only_declared_evidence(self):
        model = portfolio.build_model(catalog=self.catalog, now=NOW)
        self.assertEqual(model['evidence_mode'], 'declared')
        self.assertTrue(all(s['evidence_mode'] == 'declared' for p in model['projects'] for s in p['sources']))
        self.assertEqual(model['projects'][0]['owners'], ['Alice'])
        self.assertTrue(any('관측 기록 없음' in a for a in model['projects'][0]['alerts']))
        del self.store['sources'][portfolio.central.source_key(self.catalog['projects'][0]['source_refs'][0])]
        self.assertEqual(self.model()['evidence_mode'], 'mixed')

    def test_output_limits(self):
        p = copy.deepcopy(self.catalog['projects'][3])
        p.update(source_refs=[], phases=[], current_phase=None)
        projects=[]
        for i in range(1001):
            clone = copy.deepcopy(p)
            clone['id'] = 'project-' + str(i)
            projects.append(clone)
        with self.assertRaisesRegex(ValueError, '프로젝트 한도'):
            portfolio.build_model(catalog=dict(version=1, projects=projects), now=NOW)
        p = self.catalog['projects'][0]
        p['documents'] = [dict(p['documents'][0], id='document-' + str(i), content='가' * 20000) for i in range(60)]
        with self.assertRaisesRegex(ValueError, '모델 출력 한도'):
            self.model()

    def test_changed_signature(self):
        self.catalog['projects'][0]['criteria'][0]['command'] = 'python3 checks/new.py'
        p = self.model()['projects'][0]
        self.assertEqual(p['status'], 'in_progress')
        self.assertTrue(any('signature' in alert for alert in p['alerts']))
        self.assertFalse(any(t['kind'] == 'milestone' for t in p['timeline']))

    def test_future_records(self):
        p = self.catalog['projects'][0]
        p['runs'][1]['at'] = '2026-10-02T00:00:00Z'
        result = self.model()['projects'][0]
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['runs'][1]['status'], 'unknown')
        self.assertTrue(any('미래 검사' in a for a in result['alerts']))

    def test_conflicting_equal_timestamps(self):
        p = self.catalog['projects'][0]
        conflict = copy.deepcopy(p['runs'][1])
        conflict['at'] = conflict['at'].replace('Z', '+00:00')
        conflict['exit_code'] = 1
        p['runs'].append(conflict)
        result = self.model()['projects'][0]
        self.assertEqual(result['status'], 'in_progress')
        self.assertTrue(any('충돌' in a for a in result['alerts']))

    def test_wrong_scope(self):
        p = self.catalog['projects'][0]
        p['criteria'][0].update(scope='task', target_id='task-a')
        self.assertEqual(self.model()['projects'][0]['status'], 'unknown')
        p['criteria'][0].update(scope='project', target_id='wrong-project')
        with self.assertRaises(ValueError):
            self.model()

    def test_source_identity(self):
        self.catalog['projects'][1]['source_refs'].append(copy.deepcopy(self.catalog['projects'][0]['source_refs'][0]))
        with self.assertRaises(ValueError):
            self.model()
        self.setUp()
        source = next(iter(self.store['sources'].values()))
        source['actor_id'] = 'wrong-actor'
        with self.assertRaises(ValueError):
            self.model()

    def test_empty_and_input_bounds(self):
        self.assertEqual(portfolio.build_model(now=NOW)['projects'], [])
        self.catalog['projects'][0]['goal'] = 'x' * 20001
        with self.assertRaises(ValueError):
            self.model()
        self.setUp()
        self.catalog['projects'][0]['documents'][0]['at'] = 'not-a-time'
        with self.assertRaises(ValueError):
            self.model()
        self.setUp()
        self.catalog['projects'][0]['criteria'].append(copy.deepcopy(self.catalog['projects'][0]['criteria'][0]))
        with self.assertRaises(ValueError):
            self.model()
        self.setUp()
        self.catalog['projects'][0]['documents'][0]['phase_id'] = 'missing'
        with self.assertRaises(ValueError):
            self.model()

    def test_combined_output_array_limit(self):
        p = self.catalog['projects'][0]
        p['runs'] = [copy.deepcopy(p['runs'][1]) for _ in range(10000)]
        # Individual input arrays fit; their joined timeline must still fit.
        with self.assertRaisesRegex(ValueError, '배열 한도'):
            self.model()

    def test_private_values_rejected(self):
        for value in ('/Users/example/private.txt', '/etc/config/private.conf', 'secret=abc123', 'ghp_abcdefgh12345678', 'Authorization: Bearer abcdef123456'):
            self.catalog['projects'][0]['goal'] = value
            with self.assertRaises(ValueError):
                self.model()

    def test_html_injection(self):
        self.catalog['projects'][0]['goal'] = '</script><img src=x onerror=alert(1)>'
        model = self.model()
        rendered = portfolio.render_html(model, '<html><script id="pms-data" type="application/json">{}</script></html>')
        self.assertEqual(rendered.count('</script>'), 1)
        self.assertNotIn('<img', rendered)
        payload = rendered.split('application/json">')[1].split('</script>')[0]
        self.assertEqual(json.loads(payload), model)

    def test_deterministic_generator_and_cli_error(self):
        self.assertEqual(sample_data(), sample_data())
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            generate(root)
            raw = root / 'bad.json'
            raw.write_text('{broken')
            run = subprocess.run([sys.executable, str(Path(portfolio.__file__)), '--catalog', str(raw), '--out', str(root / 'out.html')], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertNotIn(name, run.stderr)
            self.assertFalse((root / 'out.html').exists())
            raw.write_text('{"version":1,"version":1,"projects":[]}')
            with self.assertRaises(ValueError):
                portfolio.read_json(raw)


    def test_connectivity_v2_provenance_privacy_and_completion(self):
        store,catalog,_,_=sample_data(connectivity=True)
        model=portfolio.build_model(store,catalog,now=NOW)
        self.assertEqual(model['schema_version'],2)
        self.assertTrue(all('connections' in p for p in model['projects']))
        byid={p['id']:p for p in model['projects']}
        self.assertEqual(byid['alice-recall']['status'],'complete')
        self.assertEqual(byid['dana-discovery']['connections'][0]['authority'],'declared')
        self.assertEqual(byid['dana-discovery']['connections'][0]['status'],'configured')
        calls=byid['alice-recall']['connections']
        self.assertEqual(sum(c['status']=='completed' for c in calls),2)
        self.assertEqual(sum(c['status']=='completed' and c['server'] is not None for c in calls),1)
        self.assertTrue(any(c['status']=='completed' and c['server'] is None and not c['resources'] for c in calls))
        self.assertTrue(all(c['actor_id']=='Alice' for c in calls))
        self.assertEqual(byid['bob-payments']['connections'][0]['actor_id'],'Bob')
        self.assertTrue(any(c['server'] is None for c in calls))
        bad=copy.deepcopy(store)
        for source in bad['sources'].values():
            for record in source['events'].values():
                e=record['event']
                if e['schema_version']==2:
                    e['data']['connection']['server']='token=secret';break
            else:continue
            break
        with self.assertRaises(ValueError):portfolio.build_model(bad,catalog,now=NOW)
        catalog['projects'][0]['connections']=[copy.deepcopy(catalog['projects'][3]['connections'][0])]
        with self.assertRaises(ValueError):portfolio.build_model(store,catalog,now=NOW)

if __name__ == '__main__':
    unittest.main()
