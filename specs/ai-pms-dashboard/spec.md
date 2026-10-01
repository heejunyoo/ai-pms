# 중앙 프로젝트 대시보드 구현 명세

## 목적과 범위
다수 사용자·다수 세션을 프로젝트로 연결하고 목적, 단계별 문서/결과물의 변화, 설정된 완료 기준 충족 상태를 중앙에서 본다. 자동 수집은 후속이다. 기존 central.py와 sender/receiver 및 그 테스트·계약은 변경하지 않는다. stdlib Python + 외부 리소스 없는 HTML/CSS/JS로 로컬 파일에서 동작한다. 새 API/DB/배포/글로벌 훅은 없다.

## 실제 기반
- specs/ai-pms-central/central.py: source_key는 actor/environment/project; store.sources의 각 entry.events[event_id]는 event와 received_at/file_sha256/line 근거를 가진다.
- sample/manifest.json: 서로 다른 actor가 같은 UUID를 써도 별개 출처이다.
- 기존 중앙 test_central.py 2 tests exit0. 새 test_portfolio.py는 파일 없음으로 exit2; 아직 새 구현이 없다는 기준선이다.
- Kit plan.goal/spec_ref/phases 및 result.acceptance_run은 이후 자동 수집 출처가 될 수 있으나 이번에는 명시적 로컬 catalog 입력으로 대체한다. 목표와 검사 결과를 자동 관측했다고 표현하지 않는다.

## 확정 설계
새 파일 specs/ai-pms-dashboard/portfolio.py는 기존 central JSON과 로컬 catalog JSON을 읽어 아래 정규화 view model을 생성하고 dashboard.html 템플릿에 포함한다. 기존 저장 형식은 그대로이다. 별도 catalog는 오프라인 사용자 제공 메타데이터이며 네트워크 API 계약이 아니다.

catalog={version:1,projects:[...]}; project 필드: id,name,goal,current_revision,current_phase,source_refs:[{actor_id,environment_id,project_id}],phases:[{id,name}],documents:[{id,title,kind,version,phase_id,at,session_id,actor_id,environment_id,summary,content}],criteria:[{id,label,scope:'project'|'phase'|'task',target_id,command,expected_exit_code}],runs:[{criterion_id,revision,at,exit_code,session_id,evidence}]. 모든 배열은 필수이나 비울 수 있다. goal/name/content는 명시적 입력이며 source catalog 근거를 표시한다. criterion target_id는 project scope면 project.id, phase scope면 존재하는 phase.id; task scope는 별도 작업명 식별자(프로젝트 완료로 승격 금지). source_refs의 완전 일치로만 여러 환경을 연결한다. 하나의 source를 둘 이상의 프로젝트로 매핑하면 오류. 다른 사용자의 같은 UUID를 자동 병합하지 않는다. 매핑되지 않은 출처도 누락하지 말고 fallback 프로젝트로 표시한다.

완료는 필요한 project scope criteria가 하나 이상이고 현재 revision의 각 criterion 최신 run이 모두 expected_exit_code와 일치할 때 complete. 현재 revision 실패는 failed. 이전 revision에서 전체 조건을 만족했으나 현재 검사가 부족하면 revalidation. 나머지는 in_progress; project criteria 없으면 unknown. 검사 결과는 가져온 기록이고 실행 명령은 절대 실행하지 않는다. 동일 시각의 상충 run은 불명으로 취급하고 오류/alert를 표시한다. 기준이 바뀌면 이전 결과를 새 기준에 자동 적용하지 않도록 criterion 정의의 fingerprint를 모델에서 설명하거나 입력 변경 시 검사 재입력 필요를 명시한다. catalog 기준 변경 후 예전 기록의 적용을 막는 최소 구현으로 runs에 criterion_signature를 넣고 signature=sha256(canonical criterion)로 검증한다(샘플/문서에 생성법 제공). runs 필수에 criterion_signature 추가.

phases 상태도 해당 phase scope 검사로만 계산한다. 단계 수 기반 완료율은 사용하지 않는다. 과거 완료 milestones는 timeline에 보존한다. 최신 document.version/phase/session 출처와 이전 버전을 탐색할 수 있어야 한다.

## 정규화 view model (Python과 화면 공유)
{schema_version:1,generated_at:UTC,evidence_mode:'synthetic'|'local-execution'|'declared'|'mixed',projects:[project]}
project={id,name,goal,owners:[str],current_revision,current_phase,status,status_reason,phases:[{id,name,status}],documents:[위 catalog 문서 + source_ref],criteria:[위 기준],runs:[위 run + status:'pass'|'fail'|'unknown',source_ref],sessions:[{id,actor_id,environment_id,event_count}],timeline:[{at,kind,title,detail,session_id,source_ref}],sources:[{actor_id,environment_id,project_id,evidence_mode,event_count}],alerts:[str],last_updated:UTC|null}.
status enum complete/revalidation/failed/in_progress/unknown. 모든 project 키 필수. sort timeline ascending deterministic. catalog refs use 'catalog.projects[0]...' 등 상대 논리 경로, event refs include actor/environment + event_id/file_sha256/line, 원본 event JSON은 timeline detail 안 text로 열 수 있다. private local 절대경로/secret 토큰은 reject하며 HTML/JS 삽입을 escape하고 브라우저 DOM에는 textContent로 출력한다. 입력 파일 한도/배열·텍스트 한도/enum/시간/중복 ID/참조 검증과 malformed JSON 오류를 간결하게 제공한다. 현재 관측시각보다 미래 기록은 완료로 승격 금지하며 alert.

CLI: python3 specs/ai-pms-dashboard/portfolio.py --store CENTRAL_JSON --catalog CATALOG_JSON --out OUTPUT_HTML --json-out OUTPUT_JSON. --store/--catalog 없으면 빈 프로젝트도 처리한다. 읽기만 한다. HTML은 같은 폴더 dashboard.html의 <script id="pms-data" type="application/json"> 안 초기 JSON을 생성 모델로 교체한다. script-end injection을 막아 '<' '\u003c' 등으로 escape. template는 독립 오픈시 empty state; generated preview는 실제 모델 embedded. browser에서 정규화 모델 JSON 파일을 선택하면 재렌더, 실패하면 기존 데이터 유지 + 접근가능한 오류. JSON 내 status를 검증하되 입력은 이미 산출된 snapshot이라는 안내. 브라우저는 자체 raw catalog 기준 판정을 중복 구현하지 않는다.

## 화면
깔끔한 한국어 중앙 현황: 제목/설명, 데이터 가져오기·현재 snapshot JSON 내보내기, synthetic/수동 가져오기 상태; 프로젝트 수·사용자 수·완료/재검증/진행 상태; 검색 및 사용자·상태·단계 filter; 사용자/솔루션/목적/현재 단계/최근 문서/검사 상태/세션 수/최근 변경을 비교하는 카드 또는 목록. 검색/filter 복합 적용과 결과 없음/reset.
상세에는 목표와 출처, 단계·검증, 문서 버전 및 내용, 세션·환경, 시간 흐름과 원본 근거를 탐색하는 탭/영역. 상세를 닫으면 필터 보존하고 trigger로 focus 복원. deep link 프로젝트 hash와 browser back 지원. 완료/재검증 이유와 대상 revision/command/evidence 표시. unknown과 미관측을 완료와 구분. 이벤트 건수로 생산성 순위·진행률을 만들지 않는다.
390px에서 가로 넘침 없이, semantic controls/label/aria-selected, 키보드/최소44px touch, 대비·focus visible. external fetch/resource 없음. demo를 실제 사용자로 표현하지 않는다.

## 샘플·인수
샘플 store+catalog로 Alice 프로젝트가 2환경 3세션에 연결, Bob은 같은 UUID 별개 프로젝트, Carol은 과거 완료 후 새 revision으로 재검증, 추가 기준 없음 프로젝트를 보여준다. 최소 PRD→설계→구현 문서 이력과 version2 내용, 단계 완료와 프로젝트 전체 완료의 차이, 실패/미관측을 포함한다. sample 생성기는 기존 central.valid_event를 사용하여 event 입력 형식 회귀를 막는다.
의미 검사는 sample+malformed/conflicting identity/current revision freshness/criterion signature/future run/wrong scope/empty/HTML injection을 포함한다. 부모 실제 브라우저는 목록→상세→문서 변경→세션→원본, 모든 filter, JSON import 오류 유지/정상 교체/내보내기, 뒤로가기와 390px를 확인한다.

## 분업
data-model: portfolio.py, test_portfolio.py, sample/ 전용. dashboard-ui: dashboard.html, check_ui.py 전용. 부모: spec/plan/verification/README/report/통합. review agent는 원문/명세 검토와 최종 변경 독립 검토(본인 구현 없음). 데이터와 화면은 위 model 기준으로 병렬 가능하다. 외부 목적지 등 미해결 판단 없음.

## 독립 검토 후 연결 보완
central에 관측되지 않은 catalog 출처는 evidence_mode=declared, event_count=0으로 유지하고 관측 없음 alert를 표시합니다. catalog-only 입력도 사용할 수 있으며 실행된 기록/합성으로 임의 분류하지 않습니다. 혼합 출처는 mixed입니다. 최종 view model은 최대1000프로젝트·각 배열10000개·canonical JSON 6MB로 제한하여 UI importer 한도8MB 및 텍스트총량6M과 일치시킵니다. JSON 내보내기는 compact하여 다시 가져올 수 있습니다. null exit_code는 unknown이며 화면에서 미관측으로 표시합니다. 시각 정렬은 UTC parsed instant를 사용하고 단독 검사 세션은 출처 미관측 alert를 남깁니다.
