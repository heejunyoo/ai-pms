# Harness Kit × AI PMS ELI20 전체 설명

index.html은 정본인 자기완결 한국어 설명입니다. 기존 scripts/build_dashboard_app.py가 apps/dashboard/public/overview.html로 복사하고 해당 route에 script hash CSP를 생성합니다. 외부 폰트/스크립트/API 호출 없이 읽을 수 있으며 공개 자료 열기 버튼만 명시적으로 외부 페이지를 엽니다.

주제: 전체 관계, 현재 Kit 범위, AI PMS의 원래 목적과 데이터/화면 설계, 가상의 공동 작업 흐름, 구현/검증 경계, 다음 운영 인수와 확장 제안. 한 번에 한 주제를 표시하며 단계 선택은 도해 활성 상태와 설명을 함께 바꿉니다.

검사: python3 ~/.agents/skills/eli5/check.py reports/harness-pms-eli20/index.html
빌드: python3 scripts/build_dashboard_app.py
배포: 기존 승인된 apps/dashboard Vercel 프로젝트. Kit는 canonical current_content.py의 overview 연결과 reference ZIP을 갱신합니다. 새로운 hosting 계정/인증/API 계약은 없습니다.

Astra 내용 검토는 content-review.json, 부모 실제 브라우저/공개 파일 결과는 release-proof.json을 확인하세요. 기술/내용/렌더/실제 원격 전달은 별도 증거입니다. 공개 예시는 합성이고 실제 native provider hook와 원격 두 사용자 운영 인수는 미검증입니다.

2026-10-03 준비본: 기본 화면을 목표·단계 목표·API/MCP 참조·달성 상태로 줄였습니다. 원본은 분석 근거에 보존합니다. 실제 모델 분석은 미실행입니다. 이전 release-proof는 이전 공개본의 증거이며 이번 준비본의 배포/브라우저 증거가 아닙니다.
