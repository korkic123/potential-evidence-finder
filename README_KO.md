# Potential Evidence Finder v1.0

현장 선별수집 과정에서 여러 수집 대상에 남아 있는 외부·원격 장치 관계 흔적을 통합하여 **잠재적 디지털 증거원(Potential Evidence Source)**을 식별하기 위한 연구용 프로토타입입니다.

## 사용자에게는 Python이 필요하지 않습니다

GitHub **Releases**에는 다음 두 파일을 배포하도록 구성되어 있습니다.

```text
FieldCollector_Windows_x64_v1.0.0.zip   ← 현장 USB용
CaseManager_Windows_x64_v1.0.0.exe      ← 조사관 랩탑용
SHA256SUMS.txt
```

### 현장 USB

`FieldCollector_Windows_x64_v1.0.0.zip`을 USB에 풀어 **폴더 전체**를 복사합니다.

```text
USB_ROOT/
└─ FieldCollector/
   ├─ FieldCollector.exe
   ├─ _internal/
   └─ results/
```

대상 PC에서 `FieldCollector.exe`를 실행합니다. Python, pip, requirements 설치가 필요하지 않습니다.

Field Collector는 PyInstaller **onedir** 방식으로 빌드합니다. 단일 onefile EXE가 실행 시 대상 PC의 임시 디렉터리에 번들 파일을 풀어 쓰는 동작을 피하기 위한 선택입니다.

기본 결과 위치는 실행파일 옆의 `results/`이며 GUI에서 변경할 수 있습니다.

### 조사관 랩탑

`CaseManager_Windows_x64_v1.0.0.exe` 하나를 실행합니다. 역시 Python 설치가 필요하지 않습니다.

여러 USB에서 생성된 `.pefpack`을 순차적으로 Import하여 Case-level correlation을 수행합니다.

## 기본 Field Collector 동작

기본값은 **Parsed Results Only**입니다.

- 관계 아티팩트를 직접 조회·분석
- 잠재 증거원 식별에 필요한 결과와 provenance만 저장
- 원본/근거 아티팩트는 기본적으로 저장하지 않음
- 필요한 경우 GUI에서 항목별 `Preserve source artifact / snapshot` 선택

현재 분석 대상:

- USB storage — `USBSTOR`
- Mounted volumes — `MountedDevices`
- Network resources — mapped drives / `MountPoints2`
- Portable devices — WPD 관련 흔적
- Bluetooth known devices
- SetupAPI device traces

원본 보존 선택 시 SetupAPI 로그는 파일 복사, Registry 계열은 `.reg` export snapshot 방식입니다. 이는 전체 Registry hive의 바이너리 이미징과는 구분됩니다.

## Case Manager

Case Manager는 다음을 수행합니다.

1. 서로 다른 Source에서 생성된 observation 통합
2. 동일 Potential Evidence Source entity resolution
3. 독립 Source 수와 Artifact 종류 집계
4. **Existence Confidence** 산정
5. **Acquisition Priority** 산정
6. `POTENTIAL / LOCATED / ACQUIRED / EXCLUDED` 상태 관리

현재 점수는 연구용 초기 모델이며 조사관의 판단을 대체하지 않습니다.

## PEFPACK

Field Collector와 Case Manager는 실행 코드를 공유하지 않는 독립 프로그램이며 다음 교환 규격으로 연결됩니다.

```json
{
  "package_format": "PEFPACK",
  "schema_version": 2
}
```

패키지에는 내부 파일의 SHA-256이 기록됩니다. Field Collector가 frozen EXE로 실행된 경우 해당 `FieldCollector.exe` 자체의 SHA-256도 runtime metadata에 기록합니다.

## Source code

저장소의 두 폴더는 소스 검증·연구 재현·개발을 위한 것입니다.

```text
field_collector/
case_manager/
build/
.github/workflows/
```

소스 자체는 제3자 런타임 패키지를 요구하지 않으며 Python 3.10+와 Tkinter를 사용합니다. `PyInstaller`는 **EXE를 만드는 개발자에게만 필요한 build-time dependency**이며 `build/requirements-build.txt`에 별도로 분리했습니다.

소스에서 직접 실행할 때만:

```powershell
cd field_collector
python run_collector.py
```

```powershell
cd case_manager
python run_case_manager.py
```

## Windows Release 빌드

Windows에서:

```powershell
powershell -ExecutionPolicy Bypass -File .\build\build_windows.ps1
```

또는 GitHub에 push한 뒤 **Actions → Build Windows Release → Run workflow**를 실행합니다. `v*` 태그를 push하면 Windows runner가 Release assets를 빌드하고 해당 GitHub Release에 자동 첨부하도록 workflow가 구성되어 있습니다.

현재 build 설정은 PyInstaller 6.22.3을 사용합니다.

## 연구/운영 주의사항

- Live system에서 도구를 실행하는 행위 자체가 시스템 상태에 영향을 줄 수 있습니다.
- Registry last-write time을 특정 장치의 정확한 연결시각으로 단정하지 않습니다.
- 자동 점수는 잠재적 추가 수집 대상을 빠르게 파악하기 위한 보조값입니다.
- 현재 생성되는 EXE는 기본적으로 코드 서명되지 않습니다. 실제 운영 배포 시 코드 서명과 Release hash 검증을 권장합니다.
- 본 프로젝트는 Apache License 2.0으로 공개됩니다.

## GitHub 첫 공개 권장 순서

1. 새 저장소 이름을 `potential-evidence-finder`로 생성합니다.
2. 이 ZIP의 `potential-evidence-finder/` **내부 내용 전체**를 저장소 루트에 업로드합니다.
3. 기본 브랜치에 push한 뒤 `v1.0.0` 태그를 생성해 push합니다.
4. `.github/workflows/build-windows.yml`이 Windows runner에서 Release assets를 자동 빌드합니다.
5. Release에 생성된 `FieldCollector_Windows_x64_v1.0.0.zip`, `CaseManager_Windows_x64_v1.0.0.exe`, `SHA256SUMS.txt`를 확인합니다.

예시:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

> 본 프로젝트는 Apache License 2.0으로 공개됩니다. 자세한 조건은 저장소의 `LICENSE` 파일을 확인하세요.
