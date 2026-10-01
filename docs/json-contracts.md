# 현재 JSON 입력과 Kit 기록의 연결

2026-10-01 현재 구현을 설명합니다. 새 중앙관리 계약 제안과 현행 실행 가능한 형식을 구분합니다.

## 현재 사용 가능한 파일

| 자료 | 위치 | 용도와 입력 경계 |
|---|---|---|
| 최소 프로젝트 catalog | `templates/catalog-v2.template.json` | 사용자·환경 연결, 목표, 단계, 문서, 검사 기준·결과, 선언 연결. CLI의 `--catalog` 입력입니다. |
| 상세 catalog 예시 | `specs/ai-pms-dashboard/sample/catalog.json` | 다섯 합성 프로젝트. criteria/runs/connections 작성 예시입니다. |
| 중앙 출처 manifest | `specs/ai-pms-dashboard/sample/manifest.json` | actor/environment/project와 선택된 JSONL 파일을 연결합니다. 중앙 import 입력입니다. |
| 훅/수동 이벤트 JSONL | Kit ZIP의 `activity/example-project.jsonl`, `activity/README.md`, `activity/logger.py` | 이벤트별 발생 기록. raw JSONL을 대시보드 JSON 가져오기에 넣는 형식은 아닙니다. |
| 중앙 저장 자료 | `specs/ai-pms-dashboard/sample/central.json` | 이벤트 원본, 출처, 수신 시각, 원본 파일 SHA256·행 번호. CLI의 `--store` 입력입니다. |
| 대시보드 snapshot | 공개 앱 `/snapshot.json`, `templates/snapshot-empty-v2.json` | 중앙 모델이 생성한 화면용 JSON. 대시보드 가져오기/붙여넣기의 입력입니다. |
| Handoff 작업 계획 | Kit ZIP의 `handoff/example.plan.json`, `plan.schema.json`, `packet.schema.json` | goal, 원문 요구사항, phase exit_check, task acceptance·파일 범위·제약. 별도 PMS 자동 import는 아직 없습니다. |
| Handoff 결과 | Kit ZIP의 `handoff/example.result.json`, `result.schema.json` | task_id, 실행 command/exit_code/output_tail, done_when_check/evidence, 변경 파일, 미충족 조건. 별도 PMS 자동 import는 아직 없습니다. |

Kit 웹의 AI PMS 페이지에는 역할·MCP 안전 메타데이터와 훅 예시가 있습니다. 전체 중앙 catalog/snapshot 작성 템플릿과 각 필드 안내는 지금까지 Kit ZIP에 포함되지 않았습니다. Handoff 계획/결과 템플릿이 있다고 해서 그 파일들이 PMS에 자동으로 들어오는 것은 아닙니다.

## 현재 어떤 정보가 들어오나요?

| 정보 | 현재 출처 | 저장/표시하는 내용 | 알 수 없는 내용 |
|---|---|---|---|
| 세션·도구 활동 | 로컬 command hook | 세션/Agent/호출 ID(제공된 경우), native event, 요청/완료/실패, 발생/관측 시각 | 사용자의 목적, 판단 이유, 전체 완료 조건 |
| 프로젝트 목적과 결정 | 명시적인 manual record 또는 catalog | 목표·범위·결정 요약/이유, 기준·작업·산출물 참조 | 목표 분해의 타당성, 실제 이행 여부 자동 보증 |
| 문서와 검사 | catalog | 문서 버전/작성 출처, 6필드 검사 기준, revision·종료코드·evidence·기준 signature | 테스트 계획 생성 이유/버전 변화, 실행 주체와 환경, 신뢰된 runner 검증 |
| MCP·데이터 참조 | 훅의 안전한 이름 및 명시 metadata/map | 서버/tool, status, 제공된 duration_ms, 선언 operation, resources와 근거, 명시 artifact_refs | 서버 내부 DB/API 실제 접근, 실제 산출물에 활용되었는지 |
| 철칙·하네스·루프·스킬 운영 | 현재 일부 hook 이벤트 이름·별도 로컬 gate | 도구/세션 경계만 일부 관측 | 설정 버전, 규칙 판정, loop attempts, 스킬 선택 이유/버전/효과, 병목·개선조치의 중앙 이력 |

catalog의 criterion_signature는 기준 정의 변경을 감지하는 해시입니다. runner의 암호학적 서명이나 실제 실행의 증거가 아닙니다. check.recorded의 status=pass도 선언이며 runner 관측 결과와 구분해야 합니다.

## 최소 catalog로 생성

프로젝트/사용자/환경 ID와 실제 목표·검사 조건을 바꾼 뒤 다음을 실행합니다. 템플릿의 명령은 예시이며 이 명령으로 검사를 실행하지 않습니다. 테스트를 실행하지 않았다면 runs를 비워 둡니다.

```sh
python3 specs/ai-pms-dashboard/portfolio.py --catalog templates/catalog-v2.template.json --out output/dashboard.html --json-out output/snapshot.json
```

새 중앙관리 제안은 `docs/central-management-contract.md`에 있습니다. 그 제안의 이벤트 종류는 현행 logger/import가 아직 지원하지 않습니다.
