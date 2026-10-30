# AGENTS.md — SK하이닉스 AI 해커톤 하네스

하네스 자체의 유지보수 요청에는 과제 제출·학습 퀴즈 루프를 적용하지 않는다.

## 시작 전 환경 준비

- 이 저장소의 README는 하네스 안내다. 과제 지시서는 별도로 확인하고, 위치를 `docs/INTENT.md`에 기록한다.
- 첫 사용은 `bash setup.sh`, 점검만 할 때는 `bash .harness/bin/doctor.sh`. 실패하면 `docs/SETUP.md`를 따른다.
- 선택 의존성은 실제 과제에 필요한 것만 `bash setup.sh --install <기능>`으로 설치한다.
- Codex는 `bash .harness/bin/start.sh`로 시작해 프로젝트 가상환경을 상속한다.

이 작업 공간은 "데이터를 활용한 AI 문제 해결 미션"을 푸는 곳이다.
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

## 3. Skill 라우팅

| 상황 | Skill |
|---|---|
| 과제 시작, README 해석, 필수 산출물 파악 | `$task-intake` |
| 업무 담당자(메신저) 대화 내용을 요구사항으로 정리 | `$stakeholder-sync` |
| 독립된 조사 질문이 2개 이상 | `$parallel-research` |
| 데이터 파일을 처음 볼 때 | `$data-profile` |
| 구현 계획·우선순위·범위 조정 | `$plan-slice` |
| FE 최초 준비·런타임·의존성·미리보기 문제 | `$fe-setup` |
| FE 화면·입력·조회·상호작용 구현 | `$fe-build` |
| FE 색·글꼴·화면 골격·차트 색 (SK CI 토큰) | `$fe-design` |
| 병렬 구현 레인이 필요할 때 (git worktree) | `$worktree-lanes` |
| 슬라이스 완료 판정, 커밋 | `$verify-gate` |
| 제출 문서 작성·수정 | `$doc-writer` |
| 제출 전 문서 감사 | `$doc-review` |
| 슬라이스 후 사람의 이해 점검 | `$cognition-check` |
| 제출 준비, 후속 서술형 대비 | `$defense-prep` |
| 세션 인수인계 / 컨텍스트 정리 | `$handoff` |
| 조사·분석 전 기존 결과 찾기, 결과 남기기, 이어받기 | `$ctx` |

## 4. 서브에이전트 (병렬 조사)

`.codex/agents/`에 정의: `data_profiler`, `domain_researcher`, `method_scout`, `risk_reviewer`, `verifier`, `doc_auditor`.
- **서로 독립인 질문만** 병렬로 보낸다. 결과에 의존하는 일은 순차로.
- 띄우기 전에 레인마다 `ctx.py new research <lane> --q …`로 등록한다. 각 에이전트는 `ctx/research/<lane>/report.md` 한 파일에만 쓴다. 코드 수정 금지. 끝나면 `ctx.py done`.
- 토큰 사용량도 평가 신호다. 한 번에 최대 4개, 기본 reasoning effort는 medium.
- 결과는 메인 에이전트가 `ctx/research/synthesis`(`--uses` 각 레인)로 종합하고, 서로 충돌하는 주장은 충돌로 표시한다.

## 5. 작업 기억 — `ctx/` (세션 사이로 넘어가는 유일한 기억)

대화는 잊혀도 `ctx/`는 남는다. 다음 세션·레인은 대화 기록이 아니라 `ctx/`의 결론과 근거 위치를 읽고 이어간다.
1. **먼저 찾는다.** 조사·데이터 분석·담당자 질문·프롬프트 작성 전에 `python3 .harness/bin/ctx.py find <키워드>`.
   `valid`면 `ctx.py get <ID>`로 읽고 재사용한다 — **같은 조사·같은 질문을 다시 하지 않는다.** `stale`이면 그대로 근거로 쓰지 않는다.
2. **결과는 남긴다.** `ctx.py new <종류> <slug> --q "<무엇을 묻는지>" [--serves R-n] [--inputs 파일] [--uses ID]` → 템플릿 섹션 채우기 → `ctx.py done <ID>`.
3. `ctx/index.jsonl`은 직접 고치지 않는다(훅이 막음). 목록은 `ctx/INDEX.md`, 사용법은 `$ctx`, 폴더 구성은 `ctx/README.md`.
4. 사용자가 `@ctx/…`나 ctx ID를 주면 그 항목부터 읽고, 폴더 전체를 읽지 않는다.
5. `docs/` 제출 문서는 근거로 ctx ID를 인용한다(예: D-2 근거 `decision/model-choice`).

## 6. 기술 기본값 (Python 중심)

- 분석: pandas / numpy. 단순 데이터 대시보드는 Streamlit, 신규 커스텀 FE는 TypeScript(strict)·React·Vite·Tailwind를 기본 후보로 한다. Python API가 필요하면 FastAPI를 사용한다. 기존 앱과 과제 README가 우선한다. FE 준비는 `$fe-setup`, 구현은 `$fe-build`, 디자인은 `$fe-design`(SK CI 토큰), 검증은 `$verify-gate`의 FE 절차를 따른다.
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
