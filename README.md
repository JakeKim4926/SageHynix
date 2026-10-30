# SageHynix — Codex 하네스 (SK하이닉스 AI 해커톤 2차 예선 대비)

180분 "데이터를 활용한 AI 문제 해결 미션"을 Codex로 풀기 위한 **최소** 하네스.
과제 코드나 정답은 없다. 규칙(AGENTS.md), skill 3개, 6칸 지시 형식(SCRIPT), 서브에이전트 2개, 가드레일만 있다.

3시간 안에서는 장치가 많을수록 모델이 skill 고르는 데 헤매고, 매 턴 붙는 컨텍스트가 토큰과 주의를 잡아먹는다.
그래서 **조사 · 검증 · 문서** 세 가지만 남기고, 나머지는 사람의 판단과 SCRIPT 한 장으로 대신한다.

## 구성

```
bootstrap.sh                      작업 공간에 설치 (기존 파일 덮어쓰지 않음, ~/.codex 설정 안 건드림)
template/                         작업 공간에 복사되는 것
  AGENTS.md                       절대 규칙 8개, 흐름, skill 3개, SCRIPT 사용 규칙, 커밋·보고 형식 (51줄)
  prompts/SCRIPT.md               6칸 지시 형식 + 복사용 스크립트 S1~S6
  .codex/config.toml              서브에이전트 동시 3개, effort medium — 모델·승인·샌드박스는 건드리지 않음
  .codex/hooks.json + hooks/      PreToolUse 가드, UserPromptSubmit 기록 (둘 다 평소에는 컨텍스트 주입 없음)
  .codex/rules/harness.rules      execpolicy: git push·원격 전송 forbidden, reset/clean·pkill prompt
  .codex/agents/                  researcher, verifier (둘 다 코드 수정 금지, SCRIPT 형식으로 지시받음)
  .harness/bin/                   verify.sh(검증 관문) doctor.sh(사전 체험용 자가 진단)
  docs/VERIFICATION.md            검증 기록 표
plugins/hynix-harness/skills/     skill 3개의 단일 원본
  research/                       과제·데이터·도메인·기법 조사 → docs/research/<주제>.md (+ profile_data.py)
  verify/                         verify.sh·재계산·curl → VERIFICATION.md → 커밋
  doc/                            제출 문서 작성·수정·감사·서술형 대비 (+ references/templates.md)
.agents/plugins/marketplace.json  `codex plugin marketplace add`용
tests/                            하네스 자체 테스트
```

## 6칸 SCRIPT — 일을 넘길 때의 형식

```
[Role]    누구로서 — 관점과 권한
[Context] 이미 아는 것 — 사실, 파일 경로, 정해진 결정 (대화를 가리키지 않는다)
[Task]    할 일 하나 — 이 결과로 무엇을 결정하는지
[Rules]   하지 말 것·범위 밖·규정
[Output]  돌려줄 것 — 파일 경로와 형식
[Done]    끝 조건 — 확인 가능한 문장
```

받는 쪽(서브에이전트, 새 세션, 복사해서 붙인 프롬프트)은 보내는 쪽의 대화를 모른다. 넘어가는 건 이 6칸뿐이다.

| 유실 | 막는 칸 |
|---|---|
| 목적 유실 — 왜 하는지 몰라 엉뚱한 쪽을 최적화 | [Role] [Task] |
| 맥락 유실 — 확인한 사실·결정이 안 넘어가 재조사·모순 | [Context] |
| 제약 유실 — 금지·범위가 긴 대화에서 희석 | [Rules] |
| 완료 유실 — 언제 끝인지·무엇을 돌려줄지 몰라 과잉·미완 | [Output] [Done] |

`template/prompts/SCRIPT.md`에 과제 파악(S1), 조사 위임(S2), 구현(S3), 검증 위임(S4), 문서(S5), 세션 인수인계(S6) 스크립트가 있다. `<…>`만 채워 복사한다.

## 가드레일 (평소에는 모델 컨텍스트를 쓰지 않음)

| 장치 | 동작 |
|---|---|
| PreToolUse 훅 | 차단: `git push`, 외부 호스트로 업로드/POST, scp·ssh·nc, 키·토큰·env 출력, `~/.codex/config.toml` 수정, 하네스 훅·규칙 자기수정, 감독·플랫폼 프로세스 kill, `rm -rf /·~·.·.git`, `git reset --hard`·`clean -f`·`rebase`, 작업 공간 밖 파일 수정. 허용: localhost POST, 공개 저장소 clone, pip install 등. 차단 내역은 `.harness/log/guard.jsonl` |
| UserPromptSubmit 훅 | 프롬프트를 `.harness/log/prompts.jsonl`에 기록(협업 기록 원천). 모델이 Astra 계열이면 차단. 그 외에는 아무것도 주입하지 않음 |
| execpolicy rules | 위 정책 일부를 Codex 규칙 계층에서 이중 적용 |

## 시험 당일 런북

### 사전 체험 (15분, 1회)
1. **Cofa Helper에 질문**: "본인이 만든 공개 GitHub 저장소(프로세스용 AGENTS.md·skill, 과제 코드 없음)를 git clone해서 써도 되나요?" — 가이드는 공개 저장소·Skill clone을 허용하고 개인 PC의 비공개 Skill·파일 업로드를 금지한다. 직접 만든 공개 저장소가 어느 쪽인지는 가이드만으로는 불분명하다.
2. 허용되면 설치(아래) → `.harness/bin/doctor.sh`에서 FAIL 없음 확인
3. `codex` 실행 → 폴더 신뢰 승인 → **`/hooks`에서 하네스 훅 2개 신뢰** → `/status`로 모델 확인
4. `git push` 요청이 `[harness guard]`로 막히는지 확인
5. `/skills`에 research·verify·doc 3개가 보이는지, SCRIPT S2 형식으로 "researcher를 띄워 README를 요약해"가 동작하는지 확인
6. 간단한 서버를 `0.0.0.0`으로 띄워 Browser 탭 연결 확인

### 설치 (작업 공간 터미널)
```bash
git clone https://github.com/JakeKim4926/SageHynix ~/harness
bash ~/harness/bootstrap.sh ~/workspace
```
- 작업 공간에 `AGENTS.md`가 이미 있으면 건드리지 않고 `AGENTS.harness.md`로 둔다(직접 확인 후 합칠 것).
- 설치 파일을 `chore(harness): …`로 커밋한다. `--no-commit`으로 끌 수 있다.

### 180분 흐름
| 시각 | 할 일 | 입력 |
|---|---|---|
| 0–30 | 과제·데이터 조사, 담당자 질문 | SCRIPT S1 → 질문을 담당자 메신저로 → 답을 붙여 넣고 해당 research 파일 갱신 요청. 독립 질문이 여럿이면 S2로 researcher 병렬 |
| 30–140 | 기능 하나씩 | SCRIPT S3 → `$verify` (중요 수치는 S4로 verifier). 세션을 바꾸면 S6 |
| 140–170 | 문서, 감사, 서술형 대비 | SCRIPT S5 (`$doc`) |
| 170 | 제출 | 저장 상태·필수 파일 확인 후 "제출하고 문제풀기" |

### 대안 설치: 플러그인 (skill만)
```bash
codex plugin marketplace add JakeKim4926/SageHynix
codex plugin add hynix-harness@sagehynix
```
`~/.codex/config.toml`에 항목을 추가하므로 플랫폼 관리 설정 변경으로 볼 여지가 있다. 기본은 `bootstrap.sh`.

## 자체 테스트
```bash
bash tests/run_all.sh
```

## 검증 현황
- 확인됨 (2026-10-30, 슬림화 후, Windows 11 + Python 3.12 + Codex CLI 로컬): `tests/run_all.sh` 전체 통과 — 훅 단위 테스트 9개(차단 27건·허용 14건, 프롬프트는 기록만 하고 주입 없음, Astra 차단), JSON/TOML, skill이 정확히 research·verify·doc 3개, SCRIPT 복사용 스크립트 6개가 모두 6칸 순서, 에이전트 2개의 칸 이름, 삭제된 장치를 가리키는 참조 없음, execpolicy 4건, bootstrap 설치·재실행 멱등.
- **미확인**: 실제 Codex TUI에서 훅 발동과 `.codex/agents/` 서브에이전트 노출 — 사전 체험 3~5번에서 확인.
- 이전 버전(skill 13개, ctx 포함)의 검증 기록은 git 히스토리(`8cb9b38`)에 있다.
- 시험 환경의 Codex 버전, python3/pandas 설치 여부는 알 수 없다(`doctor.sh`로 확인).
