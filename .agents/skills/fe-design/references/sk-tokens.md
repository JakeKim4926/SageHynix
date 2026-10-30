# SK하이닉스 디자인 토큰

출처: brand·accent·navy·teal·blue는 [SK하이닉스 CI 페이지](https://www.skhynix.com/company/UI-FR-CP0402/)의 공식 HEX 값이다(SK 그룹 CI를 그대로 쓴다). 같은 페이지에서 SK Orange의 RGB(255/122/0 = `#FF7A00`)는 HEX `#F47725`와 다르며, 이 하네스는 HEX를 쓴다. 중립색은 skhynix.com CSS에서 가장 많이 쓰인 값이다. brand-strong·brand-soft·순차 색은 brand에서 파생한 값이고, 상태 색은 SK CI에 없어 이 하네스의 기본값을 쓴다. 주최 측 가이드가 있으면 그 값으로 바꾼다.

## 색

| 토큰 | 값 | 용도 | 흰 배경 대비 |
|---|---|---|---|
| brand | `#EA002C` | 주요 버튼, 활성 탭, 상단 강조선 (SK Red) | 4.63 (흰 글자 가능) |
| brand-strong | `#C70025` | brand hover, brand-soft 위 글자 | 6.08 |
| brand-soft | `#FDECEF` | 선택 행·활성 칩 배경 | — |
| accent | `#F47725` | 차트 보조 계열, 아이콘, 장식 (SK Orange) | 2.80 (글자 금지, 위 글자는 ink) |
| navy | `#0E306D` | 차트 계열, 비교 기준선 (SK Navy) | 12.63 |
| teal | `#009A93` | 차트 계열 (SK Teal) | 3.47 (글자 금지) |
| blue | `#0072C6` | 차트 계열 (SK Blue) | 4.97 |
| ink | `#212121` | 본문·제목 | 16.10 |
| muted | `#666666` | 보조 글자, 축 라벨 | 5.74 |
| line | `#E5E5E5` | 카드 테두리, 구분선 | — |
| canvas | `#F5F5F5` | 페이지 배경 | — |
| surface | `#FFFFFF` | 카드·상단 바 | — |
| success | `#1A7F37` | 양호·통과 | 5.08 |
| warning | `#B54708` | 주의 | 5.43 |
| danger | `#B42318` | 오류·불량·실패 | 6.57 |

brand-soft 위 글자는 brand가 아닌 brand-strong을 쓴다(brand는 4.06으로 미달). SK 보조 색 중 Yellow `#FBBC05`·Green `#B3CF0A`는 흰 배경 대비 1.7 수준이라 쓰지 않는다.

## 글꼴·간격·모양

- 글꼴: `"Noto Sans KR", Roboto, system-ui, -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif`(skhynix.com 글꼴 우선). 설치하지 않고 있는 글꼴을 쓴다.
- 숫자(KPI·표): `font-variant-numeric: tabular-nums`, 오른쪽 정렬.
- 크기: 12 캡션 · 14 본문·표 · 16 강조 · 20 섹션 제목 · 28 KPI 값.
- 간격: 4의 배수(카드 안 16~24px, 카드 사이 16px). 모서리: 카드 8px, 버튼·입력 6px. 그림자 대신 line 테두리를 쓴다.
- 포커스: `outline: 2px solid` brand, `outline-offset: 2px`. 포커스 표시를 제거하지 않는다.
- 다크 모드는 요구될 때만 추가한다.

## 차트

- 범주 계열 순서: brand `#EA002C` → navy `#0E306D` → teal `#009A93` → accent `#F47725` → blue `#0072C6` → 기타 `#888888`. 레드와 오렌지는 색각 이상에서 비슷해 보이므로 떨어뜨려 둔다. 비교 기준(목표·이전 기간)은 navy나 점선으로 둔다.
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
  --color-navy: #0E306D;
  --color-teal: #009A93;
  --color-blue: #0072C6;
  --color-ink: #212121;
  --color-muted: #666666;
  --color-line: #E5E5E5;
  --color-canvas: #F5F5F5;
  --color-surface: #FFFFFF;
  --color-success: #1A7F37;
  --color-warning: #B54708;
  --color-danger: #B42318;
  --font-sans: "Noto Sans KR", Roboto, system-ui, -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
}
```

Tailwind를 쓰지 않으면 같은 이름으로 `:root { --color-brand: #EA002C; … }`를 정의하고 `var(--color-brand)`로 참조한다. 차트 라이브러리처럼 JS 값이 필요하면 계열 배열 하나를 한 모듈(예: `lib/chartColors.ts`)에 두고 재사용한다.
