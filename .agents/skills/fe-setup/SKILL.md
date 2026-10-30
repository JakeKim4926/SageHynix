---
name: fe-setup
description: React/TypeScript(Vite) FE 앱을 처음 만들거나, Node·npm 설치·의존성·개발 서버·포트·API 프록시·웹 IDE 미리보기 문제를 해결할 때 사용한다. 기존 앱을 확인하고 필요한 설치와 실행 검증을 수행한다. 화면 기능 구현·수정은 fe-build, 색·화면 골격은 fe-design을 사용한다. Streamlit 앱에는 쓰지 않는다.
---

# FE Setup

목표: 실제 과제 환경에서 실행 가능한 FE와 재현 명령을 확보한다.

1. 과제 안내와 기존 앱의 package.json·lockfile·실행 명령을 확인한다. 앱 루트와 패키지 매니저를 확정한다. 기존 앱은 유지하고, 신규 커스텀 UI에만 TypeScript(strict)·React·Vite·Tailwind를 기본 후보로 쓴다. 과제가 Streamlit으로 정해지면 FE Skill(fe-setup·fe-build·fe-design)은 쓰지 않는다.
2. 최초 준비·설치 실패에는 [environment.md](references/environment.md)를 읽고 실행 환경 확인 → 필요한 설치 → 재검증을 수행한다. 사전 코드 자산의 반입 허용을 가정하지 않는다. 이 스킬에는 앱 템플릿이 없으며 예시는 작업 지침이다.
3. 서버·포트·API·IDE 연결에는 [preview.md](references/preview.md)를 읽는다. 신규 앱의 기본 미리보기는 0.0.0.0:3000이다. 실제 과제 설정이 우선한다.
4. 앱에 타입 검사·린트·빌드 명령을 마련하고 [FE 검증 계약](../verify/references/frontend.md)에 연결한다. 기존 명령 이름은 유지하고 대응 관계를 기록한다. 타입 검사 script가 없으면 `"typecheck": "tsc -b"`를 더한다. 테스트 도구가 없으면 `vitest @testing-library/react @testing-library/user-event jsdom`을 dev 의존성으로 설치하고 `"test": "vitest run --dir src"`를 둔다([test-strategy.md](../verify/references/test-strategy.md) 3절). 린트는 경고도 실패로 끝나게 한다(oxlint `--deny-warnings`, ESLint `--max-warnings 0`): 훅 의존성 누락·effect 안 setState가 경고 등급이라 그대로는 종료 코드 0으로 지나간다. 신규 앱은 생성 직후 [구조 규칙](../fe-build/references/structure.md)의 flat 구조로 맞추고(템플릿의 `export default App`은 named export로, 데모 코드·로고는 제거) 구조 검사 PASS를 확인한다.
5. 실제 화면까지 확인하고 앱 경로·버전·설치/실행/검증 명령·API 경로·구조(구조 검사 첫 줄의 `구조=` 값 또는 "기존 앱 규칙")·미검증을 docs/LOG.md 현재 상태에 짧게 기록한다. 이미 확인된 환경에서 일반 UI 수정만 할 때는 설정을 반복하지 않는다. 신규 앱이면 다음은 fe-design 1단계(토큰 정의)다.

준비 완료는 설치 성공뿐 아니라 서버 응답과 실제 미리보기까지 확인한 경우다. 브라우저를 사용할 수 없으면 서버까지만 검증했다고 보고한다. 이미 승인된 구현에 재승인을 요구하거나 제출·퀴즈를 별도로 호출하지 않는다.
