# Changelog

## v1.0.0

- First GitHub-ready 1.0 release.
- Promoted the separated Field Collector / Case Manager architecture to stable repository structure.
- Default Field Collector mode remains Parsed Results Only, with optional per-artifact source preservation.
- PEFPACK schema version 2 retained for interchange compatibility.
- Existence Confidence and Acquisition Priority remain separate decision-support outputs.
- Added v1.0.0 release notes and updated automated Windows release naming.

## v0.6.0

- Added release-oriented GitHub repository layout.
- Added PyInstaller Windows build specifications.
- Field Collector release is built as portable `onedir`; Case Manager as `onefile`.
- Added GitHub Actions Windows build and tagged-release publication workflow.
- Added automatic SHA-256 release manifest.
- Removed per-application `requirements.txt` files because runtime uses only the Python standard library/Tkinter.
- Isolated PyInstaller as a build-time-only dependency.
- Field Collector defaults output beside the frozen executable in `results/`.
- Frozen Field Collector records its own executable SHA-256 in PEFPACK runtime metadata.
- UPX disabled for release builds.

## v0.5.0

- Field Collector and Case Manager made fully standalone at source-folder level.
- Removed shared runtime `common/` directory.
- PEFPACK schema compatibility retained at version 2.
