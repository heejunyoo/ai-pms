#!/usr/bin/env python3
"""Release acceptance: local checks plus fresh reviewed production evidence."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
def main():
    for script in ['specs/ai-pms-dashboard/test_portfolio.py','specs/ai-pms-dashboard/check_ui.py','specs/ai-pms-central/test_central.py']:
        subprocess.run([sys.executable,script],cwd=ROOT,check=True)
    proof=json.loads((ROOT/'specs/ai-pms-connectivity/release-proof.json').read_text())
    assert proof['github_public'] and proof['dashboard_production'] and proof['kit_production']
    assert proof['automatic_collection_deferred'] and not proof['live_user_delivery_verified']
    for field in ['connectivity_tab','scoped_resources','configured_vs_observed','failure_detail','import_export','mobile_390','kit_bilingual_links']:
        assert proof['browser'][field],field
    for name,digest in proof['sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    print('PASS: connectivity source, dashboard, Kit and public release evidence')
if __name__=='__main__':main()
