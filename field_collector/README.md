# Field Collector

Field-side GUI for extracting and parsing relationship artifacts and producing `.pefpack` results.

## Recommended operational use

Use the prebuilt GitHub Release asset `FieldCollector_Windows_x64_vX.Y.Z.zip`. Extract the whole folder to the collection USB and run `FieldCollector.exe`. No Python installation is required on the target PC.

The release folder contains the executable, its `_internal` runtime files, and a `results/` directory. Keep the entire folder together.

Default mode is **Parsed Results Only**. Source preservation is opt-in per artifact group.

## Source-mode development

Python 3.10+ with Tkinter:

```powershell
python run_collector.py
```

No third-party runtime packages are required.
