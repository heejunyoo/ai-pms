# 부모 실제 브라우저 인수 — 승인 A 로컬 전달

관측일: 2026-10-01. 부모가 CUA의 실제 Chrome 탭으로 로컬 생성물에 접속해 클릭·검색·DOM 상태 및 스크린샷을 확인했다. 서버는 127.0.0.1에만 바인딩한 임시 정적 서버다. 실제 사용자 앱 훅·외부 전송·관리자 로그인·배포의 증거가 아니다.

Generation receipt SHA-256: c437e76639163bf666fd47afa44135563def23a85b700a1f866010f1bc8a7238

관측 대상은 이 영수증의 dashboard.html, audit.html, error.html, empty.html이다. 수정된 현재 코드로 exercise --output을 다시 실행한 후 이전 화면을 reload하고 아래 경로를 다시 확인했다.

- 목록: alice/bob/carol/dave 4개 출처 카드. alice/bob의 같은 project UUID가 별도 사용자·환경으로 분리됐고 서로 다른 목표를 표시한다. Bob에는 산출물 검증 불일치가 보인다.
- 상세: Alice 목록 버튼 → artifact-1/v1 관계. Agent agent-1은 codex 관측 후보, 검사 pass, 인수 pending으로 별도 표시했다.
- 원본: artifact.recorded 버튼 → event_id 72c0910e-5d76-4d61-a1f8-b378da360def, 본문, 최초 파일 SHA-256 58214dd12acea6155c4a529ecacd5d0e426f57e6afeda5fc47a0340780fe90f7, 행 3 및 서버 mirror provenance를 확인했다. 송신 로그 원파일 해시로 표현하지 않는다.
- 검색: 목록 복귀 → 검색 bob → 1개 프로젝트와 Bob의 검증 불일치. 검색을 지우면 4개가 복원된다.
- heartbeat: Carol 상세의 수신 이벤트 0/heartbeat 1, 최근 연결 있음/최근 관측 없음, 목표·Phase 누락, 원본 이벤트 버튼 0개. Dave는 목록에서 마지막 연결 없음/heartbeat 0을 확인했다.
- 충돌: audit.html에서 Alice의 충돌 1/전달 충돌, 상세 배치 6b5ba3c7-6c40-46db-852f-e590f9577a4c의 event_conflict를 확인했다. 목표는 alice의 독립 목표를 유지했다.
- 상태 불명/중앙 저장 실패: 실제 renderer CLI가 만든 error.html에서 전달상태 불명·중앙 저장 읽기 실패 배너, 4개 등록 카드 및 각 프로젝트 관리 항목을 확인했다. 정상 집계 카운트나 작업 근거를 만들지 않는다.
- 빈 상태: empty.html의 0개 프로젝트·수집된 프로젝트가 없습니다 화면을 확인했다.
- 반응형: 최초 desktop 목록/관계/원본을 확인한 뒤 390×844로 검사했다. 최종 목록, 상세, 원본, 검색, 충돌, 오류, 빈 화면 모두 viewport 390 / document.scrollWidth 390. 스크린샷도 실제로 관측했다. 명시 viewport는 검사 후 reset했다.
- Console: 마지막 검사 경로의 error log 조회는 빈 배열. 이는 모든 실행 경로의 오류 부재 보증이 아니다.

이 기록은 부모의 실제 UI 관측이다. 해시·플래그는 관측 대상의 귀속 일관성을 확인하며 클릭의 의미나 관측의 독립성을 자동 증명하지 않는다. 합성 loopback 검증이며 actual_multi_user_delivery_verified=false, product_complete=false를 유지한다.
