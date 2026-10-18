from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from models import Observation
from utils import safe_name, sha256_file, utc_now_iso, write_json

PACKAGE_FORMAT = "PEFPACK"
SUPPORTED_SCHEMA_VERSIONS = {2}


def create_package(case_id: str, source_id: str, output_dir: Path, metadata: dict[str, Any], observations: list[Observation], source_artifacts_dir: Path | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_now_iso().replace("+00:00", "Z").replace(":", "").replace("-", "")
    final_path = output_dir / f"{safe_name(case_id)}_{safe_name(source_id)}_{stamp}.pefpack"
    with tempfile.TemporaryDirectory(prefix="pef_package_") as td:
        root = Path(td)
        observations_path = root / "observations.json"
        write_json(observations_path, [o.to_dict() for o in observations])
        packaged_artifacts = False
        if source_artifacts_dir and source_artifacts_dir.exists():
            files = [p for p in source_artifacts_dir.rglob("*") if p.is_file()]
            if files:
                packaged_artifacts = True
                target_root = root / "source_artifacts"
                for item in files:
                    relative = item.relative_to(source_artifacts_dir)
                    target = target_root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
        hashes = {"observations.json": sha256_file(observations_path)}
        artifact_root = root / "source_artifacts"
        if artifact_root.exists():
            for item in sorted(p for p in artifact_root.rglob("*") if p.is_file()):
                hashes[str(item.relative_to(root)).replace("\\", "/")] = sha256_file(item)
        manifest = dict(metadata)
        manifest.update({"observation_count": len(observations), "source_artifacts_packaged": packaged_artifacts, "file_hashes_sha256": hashes})
        write_json(root / "manifest.json", manifest)
        with zipfile.ZipFile(final_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for item in root.rglob("*"):
                if item.is_file(): zf.write(item, item.relative_to(root))
    return final_path


def read_package(path: Path) -> tuple[dict[str, Any], list[Observation], list[str]]:
    warnings: list[str] = []
    with zipfile.ZipFile(path, "r") as zf:
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        package_format = manifest.get("package_format")
        schema_version = manifest.get("schema_version")
        if package_format not in (None, PACKAGE_FORMAT):
            raise ValueError(f"Unsupported package format: {package_format!r}")
        if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(f"Unsupported PEFPACK schema_version: {schema_version!r}. Supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)}")
        observations_raw = json.loads(zf.read("observations.json").decode("utf-8"))
        observations = [Observation.from_dict(x) for x in observations_raw]
        for member, expected_hash in manifest.get("file_hashes_sha256", {}).items():
            try: data = zf.read(member)
            except KeyError:
                warnings.append(f"Package member missing: {member}")
                continue
            if hashlib.sha256(data).hexdigest() != expected_hash:
                warnings.append(f"SHA-256 mismatch: {member}")
    return manifest, observations, warnings
