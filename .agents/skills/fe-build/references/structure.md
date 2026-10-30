# FE 구조 규칙 (Layer → Feature)

신규 React 앱의 파일 위치·import 방향·구조 전환의 기준은 이 문서 하나다. 과제가 지정했거나 기존 앱이 가진 구조가 있으면 그것을 따르고, docs/LOG.md 현재 상태에 "구조: 기존 앱 규칙(<요약>)"으로 적는다. 그 경우 5절 검사 스크립트는 쓰지 않는다.

## 1. 단계

처음에는 기술 계층별 평평한 구조(flat)로 시작하고, 기능이 늘면 기능 단위(features)로 묶는다. 조건 전에 features/를 미리 만들지 않는다.

| 단계 | 조건 |
|---|---|
| flat | 시작 기본값 |
| features | 독립된 화면(별도 조회 흐름을 가진 탭·페이지)이 2개 이상, 또는 src 코드 파일이 15개를 넘음 |

```
src/                        flat
  main.tsx                  진입 — 렌더만
  App.tsx                   화면 조립, 화면 간 공유 상태
  components/               화면 조각 (KpiCard.tsx, YieldChart.tsx)
  hooks/                    상태·조회 훅 (useSummary.ts)
  api.ts                    호출·HTTP 오류·응답 검증 (커지면 api/<자원>.ts)
  lib/                      순수 계산·포맷·상수 (calc.ts, format.ts)와 그 테스트
  types.ts                  2개 이상 파일이 쓰는 타입 (커지면 types/<주제>.ts)
```

```
src/                        features
  main.tsx, App.tsx         앱 골격(상단 바·화면 전환)과 feature 화면 배치만
  features/
    yield/
      YieldPage.tsx         이 기능 화면 조립 (feature 루트의 .tsx)
      components/ hooks/ api.ts lib/ types.ts   이 기능만 쓰는 것, 필요한 것만 만든다
  components/ hooks/ api.ts lib/ types.ts       2개 이상 feature가 쓰는 공용
```

src 바로 아래 코드 파일은 main·App·api·types만 둔다. 위 표에 없는 폴더(utils/, services/, helpers/ 등)를 만들지 않는다. assets/·styles/·test/는 코드 계층이 아니므로 허용한다.

## 2. 어디에 두나

| 코드 | 위치 |
|---|---|
| JSX를 반환한다 | components/ — `PascalCase.tsx`, 파일명과 같은 이름을 named export |
| useState·useEffect를 묶은 재사용 로직, 조회+취소+LoadState | hooks/ — `useX.ts`, 같은 이름을 named export ([code-design.md](code-design.md) 7절) |
| fetch, HTTP 오류, 응답 파싱 | api.ts ([coding-rules.md](coding-rules.md) 1·2절) |
| React 없이 하는 계산·포맷·정렬·집계, 기준값 상수(D-n 주석) | lib/ |
| 2개 이상 파일이 쓰는 타입(LoadState 포함) | types.ts. 한 파일만 쓰면 그 파일 안에 둔다 |
| 한 feature만 쓰는 것 | 그 feature 안. 두 번째 feature가 쓰게 되면 공용으로 올린다 |

공용으로 올리거나 feature 안으로 내릴 때는 이동만 하고, 같은 커밋에서 동작·이름을 바꾸지 않는다.

## 3. import 방향

| 이 위치의 파일은 | import할 수 있다 |
|---|---|
| main·App | 공용 전부, feature의 루트 .tsx(화면)만 |
| feature 루트 .tsx | 자기 feature 전부, 공용 전부(App 제외) |
| components | components, hooks, lib, types |
| hooks | hooks, api, lib, types |
| api | api, lib, types |
| lib | lib, types |
| types | types |

- feature 안의 하위 폴더도 같은 표를 따른다. features/yield/lib는 features/yield/components를 import하지 않는다.
- feature끼리 import하지 않는다. 함께 쓸 것은 공용으로 올린다. 공용 코드는 feature를 import하지 않는다.
- components는 api를 직접 부르지 않는다. 조회는 hooks나 App·feature 화면에서 하고 결과를 props로 내린다.
- lib·api는 react·react-dom을 import하지 않는다. App·main은 다른 파일이 import하지 않는다.
- index 재수출 파일(barrel)과 `export default`를 만들지 않는다. 진입은 main.tsx다.
- 경로 alias `@/`는 tsconfig와 vite 설정을 함께 바꿀 때만 쓴다. 검사 스크립트는 `@/`를 src로 해석한다.

## 4. features 전환 절차

전환은 요청 없는 리팩터링이 아니라 기록된 결정으로 한다.

1. 1절 조건 충족을 확인하면 `docs/INTENT.md`에 D-n을 남긴다: 근거(화면 수·코드 파일 수), 새 feature 이름, 공용으로 남길 파일.
2. 전환 커밋은 이동만 한다: `git mv`와 import 경로 수정. 동작·이름·스타일 변경을 섞지 않는다.
3. 타입 검사·린트·빌드·기존 테스트·5절 구조 검사를 통과하고, 브라우저를 새로고침해 화면이 그대로인지 확인한다(이동 중의 HMR 오류는 새로고침 전까지 남는다). 그 뒤 `refactor(fe): features/ 구조 전환 — D-n`으로 커밋한다.
4. docs/LOG.md 현재 상태의 "구조"를 갱신한다.

## 5. 구조 검사

프로젝트 루트에서 실행한다. 앱 src 경로는 실제 앱에 맞춘다.

```bash
node .agents/skills/fe-build/scripts/check-structure.mjs frontend/src
```

- 1~3절 위반(위치·import 방향·feature 간 import·react import·barrel·default export·파일 이름)은 ERROR, 종료 코드 1이다. 고친 뒤 다시 실행한다.
- flat인데 코드 파일이 15개를 넘으면 WARN이다. 실패는 아니지만 4절 전환 여부를 D-n으로 정한다.
- 첫 줄의 `구조=` 값을 LOG 현재 상태에 옮긴다. 테스트 파일(`*.test.*`, `*.spec.*`)과 `.d.ts`는 검사하지 않는다.
- 스크립트는 하네스 검사 도구이며 앱에 복사하지 않는다. 통과시키려고 스크립트나 규칙을 고치지 않는다. 예외가 필요하면 D-n으로 남기고 사용자에게 알린다.
