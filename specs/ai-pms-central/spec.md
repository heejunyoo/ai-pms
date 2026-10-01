# 중앙 AI PMS — 로컬 중앙 수집 최소 흐름

정본: ../../PRODUCT-INTENT.md. 여러 사용자 환경 → 중앙 파일 저장/집계 → 다중 프로젝트 관리자 목록 → 원본 근거 상세를 구현한다. 개인용 작업 UI 확장이 아니다. 기존 logger v1과 글로벌 훅, API 계약, DB, 배포 설정을 변경하지 않는다.

## 조사와 기준선

- ~/.claude/harness/activity/logger.py: base_event, hook_event, record_event, LINKS, DATA, REQUIRED. v1에는 actor/environment 식별이 없다. session/agent 식별은 nullable이며 model을 뜻하지 않는다.
- project_id는 로컬 UUID. 중앙에서 같은 UUID라고 다른 출처를 합치지 않는다. baseline은 phase_id+baseline_version, artifact/check는 artifact_id+artifact_version의 정확한 일치가 필요하다.
- logger의 manual record는 goal/scope, decision reason, 산출물, 검사, 인수를 선언할 수 있다. 훅 자체로 목표/판단을 확정하지 않는다.
- 개인정보 제한, owner-only 파일, flock, bounded input은 재사용 후보. 개인 viewer는 제품 주 흐름으로 재사용하지 않는다.
- 실행 기준선: python3 -m unittest test_logger.py (activity 디렉터리) 10 tests OK. 새 인수 명령 python3 specs/ai-pms-central/test_central.py는 구현 전 파일 없음 exit 2로 확인했다.

## 확정 설계

Python stdlib CLI central.py import --manifest FILE --store DIR; central.py render --store DIR --output FILE. 서버나 신규 API 없이 중앙 저장 파일과 독립 HTML을 생성한다. 로컬 가져오기는 자동 전달이나 두 실제 사용자의 증거가 아니다.

manifest는 로컬 운영 입력: sources 배열에 actor_id, environment_id, project_id, label, evidence_mode(synthetic/local-execution), files(상대 JSONL 경로)를 명시한다. 동일 actor/environment/project는 합치되 동일 project UUID라도 다른 actor/environment는 분리한다. 상위 출처 선언을 신뢰 경계로 표시하며 인증되었다고 표현하지 않는다. 파일 경로/manifest 원문은 공개 HTML/저장 이벤트에 넣지 않는다. expected sources가 파일 없음/빈 파일/실패여도 관리자에 나타난다.

store는 owner-only JSON 파일(원자 교체+동시 import 잠금)이며 DB 스키마가 아니다. v1 이벤트를 변경하지 않고 외부 출처 context와 received_at, 파일 해시/행 번호로 근거를 감싼다. 검증은 allowlist/필수 타입/UUID/시간/버전/민감정보를 확인하고 잘못된 입력의 원문은 저장하지 않는다. source/project 불일치 거부. 크기/행 수 한도는 명시하고 초과를 관리 항목으로 보인다. 재수집은 출처 context+event_id로 멱등; 내용이 다른 같은 ID는 conflict로 표시하며 기존 기록을 덮지 않는다. 실패/충돌/중복/마지막 수집 상태를 보존한다. received_at은 최초 수집 시점, 반복 import로 이벤트 최신성을 갱신하지 않는다.

목표/Phase는 가장 최근 유효 baseline 선언에서, 범위 변경은 decision 선언에서 보인다. 존재하지 않는 baseline에 연결된 decision은 미연결이다. 검사는 정확한 프로젝트/산출물/버전과 연결하고 검증 불일치·목표 없음·Phase 불명·미연결 Agent·수집 오류·지연을 따로 표시한다. 최신 여부는 observed_at(관측 시각)으로 표시하며 occurred_at 없음을 숨기지 않는다. 24시간 기본 지연 기준은 명시, 미래 시간은 정상 최신으로 취급하지 않는다. tool.completed/Stop/pass가 프로젝트 완료/사용자 인수를 뜻하지 않는다.

HTML은 한국어 반응형, 접근 가능한 표/필터/버튼, 여러 프로젝트를 한눈에 비교한다. actor/environment, goal, Phase, 최근 scope change, agent/artifact/check, 관리 항목과 출처 모드를 보인다. 프로젝트 선택 → 정확한 연결과 원본 event JSON(개인 경로/명령 제외), event ID/해시/행 번호로 내려간다. 빈 상태에 import CLI와 파일 계약 안내. 합성 증거 배너를 유지한다. 사용자 내용은 textContent만 사용, JSON script 주입은 </script> 등을 안전하게 처리, 외부 fetch/assets 없음.

## 인수와 범위

test_central.py는 실제 logger subprocess로 독립된 임시 로그 디렉터리 두 개를 생성하고 중앙 CLI를 두 번 실행해 멱등 수집, UUID 충돌 분리, 잘못된/비밀 입력 거부, 누락/지연/미래 시간, baseline/artifact/check 교차 귀속 방지, 충돌, HTML 근거를 검사한다. 합성 픽스처임을 명시한다. sample/manifest.json과 source-a.jsonl/source-b.jsonl은 재현 가능한 합성 데모만 제공한다. README.md에 실행·로컬 형식·한도·불완전 전달 경계를 남긴다. 부모는 데모 중앙 CLI와 실제 브라우저 목록→프로젝트→원본, 모바일/빈 상태를 별도 검증한다.

수정 허용: 이 specs/ai-pms-central/ 아래 central.py, test_central.py, README.md, sample/ 파일 및 task result.json. 정본/명세/글로벌 설정/기존 테스트 변경 금지. 실패 시 신규 디렉터리만 사용 중지하며 기존 기록기를 보존한다. 실제 자동 전송 방식/인증/중앙 서비스 배포는 별도 명세와 환경 승인 이후 진행한다.

## 부모 최종 인수 관문

이번 패킷은 로컬 중앙 흐름 준비 단계이며 제품 인수 1의 실제 두 사용자 환경 전달 증거는 미달이다. 구현 테스트만으로 Phase를 닫지 않는다. 부모 전용 verify_acceptance.py는 구현 테스트 재실행, 부모의 acceptance-evidence.json 및 실제 생성된 HTML/부모 브라우저 관측 기록의 SHA-256, 목록→상세→원본과 모바일/빈 상태 확인 결과를 검사한다. evidence에는 scope=local-central-flow, evidence_mode=synthetic, actual_multi_user_delivery_verified=false, product_complete=false를 반드시 명시한다. 최종 명령: python3 specs/ai-pms-central/verify_acceptance.py. 실환경 자동 전달을 로컬 검증 성공으로 승격할 수 없다. 부모만 인수 스크립트와 증거를 작성한다.
