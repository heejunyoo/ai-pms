#!/usr/bin/env python3
"""Actual local subprocess -> catalog -> dashboard projection; synthetic identities only."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / 'kit/activity' if (ROOT / 'kit/activity').exists() else Path.home() / '.claude/harness/activity'
sys.path.insert(0, str(KIT))
import management_recorder as recorder
import test_management_recorder as tests

spec = importlib.util.spec_from_file_location('exercise_portfolio', ROOT / 'specs/ai-pms-dashboard/portfolio.py')
portfolio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portfolio)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--graph', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='pms-local-acceptance-') as directory:
        project = Path(directory)
        target = project / 'management.json'
        recorder.atomic_json(target, tests.fixture(project, "print('RAW_OUTPUT_NOT_FOR_STORAGE')\nraise SystemExit(0 if open('control.txt').read()=='pass' else 1)\n"))
        command = [sys.executable, str(KIT / 'management_recorder.py'), '--project', directory,
                   '--management', 'management.json', 'run', '--test-plan', 'test',
                   '--actor-id', 'Alice', '--environment-id', 'local', '--session-id', 'session-1']

        def model():
            p = recorder.read_json(target)
            return portfolio.build_model(catalog={'version': 3, 'projects': [p]}, now=recorder.now())

        assert subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 1
        failed = model()
        assert failed['projects'][0]['status'] == 'failed'
        (project / 'control.txt').write_text('pass')
        assert subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        passed = model()
        assert passed['projects'][0]['status'] == 'complete'
        attempts = passed['projects'][0]['management']['attempts']
        assert [a['exit_code'] for a in attempts] == [1, 0]
        assert 'RAW_OUTPUT_NOT_FOR_STORAGE' not in json.dumps(passed)
        graph_status = 'not_requested'
        if args.graph:
            p = recorder.read_json(target)
            graph = recorder.graph_record(project, p, timeout=60)
            graph_status = graph['status']
            assert graph_status == 'generated', 'Actual Graphify generation did not succeed'
            recorder.atomic_json(target, p)
        (project / 'control.txt').write_text('changed')
        p = recorder.read_json(target)
        recorder.refresh_artifact(project, p)
        recorder.atomic_json(target, p)
        stale = model()
        assert stale['projects'][0]['status'] == 'revalidation'
        if args.graph:
            assert stale['projects'][0]['management']['graphs'][0]['freshness'] == 'stale'
        result = dict(evidence='actual-local-subprocess-with-synthetic-identities',
                      actual_user_delivery=False, stages=['failed', 'complete', 'revalidation'],
                      attempt_exit_codes=[1, 0], raw_output_retained=False, graph_status=graph_status)
        (ROOT / ('specs/ai-pms-management/local-graph-proof.json' if args.graph else 'specs/ai-pms-management/local-execution-proof.json')).write_text(json.dumps(result, indent=2) + '\n')
        print('PASS: actual fail -> fix -> pass -> changed artifact revalidation; graph ' + graph_status)


if __name__ == '__main__':
    main()
