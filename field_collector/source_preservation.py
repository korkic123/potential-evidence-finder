from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

REGISTRY_TARGETS={
    "usb":[("HKLM",r"SYSTEM\CurrentControlSet\Enum\USBSTOR","registry_usbstor.reg")],
    "mounted_devices":[("HKLM",r"SYSTEM\MountedDevices","registry_mounted_devices.reg")],
    "network":[("HKCU",r"Network","registry_mapped_network_drives.reg"),("HKCU",r"Software\Microsoft\Windows\CurrentVersion\Explorer\MountPoints2","registry_mountpoints2.reg")],
    "portable_devices":[("HKLM",r"SYSTEM\CurrentControlSet\Enum\SWD\WPDBUSENUM","registry_wpd_swd.reg"),("HKLM",r"SYSTEM\CurrentControlSet\Enum\WpdBusEnumRoot","registry_wpd_root.reg")],
    "bluetooth":[("HKLM",r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices","registry_bluetooth_devices.reg")],
}

def _run_reg_export(root,subkey,destination):
    if os.name!="nt": return False,"Registry export is available only on Windows."
    destination.parent.mkdir(parents=True,exist_ok=True); key=f"{root}\\{subkey}"; creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0)
    try:proc=subprocess.run(["reg.exe","export",key,str(destination),"/y"],capture_output=True,text=True,encoding="utf-8",errors="replace",creationflags=creationflags,timeout=30)
    except (OSError,subprocess.SubprocessError) as exc:return False,f"Registry snapshot failed for {key}: {exc}"
    if proc.returncode!=0:return False,f"Registry snapshot failed for {key}: {(proc.stderr or proc.stdout or 'unknown error').strip()}"
    return True,f"Saved registry export snapshot: {key}"

def preserve_registry_group(group,destination_root):
    records=[]
    for root,subkey,filename in REGISTRY_TARGETS.get(group,[]):
        target=destination_root/"registry"/filename; ok,message=_run_reg_export(root,subkey,target)
        records.append({"artifact_group":group,"source":f"{root}\\{subkey}","method":"reg.exe export snapshot","output":f"registry/{filename}" if ok else "","success":ok,"message":message})
    return records

def preserve_setupapi(destination_root):
    if os.name!="nt":return [{"artifact_group":"setupapi","source":"%WINDIR%\\inf\\setupapi.dev.log","method":"file copy","output":"","success":False,"message":"SetupAPI source preservation is available only on Windows."}]
    windir=Path(os.environ.get("WINDIR",r"C:\Windows")); source=windir/"inf"/"setupapi.dev.log"; target=destination_root/"setupapi"/"setupapi.dev.log"
    if not source.exists():return [{"artifact_group":"setupapi","source":str(source),"method":"file copy","output":"","success":False,"message":f"SetupAPI log not found: {source}"}]
    try:
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
        return [{"artifact_group":"setupapi","source":str(source),"method":"file copy","output":"setupapi/setupapi.dev.log","success":True,"message":"Copied SetupAPI source log."}]
    except OSError as exc:return [{"artifact_group":"setupapi","source":str(source),"method":"file copy","output":"","success":False,"message":f"Cannot copy SetupAPI source log: {exc}"}]

def preserve_selected(groups:Iterable[str],destination_root:Path):
    records=[]
    for group in groups:
        records.extend(preserve_setupapi(destination_root) if group=="setupapi" else preserve_registry_group(group,destination_root))
    return records
