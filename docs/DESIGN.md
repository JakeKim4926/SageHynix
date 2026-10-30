# 설계 근거

## 1. 응시 가이드(PDF)에서 하네스 설계에 직접 영향을 준 사실

| 가이드 내용 | 하네스 결정 |
|---|---|
| 작업 180분, 이후 후속 서술형(문항당 5분, AI·복붙 금지, 제출물·작업 기록 기반 출제). FAQ에는 6문항 | 인지 부채 장치(`rehearse-explanation` 슬라이스·제출 모드)를 1급으로 둠. 타이머 훅으로 단계 전환 강제 |
| 수집 기록: 내장 AI·코딩 에이전트·실무자 에이전트 대화, 터미널 CLI 세션, AI 도구 설정, git log·diff·테스트 결과, 작업 공간 파일 | 커밋 메시지 규칙(R/D ID 연결), `VERIFICATION.md` 증거 기록, 하네스 파일 자체를 커밋(도구 설정도 평가 대상) |
| 웹 IDE(E2B), 터미널에서 `codex` 실행, 기본 승인 정책은 필요 시 요청 | 프로젝트 `.codex/config.toml`은 모델·승인·샌드박스를 덮어쓰지 않음 |
| 개인 PC 파일·비공개 Skill 업로드 불가, 공개 GitHub 저장소·Skill·MCP·Plugin은 clone/다운로드 허용, git push 불가 | 공개 저장소 clone + `bootstrap.sh` 설치 방식. `git push`는 훅·규칙 이중 차단 |
| 외부 전송 모니터링, 플랫폼 관리 설정·연결 프로세스 수정·종료 금지, 키·토큰 공개 금지 | PreToolUse 훅: 외부 업로드·원격 도구·`~/.codex/config.toml` 수정·키 출력·플랫폼 프로세스 kill 차단 |
| 권장 모델 Sol 6.1 / Terra 5.6 / Luna 6 / Sol 6.0, Astra 사용 제한, 토큰 사용량 추적(간접 평가) | UserPromptSubmit 훅이 Astra면 차단. 서브에이전트 기본 effort medium, 동시 4개 제한, "독립 질문만 병렬" 규칙 |
| 서버는 `0.0.0.0` 바인딩, Browser 탭에서 포트·경로 지정 | AGENTS.md 절대 규칙 7, `verify-before-done`에서 curl 확인 |
| 제출 문서(계획·협업 기록 등)는 AI와 작성 가능, "판단과 근거, 검증 결과, 남은 한계"를 담을 것. 필수 파일명은 과제 안내를 따름 | `write-submission-docs`: README 지정 양식 우선, 주장마다 근거 링크, 한계 섹션 필수, 제출 전 주장-근거 대조 감사 |
| 에디터와 AI가 같은 파일을 수정하면 저장 충돌 | `write-submission-docs` 수정 모드에서 "외부 변경 불러오기" 안내 |
| 응답 시간을 고려한 위임·시간 안배도 AI 활용 역량 | `plan-implementation` 슬라이스 15~30분, 재계획 기준, 서브에이전트 병렬은 독립 질문만 |
| 제출 직전 결과물 통째 교체는 부정 의심 | AGENTS.md 커밋 규칙: 통째 교체·히스토리 재작성 금지, 훅이 `reset --hard`·`rebase` 차단 |

## 2. Cofa(Probe) 평가 방식 — 웹 조사 (2026-10-29)

사실(출처 있음):
- Probe 평가 축: **Technique**(작동·검증) / **Intent**(목표·제약 전달과 조종) / **Cognition**(작동 원리·실패 지점 설명). 산출물·프롬프트·도구 설정·AI 대화·검증 기록·소스·작업 로그를 수집하고, 사후 Q&A 답변을 실제 구현과 대조한다. — https://getcofa.com/en/probe
- 과거 코파톤 참가 후기: 루트 README에 실무자의 문제와 방향이 상세히 있었고, 시나리오 에이전트는 README 범위를 거의 벗어나지 않음. 상위권은 성공 기준·범위를 실무자와 먼저 합의하고 기록했으며, 세션 인수인계 체계로 좋은 평가. 축별 편차가 가장 큰 것은 Intent, 평균이 가장 낮은 것은 Cognition. — https://brunch.co.kr/@luma/5 (개인 후기)
- SK하이닉스 공식 소식: 예선에서 Cofa-Probe 등으로 "문제 정의, AI 활용, 결과 검증"을 본다. — https://news.skhynix.co.kr/ai-hackathon-2026/

추론(검증 안 됨):
- 이번 과제도 README + 업무 담당자 에이전트 구조일 가능성이 높다 → `capture-requirements`가 README를 1차 원천으로, 담당자 질문은 짧고 선택지형으로.
- 데이터 형태(공정·수율·설비 CSV 등)는 1차 예선 후기와 주제명에서 나온 추정이다. 하네스는 특정 도메인을 가정하지 않는다.

찾지 못한 것: 공식 루브릭 배점, 토큰 사용량의 구체적 반영 방식, 2차 예선 실제 과제 유형.

## 3. Codex 기능 매핑 (공식 문서 확인, 2026-10-29)

| 기능 | 위치 | 비고 |
|---|---|---|
| AGENTS.md | 저장소 루트→cwd 순 연결, 기본 32KiB | `project_doc_max_bytes = 65536` |
| Skills | `.agents/skills/<name>/SKILL.md` (cwd~저장소 루트), `$HOME/.agents/skills` | 프런트매터 `name`, `description` 필수. 초기 목록은 컨텍스트의 2% 예산 |
| 서브에이전트 | `.codex/agents/*.toml` (`name`, `description`, `developer_instructions` 필수) | 샌드박스·승인은 부모 설정을 따름. `[agents] max_concurrent_threads_per_session` |
| Hooks | `.codex/hooks.json` | 프로젝트 `.codex/` 신뢰 + `/hooks`에서 훅 신뢰 필요(해시 기준, 변경 시 재신뢰) |
| Rules | `.codex/rules/*.rules` (`prefix_rule`) | `match`/`not_match`가 로드 시 검증됨. `codex execpolicy check`로 시험 |
| Plugins | `.codex-plugin/plugin.json` + `skills/`, 마켓플레이스 `.agents/plugins/marketplace.json` | `codex plugin marketplace add <owner/repo>` → `codex plugin add <plugin>@<marketplace>` |

## 4. 작업 기억 `ctx/` 설계 (2026-10-30)

문제: 권장 모델은 긴 문서 분석·큰 작업에서 맥락을 잃는다. 대화 압축, 긴 맥락 중간 정보의 주목 저하, 초기 제약의 희석은 모든 모델에 생기고, 약한 모델에서 더 심하다.
결정: 기억을 모델 밖 파일로 두고, 필요한 순간에 다시 넣는다.

| 결정 | 이유 |
|---|---|
| `docs/`(제출용)와 `ctx/`(작업 기억) 분리 | 과제 README가 제출 파일명을 정할 수 있고, 합치면 제출 문서에 작업 찌꺼기가 섞인다 |
| 2단 구조: `INDEX.md` 한 장 + 필요한 항목만 `get` | 폴더째 참조하면 맥락이 다시 넘친다 |
| 메타데이터는 `index.jsonl` 이벤트(덧붙이기만), 쓰기는 `ctx.py`만 | 모델이 JSON을 직접 고치면 한 글자 실수로 전체가 깨진다. 덧붙이기만 하면 병렬 레인과 git union 병합이 안전하다 |
| 본문은 Markdown, 필수 섹션 검증 | 모델이 잘 쓰는 형식. 빈 결론·근거 없는 보고를 `done` 단계에서 거부 |
| 입력 해시·의존 버전으로 `stale` 판정 | 오래된 결과를 재사용하는 실패를 막는다. 해시는 크기·mtime이 바뀐 경우에만 다시 계산 |
| 훅은 `index.jsonl`만 읽고 해시 계산 안 함 | 매 프롬프트마다 큰 데이터 파일을 해시하면 느리다. 신선도 판정은 `get`/`find`에서 |
| 매 프롬프트 주입은 관련 항목 최대 3줄 | 토큰 사용량도 평가 신호. 전체 목록은 세션 시작·재개·압축 직후에만 |
| 검색은 양방향 부분 문자열 일치 | 한국어 조사("이상치를")가 붙어도 찾게. 형태소 분석기는 의존성이 생겨 쓰지 않았다 |

한계: 검색은 단어 일치라 다른 표현으로 같은 질문을 하면 못 찾을 수 있다(`--q`에 나중에 찾을 단어를 넣으라고 skill에 명시). 모델이 `find`를 건너뛰는 것은 훅의 관련 항목 주입으로만 보완된다 — 강제는 아니다.

## 5. 의도적으로 하지 않은 것
- 모델 고정: 시험 환경의 모델 slug가 로컬과 같다는 보장이 없어 에이전트 파일에 `model`을 쓰지 않았다(부모 모델 상속).
- 승인 정책·샌드박스 완화: 플랫폼 기본 설정을 바꾸는 것으로 보일 수 있어 하지 않았다.
- Stop 훅으로 검증 강제: 턴이 끝나지 않는 루프 위험과 토큰 낭비 때문에 넣지 않았다. 대신 AGENTS.md 보고 형식과 `verify-before-done`로 유도.
- 도메인 특화 코드·정답 템플릿: "제출 직전 통째 교체"류 의심과 규정 위반 소지를 피하기 위해 넣지 않았다.
