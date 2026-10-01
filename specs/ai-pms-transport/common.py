#!/usr/bin/env python3
"""Shared, bounded local transport contract for the approved loopback pilot."""
from contextlib import contextmanager
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('ai_pms_central', HERE.parent / 'ai-pms-central/central.py')
central = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(central)

MAX_BODY = 1_048_576
MAX_EVENT = 65_536
MAX_EVENTS = 100
MAX_QUEUE = 64 * 1_048_576
MAX_STATE = 8 * 1_048_576


class TransportError(Exception):
    def __init__(self, code, status):
        self.code = code
        self.status = status
        super().__init__(code)


def encode(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise TransportError('invalid_json', 400) from error


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def strict_json(raw, limit=MAX_BODY):
    if not isinstance(raw, bytes) or len(raw) > limit:
        raise TransportError('body_too_large' if isinstance(raw, bytes) else 'invalid_json', 413 if isinstance(raw, bytes) else 400)

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
        stack = [(value, 1)]
        while stack:
            item, depth = stack.pop()
            if isinstance(item, float) and not math.isfinite(item):
                raise ValueError('nonfinite')
            if depth > 32:
                raise ValueError('nesting limit')
            if isinstance(item, dict):
                stack.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                stack.extend((child, depth + 1) for child in item)
        return value
    except (UnicodeError, ValueError, RecursionError) as error:
        raise TransportError('invalid_json', 400) from error


def validate_batch(raw):
    batch = strict_json(raw)
    if not isinstance(batch, dict) or set(batch) != {'protocol_version', 'batch_id', 'project_id', 'events'}:
        raise TransportError('invalid_batch', 400)
    if type(batch['protocol_version']) is not int or batch['protocol_version'] != 1 or not central.uid(batch['batch_id']) or not central.uid(batch['project_id']):
        raise TransportError('invalid_batch', 400)
    events = batch['events']
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise TransportError('invalid_batch', 400)
    seen = set()
    for event in events:
        try:
            valid = central.valid_event(event, batch['project_id']) and len(encode(event)) <= MAX_EVENT
        except (TypeError, ValueError, KeyError, TransportError):
            valid = False
        if not valid:
            raise TransportError('invalid_event', 400)
        if event['event_id'] in seen:
            raise TransportError('duplicate_event', 400)
        seen.add(event['event_id'])
    return batch


def validate_ack(value, batch, raw, actor_id, environment_id):
    fields = {'protocol_version', 'batch_id', 'payload_sha256', 'actor_id', 'environment_id',
              'event_ids', 'status', 'received_at'}
    if not isinstance(value, dict) or set(value) != fields:
        raise TransportError('invalid_ack', 400)
    if (type(value['protocol_version']) is not int or value['protocol_version'] != 1 or
            value['batch_id'] != batch['batch_id'] or value['payload_sha256'] != digest(raw) or
            value['actor_id'] != actor_id or value['environment_id'] != environment_id or
            value['event_ids'] != [event['event_id'] for event in batch['events']] or
            value['status'] != 'durable_inbox' or central.timestamp(value['received_at']) is None):
        raise TransportError('invalid_ack', 400)


def private_dir(path):
    path = Path(path)
    try:
        if any(part.is_symlink() for part in (path, *path.parents)):
            raise ValueError('symlink directory')
        missing = [part for part in (path, *path.parents) if not part.exists()]
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        if any(part.is_symlink() for part in (path, *path.parents)):
            raise ValueError('symlink directory')
        info = path.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('unsafe directory')
        path.chmod(0o700)
        # Persist each new directory entry, plus retry the immediate barrier when
        # a previous operation created it but failed before the parent fsync.
        for parent in dict.fromkeys([part.parent for part in reversed(missing)] + [path.parent]):
            _fsync_dir(parent)
    except (OSError, ValueError) as error:
        raise TransportError('storage_failed', 503) from error


def _safe_file(path):
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or info.st_mode & 0o077:
        raise ValueError('unsafe file')


def read_private(path, limit):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as source:
            info = os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or info.st_mode & 0o077:
                raise ValueError('unsafe file')
            if info.st_size > limit:
                raise ValueError('file limit')
            raw = source.read(limit + 1)
            if len(raw) > limit:
                raise ValueError('file limit')
            return raw
    except (OSError, ValueError) as error:
        raise TransportError('storage_failed', 503) from error


def _fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_private(path, raw):
    path = Path(path)
    private_dir(path.parent)
    if not isinstance(raw, bytes):
        raise TransportError('storage_failed', 503)
    name = None
    try:
        if path.exists() or path.is_symlink():
            _safe_file(path)
        fd, name = tempfile.mkstemp(prefix='.transport-', dir=path.parent)
        with os.fdopen(fd, 'wb') as output:
            os.fchmod(output.fileno(), 0o600)
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
        name = None
        _fsync_dir(path.parent)
    except (OSError, ValueError) as error:
        raise TransportError('storage_failed', 503) from error
    finally:
        if name is not None:
            try:
                os.unlink(name)
            except OSError:
                pass


@contextmanager
def locked(root, name, blocking=True):
    root = Path(root)
    private_dir(root)
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,80}', name):
        raise TransportError('storage_failed', 503)
    try:
        fd = os.open(root / name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            os.close(fd)
            raise ValueError('unsafe lock')
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'rb') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            except BlockingIOError as error:
                raise TransportError('busy', 429) from error
            yield
    except TransportError:
        raise
    except (OSError, ValueError) as error:
        raise TransportError('storage_failed', 503) from error
