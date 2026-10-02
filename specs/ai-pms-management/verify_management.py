#!/usr/bin/env python3
"""Run current local checks; --release additionally requires current UI/public receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', action='store_true')
    args = parser.parse_args()
    kit = ROOT / 'kit/activity' if (ROOT / 'kit/activity').exists() else Path.home() / '.claude/harness/activity'
    assert (kit / 'management.py').read_bytes() == (ROOT / 'specs/ai-pms-dashboard/management.py').read_bytes()
    for script in [
        'specs/ai-pms-management/test_management.py',
        'specs/ai-pms-management/test_traceability.py',
        str(kit / 'test_management_recorder.py'),
        'specs/ai-pms-management/check_ui_v3.py',
        'specs/ai-pms-dashboard/test_portfolio.py',
        'specs/ai-pms-dashboard/check_ui.py',
        'specs/ai-pms-central/test_central.py',
        'specs/ai-pms-management/exercise_management.py',
        'scripts/build_dashboard_app.py',
    ]:
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)
    if args.release:
        proof = json.loads((ROOT / 'specs/ai-pms-management/release-proof.json').read_text())
        assert proof['automatic_collection_deferred'] and not proof['live_user_delivery_verified']
        assert proof['github_public'] and proof['dashboard_production'] and proof['kit_production']
        for flag in ['goal_assignment_personal', 'test_reason_attempts', 'blocker_help', 'kit_improvements', 'graph_freshness', 'invalid_import_preserves', 'mobile_390', 'kit_bilingual_downloads']:
            assert proof['browser'][flag], flag
        for name, digest in proof['sha256'].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, 'stale receipt: ' + name
        review_path = ROOT / 'specs/ai-pms-management/traceability-independent-review.json'
        if not review_path.exists(): review_path = ROOT / 'specs/ai-pms-management/code-review.json'
        review = json.loads(review_path.read_text())
        assert review['verdict'] == 'no_blockers' and review['reviewer'] != 'root-management-author'
        for name, digest in review['sha256'].items():
            path = ROOT / name
            if name.startswith('kit/') and not path.exists():
                path = Path.home() / '.claude/harness' / name[4:]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'stale review: ' + name
        public = json.loads((ROOT / 'specs/ai-pms-management/public-bytes.json').read_text())
        assert public['env_route_status'] == 404 and all(x['bytes_equal'] for x in public['production_bytes'])
    print('PASS: management local checks' + (' and current release receipts' if args.release else '; browser/public release verified separately'))


if __name__ == '__main__':
    main()
