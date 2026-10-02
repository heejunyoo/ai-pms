# 토스 원칙 반영 IA 독립 목적 검토

판정: **aligned**. 사용자 원문·spec·plan·PRODUCT-INTENT.md를 직접 대조했습니다. 사람 범위 → 판단할 작업 → 프로젝트 목표/책임 작업의 흐름은 기존 중앙 관리 목적을 보존하면서 필요한 행동을 먼저 보여줍니다. 기록 근거와 문서는 점진적으로 펼치되 삭제하지 않으며, 개입에서 정확한 작업으로 이동하도록 한 설계가 적절합니다.

[토스 Product Principles](https://toss.im/tossfeed/article/tossproductprinciples)와 [UX Writing 인터뷰](https://toss.im/tossfeed/article/uxwriter-interview)를 직접 확인했습니다. 가치와 다음 행동을 먼저 드러내고 핵심 메시지와 익숙한 언어에 집중한다는 원칙을 PMS에 적용한 해석으로 타당합니다. 공식 TDS 설치나 토스 제품 자체 구현을 주장하지 않는 경계도 명확합니다.

초기 plan은 기존 check_ui_work.py만 인수 명령으로 사용해 IA 변경이 없어도 통과할 수 있었습니다. 부모가 세 인수 명령을 check_ia.py로 변경했습니다. 새 검사는 IA 순서·펼침 안의 기존 기능 접근·정확한 task focus를 검사하고 기존 work 검사를 호출해야 합니다.

데이터 계약·검증 완료 계산·사람 귀속·자동 수집 유예를 유지합니다. 이 승인은 목적·설계 정합성에 한정합니다. 실제 구현과 키보드/초점·데스크톱/390px 브라우저·공개 반영은 후속 인수 근거가 필요합니다.
