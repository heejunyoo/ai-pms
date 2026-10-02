# 현재 JSON 입력과 Kit 기록의 연결

2026-10-02 현재 구현을 설명합니다. v1/v2와 새 v3 중앙 관리 형식을 구분합니다.

## 현재 사용 가능한 파일

| 자료 | 위치 | 용도와 입력 경계 |
|---|---|---|
| 최소 프로젝트 catalog | `templates/catalog-v2.template.json` | 사용자·환경 연결, 목표, 단계, 문서, 검사 기준·결과, 선언 연결. CLI의 `--catalog` 입력입니다. |
| 상세 catalog 예시 | `specs/ai-pms-dashboard/sample/catalog.json` | 다섯 합성 프로젝트. criteria/runs/connections 작성 예시입니다. |
| 중앙 출처 manifest | `specs/ai-pms-dashboard/sample/manifest.json` | actor/environment/project와 선택된 JSONL 파일을 연결합니다. 중앙 import 입력입니다. |
| 훅/수동 이벤트 JSONL | Kit ZIP의 `activity/example-project.jsonl`, `activity/README.md`, `activity/logger.py` | 이벤트별 발생 기록. raw JSONL을 대시보드 JSON 가져오기에 넣는 형식은 아닙니다. |
| 중앙 저장 자료 | `specs/ai-pms-dashboard/sample/central.json` | 이벤트 원본, 출처, 수신 시각, 원본 파일 SHA256·행 번호. CLI의 `--store` 입력입니다. |
| 대시보드 snapshot | 공개 앱 `/snapshot.json`, `templates/snapshot-empty-v2.json` | 중앙 모델이 생성한 화면용 JSON. 대시보드 가져오기/붙여넣기의 입력입니다. |
| Handoff 작업 계획 | Kit ZIP의 `handoff/example.plan.json`, `plan.schema.json`, `packet.schema.json` | goal, 원문 요구사항, phase exit_check, task acceptance·파일 범위·제약. v3 기록기의 명시적 Handoff import를 사용할 수 있습니다. 자동 훅 import는 아닙니다. |
| Handoff 결과 | Kit ZIP의 `handoff/example.result.json`, `result.schema.json` | task_id, 실행 command/exit_code/output_tail, done_when_check/evidence, 변경 파일, 미충족 조건. v3 기록기의 명시적 Handoff import를 사용할 수 있습니다. 자동 훅 import는 아닙니다. |

Kit 웹의 AI PMS 페이지에는 역할·MCP 안전 메타데이터와 훅 예시가 있습니다. 이번 Kit ZIP에는 v3 catalog 템플릿과 필드 안내를 추가했습니다. Handoff 계획/결과 템플릿이 있다고 해서 그 파일들이 PMS에 자동으로 들어오는 것은 아닙니다.

## 기존 v1/v2에서 어떤 정보가 들어오나요?

| 정보 | 현재 출처 | 저장/표시하는 내용 | 알 수 없는 내용 |
|---|---|---|---|
| 세션·도구 활동 | 로컬 command hook | 세션/Agent/호출 ID(제공된 경우), native event, 요청/완료/실패, 발생/관측 시각 | 사용자의 목적, 판단 이유, 전체 완료 조건 |
| 프로젝트 목적과 결정 | 명시적인 manual record 또는 catalog | 목표·범위·결정 요약/이유, 기준·작업·산출물 참조 | 목표 분해의 타당성, 실제 이행 여부 자동 보증 |
| 문서와 검사 | catalog | 문서 버전/작성 출처, 6필드 검사 기준, revision·종료코드·evidence·기준 signature | 테스트 계획 생성 이유/버전 변화, 실행 주체와 환경, 신뢰된 runner 검증 |
| MCP·데이터 참조 | 훅의 안전한 이름 및 명시 metadata/map | 서버/tool, status, 제공된 duration_ms, 선언 operation, resources와 근거, 명시 artifact_refs | 서버 내부 DB/API 실제 접근, 실제 산출물에 활용되었는지 |
| 철칙·하네스·루프·스킬 운영 | 현재 일부 hook 이벤트 이름·별도 로컬 gate | 도구/세션 경계만 일부 관측 | 설정 버전, 규칙 판정, loop attempts, 스킬 선택 이유/버전/효과, 병목·개선조치의 중앙 이력 |

catalog의 criterion_signature는 기준 정의 변경을 감지하는 해시입니다. runner의 암호학적 서명이나 실제 실행의 증거가 아닙니다. check.recorded의 status=pass도 선언이며 runner 관측 결과와 구분해야 합니다.

## 최소 catalog로 생성

프로젝트/사용자/환경 ID와 실제 목표·검사 조건을 바꾼 뒤 다음을 실행합니다. 템플릿의 명령은 예시이며 이 명령으로 검사를 실행하지 않습니다. 테스트를 실행하지 않았다면 runs를 비워 둡니다.

```sh
python3 specs/ai-pms-dashboard/portfolio.py --catalog templates/catalog-v2.template.json --out output/dashboard.html --json-out output/snapshot.json
```

중앙 관리 목적과 책임은 `docs/central-management-contract.md`에 있습니다. v3는 아래의 별도 관리 JSON이며 기존 훅 이벤트 계약에 새 이벤트를 임의 추가하지 않습니다.

## v3 중앙 관리 기록

`templates/catalog-v3.template.json` 및 `specs/ai-pms-management/sample/catalog-v3.json`을 제공합니다. v3 프로젝트의 management에는 목표(objectives), 위임(assignment), 원문 요구사항(requirements), 계획 버전(plans), 테스트 설계(test_plans), 검사 대상 파일 manifest(artifact), 실행 시도(attempts), 막힘(blockers), 운영 개선(improvements), 적용 구성(harness), 선택 그래프(graphs)가 있습니다. 정확한 필드·허용값·참조 규칙은 `specs/ai-pms-management/spec.md`의 공유 계약입니다.

Kit ZIP의 `activity/management_recorder.py`, `management.py`, `catalog-v3.template.json`, `json-contracts.md`에서 같은 흐름을 사용할 수 있습니다. 기존 훅 JSONL은 도구 실행 경계이며 관리 기록은 별도의 프로젝트 JSON/catalog로 보존합니다. PC 자동 전달이나 전역 훅 설치는 수행하지 않습니다.

### 어떻게 플랜을 만들고 통과했는가?

plan은 원문 요구사항 ID, 문서 출처, 판단 이유, 요약, 버전과 작성 시각을 남깁니다. test_plan은 plan 버전과 검사 기준을 연결하고 요구사항별 선정 이유·제외 범위·검사 파일 해시를 남깁니다. Handoff import는 기존 파일에서 계획과 기준을 읽으므로 목표를 새로운 폼에 반복 입력할 필요가 없습니다. 누락된 테스트 선정 이유는 명시적 요약으로 보완합니다. Handoff 결과는 declared이며 통과 선언을 runner 관측으로 바꾸지 않습니다.

attempt는 실행 명령·시작/종료·종료코드·실행 환경·출처와 정확한 계획/검사 기준/파일 manifest 해시를 기록합니다. runner는 지정된 검사를 실제 실행하고 원문 출력은 저장하지 않습니다. 실패한 attempt를 덮어쓰지 않고 수정 후 새 attempt를 추가합니다. manifest에 포함되지 않은 파일의 최신성은 이 영수증으로 증명되지 않습니다.

### 중앙에서 무엇을 판단하는가?

현재 버전과 현재 파일 manifest에서 모든 프로젝트 조건에 대한 최신 runner 실행이 통과해야 기술 조건 충족입니다. 선언, 미래 실행, 변경된 기준/검사 파일, 다른 manifest의 통과는 현재 완료 판정에 사용하지 않습니다. 업무 성과 달성 여부는 별도 근거가 필요하며 현재 v3에서는 미관측으로 표시합니다. blocker에는 실패 근거·원인 가설/확인·담당자·다음 조치·해결 재검증을 연결합니다. improvement에는 개선 가설·변경 버전·개선 전후 시도·적용 판단을 연결합니다.

Graphify는 선택 분석이며 source revision/manifest 해시가 현재와 다르면 stale, 실패/미관측이면 unknown입니다. AST 관계를 실제 실행 경로나 테스트 커버리지로 해석하지 않습니다. 현재 소스 범위와 생성기 버전을 함께 확인해야 합니다.

## v3 필드 계약 상세

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
