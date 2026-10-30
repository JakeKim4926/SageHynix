---
name: handoff
description: 세션 인수인계. docs/WORKLOG.md에 현재 상태·다음 단계·막힌 것·최근 기록을 갱신해 새 세션, 컨텍스트 압축, 다른 레인/터미널에서 바로 이어갈 수 있게 한다. 긴 작업 전, 컨텍스트가 길어졌을 때, 세션 재시작·레인 전환 전, 약 30분마다 사용.
---

# Handoff

## 절차
1. 사실 수집(직접 실행): `git log --oneline -10`, `git status --short`, `.harness/bin/clock.sh status`, `tail -5 .harness/log/verify.log`.
2. `docs/WORKLOG.md` 갱신:
   - **현재 상태**: 단계, 완료 슬라이스(커밋 해시), 진행 중인 것과 어디까지 했는지(파일:함수).
   - **다음 단계**: 바로 실행 가능한 수준으로 3~5개, 순서대로.
   - **막힌 것 / 결정 필요**: 사용자·담당자 답이 필요한 것.
   - **최근 기록** 표에 한 줄 추가: 시각 | 한 일 | 검증 결과 | 커밋.
   - 띄워 둔 서버(포트, 터미널 탭), 열려 있는 레인(worktree)도 적는다.
3. 세션 스냅숏을 ctx에 남긴다(다음 세션이 `ctx.py find`로 찾게):
   ```bash
   python3 .harness/bin/ctx.py new session $(date +%m%d-%H%M) --q "<이 세션이 한 일 한 줄>"
   ```
   `handoff.md`의 현재 상태·다음 단계를 WORKLOG와 같게 채우고, **참조한 ctx 항목**(이 세션이 근거로 쓴 ID)을 적은 뒤 `ctx.py done session/<slug>`.
   이 세션에서 끝낸 조사·결정·슬라이스 중 아직 `draft`인 것이 있으면(`ctx.py find`) 완료하거나 WORKLOG에 미완으로 적는다.
4. 커밋: `docs(worklog): handoff — S3 진행 중, 다음 S3 테스트`
5. 사용자에게 5줄 요약. 새 세션을 권할 상황이면(컨텍스트 과다, 방향 전환) 그렇게 말한다.

## 규칙
- 짧게. WORKLOG 전체는 한 화면을 넘지 않게 오래된 기록은 요약한다.
- 추측으로 상태를 쓰지 않는다. 확인 못 한 것은 "미확인".
