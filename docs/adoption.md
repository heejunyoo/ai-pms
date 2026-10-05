# 다운로드해서 내 프로젝트에 적용하기

AI PMS는 사람별 프로젝트 목표·문서·Phase·작업·검증을 함께 보는 중앙 관리 프로토타입입니다. 처음에는 문서만 등록하고, 선택한 앱 훅을 연결한 뒤, 필요할 때 인증된 자체 호스팅 Live 파일럿을 도입하세요. 목표와 판단은 직접 입력합니다. 훅의 Stop는 턴 종료이며 목표 완료가 아닙니다.

## 1. 다운로드와 실행 위치

GitHub 저장소의 **Code → Download ZIP**으로 내려받아 압축을 풉니다. 또는 저장소 페이지에 표시된 clone URL로 clone합니다. README.md와 scripts/, specs/, kit/, templates/가 함께 있는 최상위 폴더가 실행 루트입니다. 모든 아래 명령은 이 루트에서 실행합니다. Python 3.11+와 Node.js, macOS/Linux가 필요합니다. Python 외부 패키지는 설치하지 않습니다.

```sh
python3 scripts/verify_adoption.py
python3 scripts/verify_public.py
```

첫 명령은 임시 폴더에서 수집·문서 화면·7개 합성 writer의 로컬 서비스 경로를 검사합니다. 두 번째는 기존 전체 portable 회귀 검사입니다. 두 명령은 로컬 HTTP 포트를 사용합니다. 포트 bind를 제한한 환경의 실패는 정상 앱 도입 근거가 아니므로 로컬 포트가 허용된 환경에서 다시 실행하세요. 자격 원문을 출력하거나 전역 hook/trust를 변경하지 않습니다.

GitHub의 `kit/activity/`는 내려받은 저장소의 훅/기록기 소스입니다. Harness Kit implementation.zip을 별도로 풀면 같은 파일은 `activity/`에 있습니다. **Kit의 PMS 범위는 훅 수집이고, 중앙 PMS 실행 소스는 GitHub 루트의 `specs/ai-pms-live/`입니다.** ZIP에 `pms/`가 있다고 가정하지 마세요. Kit의 일반 안전검사·규칙·skills는 별도 범위로 유지됩니다.

## 2. 문서만으로 내 프로젝트 보기

먼저 공개 화면의 가상 도입 예시를 살펴보세요. 기본 샘플은 문서·계획을 먼저 넣은 상태이며 실제 사용자 자료가 아닙니다. 기존 합성 실행 이력 예시는 별도 recorded-example.html에 있습니다. 공개 Vercel은 정적 샘플이고 실제 로그를 받을 서버가 아닙니다. private 자료를 공개 샘플/저장소에 올리지 마세요.

```sh
python3 scripts/build_dashboard_app.py
python3 -m http.server 21932 --directory apps/dashboard/public --bind 127.0.0.1
```

`http://127.0.0.1:21932/`에서 사람 → 프로젝트 → Phase → 작업/근거 순서로 엽니다. 자신의 자료는 [작업 계획 템플릿](../templates/catalog-work.template.json)을 private 파일로 복사하고 [필드 설명](json-contracts.md)에 따라 수정합니다. 예시 검사 명령은 실제 실행 가능한 프로젝트 검사로 바꾸고 runs는 실행하기 전 빈 배열로 유지하세요.

- `projects[].id`는 관리용 ID, `source_refs[].project_id`는 실제 로컬 기록기의 native 프로젝트 UUID입니다. `actor_id`와 `environment_id`까지 정확히 연결해야 합니다. 같은 이름이나 UUID만으로 다른 사람/환경을 합치지 않습니다.
- `goal`, `documents`에 원래 목표와 문서 버전·출처를 등록합니다. 문서 본문은 operator가 공유 범위를 검토해야 합니다. 훅이 목적을 추측해 채우지 않습니다.
- `phases`와 `management.work`에 Phase 목표·작업 ID·담당자·완료 조건·의존성·검사·사람 승인 요건을 등록합니다. 공동 프로젝트도 개인별 목표와 담당 작업을 명시합니다. 회사 북극성은 개인 프로젝트에 강제하지 않습니다.
- [운영 템플릿](../templates/operations.template.json)의 sessions/north_stars/contributions/capture와 [기록기 안내](../kit/activity/README.md)의 Handoff import·실제 검사 실행·review를 사용합니다. 선언 입력, 실제 검사, 현재 산출물 검증, 사람 인수를 구분합니다.

저장소 밖 private 입력과 출력의 절대 경로를 지정합니다. 출력 디렉터리는 먼저 만들고 `PMS_CATALOG`에는 검토한 catalog JSON을 지정하세요.

```sh
python3 specs/ai-pms-dashboard/portfolio.py --catalog "$PMS_CATALOG" --out "$PMS_PRIVATE_DIR/documents.html" --json-out "$PMS_PRIVATE_DIR/snapshot.json"
```

생성된 documents.html을 열거나, 로컬 대시보드의 JSON 가져오기에서 snapshot.json을 선택합니다. raw catalog는 가져오기 대상이 아닙니다. 기본 샘플의 문서 과업/출처 주석은 `sample-documentary.json`과 index HTML의 documentary-data에 있으므로 `adoption-snapshot.json`만 가져오면 해당 문서 주석 전체를 재현하지 않습니다. 내 문서의 목표·단계·작업은 catalog에 명시해 렌더하세요. catalog만 넣으면 출처 활동은 미관측입니다. 문서 등록/HTML 생성은 AI 분석 성공이나 실제 앱 수집 증거가 아닙니다. [화면과 AI 분석](human-view-and-analysis.md)을 참고하세요.

## 3. 선택한 앱의 훅 수집 연결

`kit/activity/logger.py`와 `connectivity.py`를 함께 보존하여 사용합니다. 내려받은 폴더를 옮길 계획이면 [기록기 안내](../kit/activity/README.md)에 따라 두 파일을 지속 가능한 같은 디렉터리에 배치합니다. 설정에는 실제 절대 경로를 사용하고 경로에 공백이 있으면 shell 인용을 적용하세요. 아래의 `/absolute/path/to/...`는 자신의 다운로드 위치로 바꿔야 합니다.

기존 Codex/Claude hooks 설정을 먼저 백업하고 선택한 event entry에 **추가 병합**합니다. 기존 검사·안전 hook를 덮어쓰지 마세요. Codex의 hooks.json, Claude의 settings.json에서 지원되는 command-hook entry를 검토합니다. 최신 앱별 설정 위치와 지원 이벤트는 [기록기 안내](../kit/activity/README.md)의 공식 문서 링크에서 확인하세요. Codex는 `/hooks` 리뷰와 trust 승인이 필요합니다. 이 저장소는 이를 자동 승인하지 않습니다. Cursor/Gemini native adapter는 미지원입니다.

```json
{"hooks":{"Stop":[{"hooks":[{"type":"command","command":"python3 /absolute/path/to/kit/activity/logger.py hook --source codex --project-id 11111111-1111-4111-8111-111111111111 --log-dir /absolute/private/logs"}]}]}}
```

Claude에는 `--source claude`를 사용합니다. UUID는 자신이 정한 실제 프로젝트 UUID이고 catalog source_refs와 같아야 합니다. 필요 이벤트는 지원되는 SessionStart/SessionEnd/Stop/SubagentStop 등의 entry로 따로 추가합니다. 위 JSON을 설정 전체로 덮어쓰지 마세요. 각 source/identity의 private logdir를 구분하면 출처를 확인하기 쉽습니다.

먼저 합성 stdin smoke를 별도 테스트 디렉터리에서 실행합니다. `PMS_LOG_DIR`에는 공개 폴더 밖 자신의 private 테스트 경로를 정합니다.

```sh
printf '%s' '{"hook_event_name":"SessionStart","session_id":"synthetic-smoke"}' | python3 kit/activity/logger.py hook --source codex --project-id 11111111-1111-4111-8111-111111111111 --log-dir "$PMS_LOG_DIR"
python3 kit/activity/logger.py health --log-dir "$PMS_LOG_DIR"
```

정상은 status=observed, 마지막 event ID/시각이고 JSONL event ID와 맞아야 합니다. 파일/디렉터리 권한은 0600/0700입니다. health는 logdir 기록기 전체 상태이며 모든 프로젝트의 heartbeat가 아닙니다. 빈 기록은 unknown, 손상/미지원은 unknown 또는 degraded이고 오래된 성공은 현재 정상으로 승격하지 않습니다. hook exit0만으로 기록 성공을 판정하지 마세요.

이후 **실제 앱에서** 선택 이벤트를 발생시키고 JSONL → capture-health.json의 같은 event ID를 확인합니다. 합성 stdin 검사는 실제 앱 호출을 증명하지 않습니다. 실제 앱별 확인 전 커버리지는 미검증으로 남깁니다. 원문 prompt·SQL·URL·자격을 로그에 추가하지 마세요.

## 4. 인증된 중앙 Live 파일럿

[Live 실행 안내](../specs/ai-pms-live/README.md)의 setup → service → seed → writer → manager login 순서로 시작합니다. 합성 데모는 private 임시 폴더에 7개 writer와 별도 manager 자격을 만들며 실제 훅을 설치하지 않습니다. browser는 localhost 서비스의 same-origin 페이지에서 인증 후 조회합니다. 공개 Vercel 정적 페이지는 중앙 수신기가 아닙니다.

실제 프로젝트 도입은 합성 registry/자격을 재사용하지 않고 운영자가 허가한 actor/environment/native UUID, HTTPS 목적지, owner-only token_file과 private catalog/operations/logdir를 준비합니다. 한 outbox는 한 인증 context와 목적지 전용입니다. 대상 변경에는 새 outbox를 사용하고 base revision 충돌은 검토합니다. 초기 manager seed가 끝나기 전에 writer를 시작하지 마세요. `session_goal.py bind`로 source/session/task를 연결하고 현재 검증이 충족된 뒤에만 `decide accepted`를 기록합니다.

## 5. 확인과 종료

정상 도입은 실제 앱 event ID → 로컬 health → sender의 내구 ACK → 인증된 changes → 같은 사람/환경/session/task 화면까지 맞아야 합니다. 실패 전송은 outbox를 보존하고 재시작 시 재시도합니다. 동일 ID/본문은 중복이며 다른 본문은 conflict입니다. 검증 없음을 완료로 해석하거나 충돌을 수동 JSON 수정으로 통과시키지 마세요. 목표·산출물·검사 정의가 바뀌면 과거 pass/승인은 재검증해야 합니다.

종료할 때 sender와 service 터미널에서 Ctrl-C를 누르고 정적 http.server도 종료합니다. 훅 수집을 중단하려면 백업한 설정과 비교해 자신이 추가한 entry만 제거하고 기존 hook는 보존합니다. private 데이터·자격 보관/삭제는 운영자 정책으로 결정하며 이 검사는 자동 삭제하지 않습니다. 이 로컬 파일럿은 원격 실제 다중 사용자 전달, SLA, 운영 TLS 배포 또는 브라우저 렌더 인수를 대신하지 않습니다.
