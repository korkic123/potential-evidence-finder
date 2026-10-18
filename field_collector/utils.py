from __future__ import annotations
import getpass,hashlib,json,platform,socket,sys
from datetime import datetime,timezone
from pathlib import Path
from typing import Any

def utc_now_iso():return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def host_info():return {"hostname":socket.gethostname(),"username":getpass.getuser(),"platform":platform.platform(),"python":platform.python_version()}
def runtime_info():
    frozen=bool(getattr(sys,"frozen",False)); executable=Path(sys.executable).resolve(); info={"mode":"frozen" if frozen else "source","python_executable":str(executable),"python_version":platform.python_version()}
    if frozen and executable.is_file():
        try:info["collector_executable_sha256"]=sha256_file(executable)
        except OSError as exc:info["collector_executable_hash_error"]=str(exc)
    return info
def sha256_file(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def write_json(path:Path,data:Any):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
def safe_name(text:str):
    allowed="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.";cleaned="".join(ch if ch in allowed else "_" for ch in text.strip());return cleaned or "UNNAMED"
