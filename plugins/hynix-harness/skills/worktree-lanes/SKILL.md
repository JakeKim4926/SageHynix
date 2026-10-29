---
name: worktree-lanes
description: 서로 다른 파일을 건드리는 독립 구현 작업을 git worktree 레인으로 나눠 여러 터미널의 Codex 세션이 병렬로 구현하고 메인에 병합하게 한다. 병렬 구현이 이득일 때만 사용(파일 겹침 없음, 각 30분 이상). 조사 병렬화에는 parallel-research를 쓴다.
---

# Worktree Lanes

## 언제 쓰나 / 안 쓰나
- 쓴다: 예) 레인 A = 분석 파이프라인(`src/pipeline/`), 레인 B = 웹 화면(`app/`), 인터페이스(함수 시그니처·JSON 스키마)가 먼저 합의됨.
- 안 쓴다: 같은 파일을 둘 다 고쳐야 함, 작업이 15분 이하, 인터페이스가 아직 불확실. 병합 비용이 이득보다 크다.

## 절차
1. **인터페이스 먼저**: 레인 사이 계약(함수 시그니처, 데이터 파일 스키마, API 응답 예시)을 `docs/PLAN.md`에 쓰고 커밋한다. 가능하면 스텁 코드까지 커밋.
2. **레인 생성** (메인 작업 공간에서):
   ```bash
   .harness/bin/wt.sh new pipeline
   .harness/bin/wt.sh new web
   ```
   → `~/wt/<lane>`에 브랜치 `lane/<lane>` 생성. 하네스 파일이 커밋돼 있어야 레인에도 AGENTS.md·skills·hooks가 있다.
3. **레인 실행**: 웹 IDE 터미널 `+`로 새 탭 → `cd ~/wt/<lane> && codex` → 첫 지시에 레인 범위·금지 파일·계약 위치·완료 기준을 준다.
4. **레인 종료 조건**: 레인 안에서 `.harness/bin/verify.sh` 통과 + 커밋.
5. **병합** (메인에서, 한 번에 하나씩):
   ```bash
   .harness/bin/wt.sh merge pipeline && .harness/bin/verify.sh
   .harness/bin/wt.sh merge web && .harness/bin/verify.sh
   ```
   충돌은 사람이 확인하며 해결하고, 해결 내용을 커밋 메시지에 남긴다.
6. 정리: `.harness/bin/wt.sh rm <lane>`. WORKLOG에 레인별 결과 기록.

## 주의
- 레인 worktree는 `~/wt/` (작업 공간 밖)에 있어 **병합 전에는 제출물에 포함되지 않는다.** 종료 30분 전까지 모두 병합한다.
- 서버를 레인에서 띄워도 Browser 미리보기는 포트로 접근하므로 동작한다. 레인마다 다른 포트를 쓴다.
- 동시에 도는 Codex 세션 수만큼 토큰·응답 대기도 늘어난다. 레인은 최대 2~3개.
