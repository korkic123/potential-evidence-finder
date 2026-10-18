from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Observation:
    source_id: str
    entity_type: str
    artifact_type: str
    relation_type: str
    display_name: str
    identifiers: dict[str, str] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)
    raw_reference: str | None = None
    observed_at_utc: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Observation":
        return cls(**data)
