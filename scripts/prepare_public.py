#!/usr/bin/env python3
"""Create an isolated publication snapshot; never copies home Git history/config."""
import argparse
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'__pycache__','.git','.vercel','staging','public-proof'}
PRIVATE_NAMES={'runtime-inventory.json','local-verification-log.jsonl','preparation-evidence.json','preparation-result.json','preparation-review.md'}
EXT={'.py','.md','.json','.jsonl','.html','.css','.toml','.sh','.txt'}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();out=Path(args.out).resolve()
    assert out != ROOT and ROOT not in out.parents
    out.mkdir(parents=True,exist_ok=True)
    copied=[]
    for f in ROOT.rglob('*'):
        rel=f.relative_to(ROOT)
        if not f.is_file() or set(rel.parts)&EXCLUDED or f.name in PRIVATE_NAMES:continue
        if f.suffix not in EXT and f.name not in {'.gitignore','.vercelignore'}:continue
        # The release proof is copied on final sync after production verification.
        body=f.read_text();body=body.replace(str(Path.home()),'$HOME')
        target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(body);copied.append(rel.as_posix())
    home=Path.home()
    for folder,names in {'activity':['logger.py','connectivity.py','test_logger.py','test_workflow.py','viewer.html','README.md','example-project.jsonl'],'build':['current_content.py','build_current.py','check_current.py','check_site.py','BUILD.md']}.items():
        for name in names:
            source=home/'.claude/harness'/folder/name
            assert source.is_file(),source
            target=out/'kit'/folder/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());copied.append(target.relative_to(out).as_posix())
    (out/'.gitignore').write_text('__pycache__/\n*.pyc\n.vercel/\n.env*\n*.pem\n*.key\n.DS_Store\n')
    (out/'PUBLIC_SNAPSHOT.md').write_text('''# Publication boundary

This repository is a clean public snapshot of AI PMS research, implementation, tests, synthetic samples, ELI20 report, and changed canonical Harness Kit sources. It contains no original home Git history, credentials, account configuration, private audit backups, real user hook logs, or runtime identity inventory. Personal home paths in historical documentation are replaced with $HOME. Consequently historical hash receipts describe the original local artifacts and must not be treated as fresh public verification. Current release proof and the portable tests are the release evidence.

Kit/build contains the canonical source used in the existing Harness Kit home installation; that full generator needs the separately configured Harness Kit environment. Kit/activity is portable and independently testable. Public Kit downloads contain explicit, reviewed implementation sources. The sample app is a static synthetic dashboard, not a hosted receiver or an authenticated operations service. Automatic collection from users' PCs remains deferred.
''')
    (out/'publication-manifest.json').write_text(json.dumps({'kind':'sanitized-public-snapshot','files':sorted(copied),'excluded':['home Git history','credentials and settings','private audit backups','real runtime logs and inventory'],'personal_paths_replaced':True},indent=2)+'\n')
    print('Prepared',len(copied),'public source/sample/doc files')
if __name__=='__main__':main()
