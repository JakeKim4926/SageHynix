---
name: parallel-research
description: 서로 독립적인 조사 질문(데이터 품질, 도메인 의미, 기법 후보, 위험 검토 등)을 서브에이전트 여러 개에 병렬로 맡기고 결과를 docs/research/SYNTHESIS.md로 종합한다. 조사할 축이 2개 이상이고 서로의 결과에 의존하지 않을 때 사용. 질문이 하나뿐이거나 순차 의존이면 쓰지 않는다.
---

# Parallel Research

## 1. 레인 설계 (먼저 사용자에게 보여 준다)
- 질문을 **서로 독립인** 2~4개 레인으로 나눈다. 레인마다: 이름, 담당 에이전트, 질문, 산출 파일, "이 답이 어떤 결정을 바꾸는가".
- 기본 레인 매핑:
  | 레인 | 에이전트 | 산출 |
  |---|---|---|
  | 데이터 품질·스키마 | `data_profiler` | docs/research/data.md |
  | 업무·도메인 의미 | `domain_researcher` | docs/research/domain.md |
  | 접근법·라이브러리 | `method_scout` | docs/research/method.md |
  | 계획·가정 반대 검토 | `risk_reviewer` | docs/research/risk.md |
- 이미 답이 있는 질문(README, INTENT)은 레인으로 만들지 않는다. 토큰 사용량도 평가 신호다.

## 2. 실행 — 방법 A: 세션 내 서브에이전트 (기본)
한 번의 지시로 병렬 생성한다. 예:

> data_profiler, domain_researcher, method_scout 를 병렬로 띄워라. 각자 위 표의 질문을 맡고 지정된 파일 하나에만 결과를 쓴다. 코드는 수정하지 않는다. 셋 다 끝날 때까지 기다린 뒤, 각 결론 3줄과 서로 충돌하는 주장을 요약해라.

## 3. 실행 — 방법 B: 독립 CLI 프로세스 (서브에이전트가 안 될 때)
`docs/research/lanes.txt`에 `name|question` 형식으로 레인을 적고:
```bash
.harness/bin/fanout.sh docs/research/lanes.txt 3
```
각 레인은 read-only `codex exec`로 돌고 `docs/research/<name>.md`에 결과가 쓰인다.

## 4. 종합 → docs/research/SYNTHESIS.md
```
## 결론 (결정에 쓰일 것만)
## 레인별 핵심 (각 3줄 + 파일 링크)
## 충돌하는 주장 — 누가 무엇을, 어느 쪽 근거가 강한가, 확인 방법
## 아직 모르는 것 → INTENT Q-n 또는 A-n 으로 이동
## 결정 후보 → DECISIONS D-n 초안
```

## 규칙
- 레인 보고서의 수치는 메인 에이전트가 최소 1개 이상 직접 재실행해 확인한다(무작위 표본).
- 에이전트 결과를 그대로 사실로 옮기지 않는다. 근거 없는 주장은 `미확인`.
- 커밋: `docs(research): 병렬 조사 3레인 종합 — D-1 후보 도출`
