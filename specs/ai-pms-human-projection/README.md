# 2026-10-03 화면·문서·Kit 업데이트 준비

요구: 사람이 보는 화면은 목표, Phase 목표, API/MCP 참조, 달성 상태로 줄입니다. 다른 로그는 AI 분석의 근거로 보존하고 활용 질문과 후속 행동을 정의합니다. 이번 작업은 **준비까지**이며 GitHub push와 Vercel 배포는 실행하지 않습니다.

## 확인할 화면

- 실제 프로젝트: http://127.0.0.1:21944/ — 비공개 로컬, 네 프로젝트, 기존 문서 기준 상태. 현재 훅/runner 증거가 아닙니다.
- 공개 Vercel 준비본: http://127.0.0.1:21942/ — 합성 다섯 프로젝트. Alice/Bob 공동 프로젝트와 각 사람 필터를 유지합니다.
- Kit 준비본: http://127.0.0.1:21945/ai-pms.html — 한영 안내와 새 분석 구분.
- ELI20 준비본: http://127.0.0.1:21942/overview.html — 같은 최소 화면 설명.

로컬 주소는 해당 서버 실행 중에만 열립니다. 현재 공개 Vercel은 이전 배포입니다. 실제 프로젝트·문서 발췌·목표 비교 패킷은 공개 checkout/Kit ZIP에 포함하지 않습니다.

## 준비한 결과

정본 화면 `../ai-pms-dashboard/dashboard.html`에 human-view.js/css를 내장해 공개 정적 샘플과 Live Kit가 같은 화면 투영을 사용합니다. 기본 목록은 참여자·프로젝트 목표·단계 달성 요약입니다. 프로젝트에서 전체 Phase와 참조를, 별도 단계 페이지에서 목표·상태·참조를 읽습니다. WBS/Gantt와 작업 상세는 별도 근거 화면에서 계속 사용할 수 있습니다. 원본 모델과 완료 판정은 보존했습니다.

분석별 입력→질문→권장 행동은 [구분 문서](../../docs/human-view-and-analysis.md)에 있습니다. `scripts/prepare_goal_analysis.py`는 allowlist로 목표 비교 입력만 생성합니다. 모델 실행과 경고 저장은 미구현입니다. `sample-goal-input.json`은 합성 입력이며 실제 모델 결과가 아닙니다.

Kit canonical ko/en 안내, PMS runtime 내장 화면, 분석 문서/입력 생성기, implementation ZIP과 reference ZIP, README·제품 목적·ELI20 두 페이지를 갱신했습니다. 배포 전 검증 결과와 파일 해시는 `readiness.json`에 기록합니다. 이전 공개 release-proof는 이번 준비본의 공개 증거가 아닙니다.

## 검증과 다음 실행

공개 checkout에서 `python3 scripts/verify_public.py`를 실행합니다. 기본 화면의 필터/공동 목표/Phase/참조 비추론/모델 불변/근거 경로는 check_human_view.py가 검사합니다. 이전 WBS·action 회귀 검사는 evidence_render_tests.py로 보존된 상세 렌더러를 검사하며 기본 화면의 인수 증거와 구별합니다. 실제 브라우저의 데스크톱·390px 이동/새로고침/넘침 확인은 별도입니다.

Kit는 `build_current.py`와 `check_site.py`로 36페이지·한영 ZIP·runtime allowlist를 검사합니다. 이 검사가 실제 앱 훅 trust나 원격 두 사용자 전달을 증명하지 않습니다. 글로벌 hook/trust/자격을 변경하지 않았습니다.

다음 공개 실행은 분리 public checkout의 diff/비밀정보 경계 확인 → GitHub commit/push → 기존 dashboard Vercel 배포 → 기존 Kit publish.sh 배포 → 공개 파일 byte/CSP/실제 화면 대조 순서입니다. private 실제 자료를 이 단계에 복사하지 않습니다. 모델 분석 연결은 별도 범위이며 승인/비용/권한과 근거 검증·수락/기각 저장이 필요합니다.
