# Building Windows release assets

End users do **not** need Python or pip. These instructions are only for maintainers building release binaries.

## Local Windows build

Requirements:

- Windows 10/11 x64
- Python 3.13 x64 (3.10+ is supported by the source, but the automated release build uses 3.13)
- PowerShell

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\build\build_windows.ps1
```

The script installs the build-only dependency from `build/requirements-build.txt`, builds both applications, and creates:

```text
release/
├─ FieldCollector_Windows_x64_vX.Y.Z.zip
├─ CaseManager_Windows_x64_vX.Y.Z.exe
└─ SHA256SUMS.txt
```

### Why Field Collector is `onedir`

The field component is deliberately packaged as a portable folder rather than PyInstaller `onefile`. A one-file bundle extracts its embedded files to a temporary directory at run time. For a live-system forensic utility, avoiding that additional extraction activity on the target is preferable.

### Why Case Manager is `onefile`

Case Manager runs on the investigator workstation, not the target system. A single executable is therefore more convenient and the temporary extraction behavior is less relevant to evidentiary impact.

### UPX

UPX is disabled in both specifications. This keeps the build simpler and avoids unnecessary executable packing for a forensic research tool.

### Code signing

The generated binaries are unsigned. Windows SmartScreen or endpoint-security products may warn about unsigned research binaries. For operational deployment, sign release binaries with an appropriate code-signing certificate and publish hashes with the release.
