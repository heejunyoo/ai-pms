#!/usr/bin/env python3
"""Current work-management checks; live browser/public receipts are explicit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release',action='store_true');args=parser.parse_args()
    for script in ['specs/ai-pms-work-management/test_work.py','specs/ai-pms-work-management/check_ui_work.py','specs/ai-pms-work-management/test_kit_work.py','specs/ai-pms-work-management/exercise_work.py','specs/ai-pms-management/verify_management.py']:
        subprocess.run([sys.executable,script],cwd=ROOT,check=True)
    kit=ROOT/'kit/activity' if (ROOT/'kit/activity').exists() else Path.home()/'.claude/harness/activity'
    for name in ('management.py','work.py'):
        assert (kit/name).read_bytes()==(ROOT/'specs/ai-pms-dashboard'/name).read_bytes(),name
    if args.release:
        proof=json.loads((HERE/'release-proof.json').read_text())
        assert proof['automatic_collection_deferred'] and not proof['actual_multi_user_delivery_verified']
        assert proof['github_public'] and proof['dashboard_production'] and proof['kit_production']
        for key in ['people_many_projects','shared_project','phase_tasks','manager_action','import_preserves','mobile_390','live_public_path','kit_bilingual']:
            assert proof['browser'][key],key
        for name,digest in proof['sha256'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'stale release: '+name
        review=json.loads((HERE/'code-review.json').read_text());assert review['verdict']=='no_blockers'
        for name,digest in review['sha256'].items():
            p=ROOT/name
            if name.startswith('kit/') and not p.exists():p=Path.home()/'.claude/harness'/name[4:]
            assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,'stale independent review: '+name
    print('PASS: work management checks'+(' and release evidence' if args.release else '; browser/public verified separately'))
if __name__=='__main__':main()
