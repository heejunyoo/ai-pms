# 부모 실제 브라우저 관측 — 2026-10-01

검증 대상은 로컬 파일 기반 중앙 대시보드와 ELI20 보고서입니다. Chrome CUA로 제한된 loopback HTTP 개발 미리보기를 열었습니다. 검증 도구가 file: 프로토콜을 차단하므로 브라우저 권한을 확대하지 않고, 지정된 생성 HTML·보고서 참조 문서만 제공하는 개발 경로에서 확인했습니다. 일반 사용자용 산출물은 외부 리소스 없는 HTML 파일입니다.

## 최종 코드에서 확인한 흐름

- 현황: 5개 사용자·프로젝트, Alice 완료 / Bob 검사 실패 / Carol 재검증 / Dana 기준 미관측 / Eve 출처 미연결. Alice 2환경·3세션과 Bob의 동일 원본 UUID가 별도 프로젝트로 보입니다.
- 검색·사용자·상태·단계 복합 필터로 Bob 또는 Alice 한 프로젝트만 표시했습니다. 검색 결과 없음과 초기화 복원도 확인했습니다.
- Alice 상세에서 전체 검사 통과, 설계 단계 검사, 개별 작업 검사 적용 범위를 확인했습니다. Bob은 설계 단계 완료에도 전체 검사 실패입니다. Carol은 현재 v2와 과거 v1 검사 및 완료 milestone을 구분합니다.
- 문서 버전 선택: 회상 흐름 설계 v1(요약 중심)과 v2(출처 확인·부분 결과 안내)의 실제 본문·세션·환경이 바뀌었습니다. 버전 중복 접두어 vv1을 발견·수정 후 v1/v2로 확인했습니다.
- 세션 탭: Alice laptop의 alice-1/alice-2와 desktop의 alice-3, 총2출처·3세션이 보입니다.
- 시간 흐름에서 실제 event JSON을 펼치고 event_id와 source actor/environment, file_sha256, 원본 line을 확인했습니다. 390px에서도 원본과 긴 해시가 가로 넘침 없이 보입니다.
- 상세 탭 ArrowRight로 문서 탭을 선택했습니다. browser back으로 돌아올 때 owner=Alice/status=complete/phase=구현 필터와 상세 보기 trigger 초점이 유지됐습니다.
- 미관측 기준 상세는 완료로 표시하지 않으며 기준 없음 문구를 보여줍니다. 전달 지표나 이벤트 개수를 완료율로 사용하지 않습니다.

## 가져오기와 내보내기

native filechooser.setFiles는 Chrome 확장의 로컬 파일 권한으로 차단됐습니다. 실제 파일 선택→File.text 경로는 이번 브라우저에서 미검증입니다. 권한을 바꾸지 않았습니다.

대신 정상 제품 입력인 JSON 붙여넣기 모달에서 파일과 공통인 applySnapshot 처리 경로를 실제 검증했습니다. 잘못된 JSON 문법은 오류를 보여주며 기존 Alice 상세와 모델을 유지했습니다. 빈 snapshot 적용은 프로젝트0/빈 안내로 바뀌었고, 현재 생성 snapshot 전체를 붙여넣으면 5프로젝트·상세가 복원됐습니다. 취소는 기존 모델을 유지합니다. 390px 모달 폭352px, 문서 폭390px입니다.

현황 내보내기 버튼 클릭으로 Downloads에 실제 ai-pms-snapshot.json 파일이 생성됐습니다. 브라우저 download 이벤트 대기는 timeout했으나 파일 생성과 JSON 동일성을 별도로 확인했습니다. 파일28104bytes, 현재 evidence/snapshot.json과 JSON 동등, SHA256=260b1d71b5d8a698b6a16ca4a02bc801079c7c44d69565ca641e38eb8f170ae3입니다. 이와 JSON 동등한 현재 embedded snapshot의 정상 붙여넣기 복원을 확인했습니다. native picker로 내보낸 파일을 선택했다는 의미는 아닙니다.

## 화면 검증

최종 현황을 실제 screenshot으로 확인했습니다. 헤더 내보내기 버튼의 흰색 글자/흰색 배경을 수정했고 foreground rgb(23,37,50)를 확인했습니다. 기본 desktop viewport1920px, 문서폭1920px. 모바일390×844에서 현황·문서·원본·붙여넣기 모달 문서폭390px, 가로 넘침 없음입니다. 최종 생성 empty.html도 실제 별도 탭에서 프로젝트0 및 입력 안내를 확인했습니다.

ELI20 보고서의 목적·설계/구현/전체 검사 통과/완료 후 변경 네 버튼에서 card active/passed/stale class 및 표시 상태가 실제로 바뀌었습니다. Enter로 원래 상태 복원, 선택 aria-pressed, 보고서390px 문서폭390px을 확인했습니다. 보고서의 대시보드 링크 클릭으로 실제 중앙 현황이 열리고 browser back으로 보고서가 복원됩니다.

## 증거 경계

자료는 합성 데모입니다. 자동 수집·실제 여러 PC의 전달·원격 운영 배포의 검증이 아닙니다. 검사 명령은 가져온 선언이며 UI가 실행하지 않습니다. 관련 결과물 변경 시 current_revision은 수동으로 갱신합니다. 검사 정의가 바뀐 옛 완료 이력은 변경 전 snapshot을 보관해야 합니다.

browser-verification.json은 이 관측과 현재 코드·생성 HTML·입력 snapshot의 해시를 연결합니다. 해시는 관측의 신선도를 확인하며 의미상 정확성을 자체 증명하지 않습니다. verify_dashboard.py는 새 브라우저를 자동 실행하지 않습니다.
