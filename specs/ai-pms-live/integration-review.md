# 부모 통합 검토와 남은 경계

최초 비작성 독립 검토는 sync-independent-review.md에 원래 해시/재현과 함께 보존했습니다. 다음 수정은 부모가 현재 코드와 실행 결과를 대조한 것으로 새 독립/Astra 최종 승인이 아닙니다. 사용량 한도로 담당/검토 에이전트가 종료되어 부모가 통합을 마쳤습니다.

- Native UUID/provider/event ID를 sender identity에 함께 포함하고 principal/native context별 receipt로 분리했습니다. `test_native_*`, `test_*collision*`은 다른 사용자/환경/native UUID를 분리하고 같은 context 본문 변경을409로 보존합니다. 동일 native UUID/provider 사이 같은 ID 충돌은 기존 central schema를 침묵 변경하지 않고409로 격리합니다.
- 누락/손상 건강파일을 중앙 unknown/degraded로 갱신합니다. 이미 알려진 context는 sender private 상태에 보존하여 JSONL 회전·재시작 뒤에도 기존 observed를 정상으로 남기지 않습니다. `test_missing_corrupt_health_central_projection`으로 observed→degraded→logs/health삭제→unknown을 검사했습니다.
- conflict/quarantined entity는 종속 revision을 보존하고 다른 entity 전달을 계속합니다. `test_conflict_isolated_other_entities_delivered`로 확인했습니다.
- manager seed의 실제 payload hash/revision을 private baseline으로 저장해 공동 프로젝트의 초기 noop 충돌을 피했습니다. `test_baseline_noop_shared_project_two_writers`와7writer 실제 HTTP full pilot을 통과했습니다.
- Demo seed는 redirect를 거부하고 응답 크기/정확한 ACK/eventID를 검사합니다. actual remote credential 전달은 없습니다.
- 동일 actor의 다른 환경 attempt/document/traceability 원본도 writer가 제거하지 못합니다. 원래 semantic envelope를 durable receipt에 보존하고 restart 후 `/api/history`로 과거 목표/계획/판단을 조회합니다.
- Hook가 project 매핑보다 먼저 온 경우 raw ID를 유지하고 매핑 후 reset으로 이전 unmapped 화면을 제거합니다. 인증 전 루트는 빈 login shell만200을 반환하며 실제 업무 APIs는401입니다. 이것은 spec의 인증 없는 조회401 규칙에 대한 정보 없는 shell 예외이며 업무 데이터 허용이 아닙니다. Live HTML은 hash CSP와 connect-src self, public static은 connect-src none입니다.

Parent `verify_live.py`와 공개 `verify_public.py`를 직접 실행합니다. DOM/mock parity는 실제 화면 렌더 증거가 아닙니다. 최신 CUA는 apps/browsers 없음·native pipe startup failure. 현재 remote two-user delivery, provider hook trust, actual browser/390px, fresh independent final review는 미완료입니다. 원격 목적지/참여자/보관·권한 정보를 받지 않고 private 로그를 공개 Vercel로 전송하지 않습니다.
