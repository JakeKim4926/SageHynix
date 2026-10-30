---
name: parallel-research
description: 서로 독립적인 조사 질문(데이터 품질, 도메인 의미, 기법 후보, 위험 검토 등)을 서브에이전트 여러 개에 병렬로 맡기고, 레인마다 ctx/research/<레인>/ 에 결과를 남긴 뒤 ctx/research/synthesis 로 종합한다. 이미 valid 한 레인은 다시 돌리지 않는다. 조사할 축이 2개 이상이고 서로의 결과에 의존하지 않을 때 사용. 질문이 하나뿐이거나 순차 의존이면 쓰지 않는다.
---

# Parallel Research

결과는 모두 `ctx/`에 남는다(`$ctx`). 다음 세션은 레인 대화가 아니라 `ctx/research/*/report.md`만 읽고 이어간다.

## 0. 이미 한 조사인지 먼저 확인
```bash
python3 .harness/bin/ctx.py find <주제 키워드>
```
`valid` 레인은 다시 돌리지 않고 `ctx.py get`으로 읽어 재사용한다. `stale`인 레인만 다시 한다.

## 1. 레인 설계 (먼저 사용자에게 보여 준다)
- 질문을 **서로 독립인** 2~4개 레인으로 나눈다. 레인마다: SLUG, 담당 에이전트, 질문, 관련 R ID, 범위 밖, "이 답이 어떤 결정을 바꾸는가".
- 기본 레인 매핑:
  | 레인 | 에이전트 | 결과 |
  |---|---|---|
  | 데이터 품질·스키마 | `data_profiler` | ctx/data/<데이터셋>/ (`$data-profile`) |
  | 업무·도메인 의미 | `domain_researcher` | ctx/research/domain/report.md |
  | 접근법·라이브러리 | `method_scout` | ctx/research/method/report.md |
  | 계획·가정 반대 검토 | `risk_reviewer` | ctx/research/risk/report.md |
- 이미 답이 있는 질문(README, INTENT, valid ctx 항목)은 레인으로 만들지 않는다. 토큰 사용량도 평가 신호다.

## 2. 레인 등록 (지시서 생성)
레인마다 한 번:
```bash
python3 .harness/bin/ctx.py new research method --q "결측 많은 센서 데이터의 이상치 탐지 방법과 비용" \
  --serves R-2 --inputs README.md
```
`ctx/research/method/brief.md`의 `범위 밖`을 채운다. 레인은 이 지시서와 `report.md` 템플릿만 받는다.

## 3. 실행 — 방법 A: 세션 내 서브에이전트 (기본)
한 번의 지시로 병렬 생성한다. 예:

> domain_researcher, method_scout 를 병렬로 띄워라. 각자 ctx/research/<레인>/brief.md 를 읽고 같은 폴더의 report.md 섹션만 채운다. 코드는 수정하지 않는다. 둘 다 끝나면 결론 첫 줄과 서로 충돌하는 주장만 요약해라.

끝나면 레인마다 `ctx.py done research/<레인>`. 거부되면(빈 섹션) 그 레인 보고서만 보완한다.

## 4. 실행 — 방법 B: 독립 CLI 프로세스 (서브에이전트가 안 될 때)
`ctx/research/lanes.txt`에 `name|question` 형식으로 적고:
```bash
.harness/bin/fanout.sh ctx/research/lanes.txt 3
```
fanout이 레인 등록 → read-only `codex exec` → `ctx/research/<name>/report.md` → `done`까지 처리한다. valid 레인은 건너뛴다(`FANOUT_FORCE=1`이면 다시).

## 5. 종합 → ctx/research/synthesis
```bash
python3 .harness/bin/ctx.py new research synthesis --q "<주제> 조사 종합" \
  --uses research/domain research/method research/risk --serves R-1,R-2
```
`report.md` 섹션에 맞춰 쓴다:
- **결론**: 결정에 쓰일 것만.
- **선택지**: 선택지 × 요구사항, 칸마다 근거가 된 레인 ID.
- **근거**: 레인별 핵심 3줄 + 충돌하는 주장(누가 무엇을, 어느 쪽 근거가 강한가, 확인 방법).
- **미확인**: 아직 모르는 것 → INTENT Q-n/A-n으로도 옮긴다.

`done` 후 선택이 필요하면 `ctx.py new decision <주제> --uses research/synthesis`로 결정을 남기고 `docs/DECISIONS.md`에 D-n 요약과 ID를 적는다.
레인을 다시 하면 종합은 자동으로 `stale`이 된다 — 종합도 다시 한다.

## 규칙
- 레인 보고서의 수치는 메인 에이전트가 최소 1개 이상 직접 재실행해 확인한다(무작위 표본). 결정을 떠받치는 주장은 전부 원본과 대조한다.
- 에이전트 결과를 그대로 사실로 옮기지 않는다. 근거 없는 주장은 `미확인`.
- 커밋: `docs(ctx): 병렬 조사 3레인 + synthesis — D-1 후보 도출`
