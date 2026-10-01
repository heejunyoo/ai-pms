#!/usr/bin/env python3
"""Parent-owned two-context synthetic HTTP exercise; credentials are temporary only."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent
LOGGER = Path.home() / '.claude/harness/activity/logger.py'


def require(value, message):
    if not value:
        raise ValueError(message)


def exercise(output=None):
    import common
    import receiver
    import sender
    central = common.central
    with tempfile.TemporaryDirectory(prefix='pms-transport-') as directory:
        base = Path(directory).resolve()
        project = str(uuid.uuid4())
        credentials = {actor: secrets.token_urlsafe(32) for actor in ('alice', 'bob', 'carol', 'dave')}
        environments = []
        for actor, token in credentials.items():
            environments.append({'actor_id': actor, 'environment_id': actor + '-device',
                                 'token_sha256': common.digest(token.encode()),
                                 'projects': [{'project_id': project, 'label': actor + ' 합성 프로젝트'}]})
        registry = base / 'registry.json'
        common.write_private(registry, common.encode({'version': 1, 'environments': environments}))
        inbox, store = base / 'receiver', base / 'central'
        server = receiver.make_server(registry, inbox, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f'http://127.0.0.1:{server.server_address[1]}/v1/events'
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        events = {}
        configs = {}

        def post(actor, batch):
            raw = common.encode(batch)
            request = urllib.request.Request(endpoint, data=raw, headers={
                'Content-Type': 'application/json', 'Authorization': 'Bearer ' + credentials[actor]})
            with opener.open(request, timeout=10) as response:
                ack = common.strict_json(response.read(common.MAX_BODY + 1))
            common.validate_ack(ack, batch, raw, actor, actor + '-device')
            return ack

        def record(actor, kind, data, links, extra=()):
            args = [sys.executable, str(LOGGER), 'record', '--log-dir', str(base / (actor + '-logs')),
                    '--kind', kind, '--project-id', project, '--data', json.dumps(data),
                    '--links', json.dumps(links), *extra]
            subprocess.run(args, check=True, capture_output=True)

        try:
            for actor in ('alice', 'bob'):
                logs = base / (actor + '-logs')
                subprocess.run([sys.executable, str(LOGGER), 'hook', '--log-dir', str(logs),
                                '--source', 'codex' if actor == 'alice' else 'claude', '--project-id', project],
                               input=json.dumps({'hook_event_name': 'SubagentStart', 'session_id': actor + '-session',
                                                 'agent_id': 'agent-1', 'cwd': str(base)}).encode(),
                               check=True, capture_output=True)
                record(actor, 'project.baseline', {'goal': actor + '의 독립 목표', 'scope': '승인 A 로컬 전달'},
                       {'phase_id': 'phase-1', 'baseline_version': 'v1'})
                record(actor, 'artifact.recorded', {'summary': '결과물 관측'},
                       {'artifact_id': 'artifact-1', 'artifact_version': 'v1'},
                       ('--session-id', actor + '-session', '--agent-id', 'agent-1'))
                record(actor, 'check.recorded', {'summary': '로컬 검사', 'status': 'pass', 'environment': 'local'},
                       {'check_id': 'check-1', 'artifact_id': 'artifact-1', 'artifact_version': 'v1' if actor == 'alice' else 'v2'})
                record(actor, 'acceptance.recorded', {'summary': '인수 대기', 'status': 'pending', 'environment': 'local'},
                       {'artifact_id': 'artifact-1', 'artifact_version': 'v1'})
                events[actor] = [json.loads(line) for path in sorted(logs.glob('*.jsonl')) for line in path.read_text().splitlines()]
                credential = base / (actor + '-credential')
                common.write_private(credential, credentials[actor].encode())
                config = {'version': 1, 'actor_id': actor, 'environment_id': actor + '-device',
                          'project_id': project, 'log_dir': str(logs), 'outbox': str(base / (actor + '-outbox')),
                          'endpoint': endpoint, 'credential_file': str(credential)}
                config_path = base / (actor + '-config.json')
                common.write_private(config_path, common.encode(config))
                configs[actor] = config_path
                # Exercise the actual CLI boundary with explicit test-mode authorization.
                run = subprocess.run([sys.executable, str(ROOT / 'sender.py'), '--config', str(config_path),
                                      '--once', '--loopback-test'], capture_output=True, text=True)
                require(run.returncode == 0, 'sender CLI failed')
                require(credentials[actor] not in run.stdout + run.stderr and str(base) not in run.stdout + run.stderr,
                        'sender disclosed private runtime data')
            heartbeat = {'protocol_version': 1, 'batch_id': str(uuid.uuid4()), 'project_id': project, 'events': []}
            post('carol', heartbeat)
            state = receiver.aggregate(registry, inbox, store)
            require(len(state['registered_contexts']) == 4, 'registered context loss')
            persisted = central.load_store(store)
            for actor in ('alice', 'bob'):
                context = {'actor_id': actor, 'environment_id': actor + '-device', 'project_id': project}
                actor_batches = [b for b in state['batches'] if b['context_key'] == central.source_key(context)]
                require(actor_batches and all(b['state'] == 'aggregated' for b in actor_batches), 'actor aggregation state incorrect')
                stored = persisted['sources'][central.source_key(context)]['events']
                require(len(stored) == len(events[actor]), 'lost or duplicate events')
                for event in events[actor]:
                    require(central.canonical(stored[event['event_id']]['event']) == central.canonical(event), 'event body changed')
                # A restarted sender must not enqueue a new batch for acknowledged events.
                sender.run_once(configs[actor])
            heartbeats = [b for b in state['batches'] if b['batch_id'] == heartbeat['batch_id']]
            require(len(heartbeats) == 1 and heartbeats[0]['event_count'] == 0 and heartbeats[0]['state'] == 'aggregated'
                    and heartbeats[0]['payload_sha256'] == common.digest(common.encode(heartbeat))
                    and central.timestamp(heartbeats[0]['received_at'])
                    and heartbeats[0]['context_key'] == central.source_key({'actor_id': 'carol', 'environment_id': 'carol-device', 'project_id': project}),
                    'heartbeat metadata incorrectly attributed')
            require(not any(b['context_key'] == central.source_key({'actor_id': 'dave', 'environment_id': 'dave-device', 'project_id': project}) for b in state['batches']), 'unconnected context got a receipt')
            repeated = receiver.aggregate(registry, inbox, store)
            require(len(repeated['batches']) == len(state['batches']), 'duplicate batch on sender restart')
            metadata = central.load_delivery_state(inbox / 'delivery-state.json')
            projects = central.summarize(central.load_store(store), metadata)
            by_actor = {p['actor_id']: p for p in projects}
            require(len(projects) == 4, 'missing registered-only context')
            require(by_actor['carol']['last_observed'] is None and by_actor['dave']['last_observed'] is None,
                    'heartbeat fabricated activity')
            require('산출물 검증 불일치' in by_actor['bob']['issues'], 'version mismatch hidden')
            if output:
                output.mkdir(parents=True, exist_ok=True)
                central.render(central.load_store(store), output / 'dashboard.html', metadata)
                central.render({'version': 1, 'sources': {}}, output / 'empty.html')
            conflict = copy.deepcopy(next(e for e in events['alice'] if e['kind'] == 'project.baseline'))
            conflict['data']['goal'] = '충돌해서 덮어쓰면 안 되는 목표'
            conflict_batch = {'protocol_version': 1, 'batch_id': str(uuid.uuid4()), 'project_id': project, 'events': [conflict]}
            post('alice', conflict_batch)
            conflict_state = receiver.aggregate(registry, inbox, store)
            conflict_rows = [b for b in conflict_state['batches'] if b['batch_id'] == conflict_batch['batch_id']]
            require(len(conflict_rows) == 1 and conflict_rows[0]['state'] == 'conflict'
                    and conflict_rows[0]['reason_code'] == 'event_conflict'
                    and conflict_rows[0]['context_key'] == central.source_key({'actor_id': 'alice', 'environment_id': 'alice-device', 'project_id': project})
                    and conflict_rows[0]['payload_sha256'] == common.digest(common.encode(conflict_batch)), 'event conflict hidden or misattributed')
            after = central.load_store(store)
            original = next(e for e in events['alice'] if e['kind'] == 'project.baseline')
            alice_key = central.source_key({'actor_id': 'alice', 'environment_id': 'alice-device', 'project_id': project})
            require(after['sources'][alice_key]['events'][original['event_id']]['event'] == original, 'conflict overwrote original')
            if output:
                central.render(after, output / 'audit.html', central.load_delivery_state(inbox / 'delivery-state.json'))
                # Observe the real renderer CLI's fail-safe path, not a hand-edited HTML.
                broken_store = base / 'broken-central'
                common.write_private(broken_store / 'central.json',
                                     common.encode({'version': 1, 'sources': {'bad': {'events': []}}}))
                receiver.marker(inbox)
                failed_render = subprocess.run([sys.executable, str(ROOT.parent / 'ai-pms-central/central.py'),
                                                'render', '--store', str(broken_store),
                                                '--delivery-state', str(inbox / 'delivery-state.json'),
                                                '--output', str(output / 'error.html')], capture_output=True, text=True)
                require(failed_render.returncode == 0 and 'Traceback' not in failed_render.stderr,
                        'corrupt central store failed safe rendering')
            summary = {'evidence_mode': 'synthetic-loopback', 'distinct_contexts_with_events': 2,
                       'registered_contexts': 4, 'event_count': sum(map(len, events.values())),
                       'same_project_uuid_isolated': True, 'restart_no_duplicate_batches': True,
                       'heartbeat_no_activity': True, 'conflict_preserves_original': True,
                       'actual_multi_user_delivery_verified': False, 'product_complete': False}
            if output:
                common.write_private(output / 'loopback-observation.json', common.encode(summary))
                code = {name: ROOT / name for name in ('common.py', 'receiver.py', 'sender.py', 'exercise_transport.py')}
                code['central.py'] = ROOT.parent / 'ai-pms-central/central.py'
                provenance = {'scope': 'A-local-transport', 'evidence_mode': 'synthetic-loopback',
                              'code_hashes': {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in code.items()},
                              'artifact_hashes': {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                                                  for name in ('dashboard.html', 'empty.html', 'audit.html', 'error.html', 'loopback-observation.json')}}
                common.write_private(output / 'generation.json', common.encode(provenance))
                private_values = [str(base), *credentials.values(),
                                  *(common.digest(token.encode()) for token in credentials.values())]
                for name in (*provenance['artifact_hashes'], 'generation.json'):
                    artifact = (output / name).read_bytes()
                    require(not any(value.encode() in artifact or
                                    json.dumps(value, ensure_ascii=True)[1:-1].encode() in artifact
                                    for value in private_values), 'artifact disclosed private runtime data')
            print(json.dumps(summary, ensure_ascii=False))
            return summary
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    arguments = parser.parse_args()
    exercise(arguments.output.resolve() if arguments.output else None)
