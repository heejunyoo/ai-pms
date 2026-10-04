#!/usr/bin/env python3
"""Create an isolated publication snapshot; never copies home Git history/config."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from package_live_kit import PMS_FILES
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'graphify-out','.graphify','__pycache__','.git','.vercel','.local','runtime','outbox','inbox','staging','public-proof'}
PRIVATE_NAMES={'runtime-inventory.json','local-verification-log.jsonl','preparation-evidence.json','preparation-result.json','preparation-review.md','capture-health.json','state.json','live-state.json','sender-state.json','registry.json','sender.json','demo.json'}
EXT={'.py','.md','.json','.jsonl','.html','.css','.toml','.sh','.txt'}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();out=Path(args.out).resolve()
    assert out != ROOT and ROOT not in out.parents
    out.mkdir(parents=True,exist_ok=True)
    copied=[]
    for f in ROOT.rglob('*'):
        rel=f.relative_to(ROOT)
        if not f.is_file() or set(rel.parts)&EXCLUDED or f.name in PRIVATE_NAMES:continue
        if rel.as_posix() in {'specs/ai-pms-human-projection/public-phase-390.jpg', 'specs/ai-pms-human-projection/kit-analysis-390.jpg'}:
            target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(f.read_bytes());copied.append(rel.as_posix());continue
        if f.suffix not in EXT and f.name not in {'.gitignore','.vercelignore'} and rel.as_posix()!='specs/ai-pms-dashboard/human-view.js':continue
        # The release proof is copied on final sync after production verification.
        body=f.read_text();body=body.replace(str(Path.home()),'$HOME')
        target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(body);copied.append(rel.as_posix())
    home=Path.home()
    for folder,names in {'activity':['logger.py','connectivity.py','management.py','work.py','management_recorder.py','test_management_recorder.py','catalog-v3.template.json','catalog-work.template.json','operations.template.json','json-contracts.md','test_logger.py','test_workflow.py','viewer.html','README.md','example-project.jsonl'],'build':['current_content.py','build_current.py','check_current.py','check_site.py','BUILD.md']}.items():
        for name in names:
            source=home/'.claude/harness'/folder/name
            assert source.is_file(),source
            target=out/'kit'/folder/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());copied.append(target.relative_to(out).as_posix())
    # Explicit public procedure sources also shipped in the implementation ZIP.
    for target, source in {
        'kit/codex/docs/autonomous_coding.md': '.codex/docs/autonomous_coding.md',
        'kit/claude/docs/autonomous_coding.md': '.claude/docs/autonomous_coding.md',
        'kit/handoff/SKILL.md': '.agents/skills/handoff/SKILL.md',
        'kit/claude-handoff/SKILL.md': '.claude/skills/handoff/SKILL.md',
        'kit/codex/skills/codex-improvement-loop/SKILL.md': '.codex/skills/codex-improvement-loop/SKILL.md',
    }.items():
        body=(home/source).read_bytes()
        assert b'/Users/' not in body, target
        path=out/target;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body);copied.append(target)
    for name in [*PMS_FILES,'README.md']:
        source=home/'.claude/harness/activity/pms'/name
        target=out/'kit/pms'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());copied.append(target.relative_to(out).as_posix())
    for name in ('implementation.zip','reference-ko.zip','reference-en.zip'):
        source=home/'.claude/harness/site/public'/name
        target=out/'kit/downloads'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target);copied.append(target.relative_to(out).as_posix())
    for name in ('docs/json-contracts.md', 'kit/activity/json-contracts.md'):
        target = out / name
        target.write_text(target.read_text().rstrip() + '\n')
    (out/'.gitignore').write_text('__pycache__/\n*.pyc\n.vercel/\n.env*\n*.pem\n*.key\n.DS_Store\n')
    (out/'PUBLIC_SNAPSHOT.md').write_text('''# Publication boundary

This repository is a clean public snapshot of AI PMS research, implementation, tests, synthetic samples, ELI20 report, and changed canonical Harness Kit sources. It contains no original home Git history, credentials, account configuration, private audit backups, real user hook logs, or runtime identity inventory. Personal home paths in historical documentation are replaced with $HOME. Consequently historical hash receipts describe the original local artifacts and must not be treated as fresh public verification. Portable tests and the latest IA release proof describe current checks. Older dashboard/management/connectivity/transport receipts retain their recorded scope; stale hashes are preserved rather than presented as fresh browser verification.

Kit/build contains the canonical source used in the existing Harness Kit home installation; that full generator needs the separately configured Harness Kit environment. Kit/activity is portable and independently testable. Public Kit downloads contain explicit, reviewed implementation sources. The sample app is a static synthetic dashboard, not a hosted receiver or an authenticated operations service. The opt-in self-hosted Live PMS service, incremental sender, capture health and session-goal recorder are executable in kit/pms and specs/ai-pms-live. Real provider hook trust and remote two-user delivery remain unverified. Current separate-page action detail browser acceptance is recorded separately in specs/ai-pms-action-detail; no private telemetry is sent to the public sample.
''')
    for relative in [Path('specs/ai-pms-management/release-proof.json'),Path('specs/ai-pms-work-management/release-proof.json'),Path('specs/ai-pms-work-management/code-review.json'),Path('specs/ai-pms-toss-ia/release-proof.json'),Path('specs/ai-pms-toss-ia/code-review.json'),Path('specs/ai-pms-action-detail/code-review.json'),Path('specs/ai-pms-action-detail/release-proof.json')]:
        target=out/relative
        if not target.exists():continue
        receipt=json.loads(target.read_text());changed=[];stale=[]
        for path,digest in receipt.get('sha256',{}).items():
            source=ROOT/path
            if path.startswith('kit/') and not source.exists():source=home/'.claude/harness'/path[4:]
            if not source.exists() or hashlib.sha256(source.read_bytes()).hexdigest()!=digest:
                stale.append(path);continue
            public_digest=hashlib.sha256((out/path).read_bytes()).hexdigest()
            if public_digest!=digest:changed.append(path)
            receipt['sha256'][path]=public_digest
        receipt['publication_transform']={'source_receipt_sha256':hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),'changed_paths':changed,'stale_source_paths':stale,'reason':'Only fresh source hashes reconciled after path/whitespace sanitization. Historical hashes preserved; not another independent review or browser verification.'}
        target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    (out/'publication-manifest.json').write_text(json.dumps({'kind':'sanitized-public-snapshot','files':sorted(copied),'excluded':['home Git history','credentials and settings','private audit backups','real runtime logs and inventory'],'personal_paths_replaced':True},indent=2)+'\n')
    print('Prepared',len(copied),'public source/sample/doc files')
if __name__=='__main__':main()
