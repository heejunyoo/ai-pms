#!/usr/bin/env python3
"""Full local synthetic pilot: setup → seeded admission → watchers → authenticated reads."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

import demo_setup
import live_service
import live_sender

HERE = Path(__file__).resolve().parent
common = live_service.common
opener = build_opener(ProxyHandler({}))

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp).resolve() / 'pilot'
    count = demo_setup.setup(root)
    registry = json.loads((root / 'registry.json').read_text())
    store = live_service.LiveStore(root / 'central', registry, evidence_mode='synthetic')
    server = live_service.make_server(store, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = 'http://127.0.0.1:' + str(server.server_address[1])
        demo_setup.write(root / 'demo.json', dict(version=1, url=url, synthetic=True))
        configs = []
        for path in sorted(root.glob('*/sender.json')):
            config = json.loads(path.read_text());config['url'] = url
            demo_setup.write(path, config);configs.append(config)
        token = (root / 'manager.credential').read_text()
        def query(cursor=0):
            request = Request(url + '/api/changes?after=' + str(cursor), headers={'Authorization': 'Bearer ' + token})
            with opener.open(request, timeout=10) as response:
                return common.strict_json(response.read(common.MAX_QUEUE), common.MAX_QUEUE)
        try:
            opener.open(url + '/api/changes?after=0', timeout=5)
            raise AssertionError('anonymous data read')
        except HTTPError as error:
            assert error.code == 401
        with opener.open(url, timeout=5) as response:
            shell = response.read().decode()
            assert response.status == 200 and 'data-live="true"' in shell and 'Alice' not in shell
        demo_setup.seed(root)
        writers = [live_sender.Sender(config) for config in configs]
        for writer in writers:
            writer.tick()
            assert not writer.read()['queue'], writer.read()['errors']
        assert len(writers) == count >= 2
        first = query()
        assert first['reset'] and first['operations']['sessions']
        assert {p['id'] for p in first['project_updates']} == {p['id'] for p in json.loads((HERE / 'sample/catalog.json').read_text())['projects']}
        assert all(s['evidence_mode'] == ('synthetic' if s['event_count'] else 'declared') for p in first['project_updates'] for s in p['sources'])
        initial_count = sum(len(s['events']) for s in store.read()['store']['sources'].values())
        for writer in writers:
            live_sender.Sender(writer.config).tick()
        assert sum(len(s['events']) for s in store.read()['store']['sources'].values()) == initial_count

        writer = next(w for w in writers if w.config['actor_id'] == 'Alice' and w.config['environment_id'] == 'laptop')
        logger = HERE.parents[1] / 'kit/activity/logger.py'
        if not logger.is_file(): logger = Path.home() / '.claude/harness/activity/logger.py'
        native_uuid = writer.config['project_ids'][0]
        payload = dict(hook_event_name='SessionStart', session_id='synthetic-cli-session')
        observed = time.monotonic()
        process = subprocess.run([sys.executable, str(logger), 'hook', '--source', 'codex', '--project-id', native_uuid, '--log-dir', writer.config['logdir']], input=json.dumps(payload), text=True, capture_output=True)
        assert process.returncode == 0 and not process.stderr
        writer.tick()
        updated = query(first['cursor'])
        session = next(s for s in updated['operations']['sessions'] if s['session_id'] == 'synthetic-cli-session')
        assert session['actor_id'] == 'Alice' and session['completion'] == 'unknown'
        assert session['lifecycle'] == 'started' and session['event_ids']
        elapsed = time.monotonic() - observed
        assert elapsed < 5, 'synthetic local application latency target'
        health = next(c for c in updated['operations']['capture'] if c['last_event_id'] in session['event_ids'])
        assert health['status'] == 'observed' and health['freshness'] == 'recent'
        common.write_private(Path(writer.config['logdir']) / 'capture-health.json', b'{broken')
        writer.tick()
        changed = query(updated['cursor'])
        assert any(c['actor_id'] == 'Alice' and c['environment_id'] == 'laptop' and c['status'] in ('unknown', 'degraded') for c in changed['operations']['capture'])

        catalog_path = Path(writer.config['catalog'])
        catalog = json.loads(catalog_path.read_text())
        catalog['projects'][0]['management']['work']['tasks'][0]['done_when'].append('추가된 합성 인수 조건')
        common.write_private(catalog_path, common.encode(catalog))
        writer.tick()
        change = query(changed['cursor'])
        assert catalog['projects'][0]['id'] in {p['id'] for p in change['project_updates']}
        assert not writer.read()['queue']
        before = query()
        recovered = live_service.LiveStore(root / 'central', registry, evidence_mode='synthetic')
        assert recovered.read()['cursor'] == before['cursor']
        assert recovered.read()['operations']['sessions'] == store.read()['operations']['sessions']
        print(f'Synthetic full pilot PASS: {count} writers, private setup/admission, event and management watchers, auth, restart/dedup, capture failure, local update {elapsed:.2f}s; real provider/remote/browser UNVERIFIED')
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
