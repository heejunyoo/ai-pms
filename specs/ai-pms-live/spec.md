# 사람·세션 중심 PMS와 증분 동기화

## 근거와 범위

portfolio.py build_model의 세션은 네 필드뿐, work.py derive는 실제 작업 완료 재계산 가능. dashboard.html validateModel은 strict snapshot이며 안전 DOM 사용. common.py의 private I/O·strict_json·locked·digest는 재사용. 기존 sender/receiver는 loopback pilot로 보존한다. Kit logger.py hook은 fsync하되 실패에도 exit0; management_recorder.py는 별도 v3 catalog를 저장한다.

stdlib만 사용한다. 기존 v1/v2/v3 snapshot과 검사 호환성을 보존한다. 목적지 미지정이므로 실행 가능한 자체 호스팅 중앙 서비스와 HTTPS 송신 설정을 만든다. 공용 Vercel에는 합성 운영 예시를 배포하며 영속 수신기로 주장하지 않는다. 실제 원격 두 참여 환경은 별도 실증이며 미검증 표시를 유지한다.

## 모델 계약

별도 operations 입력 파일 `{version:1,sessions:[],north_stars:[],contributions:[],capture:[]}`. 기존 catalog를 변경하지 않고 build_model(..., operations=None)의 선택 인자로 추가한다. 입력이 없으면 기존 출력 그대로다. 있을 때 snapshot.operations는 `{version:1,records:<입력>,sessions:<계산>,people:<계산>,north_stars:<계산>,contributions:<계산>,capture:<계산>}`. operations.py에서 validate(records, projects), derive(records, projects, store, now)를 공개하고 derive가 위 snapshot.operations 객체를 반환한다. strict exact keys, 참조/귀속/길이/시간/개인정보 검증, 결정적인 정렬, 정수 수치만 사용한다.

session 레코드: `{id,project_id,source_project_id,actor_id,environment_id,source,session_id,goal,goal_version,project_revision,task_ids,acceptance}`. id는 전역 레코드 ID. source는 codex/claude/cursor/gemini/unknown. task_ids는 같은 프로젝트의 현재 work 작업 ID들. acceptance는 null 또는 `{goal_version,goal_sha256,verification_sha256,decision,actor_id,at}`; decision accepted/rejected. 목표/수락은 선언 근거이며 인증된 관리자 승인으로 과장하지 않는다. source_refs의 사람/환경에 속해야 한다. native ID가 같아도 사람/환경/source/project로 분리한다. goal은 비어도 허용하고 미입력 표시. 작업이 없으면 검증 미관측; 현재 revision과 작업 완료 근거/막힘/사람 검토를 계산기로 확인한다. 세션 목표가 바뀌면 이전 acceptance 버전은 무효. 연결 작업이 완료여도 목표의 적절성은 별도 사람 판단이다.

계산 sessions는 레코드 필드 외에 `{lifecycle,last_activity_at,started_at,ended_at,completion,reason,event_ids}`만 추가한다. lifecycle started/active/ended/unknown, completion unknown/in_progress/failed/revalidation/verified/accepted/rejected. 이벤트는 해당 출처의 matching source+session만 사용하며 미래 제외; Stop은 턴 종료. 이전 목표 버전·revision·미래 수락을 현재 인수로 사용하지 않는다. native 이벤트만 있는 미연결 세션도 records.sessions에 없는 경우 자동 투영하고 목표 미입력·검증 unknown 표시한다. 자동 행 ID는 식별 조합의 digest로 생성하며 원본session 키를 보존한다. people는 `{actor_id,session_ids,project_ids,attention_session_ids}`.

north_star 레코드: `{id,scope,scope_id,name,metric,unit,period_start,period_end,baseline,target,direction,owner,observations}`. scope company/team, direction increase/decrease, baseline/target/observations.value는 정수(소수는 단위를 바꿔 표현). observations 항목 `{id,at,value,evidence,provenance}`, provenance measured/declared. 기간내 현재 시각까지 measured만 현재 관측 후보; declared/future/outsideperiod는 성과 판정 근거 아님. 계산 행은 입력 필드 외 `{current_value,current_at,measurement_state}`; state unobserved/below_target/target_met. 목표 기간 종료/시작 경계도 표시하며 미래 목표기간은 target_met 금지.

contribution 레코드: `{id,session_record_id,north_star_id,status,rationale,evidence,confirmed_by,goal_sha256,north_star_sha256,at}`. status proposed/confirmed, proposed의 confirmed_by=null, confirmed는 actor ID. 기여율 계산하지 않고 중복 성과 합산하지 않는다. 연결 확인은 인과 검증 아님. 확정도 시각/근거 명시. 독립 개인 세션은 기여 연결 없어도 정상.

## 증분 동기화 서비스

새 live_service.py/live_sender.py는 기존 pilot를 변경하지 않는다. owner-only registry는 writer entries `{actor_id,environment_id,project_ids,token_sha256}`, 별도 manager {actor_id,token_sha256}. 서버는 loopback 기본, 외부 bind는 TLS cert/key 없으면 거절한다(종단 프록시 지원은 향후). 등록된 writer만 기록하고 관리 읽기는 별도 자격. 브라우저는 same-origin, 로그인 POST를 통한 HttpOnly/SameSite=Strict cookie, 토큰 localStorage/URL 금지, CSRF Origin 검사, 외부 CORS 금지. manager만 north_star와 confirmed contribution 쓸 수 있다. cookie secure는 TLS에서 적용한다. 규모 한도·권한·출처·body 길이·duplicate JSON key·잘못된 UTF8·symlink 처리 유지.

POST /api/records envelope `{version:1,event_id,kind,base_revision,payload}`. kind hook/project/session/north_star/contribution/capture. hook payload는 `{actor_id,environment_id,event:<기존valid_event>}`; identity는 registry와 일치해야 하며 기존 native event_id로 dedup. 다른 kind payload는 위 레코드 또는 완전한 v3 project. base_revision은 해당 entity 중앙 현재 revision; 처음0, 다음 현재값. 동일 event_id+내용 재전송은 같은 ACK, 같은ID 다른내용/낡은base는409. entity revisions와 현재 변경 cursor는 정수. ACK `{event_id,cursor,entity_revision,status:'applied'}`는 검증·영속 저장·투영 완료 뒤 반환. 오류시 이전 데이터 보존. append journal을 영속 근거로 쓰고 재시작 replay; 절반 쓰기/부분 journal은 정상 완료로 처리하지 않는다. 영속 전체 상태 atomic replace 방식도 허용하며 상태당 이벤트 해시·revision·cursor를 한 트랜잭션에 저장한다. ponytail: bounded serialized pilot, 대규모 영속 DB로 전환은 실측 필요시.

GET /api/changes?after=N: `{cursor,reset,project_updates,operations,generated_at}`. 초기/reset은 전체 project_updates; 일반 갱신은 바뀐 project ID의 snapshot 행만. operations는 작고 bounded하므로 변경 있을 때 전체 operations 투영, 없으면 null. cursor는 persisted monotonic; 과거 retained 범위 밖은 reset. projection은 portfolio.build_model로 기존 work freshness 계산을 포함하며 현재시간 경과에 따른 freshness도 갱신한다. GET /api/status는 수집/집계/현재cursor 건강 상태, 개인 내용 없이 manager-only. 루트는 기존 dashboard를 연결모드로 렌더. 인증 없는 조회는401.

sender는 로컬 logdir JSONL과 catalog/operations 파일의 단일 레코드 변경을 감시, context filtering, partial line 대기, 내구 outbox/retry, atomic ACK 삭제, 실패 격리/충돌 상태 표시. catalog 원자 교체에서 project별 diff, operations도 entity별 diff하므로 전체 catalog 송신하지 않는다. 감시 재시작/오프라인에서 변경이 사라지지 않아야 한다. HTTPS 원격 URL만 또는 명시적 loopback-test http; redirect/proxy/credential URL 금지. 개인 경로·토큰은 wire payload/출력에 넣지 않는다. 중앙 base revision conflict는 조용히 overwrite 금지. CLI --once/--watch, 설정/자격 파일은 owner-only. 송신 설정은 실제 사용자가 opt-in한다.

## 화면 계약

기존 프로젝트 근거 상세를 재사용하되 첫 주 흐름은 사람 목록 → 그 사람의 세션 목록 → 목표·생명주기·목표 인수/실패 이유·작업과 근거. 회사/팀 목표 보기는 북극성 기간/단위/목표/실측과 기여 연결을 표시한다. 각 세션에서 기존 프로젝트의 작업/검사/문서까지 내려가며 뒤로가기·키보드 초점·390px 지원. 기존 import/export는 보존하고 operations 파생 필드를 Python과 동일하게 검증하여 forged completion 거부.

연결모드는 `<body data-live='true'>`로만 활성화, 기본 static은 네트워크 요청 안 함. same-origin 2초 polling, changes의 프로젝트 행 교체와 operations 반영, 기존 선택/탭/초점 보존; 연결/인증 실패·마지막 적용 시각·지연을 표시. 초기cursor0 조회, 이후 cursor, reset 처리. 기존 배열 갱신의 필터 선택 보존. 로그인 UI는 입력을 메모리로만 처리 후 지우고 cookie 방식. static 합성 예시는 사람별 여러 세션·종료되었으나 목표 실패·열려있으나 검증 통과·미연결·회사/팀 지표 제안을 포함하고 합성임을 표시.

## Kit와 인수

Kit에는 sender/service/operations 구현 및 설정·session JSON 템플릿과 로컬 live 실행 안내를 포함한다. logger 성공 마지막 event_id/at 및 오류수/마지막 실패를 별도 owner-only 건강파일에 atomic 저장하고 기록 상태를 확인하는 CLI를 추가한다. 건강 기록 자체 실패는 stderr이며 정상으로 주장하지 않는다. 실제 앱 hook 계약·지원범위는 설정과 stdin 성공이 아닌 실제 앱 실행별로 확인한다. 글로벌 hooks 자동 설치/trust 변경은 이번에 하지 않는다.

인수: test_operations.py 종료/인수/새목표/시간/귀속/지표 반례; test_live.py 실제 local HTTP 2 writer→hook+management revision→changes, restart/offline/idempotency/conflict/unauthorized/storage failure; check_ui_live.py Python/JS parity·개인 선택/세션 상세/changes 적용; Kit 건강 실패 반례. verify_live.py가 통합 검사. 실제 앱 두 환경/원격/production 브라우저가 없으면 해당 플래그 false. 부모가 공개 빌드/배포/현실 경계와 최종 독립 검토를 담당한다.

## Astra 검토 반영 — 결정 규칙과 권한

capture 레코드는 `{id,project_id,actor_id,environment_id,source,last_event_id,last_recorded_at,errors,last_failure_at,status,at}`. status observed/degraded/unknown; 시간은 null 또는 UTC, errors는 nonnegative safe integer. snapshot.operations.capture는 입력 필드 외 `{freshness,reason}`; freshness recent/stale/unknown, 마지막 정상 기록 60초 초과는 stale(미사용 중일 수도 있으므로 훅 실패로 단정하지 않음). logger 건강파일은 경로/내용/토큰 없이 작성하며 sender가 identity를 붙여 송신한다. capture 자체 저장·읽기 실패는 degraded/unknown이며 건강하다고 보고하지 않는다. 실제 훅 호출의 완전한 커버리지는 증명하지 않는다.

session 목표 digest는 id/project_id/source_project_id/actor_id/environment_id/source/session_id/goal/goal_version/project_revision/task_ids만 canonical SHA256로 계산한다. acceptance는 현재 digest·goal version 일치와 현재시각 이하일 때만 유효하다. completion 우선순위는 goal 미입력/작업 미연결 unknown, revision 불일치 revalidation, 연결된 작업 실패 failed, 근거/승인/막힘 불충분 in_progress 또는 unknown, 작업 모두 현재 완료 verified, 유효 rejected는 rejected, 유효 accepted는 모든 작업 verified일 때만 accepted다. 실패/재검증/미관측이 accepted 선언으로 덮이지 않는다. task owner가 null 또는 해당 actor여야 연결 가능(다른 담당자 작업을 본인의 세션 인수 근거로 차용 금지). same native ID는 raw project UUID를 포함한 출처와 source/session tuple로 구별한다.

lifecycle은 occurred_at 또는 observed_at의 사건시각으로 정렬하고 미래는 제외한다. 마지막 session.end가 마지막 session.start보다 같거나 늦으면 ended; end 뒤 tool/Stop만 있어도 종료 유지, 더 늦은 start가 있어야 다시 active/started다. 동일시각 start/end는 ended로 보수 판정한다. start/end 없는 tool은 active 관측이지만 종료 불명 reason 표시. delayed arrival/duplicates가 상태를 왜곡하면 안 된다.

northstar 정의 digest는 observations를 제외한 모든 정의 필드의 canonical SHA256. 실측 후보의 최신 같은 시각에 서로 다른 값이 있으면 unobserved로 보수 판정한다. 미달은 below_target이며 일정 준수 의미의 on_track이 아니다. 범위 밖/미래 관측과 declared는 측정 성과로 사용하지 않는다. 정수는 JS safe integer 범위로 제한한다. contribution 계산은 입력 외 `{confirmation_state,reason}`; 상태 proposed/confirmed/reconfirmation. confirmed라도 현재 goal digest/northstar digest와 다르거나 미래 at면 reconfirmation으로 표시한다. manager의 confirmed_by는 인증 주체 actor_id와 일치해야 한다.

registry writer에 project_ids는 native project UUID 목록이며 actor_id/environment_id 조합을 admitted source identity로 취급한다. catalog project.source_refs의 모든 identity는 registry에 미리 등록돼야 한다. writer 최초 project 생성은 자기 identity만 허용한다. 후속 project 교체는 source_refs 불변이며 타 actor의 attempts/documents/traceability/reviews/task updates를 변경·삭제·추가할 수 없다. 새 자기 검사·문서·기록의 actor는 인증 actor와 같아야 하고 작업 update는 자기 owner인 작업만 수정한다. goal/계획/artifact 변경은 등록된 프로젝트 writer의 공동 변경 선언으로 취급하며 revision conflict를 적용한다. manager가 shared project를 최초 등록하거나 source admission을 변경한다. session actor/environment도 writer와 일치하며 acceptance.actor_id는 인증 주체와 일치해야 한다. 기존 acceptance를 유지하는 것과 새 수락을 생성/변경하는 것을 구별한다. 관리자 역할은 북극성/확인 권한이며 arbitrary reviewer 이름을 실제 검토 인증으로 승격하지 않는다.

project보다 먼저 온 허가된 native hook는 durable unmapped store에 보존하고 portfolio의 기존 unmapped 프로젝트 투영을 사용한다. 이후 catalog source 연결 시 동일 원본 ID로 재투영한다. sender는 catalog/operations entity 삭제를 현재 미지원하며 삭제 감지 시 명시적인 conflict/unsupported 상태를 기록하고 중앙 잔존을 정상 동기화로 표시하지 않는다. 완전한 삭제 계약은 후속 명시 변경으로 한다.

Codex Stop/SubagentStop exit0은 현재 공식 계약에서 JSON stdout이 필요하므로 logger는 해당 이벤트에서 `{}`를 출력한다. 훅 실패도 에이전트를 막지 않되 건강 상태 및 safe stderr를 남긴다. 선택 설치 템플릿을 제공하고 사용자의 /hooks 리뷰·trust를 대신 승인하지 않는다. 공식 확인: https://developers.openai.com/codex/hooks 및 https://code.claude.com/docs/en/hooks (2026-10-02 열람).

식별자 고정: session.project_id는 catalog 프로젝트 ID, source_project_id는 native UUID이며 정확한 source_ref(actor/environment/native UUID)가 해당 catalog에 존재해야 한다. capture.project_id는 native UUID다. capture는 source identity로 catalog를 찾아 표시하며 없으면 unmapped로 보존한다. 자동 session 행에도 source_project_id를 포함한다.

## 검증 근거에 묶인 인수 — 독립 코드 검토 보완

acceptance.verification_sha256는 필수64hex다. operations.verification_digest(session, projected_project)는 canonical SHA256({project_id:project.id,current_revision:project.current_revision,criteria:project.criteria,management:{artifact,plans,test_plans,attempts,blockers,work}})로 고정한다. management에는 명시된 여섯 키만 넣고 누락 work는 null로 넣는다. session 인자는 project_id 일치 검사를 위해 사용한다. 파생 work/state/reason/generated_at/hook/capture는 digest에 넣지 않는다. 입력의 관리 work는 원본 정의/updates/reviews를 포함하므로 upstream 의존작업·동일시각 기준 교체·새검사도 바인딩된다. 검증기가 signature를 현재 프로젝트와 비교해야 인수가 유효하다.

단순화를 위해 프로젝트 전체의 검증 관련 관리 입력에 묶는다. 다른 담당 작업의 검증 관련 변경도 재확인을 요구할 수 있지만 일반 훅/시각 경과는 무효화하지 않는다. task/artifact 변경 뒤 새 통과 결과가 오더라도 과거 인수 선언은 되살아나지 않으며, 새 verification digest로 다시 수락해야 한다. Python/JS 동일 함수와 현재/과거 artifact 및 same-version task 변경·재통과 반례를 추가한다. 이 보완은 기존 goal 정의 digest를 대체하지 않고 함께 검사한다.

투영 원본 복원 규칙: verification_digest는 projected management의 test_plans에서 criterion_signature/test_plan_sha256를 제거하고, attempts에서 status를, blockers에서 verification을 제거하여 계약상 원본으로 정규화한다. 그 외 원본 키는 모두 보존한다. management.derive가 추가하는 필드의 정확한 이름은 소스와 대조하여 원본 testplan 정의 필드만 whitelist할 수 있다. 의도는 raw v3 검증 관련 입력과 같은 canonical 값이다. 시간 경과로 파생 status가 바뀌어도 digest는 불변이다.
