---
name: git
description: 브랜치 생성·커밋·main 머지 등 모든 git 작업에 쓴다. 기능(R-n) 하나를 시작할 때 main에서 작업 브랜치를 만들고, $verify 통과분을 커밋하고, 끝나면 로컬에서 main으로 --no-ff 머지한다. develop·release 브랜치, PR, push는 쓰지 않는다. "브랜치", "커밋", "머지", "작업 시작", "기능 완료", "제출 전 정리"에 트리거한다.
---

# Git

브랜치는 `main`과 작업 브랜치 두 층뿐이다. 작업 브랜치에서 커밋하고, 로컬에서 `main`으로 바로 머지한다. git log·diff도 평가 대상이므로 히스토리가 기능 단위로 읽혀야 한다.

## 원칙
- **로컬 전용.** 커밋과 머지만 한다. `git push`는 대회 규정상 금지이며 훅·rules로도 막혀 있다 — 시도하지 않고, 막혀도 우회하지 않는다(AGENTS.md 절대 규칙 9). `git remote add`·`gh pr` 등 원격·PR 작업도 하지 않는다.
- **develop·release 없음, PR 없음.** 작업 브랜치 → `main` 직행이다.
- **main에 직접 커밋하지 않는다.** 문서만 바꿀 때도 `docs/*` 브랜치를 쓴다.
- **브랜치 하나 = 작업 단위 하나** (기능 하나 / 버그 수정 하나 / 리팩터링 하나). 여러 R-n을 한 브랜치에 묶지 않는다. 범위가 커지면 나눠서 순차로 진행한다.
- **열린 작업 브랜치는 하나.** 앞 브랜치를 머지한 뒤 `main`에서 다음 브랜치를 만든다. 작업 브랜치 위에 브랜치를 쌓지 않는다.

## 브랜치 이름

| 접두사 | 용도 | 예시 |
|---|---|---|
| `feature/` | 기능 (R-n) | `feature/r2-yield-etl` |
| `fix/` | 버그 수정 | `fix/r3-yield-zero-division` |
| `refactor/` | 동작 변경 없는 구조 개선 | `refactor/fe-features-split` |
| `docs/` | 문서만 | `docs/intent-assumptions` |

R-n이 있으면 이름 앞에 소문자로 붙인다(`r2-`). 나머지는 영어 소문자·하이픈.

## 작업 시작
```bash
git status                          # 깨끗한지 확인. 남은 변경이 있으면 먼저 정리한다
git switch main
git switch -c feature/<r-n>-<이름>
```
작업 폴더가 git 저장소가 아니면(`git rev-parse --is-inside-work-tree` 실패) `git init -b main` 후 과제 원본 파일로 첫 커밋(`chore: 과제 원본 반입`)을 만든 뒤 시작한다.

## 커밋

언제 커밋하는지는 `$verify`가 정한다(통과한 작업 단위만). 여기서는 단위와 형식만 정한다.

**커밋 하나 = 목적 하나.** 여러 파일이 바뀌어도 목적이 같으면 한 커밋, 목적이 다르면 반드시 나눈다. 기능 + 버그 수정 + 설정 변경을 한 커밋에 섞지 않는다. 의존성 추가(`requirements.txt`)·설정 변경도 각각 별도 커밋이다.

타입:
- `feat` 새 기능 · `fix` 버그 수정 · `test` 테스트 추가/수정 · `docs` 문서
- `style` 화면 스타일·색·정렬 등 표시 변경(동작 변경 없음)
- `refactor` 동작 변경 없는 구조 개선
- `chore` 빌드·설정·의존성·기타 유지보수

`style`과 `refactor` 구분: 화면에 보이는 결과가 바뀌면 `style`, 코드 구조만 바뀌고 결과가 같으면 `refactor`.

형식:
```text
<type>(<scope>): <무엇을> — <왜, R-n/D-n>

- 하위 변경 1
- 하위 변경 2
- <$verify 한 줄 보고>
```
- 제목만으로 충분하면 body를 붙이지 않는다. 하위 변경이 2개 이상이거나 `$verify` 한 줄 보고(test-strategy 4절)를 남길 때 빈 줄 뒤 bullet로 쓴다.
- body는 구현 세부 나열이 아니라 리뷰 관점의 변경 포인트만 적는다.
- 브랜치 안 커밋 제목은 머지 커밋 본문에 그대로 옮겨지므로 의미 있는 문장으로 쓴다.

```text
feat(etl): 결측 웨이퍼 ID 제거 — R-2 수율 계산 왜곡 방지
fix(yield): 투입 0인 lot 나눗셈 오류 수정 — R-3 화면 500 방지
style(fe): 수율 카드 강조색을 SK Red 하나로 통일 — D-4
chore(deps): pandas 추가 — R-2 집계

feat(api): 라인별 수율 조회 API 추가 — R-3

- GET /api/yield?line= 응답에 lot 수·수율 포함
- 없는 라인은 빈 목록 반환
- PASS 라인 수율 계산(R-3) — 3개 lot CSV → A 0.95·B 0.80, 손 계산 일치 (python3 -m pytest -q tests/test_yield.py)
```

## main 머지

머지 전 확인:
- [ ] 브랜치의 모든 커밋이 `$verify` PASS다. 미통과 커밋이 있으면 머지하지 않는다
- [ ] `git status`가 깨끗하다
- [ ] `git diff main...HEAD --stat`에 이번 작업 외 파일(디버그용 임시 파일·데이터 산출물)이 없다
- [ ] 커밋 메시지가 위 형식을 따른다

절차:
```bash
git switch main
git merge --no-ff <브랜치> -m "merge: <브랜치> → main — <요약> (R-n)" \
  -m "$(git log --format='* %s' main..<브랜치>)"
python3 -m pytest -q                  # main에서 다시 확인 (FE면 frontend.md 명령)
git branch -d <브랜치>
```
- squash·fast-forward 머지를 쓰지 않는다. `--no-ff`로 기능별 커밋(검증 과정)을 main 히스토리에 그대로 남기고, 머지 커밋이 기능 단위 요약이 된다.
- 머지 커밋 본문은 두 번째 `-m`이 브랜치 커밋 제목을 `* <type>(<scope>): <요약>` bullet로 채운다.
- 충돌이 나면 해결 → 테스트 → `git commit`. 지금 해결할 수 없으면 `git merge --abort`로 되돌리고 사용자에게 보고한다.
- 머지 후 main 테스트가 실패하면 `reset`으로 되돌리지 않는다. `fix/*` 브랜치를 새로 만들어 고친 뒤 다시 머지한다.
- 브랜치 삭제는 `-d`만 쓴다. `-d`가 거부하면 머지되지 않은 커밋이 있다는 뜻이므로 `-D`로 밀지 말고 원인을 확인한다.

## 제출 전
- `git branch`에 `main`만 남았는지, `git status`가 깨끗한지 확인한다.
- 과제 README가 요구한 필수 산출물(파일명·위치·형식)을 목록으로 뽑아 main의 실제 파일과 하나씩 대조한다. 빠진 것은 docs/LOG.md에 적고 사용자에게 알린다.
- 시간 안에 끝나지 않은 브랜치도 커밋은 모두 `$verify` 통과분이므로 그대로 머지한다. 통과하지 못해 커밋하지 않은 변경은 결과물에 섞지 않고 docs/LOG.md에 미완료로 적은 뒤 처리 방법을 사용자에게 묻는다.

## 금지
- `git push`·원격 추가·PR 생성 (막혀 있어도 다른 명령으로 우회 시도 금지)
- `main`에 직접 커밋, 작업 브랜치 위에 브랜치 쌓기
- `git reset --hard`·`rebase`·`commit --amend`로 커밋된 히스토리 고치기 — 고칠 것은 새 커밋으로
- squash·fast-forward 머지, `git branch -D`
