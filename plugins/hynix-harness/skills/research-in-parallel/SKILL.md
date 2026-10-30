---
name: research-in-parallel
description: 서로 독립인 조사 질문(데이터 품질, 도메인 의미, 기법 후보, 위험 검토 등) 2~4개를 서브에이전트 레인으로 병렬 조사하고 하나의 종합으로 묶는다. 조사할 축이 2개 이상이고 서로의 결과에 의존하지 않을 때 사용. 질문이 하나뿐이거나 순차로 의존하면 쓰지 않는다.
---

# research-in-parallel

끝나면 레인마다 `ctx/research/{lane}/report.md`가 있고, 그것들을 묶은 `ctx/research/synthesis`가 `valid` 상태로 있다. 다음 세션은 레인 대화가 아니라 이 파일들만 읽는다.

## 입력
- 조사할 질문과 관련 R-n. `ctx.py find {키워드}`로 기존 레인을 찾아 `valid`는 재사용하고 `stale`만 다시 한다.

## 진행
1. **레인 설계를 사용자에게 먼저 보여 준다.** 레인마다 SLUG, 에이전트, 질문, 관련 R-n, 범위 밖, "이 답이 바꾸는 결정"을 적는다. README, INTENT, valid ctx로 이미 답할 수 있는 질문은 레인으로 만들지 않는다.

   | 레인 | 에이전트 | 결과 위치 |
   |---|---|---|
   | 데이터 품질·스키마 | `data_profiler` | `ctx/data/{slug}/` (`$inspect-dataset` 방식) |
   | 업무·도메인 의미 | `domain_researcher` | `ctx/research/domain/` |
   | 접근법·라이브러리 | `method_scout` | `ctx/research/method/` |
   | 계획·가정 반대 검토 | `risk_reviewer` | `ctx/research/risk/` |
2. **등록**: 레인마다 `python3 .harness/bin/ctx.py new research {lane} --q "{질문}" --serves R-n --inputs README.md`를 실행하고, `brief.md`의 `범위 밖`을 채운다.
3. **실행**: 서브에이전트를 한 번의 지시로 병렬로 띄운다. 예: "domain_researcher, method_scout를 병렬로 띄워라. 각자 ctx/research/{lane}/brief.md를 읽고 같은 폴더 report.md의 섹션만 채운다. 코드는 수정하지 않는다." 끝난 레인마다 `ctx.py done research/{lane}`을 실행한다.
   서브에이전트가 뜨지 않으면 `ctx/research/lanes.txt`에 `name|question`을 적고 `.harness/bin/fanout.sh ctx/research/lanes.txt 3`을 실행한다. 등록, 실행, done까지 처리하고 valid 레인은 건너뛴다.
4. **종합**: `ctx.py new research synthesis --q "{주제} 조사 종합" --uses research/{lane}... --serves R-n`. 템플릿 섹션에 맞춰 쓰되, 선택지는 선택지×요구사항 표로 만들고 칸마다 근거 레인 ID를 단다. 레인 사이에 충돌하는 주장은 누가 무엇을 주장했는지, 어느 쪽 근거가 강한지, 확인 방법을 적는다. 미확인은 INTENT Q-n/A-n으로도 옮긴다.
5. 선택이 필요하면 `ctx.py new decision {주제} --uses research/synthesis`로 남기고 `docs/DECISIONS.md`에 D-n 요약과 ID를 적는다.

## 제약
- 레인 보고서의 수치는 최소 1개를 메인 에이전트가 직접 재실행해 확인한다. 결정을 떠받치는 주장은 전부 원본과 대조한다. 근거가 없는 주장은 `미확인`으로 둔다.
- 레인을 다시 하면 종합이 자동으로 `stale`이 되므로 종합도 다시 한다.

## 완료 기준
- 모든 레인과 synthesis가 `ctx.py done`을 통과했고, 검증용 재실행 결과가 synthesis에 적혀 있다.

## 출력
- 사용자 보고: 종합 결론 첫 줄, 충돌한 주장, 새 Q-n과 D-n.
- 커밋: `docs(ctx): 병렬 조사 3레인 + synthesis — D-1 후보 도출`
