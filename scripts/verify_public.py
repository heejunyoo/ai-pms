#!/usr/bin/env python3
"""Portable public checks. Historical home-dependent receipts are not replayed."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
for name in ['kit/activity/test_logger.py','kit/activity/test_workflow.py','specs/ai-pms-central/test_central.py','specs/ai-pms-dashboard/test_portfolio.py','specs/ai-pms-dashboard/check_ui.py','specs/ai-pms-transport/test_delivery_view.py']:
    subprocess.run([sys.executable,name],cwd=ROOT,check=True)
subprocess.run([sys.executable,'scripts/build_dashboard_app.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-management/verify_management.py'],cwd=ROOT,check=True)
print('PASS: portable public source, privacy, completion, snapshot and app checks')
