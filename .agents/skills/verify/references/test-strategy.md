# 테스트 전략 — 위험 기반, 기능 단위

개발 파일과 테스트 파일을 1:1로 맞추지 않는다. 기능마다 실패 가능성과 영향도를 보고 검증 수준을 정한다. 버튼 10개에 테스트 10개보다, 그 버튼들로 저장까지 되는지 보는 흐름 테스트 1개가 낫다.

## 1. 기능 시작 때 검증 방법 정하기

구현 전에 docs/LOG.md "테스트 계획" 표에 기능마다 한 행을 쓴다. 다 만든 뒤 테스트를 맞춰 붙이지 않는다.

| 기능(R-n) | 실패 가능성 | 영향도 | 검증 방법 |
|---|---|---|---|
| 스케줄 저장 (R-2) | 높음: 입력 조합, 비동기 | 높음: 핵심 흐름 | 흐름 1: 입력 → 저장 → 목록 반영, 서버 오류면 입력 유지 |
| 시간 겹침 판정 (R-3) | 높음: 경계값 | 높음: 판정 결과 | 단위: 끝=시작·포함·분리 3건 |
| 목록 정렬 (R-5) | 낮음 | 낮음 | 생략: 브라우저 확인만 |

- 실패 가능성 높음: 계산·집계·변환, 입력 조합이 많은 분기, 0·결측·빈 결과·중복·시간 경계, 비동기 응답 순서, 외부 데이터 형식.
- 영향도 높음: 제출 수치·판정, 안 되면 과제가 실패하는 사용자 흐름, 데이터 저장·삭제, 잘못 읽으면 판단이 틀어지는 표시.

| 실패 가능성 \ 영향도 | 높음 | 낮음 |
|---|---|---|
| 높음 | 흐름 테스트 1개 + 경계값 단위 테스트 | 경계값 단위 테스트 |
| 낮음 | 흐름 테스트 1개 | 생략(브라우저 확인, 이유 한 줄) |

표와 관계없이 항상 테스트한다: 제출 수치를 만드는 계산(손 계산 기대값), 데이터 로딩 경계값, 버그 재현(verify 3단계).

## 2. 흐름 테스트 쓰는 법

- 단위는 사용자가 얻는 결과다. 이름도 동작 문장으로 쓴다: "라인을 바꾸면 그 라인 집계가 보인다".
- 사용자처럼 조작하고 화면으로 확인한다. 요소는 label·role·보이는 글자로 찾고, 클래스·내부 상태·호출 횟수를 확인하지 않는다.
- mock은 외부 경계 한 곳만: FE는 fetch, Python은 외부 API·현재 시각. 내부 함수·컴포넌트를 mock하지 않는다.
- 한 흐름에 정상 경로와 그 흐름의 가장 중요한 실패 하나(서버 오류, 입력 오류, 0·빈 결과)를 담는다.
- 위치: FE는 흐름을 조립하는 파일 옆(`App.test.tsx`, `features/<기능>/<X>Page.test.tsx`), 순수 계산 테스트는 lib 옆. Python은 `tests/test_<기능>.py`.

```tsx
// @vitest-environment jsdom
// features/summary/SummaryPage.test.tsx
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SummaryPage } from "./SummaryPage";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

test("라인을 바꾸면 그 라인 집계가 보이고 0도 숫자로 표시된다", async () => {
  vi.stubGlobal("fetch", vi.fn(async (url: string) => {
    const total = url.includes("line=A") ? 0 : 1234;
    return new Response(JSON.stringify({ total }), { status: 200 });
  }));
  render(<SummaryPage />);
  expect(await screen.findByText("전체 건수: 1,234")).toBeTruthy();
  await userEvent.selectOptions(screen.getByLabelText("라인"), "A");
  expect(await screen.findByText("전체 건수: 0")).toBeTruthy();
});

test("서버 오류면 오류 문구를 alert로 보인다", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response("", { status: 500 })));
  render(<SummaryPage />);
  expect((await screen.findByRole("alert")).textContent).toBe("집계 조회 실패 (500)");
});
```

```python
# tests/test_yield.py — load_lots·summarize_by_line은 설명용 함수
from pytest import approx

def test_line_yield_flow(tmp_path):
    """CSV 로딩부터 라인별 수율까지: total=0 lot은 분모에서 뺀다(D-3)."""
    csv = tmp_path / "lots.csv"
    csv.write_text("lot,line,good,total\nL1,A,95,100\nL2,A,0,0\nL3,B,80,100\n")
    result = summarize_by_line(load_lots(csv))
    assert result["A"] == approx(0.95)  # 손 계산 95/100
    assert result["B"] == approx(0.80)
```

피할 것: 구현을 그대로 베낀 기대값, 호출 여부만 확인하는 mock 테스트, 스냅샷, 스타일·문구만 확인하는 테스트, 커버리지 숫자 목표, 통과시키려고 기대값 고치기.

## 3. 도구

- Python: pytest. FastAPI가 있으면 TestClient로 API 흐름을 검증한다.
- FE: Vitest + Testing Library + jsdom. `package.json`에 `"test": "vitest run --dir src"`를 둔다. `run`은 감시 모드 없이 한 번 실행하고 끝내기 위해, `--dir src`는 src 밖의 E2E 파일(`*.spec.ts`)을 수집하지 않기 위해서다. jsdom은 테스트 파일 첫 줄 주석으로 지정해 설정 파일을 바꾸지 않는다.
- Playwright는 기본 구성이 아니다. 과제 README가 E2E를 요구하거나 환경에 이미 설치되어 있을 때만, 영향도·실패 가능성이 모두 높은 흐름 1~2개에 쓴다. 실제 API 연동 확인은 브라우저 도구로 한다([frontend.md](frontend.md)).

## 4. 한 줄 보고

기능마다 한 줄이다. 같은 줄을 docs/LOG.md 검증 표, 턴 끝 보고의 "검증:", 커밋 메시지 본문에 그대로 쓴다.

```
<PASS|FAIL|미검증|생략> <기능(R-n)> — <조작·입력> → <관찰 결과> (<재실행 명령 또는 테스트 이름>)
```

```
PASS 라인별 집계(R-2) — 라인 A 선택 → 전체 건수 0 표시, 서버 500 → 오류 문구 (npm --prefix frontend run test -- SummaryPage)
PASS 라인 수율 계산(R-3) — 3개 lot CSV → A 0.95·B 0.80, 손 계산 일치 (python3 -m pytest -q tests/test_yield.py)
미검증 실제 API 저장(R-2) — 백엔드 미기동 | 사람 확인: /schedule에서 저장 후 새로고침하면 목록에 남는다
생략 목록 정렬(R-5) — 영향도 낮음, 브라우저에서 헤더 클릭 시 순서 바뀜 확인
```

- 결과는 실행해서 본 것만 쓴다. 명령을 돌리지 않았으면 미검증이다.
- 미검증에는 사람이 그대로 따라 할 경로·동작·기대값을 붙인다.
- FAIL은 원인 한 줄과 함께 그대로 보고하고 커밋하지 않는다.
