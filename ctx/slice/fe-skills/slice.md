# slice/fe-skills — 슬라이스

- 목표: FE Skill 구현: fe-setup fe-build 코드 규칙 예시와 verify-gate 연결
- 관련 요구사항: -

## 한 일
- [사실] fe-setup·fe-build와 참조 문서 5개를 추가했다. 환경/미리보기, 코드 규칙·예시, 화면 상태, 데이터 계약을 분리했다.
- [사실] verify-gate/references/frontend.md와 진입점 연결, AGENTS 라우팅·스택 기본값, 스킬 15개 점검·안내를 반영했다.
- [사실] frontend/package.json도 Node/npm 실행 검사 대상에 포함했다. verify.local.sh는 실행 비트 없이 Bash로 호출하고 실패를 전파한다.
- [사실] 이전 타이머 제거 후 무출력 동작을 반영하지 못한 ctx 테스트 2개를 수정했다. 훅 코드는 이번 작업에서 변경하지 않았다.
- [사실] 사전 앱 스타터나 실제 FE 앱은 추가하지 않았다. 기존 대규모 구조 이동·삭제가 미커밋 상태여서 함께 스테이징하거나 커밋하지 않았다.

## 검증
- Python 3.12의 skill-creator/scripts/quick_validate.py를 fe-setup, fe-build, verify-gate에 실행 → 3개 모두 valid. PyYAML 6.0.3은 .harness/tmp/skill-validation에 임시 설치하고 해당 경로는 Git 제외.
- bash .harness/tests/run_all.sh → 39개 테스트 및 셸 구문 검사 통과. Windows 샌드박스의 임시 파일 제한 때문에 승인된 확장 권한으로 실행했다.
- Markdown 상대 링크 확인 → 8개 대상 존재. git diff --check → 통과.
- 최초 전체 테스트는 ctx 출력 가정 2건으로 실패했다. 무출력 기대값으로 수정한 뒤 전체 재실행이 통과했다.

## 남은 것
- 미검증: 실제 대상 모델의 Skill 선택·실행 성능, 웹 IDE의 3000 포트, 예시 TS/TSX의 앱 빌드, 실제 데이터/API 연동.
- 과제 앱 생성 시 FE 검증 명령과 verify.local.sh를 해당 패키지 매니저에 맞게 연결해야 한다.
- 반입 규정 원문 확인은 별도이며 이 검증이 규정 적합성을 증명하지 않는다.
