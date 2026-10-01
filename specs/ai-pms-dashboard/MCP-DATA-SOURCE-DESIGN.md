# MCP·데이터 소스 시각화 및 로컬 로깅 확장안

상태: 타당성 확인 및 구체 제안. 아직 화면·기록기 구현을 변경하지 않았습니다. 자동 전송은 기존 사용자 요청대로 후속입니다.

## 사용자가 알고 싶은 것

> 어떤 MCP 나 Data source 에 접근해서 활용하는지에 대해서도 시각화 추가가 가능할까? 훅에서 이런 부분도 로깅 추가 할 수 있을까?

중앙에서 사용자별 프로젝트가 어떤 외부 도구·데이터에 의존하는지, 어떤 세션에서 접근했고 그 근거가 무엇인지 확인합니다. 접근 호출과 실제 산출물의 활용은 구분합니다.

## 현재 소스의 제한

`~/.claude/harness/activity/logger.py:131-134`는 mcp__server__tool 이름을 MCP로 정규화합니다. 구체 서버·도구 이름은 보존하지 않으며 tool_input/tool_response도 기록하지 않습니다. 기존 중앙 valid_event는 관측 이벤트 data를 빈 객체로 제한하므로 logger 한 곳만 고치면 중앙에서 새 기록이 거부됩니다. 이전 generic MCP 기록에서 서버·도구·데이터 소스를 복원할 수 없습니다.

## 공식 지원 확인 (2026-10-01)

- Claude Code: MCP 이름 mcp__server__tool, PreToolUse/PostToolUse/Failure; tool_input/tool_response 및 MCP server metadata. https://code.claude.com/docs/en/hooks
- Codex: 로컬 MCP PreToolUse/PostToolUse 관측 지원. hosted WebSearch 등은 같은 로컬 훅 경로에 포함되지 않음. https://learn.chatgpt.com/docs/hooks
- Cursor: beforeMCPExecution/afterMCPExecution; 후자는 tool_name/tool_input/mcp_server_name/result_json/duration. cloud agents 제약은 별도. https://cursor.com/docs/hooks
- Gemini CLI: BeforeTool/AfterTool, tool_name/tool_input/tool_response/mcp_context. https://geminicli.com/docs/hooks/reference/

공식 지원은 현재 각 사용자 환경의 설치 버전·trust·활성화와 실제 이벤트 전달을 증명하지 않습니다. 어댑터별 실제 원본을 관측해야 합니다.

## 기록 후보와 근거

1. 기존 actor/environment/project/session/agent/tool_call_id로 프로젝트와 실행을 연결.
2. tool_identity: 안전한 raw 이름, server_alias, tool_name, transport 종류(확인된 경우).
3. 호출 상태: requested/completed/failed/unknown. pre 이벤트는 실행 성공이 아니며 결과의 error와 failure 이벤트를 확인. duration_ms는 제공되거나 정확히 상관된 pre/post일 때만 기록.
4. data_refs: type=db/document/repository/api/file, 로컬 논리 resource_id, 안전한 표시 이름, evidence=input/output/declared/unknown. 호스트·DB·문서 ID·저장소가 드러난 허용 필드만 서버별 어댑터가 추출. 자유 SQL/검색어/원문 결과에서 임의 자원을 추정하지 않음.
5. operation: read/write/delete/unknown. 검토된 도구 정의·입력의 명시적 작업 종류로만 확정. 도구 이름에 query가 있다고 모든 SQL을 읽기로 가정하지 않음.
6. 사용 연결: 단계/문서/결과물과 source 참조를 명시적으로 연결하면 활용 근거. 호출한 뒤 문서를 작성했다는 시각상 인접성만으로 해당 문서가 그 source를 사용했다고 판정하지 않음.

서버 alias=supabase가 같아도 사용자·환경별 실제 계정/DB가 같다는 뜻이 아닙니다. 출처를 actor/environment와 함께 구분하고 공통 자원은 확인된 mapping으로만 합칩니다. 일반 MCP 서버가 내부에서 호출한 모든 하위 DB/API를 훅이 보장해 관측하지는 못합니다. 필요할 때 MCP 서버측 metadata/audit 또는 소스 선언을 보완합니다. 설치/설정·실제 호출·데이터 접근 확인·산출물 참조 상태는 별도 표시합니다.

## 시각화 방향

- 프로젝트 상세에 연결 자원 탭: 세션/에이전트 → MCP 서버/도구 → 확인된 데이터 소스, 문서·산출물에 명시된 참조 연결.
- 실선=호출·입출력에 확인된 관계, 점선=선언 또는 후보; 미관측 자원은 빈 노드/불명 상태. installed 표시만으로 호출선을 만들지 않음.
- 프로젝트 카드에 관측된 연결 요약. 중앙 자원 목록에서는 관련 사용자/프로젝트, 호출·실패 기록과 읽기/쓰기 범위를 비교. 단순 호출 수를 생산성으로 순위화하지 않음.
- 자동 수집 전에 로컬 snapshot의 명시적 입력으로 화면을 구현할 수 있음. 이후 같은 의미의 로컬 훅 로그를 가져오기 경로에 연결하며 webhook이 필수 조건은 아님.

## 기록 경계와 구현 순서

자격정보·전체 도구 입력/응답·SQL·문서본문을 무조건 로깅하지 않습니다. 필요한 metadata만 allowlist 추출하고 URI query/userinfo, private paths는 제외 또는 승인된 논리 식별자로 바꿉니다.

화면 구현과 로컬 자료 입력은 기존 승인 범위 안에서 준비할 수 있습니다. 실제 로깅 확장은 logger→central validator→transport validator→version compatibility→뷰 변환을 함께 변경해야 합니다. 기존 수신 이벤트 계약 변경은 상위 AGENTS.md Ask-Before-Act 대상이므로 변경 명세·독립 검토·하위 호환 방식을 준비한 뒤 구체 승인을 받습니다. 훅 전역 설정·trust·실제 PC 배선은 별도이며 이번 타당성 조사에서 변경하지 않았습니다.
