#!/usr/bin/env python3
"""Parent acceptance for local central flow; never claims real user delivery."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_evidence(evidence, root):
    require(evidence['scope'] == 'local-central-flow', 'wrong scope')
    require(evidence['evidence_mode'] == 'synthetic', 'wrong evidence mode')
    require(evidence['actual_multi_user_delivery_verified'] is False, 'delivery is unverified')
    require(evidence['product_complete'] is False, 'product is incomplete')
    for key in ('multi_project_list', 'project_detail', 'original_event', 'mobile', 'empty_state'):
        require(evidence['browser_checks'][key] is True, 'missing browser check: ' + key)
    roles = {'central-dashboard', 'central-empty', 'browser-observation'}
    require(len(evidence['artifacts']) == 3, 'three distinct required artifacts')
    require({a['role'] for a in evidence['artifacts']} == roles, 'required artifact roles')
    paths = set()
    for artifact in evidence['artifacts']:
        relative = Path(artifact['path'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'unsafe artifact path')
        path = (root / relative).resolve()
        require(path.is_relative_to(root.resolve()) and path.is_file(), 'missing local artifact')
        require(path not in paths, 'duplicate artifact')
        paths.add(path)
        content = path.read_bytes()
        require(hashlib.sha256(content).hexdigest() == artifact['sha256'], 'stale artifact hash')
        if artifact['role'].startswith('central-'):
            require(path.suffix == '.html' and b'<html' in content.lower(), 'HTML artifact required')
        else:
            require(path.suffix == '.md' and len(content) > 200, 'browser observation required')


def selftest():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        artifacts = []
        for role, name, content in [('central-dashboard', 'dashboard.html', '<html>demo</html>'),
                                    ('central-empty', 'empty.html', '<html>empty</html>'),
                                    ('browser-observation', 'browser.md', 'browser observation\n' * 20)]:
            (root / name).write_text(content)
            artifacts.append({'role': role, 'path': name, 'sha256': hashlib.sha256(content.encode()).hexdigest()})
        valid = {'scope': 'local-central-flow', 'evidence_mode': 'synthetic',
                 'actual_multi_user_delivery_verified': False, 'product_complete': False,
                 'browser_checks': dict.fromkeys(('multi_project_list', 'project_detail', 'original_event', 'mobile', 'empty_state'), True),
                 'artifacts': artifacts}
        validate_evidence(valid, root)
        mutations = [lambda e: e.update(product_complete=True),
                     lambda e: e.update(actual_multi_user_delivery_verified=True),
                     lambda e: e.update(artifacts=[artifacts[0]] * 3),
                     lambda e: e['artifacts'][0].update(sha256='0' * 64),
                     lambda e: e['browser_checks'].update(mobile=False)]
        for mutate in mutations:
            invalid = json.loads(json.dumps(valid))
            mutate(invalid)
            try:
                validate_evidence(invalid, root)
            except ValueError:
                continue
            raise ValueError('selftest: invalid evidence accepted')
    print('acceptance guard selftest OK')


def main():
    if sys.argv[1:] == ['--selftest']:
        selftest()
        return
    require(not sys.argv[1:], 'unexpected arguments')
    subprocess.run([sys.executable, str(ROOT / 'test_central.py')], check=True)
    validate_evidence(json.loads((ROOT / 'acceptance-evidence.json').read_text()), ROOT)
    print('LOCAL CENTRAL FLOW VERIFIED; actual multi-user delivery UNVERIFIED; product INCOMPLETE')


if __name__ == '__main__':
    main()
