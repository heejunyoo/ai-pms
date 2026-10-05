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
subprocess.run([sys.executable,'specs/ai-pms-work-management/verify_work.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-toss-ia/check_ia.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-live/verify_live.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-phase-flow/check_flow.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-wbs-timeline/check_timeline.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-action-detail/check_action_detail.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-human-projection/check_human_view.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-rensei-experience/check_experience.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-visual-management/check_visual.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-readable-project/check_readable.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-component-map/check_map.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'specs/ai-pms-adoption-release/check_sample.py'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'scripts/verify_adoption.py'],cwd=ROOT,check=True)
print('PASS: portable public source, privacy, completion, snapshot and app checks')
