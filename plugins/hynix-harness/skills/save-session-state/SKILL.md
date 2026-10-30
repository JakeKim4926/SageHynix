---
name: save-session-state
description: docs/WORKLOG.md와 ctx 세션 스냅숏에 현재 상태, 다음 단계, 막힌 것을 기록해 새 세션, 컨텍스트 압축, 다른 레인이나 터미널에서 바로 이어갈 수 있게 한다. 긴 작업 전, 컨텍스트가 길어졌을 때, 세션 재시작이나 레인 전환 전, 약 30분마다 사용.
---

# save-session-state

끝나면 대화 기록 없이 `docs/WORKLOG.md`만 읽어도 다음 세션이 바로 다음 단계를 실행할 수 있다.

## 입력
- 직접 실행해서 모은 사실: `git log --oneline -10`, `git status --short`, `.harness/bin/clock.sh status`, `tail -5 .harness/log/verify.log`.

## 진행
1. `docs/WORKLOG.md`를 갱신한다.
   - **현재 상태**: 단계, 완료 슬라이스(커밋 해시), 진행 중인 것과 어디까지 했는지(파일:함수), 띄워 둔 서버(포트, 터미널 탭), 열린 레인.
   - **다음 단계**: 바로 실행할 수 있는 수준으로 3~5개, 순서대로.
   - **막힌 것 / 결정 필요**: 사용자나 담당자 답이 필요한 것.
   - **최근 기록** 표에 한 줄: 시각 | 한 일 | 검증 결과 | 커밋. 한 화면을 넘으면 오래된 기록을 요약한다.
2. `python3 .harness/bin/ctx.py new session $(date +%m%d-%H%M) --q "{이 세션이 한 일 한 줄}"`을 실행한다. `handoff.md`의 현재 상태와 다음 단계는 WORKLOG와 같게 쓰고, 이 세션이 근거로 쓴 ctx ID를 적은 뒤 `ctx.py done session/{slug}`.
3. 이 세션에서 만든 ctx 항목 중 `draft`로 남은 것은 완료하거나 WORKLOG에 미완으로 적는다.

## 제약
- 확인하지 못한 상태는 추측으로 쓰지 않고 `미확인`으로 둔다.

## 완료 기준
- WORKLOG의 다음 단계가 명령이나 파일 단위로 실행 가능하고, 세션 스냅숏이 `valid`다.

## 출력
- 사용자 보고: 5줄 요약. 컨텍스트가 과하거나 방향이 바뀌었으면 새 세션을 권한다.
- 커밋: `docs(worklog): handoff — S3 진행 중, 다음 S3 테스트`
