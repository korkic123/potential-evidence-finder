from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shutil

from artifact_collectors.setupapi import collect_setupapi
from artifact_collectors.windows_registry import (
    collect_bluetooth,
    collect_mapped_network_drives,
    collect_mountpoints2,
    collect_mounted_devices,
    collect_usbstor,
    collect_wpd,
)
from models import Observation
from package_io import create_package
from source_preservation import preserve_selected
from utils import host_info, runtime_info, utc_now_iso

TOOL_VERSION = "1.0.0"

@dataclass
class CollectionOptions:
    usb: bool = True
    mounted_devices: bool = True
    network: bool = True
    portable_devices: bool = True
    bluetooth: bool = True
    setupapi: bool = True
    preserve_usb: bool = False
    preserve_mounted_devices: bool = False
    preserve_network: bool = False
    preserve_portable_devices: bool = False
    preserve_bluetooth: bool = False
    preserve_setupapi: bool = False
    def analysis_flags(self):
        return {"usb":self.usb,"mounted_devices":self.mounted_devices,"network":self.network,"portable_devices":self.portable_devices,"bluetooth":self.bluetooth,"setupapi":self.setupapi}
    def preservation_flags(self):
        return {"usb":self.preserve_usb,"mounted_devices":self.preserve_mounted_devices,"network":self.preserve_network,"portable_devices":self.preserve_portable_devices,"bluetooth":self.preserve_bluetooth,"setupapi":self.preserve_setupapi}

@dataclass
class CollectionResult:
    package_path: Path
    observations: list[Observation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    preservation_records: list[dict] = field(default_factory=list)

def _add_provenance(observations, collected_at):
    for obs in observations:
        source_location=obs.properties.get("registry_path") or obs.properties.get("source_file") or ""
        obs.properties.setdefault("provenance",{"collector":"Potential Evidence Finder","collector_version":TOOL_VERSION,"artifact_type":obs.artifact_type,"source_location":source_location,"extraction_method":"live read and parse","collected_at_utc":collected_at})

def _attach_preserved_references(observations, records):
    successful=[r for r in records if r.get("success") and r.get("output")]
    for obs in observations:
        location=str(obs.properties.get("registry_path") or obs.properties.get("source_file") or "").casefold()
        if not location: continue
        for record in successful:
            source=str(record.get("source") or "").casefold()
            if source and (location.startswith(source) or source.startswith(location)):
                obs.raw_reference="source_artifacts/"+str(record["output"]).replace("\\","/");break

def collect(case_id: str, source_id: str, output_dir: Path, options: CollectionOptions) -> CollectionResult:
    temp_dir=output_dir/".pef_work"; source_artifacts_dir=temp_dir/"source_artifacts"; temp_dir.mkdir(parents=True,exist_ok=True)
    observations=[]; warnings=[]
    def run(fn):
        obs,errs=fn(); observations.extend(obs); warnings.extend(errs)
    if options.usb: run(lambda:collect_usbstor(source_id))
    if options.mounted_devices: run(lambda:collect_mounted_devices(source_id))
    if options.network:
        run(lambda:collect_mapped_network_drives(source_id)); run(lambda:collect_mountpoints2(source_id))
    if options.portable_devices: run(lambda:collect_wpd(source_id))
    if options.bluetooth: run(lambda:collect_bluetooth(source_id))
    if options.setupapi: run(lambda:collect_setupapi(source_id))
    collected_at=utc_now_iso(); _add_provenance(observations,collected_at)
    preservation_flags=options.preservation_flags(); requested_groups=[name for name,enabled in preservation_flags.items() if enabled]
    preservation_records=[]
    if requested_groups:
        preservation_records=preserve_selected(requested_groups,source_artifacts_dir); _attach_preserved_references(observations,preservation_records)
        warnings.extend(str(record.get("message")) for record in preservation_records if not record.get("success"))
    metadata={"package_format":"PEFPACK","schema_version":2,"tool":"Potential Evidence Finder","tool_version":TOOL_VERSION,"case_id":case_id,"source_id":source_id,"collected_at_utc":collected_at,"host":host_info(),"runtime":runtime_info(),"analysis_options":options.analysis_flags(),"source_artifact_preservation_requested":preservation_flags,"source_artifact_preservation":preservation_records,"default_collection_mode":"parsed_results_only","warning_count":len(warnings),"warnings":warnings}
    package_path=create_package(case_id,source_id,output_dir,metadata,observations,source_artifacts_dir if requested_groups else None)
    shutil.rmtree(temp_dir,ignore_errors=True)
    return CollectionResult(package_path,observations,warnings,preservation_records)
