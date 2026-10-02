# 2026-10-02 중앙 관리 v3 진행

목표/위임/개인 프로젝트·계획/테스트 선정 이유/버전·runner 시도·막힘·Kit 개선·선택 Graphify를 구현 중입니다. 최신 검증은 specs/ai-pms-management/verify_management.py이며 배포 및 실제 화면 인수까지 현재 턴에서 진행합니다. 이전 릴리스 증거는 최신 목적 전체 완료 증거가 아닙니다.

# 2026-10-01 공개 연결 근거 릴리스

- 사용자 승인에 따라 MCP v2 로그, 중앙 검증, 다수 사용자 프로젝트 대시보드와 Kit 한·영 안내를 구현했습니다.
- 공개 GitHub: https://github.com/heejunyoo/ai-pms
- 새 앱: https://ai-pms-dashboard.vercel.app ; 보고서: /report.html
- 기존 Kit: https://harness-kit.vercel.app/ai-pms.html (영어: ai-pms-en.html), 새 앱 연결과 개선된 activity ZIP.
- 정본은 이 작업 폴더 및 ~/.claude/harness의 canonical sources. 공개 복사본은 별도 ai-pms-public Git 저장소로 개인 설정/원본 home Git 이력을 포함하지 않습니다.
- 현재 검증은 specs/ai-pms-connectivity/verify_release.py와 release-proof.json, 공개 복사본 scripts/verify_public.py. 예전 해시 영수증은 역사적 자료입니다.
- 실제 앱 훅 전달, Cursor/Gemini 어댑터, 모르는 사용자 PC 자동 수집, 운영 인증/수신 서버 연결은 후속 범위입니다. 합성 호출 완료를 실제 DB 접근 감사로 승격하지 않습니다.

---

# 다음 세션 — 중앙 AI PMS 구현

## 최신 완료 — 2026-10-01 자동 수집 제외 중앙 프로젝트 대시보드

사용자는 “자동수집 부분은 이후 고민해도 될 문제… 나머지를 구현하고, 대시보드까지 완성하자.”라고 범위를 지정했습니다. 아래 이전 순서의 자동 수집/승인 B 작업을 다음 필수 과제로 되살리지 않습니다.

- `specs/ai-pms-dashboard/`에 로컬 store+catalog → 지속 프로젝트 모델 → 자기완결 HTML 대시보드를 구현했습니다. source/spec 독립 검토 후 data-model/UI를 분리 위임했고 부모가 반환·Phase 검사·실제 화면을 인수했습니다.
- 명시적 연결로 여러 환경/세션을 한 프로젝트에 연결하고, 다른 사용자 동일 UUID는 분리합니다. 문서 버전/본문·단계·세션·원본 근거, 전체/단계/작업 검사, 현재 revision 완료·실패·재검증·미관측을 표시합니다. 기준 정의 변경 시 옛 완료 이력은 변경 전 snapshot으로 보관합니다.
- 현황 검색·사용자/상태/단계 복합 필터, 상세4탭, hash/back/초점, JSON 가져오기·붙여넣기·내보내기와 빈 상태를 구현했습니다. native file picker는 검증 도구 확장의 권한 때문에 미검증입니다. 권한을 변경하지 않고 공통 applySnapshot 경로를 정상 붙여넣기 UI에서 실제 확인했습니다. 실제 내보낸 JSON도 현재 snapshot과 동등합니다.
- 부모 actual Chrome: 현황→상세→문서v1/v2→세션→원본, 복합 필터/검색없음/초기화/뒤로가기, 완료·실패·재검증·미관측, 오류 유지/빈·정상 교체/취소, export JSON 파일, 390px 현황/본문/원본/모달을 확인했습니다. ELI20 보고서도 새 목적·완료 판정으로 개정하고4상태/Enter/390px/대시보드 링크를 확인했습니다.
- 독립 검토에서 null-run UI 불일치, 시각순서, 문서 귀속 우회, 개인정보 패턴/입출력 한도 차이, 단독 검사 세션 누락과 버튼 대비/버전 표시를 수정했습니다. `code-review.md/json`은 현재 소스 해시를 연결합니다.
- 최종 `python3 specs/ai-pms-dashboard/verify_dashboard.py` **exit0**. 모델16tests, UI26반례+공통import처리/JS syntax, 기존central2tests, handoff/생성모델·HTML/저장된 부모 관측의 해시를 확인합니다. 새 브라우저 자동실행 명령은 아닙니다.
- 바로 보기: `specs/ai-pms-dashboard/evidence/dashboard.html`; 안내 `README.md`; 인수 `acceptance-evidence.json`. 보고서 `reports/ai-pms-eli20/index.html`, 새검증 `verification.json`; 이전 보고서 검증은 `verification.transport-history.json`으로 보존했습니다.
- 완료 범위 `offline_dashboard_complete=true`, `automatic_collection_deferred=true`. 실제 다중 PC 자동 전달과 원격 서비스 배포는 미검증/미실행입니다. 새 API·DB·배포·글로벌 훅을 바꾸지 않았습니다.

**이어가기:** 사용자가 요청하는 대시보드 UX/실제 로컬 입력 적용을 우선합니다. 자동 수집 및 운영 연결은 후속 요청의 구체 범위로 별도 다룹니다. 로컬 개발 미리보기 `python3 specs/ai-pms-dashboard/preview_server.py`는127.0.0.1의 지정된 생성 화면/참조 문서만 제공합니다. 현재 세션에서 사용자 확인을 위해21931포트 미리보기를 남겼습니다. 환경이 바뀌면 실행 여부를 확인하고 재시작합니다.

## 이전 설계 순서 — 2026-10-01 사용자 목적 재확인

`PRODUCT-INTENT.md`와 함께 `PRODUCT-CLARIFICATION.md`를 먼저 읽습니다. 다수 사용자의 다수 세션을 지속되는 솔루션/프로젝트로 연결하고, 목표·단계별 문서·진행·완료 기준 충족 상태를 중앙에서 보여주는 것이 목적입니다. Kit의 계획·결과·검증 기록을 자동 연결하며 설정된 프로젝트 완료 테스트 통과는 완료 판정에 사용할 수 있습니다. 작업/단계 검사와 프로젝트 전체 검사의 범위, 검증 대상 버전은 구분합니다.

**다음 순서:** 이 목적에 맞게 프로젝트 연속성, 문서·계획·검증 수집, 현황/상세 화면을 설계하고 ELI20 보고서를 개정합니다. 관리 개입 목록만으로 목적을 좁히지 않습니다. 기존 로컬 전송 인수는 유효한 기반이지만 위 제품 의미의 구현 증거는 아닙니다. 아래 승인 B 실환경 전달은 그 이후의 운영 단계이며 자동 실행하지 않습니다. 새 API 계약 등은 구체 설계 이후 승인 경계를 적용합니다.

## 최신 완료 — 2026-10-01 승인 A 로컬 자동 전달 인수

- `specs/ai-pms-transport/approval.json`에 사용자 승인 A 원문과 범위가 있습니다. 아래 준비 단계의 API 미승인 표기는 이전 상태입니다. A는 로컬 sender/receiver/API·합성 loopback·중앙 전달 상태 화면을 포함하며 외부 전송/배포·전역 훅/trust·실제 자격은 제외합니다.
- 세부 구현은 수신·집계(T1), 송신·재시도(T2), 중앙 전달 화면(T3)로 원자화해 handoff로 이관했습니다. 부모는 T1 Phase 검사 후 T2/T3를 병렬 발행했고 각 반환 계약·검사를 직접 확인했습니다. 역할·이관 조건은 transport `DELEGATION.md`에 있습니다.
- stdlib sender/receiver/common, 인증 context·프로젝트 귀속, 영속 immutable inbox와 ACK, 재시도·ACK 분실·상태 checkpoint 복구, 독립 전달 metadata와 중앙 렌더 연결을 구현했습니다. 기존 logger와 글로벌 훅·Kit·DB·배포는 변경하지 않았습니다.
- 부모 실제 HTTP 통합은 같은 프로젝트 UUID의 두 합성 사용자 context → 중앙 10이벤트를 확인했습니다. 등록 4개 중 Carol은 heartbeat만, Dave는 수신 없음입니다. 재시작 중복 방지/본문 충돌 원본 보존/정확한 payload hash와 reason 귀속, 저장 HTML·영수증의 임시 경로/자격 유출 검사도 통과했습니다.
- 독립 코드 검토의 실제 결함(새 디렉터리 parent fsync, HTTP 기본 오류 노출, 손상 registry의 서버 오류 분류, 중앙 파일 한도, nested store 손상 traceback)을 수정하고 대응 반례를 검사했습니다. 최신 검토는 `specs/ai-pms-transport/code-review.md`입니다.
- 현재 코드로 재생성한 HTML을 부모가 실제 Chrome에서 목록→상세→관계→원본, 검색, heartbeat·빈 등록, 충돌, 전달상태 불명/중앙 저장 실패, 빈 상태, 390px 가로넘침 없음까지 확인했습니다. generation 영수증은 현재 코드 tuple과 HTML을 묶고 browser-observation은 해당 generation hash를 참조합니다.
- 부모 최종 `python3 specs/ai-pms-transport/verify_transport.py` **exit 0**. handoff plan/results, 신규 3종·기존 중앙 검사, 실제 합성 HTTP를 재실행하고 현재 코드/저장 화면/부모 관측 해시를 확인합니다. 새 브라우저나 실제 앱 훅을 자동 실행하는 명령은 아닙니다. sandbox local bind가 막히면 해당 명령의 실행 권한이 필요합니다.
- 인수: `specs/ai-pms-transport/acceptance-evidence.json`. 실행·데모: transport `README.md`. 요청한 ELI20 보고서: `reports/ai-pms-eli20/index.html` — 외부 리소스 없는 한 파일이며 5개 시나리오의 카드 변화/키보드/390px를 실제 확인했습니다. 배포하지 않았습니다.
- `api_implementation_approved=true`, `local_loopback_verified=true`, 실제 두 사용자 앱 전달 및 제품 완료는 계속 false입니다. 집계·HTML 렌더는 별도 CLI이며 자동 서비스/실시간 웹 운영은 구현하지 않았습니다.

**다음 순서:** 승인 B의 중앙 HTTPS 목적지·운영 호스트와 서로 다른 실제 두 참여자 환경/동의, 자격·관리자 접근·수집/보관 범위를 구체화합니다. 사용자에게 목적지와 참여 환경 정보를 요청해 두었습니다. 이후 구체 범위 승인 → 앱 훅/trust 배선 → 실제 앱 이벤트부터 중앙 원본까지 대조하는 `specs/ai-pms-delivery/RUNBOOK.md` 인수 순서입니다. A 승인으로 외부 운영을 실행하지 않습니다. 현재 정본은 transport spec/plan/README이며 아래 준비 상태는 이전 이력입니다.

## 이전 진행 상태 — 2026-10-01 실환경 전달 승인 전 준비

- `specs/ai-pms-delivery/spec.md`에 환경별 인증 귀속, 영속 inbox ACK, offline/retry/충돌, 집계와 독립된 상태 저장/화면 표시, 개인정보 및 A/B 승인 경계를 제안으로 고정했습니다. 원문/명세 독립 검토 후 handoff 준비 패킷을 발행했습니다.
- 준비 검사 `check_preparation.py`, 실제 앱 관측 절차 `RUNBOOK.md`, 구체적 승인 범위 `APPROVAL.md`를 작성했습니다. 지정한 전역/프로젝트 설정 8개에서 알려진 logger 경로+hook 토큰 후보는 0개입니다. 플러그인/managed/기타 레이어, trust/실제 앱 이벤트는 미조사이며 활성 여부의 전체 결론이 아닙니다.
- 다음 실행은 **승인 A 확인 후** 로컬 stdlib sender/receiver 및 `POST /v1/events`, inbox/집계 상태와 중앙 렌더 연결 구현, 합성 loopback 장애/신원/중복 반례 및 부모 화면 인수입니다. API 계약 변경 Ask-Before-Act에 따라 승인을 기다립니다. 구체 범위: `specs/ai-pms-delivery/APPROVAL.md`.
- 외부 목적지·두 실제 참여자의 동의·실제 자격·앱 훅/trust·배포는 별도 승인 B입니다. 현재 API 구현 승인=false, 실제 전달=false, 제품 완료=false. 기존 logger/central 코드는 보존했습니다.
- 부모 최종 `verify_preparation.py` exit 0 및 독립 코드/문서 재검토 완료. 영수증: `specs/ai-pms-delivery/preparation-evidence.json`, 검토: `preparation-review.md`.
- 실행: `python3 specs/ai-pms-delivery/verify_preparation.py`. 준비 문서/검사/검토의 저장된 해시와 보호 코드 및 false 플래그를 확인하는 관문이며, API/네트워크/실사용자 전달 검사가 아닙니다.

## 이전 구현 상태 — 2026-09-30 로컬 중앙 흐름 인수 완료

- `specs/ai-pms-central/`에 stdlib 중앙 import/render CLI, 소유자 전용 파일 저장/집계, 관리자 목록/관계/원본 화면을 구현했습니다. 기존 글로벌 logger·훅·Kit·API 계약·DB·배포는 변경하지 않았습니다.
- 두 합성 사용자/환경을 중앙에 수집해 2출처·8이벤트·2프로젝트를 확인했습니다. 동일 project UUID라도 actor/environment별로 분리합니다. 재수집 후 8이벤트가 유지됩니다.
- 부모가 실제 Chrome에서 목록 → 상세 → Agent/산출물/검사/인수 관계 → 원본 JSON/해시/행 번호, 사용자 검색, 빈 상태, 390px 모바일을 확인했습니다. 모바일 원본의 가로 넘침을 발견·수정하고 동일 경로에서 문서 폭 390px으로 재확인했습니다.
- 관리 예외 합성 화면은 목표 없는 도구 작업/Phase 불명/미래 관측/입력 미도착/산출물 검증 불일치/수집 지연을 드러냅니다. 도구 완료와 검사 pass를 프로젝트 완료로 승격하지 않습니다.
- 원문/명세 독립 검토, 하위 모델 구현, 독립 코드 재검토, 부모의 최종 `verify_acceptance.py` 관문을 통과했습니다. 인수 영수증은 `specs/ai-pms-central/acceptance-evidence.json`, 자세한 관측은 `evidence/browser-observation.md`입니다. 코드 리뷰는 실제 두 사용자 전달/제품 완료 승인이 아닙니다.
- 실행: `python3 specs/ai-pms-central/verify_acceptance.py`. 저장된 HTML/관측 해시와 구현 테스트를 재검증하며, 새 브라우저 실행이나 실환경 전달 검사 명령은 아닙니다. 데모: `specs/ai-pms-central/evidence/preview/dashboard.html`; 관리 예외: 같은 폴더의 `audit.html`; 안내: `specs/ai-pms-central/README.md`.

**여전히 미완료:** 실제 서로 다른 두 사용자 환경의 앱 훅 → 로그 → 자동 전달 → 중앙 근거, 인증/접근 제어, 중앙 서비스 운영·배포. `actual_multi_user_delivery_verified=false`, `product_complete=false`입니다. 현재 글로벌 Codex/Claude 설정에서 activity logger 연결과 기본 로그 디렉터리를 찾지 못했으며 프로젝트/다른 경로 전체를 조사한 결론은 아닙니다(`runtime-observation.md`).

## 이전 준비 실행 순서 — 승인 A 인수 전 이력

1. **실환경 전달 명세 준비(완료):** 기존 두 출처 로컬 집계/관리 화면을 보존하고 전송 목적지, 사용자·환경의 인증/등록, 전달 acknowledgment, offline/retry/중복·충돌, 개인정보/보관 범위를 구체화합니다. 새 DB/API 계약/외부 API/배포·인프라 실행은 Ask-Before-Act이므로 먼저 로컬 명세·검토·구현 준비를 구체적으로 끝내고 필요한 승인만 요청합니다.
2. **현재 앱 훅 전달 관측 준비(절차 작성 완료, 실행 미승인):** logger 직접 stdin 검사가 아닌 앱 내 실제 도구 실행으로 event ID를 확인할 절차와 보완 입력 출처를 정의합니다. 글로벌 설정을 조용히 설치하거나 trust를 자동 승인하지 않습니다.
3. **승인 A 확인 후 전송 방식 구현:** 원문→새 명세 독립 검토 후 handoff 패킷을 발행합니다. 합성 중앙 파일 가져오기를 자동 전달 완료로 표현하지 않습니다. 로컬 익명 actor/environment 입력은 실제 사용자 인증으로 재사용하지 않습니다.
4. **실제 두 사용자 환경 인수:** 동의된 두 환경의 실제 앱 이벤트를 중앙 저장/집계/관리자 원본까지 대조하고 identity/누락/지연/재시도·중복을 관측합니다. 성공 증거가 생길 때만 실제 전달 상태를 바꾸며 중앙 제품의 나머지 운영 경계도 별도로 확인합니다.

## 시작 지시

`PRODUCT-INTENT.md`를 먼저 읽고 이 프로젝트를 이어가세요. 여러 사람이 각자의 환경에서 남기는 공통 로그를 중앙에서 모아, 목표·중간 단계·범위 변경·Agent·결과물·검증·관리 필요 사항을 파악하는 제품입니다. 개인용 작업/검토 UI의 추가 개발을 다음 단계로 선택하지 마세요.

상위 모델은 제품 목적·설계 결정·독립 인수 검토를 담당하고, 세부 구현은 handoff로 하위 모델에 위임합니다. 사용자는 이 방식을 명시적으로 요청했습니다. 분석가 제안은 사용자 승인과 구분합니다.

## 정본과 이력

- `PRODUCT-INTENT.md`: 사용자 원문, 고정 목적, 중앙 흐름 인수 기준.
- `brief.md`: 최초 문제 정의. 처음부터 중앙 수집·시각화가 목적이었습니다.
- `AI-PMS-review.md`: 연구 결과. 개인 Phase 검토 제안은 분석가 가설이며 방향 변경 승인이 아닙니다.
- `specs/ai-pms-foundation/`: 공통 기록기 기반의 제한적 구현 이력.
- `specs/ai-pms-workflow/`: 잘못된 개인용 프로토타입 방향의 이력. 향후 제품 명세로 재사용하지 않습니다.
- `specs/handoff-intent-guard/`: 이번 보강의 명세, 독립 검토, 계획 및 배포 증거.

## 이전 세션 구현 경계 — 이력

재사용 후보는 `~/.claude/harness/activity/logger.py`의 개인정보 제한·동시 기록·식별·버전 처리와 테스트입니다. `viewer.html`은 개인용 오프라인 프로토타입입니다. 예제 JSONL은 합성 데이터이며 실제 사용자 전달 증거가 아닙니다.

중앙 서비스, 여러 사용자 환경의 실제 전송, 중앙 저장/집계, 중앙 관리자 화면은 아직 구현되지 않았습니다. 기존 로컬 테스트 통과 또는 Kit 배포를 중앙 AI PMS 완성으로 표현하지 않습니다. 기존 글로벌 훅의 실제 도구 실행별 전달 증거도 미확인입니다.

## 이전 세션 실행 순서 — 로컬 흐름은 위 최신 상태 참조

1. **현재 기록 계약 조사**: logger와 foundation 명세를 읽어 actor/environment/project/session/event 식별, 목표·Phase·결정·Agent·산출물·검증 참조를 대조합니다. 훅에서 알 수 없는 목표·판단은 출처가 있는 보완 입력으로 기록하며 추정으로 확정하지 않습니다. 원문/명세 독립 검토 후 요구사항별 작업 패킷을 만듭니다.
2. **중앙 수집의 최소 흐름 구현**: 먼저 로컬 중앙 집계 경로로 서로 다른 두 사용자 환경의 기록을 모읍니다. 식별 충돌, 중복 수집, 수집 지연, 잘못된 연결을 보이는 최소 구현을 선택합니다. 파일 가져오기는 중앙 집계 검증의 출발점이며 실제 자동 전달의 완료 증거가 아닙니다. 실제 전송 방식은 명세에서 확정합니다.
3. **중앙 첫 화면 구현**: 여러 프로젝트의 사용자·목표·현재 Phase·최근 범위 변경·Agent/결과물·관리 필요 항목을 한 화면에서 비교하고, 프로젝트 → 연결 근거/원본 기록으로 내려갑니다. 모든 개인 목표가 하나의 조직 목표에 속한다고 가정하지 않습니다. 누락·지연은 별도 표시합니다.
4. **중앙 흐름 검증**: 두 출처 → 중앙 집계 → 다중 프로젝트 목록 → 프로젝트 근거 상세를 실제로 실행합니다. 합성 데이터와 실제 사용자 환경 전달을 따로 기록합니다. 목표 없는 작업, Phase 불명, 산출물 검증 불일치, 수집 지연에서 관리자가 무엇을 확인해야 하는지 검증합니다.

새 DB 스키마·신규 외부 API·API contract 변경·새 배포/인프라는 환경의 Ask-Before-Act 규칙에 따릅니다. 로컬 조사·명세·리뷰·되돌릴 수 있는 구현 준비는 계속 진행할 수 있습니다. 승인 경계를 이유로 제품 목적을 개인용 도구로 바꾸지 않습니다.

## 이번에 보강한 handoff 사용법

Codex: `~/.agents/skills/handoff/`, Claude: `~/.claude/skills/handoff/`.

계획에 원문 출처와 인용된 요구사항, 독립 검토 기록, 작업별 `requirement_ids`, 원래 목적의 인수 명령을 포함합니다. 검토자는 원문과 명세를 실제 대조합니다. 검토 이후 원문/명세가 바뀌면 해시가 달라져 계획·패킷 발행이 막히므로 재검토합니다.

검증기는 검토 누락·오래된 해시·요구사항 누락을 차단합니다. 리뷰어 문자열과 해시만으로 사람/에이전트의 독립성이나 의미 정합성이 증명되지는 않습니다. 부모가 독립 검토와 실제 중앙 흐름 인수 기준을 확인해야 합니다.

검사: `python3 ~/.agents/skills/handoff/validate.py selftest` 및 Claude 경로 동일 명령. 새 계획은 `validate.py plan <plan.json>`, 패킷은 검증된 계획에서 `emit`합니다. 정확한 CLI는 해당 SKILL.md를 따릅니다.

## Kit 안내와 배포

- 공개 사이트: https://harness-kit.vercel.app/handoff.html
- 정본 생성기: `~/.claude/harness/build/current_content.py`
- 절차: `~/.claude/harness/build/BUILD.md`
- 배포 증거: `specs/handoff-intent-guard/release-evidence.json` (배포 후 작성)

Kit는 기록/위임을 위한 기반입니다. 이 사이트 업데이트는 중앙 AI PMS 관리자 제품의 배포가 아닙니다.

## 이번 세션 종료 확인 (2026-09-30)

- Codex·Claude handoff 설치 완료, 양쪽 기존/새 selftest 통과. 보호 경로 설치는 사용자의 샌드박스 승인을 받았습니다. 원본 백업은 `specs/handoff-intent-guard/backups/`에 있습니다.
- Kit 빌드에서 34개 페이지·언어 대칭·기존 경로·개인정보 제한·번들·실제 번들 검증기 검사를 통과했습니다. 필수 Codex/Claude 하네스 검사도 빌드 관문으로 실행되었습니다.
- 배포: `https://harness-9tco29le4-luckyhyun.vercel.app`, 공개 별칭 `https://harness-kit.vercel.app`.
- 공개 한국어/영어 handoff HTML, implementation ZIP, 두 언어 참고 ZIP을 실제 다운로드했고 로컬 배포 파일과 SHA-256이 모두 일치합니다. 브라우저에서 한국어 목적 보강 영역과 영문 안내를 확인했습니다. 모바일 렌더 검증은 별도 실행하지 않았습니다.
- 독립 검토자가 원문·명세 정렬을 승인하고 실제 코드 결함을 지적했습니다. 검토자와 구현 하위 모델이 사용량 한도로 종료되어, 마지막 비정상 입력 수정과 최종 코드 확인은 부모가 마무리했습니다. 이 경계는 `code-review.md`에 기록되어 있으며 독립 최종 코드 재승인으로 표현하지 않습니다.
- 재확인: `python3 specs/handoff-intent-guard/verify_release.py` (저장된 공개 다운로드/설치 증거를 재검증하며 새 배포의 실시간 확인 명령은 아닙니다).

이 문단은 이전 세션 종료 이력입니다. 로컬 중앙 수집 최소 흐름은 이후 구현·인수했으므로 다음 세션은 문서 맨 위의 **승인 A 확인 후 로컬 전달 구현**부터 시작하세요.
