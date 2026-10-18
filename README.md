# Potential Evidence Finder v1.0

Research prototype for identifying potential digital evidence sources by correlating relationship artifacts across multiple collected systems.

## Release model

End users do **not** install Python or requirements.

GitHub Releases are designed to contain:

- `FieldCollector_Windows_x64_vX.Y.Z.zip` — portable onedir bundle for field USB media.
- `CaseManager_Windows_x64_vX.Y.Z.exe` — single executable for the investigator workstation.
- `SHA256SUMS.txt` — release asset hashes.

Field Collector intentionally uses PyInstaller `onedir` instead of `onefile` to avoid the one-file bundle's run-time extraction of embedded support files to a temporary directory on the target system. Case Manager runs on the investigator workstation and is packaged as `onefile` for convenience.

The source tree has no third-party runtime dependency. PyInstaller is a **build-only** dependency and is isolated under `build/requirements-build.txt`.

See `README_KO.md` for the detailed workflow and `build/BUILDING.md` for Windows build instructions.


## License

Licensed under the Apache License 2.0. See `LICENSE`.
