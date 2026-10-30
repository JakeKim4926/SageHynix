---
name: ctx
description: 작업 기억 저장소 ctx/ 를 다룬다. 조사·데이터 분석·결정·슬라이스 결과·재사용 프롬프트·세션 인수인계를 ctx/<종류>/<주제>/ 에 남기고, 새 작업 전에 이미 한 것을 찾아 재사용한다(재조사·같은 질문 반복 금지). 조사나 분석을 시작하기 전, 결과를 남길 때, 다른 세션의 결과를 이어받을 때 사용.
---

# ctx — 작업 기억

`ctx/`는 세션 사이로 넘어가는 유일한 기억이다. 대화 기록은 넘기지 않는다. 결론과 근거 위치만 넘긴다.
명령은 모두 `python3 .harness/bin/ctx.py …` (아래에선 `ctx.py`로 줄임).

## 1. 작업 전: 먼저 찾는다 (필수)
```bash
ctx.py find 이상치 탐지        # 키워드 몇 개
```
| 결과 | 할 일 |
|---|---|
| `valid` | `ctx.py get <ID>`로 읽고 그대로 쓴다. **같은 조사·질문을 다시 하지 않는다.** 답변에 ID를 인용 |
| `stale` | 이유(입력 변경/의존 항목 갱신)를 보고, 바뀐 부분만 다시 한다 → `new … --redo` |
| `draft` | 다른 세션이 쓰다 만 것. 이어서 쓰고 `done` |
| 없음 | 새로 만든다 (2) |

사용자가 `@ctx/…` 파일이나 ID를 주면 그 항목부터 읽는다. 폴더 전체를 읽지 않는다 — 목록은 `ctx/INDEX.md` 한 장.

## 2. 새 항목 만들기
```bash
ctx.py new research anomaly --q "이 데이터에 맞는 이상치 탐지 방법과 비용" \
  --serves R-2,R-4 --inputs data/sensor.csv
```
- 종류: `research` `data` `decision` `slice` `prompt` `session` `note` (폴더 구성은 `ctx/README.md`).
- SLUG: 영문 소문자·숫자·`-` (예: `anomaly`, `s3-dashboard`, `1030-1420`).
- `--q`: 무엇을 묻는지/목적. **검색은 이 문장과 요약으로 한다** — 나중에 찾을 단어를 넣는다.
- `--inputs`: 이 결과가 기대는 파일(데이터, README, INTENT). 바뀌면 자동 `stale`.
- `--uses`: 근거로 쓴 다른 ctx 항목(결정이 조사들을 쓰는 경우). 그 항목이 다시 작성되면 `stale`.

## 3. 본문 쓰기 → 완료
- 생성된 템플릿의 `##` 섹션을 채운다. 주장마다 `[사실|추론]`과 출처(명령, 파일:줄, URL). 확인 못 한 것은 `미확인` 섹션에.
- 요약 섹션(조사는 `결론`, 결정은 `결정` …)의 **첫 줄이 INDEX 한 줄**이 된다. 그 줄만 읽어도 쓸모 있게.
```bash
ctx.py done research/anomaly
```
- 필수 섹션이 비었거나 입력 파일이 없으면 거부된다. 고쳐서 다시 실행한다. `valid`가 되면 커밋.

## 4. 바꾸기
- 결론이 틀렸거나 새 버전으로 대체: `ctx.py new research anomaly-v2 --q … ` 작성·완료 후 `ctx.py status research/anomaly superseded --by research/anomaly-v2`
- 다시 작성: `ctx.py new research anomaly --redo` (이전 본문은 `_prev/`에 남는다)
- 전체 점검·INDEX 재생성: `ctx.py check`

## 종류별 쓰임
| 종류 | 언제 | 연결 skill |
|---|---|---|
| research | 조사 레인 하나, 종합(`research/synthesis`, `--uses` 각 레인) | `$parallel-research` |
| data | 데이터 파일 하나의 프로파일과 해석 | `$data-profile` |
| decision | 선택지 비교와 근거 대조. `docs/DECISIONS.md`에는 D-n 요약 + 이 ID | `$plan-slice` |
| slice | 슬라이스 하나의 한 일·검증 결과 | `$verify-gate` |
| prompt | 다시 쓸 만한 프롬프트(담당자 질문 틀, 리뷰 지시 등) | — |
| session | 세션을 닫거나 레인을 바꿀 때 상태 스냅숏 | `$handoff` |
| note | 그 밖에 다시 묻지 않으려고 적어 두는 사실(담당자 답변 원문 등) | `$stakeholder-sync` |

## 규칙
- `ctx/index.jsonl`은 직접 열어 고치지 않는다(훅이 막음). 메타데이터는 `ctx.py`만 쓴다.
- `stale` 항목을 근거로 결정·구현하지 않는다.
- 같은 일을 다시 한 이유가 있으면(입력 변경, 결론 의심) `--redo` 전에 사용자에게 한 줄로 알린다.
- 커밋: `docs(ctx): research/anomaly — IsolationForest 우선 (R-2)`
