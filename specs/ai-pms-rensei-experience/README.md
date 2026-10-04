# 사람 중심 화면 개선 인수

Rensei 후보를 사람 관점의 단계 흐름·판단 필요 처리함으로 구현합니다. [범위](../../docs/rensei-experience.md), [원자 계획](plan.json), [통합 영수증](integration-proof.json), [Astra 최종 검토](final-review.json)를 확인하세요.

```sh
python3 specs/ai-pms-rensei-experience/check_experience.py
python3 scripts/verify_public.py
```

검사는 실제 model 판정을 보존한 simulated DOM 회귀입니다. 실제 렌더·390px·브라우저 history/reload·실제 provider 훅·원격 두 사용자 운영·모델 분석은 별도 인수입니다. 이전 릴리스의 화면 캡처와 현재 소스 검사를 섞지 않습니다.
