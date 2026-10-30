---
name: fe-build
description: React/TypeScript(Vite) 앱의 대시보드·페이지·컴포넌트 기능을 구현하거나 수정할 때 사용한다. 입력·필터·검색·조회·표·차트 데이터 표시·버튼 동작을 붙이거나 고칠 때("화면에 ~ 보여줘", "필터·차트 추가해줘"). 타입과 데이터 계약, 화면 상태를 지키며 요구사항 하나를 데이터부터 화면까지 연결한다. 앱 생성·설치·서버·미리보기는 fe-setup, 색·글꼴·화면 골격·차트 색은 fe-design을 사용한다. Streamlit 화면에는 쓰지 않는다.
---

# FE Build

목표: 실제 데이터로 동작하고 사용자가 해석할 수 있는 기능을 구현한다.

1. 이번 요구사항·수용 기준, 앱 경로, 기존 컴포넌트·scripts를 읽는다. 기존 계획과 승인을 재사용한다. 앱이나 실행 명령이 아직 없으면 fe-setup을 먼저 하고, 실행 환경이 바뀌거나 막힐 때도 fe-setup으로 돌아간다. 새 화면인데 디자인 토큰이 없으면 fe-design 1~2단계를 먼저 적용한다.
2. 코드 작성 전에 [coding-rules.md](references/coding-rules.md)를 읽는다. 같은 작업에서 이미 읽고 변경되지 않았다면 재독하지 않는다. 기존 프로젝트 규칙을 우선한다. 신규 앱의 첫 컴포넌트를 만들 때, 컴포넌트를 나누거나 상태 위치를 정할 때는 [code-design.md](references/code-design.md) 예시를 본다.
3. 비동기 조회·입력 화면이면 [ui-states.md](references/ui-states.md), API·수치·차트를 다루면 [data-contract.md](references/data-contract.md)를 구현 전에 읽는다. 차트 계열 색은 fe-design의 [sk-tokens.md 차트 절](../fe-design/references/sk-tokens.md)을 따른다.
4. 실제 입력 → 계산/API → 화면의 가장 작은 동작 단위로 구현한다. 새 라이브러리·범용 엔진·추상화는 현재 요구사항에 필요할 때만 추가한다. 임시 데이터는 표시하고 실제 데이터 연결 여부를 구분한다.
5. 변경한 동작을 확인하고 완료 판정은 [verify](../verify/SKILL.md) 절차를 따른다. FE 검사는 그 안에서 [frontend.md](../verify/references/frontend.md)로 합친다. 타입·빌드·화면 검증의 결과를 구분한다. 별도 검증 Skill이나 중복 기록을 만들지 않는다.

FE 변경 요약은 사용자 동작의 변화·검증 결과·남은 한계로 보고한다. 커밋·인지 점검은 상위 작업 흐름에서 한 번만 수행하며 하네스 유지보수에는 제출·퀴즈 루프를 적용하지 않는다.
