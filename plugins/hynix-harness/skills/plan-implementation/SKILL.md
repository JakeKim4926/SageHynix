---
name: plan-implementation
description: INTENT의 요구사항을 우선순위와 남은 시간에 맞춰 수직 슬라이스(데이터→로직→출력까지 작동하는 최소 단위)로 나누고 docs/PLAN.md를 작성하거나 다시 짠다. 파일이 겹치지 않는 슬라이스는 git worktree 병렬 레인으로 나눈다. 조사 후 구현 착수 전, 시간이 밀려 범위를 다시 잡을 때, 병렬 구현을 검토할 때 사용.
---

# plan-implementation

끝나면 `docs/PLAN.md`에 사용자가 승인한 슬라이스 표와 범위 밖 목록이 있고, 첫 슬라이스를 바로 시작할 수 있다.

## 입력
- `docs/INTENT.md`(R/A/Q), `ctx/INDEX.md`의 valid 항목(특히 `research/synthesis`, `decision/*`은 `ctx.py get`으로 읽는다), `.harness/bin/clock.sh status`의 남은 시간.

## 진행
1. **첫 슬라이스는 가장 얇은 종단 간 경로**로 잡는다: 실제 데이터 로딩 → 핵심 계산 1개 → 결과 출력(화면이나 파일).
2. 슬라이스 표를 채운다: 충족 R-n, 수용 기준, 검증 방법(테스트, 명령, 화면 확인), 예상 시간(분). 30분이 넘는 슬라이스는 쪼갠다.
3. 범위 밖 목록을 적는다. 하지 않기로 한 것도 의도의 일부다.
4. 선택지가 있던 판단(방법, 라이브러리, 화면 형태)은 `python3 .harness/bin/ctx.py new decision {주제} --uses {근거 ctx ID}`로 남기고, `docs/DECISIONS.md`에 D-n 요약과 ID를 적는다.
5. 파일이 겹치지 않고 각각 30분 이상인 슬라이스가 2개 이상이면 병렬 레인을 제안한다. 레인 사이 인터페이스가 아직 불확실하면 제안하지 않는다. 승인되면 [references/worktree-lanes.md](references/worktree-lanes.md)를 읽고 따른다.
6. 계획 요약을 보여 주고 승인을 받은 뒤 구현을 시작한다.

**재계획**: 남은 시간이 남은 슬라이스 예상 합계의 1.3배보다 적으면 다시 짠다. Could, Should 순으로 잘라 내고, 잘라 낸 것과 이유를 DECISIONS에 적고 INTENT 상태를 `범위 제외`로 바꾼다.

## 제약
- Must 슬라이스 합계가 남은 Build 시간의 70%를 넘지 않게 한다(검증과 문서 몫).
- 계획에 없는 기능을 구현 중에 끼워 넣지 않는다. 필요하면 PLAN부터 고친다.

## 완료 기준
- 모든 Must R-n이 어느 슬라이스에 들어가 있거나 `범위 제외`로 기록돼 있다.
- 사용자가 계획을 승인했다.

## 출력
- 사용자 보고: 슬라이스 표, 범위 밖, 승인 요청.
- 커밋: `docs(plan): 슬라이스 S1~S4 계획 — R-1,R-2 우선`
