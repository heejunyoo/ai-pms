# 부모 인수 검증 독립 검토

검토자: independent-central-reviewer. 대상: verify_acceptance.py, runtime-observation.md. 최초 판정: 수정 필요. 현재 재검토 판정은 아래에 기록한다. 구현 테스트와 실제 브라우저 인수는 아직 이 검토에서 실행하지 않았다.

## 실제 결함

1. **높음 — HTML/부모 브라우저 관측 기록을 필수로 검증하지 않는다.** artifacts 개수 >= 3 및 각 파일 해시만 검사한다. 역할/확장자/서로 다른 경로/관측 대상 HTML과 기록의 연결을 확인하지 않아 하나의 임의 텍스트 파일을 세 번 나열해도 통과한다. 명세의 실제 생성 HTML과 부모 관측 기록 SHA-256 요구를 강제하지 못한다. 독립 임시 디렉터리에서 unrelated.txt 한 개를 세 번 등록한 증거로 통과를 재현했다. 구현 테스트 subprocess만 mock하여 증거 검증을 분리한 재현이며 실제 제품 인수 성공이 아니다. HTML과 관측 기록을 명시적 서로 다른 필수 artifact 역할로 지정하고, 경로/해시 및 관측 대상 HTML 연결을 검사해야 한다. artifacts 경로는 현재 절대 경로와 상위 경로도 허용한다. 인수 산출물 루트 안으로 제한하는 편이 적절하다.
2. **중간 — assert에 의존한 완료 관문이 최적화 실행에서 제거된다.** python3 -O 또는 PYTHONOPTIMIZE 환경에서는 scope/합성 모드/실제 전달 미완료/제품 미완료/브라우저 상태/파일 해시 검증이 모두 사라진다. 잘못된 증거에는 명시적 예외 또는 실패 종료를 사용해야 한다. 고정 명령이 일반 python3여도 PYTHONOPTIMIZE 환경으로 이 문제가 발생할 수 있다.

## 요구사항별 정렬과 경계

- central-1: runtime-observation은 현재 logger 배선과 로그 디렉터리의 부재를 제한된 파일 조사로만 표현한다. 실제 전달 미검증 경계를 유지하며 두 사용자 전달 완료를 주장하지 않는다. 검증기에는 actual_multi_user_delivery_verified=false가 있으나 최적화에서도 강제해야 한다.
- central-2: multi_project_list 플래그를 요구하지만 목표/Phase/최근 변경/Agent/결과물/관리 항목의 실제 표시 내용과 해당 HTML을 직접 검사하지 않는다. 부모 관측 기록이 그 내용을 남겨야 하며 검증기는 정확한 산출물 종류/연결을 강제해야 한다.
- central-3: project_detail/original_event 플래그는 선언을 검사한다. 목록→선택 프로젝트→해당 원문 이벤트로 이어진 부모 관측이 필요하다.
- central-4: 구현 테스트 재실행에 위임한다. browser_checks에는 누락/미연결/지연을 확인한 관리자 관측 항목이 없다. 구현 테스트의 실제 커버리지와 화면 표현은 후속 구현 검토에서 확인해야 한다.
- central-5: 합성 및 product_complete=false 경계를 보존하고 구현 테스트 이외의 부모 증거를 요구한다는 방향은 정렬된다. 위 결함을 고쳐야 명세상 최종 관문을 실제 강제한다.

runtime-observation.md는 설정 두 파일과 기본 위치만 조사했다고 범위를 좁히며 전체 배선 부재로 확대하지 않는다. 실제 도구 실행→로컬 기록→전송→중앙 원문을 별도 검증해야 한다는 설명도 원문에 정렬된다. 이 문서의 조사 내용 자체를 독립적으로 재확인한 검토는 아니다.

파일 해시와 부모 관측 영수증은 증거의 일관성을 확인한다. 부모 실제 UI 실행의 진실성이나 의미적 충족을 암호학적으로 증명하지 않으며, 본 검토도 이를 증명했다고 주장하지 않는다.

## 수정본 재검토 — 수용

verify_acceptance.py 수정본을 직접 읽었다. require()가 명시적 ValueError를 발생시켜 최적화 실행에서도 검증이 유지된다. artifact 세 개에 central-dashboard/central-empty/browser-observation 역할을 정확히 요구하고 서로 다른 resolve된 루트 내부 파일 경로, HTML/Markdown 형식, 각 파일의 실제 SHA-256을 검사한다. 기존 동일 임의 파일 세 번 및 최적화 관문 제거 결함은 수정되었다. 부모 evidence에서 세 파일을 함께 명시하므로 관측 대상 산출물 집합은 식별된다.

독립 실행: python3 specs/ai-pms-central/verify_acceptance.py --selftest 및 python3 -O specs/ai-pms-central/verify_acceptance.py --selftest 모두 exit 0, acceptance guard selftest OK. 제품완료/실제 전달완료/중복 파일/오래된 hash/mobile 누락을 거부하는 실행 가능한 검사가 유지된다.

central-1..5의 로컬 준비 단계 인수 관문으로 수용한다. 이는 구현 완료 또는 실제 브라우저 인수 완료 판정이 아니다. 브라우저 관측 Markdown의 실제 실행 진실성 및 각 요구사항 표시 내용은 부모 실제 관측과 독립 구현 검토의 책임으로 남는다. 현재 Markdown 형식/최소 길이 검사 자체가 UI 의미 정합성을 증명하지 않는다. 전체 verify_acceptance.py 본 명령은 이 재검토에서 실행하지 않았다.
