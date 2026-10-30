# VERIFICATION — 검증 기록

> `$verify`로 갱신. 실제 실행한 명령과 관찰 결과만 적는다. 실행 못 한 것은 '미검증'.

## 요구사항 추적
| 요구사항 | 구현 위치 | 검증 명령/방법 | 결과 | 시각 |
|---|---|---|---|---|

## 수치 결과 재현
| 지표 | 값 | 재현 명령 | 데이터/seed |
|---|---|---|---|

## 미검증 / 알려진 한계
-

## 하네스 유지보수 — FE Skill (2026-10-30)

| 대상 | 검증 명령/방법 | 결과 |
|---|---|---|
| fe-setup·fe-build·verify-gate | skill-creator/scripts/quick_validate.py를 각 폴더에 실행 | 3개 valid |
| 설치 점검·검증 확장·기존 하네스 | bash .harness/tests/run_all.sh | 39개 테스트 및 셸 구문 통과 |
| 참조 문서 연결 | Markdown 상대 링크 대상 존재 확인 | 8개 통과 |
| 변경 형식 | git diff --check | 통과 |

처음 전체 검사에서 이전 타이머 제거 후 출력 가정이 남은 ctx 테스트 2개가 실패했고 수정 후 재실행했다. 실제 모델의 스킬 선택, 예시 TS/TSX 앱 빌드, 웹 IDE 미리보기와 실제 API 연동은 미검증이다. 테스트는 임시 작업 공간에서 실행했으며 외부 모델 호출은 하지 않았다.

## 하네스 유지보수 — skill 16→6 축소 (2026-10-30)

| 대상 | 검증 명령/방법 | 결과 |
|---|---|---|
| 하네스 단위 테스트·셸 구문 | bash .harness/tests/run_all.sh | 23개 테스트 및 셸 구문 통과 (ctx 테스트 삭제) |
| 환경 점검 | bash .harness/bin/doctor.sh (Windows Git Bash, uv Python 3.12) | 실패 0개 |
| Markdown 상대 링크·skill 프런트매터 | 링크 대상 존재, `name`이 폴더명과 일치 | 깨진 링크 0개, 6개 일치 |

실제 Codex에서 skill 6개·서브에이전트 2개 노출, SCRIPT 형식 지시에 대한 서브에이전트 응답, Linux 웹 IDE 동작은 미검증이다.
