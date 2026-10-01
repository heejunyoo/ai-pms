"""Install only the reviewed handoff package files, preserving backups."""
import shutil
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ('validate.py', 'plan.schema.json', 'packet.schema.json', 'example.plan.json',
         'SKILL.md', 'intent_guard.py', 'example-intent.md', 'example-spec.md', 'example-review.json')

def main():
    assert 'VERDICT: aligned' in (HERE / 'code-review.md').read_text()
    backup = HERE / 'backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    pairs = [('codex-handoff', Path.home()/'.agents/skills/handoff'),
             ('claude-handoff', Path.home()/'.claude/skills/handoff')]
    for name, target in pairs:
        for filename in FILES:
            source = HERE / 'staging' / name / filename
            assert source.is_file()
            installed = target / filename
            if installed.exists():
                saved = backup / name / filename
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(installed, saved)
            shutil.copy2(source, installed)
    print(f'Installed reviewed packages; originals saved in {backup}')

if __name__ == '__main__':
    main()
