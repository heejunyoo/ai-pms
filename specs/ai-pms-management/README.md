# 중앙 관리 v3

목표·회사 위임·개인 프로젝트·원문 요구사항·계획/검사 계획의 버전과 이유·실행 시도·막힘·Kit 개선·선택적 Graphify 근거를 연결합니다. PC 자동 전달은 제외합니다.

## 사용 순서

1. Kit implementation.zip의 activity/ 폴더를 안내대로 배치합니다. catalog-v3.template.json과 json-contracts.md를 확인하고 프로젝트의 실제 목표·사용자/환경·검사 기준·manifest 파일 범위를 지정합니다. 0으로 채운 파일 해시는 예시이므로 그대로 실행하지 않습니다.
2. 기존 Handoff 계획/결과를 management_recorder.py의 handoff 명령으로 가져옵니다. README의 명령 예시를 따릅니다. importer는 검토한 기준과 실행 명령·예상 종료코드가 일치해야 연결하며, 결과는 declared로 보존합니다.
3. run 명령으로 검사를 실제 실행합니다. 실패 후 수정·재실행하면 새 시도가 추가됩니다. 검사 파일을 변경하면 검사 계획 버전을 명시적으로 갱신해야 합니다.
4. v3 catalog로 중앙 화면용 snapshot을 만듭니다. 훅 활동은 --store로 함께 제공할 수 있습니다. 다른 PC 파일은 중앙 import 전에 actor/environment/project를 검토해 연결합니다.

```sh
python3 specs/ai-pms-dashboard/portfolio.py --catalog my-catalog.json --out dashboard.html --json-out snapshot.json
python3 specs/ai-pms-management/verify_management.py
```

snapshot.json을 공개 대시보드에 붙여넣어 사용할 수 있습니다. 브라우저에서 처리하며 서버로 업로드하지 않습니다. 공개 샘플은 합성 데이터입니다. 로컬 run은 네트워크 전송 없이 명령을 실행하므로 실행할 명령의 목적과 파일 범위를 먼저 확인합니다.

## 근거 경계

runner 기록은 실제 로컬 실행 관측이지만 외부 인증된 서명은 아닙니다. manifest는 명시된 파일에만 적용되며 포괄성은 선언입니다. timeout/시작 실패는 종료코드 미관측이며 통과로 사용하지 않습니다. 현재 검사 계획·기준·파일 버전이 다르면 과거 통과와 해결 상태를 재검증으로 표시합니다. 기술 조건 충족과 회사 업무 성과는 별도이며 업무 성과는 미관측입니다.

Graphify는 필요할 때만 --graph 또는 graph 명령으로 실행합니다. 별도 프로젝트 경계, code-only/no-cluster, 실제 그래프 파일 검사, 해시 기반 재사용을 적용합니다. HOME/HOME Git 루트와 경계를 벗어난 symlink는 거부합니다. 전역 훅은 설치하지 않습니다. 생성 성공은 AST 구조 자료이며 runtime/coverage 증명이 아닙니다.

실행 검증: test_management.py(모델/참조/해시), Kit test_management_recorder.py(실제 subprocess/Handoff/보존/그래프), check_ui_v3.py(브라우저 입력 검증 parity), exercise_management.py(실제 fail→fix→pass→변경 재검증). verify_management.py --release는 현재 독립 검토·화면·공개 바이트 영수증까지 확인합니다. 과거 dashboard/connectivity/transport release는 당시 범위의 역사적 증거입니다.
