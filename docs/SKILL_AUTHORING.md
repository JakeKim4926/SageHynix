# SKILL.md 작성 구조와 스킬 파일 구조 (Sol 6.0 / Luna 6 기준)

조사일 2026-10-30. 로컬 기준 `codex-cli 0.164.0`과 내장 `~/.codex/skills/.system/skill-creator`.

## 0. 전제: "Luna·Sol 6.0"과 근거의 범위

- 대상 모델은 대회 권장 목록(DESIGN.md §1)의 `gpt-6-sol`(Sol 6.0)과 `gpt-6-luna`(Luna 6). 2026-09-22 출시. [사실]
- OpenAI 문서에는 Sol·Luna 전용 SKILL.md 작성 지침이 **없다**. GPT-6 가이드의 프롬프트·스킬 항목은 "GPT-6 Astra에서 관찰"한 내용을 GPT-6 계열 전체의 출발점으로 제시한다. [사실]
- 그래서 이 문서는 세 가지를 합친다: Codex 공식 스킬 스펙(로컬 0.164 skill-creator 포함), GPT-6·GPT-5.6 프롬프트 가이드, Agent Skills 표준(agentskills.io)과 Anthropic 작성 가이드 및 커뮤니티 관행. [추론]
- 웹에는 "GPT-5.6 Sol/Terra/Luna"와 "GPT-6 Sol/Luna"라는 명칭이 섞여 있다. 출처를 읽을 때 모델 버전을 확인한다. [사실]

## 1. 스킬 파일 구조 (Codex)

```text
skill-name/                  폴더명 = name
├── SKILL.md                 필수. 프런트매터 + 본문
├── agents/openai.yaml       권장. UI 메타데이터·호출 정책·MCP 의존성 (모델이 아니라 하네스가 읽음)
├── scripts/                 선택. 결정적으로 실행할 코드. 읽지 않고 실행만 하면 컨텍스트 비용 0
├── references/              선택. 특정 모드에서만 읽는 문서 (스키마, 정책, 상세 절차)
└── assets/                  선택. 결과물에 복사되는 템플릿·이미지·폰트
```

- README, 설치 가이드, CHANGELOG, 중복된 빠른 참조는 넣지 않는다 (skill-creator 지침).
- 필요 없는 디렉터리나 placeholder는 만들지 않는다. 짧은 스킬은 `SKILL.md` 하나로 충분하다.

**탐색 위치** (cwd에서 저장소 루트까지 올라가며 스캔): `$CWD/.agents/skills` → 상위 `.agents/skills` → `$REPO_ROOT/.agents/skills` → `$HOME/.agents/skills` → `/etc/codex/skills` → 내장 skill. 같은 `name`이 여러 개면 병합하지 않고 모두 표시한다. 심볼릭 링크를 지원한다.

**배포 단위 = 플러그인**: `plugins/<p>/.codex-plugin/plugin.json` + `skills/` (선택: `.mcp.json`, `hooks.json`, `agents/`, `commands/`, `assets/`). 마켓플레이스는 `.agents/plugins/marketplace.json`. openai/skills 저장소(28.4k★)는 지원 중단됐고 openai/plugins(7.7k★)로 넘어갔다.

**컨텍스트 예산**: 시작 시 모든 스킬의 이름·설명·경로를 목록으로 주입한다. 이 목록은 컨텍스트 창의 2%까지 쓴다(창 크기를 모르면 8,000자). 넘치면 설명부터 줄이고, 그래도 넘치면 스킬을 빼고 경고한다. `skills.max_context_tokens`로 최대 10,000토큰까지 늘릴 수 있다. 끄려면 `[[skills.config]] path=… enabled=false`.

### 1.1 프런트매터 (로컬 `quick_validate.py` 기준)

| 필드 | 규칙 |
|---|---|
| `name` | 필수. `^[a-z0-9-]+$`, 64자 이하, 앞뒤 `-` 금지, `--` 금지, 폴더명과 같게 |
| `description` | 필수. 1024자 이하, **`<` `>` 금지**, `[TODO:`로 시작하면 실패 |
| 허용 키 | `name`, `description`, `license`, `allowed-tools`, `metadata` 이외는 검증 실패 |
| `metadata.short-description` | 내장 스킬이 쓰는 관례 (예: skill-creator) |

GitHub의 구버전 skill-creator는 "name·description 외 필드 금지"라고 하지만 0.164는 위 5개를 허용한다. 로컬 버전을 따른다.

### 1.2 `agents/openai.yaml`

```yaml
interface:
  display_name: "Verify Gate"
  short_description: "슬라이스 완료 판정과 커밋"      # 25–64자
  default_prompt: "Use $verify-before-done to check this slice before commit."  # $name을 반드시 포함
policy:
  allow_implicit_invocation: true   # false면 목록에 주입하지 않음. $name 명시 호출만 가능
dependencies:
  tools:
    - type: "mcp"                   # 현재 mcp만 지원
      value: "github"
      transport: "streamable_http"
      url: "https://…"
```

문자열 값은 모두 따옴표로 감싼다. 아이콘·색상은 사용자가 줄 때만 넣는다. 위험한 작업이라는 이유만으로 explicit-only로 바꾸지 않는다. 자동 발견은 그대로 두고, 실제 변경 직전에 승인을 받는다 (0.164 지침).

## 2. 세 단계 로딩과 크기 기준

| 단계 | 로드 시점 | 기준 |
|---|---|---|
| 이름·설명 | 항상 | 약 100단어. 짧고 다른 스킬과 겹치지 않게 |
| SKILL.md 본문 | 스킬을 고른 뒤 | 500줄 미만, 5k 토큰 미만이 표준 권고. 0.164 지침: "상한은 목표가 아니다". 과제가 허락하는 한 짧게 |
| references/scripts/assets | 필요할 때 | 참조는 SKILL.md에서 **한 단계만**. 100줄 넘는 참조 파일은 맨 위에 목차. 아주 큰 참조는 grep 검색어를 적어 둔다 |

## 3. SKILL.md 본문 골격과 엄격 판정 기준

여러 출처에서 겹치는 구조다. GPT-5.6 가이드의 섹션 순서는 Goal → Success criteria → Constraints → Tools → Output → Stop rules. skill-creator 0.164는 outcome, non-obvious context, real constraints, references를 꼽는다. Anthropic 가이드는 workflow, checklist, feedback loop를 꼽는다.

```markdown
---
name: verify-before-done
description: {무엇을 하는지 한 문장}. {언제 쓰는지: 사용자가 실제로 쓸 단어·파일 형식·상황}. {오라우팅이 실제로 생길 때만: 언제 쓰지 않는지}.
---

# verify-before-done

{한두 줄: 이 스킬이 끝나면 무엇이 참이 되는가 (outcome)}

## 입력
## 진행        ← 모드가 여럿이면 여기서 라우팅, 모드별 상세는 references/
## 제약
## 완료 기준
## 출력
```

이 저장소는 위 골격을 **모든 스킬에 그대로** 적용한다. 섹션 이름과 순서를 고정해 두면 Sol과 Luna 모두 같은 위치에서 같은 정보를 찾는다. 점검할 때는 아래 기준으로 섹션마다 과소·과도를 판정한다.

| 섹션 | 과소 (채워야 함) | 과도 (덜어 내야 함) |
|---|---|---|
| name | 이름만 보고 무엇을 위해 쓰는지 알 수 없음: 약어(`ctx`), 명사 하나(`intent`), 산출물 이름(`data-profile`), 수단만 있는 이름(`handoff`, `plan-slice`) | 4단어를 넘음 |
| description | 무엇만 있고 언제가 없음, 트리거 단어 없음 | 워크플로 요약, 다른 스킬과 겹치는 트리거, `<` `>` |
| outcome 줄 | 없음, 또는 "~한다" 같은 행동만 있고 끝난 상태가 없음 | 평가 배경 설명이 2줄을 넘음 |
| 입력 | 없을 때 어디서 찾는지 빠짐 | 모델이 알아서 찾는 파일을 나열함 |
| 진행 | 순서가 중요한데 번호가 없음, 정확해야 하는 명령이 산문으로만 있음 | 모델이 이미 아는 일반 절차(파일 목록 보기 등), 한 모드에서만 쓰는 긴 상세가 본문에 있음 |
| 제약 | 깨지면 실제 문제가 되는 불변식이 빠짐 | AGENTS.md에 이미 있는 규칙(거짓 보고 금지, README 우선 등)을 반복, 판단 문제에 MUST/NEVER |
| 완료 기준 | 없음, 또는 관찰할 수 없는 기준("잘 정리됨") | 진행 단계를 다시 나열 |
| 출력 | 사용자 보고 형식이나 커밋 메시지가 없음 | 문장 단위 템플릿을 본문에 통째로 넣음(→ references/ 또는 assets/) |

**합치기 기준**: 두 스킬이 아래 중 두 가지 이상에 해당하면 하나로 합치고 차이는 `진행` 안의 모드로 둔다.
1. 같은 산출물 파일을 만들거나 고친다.
2. 제약이 절반 이상 같다.
3. 한쪽이 다른 쪽의 절차를 이름으로 불러 쓴다("$x의 4단계 방식").
4. 한쪽은 다른 쪽이 결정한 뒤에만 쓰인다(→ 그쪽의 references/로 내린다).

### 3.1 description 쓰기

- 선택은 description만 보고 한다. **"언제 쓰는지"는 전부 description에 넣는다.** 본문의 "When to use" 섹션은 스킬이 선택된 뒤에야 읽히므로 소용없다.
- 무엇 + 언제 + 트리거 단어(사용자가 실제로 칠 말, 파일 확장자, 오류 메시지). 3인칭·서술형으로 쓴다.
- **워크플로를 요약하지 않는다.** superpowers 관찰에 따르면 모델은 설명에 적힌 요약만 따르고 본문을 건너뛴다.
- 짧게. 스킬이 많아지면 Codex가 설명을 자른다. 모호하거나 범용적인 설명("DB 관련 작업")은 과잉 트리거된다.
- 제외 조건은 실제로 잘못 라우팅될 때만 쓴다.

### 3.2 본문 쓰기

- 모델이 이미 아는 내용은 빼고 결정을 바꾸는 정보만 남긴다. "Codex is already very smart."
- **위험도에 맞춰 자유도를 정한다.** 열린 작업은 결과와 판단 기준만, 선호 패턴이 있으면 예시나 파라미터화한 스크립트, 깨지기 쉬운 순서는 고정 명령("이 명령을 그대로 실행, 플래그 추가 금지").
- 명령형으로, 입력과 출력을 명시한다. 용어는 하나로 통일한다(필드/박스/요소를 섞지 않는다).
- 선택지를 늘어놓지 말고 기본값 하나와 예외 경로 하나를 준다.
- 스크립트는 실행할지 읽을지 명시한다. 인터프리터로 호출한다(`bash scripts/x.sh`, `python3 scripts/x.py`). 경로는 `/`를 쓴다.
- 날짜에 따라 바뀌는 정보는 넣지 않는다. 필요하면 "Old patterns"로 분리한다.

## 4. Sol 6.0과 Luna 6가 같은 스킬을 읽을 때

| 관점 | 근거 | 적용 |
|---|---|---|
| outcome 우선 | GPT-5.6 가이드: "목적지를 설명하고 모든 단계를 처방하지 말라" | 골격의 outcome 줄과 완료 기준을 비우지 않는다 |
| 과잉 지시 | Codex 팀 E. Provencher: 레시피형 스킬은 최신 모델의 결과를 오히려 해친다 | 판단 문제는 판단 기준만, 고정 절차는 깨지기 쉬운 곳에만 |
| 소형 모델 | Anthropic: 사용할 모든 모델로 시험하고, 작은 모델에는 안내가 더 필요하다 | 정확해야 하는 단계는 산문이 아니라 명령·체크리스트·`scripts/`로 쓴다. 이렇게 하면 Sol을 묶지 않으면서 Luna도 따라간다 |
| 절대어 | GPT-5.6 가이드: ALWAYS·NEVER·must는 진짜 불변식에만 | 제약 섹션에서만 쓴다 |
| 지시 충돌 | GPT-6 가이드: 스킬 지침이 충돌하면 모델이 일찍 멈출 수 있다. 권장 문구 "사용자 지시가 스킬 지침보다 우선한다" | 스킬마다 반복하지 않고 AGENTS.md에 한 번 둔다 |

## 5. 커뮤니티에서 주목받는 패턴

| 출처 | 규모 | 가져올 것 |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | 약 309k★, Codex App/CLI 지원 | description은 "Use when…" + 증상·트리거만, 워크플로 요약 금지. **스킬도 TDD**: 스킬 없이 실패를 먼저 관찰(RED) → 최소 스킬(GREEN) → 빠져나갈 구멍 막기. 규율형 스킬에는 합리화 표(변명→반박)와 red flags. "실패 유형에 맞는 형식": 규칙 위반에는 금지+표, 출력 형태 오류에는 긍정형 레시피, 누락에는 템플릿 필수 필드 |
| [Anthropic 작성 가이드](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) / [agentskills.io 표준](https://agentskills.io/specification) | 크로스 에이전트 표준 | 자유도 3단계, 참조 1단계, 체크리스트 워크플로, validate-fix 루프, plan-validate-execute(중간 계획 파일을 스크립트로 검증), 평가 3개를 먼저 만든 뒤 작성 |
| OpenAI skill-creator (0.164 내장) | 공식 | 범위·의도 보존, 위험에 비례한 구체성, 발견 비용 최소화, 독립 서브에이전트로 forward-test (정답·의심 버그는 주지 않고 실제 요청만 줌) |

## 6. 이 저장소 점검 결과 (2026-10-30)

§3 판정 기준을 13개 스킬에 적용했다. 4쌍이 합치기 기준에 걸려 13개에서 9개가 됐다. SKILL.md 합계는 452줄에서 337줄이 됐고, 한 모드에서만 쓰는 상세 33줄은 references/로 내렸다. 이름도 name 기준에 걸려 9개 모두 "동사-목적어"로 바꿨다(아래 표의 괄호 안이 이전 이름). `$`를 입력했을 때 목록에서 이름만 보고 목적을 고를 수 있게 하려는 것이다.

| 합친 결과 | 원래 스킬 | 걸린 합치기 기준 |
|---|---|---|
| `capture-requirements` | task-intake + stakeholder-sync | 1(둘 다 INTENT.md), 2(추론 표시·충돌 시 질문·구현 금지) |
| `plan-implementation` + `references/worktree-lanes.md` | plan-slice + worktree-lanes | 4(레인은 plan-slice가 병렬을 제안한 뒤에만 쓰임) |
| `write-submission-docs` | doc-writer + doc-review | 1(같은 제출 문서), 2(근거·과장·한계·실행 명령), 3(writer가 review 체크리스트를, review가 writer 수정 모드를 호출) |
| `rehearse-explanation` + `references/defense.md` | cognition-check + defense-prep | 1(둘 다 COGNITION.md), 3(defense-prep이 "cognition-check 4단계 방식"으로 채점) |

| 스킬 | 과소였던 것 (채움) | 과도했던 것 (덜어 냄) |
|---|---|---|
| capture-requirements (intent) | 완료 기준 없음 | 파일 목록용 `find` 명령, AGENTS.md와 겹치는 가정 규칙 |
| inspect-dataset (data-profile) | outcome·완료 기준·사용자 보고 없음. description의 `<데이터셋>` | description의 처리 과정 요약 |
| research-in-parallel (parallel-research) | outcome·완료 기준 없음. description의 `<레인>` | ctx 사용법 반복, AGENTS.md §5와 겹치는 병렬 규칙, 종합 섹션 해설(66→37줄) |
| plan-implementation (plan-slice) | outcome·완료 기준 없음, 입력이 진행 1단계에 섞여 있음 | — |
| verify-before-done (verify-gate) | outcome, 멈추는 조건(같은 실패 3회 → 보고) 없음 | "다음은 cognition-check"를 출력으로 옮김 |
| write-submission-docs (submit-docs) | 완료 기준 없음 | "짧게, 표와 목록 우선" 같은 일반 조언 |
| rehearse-explanation (cognition-check) | 입력·완료 기준 없음 | 서술형 질문 유형 표를 references/로 |
| save-session-state (handoff) | outcome·완료 기준 없음 | — |
| reuse-prior-work (ctx) | 완료 기준 없음. description의 `<종류>/<주제>` | 다른 스킬 이름을 나열한 종류별 표 |

남은 것:
- `agents/openai.yaml`이 없다. `/skills` 목록의 표시명과 `default_prompt`가 비어 있다.
- "사용자 지시가 스킬 지침보다 우선한다" 문구가 AGENTS.md에 없다.
- 이 PC에는 Python이 없어 `quick_validate.py`와 `tests/run_all.sh`의 Python 단계를 돌리지 못했다. 프런트매터 규칙은 셸로 재현해 확인했다.
- 실제 Codex 세션에서 9개 스킬의 트리거가 기대대로 걸리는지는 확인하지 않았다(사전 체험 5번).

## 출처

- Codex Skills 문서: https://learn.chatgpt.com/docs/build-skills (developers.openai.com/codex/skills에서 리다이렉트)
- 로컬 `~/.codex/skills/.system/skill-creator/SKILL.md`, `references/openai_yaml.md`, `scripts/quick_validate.py` (codex-cli 0.164.0)
- OpenAI GPT-6 가이드: https://developers.openai.com/api/docs/guides/latest-model (`?model=gpt-6-luna`)
- OpenAI GPT-5.6 프롬프트 가이드: https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6
- E. Provencher (Codex) 스킬 설명·과잉 지시 관련 글: https://archive.codenewsletter.ai/2095991462416490862
- openai/skills (deprecated): https://github.com/openai/skills · openai/plugins: https://github.com/openai/plugins
- superpowers writing-skills: https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md
