#!/usr/bin/env python3
"""Small recorder check: current acceptance, definition change and failed-work refusal."""
import copy
import json
from pathlib import Path
import session_goal as recorder

HERE = Path(__file__).resolve().parent
catalog = json.loads((HERE / 'sample/catalog.json').read_text())
records = json.loads((HERE / 'sample/operations.json').read_text())
verified = next(s for s in records['sessions'] if s['acceptance'])
p = next(p for p in catalog['projects'] if p['id'] == verified['project_id'])
bound, identity = recorder.bind(records, catalog, project_id=p['id'], actor_id=verified['actor_id'], environment_id=verified['environment_id'], source=verified['source'], session_id='new-explicit-session', source_project_id=verified['source_project_id'], goal_version='new-goal', goal='명시적으로 확인한 목표', task_ids=verified['task_ids'])
accepted = recorder.decide(bound, catalog, identity, verified['actor_id'], 'accepted')
model = recorder.portfolio.build_model(catalog=catalog, operations=accepted)
assert next(s for s in model['operations']['sessions'] if s['id'] == identity)['completion'] == 'accepted'
changed = copy.deepcopy(catalog)
target = next(project for project in changed['projects'] if project['id'] == verified['project_id'])
target['management']['work']['tasks'][0]['done_when'].append('새로운 완료 조건')
model = recorder.portfolio.build_model(catalog=changed, operations=accepted)
assert next(s for s in model['operations']['sessions'] if s['id'] == identity)['completion'] != 'accepted'
missing, missing_id = recorder.bind(records, catalog, project_id=p['id'], actor_id=verified['actor_id'], environment_id=verified['environment_id'], source=verified['source'], session_id='no-linked-check', source_project_id=verified['source_project_id'], goal_version='v1', goal='검증 없음', task_ids=[])
try:
    recorder.decide(missing, catalog, missing_id, verified['actor_id'], 'accepted')
    raise AssertionError('accepted unverified goal')
except ValueError:
    pass
print('Session recorder PASS: explicit binding, current acceptance, changed-definition invalidation, missing-check refusal')
