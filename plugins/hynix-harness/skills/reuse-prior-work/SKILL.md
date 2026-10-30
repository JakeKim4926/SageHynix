---
name: reuse-prior-work
description: 작업 기억 저장소 ctx/에서 이미 한 조사, 데이터 분석, 결정, 슬라이스 결과, 담당자 답변, 세션 인수인계를 찾아 재사용하고, 새 결과를 남긴다. 조사나 분석을 시작하기 전, 결과를 남길 때, 사용자가 ctx 파일이나 ID를 주거나 다른 세션의 결과를 이어받을 때 사용.
---

# reuse-prior-work

끝나면 같은 조사나 질문을 다시 하지 않고 기존 결과를 ID로 인용했거나, 새 결과가 `valid` 항목으로 남아 있다. `ctx/`는 세션 사이로 넘어가는 유일한 기억이다. 대화 기록이 아니라 결론과 근거 위치만 넘긴다.

## 입력
- 찾을 키워드, 또는 사용자가 준 `@ctx/…` 파일이나 ID. ID가 있으면 그 항목부터 읽고 폴더 전체는 읽지 않는다. 전체 목록은 `ctx/INDEX.md` 한 장이다.

## 진행
명령은 모두 `python3 .harness/bin/ctx.py …`이다(아래에서는 `ctx.py`).

1. **찾기**: `ctx.py find 이상치 탐지`
   | 결과 | 할 일 |
   |---|---|
   | `valid` | `ctx.py get {ID}`로 읽고 그대로 쓴다. 답변에 ID를 인용한다 |
   | `stale` | 이유(입력 변경, 의존 항목 갱신)를 보고 바뀐 부분만 다시 한다 → `new … --redo` |
   | `draft` | 다른 세션이 쓰다 만 것. 이어서 쓰고 `done` |
   | 없음 | 새로 만든다 |
2. **만들기**: `ctx.py new research anomaly --q "이 데이터에 맞는 이상치 탐지 방법과 비용" --serves R-2,R-4 --inputs data/sensor.csv`
   - 종류: `research` `data` `decision` `slice` `prompt` `session` `note`. 폴더 구성은 `ctx/README.md`.
   - SLUG: 영문 소문자, 숫자, `-` (예: `anomaly`, `s3-dashboard`, `1030-1420`).
   - `--q`: 검색은 이 문장과 요약으로 한다. 나중에 찾을 단어를 넣는다.
   - `--inputs`: 결과가 기대는 파일. 바뀌면 자동으로 `stale`.
   - `--uses`: 근거로 쓴 다른 ctx 항목. 그 항목이 다시 작성되면 `stale`.
3. **쓰기**: 생성된 템플릿의 `##` 섹션을 채운다. 주장마다 `[사실|추론]`과 출처(명령, 파일:줄, URL)를 달고, 확인 못 한 것은 `미확인`에 둔다. 요약 섹션(조사는 `결론`, 결정은 `결정`)의 첫 줄이 INDEX 한 줄이 되므로 그 줄만 읽어도 쓸모 있게 쓴다.
4. **완료**: `ctx.py done research/anomaly`. 필수 섹션이 비었거나 입력 파일이 없으면 거부되니 고쳐서 다시 실행한다.
5. **바꾸기**: 새 버전으로 대체하면 새 항목을 만든 뒤 `ctx.py status research/anomaly superseded --by research/anomaly-v2`. 같은 항목을 다시 쓰면 `ctx.py new research anomaly --redo`(이전 본문은 `_prev/`에 남는다). 전체 점검과 INDEX 재생성은 `ctx.py check`.

## 제약
- `ctx/index.jsonl`은 직접 고치지 않는다(훅이 막는다). 메타데이터는 `ctx.py`로만 바꾼다.
- `stale` 항목을 근거로 결정하거나 구현하지 않는다.
- `valid` 항목을 다시 해야 할 이유가 있으면(입력 변경, 결론 의심) `--redo` 전에 사용자에게 한 줄로 알린다.

## 완료 기준
- 새로 만든 항목이 `ctx.py done`을 통과해 `valid`다.

## 출력
- 답변에 사용한 ctx ID를 인용한다.
- 커밋: `docs(ctx): research/anomaly — IsolationForest 우선 (R-2)`
