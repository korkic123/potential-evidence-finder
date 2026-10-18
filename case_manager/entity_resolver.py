from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass

from models import Observation


@dataclass
class ResolvedEntity:
    entity_id: str
    entity_type: str
    display_name: str
    identity_strength: str
    match_key: str
    observations: list[Observation]

    @property
    def source_count(self) -> int:
        return len({o.source_id for o in self.observations})

    @property
    def artifact_count(self) -> int:
        return len({o.artifact_type for o in self.observations})


def _norm(value: str) -> str:
    return str(value).strip().strip("\\").casefold()


def _device_instance_key(obs: Observation) -> tuple[str, str] | None:
    pnp = obs.identifiers.get("pnp_device_instance") or obs.identifiers.get("setupapi_device_path")
    if pnp:
        return f"{obs.entity_type}|device_instance|{_norm(pnp)}", "medium"

    wpd = obs.identifiers.get("wpd_instance_id")
    if wpd:
        return f"{obs.entity_type}|wpd_instance|{_norm(wpd)}", "medium"
    setup_wpd = obs.identifiers.get("setupapi_wpd_path")
    if setup_wpd:
        normalized = _norm(setup_wpd)
        for prefix in ("swd\\wpdbusenum\\", "wpdbusenum\\", "wpd\\"):
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
        return f"{obs.entity_type}|wpd_instance|{normalized}", "medium"
    return None


def observation_match_key(obs: Observation) -> tuple[str, str]:
    bluetooth = obs.identifiers.get("bluetooth_address")
    if bluetooth:
        return f"{obs.entity_type}|bluetooth_address|{_norm(bluetooth)}", "strong"

    remote = obs.identifiers.get("remote_path")
    if remote:
        return f"{obs.entity_type}|remote_path|{_norm(remote)}", "strong"

    device_key = _device_instance_key(obs)
    if device_key:
        return device_key

    serial = obs.identifiers.get("usb_serial_candidate")
    if serial:
        return f"{obs.entity_type}|usb_serial_candidate|{_norm(serial)}", "medium"

    mounted = obs.identifiers.get("mounted_device_data")
    if mounted:
        return f"{obs.entity_type}|mounted_device_data|{_norm(mounted)}", "medium"

    weak = f"{obs.entity_type}|weak|{obs.source_id.casefold()}|{obs.display_name.casefold()}"
    return weak, "weak"


def resolve_entities(observations: list[Observation]) -> list[ResolvedEntity]:
    grouped: dict[str, list[Observation]] = defaultdict(list)
    strengths: dict[str, str] = {}
    for obs in observations:
        key, strength = observation_match_key(obs)
        grouped[key].append(obs)
        strengths[key] = strength

    entities: list[ResolvedEntity] = []
    for key, obs_list in grouped.items():
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
        display_name = max((o.display_name for o in obs_list if o.display_name), key=len, default="Unknown")
        entities.append(ResolvedEntity(
            entity_id=f"E-{digest}",
            entity_type=obs_list[0].entity_type,
            display_name=display_name,
            identity_strength=strengths[key],
            match_key=key,
            observations=obs_list,
        ))
    return sorted(entities, key=lambda e: (e.source_count, e.artifact_count), reverse=True)
