# 해커톤 환경 준비

대상은 Bash 4+, Git, Python 3.9+를 실행할 수 있는 Linux 웹 IDE다. Windows에서는 Git Bash로 사전 점검할 수 있지만 실제 플랫폼 검증을 대신하지 않는다. 하네스의 ctx와 훅은 Python 표준 라이브러리만 사용한다.

## 1. 과제와 제출 폴더 확인

주최 측이 정한 작업 폴더·README·제출 대상을 먼저 확인한다. 이 저장소 README는 하네스 설명이며 과제 지시서가 아니다. 별도의 과제 지시서 위치를 docs/INTENT.md에 기록한다.

clone한 폴더가 작업·제출 대상이면 그 안에서:

```bash
bash setup.sh
```

주최 측 과제 폴더가 이미 있다면 하네스 저장소에서:

```bash
bash bootstrap.sh /실제/과제/폴더
cd /실제/과제/폴더
```

bootstrap은 기존 파일과 과제 README를 덮어쓰지 않는다. 내용이 다른 기존 파일은 충돌 목록으로 출력하고 실패 상태로 종료한다. 기존 AGENTS.md는 보존하고 AGENTS.harness.md를 추가하므로 직접 검토해 합친다. 프로젝트 설정·훅 충돌도 검토 후 반영한다. 자동 커밋은 하지 않는다. 설치된 하네스를 검토·커밋해야 새 worktree에 전달된다.

## 2. 설치 여부 판별

```bash
bash .harness/bin/doctor.sh
bash .harness/bin/doctor.sh --profile verify data
```

기본 점검: 실제 도구 실행 성공, Python/Bash 버전, 저장소 루트, 스킬 16개, 에이전트 정의 6개, 훅 JSON·정책 입력 테스트, ctx 초기화 및 병합 설정. `package.json`이 있는 경우에만 Node/npm도 요구한다. 점검은 패키지를 설치하거나 ctx를 갱신하지 않는다.

- `OK`: 해당 자동 검사 통과.
- `FAIL`: 필수 항목 또는 명시적으로 선택한 기능을 사용할 수 없음. 종료 코드 1.
- 선택하지 않은 기능: 미설치여도 기본 시작을 막지 않음.
- 수동 확인: Codex 내 실제 훅 실행·신뢰·모델·에이전트 노출·제출 위치. 자동 통과와 별개다.

## 3. 필요한 기능만 설치

먼저 import를 검사하고, 없는 기능만 선택한다. 이미 동작하는 항목은 설치하지 않는다.

| 기능 | 명령의 기능명 | 패키지 |
|---|---|---|
| Python 검증 | verify | pytest, ruff |
| 표 데이터 분석 | data | pandas, numpy |
| Excel | excel | pandas, openpyxl, xlrd |
| Parquet | parquet | pandas, pyarrow |
| API 서버 | api | fastapi, uvicorn |
| 대시보드 | dashboard | streamlit |
| 차트 | plot | matplotlib |
| 머신러닝 | ml | scikit-learn (import 이름 sklearn) |

```bash
bash setup.sh --install verify data
# 실제 파일이 Excel일 때만
bash setup.sh --install excel
```

패키지가 부족하면 프로젝트 `.venv`를 만들고 그 Python의 `-m pip`로 설치한다. 새 환경은 `--system-site-packages`로 플랫폼의 기존 패키지를 읽어 재사용하며, 추가 설치는 `.venv`에 한다. 기존 `.venv`는 재생성하지 않는다. import 실패는 미설치뿐 아니라 버전 충돌일 수도 있다. 설치 후에도 실패하면 멈추고 원인을 출력한다. 기존 패키지 전체를 업그레이드하지 않는다.

직접 설치한 선택 패키지 목록은 `.harness/requirements.local.txt`에 기록한다. 이것은 과제의 완전한 의존성 잠금 파일이 아니다. 실제 제출 코드가 사용하는 패키지·버전은 과제 requirements에 별도로 기록한다. 가상환경과 로그는 Git에서 제외한다.

설치 후 같은 인터프리터로 선택 기능을 재검사한다. 하네스 스크립트는 프로젝트 `.venv`를 우선 사용한다. 수동 Python 작업에도 같은 환경을 쓰려면 Linux에서 `source .venv/bin/activate`한다.

## 4. 누락·실패별 복구

| 상황 | 확인 및 조치 |
|---|---|
| Python 명령만 있고 실행 실패 | `python3 --version`과 `python --version`을 직접 실행. 실행 가능한 3.9+가 필요하다. Windows Store 별칭은 설치로 간주하지 않는다. |
| Bash/Git/Python 자체 없음 | 플랫폼 안내의 터미널·환경을 먼저 확인. OS 패키지 설치가 허용된 Debian/Ubuntu 환경에서만 아래 예시 사용. 권한이 없으면 운영자에게 복구 요청. |
| venv 생성 불가 | `python3 -m venv .venv`의 오류 확인. Debian/Ubuntu라면 python3-venv가 별도 패키지일 수 있다. 실패한 환경을 자동 삭제하지 않는다. |
| venv의 pip 없음 | Linux: `.venv/bin/python3 -m ensurepip --default-pip` 후 `.venv/bin/python3 -m pip --version`. ensurepip도 없으면 Python 배포 환경을 복구한다. |
| 설치 네트워크 오류 | 플랫폼의 허용 패키지 인덱스·네트워크 설정을 확인하고 같은 setup 명령을 재실행. 인증정보를 출력하거나 설정을 임의 교체하지 않는다. |
| import 오류·버전 충돌 | `.venv/bin/python3 -m pip check`와 실패 모듈 직접 import로 오류 확인. 과제 버전 제약에 맞춰 해당 패키지만 조정한다. |
| Codex 없음/실행 실패 | 플랫폼 지정 터미널·PATH·실행 방법을 확인하고 운영자 안내에 따른다. 플랫폼 Codex를 임의 설치·업그레이드하거나 개인 인증으로 대체하지 않는다. |
| Node/npm 없음 | package.json이 있는 과제만 필요. 플랫폼이 제공하는 런타임 또는 과제 지정 버전을 사용한다. |
| 스킬/하네스 파일 누락 | 지정 작업 폴더에 bootstrap을 재실행하거나 누락 파일을 복구한다. 기존 충돌 파일은 수동 검토한다. |

OS 설치가 허용되고 sudo 권한이 있는 Debian/Ubuntu에 한한 예시다. 다른 환경에서 그대로 실행하지 않는다.

```bash
sudo apt-get update
# 아래 중 실제 누락된 항목만 설치
sudo apt-get install bash git python3 python3-venv python3-pip
```

Python 가상환경·pip 근거: https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/

## 5. Codex 시작과 수동 확인

```bash
bash .harness/bin/start.sh
```

이 실행기는 작업 폴더로 이동하고 프로젝트 `.venv` 경로를 상속해 Codex를 시작한다. 플랫폼의 모델·인증·승인 정책 설정은 변경하지 않는다.

1. 프로젝트 신뢰와 `/hooks`의 훅 신뢰를 확인한다. 명령이 없는 버전이면 플랫폼 도움말에서 지원 여부를 확인한다.
2. `/status`로 모델을 확인하고 과제에서 허용한 모델을 선택한다.
3. `/skills`에서 16개 스킬을 확인한다. 첫 요청에서 ctx 안내가 실제로 주입되는지 확인한다.
4. 서브에이전트 노출을 별도로 확인한다. 불가능하면 순차 작업 또는 fanout 대안을 선택한다.
5. 웹 과제라면 실제 포트로 Browser 미리보기 연결을 확인한다.

공유 상태 저장소는 메인 프로젝트 `.harness/state/`다. `HYNIX_HARNESS_HOME`으로 위치를 지정할 수 있으며, ctx와 로그는 각 레인의 폴더를 쓴다.

## 6. 하네스 자체 검증

```bash
bash .harness/tests/run_all.sh
```

하네스 테스트는 `.harness/tests/`, 과제 테스트는 `tests/`에 둔다. 실제 플랫폼의 Codex 신뢰·훅 동작은 이 테스트로 보증되지 않는다.

## FE 환경 확인

`package.json`이 루트 또는 `frontend/`에 있으면 자동 점검은 Node/npm의 실제 실행도 확인한다. 다른 앱 경로와 pnpm/yarn은 `$fe-setup`에서 프로젝트에 맞게 직접 확인한다. 이 점검만으로 패키지 버전 호환성·브라우저 실행·미리보기 연결까지 검증되는 것은 아니다.

`$fe-setup`에서 lockfile과 런타임을 확인한 뒤 필요한 의존성만 설치한다. 신규 앱의 3000 포트 바인딩과 실제 IDE 미리보기를 확인하고 실행 명령을 기록한다. 앱 검증 명령은 `.harness/verify.local.sh`에 연결하거나 직접 실행해 `docs/VERIFICATION.md`에 남긴다. FE 문서만 변경한 경우 실제 앱 검증을 통과했다고 보고하지 않는다.
