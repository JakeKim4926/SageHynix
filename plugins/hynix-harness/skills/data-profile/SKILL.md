---
name: data-profile
description: 제공된 데이터 파일(CSV/TSV/Excel/JSON/Parquet)의 스키마·결측·중복·분포·이상치·키 후보를 스크립트로 프로파일링하고 docs/research/data.md에 근거와 함께 기록한다. 데이터를 처음 볼 때, 지표 계산·모델링 전에 사용.
---

# Data Profile

## 실행
```bash
python3 .agents/skills/data-profile/scripts/profile_data.py data/*.csv > docs/research/data.md
```
- pandas가 있으면 pandas로, 없으면 표준 라이브러리 csv로 동작한다(엑셀·parquet는 pandas 필요).
- 큰 파일은 `--max-rows 200000`으로 표본 프로파일링하고, 표본이라는 사실을 보고서에 남긴다.

## 스크립트 출력 이후 반드시 사람이 볼 수 있게 덧붙일 것
1. **컬럼 의미 추정표**: 컬럼 → 추정 의미 → 근거(이름·값 패턴) → 확신도. 확신 낮은 것은 INTENT Q-n으로.
2. **키와 조인**: 고유 키 후보, 파일 간 조인 키와 매칭률(실제 계산).
3. **함정**: 누수 위험(결과를 이미 포함한 컬럼), 시간 순서, 단위 혼재, 코드값 불일치, 중복 행, 클래스 불균형.
4. **분석 영향**: "그래서 무엇을 조심해서 계산해야 하나" 3줄.

## 규칙
- 보고서의 모든 수치는 실행 결과에서 온다. 계산 안 한 비율을 쓰지 않는다.
- 원본 데이터 파일은 수정하지 않는다. 정제는 별도 스크립트/파일로.
- 커밋: `docs(data): 데이터 프로파일 — 결측·중복·키 조사`
