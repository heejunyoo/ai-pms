#!/usr/bin/env python3
"""Verify the offline dashboard and freshness of saved parent browser evidence."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import portfolio

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SKILL = Path.home() / '.agents/skills/handoff/validate.py'
CODE = ['portfolio.py', 'dashboard.html', 'test_portfolio.py', 'check_ui.py', 'sample/generate.py']
BROWSER_CHECKS = ['portfolio', 'compound_filters', 'search_empty_reset', 'project_checks', 'document_versions', 'sessions_environments', 'timeline_original', 'back_filter_focus', 'revalidation', 'unknown', 'import_error_preserves', 'import_replaces', 'export_reimport', 'mobile_390', 'empty', 'report_all_states', 'report_mobile_390']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def run(parts):
    result = subprocess.run(parts, cwd=ROOT, capture_output=True, text=True)
    require(result.returncode == 0, '검사 실패: ' + ' '.join(parts) + '\n' + result.stdout[-3000:] + result.stderr[-3000:])
    return dict(command=' '.join(parts), exit_code=0, output_tail=(result.stdout + result.stderr)[-1500:])

def embedded(path):
    match = re.search(r'<script id="pms-data" type="application/json">(.*?)</script>', path.read_text(), re.S)
    require(match is not None, 'embedded snapshot missing')
    return json.loads(match[1])

def main():
    checks = []
    for parts in ([sys.executable,str(SKILL),'plan',str(HERE/'plan.json')],
                  [sys.executable,str(SKILL),'result',str(HERE/'data-model-result.json'),'--plan',str(HERE/'plan.json')],
                  [sys.executable,str(SKILL),'result',str(HERE/'dashboard-ui-result.json'),'--plan',str(HERE/'plan.json')],
                  [sys.executable,str(HERE/'test_portfolio.py')],
                  [sys.executable,str(HERE/'check_ui.py')],
                  [sys.executable,str(ROOT/'specs/ai-pms-central/test_central.py')],
                  [sys.executable,str(Path.home()/'.agents/skills/eli5/check.py'),str(ROOT/'reports/ai-pms-eli20/index.html')]):
        checks.append(run(parts))
    snapshot = json.loads((HERE/'evidence/snapshot.json').read_text())
    model = portfolio.build_model(portfolio.read_json(HERE/'sample/central.json'),portfolio.read_json(HERE/'sample/catalog.json'),snapshot['generated_at'])
    require(snapshot == model, 'saved model differs from current inputs')
    require((HERE/'evidence/dashboard.html').read_text() == portfolio.render_html(model), 'generated dashboard stale')
    empty_path = HERE/'evidence/empty.html'
    empty_model = embedded(empty_path)
    require(empty_model == portfolio.build_model(now=empty_model['generated_at']), 'empty snapshot mismatch')
    require(empty_path.read_text() == portfolio.render_html(empty_model), 'empty template stale')
    projects = {p['id']:p for p in model['projects']}
    alice = projects['alice-recall']
    require(len(alice['sources']) == 2 and len(alice['sessions']) == 3 and alice['status'] == 'complete', 'multi-session continuity missing')
    require(projects['bob-payments']['status'] == 'failed' and projects['bob-payments']['owners'] == ['Bob'], 'identity/scope failed')
    require(projects['carol-dashboard']['status'] == 'revalidation', 'revalidation missing')
    require(projects['dana-discovery']['status'] == 'unknown', 'unknown promoted')
    browser = json.loads((HERE/'evidence/browser-verification.json').read_text())
    for item in BROWSER_CHECKS:
        require(browser['checks'].get(item) is True, 'browser evidence missing: '+item)
    for name, value in browser['artifact_sha256'].items():
        require(digest(ROOT/name) == value, 'browser evidence stale: '+name)
    expected = {str((HERE/name).relative_to(ROOT)) for name in CODE} | {'reports/ai-pms-eli20/index.html','specs/ai-pms-dashboard/evidence/dashboard.html','specs/ai-pms-dashboard/evidence/empty.html','specs/ai-pms-dashboard/evidence/snapshot.json','specs/ai-pms-dashboard/evidence/browser-observation.md'}
    require(expected <= set(browser['artifact_sha256']), 'browser artifact coverage missing')
    review = json.loads((HERE/'code-review.json').read_text())
    require(review['verdict'] == 'no_blockers' and review['reviewer'] != 'root-dashboard-author', 'independent final review missing')
    for name in CODE + ['preview_server.py','verify_dashboard.py']:
        key = str((HERE/name).relative_to(ROOT))
        require(review['code_sha256'].get(key) == digest(HERE/name), 'final review stale: '+key)
    receipt = dict(scope='offline-central-project-dashboard', offline_dashboard_complete=True, automatic_collection_deferred=True, actual_multi_user_delivery_verified=False, remote_service_deployed=False, evidence_mode='synthetic', tests=checks, project_count=len(model['projects']), browser_receipt_sha256=digest(HERE/'evidence/browser-verification.json'), code_review_sha256=digest(HERE/'code-review.json'), artifact_sha256=browser['artifact_sha256'])
    (HERE/'acceptance-evidence.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print('PASS: offline project dashboard; '+str(len(model['projects']))+' projects; saved parent browser evidence matches current artifacts')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (AssertionError,OSError,ValueError,KeyError,TypeError) as error:
        print('FAIL: '+str(error),file=sys.stderr)
        sys.exit(1)
