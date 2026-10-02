#!/usr/bin/env python3
"""Record an explicit session goal or acceptance; never infers goals from tool counts."""
import argparse
import copy
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'ai-pms-dashboard'))
sys.path.insert(0, str(HERE.parent / 'ai-pms-transport'))
import common
import operations
import portfolio


def bind(records, catalog, *, project_id, actor_id, environment_id, source, session_id, source_project_id, goal_version, goal, task_ids):
    candidate = copy.deepcopy(records)
    project = next(p for p in catalog['projects'] if p['id'] == project_id)
    session = dict(id='session-' + operations.digest([project_id, source_project_id, actor_id, environment_id, source, session_id])[:32], project_id=project_id, source_project_id=source_project_id, actor_id=actor_id, environment_id=environment_id, source=source, session_id=session_id, goal=project['goal'] if goal is None else goal, goal_version=goal_version, project_revision=project['current_revision'], task_ids=task_ids, acceptance=None)
    old = next((s for s in candidate['sessions'] if operations.identity(s) == operations.identity(session)), None)
    if old:
        session['id'] = old['id']
        session['acceptance'] = old['acceptance']  # Definition changes invalidate its old digest, not erase history.
        candidate['sessions'] = [s for s in candidate['sessions'] if s['id'] != old['id']]
    candidate['sessions'].append(session)
    portfolio.build_model(catalog=catalog, operations=candidate)
    return candidate, session['id']


def decide(records, catalog, session_record_id, actor_id, decision):
    candidate = copy.deepcopy(records)
    session = next(s for s in candidate['sessions'] if s['id'] == session_record_id)
    session['acceptance'] = None
    model = portfolio.build_model(catalog=catalog, operations=candidate)
    row = next(s for s in model['operations']['sessions'] if s['id'] == session_record_id)
    if decision == 'accepted' and row['completion'] != 'verified':
        raise ValueError('current linked work not verified')
    project = next(p for p in model['projects'] if p['id'] == session['project_id'])
    session['acceptance'] = dict(goal_version=session['goal_version'], goal_sha256=operations.goal_digest(session), verification_sha256=operations.verification_digest(session, project), decision=decision, actor_id=actor_id, at=common.now())
    portfolio.build_model(catalog=catalog, operations=candidate)
    return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--operations', type=Path, required=True)
    commands = parser.add_subparsers(dest='action', required=True)
    command = commands.add_parser('bind')
    for field in ('project-id', 'source-project-id', 'actor-id', 'environment-id', 'session-id', 'goal-version'):
        command.add_argument('--' + field, required=True)
    command.add_argument('--source', choices=sorted(operations.SOURCES - {'unknown'}), required=True)
    command.add_argument('--goal')
    command.add_argument('--task-id', action='append', default=[])
    command = commands.add_parser('decide')
    command.add_argument('--session-record-id', required=True)
    command.add_argument('--actor-id', required=True)
    command.add_argument('--decision', choices=('accepted', 'rejected'), required=True)
    args = parser.parse_args()
    try:
        catalog = common.strict_json(common.read_private(args.catalog, portfolio.MAX_FILE), portfolio.MAX_FILE)
        with common.locked(args.operations.parent, 'operations.lock'):
            records = common.strict_json(common.read_private(args.operations, portfolio.MAX_FILE), portfolio.MAX_FILE) if args.operations.exists() or args.operations.is_symlink() else dict(version=1, sessions=[], north_stars=[], contributions=[], capture=[])
            if args.action == 'bind':
                records, identity = bind(records, catalog, **{field: getattr(args, field) for field in ('project_id', 'actor_id', 'environment_id', 'source', 'session_id', 'source_project_id', 'goal_version', 'goal')}, task_ids=args.task_id)
            else:
                records = decide(records, catalog, args.session_record_id, args.actor_id, args.decision)
                identity = args.session_record_id
            common.write_private(args.operations, common.encode(records))
        print('Recorded explicit session goal/decision: ' + identity + '. Sender synchronization is separate.')
        return 0
    except Exception:
        print('session record failed: check private inputs, source ownership and current verification', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
