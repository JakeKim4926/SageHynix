# SK 디자인 토큰

출처: SK Red `#EA002C`(Pantone 186C)는 SK 계열사 공식 CI 페이지 값이다. SK Orange는 `#F47725`(SK플래닛 CI)를 쓰며, 일부 계열사는 `#FF7A00`으로 표기한다. 주최 측 가이드가 있으면 그 값으로 바꾼다. 나머지 중립·상태·차트 색은 이 하네스의 기본값이다.

## 색

| 토큰 | 값 | 용도 | 흰 배경 대비 |
|---|---|---|---|
| brand | `#EA002C` | 주요 버튼, 활성 탭, 상단 강조선 | 4.63 (흰 글자 가능) |
| brand-strong | `#C70025` | brand hover, brand-soft 위 글자 | 6.08 |
| brand-soft | `#FDECEF` | 선택 행·활성 칩 배경 | — |
| accent | `#F47725` | 차트 보조 계열, 아이콘, 장식 | 2.80 (글자 금지, 위 글자는 ink) |
| ink | `#191F28` | 본문·제목 | 16.56 |
| muted | `#5B6370` | 보조 글자, 축 라벨 | 6.06 |
| line | `#E1E4EA` | 카드 테두리, 구분선 | — |
| canvas | `#F5F6F8` | 페이지 배경 | — |
| surface | `#FFFFFF` | 카드·상단 바 | — |
| success | `#1A7F37` | 양호·통과 | 5.08 |
| warning | `#B54708` | 주의 | 5.43 |
| danger | `#B42318` | 오류·불량·실패 | 6.57 |

brand-soft 위 글자는 brand가 아닌 brand-strong을 쓴다(brand는 4.06으로 미달).

## 글꼴·간격·모양

- 글꼴: `"Pretendard", system-ui, -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", "Noto Sans KR", sans-serif`. 설치하지 않고 있는 글꼴을 쓴다.
- 숫자(KPI·표): `font-variant-numeric: tabular-nums`, 오른쪽 정렬.
- 크기: 12 캡션 · 14 본문·표 · 16 강조 · 20 섹션 제목 · 28 KPI 값.
- 간격: 4의 배수(카드 안 16~24px, 카드 사이 16px). 모서리: 카드 8px, 버튼·입력 6px. 그림자 대신 line 테두리를 쓴다.
- 포커스: `outline: 2px solid` brand, `outline-offset: 2px`. 포커스 표시를 제거하지 않는다.
- 다크 모드는 요구될 때만 추가한다.

## 차트

- 범주 계열 순서: brand `#EA002C` → slate `#475569` → accent `#F47725` → teal `#0E7490` → 기타 `#8B95A1`. 비교 기준(목표·이전 기간)은 slate나 점선으로 둔다.
- accent(2.80)는 흰 배경에서 그래픽 대비 3:1에 못 미친다. 선이나 작은 점에 쓰면 값 라벨이나 범례를 함께 둔다.
- 순차(밀도·불량 건수 등 클수록 주목할 값): `#FDECEF` → `#F7A8B6` → `#EF5A75` → `#EA002C` → `#8F001B`. 밝은 두 단계는 흰 배경과 구분이 약하므로 셀 테두리나 값 라벨을 붙인다.
- 클수록 좋은 값(수율·통과율)을 레드 순차로 칠하지 않는다. 양호/불량 구분은 success/danger 상태 토큰을 쓴다.

## 적용 예

Tailwind v4 진입 CSS(`src/index.css` 등). 이 토큰에서 `bg-brand`, `text-ink`, `border-line` 같은 클래스가 생긴다.

```css
@import "tailwindcss";

@theme {
  --color-brand: #EA002C;
  --color-brand-strong: #C70025;
  --color-brand-soft: #FDECEF;
  --color-accent: #F47725;
  --color-ink: #191F28;
  --color-muted: #5B6370;
  --color-line: #E1E4EA;
  --color-canvas: #F5F6F8;
  --color-surface: #FFFFFF;
  --color-success: #1A7F37;
  --color-warning: #B54708;
  --color-danger: #B42318;
  --font-sans: "Pretendard", system-ui, -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", "Noto Sans KR", sans-serif;
}
```

Tailwind를 쓰지 않으면 같은 이름으로 `:root { --color-brand: #EA002C; … }`를 정의하고 `var(--color-brand)`로 참조한다. 차트 라이브러리처럼 JS 값이 필요하면 계열 배열 하나를 한 모듈(예: `lib/chartColors.ts`)에 두고 재사용한다.
