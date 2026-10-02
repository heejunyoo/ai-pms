#!/usr/bin/env python3
"""Opt-in synthetic local pilot setup. Never installs provider hooks or exports keys."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import sys
import urllib.request
import uuid

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('redirect refused')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'ai-pms-transport'))
import common


def write(path, value):
    common.write_private(path, common.encode(value))


def setup(directory, port=8765):
    directory = Path(directory).absolute()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('choose an empty directory')
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('invalid port')
    common.private_dir(directory)
    catalog = json.loads((HERE / 'sample/catalog.json').read_text())
    operations = json.loads((HERE / 'sample/operations.json').read_text())
    store = json.loads((HERE / 'sample/central.json').read_text())
    admitted = {}
    for p in catalog['projects']:
        for r in p['source_refs']:
            admitted.setdefault((r['actor_id'], r['environment_id']), set()).add(r['project_id'])
    manager = secrets.token_urlsafe(32)
    common.write_private(directory / 'manager.credential', manager.encode())
    registry = {'manager': {'actor_id': 'Alice', 'token_sha256': hashlib.sha256(manager.encode()).hexdigest()}, 'writers': []}
    url = f'http://127.0.0.1:{port}'
    for (actor, environment), project_ids in sorted(admitted.items()):
        writer = directory / f'{actor}-{environment}'
        common.private_dir(writer)
        credential = secrets.token_urlsafe(32)
        common.write_private(writer / 'writer.credential', credential.encode())
        registry['writers'].append(dict(actor_id=actor, environment_id=environment, project_ids=sorted(project_ids), token_sha256=hashlib.sha256(credential.encode()).hexdigest()))
        selected = [p for p in catalog['projects'] if any(r['actor_id'] == actor and r['environment_id'] == environment for r in p['source_refs'])]
        write(writer / 'catalog.json', dict(version=3, projects=selected))
        own = [s for s in operations['sessions'] if s['actor_id'] == actor and s['environment_id'] == environment]
        ids = {s['id'] for s in own}
        write(writer / 'operations.json', dict(version=1, sessions=own, north_stars=[], contributions=[c for c in operations['contributions'] if c['session_record_id'] in ids and c['status'] == 'proposed'], capture=[]))
        common.private_dir(writer / 'logs')
        rows = {}
        for source in store['sources'].values():
            if source['actor_id'] == actor and source['environment_id'] == environment:
                for r in source['events'].values():
                    e = r['event']
                    rows.setdefault(e['observed_at'][:10], []).append(e)
        for day, events in rows.items():
            common.write_private(writer / 'logs' / (day + '.jsonl'), b''.join(common.encode(e) + b'\n' for e in sorted(events, key=lambda e: (e['observed_at'], e['event_id']))))
        write(writer / 'sender.json', dict(version=1, url=url, actor_id=actor, environment_id=environment, project_ids=sorted(project_ids), token_file=str(writer / 'writer.credential'), logdir=str(writer / 'logs'), catalog=str(writer / 'catalog.json'), operations=str(writer / 'operations.json'), outbox=str(writer / 'outbox'), loopback_test=True, base_revisions={'project:' + p['id']: 1 for p in selected}, base_hashes={'project:' + p['id']: common.digest(common.encode(p)) for p in selected}))
    write(directory / 'registry.json', registry)
    write(directory / 'demo.json', {'version': 1, 'url': url, 'synthetic': True})
    common.private_dir(directory / 'central')
    return len(admitted)


def seed(directory):
    directory = Path(directory)
    settings = common.strict_json(common.read_private(directory / 'demo.json', 1024))
    url = settings['url']
    import re
    if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]{1,5}', url):
        raise ValueError('local synthetic pilot only')
    credential = common.read_private(directory / 'manager.credential', 256).decode()
    catalog = json.loads((HERE / 'sample/catalog.json').read_text())
    operations = json.loads((HERE / 'sample/operations.json').read_text())
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    for kind, payloads in [('project', catalog['projects']), ('north_star', operations['north_stars'])]:
        for payload in payloads:
            envelope = dict(version=1, event_id=str(uuid.uuid4()), kind=kind, base_revision=0, payload=payload)
            request = urllib.request.Request(url + '/api/records', common.encode(envelope), {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + credential}, method='POST')
            with opener.open(request, timeout=10) as response:
                ack = common.strict_json(response.read(common.MAX_BODY + 1))
                if response.status != 200 or set(ack) != {'event_id', 'cursor', 'entity_revision', 'status'} or ack['event_id'] != envelope['event_id'] or ack['status'] != 'applied' or type(ack['entity_revision']) is not int or ack['entity_revision'] != 1 or type(ack['cursor']) is not int or ack['cursor'] < 1:
                    raise ValueError('unexpected seed revision')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--seed', action='store_true')
    args = parser.parse_args()
    try:
        if args.seed:
            seed(args.directory)
            print('Synthetic projects and north stars seeded. Run each sender; real app hooks remain unverified.')
        else:
            count = setup(args.directory, args.port)
            print(f'Synthetic pilot prepared: {count} writer environments. Credentials remain in private files; no hooks installed.')
        return 0
    except Exception:
        print('demo setup failed: check empty private directory, service and configuration', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
