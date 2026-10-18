from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models import Observation
from package_io import create_package


def main():
    out = ROOT / "demo_packages"
    out.mkdir(exist_ok=True)
    device = r"USBSTOR\Disk&Ven_SanDisk&Prod_Ultra\ABC123&0"
    datasets = {
        "PC-A": [
            Observation("PC-A", "external_storage", "USBSTOR", "previously_connected", "SanDisk Ultra", {"pnp_device_instance": device, "usb_serial_candidate": "ABC123"}),
            Observation("PC-A", "external_storage", "SetupAPI", "installation_or_connection_trace", device, {"setupapi_device_path": device}),
            Observation("PC-A", "network_resource", "MappedNetworkDrive", "mapped_or_known", r"\\NAS01\CaseShare", {"remote_path": r"\\nas01\caseshare"}),
        ],
        "PC-B": [
            Observation("PC-B", "external_storage", "USBSTOR", "previously_connected", "SanDisk Ultra", {"pnp_device_instance": device, "usb_serial_candidate": "ABC123"}),
            Observation("PC-B", "network_resource", "MountPoints2", "previously_accessed", r"\\NAS01\CaseShare", {"remote_path": r"\\nas01\caseshare"}),
        ],
    }
    for source_id, observations in datasets.items():
        create_package("DEMO-001", source_id, out, {"package_format":"PEFPACK","schema_version":2,"case_id":"DEMO-001","source_id":source_id,"host":{"hostname":source_id},"collected_at_utc":"2026-10-18T00:00:00+00:00","default_collection_mode":"parsed_results_only"}, observations, source_artifacts_dir=None)
    print(f"Created demo packages in: {out}")

if __name__ == "__main__": main()
