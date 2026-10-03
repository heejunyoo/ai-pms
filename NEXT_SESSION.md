## 최신 완료 — 별도 페이지 IA와 사람이 행동할 수 있는 상세

사람/프로젝트 최소 목록 → 하나의 공동 프로젝트 WBS → 하나의 작업/단계/최종 완료 상세를 별도 hash 주소로 구현했습니다. 목록은 차트를 쌓지 않으며 작업 상세는 지금 할 일·담당/요청·막힘 이유·완료 조건 네 항목을 먼저 보여줍니다. Alice/Bob 공동 예시는 실제 선언된 책임/위임 기준이며 Bob의 중복 정책 합의 작업을 명시했습니다. 검증/문서는 접힌 근거로 유지하고 nested 펼침·summary 포커스는 증분 갱신에도 유지합니다.

최신 정본/영수증: specs/ai-pms-action-detail/{source.md,spec.md,plan.json,code-review.json,browser-observation.json,release-proof.json,public-bytes.json}. Astra 최종 pass, 공개 portable suite 및 추가 nested regression pass. 실제1440/390 화면, native history/reload/계획복귀, 공동 계획/사람scope, 브라우저 direct synthetic delta 근거/focus 확인. Dashboard/Kit 공개 배포 READY 및44파일 바이트 일치 확인. README/ELI20/Kit 한영 및 ZIP 갱신 완료.

공개 https://ai-pms-dashboard.vercel.app/#project=alice-recall&task=action-3 은 합성 읽기 전용 샘플입니다. 실제 provider hook 신뢰와 두 사용자 원격 private 전달은 계속 false이며 전체 제품 완료가 아닙니다. 모바일 가로 사람목록의 자동화 offscreen pointer 타겟은 불안정했고 실제 keyboard focus/Enter 경로로 Bob2프로젝트 확인했습니다. 새 작업에서 실제 중앙 운영 인수는 기존 Live README 경계대로 별도 검증합니다.

아래 WBS/inline 기록은 이전 이력이며 최신 별도 페이지 인수를 대체하지 않습니다.

## 최신 진행 — WBS/timeline 시각 재구현

사용자는 기존 Phase 화살표 카드를 시각적으로 부족하다고 거부했습니다. `specs/ai-pms-wbs-timeline/` 정본을 따릅니다. TeamGantt 계층형 작업표 + Linear milestone 구성을 참고해 WBS 행/담당/상태와 오른쪽 Gantt를 정렬하고 task/Phase 하단 상세를 제공합니다. 공개 날짜는 명시적 가상 schedule fixture이며 exact synthetic project/plan/revision 연결; 실제 일정 없는 입력은 Phase축입니다. 원래 목표와 완료 계산을 유지합니다.

새 check_timeline + 기존 check_flow + 전체 공개 suite 통과, Astra 최종 코드 검토 pass. 실제1440/390 화면·막대/diamond 클릭·키보드 복귀·Bob scope 확인. 모바일400→증분400→reset400 실제 브라우저 확인. 공개 Dashboard/Kit READY 및44파일 byte대조 pass. 최신 인수는 specs/ai-pms-wbs-timeline/{release-proof.json,browser-observation.json,code-review.json}. 실사용자 원격 전달은 계속 false입니다.

아래 Phase flow 배포는 이전 이력이며 이번 디자인 인수 증거가 아닙니다.

## 최신 화면 개편 — WBS/Phase flow

사용자가 초기 WBS/Gantt 의도가 구현에서 누락되었다고 지적했습니다. UI 수정은 `specs/ai-pms-phase-flow/{source.md,spec.md,plan.json}` 정본과 별도 독립 검토에 따라 반영했습니다. 사람별 프로젝트 목표→모든 Phase→최종 완료 확인 그래프가 primary이며 클릭 하단 상세가 작업/완료 조건/검사 근거를 제공합니다. 이전 나열식 IA를 현재 목적 달성 증거로 사용하지 않습니다. 실제 일정 데이터 없이 Gantt 날짜/기간을 추정하지 않습니다.

`check_flow.py`와 공개 전체 검사 통과. 부모가 실제 headless Chromium에서 사람 필터, 전체 Phase 유지, 단계 상세/담당 작업 강조, 키보드 Enter/Space와 포커스 복귀, 1280px 및390px 가로 넘침 없음을 확인했습니다. 모바일 화살표가 클릭을 가리는 문제는24px 폭으로 수정했고 공개 배포에서 단계/최종 노드 실제 클릭을 재검증했습니다. 최신 배포/브라우저 영수증은 `specs/ai-pms-phase-flow/release-proof.json`과 `browser-observation.json`에 있습니다. 실사용자 원격 전달은 계속 미검증입니다.

이전 실행/배포 기록은 아래와 같습니다. 최신 flow 인수 및 release-proof를 확인하세요.

## 최신 구현 — 사람·세션·북극성·Live 중앙 운영

최신 정본은 `specs/ai-pms-live/README.md`와 spec/plan입니다. 사람 → 세션 → 목표/종료/현재 검증·인수 → Phase/작업/테스트·문서, 회사·팀 지표와 제안/확인 기여를 구현했습니다. 기술 완료와 업무 성과를 분리합니다. 캡처 health, private writer/manager 인증, entity별 durable ACK, 원문 기록 이력, cursor 증분 투영,2초 sender/화면 polling을 구현했습니다. Kit ZIP에는 실행 가능한 pms runtime과 operations JSON 템플릿/전체 필드 설명이 포함됩니다.

부모 `verify_live.py` 통과:44 operations/38 실제 로컬 HTTP/6 Kit 오류·경합 검사,38 snapshot Python-JS parity·DOM 갱신 검사, 명시적인 세션 목표/인수 기록,7개 합성 writer full pilot. logger CLI 이벤트 생성→중앙 모델 업데이트 약0.24초는 로컬 합성 검사입니다. 실제 앱 훅 호출이나 원격 전달 latency 증거가 아닙니다. 하네스 구성 verify.py도 통과했습니다.

Astra는 원래 목적/간극/초기 spec을 검토했습니다. 후속 acceptance binding은 비작성 독립 검토자가 확인했고 sync 최초 독립 검토 blocker를 부모가 수정·실행 확인했습니다. 에이전트 사용량 한도로 최신 sync 변경의 새 독립/Astra 재검토는 미완료입니다. DOM 검사는 실제 브라우저 렌더가 아닙니다. 당시 CUA 연결은 apps/browsers 빈 목록·native pipe startup failure였습니다. 이후 Phase flow 개편은 agent-browser로 실제 데스크톱/390px를 별도로 확인했으며 최신 영수증을 우선합니다.

**다음 운영 인수:** 실제 중앙 HTTPS 주소·서버/보관 정책·참여자 귀속·조회 권한을 정한 뒤 실제 두 사용자 환경의 native 앱 훅 생성→private sender ACK→중앙 원문/세션→브라우저 갱신을 같은 event ID로 대조합니다. 공개 Vercel은 합성 정적 앱이며 private 수신기가 아닙니다. 글로벌 훅/trust·실제 자격/로그는 자동 공개하지 않았습니다. Pilot 파일 저장은64MiB/10,000 receipts 한도이며 부하/운영 SLA 미검증입니다. `specs/ai-pms-live/release-proof.json`에 기존 주소 배포 READY와44개 공개 파일 바이트 일치를 기록했습니다. 이를 확인한 뒤 기존 이력을 현재 증거로 되살리지 마세요.

아래는 이전 상태 기록입니다.

## 최신 상태 — 2026-10-02 사람·세션·실시간 중앙 관리 재점검

최신 사용자 요청은 사람 → 세션 → 세션 목표/인수 → 회사·팀 북극성, 실제 훅 생성·로컬 실시간 확인·중앙 증분 전달·화면 갱신입니다. 이전 자동 PC 수집 유보는 최신 요청의 제외 근거로 사용하지 않습니다. `PRODUCT-INTENT.md` 마지막 정정과 `docs/person-session-live-gap.md`를 먼저 읽으세요.

Astra 독립 코드 검토에서 현재 세션은 ID/사람/환경/이벤트 수만 갖고, 목표/작업/테스트/승인은 전송되지 않는 별도 v3 JSON임을 확인했습니다. 수신 이후 집계는 별도 CLI이며 공개 화면은 수동 snapshot입니다. 토스 IA는 이 구조를 바꾸지 않았습니다. 현재 제품을 실시간 다중 사용자 PMS 완료로 표현하지 마세요.

이번 점검에서 sender/receiver 회귀 검사를 재실행해 통과했습니다. Astra synthetic logger 실험은 시작/턴 종료/세션 종료 기록과 저장 실패 시 exit 0을 확인했습니다. 실제 앱 훅 호출·실제 두 환경 원격 전달·현재 브라우저 렌더는 검증하지 않았습니다. 이번 변경은 목적·간극·인수 조건 문서이며 제품 구현이나 배포 변경은 없습니다.

다음 실행은 최신 목적 기준으로 세션/목표/기여 모델과 관리 변경까지 전달하는 계약을 구체화하고 독립 검토한 뒤, 기존 내구성 outbox/inbox와 검증 계산기를 재사용해 로컬 수집 상태 → 지속 집계 → cursor 조회 → 화면 갱신을 연결합니다. 원격 단계는 실제 목적지·참여자 귀속·조회 권한·TLS/자격 관리 경계를 정해 실제 두 환경으로 인수합니다. 과거 HTML/ZIP 바이트 검증은 이 경로의 증거가 아닙니다.

아래는 이전 이력입니다.

## 이전 상태 — 2026-10-02 토스 원칙 기반 IA 적용

첫 화면은 사람 선택 → 판단할 작업 → 프로젝트, 상세는 작업 현황·목표/판단·문서 중심으로 바꿨습니다. JSON·고급 필터·통계·MCP/세션 기록은 펼침에 유지하며 접힌 필터도 적용 수가 보입니다. 개입에서 정확한 작업으로 이동하고 키보드 초점을 복원합니다. 기존 데이터 모델 및 완료 판정은 바뀌지 않았습니다.

정본: `specs/ai-pms-toss-ia/`. 부모 `check_ia.py`, 공개 portable suite, 44개 production byte 대조 통과. https://ai-pms-dashboard.vercel.app 배포 완료. Astra는 목적 정렬과 코드 주요 경로를 검토하고 사람 카드 초점 P2를 발견했습니다. 수정 후 부모가 재검증했으며 최종 Astra 재승인은 사용량 한도로 미완료입니다.

다음은 실제 브라우저 데스크톱/390px 렌더, 사람 선택→개입→정확한 작업→근거→목록 초점 복귀, 더보기/필터 초기화, JSON 오류/내보내기 경로 확인입니다. 브라우저 도구 연결 실패로 이번 실제 화면 확인은 미완료입니다. 이전 UI receipt를 이번 IA의 현재 결과로 사용하지 마세요. 자동 PC 수집/실제 다중 사용자 전달은 계속 유예입니다.

아래는 이전 이력입니다.

## 최신 상태 — 2026-10-02 작업 관리 개편

사람 필터 → 공동/개인 목표 → Phase → 담당 원자 작업 → 완료 조건/검사/승인/막힘/다음 행동을 구현했습니다. Kit Handoff import와 update/review 명령, 작업 JSON 템플릿과 문서를 함께 추가했습니다. 새 코드 위치는 `specs/ai-pms-work-management/`입니다. Astra 최종 검토는 no_blockers입니다. `python3 scripts/verify_public.py` 및 실제 로컬 subprocess 검증이 통과했습니다.

대시보드와 기존 Kit는 공개 배포했습니다. 44개 공개 파일 바이트 대조를 통과했습니다. 자동 PC 수집과 실제 다중 사용자 전달은 계속 유예 상태입니다. 현재 화면은 합성 샘플입니다.

실제 로컬 브라우저에서 사람 필터·공동 프로젝트 책임 분리·3개 Phase·관리 행동·390px 상세·잘못된 JSON 거부/기존 상태 보존을 확인했습니다. 도구 연결이 끊겨 내보내기 다운로드, 모바일 목록/보고서, 배포 후 브라우저 및 Kit 한/영 실화면 확인이 남았습니다. `specs/ai-pms-work-management/browser-observation.md`와 `release-proof.json`을 확인하고 이 경계부터 이어가세요. `verify_work.py --release`는 남은 브라우저 확인을 통과로 기록할 때까지 실패해야 합니다.

아래는 이전 작업 이력입니다. 최신 승인과 상태를 덮어쓰지 않습니다.

# 2026-10-02 추가 완료 — 변경·판단·인계·기록 상태

Atlas-inspired four improvements are implemented as optional management.traceability, preserving old v3. New dashboardtab connects checkpoints/decisions/handoffs/capture. Kit checkpoint reads Git safely with explicit declared session/agent attribution; record imports decision/handoff/capture without promoting usage. Git roots excludeHOME; noGit works with nulls, unbornGit requiresinitialcommit; ignored/submodule content outofscope. Actual Git13checks, tracecontract19checks, legacy26, UI parity and malformedpreservation passed; actualproduction newtab/mobile/export verified. AutomaticPCcollection remainsdeferred. Currentcombinedreview is traceability-independent-review.json plus traceability-review.json; oldcode-review is historical. Currentacceptance command remains python3 specs/ai-pms-management/verify_management.py --release.

# 2026-10-02 중앙 관리 v3 공개 릴리스

목표/위임/개인 프로젝트·계획/테스트 선정 이유/버전·runner 시도·막힘·Kit 개선·선택 Graphify를 구현하고 공개 대시보드 및 한·영 Kit에 배포했습니다. 최신 검증은 `python3 specs/ai-pms-management/verify_management.py --release`; 현재 증거는 같은 폴더의 release-proof.json, browser-observation.md, code-review.json, public-bytes.json입니다. 공개 주소는 https://ai-pms-dashboard.vercel.app 및 https://harness-kit.vercel.app/ai-pms.html 입니다. 공개 소스 https://github.com/heejunyoo/ai-pms 의 templates/catalog-v3.template.json, docs/json-contracts.md 및 Kit ZIP activity/ 폴더에 템플릿·전체 필드 설명·실행 기록기가 있습니다.

실제 subprocess 실패→수정→통과→파일 변경 후 재검증을 로컬로 확인했고 선택 Graphify의 실제 생성 및 오래된 근거도 확인했습니다. 대시보드 샘플은 합성 사용자이며 업무 성과는 미관측입니다. Graphify는 필수가 아니며 전역 훅을 설치하지 않았습니다. 자동 다중 PC 수집·인증된 운영 서버·실제 앱 훅 전달·Cursor/Gemini 어댑터는 후속 범위입니다. native file chooser는 미검증이며 JSON 붙여넣기 경로와 공개 앱에서 내보낸 v3 JSON의 snapshot 동일성은 실제로 확인했습니다. 이전 릴리스 증거는 최신 목적 전체 완료 증거가 아닙니다.

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
