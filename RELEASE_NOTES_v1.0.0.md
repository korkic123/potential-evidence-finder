# Potential Evidence Finder v1.0.0

First GitHub-ready 1.0 release of the research prototype for identifying potential digital evidence sources from relationship artifacts collected across multiple target systems.

## Release assets

- **FieldCollector_Windows_x64_v1.0.0.zip** — portable `onedir` bundle for field USB media. No Python installation is required on the target PC.
- **CaseManager_Windows_x64_v1.0.0.exe** — investigator workstation application for importing and correlating `.pefpack` results.
- **SHA256SUMS.txt** — SHA-256 hashes for the release binaries.
- GitHub automatically provides the source-code archives for the `v1.0.0` tag.

## v1.0 highlights

- GUI-based Field Collector and Case Manager are fully separated and independently deployable.
- Default collection mode is **Parsed Results Only**.
- Optional source-artifact/snapshot preservation is available per artifact category.
- PEFPACK schema version 2 records provenance and internal SHA-256 values.
- Case-level entity resolution merges observations referring to the same potential evidence source.
- **Existence Confidence** and **Acquisition Priority** are shown separately.
- Candidate states: `POTENTIAL`, `LOCATED`, `ACQUIRED`, `EXCLUDED`.
- Windows release build is automated with PyInstaller and GitHub Actions.

## Field artifacts currently analyzed

- USBSTOR
- MountedDevices
- mapped network resources / MountPoints2
- WPD-related portable-device traces
- Bluetooth known-device traces
- SetupAPI device traces

## Research status

This is a research prototype. Automated scores are decision-support values and do not replace examiner judgment. Live execution can alter system state; the tool records provenance and runtime metadata to support reproducibility and review.
