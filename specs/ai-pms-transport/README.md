# AI PMS 승인 A — 로컬 자동 전달

로컬 sender → 인증 receiver → 영속 inbox → 중앙 집계 → 관리자 HTML을 구현·검증했습니다. 두 합성 환경의 10개 이벤트, 동일 프로젝트 UUID의 사용자·환경 격리, 재시작 중복 방지, heartbeat/작업 구분, 충돌 원본 보존을 실제 loopback HTTP로 확인했습니다.

실제 두 사용자 앱 훅 전달, 외부 서비스·관리자 인증·배포는 미검증입니다. `actual_multi_user_delivery_verified=false`, `product_complete=false`입니다.

프로젝트 루트에서:

```sh
python3 specs/ai-pms-transport/verify_transport.py
```

최종 관문은 handoff 계획·세 반환 계약, 수신·송신·전달 화면 및 기존 중앙 검사, 실제 합성 HTTP 통합을 재실행합니다. 현재 코드·저장 HTML·부모 관측 영수증의 해시도 대조합니다. 저장 브라우저 근거를 확인하며 새 브라우저를 자동 실행하지 않습니다. 샌드박스가 local bind를 막으면 이 검증 명령에 실행 권한이 필요합니다.

직접 열 수 있는 산출물:

- [중앙 목록](evidence/dashboard.html): 작업이 있는 두 환경, heartbeat만 있는 환경, 등록만 된 환경.
- [충돌](evidence/audit.html): 정확한 이벤트 충돌과 기존 목표 보존.
- [상태·저장 오류](evidence/error.html): 전달 상태 불명 및 내부 구조가 손상된 중앙 저장소의 안전한 화면.
- [빈 상태](evidence/empty.html).
- [ELI20 보고서](../../reports/ai-pms-eli20/index.html): 목적·역할·실제 흐름·장애 시나리오·현재 검증 범위.
- [인수 영수증](acceptance-evidence.json), [브라우저 관측](evidence/browser-observation.md), [독립 검토](code-review.md).

수신 ACK는 inbox 저장 확인이며 집계·업무 인수는 별도입니다. 송신기는 반복 실행할 수 있지만 집계·HTML 렌더는 별도 CLI이며 현재 HTML은 생성 시점의 상태입니다. 수신함/전송함 64MiB 파일럿 한도와 보존 정책을 유지하며 무제한 운영을 제공하지 않습니다. 외부 목적지·실제 자격·훅/trust·운영은 승인 B를 구체화한 뒤 진행합니다.

`exercise_transport.py --output DIR`은 새 HTML과 generation 영수증을 만듭니다. 기존 evidence를 갱신하면 부모 브라우저 관측과 인수 영수증도 다시 작성해야 최종 관문을 통과합니다. 이전 중앙·준비 단계 자료는 역사 증거로 보존했습니다.
