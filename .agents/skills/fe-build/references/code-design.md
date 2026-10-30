# 구조·이름·컴포넌트 설계 예시

[coding-rules.md](coding-rules.md) 0절·5절의 예시다. 신규 앱의 첫 컴포넌트를 만들 때, 컴포넌트를 나누거나 상태 위치를 정할 때 읽는다. Lot은 설명용 타입이며 실제 필드는 데이터에서 확인한다.

## 1. 이름과 기준값

```tsx
// lib/calc.ts — React를 import하지 않는 순수 함수
export const YIELD_TARGET = 0.95; // D-2: 담당자 답변 기준 목표 수율

export function isBelowTarget(yieldRatio: number): boolean {
  return yieldRatio < YIELD_TARGET;
}
```

```tsx
// components/LineFilter.tsx — 받는 prop은 onX
export function LineFilter({ value, onChange }: { value: string; onChange: (line: string) => void }) {
  return (
    <label>
      라인
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="all">전체</option>
        <option value="A">A</option>
      </select>
    </label>
  );
}

// App.tsx — 만드는 쪽은 handleX
const handleLineChange = (nextLine: string) => {
  setLine(nextLine);
  setPage(1);
};
<LineFilter value={line} onChange={handleLineChange} />;
```

나쁜 예: `0.95`를 컴포넌트 여러 곳에 직접 쓰기, `const [flag, setFlag]`, `onClick={doIt}`, `export default function () {}`.

## 2. render 함수 대신 컴포넌트

```tsx
// 나쁜 예: 렌더마다 새 함수, 이름이 개발 도구에 안 보임, 분리하기 어려움
function LotTable({ lots }: { lots: Lot[] }) {
  const renderRow = (lot: Lot) => <tr key={lot.id}><td>{lot.id}</td></tr>;
  return <table><tbody>{lots.map(renderRow)}</tbody></table>;
}

// 좋은 예
function LotRow({ lot }: { lot: Lot }) {
  return <tr><td>{lot.id}</td></tr>;
}

function LotTable({ lots }: { lots: Lot[] }) {
  return <table><tbody>{lots.map((lot) => <LotRow key={lot.id} lot={lot} />)}</tbody></table>;
}
```

## 3. boolean 모드 prop 대신 분리

```tsx
// 나쁜 예: isCompact·isEditable·showChart 조합마다 분기가 늘어난다
<LotCard lot={lot} isCompact isEditable={false} showChart />

// 좋은 예: 화면 용도별 컴포넌트, 공통 부분만 작은 컴포넌트로 공유
<LotSummaryCard lot={lot} />
<LotDetailPanel lot={lot} />
```

## 4. 조건부 렌더링

```tsx
// 나쁜 예: defectCount가 0이면 화면에 "0"이 찍힌다
{defectCount && <DefectBadge count={defectCount} />}

// 좋은 예
{defectCount > 0 && <DefectBadge count={defectCount} />}
```

```tsx
// 나쁜 예: 중첩 삼항
return lots === null ? <Spinner /> : lots.length === 0 ? <Empty /> : <LotTable lots={lots} />;

// 좋은 예: early return
if (lots === null) return <Spinner />;
if (lots.length === 0) return <Empty />;
return <LotTable lots={lots} />;
```

## 5. useEffect가 필요 없는 경우

```tsx
// 나쁜 예: 파생값을 effect로 동기화 — 한 번 더 렌더되고 값이 어긋날 수 있다
const [filtered, setFiltered] = useState<Lot[]>([]);
useEffect(() => {
  setFiltered(lots.filter((lot) => lot.line === line));
}, [lots, line]);

// 좋은 예: 렌더 중 계산
const filtered = lots.filter((lot) => lot.line === line);
```

```tsx
// 나쁜 예: 사용자 동작의 결과를 effect로 처리
useEffect(() => {
  if (submitted) downloadCsv(filtered);
}, [submitted, filtered]);

// 좋은 예: 이벤트 핸들러에서 처리
const handleDownload = () => downloadCsv(filtered);
```

useEffect가 맞는 경우: 조건이 바뀔 때 API 조회(취소 포함, coding-rules 2절), 구독, 타이머, 차트 라이브러리처럼 DOM을 직접 다루는 외부 객체 연결.

## 6. 상태 위치

```tsx
// 필터를 표와 차트가 함께 쓴다 → 공통 부모(App)에 둔다
function App({ lots }: { lots: Lot[] }) {
  const [line, setLine] = useState("all");
  const visibleLots = lots.filter((lot) => line === "all" || lot.line === line);
  return (
    <>
      <LineFilter value={line} onChange={setLine} />
      <YieldChart lots={visibleLots} />
      <LotTable lots={visibleLots} />
    </>
  );
}
```

정렬 방향처럼 표 안에서만 쓰는 상태는 LotTable 안에 둔다. 전역 상태 라이브러리는 요구사항이 생길 때 도입한다.
