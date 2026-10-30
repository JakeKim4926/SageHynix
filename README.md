# SageHynix — 해커톤용 Codex 하네스

데이터·AI 문제 해결 과제를 위한 작업 규칙, 스킬 5개(검증 + git + FE 3개), 서브에이전트 2개, 6칸 지시 형식(SCRIPT), 가드레일 훅을 담은 프로젝트다. 180분 안에 쓸 수 있는 만큼만 남겼다. **이 README는 하네스 안내이며, 주최 측 과제 지시서가 아니다.**

## 빠른 시작

clone한 폴더를 그대로 작업 폴더로 쓰거나:

```bash
git clone https://github.com/JakeKim4926/SageHynix.git
cd SageHynix
```

과제 폴더가 따로 있으면 그 폴더에서 하네스 파일만 복사한다. `-n`은 과제 README 등 기존 파일을 덮어쓰지 않는다.

```bash
git clone https://github.com/JakeKim4926/SageHynix.git /tmp/h
cp -rn /tmp/h/AGENTS.md /tmp/h/.agents /tmp/h/.codex /tmp/h/prompts .
```

## 구조

```text
AGENTS.md          Codex 작업 규칙
.agents/skills/     verify, git, fe-setup, fe-build, fe-design
.codex/            프로젝트 설정, 에이전트(researcher, verifier), 가드레일 훅, 규칙
prompts/SCRIPT.md   6칸 지시 형식과 복사용 빈 틀
```

프로젝트 설정은 모델·승인 정책·샌드박스·인증을 덮어쓰지 않는다. 훅 로그(`.codex/log/`)와 가상환경은 Git에서 제외한다.

## 과제 시작

1. Codex 프로젝트 신뢰와 훅 신뢰를 확인한다. `/skills`에 5개가 보이는지, 허용 모델인지 확인한다.
2. `prompts/SCRIPT.md`의 빈 틀을 복사해 **실제 과제 지시서 경로**를 채우고 과제를 파악한다.
3. 기능마다 `main`에서 작업 브랜치를 만들고, 구현 → `$verify` → 커밋을 반복한 뒤 로컬에서 `main`으로 머지한다(`$git`, push·PR 없음).

| 쓰는 곳 | 형식 |
|---|---|
| 사람 → Codex, Codex → 서브에이전트, 세션 → 새 세션 | `prompts/SCRIPT.md` 6칸 `[Role] [Context] [Task] [Rules] [Output] [Done]` |
| 업무 담당자(메신저) | 짧은 자연어 질문 + 선택지 |

작업 기억은 과제 중에 Codex가 만드는 파일로만 남는다: 요구사항·결정은 `docs/INTENT.md`, 조사는 `docs/research/<주제>.md`, 검증과 인수인계는 `docs/LOG.md`.

플랫폼에서 훅 신뢰·실행, 커스텀 에이전트 노출, Browser 포트 연결은 직접 확인해야 한다. 실제 시험 환경의 설치 패키지와 Codex 버전은 미확인이다.

## FE 작업

기존 앱과 과제 요구를 우선한다. 신규 커스텀 UI의 기본 후보는 TypeScript(strict)·React·Vite·Tailwind이며, 기본 미리보기는 `0.0.0.0:3000`이다.

- `$fe-setup`: 실제 환경과 의존성 확인, 필요한 설치, 미리보기 검증.
- `$fe-build`: 구조 규칙(flat → features)과 구조 검사 스크립트, 코드 작성 규칙·예시, 데이터 계약, 화면 상태를 따라 기능 구현.
- `$fe-design`: SK하이닉스 공식 CI(SK Red·SK Orange와 보조색) 기반 디자인 토큰·화면 골격·차트 색 적용.
- `$verify`: 기능 시작 때 위험 기반 테스트 계획([test-strategy.md](.agents/skills/verify/references/test-strategy.md)), 작업 단위마다 완료 판정·커밋 관문(테스트·수치 재계산·서버/화면 확인)과 기능별 한 줄 보고. FE 변경은 [frontend.md](.agents/skills/verify/references/frontend.md) 기준을 더한다.
