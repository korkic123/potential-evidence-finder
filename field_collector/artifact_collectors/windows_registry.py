from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from models import Observation

try:
    import winreg
except ImportError:
    winreg=None

def _filetime_to_iso(value:int)->str|None:
    if not value:return None
    try:return datetime.fromtimestamp((value-116444736000000000)/10_000_000,tz=timezone.utc).replace(microsecond=0).isoformat()
    except (OverflowError,OSError,ValueError):return None

def _enum_subkeys(root:Any,path:str)->list[str]:
    names=[]
    with winreg.OpenKey(root,path,0,winreg.KEY_READ) as key:
        idx=0
        while True:
            try:names.append(winreg.EnumKey(key,idx));idx+=1
            except OSError:break
    return names

def _read_values(root:Any,path:str)->tuple[dict[str,Any],str|None]:
    values={}
    with winreg.OpenKey(root,path,0,winreg.KEY_READ) as key:
        _,value_count,last_write=winreg.QueryInfoKey(key)
        for idx in range(value_count):
            try:
                name,value,_=winreg.EnumValue(key,idx)
                if isinstance(value,bytes):value=value.hex()
                elif isinstance(value,(list,tuple)):value=[str(v) for v in value]
                values[name or "(Default)"]=value
            except OSError:continue
    return values,_filetime_to_iso(last_write)

def collect_usbstor(source_id:str)->tuple[list[Observation],list[str]]:
    observations=[];errors=[]
    if os.name!="nt" or winreg is None:return observations,["USBSTOR collection is available only on Windows."]
    base=r"SYSTEM\CurrentControlSet\Enum\USBSTOR"
    try:device_classes=_enum_subkeys(winreg.HKEY_LOCAL_MACHINE,base)
    except OSError as exc:return observations,[f"USBSTOR unavailable: {exc}"]
    for device_class in device_classes:
        class_path=base+"\\"+device_class
        try:instances=_enum_subkeys(winreg.HKEY_LOCAL_MACHINE,class_path)
        except OSError as exc:errors.append(f"Cannot enumerate {class_path}: {exc}");continue
        for instance in instances:
            path=class_path+"\\"+instance
            try:values,last_write=_read_values(winreg.HKEY_LOCAL_MACHINE,path)
            except OSError as exc:errors.append(f"Cannot read {path}: {exc}");continue
            friendly=str(values.get("FriendlyName") or values.get("DeviceDesc") or device_class)
            identifiers={"usb_device_class":device_class,"usb_instance_id":instance,"pnp_device_instance":f"USBSTOR\\{device_class}\\{instance}"}
            if instance and "&" not in instance.rstrip("&0"):identifiers["usb_serial_candidate"]=instance.removesuffix("&0")
            observations.append(Observation(source_id,"external_storage","USBSTOR","previously_connected",friendly,identifiers,{"manufacturer":values.get("Mfg"),"service":values.get("Service"),"registry_key_last_write_utc":last_write,"registry_path":"HKLM\\"+path},observed_at_utc=last_write))
    return observations,errors

def _decode_mounted_data(raw:bytes)->str:
    if not raw:return ""
    for encoding in ("utf-16-le","utf-8","latin-1"):
        try:
            text=raw.decode(encoding,errors="strict").rstrip("\x00")
            if sum(ch.isprintable() for ch in text)>=max(1,len(text)//2):return text
        except UnicodeError:pass
    return raw.hex()

def collect_mounted_devices(source_id:str)->tuple[list[Observation],list[str]]:
    observations=[];errors=[]
    if os.name!="nt" or winreg is None:return observations,["MountedDevices collection is available only on Windows."]
    path=r"SYSTEM\MountedDevices"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,path,0,winreg.KEY_READ) as key:
            _,count,last_write=winreg.QueryInfoKey(key);last_write_iso=_filetime_to_iso(last_write)
            for idx in range(count):
                try:name,data,_=winreg.EnumValue(key,idx)
                except OSError:continue
                decoded=_decode_mounted_data(data) if isinstance(data,bytes) else str(data)
                label=name.replace("\\DosDevices\\","") if name.startswith("\\DosDevices\\") else name
                identifiers={"mounted_value_name":name}
                if decoded:identifiers["mounted_device_data"]=decoded
                observations.append(Observation(source_id,"mounted_volume","MountedDevices","mounted_or_known",label,identifiers,{"decoded_data":decoded,"registry_path":"HKLM\\"+path,"registry_key_last_write_utc":last_write_iso},observed_at_utc=last_write_iso))
    except OSError as exc:errors.append(f"MountedDevices unavailable: {exc}")
    return observations,errors

def collect_mapped_network_drives(source_id:str)->tuple[list[Observation],list[str]]:
    observations=[];errors=[]
    if os.name!="nt" or winreg is None:return observations,["Mapped network drive collection is available only on Windows."]
    base=r"Network"
    try:drives=_enum_subkeys(winreg.HKEY_CURRENT_USER,base)
    except OSError:drives=[]
    for drive in drives:
        path=base+"\\"+drive
        try:values,last_write=_read_values(winreg.HKEY_CURRENT_USER,path)
        except OSError as exc:errors.append(f"Cannot read HKCU\\{path}: {exc}");continue
        remote=str(values.get("RemotePath") or "")
        if not remote:continue
        observations.append(Observation(source_id,"network_resource","MappedNetworkDrive","mapped_or_known",remote,{"remote_path":remote.casefold()},{"drive_letter":drive,"provider":values.get("ProviderName"),"username":values.get("UserName"),"registry_path":"HKCU\\"+path,"registry_key_last_write_utc":last_write},observed_at_utc=last_write))
    return observations,errors

def collect_mountpoints2(source_id:str)->tuple[list[Observation],list[str]]:
    observations=[];errors=[]
    if os.name!="nt" or winreg is None:return observations,["MountPoints2 collection is available only on Windows."]
    base=r"Software\Microsoft\Windows\CurrentVersion\Explorer\MountPoints2"
    try:names=_enum_subkeys(winreg.HKEY_CURRENT_USER,base)
    except OSError:names=[]
    for name in names:
        path=base+"\\"+name
        try:_,last_write=_read_values(winreg.HKEY_CURRENT_USER,path)
        except OSError:last_write=None
        entity_type="network_resource" if name.startswith("##") else "mounted_volume"
        normalized=name.replace("##",r"\\",1).replace("#","\\") if name.startswith("##") else name
        identifiers={"mountpoints2_key":name}
        if entity_type=="network_resource":identifiers["remote_path"]=normalized.casefold()
        observations.append(Observation(source_id,entity_type,"MountPoints2","previously_accessed",normalized,identifiers,{"registry_path":"HKCU\\"+path,"registry_key_last_write_utc":last_write},observed_at_utc=last_write))
    return observations,errors

def collect_wpd(source_id:str)->tuple[list[Observation],list[str]]:
    observations=[];errors=[]
    if os.name!="nt" or winreg is None:return observations,["Portable-device collection is available only on Windows."]
    for base in [r"SYSTEM\CurrentControlSet\Enum\SWD\WPDBUSENUM",r"SYSTEM\CurrentControlSet\Enum\WpdBusEnumRoot"]:
        try:items=_enum_subkeys(winreg.HKEY_LOCAL_MACHINE,base)
        except OSError:continue
        for item in items:
            path=base+"\\"+item
            try:values,last_write=_read_values(winreg.HKEY_LOCAL_MACHINE,path)
            except OSError as exc:errors.append(f"Cannot read HKLM\\{path}: {exc}");continue
            friendly=str(values.get("FriendlyName") or values.get("DeviceDesc") or item)
            observations.append(Observation(source_id,"portable_device","WPD","previously_connected",friendly,{"wpd_instance_id":item},{"manufacturer":values.get("Mfg"),"registry_path":"HKLM\\"+path,"registry_key_last_write_utc":last_write},observed_at_utc=last_write))
    return observations,errors

def collect_bluetooth(source_id:str)->tuple[list[Observation],list[str]]:
    observations=[];errors=[]
    if os.name!="nt" or winreg is None:return observations,["Bluetooth collection is available only on Windows."]
    base=r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
    try:devices=_enum_subkeys(winreg.HKEY_LOCAL_MACHINE,base)
    except OSError:return observations,[]
    for dev in devices:
        path=base+"\\"+dev
        try:values,last_write=_read_values(winreg.HKEY_LOCAL_MACHINE,path)
        except OSError as exc:errors.append(f"Cannot read HKLM\\{path}: {exc}");continue
        name=values.get("Name");friendly=name if isinstance(name,str) else f"Bluetooth {dev}"
        observations.append(Observation(source_id,"bluetooth_device","BTHPORT","paired_or_known",friendly,{"bluetooth_address":dev.lower()},{"registry_path":"HKLM\\"+path,"registry_key_last_write_utc":last_write},observed_at_utc=last_write))
    return observations,errors
