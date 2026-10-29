# AGENTS.md — SK하이닉스 AI 해커톤 하네스

이 작업 공간은 180분 안에 "데이터를 활용한 AI 문제 해결 미션"을 푸는 곳이다.
평가는 **결과물 + 과정(대화·터미널·git log/diff·테스트 결과·문서)** 을 함께 본다.
너(Codex)의 목표는 코드를 많이 쓰는 것이 아니라, 아래 세 가지 부채를 남기지 않고 검증된 결과를 내는 것이다.

| 부채 | 평가 축 | 이 하네스에서 막는 방법 |
|---|---|---|
| 기술 부채 | Technique — 작동하고 검증되는가 | `$verify-gate`, `.harness/bin/verify.sh`, 슬라이스 단위 커밋 |
| 의도 부채 | Intent — 목표·제약을 정확히 반영했는가 | `$task-intake`, `$stakeholder-sync`, `docs/INTENT.md` 요구사항 ID 추적 |
| 인지 부채 | Cognition — 사람이 설명할 수 있는가 | `$cognition-check`, `$defense-prep`, `docs/COGNITION.md` |

## 1. 절대 규칙 (위반 금지)

1. **거짓 보고 금지.** 실행하지 않은 명령, 확인하지 않은 수치, 통과하지 않은 테스트를 "완료/통과"라고 쓰지 않는다. 확인 못 한 것은 `미검증`이라고 명시한다.
2. **애매하면 묻는다.** 요구사항·데이터 의미·성공 기준이 둘 이상으로 해석되면 추측으로 구현하지 말고, 사용자에게 질문하거나 "업무 담당자에게 물어볼 질문"을 만들어 제시한다. 시간이 없어 가정을 택했다면 `docs/INTENT.md`의 가정(A-n)에 기록한다.
3. **과제 README가 최우선.** 필수 파일명·산출물·형식은 과제 README/안내를 따른다. 이 하네스의 기본 문서 이름과 충돌하면 README 쪽을 쓴다.
4. **외부 전송 금지.** `git push`, 외부로의 파일 업로드(curl -F/-T/--data 등), scp/ssh/nc 사용 금지. 공개 저장소 `git clone`과 패키지 설치는 허용.
5. **플랫폼 설정 불가침.** `~/.codex/config.toml`, 감독·연결 프로세스, 키·토큰을 수정·종료·출력하지 않는다. `.codex/hooks*`, `.codex/rules/`(가드레일)도 수정하지 않는다 — 필요하면 사용자에게 요청한다.
6. **모델:** Astra 계열은 사용 제한. 권장 모델은 Sol 6.1 / Terra 5.6 / Luna 6 / Sol 6.0 (`/model`로 선택).
7. **웹 서버는 `0.0.0.0`에 바인딩**하고 실제 포트를 출력한다(Browser 미리보기용). 서버 실행 터미널은 닫지 않는다.
8. **개인 API 키 사용 금지.** 외부 LLM API를 코드에서 호출하지 않는다(과제가 명시적으로 제공한 경우 제외).

## 2. 작업 루프

```
Intake → Research → Plan → [Slice: 구현 → 검증 → 커밋 → 설명] × N → Harden/Docs → Defense → Submit
```

- 한 번에 하나의 **수직 슬라이스**(데이터 → 로직 → 화면/출력까지 작동하는 최소 단위)만 진행한다.
- 슬라이스가 끝날 때마다 `$verify-gate` → 커밋 → `$cognition-check` 순서로 마무리한다.
- 긴 작업 전·컨텍스트가 길어질 때·세션을 바꿀 때 `$handoff`로 `docs/WORKLOG.md`를 갱신한다.

## 3. 시간 예산 (180분, 훅이 매 프롬프트에 경과 시간을 주입한다)

| 구간 | 단계 | 산출물 |
|---|---|---|
| 0–20분 | Intake: README 정독, 업무 담당자 질의 | `docs/INTENT.md` |
| 20–35분 | Research(병렬) + Plan | `docs/research/*`, `docs/PLAN.md` |
| 35–130분 | Build: 슬라이스 반복 | 코드, 테스트, 커밋 |
| 130–155분 | Harden + 문서 | `docs/VERIFICATION.md`, 제출 문서 |
| 155–170분 | Defense 준비, 최종 문서 감사 | `docs/COGNITION.md` |
| 170–180분 | 제출 (종료 10분 전 시작) | — |

시간이 밀리면 범위를 줄인다(요구사항 우선순위 기준). 범위를 줄인 사실과 이유는 `docs/DECISIONS.md`에 남긴다.

## 4. Skill 라우팅

| 상황 | Skill |
|---|---|
| 과제 시작, README 해석, 필수 산출물 파악 | `$task-intake` |
| 업무 담당자(메신저) 대화 내용을 요구사항으로 정리 | `$stakeholder-sync` |
| 독립된 조사 질문이 2개 이상 | `$parallel-research` |
| 데이터 파일을 처음 볼 때 | `$data-profile` |
| 구현 계획·우선순위·타임박스 | `$plan-slice` |
| 병렬 구현 레인이 필요할 때 (git worktree) | `$worktree-lanes` |
| 슬라이스 완료 판정, 커밋 | `$verify-gate` |
| 제출 문서 작성·수정 | `$doc-writer` |
| 제출 전 문서 감사 | `$doc-review` |
| 슬라이스 후 사람의 이해 점검 | `$cognition-check` |
| 제출 15분 전, 후속 서술형 대비 | `$defense-prep` |
| 세션 인수인계 / 컨텍스트 정리 | `$handoff` |

## 5. 서브에이전트 (병렬 조사)

`.codex/agents/`에 정의: `data_profiler`, `domain_researcher`, `method_scout`, `risk_reviewer`, `verifier`, `doc_auditor`.
- **서로 독립인 질문만** 병렬로 보낸다. 결과에 의존하는 일은 순차로.
- 각 에이전트는 `docs/research/<lane>.md` 한 파일에만 쓴다. 코드 수정 금지.
- 토큰 사용량도 평가 신호다. 한 번에 최대 4개, 기본 reasoning effort는 medium.
- 결과는 메인 에이전트가 `docs/research/SYNTHESIS.md`로 종합하고, 서로 충돌하는 주장은 충돌로 표시한다.

## 6. 기술 기본값 (Python 중심)

- 분석: pandas / numpy. 웹: 요구가 대시보드면 Streamlit, API·커스텀 화면이면 FastAPI(+간단한 HTML). 과제 README가 다르면 README를 따른다.
- 설치 전 `python3 -c "import pandas"`처럼 이미 있는지 먼저 확인한다. 의존성은 `requirements.txt`에 기록.
- 숫자 결과(지표, 집계)는 **재현 명령**과 함께 남긴다. 무작위성이 있으면 seed 고정.
- 테스트는 `tests/`에 pytest로. 최소한 핵심 계산 함수와 데이터 로딩 경계값을 테스트한다.

## 7. 커밋 규칙 (git log도 평가 대상)

- 슬라이스·의미 단위로 커밋. 메시지: `<type>(<scope>): <무엇을> — <왜>` (예: `feat(etl): 결측 웨이퍼 ID 제거 — R-2 수율 계산 왜곡 방지`)
- 요구사항 ID(R-n)와 결정 ID(D-n)를 메시지에 연결한다.
- `git reset --hard`, 히스토리 재작성, 제출 직전 결과물 통째 교체 금지.

## 8. 보고 형식 (매 턴 끝)

```
한 일: …
검증: <실행한 명령> → <결과 요약> | 미검증: …
다음: …
결정 필요: … (없으면 생략)
```
