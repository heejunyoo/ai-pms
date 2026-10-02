# 중앙 관리 구현 명세

기존 v1/v2 유지. v3 catalog는 projects에 management 필드를 추가하며 schema_version=3 snapshot에서도 각 프로젝트에 management 추가(미매핑은 null). v3에서는 legacy runs 입력은 빈 배열만 허용; runner attempts에서 정규화 runs를 만들어 기존 completion 로직을 재사용. v1/v2 결과는 입력 선언임을 UI에 유지. 새 외부 수집/API/DB 없음.

## 정본 공유 계약
management 객체는 아래 정확한 필드만 허용. portfolio.validate_tree 안전 검사와 크기 한도를 공통 적용. null 허용은 명시된 것만. 모든 id/version은 기존 identifier, SHA256은 소문자64hex, 시각은 UTC Z, 상대파일 경로는 프로젝트 내(normalized relative, .. 및 absolute 거부). 새 코드 stdlib only.
- objectives: [{id,version,kind:company|personal,parent_id:null|id,title,success_condition,source,at}]. 버전별 unique; parent는 같은 objective ID의 모든 버전에서 동일한 parent_id이어야 하며 ID 그래프 기준 cycle/참조 검증. 회사 success_condition은 선언이며 UI에 항상 업무 성과 미관측(기술 검사와 별도) 표시.
- assignment: null|{objective_id,objective_version,kind:outcome|task,issuer,assignee,at,acceptance}; objective/owner 참조. 개인도 연결가능하나 필수아님.
- requirements: [{id,text,source}]. unique.
- plans: [{id,version,at,summary,reason,requirement_ids,handoff_ref:null|string}]. requirements 참조. 명시적 설명만 기록.
- test_plans: [{id,version,plan_id,plan_version,criterion_id,requirement_ids,reason,excluded,at,definition,test_files}]. definition은 기존 six-field criterion. test_files=[{path,sha256}]. 현재 p.criteria 각각을 최신(at) test_plan이 정확하게 덮어야 함. 이전 정의 test_plan도 보존. 검사 계획 생성 이유/원문 연결/개정 이유는 reason에 남김.
- artifact: {revision,sha256,files:[{path,sha256}]}; revision=current_revision. files는 unique normalized relative paths, sha256=actual file bytes digest. artifact.sha256=SHA256(canonical(files sorted by path)); canonical은 portfolio.canonical과 동일 ASCII JSON(sort_keys=True,separators=(comma,colon),allow_nan=False). runner --management 입력의 artifact.files에 명시된 파일만 읽고 실행 전/후 digest 갱신. artifact.files는 검사와 관련된 test_files를 모두 포함해야 하며 포괄성은 사용자 선언이지 전체 workspace 증명이 아님. 실행전 해시를 attempt.artifact_sha256에 기록하고 사후 실제 manifest를 management.artifact에 저장하므로 변경이 생기면 그 attempt는 현재 판정 unknown. attempt 자체는 보존. 사후 파일 없어지면 작업 실패로 반환하고 관리 파일 원본 유지; runner 실패 영수증은 별도 안전 receipt 보존. 동일 revision의 이전 해시 attempt는 stale(unknown)로 보존하며 구조 자체 거부하지 않는다.
- attempts: [{id,test_plan_id,test_plan_version,test_plan_sha256,criterion_signature,revision,artifact_sha256,command,started_at,at,exit_code,actor_id,environment_id,session_id,environment:unit|mock|local|browser|live-provider|production,runner,summary,provenance:runner|declared}]. signature는 definition 기존 criterion_signature; test_plan_sha256=전체 test_plan canonical hash. 같은id unique; actor/environment mapped; command/planhash/signature 불일치 거부, 종료이전시작 거부. runner도 외부 서명 신뢰보증 아님. 미래 attempt는 unknown; declared는 completion 사용금지. 현재 revision인데 artifact hash 다르면 stale unknown. 과거 revision은 과거판정 가능하되 현재완료로승격금지.
- blockers: [{id,status:open|resolved,summary,cause_state:hypothesis|confirmed,cause,attempt_ids,owner,next_action,resolved_by:null|attempt_id}]. attempts/owner참조; resolved는 실제 pass attempt 필요(derivedstatus; 최신artifact이면해결, 바뀌었으면revalidation). inactivity로추정금지.
- improvements: [{id,area:rule|harness|loop|skill|mcp,version,hypothesis,change,evidence_attempt_ids,validation_attempt_ids,decision:proposed|trial|adopt|hold}]. attempts참조; adoption 효과는 명시기록, 빈validation이면검증미관측표시. 자동생산성점수없음.
- harness: [{id,version,source,at}]. 설치선언과실행근거구분.
- graphs: [{id,generator,version,mode:code-only,source_revision,source_sha256,at,status:generated|failed|unknown}]. 최신성은 현재 artifact와revision 일치+미래아님이면current; 다르면stale, 생성실패면unknown. AST=runtime/coverage아님.

## 코드 경계와 작업
Backend: specs/ai-pms-dashboard/management.py 신규, portfolio.py v3연결, specs/ai-pms-management/test_management.py, sample/catalog-v3.json (기존syntheticcatalog기반 Alice회사결과위임/Bob작업지시/Carol개인 포함), generate_sample.py. UI: dashboard.html 및 specs/ai-pms-management/check_ui_v3.py 신규만. Kit: ~/.claude/harness/activity/management_recorder.py, test_management_recorder.py, README.md 및 build/current_content.py/build_current.py; globalhooks/config 건드리지않음. 부모는공유module복사,템플릿/안내/ELI20/앱빌드통합/검증/배포담당.

Backend management.validate/project support derive runs+management view; UI management는 입력계약 동일 + attempts에 status:pass|fail|unknown, graphs에 freshness:current|stale|unknown, blockers에 verification:current|revalidation|unknown 추가. UI는 import시같은기본참조/정의hash/명령/artifact/provenance 경계 검증하고 완료결과와정규화runs 불일치거부. Web Crypto async 변경가능, sync JS canonical SHA256 구현도가능. 허위기록과 hash는신뢰보증아님.

Kit CLI: --project explicitdir, --management file for record, Handoff import plan/result helper와 run test-plan helper. 출력/원문 전체stdout를 저장하지않고 summary만, stdout DEVNULL. 실행command는 shlex argv(shell=False), timeout, 기존파일보존/atomic append. 사전/사후 manifest다르면 결과current로승격금지. Handoff import는 requirement source/plan/reason/acceptance_test를 seed하여 existing management와연결; Handoff 결과는 declared attempt로만. Graphify --graph optional 명시project내code-only/no-cluster; HOMEرفض, symlink탈출거부, 실패로메인test막지않음. hook 제안은 opt-in project wrapper로 전달(설치안함), 구조로그 JSONL을 local에쓰고 management.graphs에 반영. 비밀rawlog/환경/URL/API키자동수집금지.

## 검증
의미있는검사: 목표참조/cycle/담당귀속, 실패→수정→통과/개정기준변경/산출물변경재검증, 명령/planhash/artifact불일치, declared notcomplete, Handoff declared import, actual subprocess failpass 기록, graph failed/stale/unknown. 관리자UI company/task/personal, 이유/버전/요구사항/attempt/막힘/담당/개선/그래프최신성/MCP연결 모두탐색; v1/v2호환·잘못된import기존상태보존·390px 실제브라우저. publicsample 합성표시. docs/json-contracts.md와템플릿ZIP 제공. 최종 verify_management.py는 실제로실행한로컬test+빌드+현재관측해시 확인; 공개배포경로별실제bytes+UI별도확인. 기존proof는역사적유지.
