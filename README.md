# SageHynix — 해커톤용 Codex 하네스

데이터·AI 문제 해결 과제를 위한 작업 규칙, 스킬 16개, 검증 도구, 작업 기억을 담은 프로젝트다. **이 README는 하네스 안내이며, 주최 측 과제 지시서가 아니다.**

## 빠른 시작

clone한 폴더를 작업·제출 폴더로 사용할 수 있는지 먼저 확인한다.

```bash
git clone https://github.com/JakeKim4926/SageHynix.git
cd SageHynix
bash setup.sh
```

`setup.sh`는 ctx·Git 제외/병합 설정·실행 권한을 준비하고 환경을 점검한다. 기본 실행은 패키지를 설치하지 않는다. 실패하면 종료 코드 1과 복구 안내를 출력한다.

주최 측이 지정한 과제 폴더가 이미 있다면 그 폴더에 적용한다.

```bash
bash bootstrap.sh /실제/과제/폴더
cd /실제/과제/폴더
```

기존 과제 README와 파일을 보존한다. 충돌 파일은 목록으로 보고하며 자동 커밋하지 않는다. 파일을 검토하고 충돌을 해결한 뒤 커밋해야 worktree 레인에도 하네스가 전달된다.

## 필요한 도구만 준비

```bash
# 점검만: 설치·ctx 갱신 없음
bash .harness/bin/doctor.sh
bash .harness/bin/doctor.sh --profile data verify

# 해당 기능이 필요할 때: 누락 패키지 설치 후 재검증
bash setup.sh --install data verify

# 준비한 프로젝트 환경으로 Codex 실행
bash .harness/bin/start.sh
```

선택 기능: `verify`, `data`, `excel`, `parquet`, `api`, `dashboard`, `plot`, `ml`.

핵심 하네스는 Bash 4+, Git, Python 3.9+, 플랫폼의 Codex를 사용한다. 데이터·웹 라이브러리는 과제에 필요한 것만 설치한다. 설치 여부 판별, 가상환경, 누락 도구 설치 안내와 실패별 복구는 **[환경 준비 가이드](docs/SETUP.md)**를 따른다.

## 프로젝트 구조

```text
AGENTS.md                 Codex 작업 규칙 및 시작 절차
.agents/skills/            스킬 16개의 단일 원본
.codex/                   프로젝트 설정, 에이전트, 훅, 규칙
.harness/bin/              환경 점검, ctx, 검증, worktree, fanout
.harness/tests/            하네스 자체 테스트 (과제 tests/와 분리)
ctx/                      조사·결정·데이터·세션 작업 기억
docs/                     INTENT, PLAN, DECISIONS, VERIFICATION, COGNITION, WORKLOG
setup.sh                  현재 폴더 초기화·선택 설치·검증
bootstrap.sh              기존 과제 폴더에 하네스 적용
```

`template/` 및 플러그인 설치를 거치지 않고 루트 파일을 직접 사용한다. 프로젝트 설정은 모델·승인 정책·샌드박스·인증을 덮어쓰지 않는다. 가상환경·로그·로컬 상태는 Git에서 제외한다.

## 과제 시작

1. 환경 점검 통과 후 Codex 프로젝트 신뢰와 훅 신뢰를 확인한다. `/skills`에 16개가 보이는지, 허용 모델인지 확인한다.
2. `$task-intake`에 **실제 과제 지시서 경로**를 전달한다.
3. 조사·계획 → 구현 → `$verify-gate` → `$cognition-check`를 반복한다.
4. `$doc-writer`, `$doc-review`, `$defense-prep`로 제출을 준비한다.

작업 기억은 `ctx/`에 남는다. `$ctx`로 기존 결과를 찾고, `$handoff`로 다음 세션에 상태를 전달한다. 병렬 조사에는 `$parallel-research`, 독립 구현에는 `$worktree-lanes`를 쓴다.

하네스의 정책 검사 통과와 Codex 내부에서 훅이 실제 실행되는 것은 별개다. 플랫폼에서 훅 신뢰·실행, 커스텀 에이전트 노출, Browser 포트 연결을 확인해야 한다. 실제 시험 환경의 설치 패키지와 Codex 버전은 미확인이다.

## 하네스 자체 검증

```bash
bash .harness/tests/run_all.sh
```

단위 테스트와 셸 구문 검사를 실행한다. 실제 Codex 모델 호출이나 패키지 다운로드는 하지 않는다. 과제 코드는 별도 `tests/`와 `bash .harness/bin/verify.sh`로 검증한다.

설계 배경과 기존 조사 기록: [docs/DESIGN.md](docs/DESIGN.md).

## FE 작업

기존 앱과 과제 요구를 우선한다. 신규 커스텀 UI의 기본 후보는 TypeScript(strict)·React·Vite·Tailwind이며, 기본 미리보기는 `0.0.0.0:3000`이다.

- `$fe-setup`: 실제 환경과 의존성 확인, 필요한 설치, 미리보기 검증.
- `$fe-build`: 코드 작성 규칙·예시, 데이터 계약, 화면 상태를 따라 기능 구현.
- `$fe-design`: SK CI(SK Red·SK Orange) 기반 디자인 토큰·화면 골격·차트 색 적용.
- `$verify-gate`: FE 타입·린트·빌드·실제 동작·수치 검증을 기존 기록에 통합.

FE 스킬은 자연어 절차와 예시이며 사전 앱 템플릿을 포함하지 않는다. 코드·스킬 반입 허용은 과제 규정을 따른다. Node/npm 설치는 현재 `setup.sh --install` Python 프로필에 포함되지 않는다.

FE 자동 검증은 과제 작업 중 `.harness/verify.local.sh`에 앱 명령을 연결한다. 이 파일은 `verify.sh`가 Bash로 실행하므로 실행 비트가 없어도 동작한다. 기본 `npm test --if-present` 성공만으로 FE 검증을 통과 처리하지 않는다. 자세한 기준은 [.agents/skills/verify-gate/references/frontend.md](.agents/skills/verify-gate/references/frontend.md)를 따른다.
