# STE 적용 릴리스 · 2026-10-05

AI PMS 도입 안내와 Live 설정을 사전 조건·실행·확인 근거·실패 시 행동으로 나눴습니다. `blocked`는 “진행 막힘”으로 표시합니다. Live 안내의 마지막 화면 반영 시각과 cursor 기록을 분리하고, 시간 경과만으로 연결 실패를 단정하지 않습니다. 완료 계산·API 계약·원문 명령은 보존했습니다.

ELI20, Handoff, 전문가 분석, 독립 패널, improvement-loop, audit와 STE 스킬의 필요한 문장에만 선택적으로 적용합니다. 독립 패널은 초안·교차검토 후 최종 문장을 다듬습니다. 스킬 10개 정의를 검증했고, Claude expert-panel의 기존 메타데이터 이름도 폴더명에 맞췄습니다. Kit 한·영 안내와 구현·참고 ZIP에 반영했습니다. archify 설치는 보류합니다.

`release-proof.json`은 검증 범위와 배포 주소·소스 해시, `local-browser.json`과 `public-browser.json`은 실제 Chrome 경로, `public-bytes.json`은 운영 주소의 87개 페이지·묶음 일치를 기록합니다. 브라우저는 1440px·390px에서 언어 전환, ELI20·STE 조작, 프로젝트 상세/새로고침을 확인했습니다. 인증된 합성 로컬 Live의 상태 문구와 연결 실패 시 이전 현황 보존도 확인했습니다. 실제 사용자 private 입력은 그대로 두고 로컬 HTML 표현만 갱신했습니다.

재검사: `python3 scripts/verify_public.py`. Kit는 별도 구성된 환경에서 `~/.claude/harness/site/publish.sh --check`로 검사합니다. 실제 앱 trust·훅 전달과 원격 실제 다중 사용자 운영은 이번 릴리스로 증명하지 않습니다. 한국어는 자체 명료성 가이드이며 영어 사전 승인은 별도 확인 대상입니다.

GitHub 커밋 `8cfb1d3`의 ZIP을 새로 내려받아 검토한 17개 소스·묶음 해시를 대조하고 `verify_adoption.py`를 통과했습니다. 근거는 `github-download.json`입니다. 이후 증거 기록만 추가했으며 실행 소스는 바꾸지 않았습니다.
