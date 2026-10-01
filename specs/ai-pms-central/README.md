# AI PMS 로컬 중앙 흐름

두 사용자 환경의 logger v1 JSONL을 한 로컬 저장소에 가져와 관리자 HTML을 만듭니다. `sample/`은 **합성 데이터**입니다. 실제 사용자 환경의 자동 훅 전달, 인증, 중앙 서비스 운영, 제품 완료의 증거가 아닙니다. 현재 런타임 훅 배선과 실사용자 전달은 별도 검증이 필요합니다.

```sh
python3 specs/ai-pms-central/central.py import --manifest specs/ai-pms-central/sample/manifest.json --store /private/tmp/ai-pms-demo-store
python3 specs/ai-pms-central/central.py render --store /private/tmp/ai-pms-demo-store --output /private/tmp/ai-pms-demo.html
python3 specs/ai-pms-central/test_central.py
```

`/private/tmp/ai-pms-demo.html`을 브라우저에서 열면 목록 → 프로젝트 → 관계 목록 → 원본 이벤트로 내려갑니다. 저장 결과는 `--store` 아래 `central.json`이며 소유자 전용 `0700` 디렉터리·`0600` 파일입니다. HTML도 `0600`으로 기록합니다. `--manifest`의 각 `sources` 항목은 `actor_id`, `environment_id`, `project_id`(UUID), `label`, `evidence_mode`(`synthetic` 또는 `local-execution`), `files`(manifest 기준 상대 JSONL 경로)를 요구합니다. 출처 선언은 운영 입력이며 사용자 인증 증거가 아닙니다. 같은 UUID라도 actor/environment가 다르면 다른 프로젝트로 집계합니다.

각 JSONL 행은 기존 `logger.py` v1 계약을 그대로 따릅니다. 중앙 파일은 이벤트 본문과 출처 context, 최초 수집 시각, 입력 파일 SHA-256·행 번호를 보존합니다. 파일 경로, 명령, 원문 오류 입력은 저장·화면에 담지 않습니다. 출처별 `event_id` 재수집은 중복으로 세고 최초 기록을 유지합니다. 같은 ID의 다른 본문은 충돌로 기록합니다. 목표·Phase는 최신 유효 baseline 선언만, 범위 변경은 연결된 decision만 보여줍니다. 검사와 인수는 같은 출처의 정확한 `artifact_id`·`artifact_version`에 연결합니다. 수동 Agent 선언의 provider는 추측하지 않고 관측 후보·모호함·미연결로 구분합니다.

수집 한도는 manifest 1 MiB·출처 100개·출처당 파일 100개, 입력 파일 8 MiB·행 65,536 bytes·출처당 이벤트 10,000개, 중앙 저장 파일 64 MiB입니다. 초과·잘못된 행·누락 파일은 원문 없이 수치로 남기고 관리 항목에 표시합니다. 저장 한도를 넘는 import는 기존 저장 파일을 유지하고 실패합니다. 최근 관측 `observed_at`이 24시간 넘으면 지연, 미래면 미래 시각으로 표시합니다. `occurred_at`이 없는 것을 보완 추정하지 않습니다. 도구 완료·Stop·검사 통과는 프로젝트 완료나 사용자 인수를 뜻하지 않습니다.

검사는 독립 임시 로그 디렉터리에서 **실제 logger subprocess**를 실행한 뒤 합성 이벤트를 중앙 CLI로 가져옵니다. 이것도 실제 두 사용자 환경에서 중앙으로 자동 전달됐다는 증거는 아닙니다. 로컬 화면 인수와 실제 전달 확인은 부모의 별도 관문에서 다룹니다.
