from __future__ import annotations

import getpass, hashlib, json, platform, socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def utc_now_iso() -> str: return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def host_info() -> dict[str, str]: return {"hostname":socket.gethostname(),"username":getpass.getuser(),"platform":platform.platform(),"python":platform.python_version()}
def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()
def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
def safe_name(text: str) -> str:
    allowed="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."; cleaned="".join(ch if ch in allowed else "_" for ch in text.strip()); return cleaned or "UNNAMED"
