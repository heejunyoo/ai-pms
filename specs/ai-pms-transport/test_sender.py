#!/usr/bin/env python3
"""Synthetic real-HTTP sender recovery and negative checks; no real credentials."""
import copy
import http.server
import importlib
import os
from pathlib import Path
import tempfile
import threading
import uuid
from unittest.mock import patch

import common as c
import receiver as r
import sender as s
from test_receiver import event, rejected


def main():
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory).resolve(); base.chmod(0o700)
        project = str(uuid.uuid4())
        reg = base / 'registry.json'
        c.write_private(reg, c.encode({'version': 1, 'environments': [{'actor_id': 'synthetic', 'environment_id': 'pilot', 'token_sha256': c.digest(b'temporary'), 'projects': [{'project_id': project, 'label': '합성'}]}]}))
        server = r.make_server(reg, base / 'receiver')
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        logs = base / 'logs'; c.private_dir(logs)
        token = base / 'token'; c.write_private(token, b'temporary')
        config = {'version': 1, 'actor_id': 'synthetic', 'environment_id': 'pilot', 'project_id': project, 'log_dir': str(logs), 'outbox': str(base / 'outbox'), 'endpoint': f'http://127.0.0.1:{server.server_port}/v1/events', 'credential_file': str(token)}
        conf = base / 'config.json'; c.write_private(conf, c.encode(config))
        sample = event(project)
        other = event(str(uuid.uuid4()))
        incomplete = event(project)
        log = logs / '2026-10-01.jsonl'
        c.write_private(log, c.encode(other) + b'\n' + c.encode(sample) + b'\n' + c.encode(incomplete))
        c.write_private(logs / 'project-index.json', b'not JSON')
        c.private_dir(logs / 'nested')
        c.write_private(logs / 'nested' / '2026-10-01.jsonl', b'not JSON')
        try:
            with patch.dict(os.environ, {'http_proxy': 'http://127.0.0.1:1', 'HTTP_PROXY': 'http://127.0.0.1:1'}):
                assert s.run_once(conf)['acked'] == 1
            batches = list((base / 'outbox' / 'batches').glob('*.json'))
            original = batches[0].read_bytes()
            assert c.validate_batch(original)['events'] == [sample]
            assert s.run_once(conf)['acked'] == 1
            assert len(list((base / 'receiver' / 'inbox').iterdir())) == 1
            assert importlib.reload(s).run_once(conf)['acked'] == 1
            c.write_private(log, log.read_bytes() + b'\n')
            assert s.run_once(conf)['acked'] == 2
            assert s.run_once(conf, heartbeat=True)['acked'] == 3
            assert s.run_once(conf)['acked'] == 3
            assert len(list((base / 'outbox' / 'batches').iterdir())) == 3
            # Invalid matching lines carry only hashed alias, line number and safe reason.
            c.write_private(log, log.read_bytes() + b'not-json\n')
            stats = s.run_once(conf)
            assert stats['status'] == 'invalid_log' and set(stats['errors'][0]) == {'file_alias', 'line', 'reason_code'}
            c.write_private(log, c.encode(sample) + b'\n' + c.encode(incomplete) + b'\n')
            # Config binding prohibits redirecting an existing context's durable outbox.
            c.write_private(conf, c.encode(dict(config, actor_id='someone-else')))
            rejected(lambda: s.run_once(conf), 'invalid_state')
            c.write_private(conf, c.encode(config))
            for endpoint in ('http://localhost:1/v1/events', 'https://127.0.0.1:1/v1/events', 'http://127.0.0.1:1/v1/events?secret=yes', 'http://u@127.0.0.1:1/v1/events'):
                c.write_private(conf, c.encode(dict(config, endpoint=endpoint)))
                rejected(lambda: s.run_once(conf), 'invalid_endpoint')
            c.write_private(conf, c.encode(config))
            # Immutable outbox before checkpoint survives a failed state write.
            recovered_event = event(project)
            c.write_private(log, log.read_bytes() + c.encode(recovered_event) + b'\n')
            with patch.object(s, 'save_state', side_effect=c.TransportError('storage_failed', 503)):
                rejected(lambda: s.run_once(conf), 'storage_failed')
            assert len(list((base / 'outbox' / 'batches').iterdir())) == 4
            assert importlib.reload(s).run_once(conf)['acked'] == 4
            assert batches[0].read_bytes() == original
            # ACK state failure forces identical retransmission after restart.
            ack_event = event(project)
            c.write_private(log, log.read_bytes() + c.encode(ack_event) + b'\n')
            original_save = s.save_state
            def fail_ack(root, state):
                if sum(x['status'] == 'acked' for x in state['batches'].values()) == 5:
                    raise c.TransportError('storage_failed', 503)
                original_save(root, state)
            with patch.object(s, 'save_state', side_effect=fail_ack):
                rejected(lambda: s.run_once(conf), 'storage_failed')
            assert len(list((base / 'receiver' / 'inbox').iterdir())) == 5
            assert importlib.reload(s).run_once(conf)['acked'] == 5
            assert len(list((base / 'receiver' / 'inbox').iterdir())) == 5
            # Conflicting same event id never transmits and survives restarts.
            changed = copy.deepcopy(sample); changed['session_id'] = 'changed'
            c.write_private(log, log.read_bytes() + c.encode(changed) + b'\n')
            assert s.run_once(conf)['status'] == 'blocked'
            with patch.object(s, 'transmit', side_effect=AssertionError('must not send')):
                assert s.run_once(conf)['status'] == 'blocked'
            assert len(list((base / 'receiver' / 'inbox').iterdir())) == 5
        finally:
            server.shutdown(); server.server_close(); thread.join()

        # Fresh outbox for offline, dropped response, wrong ACK and HTTP policies.
        c.write_private(log, c.encode(event(project)) + b'\n')
        config['outbox'] = str(base / 'retry-outbox')
        c.write_private(conf, c.encode(config))
        with patch.object(s.time, 'time', return_value=100):
            stats = s.run_once(conf)
            assert stats['queued'] == 1
            state = c.strict_json(c.read_private(Path(config['outbox']) / 'sender-state.json', c.MAX_STATE))
            assert 101 <= next(iter(state['batches'].values()))['next_retry_at'] <= 101.25
            with patch.object(s, 'transmit', side_effect=AssertionError('retry too early')):
                assert s.run_once(conf)['queued'] == 1

        class Handler(http.server.BaseHTTPRequestHandler):
            mode = 'wrong'
            bodies = []
            def log_message(self, *args):
                pass
            def do_POST(self):
                raw = self.rfile.read(int(self.headers['Content-Length']))
                self.bodies.append(raw)
                if self.mode == 'drop':
                    r.receive(raw, 'temporary', reg, base / 'receiver')
                    self.close_connection = True
                    return
                if self.mode == 'redirect':
                    self.send_response(302); self.send_header('Location', 'http://192.0.2.1/v1/events'); self.end_headers(); return
                if self.mode == '429':
                    self.send_response(429); self.send_header('Retry-After', '999'); self.end_headers(); return
                if self.mode == 'blocked':
                    self.send_response(403); self.end_headers(); return
                ack = r.receive(raw, 'temporary', reg, base / 'receiver')
                if self.mode == 'wrong':
                    ack['environment_id'] = 'wrong'
                body = c.encode(ack)
                self.send_response(200); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
        retry_server = http.server.HTTPServer(('127.0.0.1', server.server_port), Handler)
        thread = threading.Thread(target=retry_server.serve_forever, daemon=True); thread.start()
        try:
            for clock, mode, reason in ((200, 'wrong', 'invalid_ack'), (300, 'drop', 'request_failed'), (400, 'redirect', 'request_failed'), (500, '429', 'request_failed')):
                Handler.mode = mode
                with patch.object(s.time, 'time', return_value=clock):
                    assert s.run_once(conf)['queued'] == 1
                state = c.strict_json(c.read_private(Path(config['outbox']) / 'sender-state.json', c.MAX_STATE))
                item = next(iter(state['batches'].values()))
                assert item['reason_code'] == reason
                if mode == '429':
                    assert item['next_retry_at'] == 530
            assert all(raw == Handler.bodies[0] for raw in Handler.bodies)
            Handler.mode = 'ok'
            with patch.object(s.time, 'time', return_value=600):
                assert importlib.reload(s).run_once(conf)['acked'] == 1
            assert len(list((base / 'receiver' / 'inbox').iterdir())) == 6
            config['outbox'] = str(base / 'blocked-outbox'); c.write_private(conf, c.encode(config))
            Handler.mode = 'blocked'
            assert s.run_once(conf)['blocked'] == 1
            Handler.mode = 'ok'
            assert s.run_once(conf)['status'] == 'blocked'
            # Capacity is backpressure, preserves log, never sends an unpersisted batch.
            config['outbox'] = str(base / 'cap-outbox'); c.write_private(conf, c.encode(config))
            before = log.read_bytes()
            with patch.object(c, 'MAX_QUEUE', len(before) + 1):
                stats = s.run_once(conf)
                assert stats['backpressure'] and stats['acked'] == 0
            assert log.read_bytes() == before
            assert not list((Path(config['outbox']) / 'batches').iterdir())
            assert s.run_once(conf)['acked'] == 1
            # ACK checkpoint replacement may happen before its fsync fails.
            extra = event(project)
            c.write_private(log, log.read_bytes() + c.encode(extra) + b'\n')
            original_write = c.write_private
            def fail_after_ack(path, raw):
                original_write(path, raw)
                if Path(path).name == 'sender-state.json':
                    state = c.strict_json(raw, c.MAX_STATE)
                    if sum(v['status'] == 'acked' for v in state['batches'].values()) == 2:
                        raise c.TransportError('storage_failed', 503)
            with patch.object(c, 'write_private', side_effect=fail_after_ack):
                rejected(lambda: s.run_once(conf), 'storage_failed')
            count = len(Handler.bodies)
            assert s.run_once(conf)['acked'] == 2
            assert len(Handler.bodies) == count + 1
            assert Handler.bodies[-1] == Handler.bodies[-2]
            # Canonical body size, rather than raw whitespace, governs event validity.
            config['outbox'] = str(base / 'size-outbox'); c.write_private(conf, c.encode(config))
            many = [event(project) for _ in range(101)]
            for item in many:
                item.update(source='manual', authority='declared', kind='decision.recorded', native_event='decision.recorded')
                item['links'].update(phase_id='phase', baseline_version='v1', decision_id='decision')
                item['data'] = {k: '합' * 2000 for k in ('summary', 'reason', 'scope_added', 'scope_removed')}
            c.write_private(log, b'\n'.join(c.encode(item) for item in many) + b'\n')
            stats = s.run_once(conf)
            bodies = [c.read_private(p, c.MAX_BODY) for p in (Path(config['outbox']) / 'batches').iterdir()]
            assert stats['acked'] >= 2 and sum(len(c.validate_batch(b)['events']) for b in bodies) == 101
            assert all(len(b) <= c.MAX_BODY and len(c.validate_batch(b)['events']) <= 100 for b in bodies)
            assert s.run_once(conf)['acked'] == stats['acked']
            token.chmod(0o644)
            rejected(lambda: s.run_once(conf), 'storage_failed')
            token.chmod(0o600)
            with c.locked(Path(config['outbox']), 'sender.lock', blocking=False):
                rejected(lambda: s.run_once(conf), 'busy')
        finally:
            retry_server.shutdown(); retry_server.server_close(); thread.join()
        assert s.retry_after('999') == 30 and s.retry_after('invalid') == 0
        with patch.object(s.time, 'time', return_value=0):
            assert s.retry_after('Thu, 01 Jan 1970 00:00:20 GMT') == 20
    print('sender: actual HTTP mixed-project/restart/offline/wrongACK/drop/redirect/retry/blocked/cap/heartbeat/state-failure checks passed')


if __name__ == '__main__':
    main()
