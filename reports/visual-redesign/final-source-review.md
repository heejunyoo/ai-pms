# 시각화 최종 독립 소스 검토

2026-10-04. QA 에이전트가 UI 구현 에이전트의 완료 설명과 별도로 현재 canonical JS/CSS, embedded HTML, 새 회귀 및 기존 두 회귀를 확인했습니다. 실제 브라우저·스크린샷·고객 이해도 검증은 하지 않았습니다. 모바일은 이번 인수 범위에서 제외합니다.

## 판정

소스와 합성 DOM에서 전체 공동 계획·원자 작업·세션 의미·보수적 현재 검증을 유지하는 구현을 확인했습니다. 최종 아래 세 명령 모두 종료코드 0입니다. 실제 화면의 미적 완성도, 데스크톱 가독성, 실제 브라우저 history/reload는 **미검증**입니다. 중앙 원격 두 사용자 전달·실제 앱 훅 전달을 이 결과로 승인하지 않습니다.

- `python3 specs/ai-pms-visual-management/check_visual.py`
- `python3 specs/ai-pms-human-projection/check_human_view.py`
- `python3 specs/ai-pms-rensei-experience/check_experience.py`

## 검토 결과

- 기본 WBS는 모든 Phase와 원자 작업을 유지하고 Bob 선택 뒤에도 Alice·미지정 작업을 남깁니다. 담당 강조는 완료 계산을 바꾸지 않습니다. 상태는 기호와 텍스트를 포함합니다. Phase별 작업 통로와 별도 최종 인수 주소가 유지됩니다.
- 완료 Phase는 처음 접히고 진행·막힘·검토·재검증 Phase는 처음 펼쳐집니다. 모든 heading에 작업 개수가 있으며 접힘·포커스·사람 범위는 applyChanges의 delta/reset에서도 유지됩니다. Phase별 펼침을 제공하며 전체 작업을 한꺼번에 펼치는 별도 버튼은 없습니다.
- 참여자 요약은 전체 작업 제목을 반복하는 대신 담당 작업/단계 개수와 담당 단계 상세 링크를 제공합니다. 개수는 작업량·노력·성과 비율로 환산하지 않습니다.
- 기본 근거 진입은 작업 결과/실행 이력/참고 자료 세 가지입니다. 기존 9종 원본 분류는 실제 native details의 자손으로 보존됩니다. 기술 원문이 숨겨져도 문서·검사·목표·판단·인계·연결 기록을 삭제하지 않습니다.
- 실제 세션 evidence 진입은 단일 history section에 다섯 operation/두 legacy 행을 표시하는 합성 반례를 통과했습니다. 동일 ID라도 actor/environment/provider/source-project가 다르면 유지하고 완전한 원본 identity가 일치할 때만 raw/goal을 병합합니다. provider가 불명확한 legacy는 합치지 않습니다. 종료/목표 실패, 여러 작업 연결, 사람 범위, 미수집 상태, 모델 불변성을 검증했습니다.
- 날짜축은 바인딩된 synthetic schedule만 사용합니다. project/plan/version/revision 불일치, 누락 작업, 잘못된 날짜, 다른 schedule kind 및 private evidence에서는 단계축으로 돌아갑니다. 문서상 완료는 날짜·문서 기준과 현재 미확인을 표시하고 현재 최종 인수로 승격하지 않습니다.
- HTML처럼 생긴 작업명은 native text로 남습니다. 사람 URL·절대 anchor href·새 runtime 초기화·live focus·스크롤·reset 및 기존 attention/unknown/non-inference 회귀를 유지했습니다.

## 독립 검토에서 발견하여 수정한 결함

문서에만 있는 작업의 early-return 경로는 작업 클릭 뒤 포커스를 새 상세로 옮기지 않았습니다. `docLink.focus(); docLink.click()` 뒤 taskId/connected focus 반례를 추가하자 실제 exit1 `Document-only task should receive native focus`가 발생했습니다. UI가 해당 분기에서 disclosure와 같은 주소 포커스를 복원하고 새 작업 진입에서 panel.focus를 실행한 뒤 최종 회귀 exit0을 확인했습니다. 이 실패는 실제 합성 DOM 실행 기록이며 브라우저 관찰을 뜻하지 않습니다.

기존 UI에서 check_experience.py는 exit0이었습니다. 새 check_visual.py는 구현 전 `Whole WBS must be the primary project plan`에서 실제 exit1을 기록했습니다. 새로운 문제를 기존 통과만으로 검증했다고 표현하지 않습니다.

## 부모에게 전달한 잔여 관찰

초기 최종 검토에서 프로젝트 기본 WBS의 전체 API/MCP 요약 경로 누락을 부모에게 전달했습니다. UI가 기본 계획에 짧은 이름·근거 유형 요약과 직접 설정·호출 근거 링크를 복원했습니다. 새 회귀에서 humanReferences의 이름·basis가 기본 화면에 존재하고 native link 클릭이 connections 근거로 이어지는 것을 확인했습니다. Phase별 명시 연결만 사용하며 설정과 호출 관측을 구별하는 비추론 검증도 유지됩니다. 추가 회귀까지 포함한 최종 세 명령은 모두 exit0입니다. 미해결 소스 차단 결함은 발견하지 않았으며, 실제 데스크톱 인수 경계는 그대로 미완료입니다.

## 확인한 파일 바이트

- `specs/ai-pms-dashboard/human-view.js`: `a9dd01579afe6552ba1c53ca24b2a44a1ce4cd0be97152a7f13e018651846a80`
- `specs/ai-pms-dashboard/human-view.css`: `bcfdfb7361344ac7604143598acecb58c514cdd3bc206c8de8215178e2f98574`
- `specs/ai-pms-dashboard/dashboard.html`: `db3ab473f4ba3f35a0d71b1a483d3d07219e796369534abc90f8ebfd5163b454`
- `specs/ai-pms-visual-management/check_visual.py`: `0da9756e986e7863432bad094ee678ac4b6bcd120d9565d2dd03a97a1b38029e`

해시는 검토 대상을 고정할 뿐 실제 브라우저·사용성 인수나 의미적 정합성을 단독 증명하지 않습니다.

## 부모 통합 뒤 전체 suite에서 발견한 IA 검사 충돌

부모의 공개 fullsuite에서 `check_ia.py:124`가 실패했고 QA에서도 실제 exit1 `Cannot read properties of undefined (reading click)`를 재현했습니다. 새 native 기술 details가 닫힌 상태에서 기존 검사가 그 안의 숨은 tab에 직접 keydown을 주입해 visible tab 배열이 비었습니다. 실제 사용자는 닫힌 details 안의 버튼에 키보드로 도달하지 못하므로 기존 키보드 검증의 진입 조건을 보완했습니다.

`check_ia.py`는 기술 details가 기본 닫힘임을 먼저 assertion으로 확인한 뒤 `human-technical-evidence.open=true`를 설정합니다. 이후 기존 End 키·중첩 details 접힘 제외·최종 tab focus·선택 상태·이력 복귀 assertion을 하나도 삭제/skip하지 않고 그대로 실행합니다. 부모가 runtime 빈 배열 `if(!tabs[n])return` guard를 반영했고, 그 현재 dashboard로 QA가 다시 실행하여 exit0을 확인했습니다. 이것은 실제 숨은 버튼의 브라우저 keyboard 동작을 검증했다는 뜻이 아닙니다.

최종 `python3 specs/ai-pms-toss-ia/check_ia.py` exit0입니다. 연쇄 실행된 work UI parity(24 Python snapshot, 36 forged import), v2/v3 exact contract·관리 모델·validator·text safety 검사도 통과했습니다. 실제 브라우저 인수 경계는 변하지 않습니다.
