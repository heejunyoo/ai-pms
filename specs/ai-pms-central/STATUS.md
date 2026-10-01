# 현재 결과 — 로컬 중앙 흐름 검증

2026-09-30: 두 합성 출처 → 중앙 파일 저장/집계 → 다중 프로젝트 목록 → 관계 목록 → 원본 이벤트를 구현하고 부모가 실제 Chrome에서 인수했다. 로컬 중앙 준비 단계 완료이며 중앙 AI PMS 제품 완료는 아니다.

- 구현: central.py import/render, owner-only 원자 파일 저장과 잠금, 기존 logger v1 형식 보존. 출처 context를 바깥에 붙인다.
- 식별/연결: actor/environment/project별 격리, event_id 멱등 및 충돌 보존, 정확한 baseline/산출물 버전, source/session/agent별 관측과 manual 후보/모호함 처리.
- 관리자 화면: 목표·Phase·최근 변경·Agent/산출물/검사/인수·관리 필요 항목, 검색, 프로젝트 상세, event JSON/해시/행 번호. 누락/미연결/지연/미래 시각/과거 수집 오류를 완료로 표현하지 않는다.
- 검사: 실제 logger subprocess를 사용하는 2개 통합 테스트, 독립 코드 검토, 부모 CLI 두 번 수집(2출처/8이벤트), Chrome 목록/상세/원본/검색/빈 상태/390px 재검증. 모바일 원본 가로 넘침을 실제 발견하고 수정 후 같은 경로에서 재검증했다.
- 증거: intent-review.json, code-review.md, implementation-result.json, acceptance-evidence.json, evidence/browser-observation.md 및 스크린샷. verify_acceptance.py는 저장된 관측·파일 해시와 구현 테스트를 검증한다. 새 UI 실행을 자동 재현하거나 실제 전달을 검증하는 스크립트가 아니다.

다음 실제 전달 단계는 미완료다. 글로벌 Codex/Claude activity hook 배선과 기본 로그 디렉터리를 현재 조사에서 찾지 못했다(runtime-observation.md 참조). 자동 전송/인증/중앙 서비스·운영·배포를 이번에 구현하거나 승인받지 않았다. 개인정보 정규식은 알려진 일부 패턴만 차단하며 완전한 비밀 탐지가 아니다. 대규모 집계와 조직 인증·접근 제어·retention은 후속 설계 대상이다.

재확인: 프로젝트 루트에서 `python3 specs/ai-pms-central/verify_acceptance.py`. 실행 안내는 README.md. 데모는 evidence/preview/dashboard.html, 관리 예외는 evidence/preview/audit.html. 다음 순서는 최상위 NEXT_SESSION.md에 기록한다.
