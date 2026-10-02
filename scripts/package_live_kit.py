#!/usr/bin/env python3
"""Copy explicitly allowlisted, credential-free PMS runtime into canonical Kit."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PMS_FILES=['specs/ai-pms-live/live_service.py', 'specs/ai-pms-live/live_sender.py', 'specs/ai-pms-live/session_goal.py', 'specs/ai-pms-live/demo_setup.py', 'specs/ai-pms-live/README.md', 'specs/ai-pms-live/sample/catalog.json', 'specs/ai-pms-live/sample/operations.json', 'specs/ai-pms-live/sample/central.json', 'specs/ai-pms-dashboard/portfolio.py', 'specs/ai-pms-dashboard/management.py', 'specs/ai-pms-dashboard/work.py', 'specs/ai-pms-dashboard/operations.py', 'specs/ai-pms-dashboard/dashboard.html', 'specs/ai-pms-central/central.py', 'specs/ai-pms-central/connectivity.py', 'specs/ai-pms-transport/common.py']
def main():
    destination=Path.home()/'.claude/harness/activity/pms'
    for name in PMS_FILES:
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True)
        body=(ROOT/name).read_bytes()
        assert b'/Users/' not in body,name
        target.write_bytes(body)
    (destination/'README.md').write_text('# AI PMS runtime\n\nStart in this directory. Follow specs/ai-pms-live/README.md for private synthetic setup, service, seed, sender and manager login. The public Vercel dashboard is a static sample. No provider hooks, trust, accounts or remote destination are installed. Python 3.11+; macOS/Linux.\n')
    print('Packaged',len(PMS_FILES),'explicit PMS runtime files; no credentials/runtime state')
if __name__=='__main__':main()
