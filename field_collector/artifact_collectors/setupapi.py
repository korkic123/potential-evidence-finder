from __future__ import annotations

import os
import re
from pathlib import Path

from models import Observation

USB_RE = re.compile(r"USBSTOR\\[^\s\]]+", re.IGNORECASE)
WPD_RE = re.compile(r"(?:WPDBUSENUM|WPD)\\[^\s\]]+", re.IGNORECASE)


def collect_setupapi(source_id: str) -> tuple[list[Observation], list[str]]:
    observations: list[Observation] = []
    errors: list[str] = []
    if os.name != "nt":
        return observations, ["SetupAPI collection is available only on Windows."]
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    log_path = windir / "inf" / "setupapi.dev.log"
    if not log_path.exists():
        return observations, [f"SetupAPI log not found: {log_path}"]
    try:
        text = log_path.read_text(encoding="utf-16", errors="replace")
        if "USBSTOR" not in text.upper() and "WPD" not in text.upper():
            text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return observations, [f"Cannot read SetupAPI log: {exc}"]
    seen:set[tuple[str,str]]=set()
    for line in text.splitlines():
        upper=line.upper()
        if "USBSTOR" not in upper and "WPDBUSENUM" not in upper and "WPD" not in upper: continue
        for match in USB_RE.findall(line):
            key=("USBSTOR",match.casefold())
            if key in seen: continue
            seen.add(key)
            observations.append(Observation(source_id,"external_storage","SetupAPI","installation_or_connection_trace",match,{"setupapi_device_path":match.casefold()},{"source_file":str(log_path),"source_record_excerpt":line.strip()[:1000]}))
        for match in WPD_RE.findall(line):
            key=("WPD",match.casefold())
            if key in seen: continue
            seen.add(key)
            observations.append(Observation(source_id,"portable_device","SetupAPI","installation_or_connection_trace",match,{"setupapi_wpd_path":match.casefold()},{"source_file":str(log_path),"source_record_excerpt":line.strip()[:1000]}))
    return observations, errors
