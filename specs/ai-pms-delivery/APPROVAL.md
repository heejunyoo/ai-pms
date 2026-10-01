# 실환경 전달 승인 범위 제안 — 현재 미승인

현재 `api_implementation_approved=false`, `actual_delivery_verified=false`, `product_complete=false`입니다. 이 파일은 승인 기록이 아닙니다. [spec.md](spec.md)는 구현 전 제안 계약이며 현행 API가 아닙니다.

## A. 로컬 구현 승인을 요청할 범위

승인 시에만 새 handoff 패킷으로 stdlib sender/receiver, 인증 context 등록, owner-only outbox·immutable inbox·집계 상태 파일, `POST /v1/events` 제안 계약, 기존 central import/render 연결을 구현합니다. 검증은 loopback(127.0.0.1 또는 ::1)과 합성 자격·이벤트로 제한합니다. 실제 사용자 훅·전역 설정·신뢰 승인, 실제 비밀 생성, 외부 HTTPS 전송, 포트 공개, 서비스 자동 시작, 배포는 A에 포함되지 않습니다. 인증·멱등 ACK·재시도·저장 실패·충돌·화면 반영을 별도 반례 검사하고 기존 테스트를 보존합니다.

## B. 실제 운영은 별도 승인이 필요한 범위

외부 HTTPS 목적지와 관리 호스트, 참여자 동의와 actor/environment/project 등록, 실제 환경별 자격 발급·보관, 앱 훅 설치 및 trust, 데이터 보관·삭제·관리자 열람 범위, 네트워크/방화벽/배포를 각각 실제 환경에 맞게 확정한 뒤 요청합니다. A의 loopback 성공은 B의 권한이나 실제 전달 증거가 아닙니다. 관리자 공개 웹 접속은 별도의 인증·배포 결정 없이는 제공하지 않습니다.

승인 후에도 [RUNBOOK.md](RUNBOOK.md)의 서로 다른 두 실제 사용자 앱 → logger → outbox → 인증 수신함 → 중앙 집계 → 관리자 원본 대조를 통과해야 실제 전달을 검증했다고 기록할 수 있습니다. 현재 준비 검사의 실행 결과는 알려진 로컬 설정의 logger **후보 선언 수**이며, 실환경 전달과 제품 완료 플래그는 계속 false입니다.
