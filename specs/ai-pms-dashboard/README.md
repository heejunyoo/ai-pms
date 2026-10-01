# 중앙 AI PMS 대시보드

자동 수집 없이 로컬로 가져온 자료를 사용하는 중앙 현황·상세 화면입니다. 외부 리소스나 서버 없이 생성된 HTML을 브라우저에서 열 수 있습니다. `evidence/dashboard.html`은 다섯 합성 사용자 프로젝트를 넣은 실행 예제입니다.

## 바로 보기

- `evidence/dashboard.html`: 합성 프로젝트 현황, 사용자/상태/단계 필터, 문서 버전, 검사·세션·변경 이력·원본 근거.
- `dashboard.html`: 데이터 없는 정본 템플릿. 정규화 snapshot JSON 가져오기 가능.
- `evidence/snapshot.json`: 가져오기 가능한 합성 snapshot.
- `../../reports/ai-pms-eli20/index.html`: 제품 목적과 완료 판정을 설명하는 ELI20 보고서.

생성 HTML은 임시 미리보기 서버를 종료한 뒤에도 파일로 사용할 수 있습니다. 브라우저에서 파일 프로토콜을 제한하는 검증 도구에서는 아래 제한된 개발 서버를 사용합니다. 실제 사용자 자료를 공개 서버에 올리지 않습니다.

## 새 자료로 생성

```sh
mkdir -p output
python3 specs/ai-pms-dashboard/portfolio.py \
  --store specs/ai-pms-central/evidence/store/central.json \
  --catalog specs/ai-pms-dashboard/sample/catalog.json \
  --out output/dashboard.html --json-out output/snapshot.json
```

store는 기존 중앙 저장 JSON, catalog는 프로젝트 연결·목표·단계·문서·완료 기준·검사 결과의 로컬 입력입니다. 위 명령은 입력 예시이므로 실제 store에 맞는 catalog의 source_refs를 준비해야 합니다. 두 경로를 생략하면 빈 화면, store만 지정하면 목표/완료 기준 미입력 출처도 보존합니다. catalog만 지정하면 사용자 제공 자료로 표시하고 실행 출처 미관측을 알립니다. 입력 원본은 수정하지 않습니다.

JSON 파일 가져오기 또는 붙여넣기는 **생성된 snapshot**을 받습니다. raw central/catalog는 CLI로 변환하세요. 잘못된 snapshot을 가져오면 기존 현황을 유지합니다. 내보낸 파일은 다시 가져올 수 있습니다. 프로젝트 상세 URL의 hash를 사용해 같은 화면을 다시 열 수 있고 필터는 상세에서 돌아와도 유지됩니다.

## 입력 작성

전체 입력 예제는 `sample/catalog.json`, 생성 방법은 `sample/generate.py`와 `sample/README.md`에 있습니다. source_refs는 actor_id/environment_id/project_id가 정확히 일치해야 합니다. Alice의 두 환경처럼 명시적으로 연결하며, 다른 사용자의 우연히 같은 project UUID를 자동 합치지 않습니다. 같은 출처의 중복 매핑은 거부합니다. 문서는 각 버전의 본문·단계·작성 세션과 사용자/환경을 함께 기록합니다.

완료 기준의 scope는 project/phase/task입니다. project 검사 대상은 해당 프로젝트 ID입니다. run은 criterion_id, 대상 revision, 실행 시각, 종료 코드, session_id, evidence, criterion_signature를 기록합니다. signature는 검사 정의의 SHA-256 식별값이며 실제 실행의 진위를 증명하는 암호학적 서명은 아닙니다. 종료 코드를 모르면 null을 사용합니다. 검사 명령은 대시보드가 실행하지 않습니다.

현재 revision의 전체 기준이 모두 통과하면 완료, 최신 전체 검사 실패면 검사 실패, 이전 revision에서 완료 후 현재 결과가 부족하면 재검증 필요입니다. 전체 기준이 없으면 미관측입니다. 미래 시각·상충 결과·변경된 기준의 옛 결과는 완료로 승격하지 않습니다. 검사 기준 정의 자체를 바꾸면 옛 기준의 완료 milestone은 이 snapshot에서 복원되지 않습니다. 변경 전 snapshot을 보관해 당시 완료 근거를 남겨야 합니다. 관련 결과물 변경 시 current_revision을 갱신해야 하며, 이번 수동 입력 방식이 변경을 자동 탐지하지는 않습니다.

입력 파일당16MB, 최종 프로젝트1000개·각 배열10000개·정규화 model canonical JSON6MB 한도입니다. UI snapshot 파일8MB·텍스트총량6M 한도와 맞춥니다. 개인 절대경로·알려진 자격 형식은 거부하며 오류 메시지에 원문을 출력하지 않습니다. 문서 본문은 HTML을 실행하지 않고 텍스트로 보여줍니다.

## 검증

```sh
python3 specs/ai-pms-dashboard/verify_dashboard.py
```

모델 의미 검사, UI 구조·JS 구문·입력 반례, 기존 중앙 회귀, handoff 검토·반환, 생성 모델/HTML과 저장된 부모 브라우저 관측의 코드 해시를 확인합니다. 새 브라우저를 자동 실행하는 명령은 아닙니다. 실제 관측 경로와 범위는 `evidence/browser-observation.md`, 독립 검토는 `code-review.md`, 인수는 `acceptance-evidence.json`입니다.

개발 미리보기: `python3 specs/ai-pms-dashboard/preview_server.py` → `http://127.0.0.1:21931/`. loopback에서 생성 대시보드·빈 화면·보고서와 보고서가 참조하는 지정된 안내/인수 문서만 제공합니다. 디렉터리나 임의 파일을 열람하는 경로는 없습니다. 서버가 샌드박스의 포트 제한에 걸리면 실행 권한이 필요합니다. 제품 API/자동 수집 서버가 아닙니다.

## 이번 완료 경계

오프라인 중앙 프로젝트 대시보드가 이번 범위입니다. 실제 여러 PC에서의 자동 수집·원격 인증/서비스 운영·배포는 후속입니다. 합성 시연 및 사용자 제공 검사 기록을 실제 앱 자동 전달 증거로 표현하지 않습니다.
