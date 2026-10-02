#!/usr/bin/env python3
"""Local implementation gate, never proof of real multi-user delivery."""
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for name in ('test_operations.py', 'test_live.py', 'check_ui_live.py', 'test_kit_live.py', 'test_session_goal.py', 'test_demo.py'):
    subprocess.run([sys.executable, str(HERE / name)], cwd=ROOT, check=True)
print('LOCAL LIVE PMS CHECKS PASS; actual provider/remote two-user delivery requires separate evidence')
