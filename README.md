# AI PMS

여러 사용자가 각자 에이전트로 만드는 솔루션을 프로젝트 목표부터 문서·단계·검증·MCP와 데이터 참조까지 한곳에서 살펴보는 중앙 관리 프로토타입입니다.

- [대시보드 샘플](https://ai-pms-dashboard.vercel.app)
- [ELI20 보고서](https://ai-pms-dashboard.vercel.app/report.html)
- [Harness Kit 안내](https://harness-kit.vercel.app/ai-pms.html)

샘플은 5개 합성 프로젝트를 사용합니다. 같은 프로젝트의 여러 세션과 환경은 명시적으로 연결하며, 다른 사용자의 동일 ID나 MCP 별칭은 자동으로 합치지 않습니다. 현재 결과물 버전의 프로젝트 전체 검사 기준이 모두 통과할 때 완료로 표시하고, 변경 후에는 재검증 필요 상태를 유지합니다.

MCP 화면은 설정·요청·성공·실패와 데이터 참조의 선언·입력·출력 근거를 구분합니다. 서버 성공은 내부 DB 접근 증명이 아닙니다. 훅 기록기는 입력·응답 원문, SQL, URL, 개인 파일 경로, 자격 증명을 저장하지 않습니다. 검토한 로컬 resource map과 명시적인 메타데이터만 선택적으로 반영합니다.

## 실행

Python 3.11+와 Node.js가 필요합니다. 별도 Python 패키지는 없습니다.

```sh
python3 scripts/build_dashboard_app.py
python3 -m http.server 21932 --directory apps/dashboard/public
```

브라우저에서 `http://localhost:21932`를 엽니다. 정규화된 snapshot JSON을 파일 또는 붙여넣기로 가져오고 내보낼 수 있습니다. 원격 API나 검사 명령을 실행하지 않습니다.

공개 소스 검사:

```sh
python3 scripts/verify_public.py
```

입력 모델·완료 기준은 [대시보드 안내](specs/ai-pms-dashboard/README.md), 연결 로그 계약은 [연결 명세](specs/ai-pms-connectivity/spec.md), 로컬 기록기는 [Kit 활동 기록 안내](kit/activity/README.md)를 참고하세요. [공개 경계](PUBLIC_SNAPSHOT.md)에는 제외된 개인 자료와 역사적 검증 영수증의 한계를 설명합니다.

각 PC에서 자동 수집하는 연결은 후속 과제입니다. 공개 앱은 합성 샘플을 보여주는 정적 앱이며 실제 다중 PC 전송·앱 훅 전달의 증거로 사용하지 않습니다. 수신·재시도 구현은 `specs/ai-pms-transport`에 포함되며 현재 샘플 앱에는 연결하지 않았습니다.
