#!/usr/bin/env python3
"""Authenticated durable inbox for the approved synthetic loopback pilot."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from pathlib import Path
import re
import signal
import socket
import sys

import common as c


def registry(path):
    try:
        doc = c.strict_json(c.read_private(path, c.MAX_BODY))
        if not isinstance(doc, dict) or set(doc) != {'version', 'environments'} or type(doc['version']) is not int or doc['version'] != 1:
            raise ValueError()
        if not isinstance(doc['environments'], list) or len(doc['environments']) > 100:
            raise ValueError()
        contexts, tokens, total = set(), set(), 0
        for env in doc['environments']:
            if not isinstance(env, dict) or set(env) != {'actor_id', 'environment_id', 'token_sha256', 'projects'}:
                raise ValueError()
            identity = (env['actor_id'], env['environment_id'])
            if not all(c.central.identifier(v) for v in identity) or identity in contexts:
                raise ValueError()
            token = env['token_sha256']
            if not isinstance(token, str) or not re.fullmatch('[a-f0-9]{64}', token) or token in tokens:
                raise ValueError()
            contexts.add(identity); tokens.add(token)
            if not isinstance(env['projects'], list):
                raise ValueError()
            projects = set()
            for project in env['projects']:
                if not isinstance(project, dict) or set(project) != {'project_id', 'label'}:
                    raise ValueError()
                if not c.central.uid(project['project_id']) or project['project_id'] in projects or not c.central.safe_text(project['label'], 80) or not project['label'].strip():
                    raise ValueError()
                projects.add(project['project_id']); total += 1
            if total > 100:
                raise ValueError()
        return doc['environments']
    except (c.TransportError, ValueError, TypeError, KeyError) as error:
        raise c.TransportError('invalid_registry', 503) from error


def registered(environments):
    return [{'actor_id': e['actor_id'], 'environment_id': e['environment_id'], **p}
            for e in environments for p in e['projects']]


def inbox_name(context, batch_id):
    return c.digest(c.encode([c.central.source_key(context), batch_id])) + '.json'


def sync_file(path, limit=c.MAX_STATE):
    # Replay must repeat both barriers even after a previous rename/fsync failure.
    c.read_private(path, limit)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    c._fsync_dir(Path(path).parent)


def marker(root):
    c.write_private(root / 'delivery-state.error', b'delivery_state_unknown\n')


def save_state(root, state):
    raw = c.encode(state)
    if len(raw) > c.MAX_STATE:
        raise c.TransportError('metadata_failed', 503)
    c.write_private(root / 'delivery-state.json', raw)


def clear_marker(root):
    try:
        (root / 'delivery-state.error').unlink()
        c._fsync_dir(root)
    except OSError as error:
        # A failed removal barrier must not leave an apparently healthy snapshot.
        marker(root)
        raise c.TransportError('metadata_failed', 503) from error


def load_inboxes(root):
    result = []
    directory = root / 'inbox'
    c.private_dir(directory)
    for path in sorted(directory.iterdir()):
        try:
            if not re.fullmatch('[a-f0-9]{64}\\.json', path.name):
                raise ValueError()
            item = c.strict_json(c.read_private(path, c.MAX_STATE), c.MAX_STATE)
            if not isinstance(item, dict) or set(item) != {'raw', 'batch', 'context', 'receipt'} or not isinstance(item['raw'], str):
                raise ValueError()
            raw = item['raw'].encode('utf-8')
            batch = c.validate_batch(raw)
            context = item['context']
            if not isinstance(context, dict) or set(context) != {'actor_id', 'environment_id', 'project_id', 'label'}:
                raise ValueError()
            if not all(c.central.identifier(context[k]) for k in ('actor_id', 'environment_id')) or context['project_id'] != batch['project_id'] or not c.central.safe_text(context['label'], 80) or not context['label'].strip():
                raise ValueError()
            if item['batch'] != batch or path.name != inbox_name(context, batch['batch_id']):
                raise ValueError()
            c.validate_ack(item['receipt'], batch, raw, context['actor_id'], context['environment_id'])
            result.append(item)
        except (c.TransportError, ValueError, TypeError, KeyError, UnicodeError) as error:
            raise c.TransportError('inbox_invalid', 503) from error
    return sorted(result, key=lambda i: (c.central.timestamp(i['receipt']['received_at']), inbox_name(i['context'], i['batch']['batch_id'])))


def snapshot(environments, items):
    return {'version': 1, 'registered_contexts': registered(environments), 'batches': [
        {'context_key': c.central.source_key(i['context']), 'batch_id': i['batch']['batch_id'],
         'payload_sha256': i['receipt']['payload_sha256'], 'received_at': i['receipt']['received_at'],
         'event_count': len(i['batch']['events']), 'state': 'queued', 'reason_code': 'none', 'updated_at': c.now()}
        for i in items]}


def receive(raw, bearer, registry_path, root):
    root = Path(root)
    with c.locked(root, 'transport.lock'):
        environments = registry(registry_path)
        if not isinstance(bearer, str) or not bearer or len(bearer) > 4096:
            raise c.TransportError('unauthorized', 401)
        token = c.digest(bearer.encode('utf-8'))
        env = next((e for e in environments if hmac.compare_digest(token, e['token_sha256'])), None)
        if env is None:
            raise c.TransportError('unauthorized', 401)
        batch = c.validate_batch(raw)
        project = next((p for p in env['projects'] if p['project_id'] == batch['project_id']), None)
        if project is None:
            raise c.TransportError('project_forbidden', 403)
        context = {'actor_id': env['actor_id'], 'environment_id': env['environment_id'], **project}
        marker(root)
        items = load_inboxes(root)
        path = root / 'inbox' / inbox_name(context, batch['batch_id'])
        previous = next((i for i in items if inbox_name(i['context'], i['batch']['batch_id']) == path.name), None)
        if previous:
            if previous['raw'].encode('utf-8') != raw:
                raise c.TransportError('batch_conflict', 409)
            try:
                sync_file(path)
            except (OSError, ValueError) as error:
                raise c.TransportError('storage_failed', 503) from error
            receipt = previous['receipt']
        else:
            receipt = {'protocol_version': 1, 'batch_id': batch['batch_id'], 'payload_sha256': c.digest(raw),
                       'actor_id': env['actor_id'], 'environment_id': env['environment_id'],
                       'event_ids': [e['event_id'] for e in batch['events']], 'status': 'durable_inbox', 'received_at': c.now()}
            item = {'raw': raw.decode('utf-8'), 'batch': batch, 'context': context, 'receipt': receipt}
            contents = c.encode(item)
            # Immutable writes: one temp replaces an absent destination, so projected
            # bytes include the entire new temp once; retained inbox has a finite cap.
            if sum(p.stat().st_size for p in (root / 'inbox').iterdir()) + len(contents) > c.MAX_QUEUE:
                raise c.TransportError('capacity', 429)
            c.write_private(path, contents)
            items.append(item)
        try:
            save_state(root, snapshot(environments, items))
            clear_marker(root)
        except (c.TransportError, OSError):
            pass  # Durable inbox remains sufficient for ACK; marker stays visible.
        return receipt


def aggregate(registry_path, root, store):
    root, store = Path(root), Path(store)
    with c.locked(root, 'transport.lock'):
        marker(root)
        environments = registry(registry_path)
        items = load_inboxes(root)
        state = snapshot(environments, items)
        save_state(root, state)
        contexts = {c.central.source_key(v): v for v in state['registered_contexts']}
        c.private_dir(root / 'mirrors')
        for item, status in zip(items, state['batches']):
            context, batch = item['context'], item['batch']
            if contexts.get(status['context_key']) != context:
                status.update(state='failed', reason_code='registration_changed')
            else:
                try:
                    mirror = 'mirrors/' + inbox_name(context, batch['batch_id']).replace('.json', '.jsonl')
                    payload = b''.join(c.encode(event) + b'\n' for event in batch['events'])
                    c.write_private(root / mirror, payload)
                    source = {**context, 'evidence_mode': 'synthetic', 'files': [mirror]}
                    manifest = root / 'aggregate-manifest.json'
                    c.write_private(manifest, c.encode({'sources': [source]}))
                    c.private_dir(store)
                    previous = c.central.load_store(store)['sources'].get(status['context_key'])
                    if previous is not None and (not isinstance(previous, dict) or not isinstance(previous.get('events'), dict)):
                        raise ValueError('invalid storage')
                    c.central.import_sources(manifest, store)
                    sync_file(store / 'central.json', c.central.MAX_STORE)
                    stored = c.central.load_store(store)['sources'].get(status['context_key'])
                    if not stored or any(stored.get(k) != context[k] for k in context):
                        raise ValueError()
                    missing, conflict = False, False
                    for event in batch['events']:
                        record = stored['events'].get(event['event_id'])
                        if record is None:
                            missing = True
                        elif c.central.canonical(record['event']) != c.central.canonical(event):
                            conflict = True
                    status.update(state='conflict' if conflict else 'failed' if missing else 'aggregated',
                                  reason_code='event_conflict' if conflict else 'import_failed' if missing else 'none')
                except (c.TransportError, OSError, ValueError, TypeError, KeyError, AttributeError):
                    status.update(state='failed', reason_code='import_failed')
            status['updated_at'] = c.now()
            save_state(root, state)
        clear_marker(root)
        return state


def make_server(registry_path, root, host='127.0.0.1', port=0):
    if host not in ('127.0.0.1', '::1') or type(port) is not int or not 0 <= port <= 65535:
        raise c.TransportError('loopback_required', 400)
    registry(registry_path)
    c.private_dir(root)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *args):
            pass

        def send_error(self, code, message=None, explain=None):
            self.response(code, {'error': 'invalid_http'})

        def response(self, status, value):
            raw = c.encode(value)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(raw)
            self.close_connection = True

        def do_GET(self):
            self.response(405 if self.path == '/v1/events' else 404, {'error': 'method_not_allowed' if self.path == '/v1/events' else 'not_found'})

        do_HEAD = do_GET
        do_PUT = do_GET
        do_DELETE = do_GET

        def do_POST(self):
            try:
                if self.path != '/v1/events':
                    raise c.TransportError('not_found', 404)
                lengths = self.headers.get_all('Content-Length', [])
                if self.headers.get_all('Transfer-Encoding') or len(lengths) != 1 or not re.fullmatch('[0-9]{1,10}', lengths[0]):
                    raise c.TransportError('invalid_headers', 400)
                size = int(lengths[0])
                if size > c.MAX_BODY:
                    raise c.TransportError('body_too_large', 413)
                if self.headers.get_all('Content-Type') != ['application/json']:
                    raise c.TransportError('invalid_headers', 400)
                auth = self.headers.get_all('Authorization', [])
                if len(auth) != 1 or not auth[0].startswith('Bearer ') or any(ord(v) < 33 or ord(v) > 126 for v in auth[0][7:]):
                    raise c.TransportError('unauthorized', 401)
                raw = self.rfile.read(size)
                if len(raw) != size:
                    raise c.TransportError('invalid_body', 400)
                self.response(200, receive(raw, auth[0][7:], registry_path, root))
            except c.TransportError as error:
                self.response(error.status, {'error': error.code})
            except (OSError, ValueError, TypeError, UnicodeError):
                self.response(503, {'error': 'storage_failed'})

    class Server(HTTPServer):
        address_family = socket.AF_INET6 if host == '::1' else socket.AF_INET

    return Server((host, port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    serve = commands.add_parser('serve')
    serve.add_argument('--host', default='127.0.0.1')
    serve.add_argument('--port', type=int, default=0)
    serve.add_argument('--loopback-test', action='store_true', required=True)
    agg = commands.add_parser('aggregate')
    agg.add_argument('--store', type=Path, required=True)
    for command in (serve, agg):
        command.add_argument('--registry', type=Path, required=True)
        command.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'aggregate':
            state = aggregate(args.registry, args.root, args.store)
            print('batches=' + str(len(state['batches'])))
            return 1 if any(b['state'] in ('failed', 'conflict') for b in state['batches']) else 0
        with make_server(args.registry, args.root, args.host, args.port) as server:
            signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
            print(server.server_port, flush=True)
            server.serve_forever()
        return 0
    except KeyboardInterrupt:
        return 0
    except (c.TransportError, OSError, ValueError):
        print('receiver: operation_failed', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
