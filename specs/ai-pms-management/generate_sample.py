#!/usr/bin/env python3
"""Entirely synthetic management illustrations; no real subprocess receipts."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('sample_management',ROOT/'ai-pms-dashboard'/'management.py')
management=importlib.util.module_from_spec(spec);spec.loader.exec_module(management)
NOW='2026-10-01T00:00:00Z'

def make_catalog():
    catalog=json.loads((ROOT/'ai-pms-dashboard'/'sample'/'catalog.json').read_text()); catalog['version']=3
    for i,p in enumerate(catalog['projects']):
        owner=p['source_refs'][0]['actor_id']; p['runs']=[]
        personal=owner=='Carol' or i>2
        narrative={
            'Alice': ('고객 요청 분류 시간 단축', '고객 요청 지식 검색과 출처 표시', '합성 Company 요청분류 개선 지시문', '고객 질문을 지식 검색으로 연결하고 출처가 없는 답변을 차단한다', '출처 누락을 탐지한 실패 입력을 검증하고 출처 확인 분기를 수정했다'),
            'Bob': ('고객 요청 분류 시간 단축', '결제 요청 검증 구현', '합성 Company 결제검증 작업 지시문', '중복 결제 요청과 누락 금액을 검증한다', '중복 요청의 처리 순서가 불명확하여 담당자 지원이 필요하다'),
            'Carol': ('개인 프로젝트 현황을 한 화면에서 확인', '개인 대시보드', '합성 Carol 개인 요구사항 노트', '프로젝트 현황과 최신 검사 시각을 표시한다', '최신 검사 시각 기준을 개정했으므로 과거 통과 기록을 재검증한다'),
        }.get(owner, ('개인 아이디어 검토', '개인 기획', '합성 개인 노트', '아이디어의 요구사항을 정리한다', '아직 기술 검사를 계획하지 않았다'))
        p['name']=narrative[1]+' · 합성 예시';p['goal']=narrative[3]
        if owner=='Alice':
            for d in p['documents']:
                d['title']='고객 지식 검색 '+({'requirements':'요구사항','design':'설계','implementation':'구현 결과'}.get(d['kind'],d['kind']))
                d['summary']='합성 예시: 고객 질문에 대한 검색 결과와 출처 확인을 설계·구현합니다.'
                d['content']='합성 문서 '+d['version']+'\n요구사항: 출처 없는 답변을 차단합니다.\n검사: 검색 결과의 출처를 확인하고 누락된 경우 표시를 차단합니다.\n미검증: 실제 고객 요청 처리 시간 감소 여부.'
        objective=dict(id='objective-'+owner,version='v1',kind='personal' if personal else 'company',parent_id=None,title=narrative[0],success_condition='고객 요청 분류 시간 단축 여부는 실제 업무 성과 미관측' if not personal else '개인 프로젝트 현황 파악; 합성 예시이며 실제 사용 결과 미관측',source=narrative[2],at='2026-09-29T00:00:00Z')
        m=dict(objectives=[objective],assignment=None if personal else dict(objective_id=objective['id'],objective_version='v1',kind='outcome' if owner=='Alice' else 'task',issuer='Company',assignee=owner,at='2026-09-29T00:10:00Z',acceptance=narrative[3]),requirements=[dict(id='req-core',text=narrative[3],source=narrative[2])],plans=[dict(id='implementation',version='v1',at='2026-09-29T01:00:00Z',summary=narrative[3],reason='요구사항 원문을 구현과 검사로 연결: '+narrative[3],requirement_ids=['req-core'],handoff_ref='synthetic-plan.json')],test_plans=[],artifact={},attempts=[],blockers=[],improvements=[],harness=[dict(id='kit',version='v1',source='합성 Kit 설치 선언; 실행 근거와 별도',at='2026-09-29T01:00:00Z')],graphs=[])
        files=[dict(path='synthetic-test.py',sha256=__import__('hashlib').sha256(b'synthetic illustrative file; no execution\n').hexdigest())]
        m['artifact']=dict(revision=p['current_revision'],sha256=management.artifact_sha256(files),files=files)
        for j,c in enumerate(p['criteria']):
            tp=dict(id='test-'+c['id'],version='v1',plan_id='implementation',plan_version='v1',criterion_id=c['id'],requirement_ids=['req-core'],reason='업무 요구사항의 기술 동작을 검사: '+narrative[3]+'; '+c['label'],excluded='외부 provider 및 실제 업무 성과는 관측하지 않음',at='2026-09-29T02:00:00Z',definition=copy.deepcopy(c),test_files=copy.deepcopy(files))
            m['test_plans'].append(tp)
            def attempt(suffix,exit_code,at,revision=None,artifact=None):
                return dict(id='attempt-'+c['id']+'-'+suffix,test_plan_id=tp['id'],test_plan_version=tp['version'],test_plan_sha256=management.test_plan_sha256(tp),criterion_signature=management.criterion_signature(tp['definition']),revision=revision or p['current_revision'],artifact_sha256=artifact or m['artifact']['sha256'],command=c['command'],started_at=at,at=at,exit_code=exit_code,actor_id=owner,environment_id=p['source_refs'][0]['environment_id'],session_id=owner.lower()+'-management',environment='mock',runner='synthetic-example',summary=('실패: '+narrative[4] if suffix=='fail' else '수정 후 통과: '+narrative[4] if suffix=='pass' else '과거 기준 통과; 최신 기준과 산출물 재검증 필요')+' · 합성 실행 예시',provenance='runner')
            if owner=='Alice':
                m['attempts'].extend([attempt('fail',1,'2026-09-29T03:00:00Z'),attempt('pass',c['expected_exit_code'],'2026-09-29T04:00:00Z')])
            elif owner=='Bob': m['attempts'].append(attempt('fail',1,'2026-09-29T03:00:00Z'))
            elif owner=='Carol':
                m['attempts'].append(attempt('old',c['expected_exit_code'],'2026-09-29T03:00:00Z',artifact='0'*64))
                newer=copy.deepcopy(tp); newer['version']='v2';newer['at']='2026-09-29T04:00:00Z';newer['reason']='최신 검사 시각 표시를 인수 기준에 추가; 과거 통과를 재검증해야 한다';newer['definition']['label']+=' · 개정';m['test_plans'].append(newer);c.update(newer['definition'])
        if m['attempts']:
            first=m['attempts'][0]; last=next((a for a in reversed(m['attempts']) if a['test_plan_id']==first['test_plan_id']),first)
            m['blockers'].append(dict(id='blocker-main',status='resolved' if owner=='Alice' else 'open',summary='출처 누락 수정 후 재검사 통과' if owner=='Alice' else '중복 결제 요청 처리 지원 요청' if owner=='Bob' else '개정 기준과 변경된 산출물 재검증',cause_state='confirmed' if owner=='Alice' else 'hypothesis',cause=narrative[4],attempt_ids=[first['id']],owner=owner,next_action='검사 재실행 및 담당자 지원',resolved_by=last['id'] if owner=='Alice' else None))
            m['improvements'].append(dict(id='loop-change',area='loop',version='v1',hypothesis='실패 입력을 검증 루프에 포함하면 같은 오류를 찾을 수 있다',change='합성 검사 검증 루프에 실패 사례 추가',evidence_attempt_ids=[first['id']],validation_attempt_ids=[last['id']] if owner=='Alice' else [],decision='adopt' if owner=='Alice' else 'trial'))
        m['graphs']=[dict(id='graph-synthetic',generator='synthetic-graphify',version='v1',mode='code-only',source_revision=p['current_revision'],source_sha256=m['artifact']['sha256'] if owner!='Carol' else '0'*64,at='2026-09-29T05:00:00Z',status='failed' if owner=='Bob' else 'generated')]
        p['management']=m; management.validate(p)
    return catalog

if __name__=='__main__':
    out=Path(__file__).parent/'sample'/'catalog-v3.json'; out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(make_catalog(),ensure_ascii=False,indent=2)+'\n')
    print('synthetic management catalog generated')
