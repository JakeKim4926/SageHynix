# FE 코드 작성 규칙과 예시

기존 코드의 일관된 규칙이 우선이다. 아래는 신규 TypeScript/React 코드의 기본값이며, 예시의 Summary는 설명용 계약이다. 실제 데이터 필드와 업무 의미를 먼저 확인한다.

## 1. 타입과 외부 데이터

strict를 유지한다. 근거 없는 any·@ts-ignore·non-null assertion으로 오류를 숨기지 않는다. 외부 응답은 unknown으로 받아 경계에서 검증한다. 복잡한 제네릭보다 구체적인 타입을 우선하고, 기존 스키마 검증 도구가 있으면 재사용한다.

`(await response.json()) as Summary`는 검증이 아니다. 작은 응답은 다음처럼 확인할 수 있다.

```ts
export type Summary = { total: number };

export function parseSummary(value: unknown): Summary {
  if (
    typeof value !== "object" || value === null ||
    !("total" in value) || typeof value.total !== "number" ||
    !Number.isInteger(value.total) || value.total < 0
  ) {
    throw new Error("집계 응답 형식이 올바르지 않습니다.");
  }
  return { total: value.total };
}
```

## 2. 통신 경계

호출·HTTP 오류·응답 검증은 기능별 API 모듈 또는 lib/api.ts에서 처리한다. 화면마다 복제하지 않는다. 아래 코드는 위 타입과 파서가 같은 모듈에 있는 경우다.

```ts
export async function getSummary(signal?: AbortSignal): Promise<Summary> {
  const response = await fetch("/api/summary", { signal });
  if (!response.ok) throw new Error(`집계 조회 실패 (${response.status})`);
  const value: unknown = await response.json();
  return parseSummary(value);
}
```

조건 변경 중 이전 응답이 도착하면 최신 결과를 덮어쓰지 않도록 취소 또는 요청 식별자를 사용한다. 취소를 사용자 오류로 표시하지 않는다. 기존 쿼리 라이브러리가 있으면 그 방식을 따른다.

## 3. 상태는 모순 없이

로딩·오류·성공을 독립 boolean으로 중복 저장하기보다 판별 가능한 상태로 표현한다. 아래 예시는 Summary 타입을 같은 모듈에 두거나 type import한 경우다.

```tsx
type LoadState<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: T };

function SummaryPanel({ state }: { state: LoadState<Summary> }) {
  if (state.status === "loading") return <p role="status">불러오는 중입니다.</p>;
  if (state.status === "error") return <p role="alert">{state.message}</p>;
  return <p>전체 건수: {state.data.total.toLocaleString("ko-KR")}</p>;
}
```

사용자 실행 전 대기 상태가 있으면 idle을 추가한다. 재조회 중 기존 결과 유지가 필요하면 그 UX를 명시해 상태 모델을 확장한다.

## 4. 숫자 의미 보존

0·결측·빈 결과를 구분하고 반올림은 표시 단계에서 한다. `value || "—"`는 0을 결측으로 바꾸므로 사용하지 않는다. `value ?? "—"`는 null과 undefined만 대체한다.

```ts
// 입력 계약: 0~1의 검증된 비율 또는 결측 null
export function formatPercent(ratio: number | null): string {
  return ratio === null ? "—" : `${(ratio * 100).toFixed(1)}%`;
}
```

검증 예: 0 → "0.0%", 0.125 → "12.5%", null → "—". NaN·범위 초과는 입력 경계에서 처리한다. 분모가 0인 경우의 의미는 업무 계산 계약으로 정한다.

## 5. 필요한 만큼 분리

기존 컴포넌트와 스타일을 먼저 재사용한다. 반복이나 책임 분리 필요가 생길 때 공통화한다. 파일 줄 수만으로 분할하지 않는다. 단순 화면에 범용 폼·표 엔진을 먼저 만들지 않는다.

파생값은 중복 상태로 저장하지 않는다: `const selectedRows = rows.filter(row => selectedIds.has(row.id));`.
useMemo/useCallback·전역 상태·별도 라우터는 기본 설치 항목이 아니다. 측정된 문제나 요구사항이 있으면 도입한다. React 상태의 배열·객체는 직접 변경하지 않는다. 목록 key는 안정된 데이터 ID를 사용한다.

## 6. 의미 있는 HTML과 스타일

클릭 동작은 button, 이동은 링크, 입력에는 label을 사용한다. 색상만으로 상태를 전달하지 않는다. 재사용할 색상·간격은 프로젝트 디자인 토큰에 맞춘다. Tailwind 클래스 반복이 커지면 실제 공통 컴포넌트로 묶는다.

```tsx
function AnalyzeButton({ busy, onRun }: { busy: boolean; onRun: () => void }) {
  return (
    <button type="button" disabled={busy} onClick={onRun}>
      {busy ? "분석 중…" : "분석 실행"}
    </button>
  );
}
```

## 검증 연결

타입·린트는 자동 검사, 입력·오류·빈 결과는 동작 확인, 수치는 대표 입력 재계산, 키보드·화면 겹침은 브라우저 확인으로 검증한다. 예제 코드를 복사했다는 사실만으로 검증되었다고 보고하지 않는다.
