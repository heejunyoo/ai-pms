# 합성 입력

`python3 specs/ai-pms-dashboard/sample/generate.py`로 중앙 저장 snapshot, manifest, JSONL 원본과 catalog를 결정적으로 다시 만듭니다. `generate.py OUTPUT_DIR`로 별도 폴더를 사용할 수 있습니다. 실제 사람·환경의 기록이 아니며 catalog의 command는 실행하지 않습니다.

Alice는 2개 환경과 3개 세션, PRD→설계 v1/v2→구현 문서를 연결합니다. Bob은 Alice와 같은 원본 project UUID를 사용하지만 별도 사용자·프로젝트입니다. Bob은 설계 단계 검사를 통과해도 전체 검사가 실패합니다. Carol은 v1 완료 후 v2 검사가 없어 재검증 상태입니다. Dana는 완료 기준이 없습니다. 미연결 Eve 출처도 목록에서 보존합니다.

검사 정의를 변경하면 기존 검사 기록을 새 기준에 적용하지 않습니다. 새 기준으로 실행한 결과를 수동 입력할 때 다음처럼 signature를 만드세요. 정의 변경 후 이전 기록에 새 signature만 붙이는 것은 유효한 재검증이 아닙니다.

```python
from portfolio import criterion_signature
run['criterion_signature'] = criterion_signature(criterion)
```

signature는 `id,label,scope,target_id,command,expected_exit_code` 여섯 필드의 정렬된 canonical JSON(`ensure_ascii=True`, `separators=(',', ':')`) SHA-256입니다. 가져온 기록의 진위나 실제 실행을 암호학적으로 증명하는 서명은 아닙니다.
