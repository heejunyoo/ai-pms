# 부모 브라우저 인수 관측 — 2026-09-30

환경: 실제 Chrome 연결, cua_repl의 DOM snapshot/클릭/검색/viewport/screenshot API. 합성 HTML만 127.0.0.1:21930에서 임시 제공했다. 서비스 배포나 사용자 전달 증거가 아니다. 화면 생성기 최종 해시: 7e5780995b2ae6cd2493efd5fbee19a14eb0425c02adbd39376f437a82e65cd5.

## 중앙 목록과 원본

- sample manifest를 부모가 import 두 번 실행했다. 두 실행 모두 sources=2 events=8, render projects=2. 같은 project UUID의 alice/codex-mac과 bob/claude-linux를 별도 행에서 확인했다.
- 목록은 각 목표/design 또는 research 단계/범위 변경/Agent·산출물·검사·인수 수/관리 항목을 표시한다. 합성 데이터와 자동 전달 미검증 배너가 보인다.
- alice 버튼 → 프로젝트 상세에서 dashboard/v1, Agent agent1의 codex 관측 후보, pass 검사와 pending 인수의 정확한 event ID를 확인했다. 후보를 인증된 귀속으로 표현하지 않는다.
- artifact.recorded 버튼 → 원본 JSON, event_id 00000000-0000-4000-8000-000000000004, SHA-256 cc3fea160a2beca8f92c21091477a413ca5ded6cc4705416b1a3888a84ad1a1a, 행 4, 최초 수집 2026-09-30T12:31:54.390431Z를 확인했다. occurred_at:null과 authority:declared를 그대로 보인다.
- bob 상세는 산출물 없음/검사 미연결/수집 지연을 표시한다. alice 산출물과 잘못 연결하지 않는다. 최근 수집은 9월 30일이어도 최근 관측은 9월 26일로 유지된다.
- 검색 bob → 1개 프로젝트가 보이며 alice는 필터링된다. 검색 제거 → 2개로 복원된다.

## 모바일·빈 상태

- 390×844px 목록은 프로젝트 카드로 바뀌었다. width/documentWidth/bodyWidth=390.
- 초기 상세 원본에서 document/bodyWidth=590인 실패를 직접 발견하고 기록했다. 구현자가 긴 관계/버튼/provenance 문자열 줄바꿈을 고쳤다.
- 최종 HTML을 다시 생성/재로드하고 같은 alice→artifact 원본 경로를 실제 재실행했다. width/documentWidth/bodyWidth=390, 긴 hash·JSON은 화면 안에서 줄바꿈되고 원본 패널을 읽을 수 있다. 수정 후 원본 스크린샷: original-mobile.png. 이전 실패 이미지 original-mobile-before-fix.png는 실패 이력이다.
- empty.html은 0개 프로젝트, 수집된 프로젝트가 없습니다, manifest/CLI 안내를 보인다. 모바일 documentWidth=390. viewport override를 reset했다.
- 브라우저 captured console error/warn 로그는 빈 배열이었다. 웹 런타임 전체/외부 서비스 검증의 증거는 아니다.
- 모바일 상세 DOM snapshot에 숨겨진 표의 CSS 가상 라벨 텍스트가 포함되는 도구 관측 특성이 남아 있지만 실제 화면에는 표가 나타나지 않는다. 스크린샷과 레이아웃 폭을 함께 확인했다. 독립 스크린리더 검사는 하지 않았다.

## 관리 예외 별도 화면

부모가 audit-input 합성 fixture를 만들어 같은 중앙 CLI를 실행했다(sources=4 events=9, projects=4). audit.html에서 목표 없는 tool.completed 작업은 목표 없음/Phase 불명/미래 관측 시각으로 보이며 완료로 승격되지 않는다. 파일 미도착 출처는 목표 없음/Phase 불명/연결 실패·입력 없음으로 나타난다. 원래 두 출처의 인수 대기·산출물 검증 불일치·지연도 유지된다. 이는 관리 예외 모사이며 실제 사용자 환경이 아니다.

스크린샷: dashboard-desktop.png, dashboard-mobile.png, original-event.png, original-mobile.png, empty-desktop.png, empty-mobile.png, audit-desktop.png. 부모 직접 관측이며 독립 검토자가 UI를 별도 실행한 결과가 아니다. 실제 다중 사용자 자동 전달과 제품 완료는 false다.
