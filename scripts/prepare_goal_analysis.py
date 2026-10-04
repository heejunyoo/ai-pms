#!/usr/bin/env python3
"""Prepare allowlisted goal comparison input. Never invokes a model or emits warnings."""
import argparse
import hashlib
import json
from pathlib import Path


def prepare(snapshot):
    projects = []
    for project in snapshot['projects']:
        work = project.get('work') or {}
        projects.append({
            'project_id': project['id'], 'name': project['name'],
            'owners': project['owners'], 'goal': project.get('goal'),
            'plan_id': work.get('plan_id'), 'plan_version': work.get('plan_version'),
            'objective_declarations': [{key: item.get(key) for key in ('id','version','kind','parent_id','title','success_condition','source')}
                                       for item in (project.get('management') or {}).get('objectives', [])],
            'phases': [{'phase_id': phase['id'], 'goal_label': phase['name']}
                       for phase in work.get('phases', project.get('phases', []))],
            'success_criteria': [{'id': item['id'], 'scope': item.get('scope'),
                                  'target_id': item.get('target_id'), 'description': item.get('label')}
                                 for item in project.get('criteria', [])],
            'source_refs': [{key: item.get(key) for key in ('actor_id','environment_id','project_id','evidence_mode')}
                            for item in project.get('sources', [])],
        })
    return {'kind': 'goal-comparison-input', 'version': 1,
            'evidence_mode': snapshot.get('evidence_mode'),
            'snapshot_generated_at': snapshot.get('generated_at'),
            'model_analysis_executed': False, 'findings': [], 'projects': projects,
            'missing_context': ['target audience and intended outcome may need confirmation',
                                'scope and confirmed organizational contribution must be resolved before warning'],
            'instruction': 'Compare intended outcome, audience, success criteria and scope. Shared technology or a shared team goal alone is not duplication. Existing collaboration is not duplicate effort. Cite evidence; propose only. Never merge projects or change completion.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    raw = args.snapshot.read_bytes()
    result = prepare(json.loads(raw))
    result['snapshot_sha256'] = hashlib.sha256(raw).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('Prepared goal input:', len(result['projects']), 'projects; model not invoked; no findings generated')


if __name__ == '__main__':
    main()
