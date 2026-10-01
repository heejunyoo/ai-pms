# 공식 문서와 구현 근거 — 확인 2026-10-01

- [OpenAI Docs: Codex Hooks](https://learn.chatgpt.com/docs/hooks): configured hook은 hash에 대한 검토/trust 이후 실행된다. 새/변경 hook의 trust를 자동 우회하지 않는다. 지원 로컬 도구 PostToolUse와 hosted tool 예외를 구분하고 실제 앱에서 확인할 도구 경로를 선택한다. transcript 형식은 안정 계약이 아니므로 전송기에서 파싱/업로드하지 않는다. hook 출처에는 hooks.json, config.toml inline [hooks], 플러그인 등이 있어 글로벌 JSON 하나의 부재로 전체 배선을 부정할 수 없다.
- [Claude Code: Hooks reference](https://code.claude.com/docs/en/hooks): 성공 PostToolUse와 PostToolUseFailure는 별도다. source/session/tool_use_id/agent 필드가 모든 이벤트에서 존재한다고 가정하지 않는다. 로깅 allowlist 밖의 prompt/tool_input/tool_response/transcript_path는 전송하지 않는다. 도구 성공은 제품 완료 증거가 아니다.
- 기존 로컬 코드: ../ai-pms-central/central.py, ../ai-pms-central/README.md, ~/.claude/harness/activity/logger.py. 실제 앱 전달 증거는 아직 없고 설치 버전 출력만 확인했다. 설치 버전 확인은 사용자의 앱 호스트/플러그인/프로젝트 layer별 활성 훅 검증을 대신하지 않는다.

공식 문서가 직접 말하는 지원/입력과 이 프로젝트의 전송/인증/ACK 설계 제안을 구분한다. 외부 서비스·API·hook 설치를 실행했다는 자료가 아니다.
