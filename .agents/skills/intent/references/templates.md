# 템플릿

## docs/INTENT.md

```markdown
# INTENT

## 0. 원문
- docs/task/README.md (반입 커밋 <hash>) — 수정 금지, 인용만

## 1. 목적
- P-1: "<원문 인용>" (docs/task/README.md:<줄>) → <누가 무엇을 판단하는 데 쓰나>

## 2. 요구사항·수용 기준
| AC | R | P | 우선 | 원문 근거 | 수용 기준 (목적 지표·임계값·측정 데이터) | 상태 |
|---|---|---|---|---|---|---|
| AC-1.1 | R-1 | P-1 | M | docs/task/README.md:12 | 검증셋에서 이상 설비 recall ≥ 0.9, 오탐률 ≤ 10% | 승인 |
| AC-1.2 | R-1 | P-1 | S | A-2 | 전체 데이터 추론 1회 1초 이내 | 가정 |

## 3. 비목표·금지
- <원문이 요구하지 않는 것, 하지 말라고 한 것> (docs/task/README.md:<줄>)
```

- 검사 대상은 표 첫 칸이 `AC-n.m`인 행이다. 한 행에 AC 하나, 근거 칸에 `docs/task/<파일>:<줄>` 또는 `A-n`.
- 상태: `승인` / `가정` / `보류`. 상태를 바꾸는 것도 AC 행 변경이므로 decision이 필요하다.

## docs/ledger.jsonl

한 줄에 JSON 객체 하나. 끝에 추가만 한다. `ts`(예: "10:42")는 선택이다.

| type | 필수 키 | 쓰는 때 |
|---|---|---|
| `decision` | `id`(D-n), `refs`, `what`, `why`, `by`(user/agent) | AC 승인·변경, 기법·지표 선택 |
| `assumption` | `id`(A-n), `refs`, `what` | 원문에 없어 고른 기본값 |
| `question` | `id`(Q-n), `refs`, `what` | 사용자·담당자에게 묻는 것 |
| `answer` | `refs`([Q-n]), `what` | 질문의 답 |
| `verify` | `refs`([AC-n.m]), `result`(PASS/FAIL/미검증/생략), `line` | `$verify` 4단계 한 줄. `where`(파일:함수) 선택 |

`refs`의 `R-n`은 그 R의 모든 AC를 가리킨다.

```json
{"type":"assumption","id":"A-2","refs":["AC-1.2"],"what":"응답 시간 요구가 없어 1초로 둔다","ts":"09:20"}
{"type":"question","id":"Q-1","refs":["AC-1.1"],"what":"오탐 허용치는? ① 10% ② 5% ③ 제한 없음"}
{"type":"decision","id":"D-1","refs":["R-1"],"what":"AC-1.1·1.2 승인","why":"사용자 확인","by":"user"}
{"type":"decision","id":"D-2","refs":["AC-1.1"],"what":"accuracy ≥ 0.95 → 이상 recall ≥ 0.9","why":"docs/task/README.md:12 '놓치지 않도록', 이상 비율 3%","alt":"F1","by":"user"}
{"type":"verify","refs":["AC-1.1"],"result":"PASS","line":"PASS 이상 탐지(R-1) — 검증셋 → recall 0.93 (python3 -m pytest -q tests/test_detect.py)","where":"src/detect.py:score"}
```

## docs/LOG.md

```markdown
# LOG

## 현재 상태
- 진행: <브랜치> — <R-n> / 다음: … / 막힘: …
- 앱·실행: <경로, 명령, 포트> / 미검증: …

## 테스트 계획
| 기능(R-n) | 실패 가능성 | 영향도 | 검증 방법 |
|---|---|---|---|
```

검증 결과는 LOG가 아니라 ledger의 verify 줄에 쓴다.
