---
name: intent
description: 과제를 파악한 직후, 구현 전에 과제 지시서 원문을 docs/task/에 반입하고 목적(P-n)·요구사항(R-n)·수용 기준(AC-n.m)을 원문 줄 근거와 함께 docs/INTENT.md 계약으로 쓴다. 가정·질문·결정·의도 변경은 docs/ledger.jsonl에 추가만 한다. 요구사항·성공 기준·지표를 정하거나 바꿀 때, 담당자 질문을 만들 때 사용한다. 테스트·완료 판정은 verify, 브랜치·커밋은 git을 사용한다.
---

# Intent

원문(`docs/task/`)·해석(`docs/INTENT.md`)·이력(`docs/ledger.jsonl`)을 섞지 않는다. AI가 쓴 해석을 원문처럼 다루지 않는다. 형식은 [templates.md](references/templates.md)를 따른다. 검사는 커밋할 때 `.codex/hooks/git`이 자동으로 한다.

## 계약 (과제 파악 직후 1회)
1. **원문 반입**: 과제 지시서를 그대로 `docs/task/`에 `cp`한다(파일명 유지). 채팅·웹으로 받은 지시는 원문 그대로 `.md`로 저장하고 첫 줄에 출처를 적는다. 반입 후 수정·삭제는 훅이 막는다.
2. **목적 P-n**: 원문에서 "왜"에 해당하는 문장을 인용하고, 결과로 누가 무엇을 판단하는지 한 줄로 쓴다.
3. **R-n과 AC-n.m**: 표 한 행에 AC 하나. 원문 근거는 `docs/task/<파일>:<줄>`, 원문에 없으면 ledger의 가정 `A-n`을 적고 상태는 `가정`. AC는 목적을 재는 지표·임계값·측정 데이터로 쓴다. 대리 지표 하나(예: 불균형 데이터의 정확도)만으로 쓰지 않는다.
4. **애매한 점**: ledger에 question(Q-n)으로, 시간 때문에 고른 기본값은 assumption(A-n)으로 남긴다. 담당자에게는 짧은 자연어 질문과 선택지를 보낸다.
5. **사용자 승인**: AC 표를 보이고 승인받는다. 승인 전 AC의 상태는 `가정`이다. 승인은 decision(`by: "user"`, refs: 승인한 AC)으로 남기고 상태를 `승인`으로 바꾼다. 이 decision 없이 `승인`인 AC는 커밋 훅이 막는다. `docs/` 브랜치에서 원문·INTENT·ledger를 커밋한다(`$git`).

## 바꿀 때
- AC 행을 고치거나 지우려면 사용자 승인을 받고, 같은 커밋에 decision(what 전→후, why 원문 근거, alt, by)을 추가한다. 승인 없이 바꾸면 커밋이 `[harness guard]`로 막힌다.
- 새 AC는 `가정`으로 추가하고 사용자에게 알린다. 승인받으면 계약 5단계처럼 `승인`으로 바꾼다. 질문에 답이 오면 answer(refs: [Q-n])를 추가하고 관련 가정·AC를 갱신한다.
- 기존 ledger 줄은 고치지 않는다. 정정도 새 줄이다.

추적표(AC | R | 원문 근거 | 결정 D | 최신 검증)가 필요하면 `python3 .codex/hooks/intent_trace.py report`.

## 검사 메시지
- `[harness guard]` 원문 수정, D-n 없는 AC 변경, 사용자 decision 없는 `승인` AC: 멈추고 사용자에게 보고한다(AGENTS.md 절대 규칙 9).
- `[trace check]` 원문이 있는데 INTENT 없는 feat·fix, JSON·필수 키·원문 근거·R-n·verify PASS·재실행 명령 누락: 메시지대로 고쳐 다시 커밋한다. `--no-verify`·`core.hooksPath` 변경은 금지다.
