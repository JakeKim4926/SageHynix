---
name: inspect-dataset
description: 제공된 데이터 파일(CSV, TSV, Excel, JSON, Parquet)의 스키마, 결측, 중복, 분포, 이상치, 키 후보를 스크립트로 프로파일링하고 해석을 ctx에 남긴다. 데이터 파일을 처음 볼 때, 지표 계산이나 모델링 전에 사용.
---

# inspect-dataset

끝나면 데이터셋 하나(파일 묶음)마다 `ctx/data/{slug}/`에 실행 결과인 `profile.md`와 해석인 `notes.md`가 `valid` 상태로 있다.

## 입력
- 데이터 파일 경로. 먼저 `python3 .harness/bin/ctx.py find {데이터셋 이름}`을 실행한다. `valid`면 다시 돌리지 않고 `ctx.py get data/{slug}`로 읽는다.

## 진행
1. 등록하고 프로파일을 실행한다. `--inputs`에 건 파일이 바뀌면 이 항목은 자동으로 `stale`이 된다.
   ```bash
   python3 .harness/bin/ctx.py new data sensor --q "sensor.csv 프로파일: 스키마·결측·키" --inputs data/sensor.csv
   python3 .agents/skills/inspect-dataset/scripts/profile_data.py data/sensor.csv > ctx/data/sensor/profile.md
   ```
   pandas가 없으면 표준 라이브러리로 CSV만 처리한다(Excel, Parquet는 pandas 필요). 큰 파일은 `--max-rows 200000`으로 표본을 쓰고, 표본이라는 사실을 notes에 적는다.
2. `notes.md`를 채운다:
   - **컬럼 의미 추정표**: 컬럼, 추정 의미, 근거(이름·값 패턴), 확신도. 확신이 낮은 것은 INTENT Q-n으로 옮긴다.
   - **키와 조인**: 고유 키 후보, 파일 간 조인 키와 실제로 계산한 매칭률.
   - **함정**: 누수(결과를 이미 담은 컬럼), 시간 순서, 단위 혼재, 코드값 불일치, 중복 행, 클래스 불균형.
   - **분석 영향**: 계산할 때 조심할 점 3줄.
3. `python3 .harness/bin/ctx.py done data/{slug}`

## 제약
- notes의 모든 수치는 실행 결과에서 가져온다. 계산하지 않은 비율은 쓰지 않는다.
- 원본 데이터 파일은 수정하지 않는다. 정제는 별도 스크립트와 파일로 한다.

## 완료 기준
- `ctx.py done`이 통과한다(필수 섹션이 비어 있으면 거부된다).

## 출력
- 사용자 보고: 행·열 수, 키 후보, 가장 큰 함정 3개, 새로 생긴 Q-n.
- 커밋: `docs(ctx): data/sensor — 결측·중복·키 조사`
