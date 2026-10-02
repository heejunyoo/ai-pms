#!/usr/bin/env python3
"""Runnable counterexamples for conservative goal and measurement projections."""
import copy
import unittest
import generate_sample as sample
h=sample.operations.helpers();op=sample.operations

class OperationsTests(unittest.TestCase):
    def setUp(self):self.catalog,self.store,self.records=sample.make_sample()
    def model(self):return h.build_model(self.store,self.catalog,sample.NOW,operations=self.records)
    def view(self):return self.model()['operations']
    def first(self):return next(s for s in self.view()['sessions'] if s['id']=='goal-0')
    def change_acceptance(self,**updates):self.records['sessions'][0]['acceptance'].update(updates)
    def test_optional_legacy(self):self.assertNotIn('operations',h.build_model(self.store,self.catalog,sample.NOW))
    def test_sample_states(self):
        view=self.view();first=self.first()
        self.assertEqual((first['lifecycle'],first['completion']),('active','accepted'))
        self.assertTrue(any(s['lifecycle']=='ended' and s['completion']=='failed' for s in view['sessions']))
        self.assertTrue(any(s['goal']=='' and s['completion']=='unknown' for s in view['sessions']))
        self.assertGreater(len(view['people']),1)
        self.assertTrue(any(len(p['project_ids'])>1 for p in view['people']))
        self.assertTrue(all(s['evidence_mode']=='synthetic' for s in self.store['sources'].values()))
    def test_rejected(self):self.change_acceptance(decision='rejected');self.assertEqual(self.first()['completion'],'rejected')
    def test_old_goal_version(self):self.change_acceptance(goal_version='v0');self.assertEqual(self.first()['completion'],'verified')
    def test_future_acceptance(self):self.change_acceptance(at='2026-10-03T00:00:00Z');self.assertEqual(self.first()['completion'],'verified')
    def test_changed_goal(self):self.records['sessions'][0]['goal']='다른 목표';self.assertEqual(self.first()['completion'],'verified')
    def test_changed_task_digest(self):self.records['sessions'][0]['task_ids']=[];self.assertEqual(self.first()['completion'],'unknown')
    def test_changed_revision(self):self.records['sessions'][0]['project_revision']='old';self.assertEqual(self.first()['completion'],'revalidation')
    def test_failure_acceptance_cannot_cover(self):
        p=self.catalog['projects'][0]
        next(a for a in p['management']['attempts'] if a['test_plan_id']=='test-action-1-check')['exit_code']=1
        self.assertEqual(self.first()['completion'],'failed')
    def test_blocked_acceptance_cannot_cover(self):
        p=self.catalog['projects'][0];p['management']['work']['updates'].append(dict(id='blocked-first',task_id='action-1',at='2026-10-02T11:55:00Z',state='blocked',summary='막힘',next_action='해결'))
        self.assertEqual(self.first()['completion'],'in_progress')
    def test_missing_goal(self):self.records['sessions'][0]['goal']='';self.assertEqual(self.first()['completion'],'unknown')
    def test_wrong_owner(self):
        self.records['sessions'][0]['task_ids']=['action-3']
        with self.assertRaises(ValueError):self.view()
    def test_wrong_native_uuid(self):
        self.records['sessions'][0]['source_project_id']='99999999-9999-4999-8999-999999999999'
        with self.assertRaises(ValueError):self.view()
    def add_event(self,kind,at,occurred=None):
        ref=self.catalog['projects'][0]['source_refs'][0];source=self.store['sources'][h.central.source_key(ref)];record=copy.deepcopy(next(iter(source['events'].values())))
        eid='99999999-9999-4999-8999-999999999999';record['event'].update(event_id=eid,kind=kind,native_event='SessionEnd' if kind=='session.end' else 'SessionStart',observed_at=at,occurred_at=occurred);source['events'][eid]=record
    def test_end_survives_later_stop(self):self.add_event('session.end','2026-10-02T11:02:00Z');self.assertEqual(self.first()['lifecycle'],'ended')
    def test_delayed_end_event_time(self):self.add_event('session.end','2026-10-02T11:59:00Z','2026-10-02T11:02:00Z');self.assertEqual(self.first()['ended_at'],'2026-10-02T11:02:00Z')
    def test_same_time_end_precedence(self):self.add_event('session.end','2026-10-02T11:00:00Z');self.assertEqual(self.first()['lifecycle'],'ended')
    def test_future_end_ignored(self):self.add_event('session.end','2026-10-03T00:00:00Z');self.assertEqual(self.first()['lifecycle'],'active')
    def test_native_uuid_isolation(self):
        self.assertEqual(len([s for s in self.view()['sessions'] if s['session_id']=='same-native-session']),2)
        p=self.catalog['projects'][0];ref=copy.deepcopy(p['source_refs'][0]);ref['project_id']='99999999-9999-4999-8999-999999999998';p['source_refs'].append(ref)
        source=copy.deepcopy(next(iter(self.store['sources'].values())));source.update(ref)
        for r in source['events'].values():r['event']['project_id']=ref['project_id']
        self.store['sources'][h.central.source_key(ref)]=source
        self.assertEqual(len([s for s in self.view()['sessions'] if s['session_id']=='same-native-session']),3)
    def test_source_isolation(self):
        source=next(iter(self.store['sources'].values()));record=copy.deepcopy(next(iter(source['events'].values())));eid='99999999-9999-4999-8999-999999999999';record['event'].update(event_id=eid,source='claude');source['events'][eid]=record
        self.assertTrue(any(s['source']=='claude' and s['goal']=='' for s in self.view()['sessions']))
    def test_measured_vs_declared(self):self.assertTrue(all(s['current_value']==20 and s['measurement_state']=='below_target' for s in self.view()['north_stars']))
    def test_future_measurement(self):
        self.records['north_stars'][0]['observations'][0]['at']='2026-10-03T00:00:00Z';self.assertEqual(self.view()['north_stars'][0]['measurement_state'],'unobserved')
    def test_outside_period(self):self.records['north_stars'][0]['observations'][0]['at']='2026-09-01T00:00:00Z';self.assertEqual(self.view()['north_stars'][0]['measurement_state'],'unobserved')
    def test_future_period(self):
        self.records['north_stars'][0]['period_start']='2026-10-03T00:00:00Z';self.assertEqual(self.view()['north_stars'][0]['measurement_state'],'unobserved')
    def test_conflicting_measurement(self):
        star=self.records['north_stars'][0];star['observations'].append(dict(star['observations'][0],id='conflict',value=100));self.assertEqual(self.view()['north_stars'][0]['measurement_state'],'unobserved')
    def test_decrease(self):self.records['north_stars'][0]['direction']='decrease';self.assertEqual(self.view()['north_stars'][0]['measurement_state'],'target_met')
    def test_contribution_states(self):self.assertEqual([c['confirmation_state'] for c in self.view()['contributions']],['proposed','confirmed'])
    def test_contribution_changed_goal(self):self.records['sessions'][0]['goal']='변경';self.assertEqual(self.view()['contributions'][1]['confirmation_state'],'reconfirmation')
    def test_contribution_changed_metric(self):self.records['north_stars'][1]['target']=40;self.assertEqual(self.view()['contributions'][1]['confirmation_state'],'reconfirmation')
    def test_contribution_observation_not_definition(self):self.records['north_stars'][1]['observations'][0]['value']=40;self.assertEqual(self.view()['contributions'][1]['confirmation_state'],'confirmed')
    def test_future_contribution(self):self.records['contributions'][1]['at']='2026-10-03T00:00:00Z';self.assertEqual(self.view()['contributions'][1]['confirmation_state'],'reconfirmation')
    def test_capture_recent_stale_unknown(self):
        self.assertEqual(self.view()['capture'][0]['freshness'],'recent');self.records['capture'][0]['last_recorded_at']='2026-10-02T11:58:59Z';self.assertEqual(self.view()['capture'][0]['freshness'],'stale');self.records['capture'][0]['status']='degraded';self.assertEqual(self.view()['capture'][0]['freshness'],'unknown')
    def test_capture_future(self):self.records['capture'][0]['last_recorded_at']='2026-10-03T00:00:00Z';self.assertEqual(self.view()['capture'][0]['freshness'],'unknown')
    def test_capture_unmapped(self):self.records['capture'][0]['project_id']='99999999-9999-4999-8999-999999999999';self.assertIn('미연결',self.view()['capture'][0]['reason'])
    def test_safeinteger(self):
        self.records['north_stars'][0]['target']=9007199254740992
        with self.assertRaises(ValueError):self.view()
    def test_bool_not_integer(self):
        self.records['capture'][0]['errors']=True
        with self.assertRaises(ValueError):self.view()
    def test_exact_keys(self):
        self.records['sessions'][0]['completed']=True
        with self.assertRaises(ValueError):self.view()
    def test_private_path(self):
        self.records['sessions'][0]['goal']='file /Users/private/data'
        with self.assertRaises(ValueError):self.view()
    def test_artifact_changed_and_repassed(self):
        p=self.catalog['projects'][0];mg=p['management'];mg['artifact']['files'][0]['sha256']='e'*64;mg['artifact']['sha256']=h.management.artifact_sha256(mg['artifact']['files'])
        for tp in mg['test_plans']:
            tp['test_files']=copy.deepcopy(mg['artifact']['files'])
        for a in mg['attempts']:
            tp=next(tp for tp in mg['test_plans'] if tp['id']==a['test_plan_id'])
            a['artifact_sha256']=mg['artifact']['sha256'];a['test_plan_sha256']=h.management.test_plan_sha256(tp)
        self.assertEqual(self.first()['completion'],'verified')
    def test_sameversion_task_changed_repassed(self):
        self.catalog['projects'][0]['management']['work']['tasks'][0]['done_when']=['다른 인수 조건']
        self.assertEqual(self.first()['completion'],'verified')
    def test_missing_verification_signature(self):
        del self.records['sessions'][0]['acceptance']['verification_sha256']
        with self.assertRaises(ValueError):self.view()
    def test_new_verification_acceptance(self):
        self.catalog['projects'][0]['management']['work']['tasks'][0]['done_when']=['다른 인수 조건']
        projected=h.build_model(self.store,self.catalog,sample.NOW)
        self.change_acceptance(verification_sha256=op.verification_digest(self.records['sessions'][0],projected['projects'][0]))
        self.assertEqual(self.first()['completion'],'accepted')
    def test_verification_clock_stability(self):
        self.catalog['projects'][0]['management']['attempts'][0]['at']='2026-10-03T11:00:00Z'
        before=h.build_model(self.store,self.catalog,sample.NOW)['projects'][0]
        after=h.build_model(self.store,self.catalog,'2026-10-04T12:00:00Z')['projects'][0]
        self.assertNotEqual(before['management']['attempts'][0]['status'],after['management']['attempts'][0]['status'])
        self.assertEqual(op.verification_digest(self.records['sessions'][0],before),op.verification_digest(self.records['sessions'][0],after))
    def test_raw_verification_equivalent(self):
        raw=self.catalog['projects'][0];projected=h.build_model(self.store,self.catalog,sample.NOW)['projects'][0]
        self.assertEqual(op.verification_digest(self.records['sessions'][0],raw),op.verification_digest(self.records['sessions'][0],projected))
    def test_deterministic(self):self.assertEqual(self.view(),self.view())

if __name__=='__main__':unittest.main()
