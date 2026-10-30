# SK하이닉스 디자인 토큰

출처: brand·accent·navy·teal·action은 [SK하이닉스 CI 페이지](https://www.skhynix.com/company/UI-FR-CP0402/)의 공식 HEX 값이다(SK 그룹 CI를 그대로 쓴다). 같은 페이지에서 SK Orange의 RGB(255/122/0 = `#FF7A00`)는 HEX `#F47725`와 다르며, 이 하네스는 HEX를 쓴다. 중립색과 역할 배치는 skhynix.com CSS를 따른다: 레드는 로고 주변에만 두고, 상호작용(강조 버튼·링크·선택)은 한 가지 파란 계열(사이트는 `#4747B3`, 여기서는 CI의 SK Blue)로 한다. 단, 화면 틀의 강조색을 하나로 줄이려고 활성 탭은 사이트의 오렌지 막대 대신 ink 막대로 한다. `-strong`·`-soft`·순차·발산 색은 토큰에서 계산한 파생값이고, 상태 색은 SK CI에 없어 이 하네스의 기본값을 쓴다. 주최 측 가이드가 있으면 그 값으로 바꾼다.

## 색

| 토큰 | 값 | 역할 | 흰 배경 대비 |
|---|---|---|---|
| brand | `#EA002C` | 서비스명 막대, 차트 하이라이트 1개, 순차·발산 끝 (SK Red) | 4.63 |
| action | `#0072C6` | 강조 버튼, 링크, 체크·라디오 선택, 포커스 (SK Blue) | 4.97 (흰 글자 가능) |
| action-strong | `#005B9E` | action hover·누름, action-soft 위 글자 | 7.02 |
| action-soft | `#EBF4FA` | 선택 행·활성 칩·정보 안내 배경 | — |
| accent | `#F47725` | 서비스명 막대, 차트 계열, 순차 중간, 아이콘 (SK Orange) | 2.80 (글자 금지, 위 글자는 ink) |
| navy | `#0E306D` | 차트 1번 계열·비교 기준선, 정보 안내 글자 (SK Navy) | 12.63 |
| teal | `#009A93` | 차트 계열 (SK Teal) | 3.47 (글자 금지) |
| ink | `#212121` | 본문·제목·표 링크, 활성 탭 막대, 툴팁 배경 | 16.10 |
| muted | `#666666` | 보조 글자, 축 라벨, 표 헤더 글자, 비활성 탭 | 5.74 |
| subtle | `#888888` | 입력 테두리, 안내 문구(placeholder), 차트 기타 계열 | 3.54 |
| dim | `#B7C1D3` | 차트에서 강조하지 않는 막대·계열 (navy 30%) | 1.81 (값 라벨 병기) |
| disabled | `#BDBDBD` | 비활성 글자·테두리 | 1.88 (비활성은 대비 예외) |
| line | `#E5E5E5` | 카드 테두리, 구분선, 보조 버튼 테두리, 차트 격자 | — |
| canvas | `#F5F5F5` | 페이지 배경, 표 헤더·행 hover, 비활성 배경 | — |
| surface | `#FFFFFF` | 카드·상단 바·보조 버튼 | — |
| success / success-soft | `#1A7F37` / `#EDF5EF` | 양호·통과 글자·아이콘 / 배지·배너 배경 | 5.08 (soft 위 4.57) |
| warning / warning-soft | `#B54708` / `#F9F0EB` | 주의 | 5.43 (soft 위 4.83) |
| danger / danger-soft | `#B42318` / `#F9EDED` | 오류·불량·실패 | 6.57 (soft 위 5.75) |

- brand는 버튼·탭·링크·포커스·오류에 쓰지 않는다. brand와 danger의 명도 대비는 1.42라 한 화면에서 "강조"와 "불량"이 구분되지 않는다.
- action-soft 위 글자는 action이 아닌 action-strong이나 navy를 쓴다(action은 4.47로 미달).
- SK 보조 색 중 Yellow `#FBBC05`·Green `#B3CF0A`·Purple `#68127A`는 쓰지 않는다(앞의 둘은 흰 배경 대비 1.7 수준).

## 컴포넌트별 색

표에 없는 컴포넌트는 가장 가까운 행을 따르고, 새 색을 만들지 않는다.

| 컴포넌트 | 기본 | hover·활성·선택 | 비활성·오류 |
|---|---|---|---|
| 상단 바 | surface 배경, 하단 1px line 선, ink 서비스명(굵게) 앞에 4×18px 세로 막대 `linear-gradient(accent, brand)`, 모서리 2px | — | — |
| 강조 버튼 (화면당 1종) | action 배경, 흰 글자 | action-strong 배경 | canvas 배경, disabled 글자 |
| 보조 버튼 | surface 배경, line 테두리, ink 글자 | canvas 배경 | disabled 글자·테두리 |
| 위험 동작 버튼 (삭제 등) | surface 배경, danger 테두리·글자 | danger-soft 배경 | disabled 글자·테두리 |
| 링크 (본문·안내) | action 글자, 밑줄 | action-strong | — |
| 링크 (표 안의 ID 등) | ink 글자, 밑줄 없음 | action 글자 + 밑줄 | — |
| 입력·선택 상자 | surface 배경, subtle 테두리, ink 글자, subtle 안내 문구 | 포커스 링 | 비활성: canvas 배경·disabled 글자 / 오류: danger 테두리 + 아래 danger 문구 |
| 체크박스·라디오 | subtle 테두리 | 선택: action 배경·테두리 | disabled 테두리 |
| 탭 | muted 글자 | 활성: ink 글자(굵게) + 하단 3px ink 막대 | — |
| 필터 칩 | surface 배경, line 테두리, muted 글자 | 선택: action-soft 배경, action 테두리, action-strong 글자 | — |
| 카드 | surface 배경, line 테두리, 모서리 8px | — | — |
| KPI 카드 | muted 라벨, ink 값 | — | — |
| KPI 증감 | 아래 규칙 참고 | — | — |
| 표 | 헤더 canvas 배경·muted 글자, 행 구분 line | 행 hover canvas, 선택 행 action-soft | — |
| 상태 배지·알림 배너 | 상태 `-soft` 배경 + 상태 글자 + 아이콘·문구 | — | — |
| 정보·로딩·갱신 중 안내 | action-soft 배경, navy 글자 | — | — |
| 빈 결과 안내 | canvas 배경, muted 글자 | — | — |
| 툴팁 | ink 배경, 흰 글자 | — | — |
| 모달 | surface 본문, ink 50% 배경막 | — | — |
| 포커스 링 (모든 조작 요소) | `outline: 2px solid` action, `outline-offset: 2px` | — | — |

KPI 증감은 값이 오르고 내린 방향이 아니라 좋고 나쁨으로 색을 정한다. 수율·통과율이 오르거나 불량률이 내리면 success, 그 반대면 danger를 쓴다. 증감 값 앞에는 ▲/▼와 부호를 붙이고, 좋고 나쁨을 판단할 수 없는 지표는 muted로 둔다.

## 글꼴·간격·모양

- 글꼴: `"Noto Sans KR", Roboto, system-ui, -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif`(skhynix.com 글꼴 우선). 설치하지 않고 있는 글꼴을 쓴다.
- 숫자(KPI·표): `font-variant-numeric: tabular-nums`, 오른쪽 정렬.
- 크기: 12 캡션 · 14 본문·표 · 16 강조 · 20 섹션 제목 · 28 KPI 값.
- 간격: 4의 배수(카드 안 16~24px, 카드 사이 16px). 모서리: 카드 8px, 버튼·입력 6px. 그림자 대신 line 테두리를 쓴다.
- 포커스 표시를 제거하지 않는다.
- 다크 모드는 요구될 때만 추가한다.

## 차트

- 범주 계열 순서: navy `#0E306D` → action `#0072C6` → teal `#009A93` → accent `#F47725` → 기타 subtle `#888888`. 차가운 색 3개 뒤에 따뜻한 색 1개를 두어 특정 계열이 이유 없이 튀지 않게 한다. 비교 기준(목표·이전 기간)은 navy 점선으로 둔다. 격자는 line, 축 라벨은 muted, 툴팁은 ink 배경이다.
- 강조할 항목 1개(선택한 제품·이상치·현재 기간)만 brand `#EA002C`로 칠하고, 나머지 막대·계열은 dim `#B7C1D3`으로 낮춘다. dim은 흰 배경 대비가 1.81이므로 값 라벨이나 축 눈금을 함께 둔다. 한 차트에 brand와 danger를 함께 쓰지 않는다.
- accent(2.80)는 흰 배경에서 그래픽 대비 3:1에 못 미친다. 선이나 작은 점에 쓰면 값 라벨이나 범례를 함께 둔다.
- 순차(밀도·불량 건수 등 클수록 주목할 값): `#FEF1E9` → `#F9B487` → accent `#F47725` → brand `#EA002C` → `#8F001B`. 행복날개의 오렌지→레드 흐름이다. 밝은 두 단계는 흰 배경과 구분이 약하므로 셀 테두리나 값 라벨을 붙인다.
- 발산(목표 대비 ±, 편차): navy `#0E306D` → `#93A2BD` → canvas `#F5F5F5` → `#F9B487` → brand `#EA002C`. 양 끝이 무엇을 뜻하는지 범례에 적는다.
- 클수록 좋은 값(수율·통과율)을 레드 순차로 칠하지 않는다. 양호/불량 구분은 success/danger 상태 토큰을 쓴다.

## 적용 예

Tailwind v4 진입 CSS(`src/index.css` 등). 이 토큰에서 `bg-action`, `text-ink`, `border-line` 같은 클래스가 생긴다.

```css
@import "tailwindcss";

@theme {
  --color-brand: #EA002C;
  --color-action: #0072C6;
  --color-action-strong: #005B9E;
  --color-action-soft: #EBF4FA;
  --color-accent: #F47725;
  --color-navy: #0E306D;
  --color-teal: #009A93;
  --color-ink: #212121;
  --color-muted: #666666;
  --color-subtle: #888888;
  --color-dim: #B7C1D3;
  --color-disabled: #BDBDBD;
  --color-line: #E5E5E5;
  --color-canvas: #F5F5F5;
  --color-surface: #FFFFFF;
  --color-success: #1A7F37;
  --color-success-soft: #EDF5EF;
  --color-warning: #B54708;
  --color-warning-soft: #F9F0EB;
  --color-danger: #B42318;
  --color-danger-soft: #F9EDED;
  --font-sans: "Noto Sans KR", Roboto, system-ui, -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
}
```

Tailwind를 쓰지 않으면 같은 이름으로 `:root { --color-action: #0072C6; … }`를 정의하고 `var(--color-action)`로 참조한다. 차트 라이브러리처럼 JS 값이 필요하면 계열 배열 하나를 한 모듈(예: `lib/chartColors.ts`)에 두고 재사용한다.
