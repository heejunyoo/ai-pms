#!/usr/bin/env python3
"""Approval preparation only; never a live delivery test."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    validator = Path.home() / '.agents/skills/handoff/validate.py'
    subprocess.run([sys.executable, str(validator), 'plan', str(ROOT / 'plan.json')], check=True, cwd=PROJECT)
    subprocess.run([sys.executable, str(validator), 'result', str(ROOT / 'preparation-result.json'), '--plan', str(ROOT / 'plan.json')], check=True, cwd=PROJECT)
    subprocess.run([sys.executable, str(ROOT / 'check_preparation.py'), '--selftest'], check=True, cwd=PROJECT)
    subprocess.run([sys.executable, str(ROOT / 'check_preparation.py')], check=True, cwd=PROJECT)
    evidence = json.loads((ROOT / 'preparation-evidence.json').read_text())
    require(evidence['scope'] == 'approval-preparation', 'wrong scope')
    for key in ('api_implementation_approved', 'actual_delivery_verified', 'product_complete'):
        require(evidence[key] is False, 'unapproved completion claim: ' + key)
    required = {'spec.md', 'sources.md', 'plan.json', 'intent-review.json', 'check_preparation.py',
                'runtime-inventory.json', 'RUNBOOK.md', 'APPROVAL.md', 'preparation-result.json', 'preparation-review.md'}
    require(set(evidence['file_hashes']) == required, 'missing preparation file')
    for name, digest in evidence['file_hashes'].items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, 'stale file: ' + name)
    inventory = json.loads((ROOT / 'runtime-inventory.json').read_text())
    for key in ('api_implementation_approved', 'actual_delivery_verified', 'product_complete'):
        require(inventory[key] is False, 'inventory must remain preparation only')
    preserved = {'central.py': ROOT.parent / 'ai-pms-central/central.py',
                 'test_central.py': ROOT.parent / 'ai-pms-central/test_central.py',
                 'logger.py': Path.home() / '.claude/harness/activity/logger.py'}
    require(set(evidence['preserved_code_hashes']) == set(preserved), 'missing preserved code')
    for name, digest in evidence['preserved_code_hashes'].items():
        require(hashlib.sha256(preserved[name].read_bytes()).hexdigest() == digest, 'changed protected source')
    print('APPROVAL PREPARATION VERIFIED; API approval REQUIRED; live delivery NOT EXECUTED')


if __name__ == '__main__':
    main()
