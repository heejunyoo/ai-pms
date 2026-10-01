#!/usr/bin/env python3
"""Runnable synthetic HTTP and durable receiver counterexamples."""
import copy
import http.client
import os
from pathlib import Path
import socket
import tempfile
import threading
import uuid
from unittest.mock import patch

import common as c
import receiver as r


def event(project, event_id=None):
    return {'schema_version': 1, 'adapter_version': '1', 'event_id': event_id or str(uuid.uuid4()),
            'observed_at': c.now(), 'occurred_at': None, 'source': 'codex', 'native_event': 'SessionStart',
            'kind': 'session.start', 'authority': 'observed', 'project_id': project,
            'tool_name': None, 'links': dict.fromkeys(c.central.LINKS), 'data': {}, 'missing_fields': [],
            **dict.fromkeys(c.central.IDS)}


def batch(project, events=None):
    return {'protocol_version': 1, 'batch_id': str(uuid.uuid4()), 'project_id': project, 'events': events or []}


def rejected(call, code=None):
    try:
        call()
    except c.TransportError as error:
        assert code is None or error.code == code, error.code
        return
    raise AssertionError('expected rejection')


def main():
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory).resolve()
        base.chmod(0o700)
        project = str(uuid.uuid4())
        reg = base / 'registry.json'
        environments = [{'actor_id': 'actor-' + str(n), 'environment_id': 'env-' + str(n),
                         'token_sha256': c.digest(('temporary-' + str(n)).encode()),
                         'projects': [{'project_id': project, 'label': '합성 ' + str(n)}]} for n in (1, 2)]
        c.write_private(reg, c.encode({'version': 1, 'environments': environments}))
        root, store = base / 'receiver', base / 'store'
        sample = event(project)
        request = batch(project, [sample]); raw = c.encode(request)
        server = r.make_server(reg, root)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()

        def request_http(payload=raw, token='temporary-1', route='/v1/events', method='POST'):
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
            connection.request(method, route, payload, {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
            response = connection.getresponse()
            result = (response.status, c.strict_json(response.read()))
            connection.close()
            return result

        try:
            assert request_http(token='forged')[0] == 401
            assert request_http(route='/')[0] == 404
            assert request_http(method='GET')[0] == 405
            assert request_http(method='OPTIONS') == (501, {'error': 'invalid_http'})
            c.write_private(reg, b'{')
            assert request_http() == (503, {'error': 'invalid_registry'})
            c.write_private(reg, c.encode({'version': 1, 'environments': environments}))
            forged = dict(request, actor_id='actor-2')
            assert request_http(c.encode(forged))[0] == 400
            assert request_http(c.encode(dict(request, project_id=str(uuid.uuid4()), events=[])))[0] == 403
            malformed = copy.deepcopy(request); malformed['events'][0]['tool_name'] = []
            assert request_http(c.encode(malformed))[0] == 400
            assert request_http(b'{"protocol_version":1,"protocol_version":1}')[0] == 400
            assert request_http(b'{"number":1e400}')[0] == 400
            ack_status, ack = request_http(); assert ack_status == 200
            c.validate_ack(ack, request, raw, 'actor-1', 'env-1')
            assert request_http()[1] == ack
            assert request_http(raw + b' ')[0] == 409
            assert request_http(token='temporary-2')[0] == 200
            assert len(list((root / 'inbox').iterdir())) == 2
            # Duplicate Content-Length and transfer encoding are rejected over a raw socket.
            for headers in ('Content-Length: 0\r\nContent-Length: 0', 'Content-Length: 0\r\nTransfer-Encoding: chunked'):
                with socket.create_connection(('127.0.0.1', server.server_port), timeout=3) as connection:
                    connection.sendall(('POST /v1/events HTTP/1.1\r\nHost: localhost\r\n' + headers + '\r\nContent-Type: application/json\r\n\r\n').encode())
                    assert b' 400 ' in connection.recv(4096)
            revoked = copy.deepcopy(environments); revoked.pop(0)
            c.write_private(reg, c.encode({'version': 1, 'environments': revoked}))
            assert request_http()[0] == 401
            state = r.aggregate(reg, root, store)
            assert sorted(b['state'] for b in state['batches']) == ['aggregated', 'failed']
            assert next(b for b in state['batches'] if b['state'] == 'failed')['reason_code'] == 'registration_changed'
            c.write_private(reg, c.encode({'version': 1, 'environments': environments}))
        finally:
            server.shutdown(); server.server_close(); thread.join()

        state = r.aggregate(reg, root, store)
        assert all(b['state'] == 'aggregated' for b in state['batches'])
        data = c.central.load_store(store)
        assert len(data['sources']) == 2 and all(len(s['events']) == 1 for s in data['sources'].values())
        with patch.object(c, 'read_private', wraps=c.read_private) as bounded:
            r.sync_file(store / 'central.json', c.central.MAX_STORE)
            bounded.assert_called_once_with(store / 'central.json', c.central.MAX_STORE)
        original = {p.name: p.read_bytes() for p in (root / 'inbox').iterdir()}
        changed = copy.deepcopy(sample); changed['session_id'] = 'different'
        conflict = batch(project, [changed]); r.receive(c.encode(conflict), 'temporary-1', reg, root)
        state = r.aggregate(reg, root, store)
        assert next(b for b in state['batches'] if b['batch_id'] == conflict['batch_id'])['reason_code'] == 'event_conflict'
        assert all((root / 'inbox' / name).read_bytes() == contents for name, contents in original.items())
        state = r.aggregate(reg, root, store)
        assert sum(len(s['events']) for s in c.central.load_store(store)['sources'].values()) == 2
        heartbeat = batch(project)
        r.receive(c.encode(heartbeat), 'temporary-2', reg, root)
        state = r.aggregate(reg, root, store)
        assert next(b for b in state['batches'] if b['batch_id'] == heartbeat['batch_id'])['event_count'] == 0

        # Failure before marker persistence forbids both inbox and ACK.
        failing = base / 'failing'
        with patch.object(r, 'marker', side_effect=c.TransportError('storage_failed', 503)):
            rejected(lambda: r.receive(raw, 'temporary-1', reg, failing), 'storage_failed')
        assert not (failing / 'inbox').exists()
        # New directory entries get parent durability before an inbox file can ACK.
        barriers = []
        with patch.object(c, '_fsync_dir', side_effect=lambda p: barriers.append(Path(p))):
            c.private_dir(base / 'new-parent' / 'new-child')
        assert barriers == [base, base / 'new-parent']
        # Inbox directory barrier failure leaves an immutable file, but no ACK;
        # replay must recheck that barrier, and later retry succeeds unchanged.
        durable = base / 'durable'
        original_sync = c._fsync_dir
        def fail_inbox(path):
            if Path(path) == durable / 'inbox':
                raise OSError('synthetic')
            original_sync(path)
        with patch.object(c, '_fsync_dir', side_effect=fail_inbox):
            rejected(lambda: r.receive(raw, 'temporary-1', reg, durable), 'storage_failed')
            assert len(list((durable / 'inbox').iterdir())) == 1
            rejected(lambda: r.receive(raw, 'temporary-1', reg, durable), 'storage_failed')
        recovered = r.receive(raw, 'temporary-1', reg, durable)
        assert recovered['payload_sha256'] == c.digest(raw)
        # Metadata failure after durable inbox is acknowledged, never presented healthy.
        with patch.object(r, 'save_state', side_effect=c.TransportError('metadata_failed', 503)):
            ack = r.receive(c.encode(batch(project)), 'temporary-1', reg, durable)
            assert ack['status'] == 'durable_inbox' and (durable / 'delivery-state.error').exists()
            rejected(lambda: r.aggregate(reg, durable, base / 'durable-store'), 'metadata_failed')
        r.aggregate(reg, durable, base / 'durable-store')
        assert not (durable / 'delivery-state.error').exists()
        # Central failures live in independent metadata; partial imports cannot pass.
        with patch.object(c.central, 'import_sources', side_effect=OSError('synthetic')):
            state = r.aggregate(reg, durable, base / 'bad-store')
        assert all(b['reason_code'] == 'import_failed' for b in state['batches'])
        with patch.object(c.central, 'import_sources', return_value=None):
            state = r.aggregate(reg, durable, base / 'missing-store')
        assert all(b['state'] == 'failed' for b in state['batches'])
        corrupted = c.central.load_store(store)
        for source in corrupted['sources'].values():
            source['events'] = []
        corrupt_store = base / 'corrupt-store'
        c.write_private(corrupt_store / 'central.json', c.encode(corrupted))
        state = r.aggregate(reg, root, corrupt_store)
        assert all(b['state'] == 'failed' and b['reason_code'] == 'import_failed'
                   for b in state['batches'])
        assert c.strict_json(c.read_private(corrupt_store / 'central.json', c.central.MAX_STORE)) == corrupted
        with patch.object(c, 'MAX_QUEUE', 1):
            rejected(lambda: r.receive(c.encode(batch(project)), 'temporary-1', reg, base / 'capacity'), 'capacity')
        c.write_private(durable / 'inbox' / ('a' * 64 + '.json'), b'{}')
        rejected(lambda: r.aggregate(reg, durable, base / 'durable-store'), 'inbox_invalid')
        assert (durable / 'delivery-state.error').exists()
        for invalid in (b'{"x":NaN}', b'{"x":1e400}', b'[' * 34 + b'0' + b']' * 34):
            rejected(lambda: c.strict_json(invalid), 'invalid_json')
        assert all(p.stat().st_mode & 0o077 == 0 for p in (root / 'inbox').iterdir())
    print('receiver: synthetic HTTP auth, durable replay, metadata failures, context isolation and conflicts passed')


if __name__ == '__main__':
    main()
