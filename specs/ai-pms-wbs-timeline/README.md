# WBS와 타임라인

목표를 Phase와 원자 작업으로 나누고, 계층형 WBS 행을 일정 막대와 나란히 보여줍니다. 담당자·상태, Phase별 완료 작업 수, 최종 인수 마일스톤을 비교합니다. 사람 필터는 프로젝트 전체 계획을 유지하며 본인 담당을 강조합니다. Phase 또는 작업 선택은 차트 아래에서 완료 조건·검사·막힘·다음 행동의 근거를 펼칩니다.

공개 샘플 날짜는 sample-schedule.json에 작성한 **가상 계획**입니다. 실제 로그 날짜, 납기 추정 또는 에이전트 성과가 아닙니다. 합성 예시의 project_id/plan_id/plan_version/revision에 엄격히 연결합니다. 이 view fixture는 기존 catalog/API 계약을 바꾸지 않습니다. 원문 JSON이나 private live 화면에 일정이 없으면 Phase축을 표시합니다. 선언한 task.depends_on만 의존 관계입니다. Phase 순서 자체가 의존성은 아닙니다.

## 디자인 근거

[TeamGantt Gantt view](https://support.teamgantt.com/article/143-gantt-view/)의 작업 계층과 막대 정렬, [Linear timeline](https://linear.app/docs/timeline)의 절제된 마일스톤 표현을 참고했습니다. 제품 복제가 아니라 현재 PMS의 목표/검증 모델에 맞춘 화면 구성입니다.

## 인수

python3 specs/ai-pms-wbs-timeline/check_timeline.py

기존 check_flow.py는 Phase 선택/최종 gate/사람 scope/live 회귀를 유지합니다. 새 검사는 WBS와 명시적 일정 binding/미입력 fallback/task selection을 확인합니다. 실제 화면 품질·클릭·모바일 스크롤은 부모의 browser-observation.json에 별도 기록합니다. 최신 배포 범위는 release-proof.json이며 실사용자 원격 훅 전달의 증거가 아닙니다.
