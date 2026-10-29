# SageHynix — Codex 하네스 (SK하이닉스 AI 해커톤 2차 예선 대비)

180분 "데이터를 활용한 AI 문제 해결 미션"을 Codex로 풀 때 **기술·의도·인지 부채**를 남기지 않도록 미리 만들어 둔 하네스.
과제 코드나 정답은 들어 있지 않다. 프로세스 도구(규칙, skill, 서브에이전트, 가드레일, 스크립트, 문서 골격)만 있다.

| 부채 | Cofa 평가 축 | 하네스 장치 |
|---|---|---|
| 기술 | Technique: 작동하고 검증되는가 | `verify-gate` skill, `verify.sh`, `verifier` 에이전트, 슬라이스 단위 커밋 규칙 |
| 의도 | Intent: 목표·제약을 정확히 전달·반영했나 | `task-intake`, `stakeholder-sync`, `plan-slice`, `docs/INTENT.md`(R/A/Q ID 추적) |
| 인지 | Cognition: 사람이 설명할 수 있나 | `cognition-check`, `defense-prep`, `handoff`, `docs/COGNITION.md` |

설계 근거와 출처는 [docs/DESIGN.md](docs/DESIGN.md).

## 구성

```
bootstrap.sh                      작업 공간에 설치 (기존 파일 덮어쓰지 않음, ~/.codex 설정 안 건드림)
template/                         작업 공간에 복사되는 것
  AGENTS.md                       Codex 운영 규칙: 절대 규칙, 작업 루프, 시간 예산, skill 라우팅
  .codex/config.toml              프로젝트 설정(서브에이전트 동시 4개, effort medium) — 모델·승인·샌드박스는 건드리지 않음
  .codex/hooks.json + hooks/      SessionStart·UserPromptSubmit·PreToolUse 훅 (아래 가드레일)
  .codex/rules/harness.rules      execpolicy: git push·원격 전송 forbidden, reset/clean·pkill prompt
  .codex/agents/*.toml            서브에이전트 6종: data_profiler, domain_researcher, method_scout,
                                  risk_reviewer, verifier, doc_auditor (모두 코드 수정 금지)
  .harness/bin/                   clock.sh(타이머) wt.sh(워크트리) fanout.sh(병렬 조사)
                                  verify.sh(검증 관문) doctor.sh(자가 진단)
  docs/                           INTENT, PLAN, DECISIONS, WORKLOG, VERIFICATION, COGNITION, research/
plugins/hynix-harness/            Codex 플러그인 (skill 12개의 단일 원본)
  skills/                         task-intake, stakeholder-sync, parallel-research, data-profile,
                                  plan-slice, worktree-lanes, verify-gate, doc-writer, doc-review,
                                  cognition-check, defense-prep, handoff
.agents/plugins/marketplace.json  `codex plugin marketplace add`용
tests/                            하네스 자체 테스트
```

## 가드레일

| 장치 | 동작 |
|---|---|
| UserPromptSubmit 훅 | 모델이 Astra 계열이면 프롬프트 차단. 매 프롬프트에 `경과 N분 / 남은 M분 · 현재 단계` 주입. 프롬프트를 `.harness/log/prompts.jsonl`에 기록(협업 기록 원천) |
| SessionStart 훅 | 타이머 상태, 재개 시 `docs/WORKLOG.md` 먼저 읽으라는 지시 주입 |
| PreToolUse 훅 | 차단: `git push`, 외부 호스트로 업로드/POST, scp·ssh·nc, 키·토큰·env 출력, `~/.codex/config.toml` 수정, 하네스 훅·규칙 자기수정, 감독·플랫폼 프로세스 kill, `rm -rf /·~·.·.git`, `git reset --hard`·`clean -f`·`rebase`. 허용: localhost POST, 공개 저장소 clone, pip install 등. 차단 내역은 `.harness/log/guard.jsonl` |
| execpolicy rules | 위 정책 일부를 Codex 규칙 계층에서 이중으로 적용 |

## 시험 당일 런북

### 사전 체험 (15분, 1회) — 반드시 확인
1. **Cofa Helper에 질문**: "본인이 만든 공개 GitHub 저장소(프로세스용 AGENTS.md·skill, 과제 코드 없음)를 git clone해서 써도 되나요?" — 가이드는 "일반적으로 공개된 GitHub 저장소·Skill"의 clone을 허용하고 "개인 PC의 비공개 Skill·파일 업로드"를 금지한다. 직접 만든 공개 저장소가 어느 쪽인지는 가이드만으로는 불분명하다.
2. 허용되면 설치(아래) → `.harness/bin/doctor.sh`에서 FAIL 없음 확인
3. `codex` 실행 → 폴더 신뢰 승인 → **`/hooks`에서 하네스 훅 3개 신뢰** → `/status`로 모델 확인
4. 아무 프롬프트나 보내서 응답 컨텍스트에 `[harness] 경과…`가 반영되는지, `git push` 요청이 `[harness guard]`로 막히는지 확인
5. `/skills`에 12개가 보이는지, "data_profiler와 method_scout를 병렬로 띄워서 README를 요약해" 같은 요청으로 서브에이전트가 뜨는지 확인 (안 뜨면 `fanout.sh` 사용)
6. 간단한 서버를 `0.0.0.0`으로 띄워 Browser 탭 연결 확인

### 설치 (작업 공간 터미널)
```bash
git clone https://github.com/JakeKim4926/SageHynix ~/harness
bash ~/harness/bootstrap.sh ~/workspace
```
- 작업 공간에 `AGENTS.md`가 이미 있으면 건드리지 않고 `AGENTS.harness.md`로 둔다(직접 확인 후 합칠 것).
- 설치 파일을 `chore(harness): …`로 커밋한다(워크트리 레인이 하네스를 물려받도록). `--no-commit`으로 끌 수 있다.

### 180분 흐름
| 시각 | 할 일 | 입력 예 |
|---|---|---|
| 0분 | 타이머 시작 | `.harness/bin/clock.sh start` |
| 0–20 | 과제 파악, 담당자 질문 | `$task-intake` → 질문을 업무 담당자 메신저로 전송 → 답을 붙여 넣고 `$stakeholder-sync` |
| 20–35 | 병렬 조사, 계획 | `$data-profile`, `$parallel-research`, `$plan-slice` |
| 35–130 | 슬라이스 반복 | 구현 → `$verify-gate` → `$cognition-check` (30분마다 `$handoff`) |
| 130–155 | 보강, 문서 | `$doc-writer` |
| 155–170 | 감사, 서술형 대비 | `$doc-review`, `$defense-prep` |
| 170 | 제출 시작 | 저장 상태·필수 파일 확인 후 "제출하고 문제풀기" |

병렬 구현이 필요하면 `$worktree-lanes`(`.harness/bin/wt.sh new <lane>` → 새 터미널 탭에서 `cd ~/wt/<lane> && codex`).

### 대안 설치: 플러그인 (skill만)
```bash
codex plugin marketplace add JakeKim4926/SageHynix
codex plugin add hynix-harness@sagehynix
```
`~/.codex/config.toml`에 항목을 추가하므로, 플랫폼 관리 설정 변경으로 볼 여지가 있다. 기본은 위 `bootstrap.sh`(작업 공간 안에만 설치).

## 자체 테스트
```bash
bash tests/run_all.sh
```

## 검증 현황 (2026-10-29, Windows 10 + Codex CLI 0.125/0.165 로컬)
- 확인됨: 훅 정책 단위 테스트(차단 27건·허용 14건 등 11개 테스트), execpolicy 규칙 판정, bootstrap 설치·재실행 멱등성·기존 AGENTS.md 보존, `codex debug prompt-input`으로 AGENTS.md와 skill 12개 주입, `wt.sh` 레인 생성→병합→삭제, `fanout.sh` 2개 레인 병렬 실행·파일 출력, 프로파일러(pandas 3.1 / 표준 라이브러리), 플러그인 marketplace add → plugin add(skill 12개 설치).
- **미확인**: (1) Codex 안에서 훅이 실제로 발동하는지 — 훅 신뢰는 `/hooks` 대화형 승인이 필요해 로컬 비대화형 실행에서 확인 못 함. (2) `.codex/agents/` 커스텀 에이전트가 spawn 도구에 노출되는지 — `codex exec`에서는 보이지 않았음(TUI에서는 미확인). (3) `fanout.sh` 레인 안에서의 파일 읽기 — 로컬 Windows 샌드박스 ACL 오류로 실패, 시험 환경(Linux)에서는 미확인. 셋 다 사전 체험 4·5번에서 확인할 것.
- 시험 환경의 Codex 버전, python3/pandas 설치 여부는 알 수 없다(`doctor.sh`로 확인).
