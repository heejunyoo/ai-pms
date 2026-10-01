#!/usr/bin/env python3
"""Bounded durable sender for the explicitly approved synthetic loopback pilot."""
import argparse
import datetime as dt
import email.utils
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import common as c


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def load_config(path):
    value = c.strict_json(c.read_private(path, c.MAX_STATE), c.MAX_STATE)
    fields = {'version', 'actor_id', 'environment_id', 'project_id', 'log_dir', 'outbox', 'endpoint', 'credential_file'}
    if (not isinstance(value, dict) or set(value) != fields or type(value['version']) is not int or
            value['version'] != 1 or not c.central.identifier(value['actor_id']) or
            not c.central.identifier(value['environment_id']) or not c.central.uid(value['project_id']) or
            any(not isinstance(value[k], str) or not value[k] for k in fields - {'version'})):
        raise c.TransportError('invalid_config', 400)
    try:
        url = urllib.parse.urlsplit(value['endpoint'])
        if (url.scheme != 'http' or url.hostname not in ('127.0.0.1', '::1') or url.username is not None or
                url.password is not None or url.path != '/v1/events' or url.query or url.fragment or
                url.port is None or not 1 <= url.port <= 65535 or
                url.netloc != (('[' + url.hostname + ']') if url.hostname == '::1' else url.hostname) + ':' + str(url.port)):
            raise ValueError()
    except ValueError as error:
        raise c.TransportError('invalid_endpoint', 400) from error
    token = c.read_private(value['credential_file'], 4096).decode('ascii').strip()
    if not re.fullmatch(r'[A-Za-z0-9._~-]{1,4096}', token):
        raise c.TransportError('invalid_credential', 400)
    return value, token


def binding(config):
    return {k: config[k] for k in ('actor_id', 'environment_id', 'project_id')} | {'endpoint_sha256': c.digest(config['endpoint'].encode())}


def save_state(root, state):
    raw = c.encode(state)
    if len(raw) > c.MAX_STATE:
        raise c.TransportError('state_limit', 503)
    c.write_private(root / 'sender-state.json', raw)


def load_state(root, config):
    path = root / 'sender-state.json'
    if not path.exists() and not path.is_symlink():
        # Persist identity before the first immutable batch: recovery cannot rebind it.
        if any((root / 'batches').iterdir()):
            raise c.TransportError('state_missing', 503)
        state = {'version': 1, 'binding': binding(config), 'blocked': False, 'batches': {}}
        save_state(root, state)
        return state
    state = c.strict_json(c.read_private(path, c.MAX_STATE), c.MAX_STATE)
    if (not isinstance(state, dict) or set(state) != {'version', 'binding', 'blocked', 'batches'} or
            type(state['version']) is not int or state['version'] != 1 or state['binding'] != binding(config) or
            type(state['blocked']) is not bool or not isinstance(state['batches'], dict)):
        raise c.TransportError('invalid_state', 503)
    for key, item in state['batches'].items():
        if (not c.central.uid(key) or not isinstance(item, dict) or
                set(item) != {'status', 'attempts', 'next_retry_at', 'reason_code'} or
                item['status'] not in ('queued', 'acked', 'blocked') or type(item['attempts']) is not int or item['attempts'] < 0 or
                type(item['next_retry_at']) not in (int, float) or item['next_retry_at'] < 0 or
                item['reason_code'] not in ('none', 'request_failed', 'invalid_ack', 'http_blocked', 'event_conflict')):
            raise c.TransportError('invalid_state', 503)
    return state


def queued():
    return {'status': 'queued', 'attempts': 0, 'next_retry_at': 0, 'reason_code': 'none'}


def recover(root, state, project):
    batches, identities, total = {}, {}, 0
    for path in sorted((root / 'batches').iterdir()):
        if not c.central.uid(path.stem) or path.suffix != '.json':
            raise c.TransportError('invalid_outbox', 503)
        raw = c.read_private(path, c.MAX_BODY)
        batch = c.validate_batch(raw)
        if batch['batch_id'] != path.stem or batch['project_id'] != project:
            raise c.TransportError('invalid_outbox', 503)
        total += len(raw)
        if total > c.MAX_QUEUE:
            raise c.TransportError('queue_limit', 503)
        for event in batch['events']:
            key, hashed = event['event_id'], c.digest(c.encode(event))
            if key in identities and identities[key] != hashed:
                raise c.TransportError('event_conflict', 503)
            identities[key] = hashed
        # Recheck durability after an earlier post-replace directory fsync failure.
        try:
            c._fsync_dir(path.parent)
        except OSError as error:
            raise c.TransportError('storage_failed', 503) from error
        batches[path.stem] = (batch, raw)
        state['batches'].setdefault(path.stem, queued())
    if set(state['batches']) - set(batches):
        raise c.TransportError('invalid_outbox', 503)
    inflight = root / 'inflight.json'
    if inflight.exists() or inflight.is_symlink():
        key = c.strict_json(c.read_private(inflight, 1024))
        if not isinstance(key, str) or key not in batches:
            raise c.TransportError('invalid_state', 503)
        if state['batches'][key]['status'] != 'blocked':
            state['batches'][key]['status'] = 'queued'
            state['batches'][key]['next_retry_at'] = 0
    return batches, identities, total


def retry_after(value):
    try:
        seconds = float(value)
    except (ValueError, TypeError):
        try:
            seconds = email.utils.parsedate_to_datetime(value).timestamp() - time.time()
        except (ValueError, TypeError, OverflowError):
            return 0
    return min(30, max(0, seconds))


def transmit(config, token, batch, raw):
    request = urllib.request.Request(config['endpoint'], raw, {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}, method='POST')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=10) as response:
            ack = c.strict_json(response.read(c.MAX_BODY + 1))
            c.validate_ack(ack, batch, raw, config['actor_id'], config['environment_id'])
        return 'acked', 'none', 0
    except urllib.error.HTTPError as error:
        return ('blocked', 'http_blocked', 0) if error.code in (400, 401, 403, 409, 413) else ('queued', 'request_failed', retry_after(error.headers.get('Retry-After')))
    except c.TransportError:
        return 'queued', 'invalid_ack', 0
    except (OSError, ValueError, urllib.error.URLError):
        return 'queued', 'request_failed', 0


def run_once(config_path, heartbeat=False):
    config, token = load_config(config_path)
    root = Path(config['outbox'])
    with c.locked(root, 'sender.lock', blocking=False):
        c.private_dir(root / 'batches')
        state = load_state(root, config)
        batches, identities, total = recover(root, state, config['project_id'])
        stats = {'status': 'ok', 'queued': 0, 'acked': 0, 'blocked': 0, 'errors': [], 'backpressure': False, 'reason_code': 'none'}
        if state['blocked'] or any(s['status'] == 'blocked' for s in state['batches'].values()):
            stats.update(status='blocked', blocked=1, reason_code='event_conflict' if state['blocked'] else 'http_blocked')
            return stats
        pending = []
        def flush():
            nonlocal total, pending
            if not pending:
                return True
            batch = {'protocol_version': 1, 'batch_id': str(uuid.uuid4()), 'project_id': config['project_id'], 'events': pending}
            raw = c.encode(batch)
            # ponytail: ACKed bytes are retained; archival is needed after the 64MiB pilot ceiling.
            # Atomic write uses one extra temporary body; include it in projected cap.
            if total + 2 * len(raw) > c.MAX_QUEUE:
                stats['backpressure'] = True
                return False
            c.write_private(root / 'batches' / (batch['batch_id'] + '.json'), raw)
            state['batches'][batch['batch_id']] = queued()
            batches[batch['batch_id']] = (batch, raw)
            total += len(raw)
            pending = []
            save_state(root, state)
            return True
        log_dir = Path(config['log_dir'])
        if log_dir.is_symlink() or not log_dir.is_dir() or any(p.is_symlink() for p in log_dir.parents):
            raise c.TransportError('invalid_log_dir', 503)
        for path in sorted(log_dir.iterdir()):
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}\.jsonl', path.name):
                continue
            try:
                dt.date.fromisoformat(path.stem)
            except ValueError:
                continue
            raw = c.read_private(path, c.MAX_QUEUE)
            lines = raw.split(b'\n')[:-1]
            for line_number, line in enumerate(lines, 1):
                try:
                    event = c.strict_json(line, c.MAX_QUEUE)
                    if isinstance(event, dict) and event.get('project_id') != config['project_id']:
                        continue
                    candidate = {'protocol_version': 1, 'batch_id': str(uuid.uuid4()), 'project_id': config['project_id'], 'events': [event]}
                    c.validate_batch(c.encode(candidate))
                except c.TransportError as error:
                    if len(stats['errors']) < 100:
                        stats['errors'].append({'file_alias': c.digest(path.name.encode()), 'line': line_number, 'reason_code': error.code})
                    continue
                key, hashed = event['event_id'], c.digest(c.encode(event))
                if key in identities:
                    if identities[key] != hashed:
                        state['blocked'] = True
                        save_state(root, state)
                        stats.update(status='blocked', blocked=1, reason_code='event_conflict')
                        return stats
                    continue
                probe = dict(candidate, events=pending + [event])
                if len(pending) >= c.MAX_EVENTS or len(c.encode(probe)) > c.MAX_BODY:
                    if not flush():
                        break
                pending.append(event)
                identities[key] = hashed
            if stats['backpressure']:
                break
        if not stats['backpressure']:
            flush()
        if heartbeat and not stats['backpressure']:
            batch = {'protocol_version': 1, 'batch_id': str(uuid.uuid4()), 'project_id': config['project_id'], 'events': []}
            raw = c.encode(batch)
            if total + 2 * len(raw) > c.MAX_QUEUE:
                stats['backpressure'] = True
            else:
                c.write_private(root / 'batches' / (batch['batch_id'] + '.json'), raw)
                state['batches'][batch['batch_id']] = queued()
                batches[batch['batch_id']] = (batch, raw)
        save_state(root, state)
        for key, (batch, raw) in batches.items():
            item = state['batches'][key]
            if item['status'] != 'queued' or item['next_retry_at'] > time.time():
                continue
            # A surviving marker makes even a post-replace checkpoint failure resend.
            c.write_private(root / 'inflight.json', c.encode(key))
            status, reason, minimum = transmit(config, token, batch, raw)
            item['attempts'] += 1
            item.update(status=status, reason_code=reason, next_retry_at=0 if status != 'queued' else time.time() + min(30, max(minimum, min(30, 2 ** min(item['attempts'] - 1, 5)) + random.uniform(0, 0.25))))
            save_state(root, state)
            try:
                (root / 'inflight.json').unlink()
                c._fsync_dir(root)
            except OSError as error:
                raise c.TransportError('storage_failed', 503) from error
            if status == 'blocked':
                break
        for item in state['batches'].values():
            stats[item['status']] += 1
        if stats['blocked']:
            stats['reason_code'] = 'http_blocked'
        stats['status'] = 'blocked' if stats['blocked'] else 'backpressure' if stats['backpressure'] else 'invalid_log' if stats['errors'] else 'pending' if stats['queued'] else 'ok'
        return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--heartbeat', action='store_true')
    parser.add_argument('--loopback-test', action='store_true', required=True)
    args = parser.parse_args()
    try:
        while True:
            stats = run_once(args.config, heartbeat=args.heartbeat)
            print(c.encode(stats).decode())
            if args.once or stats['status'] in ('blocked', 'invalid_log', 'backpressure'):
                return 0 if stats['status'] == 'ok' else 1
            args.heartbeat = False
            time.sleep(2)
    except KeyboardInterrupt:
        return 0
    except (c.TransportError, OSError, ValueError, UnicodeError) as error:
        print(c.encode({'error': error.code if isinstance(error, c.TransportError) else 'sender_failed'}).decode())
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
