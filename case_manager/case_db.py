from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from entity_resolver import resolve_entities
from models import Observation
from package_io import read_package
from scorer import score_acquisition_priority, score_existence_confidence
from utils import utc_now_iso

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    hostname TEXT,
    collected_at_utc TEXT,
    imported_at_utc TEXT NOT NULL,
    package_path TEXT,
    observation_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    display_name TEXT NOT NULL,
    identifiers_json TEXT NOT NULL,
    properties_json TEXT NOT NULL,
    raw_reference TEXT,
    observed_at_utc TEXT,
    FOREIGN KEY(source_id) REFERENCES sources(source_id)
);
CREATE TABLE IF NOT EXISTS entity_status (
    entity_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'POTENTIAL',
    note TEXT NOT NULL DEFAULT ''
);
"""


class CaseDatabase:
    def __init__(self, path: Path):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    @classmethod
    def create(cls, path: Path, case_id: str) -> "CaseDatabase":
        path.parent.mkdir(parents=True, exist_ok=True)
        db = cls(path)
        db.set_meta("case_id", case_id)
        db.set_meta("created_at_utc", utc_now_iso())
        return db

    def close(self) -> None:
        self.conn.close()

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_meta(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def import_package(self, package_path: Path) -> list[str]:
        manifest, observations, warnings = read_package(package_path)
        case_id = str(manifest.get("case_id", ""))
        db_case = self.get_meta("case_id")
        if db_case and case_id and db_case != case_id:
            raise ValueError(f"Package case_id '{case_id}' does not match open case '{db_case}'.")
        source_id = str(manifest.get("source_id", "UNKNOWN"))
        host = manifest.get("host", {}) or {}

        existing = self.conn.execute("SELECT source_id FROM sources WHERE source_id=?", (source_id,)).fetchone()
        if existing:
            raise ValueError(f"Source '{source_id}' is already imported. Use a unique Source ID for each collected source.")

        self.conn.execute(
            "INSERT INTO sources(source_id, hostname, collected_at_utc, imported_at_utc, package_path, observation_count) VALUES (?, ?, ?, ?, ?, ?)",
            (
                source_id,
                str(host.get("hostname", "")),
                str(manifest.get("collected_at_utc", "")),
                utc_now_iso(),
                str(package_path),
                len(observations),
            ),
        )
        for obs in observations:
            self.conn.execute(
                """INSERT INTO observations(
                    source_id, entity_type, artifact_type, relation_type, display_name,
                    identifiers_json, properties_json, raw_reference, observed_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    obs.source_id,
                    obs.entity_type,
                    obs.artifact_type,
                    obs.relation_type,
                    obs.display_name,
                    json.dumps(obs.identifiers, ensure_ascii=False),
                    json.dumps(obs.properties, ensure_ascii=False),
                    obs.raw_reference,
                    obs.observed_at_utc,
                ),
            )
        self.conn.commit()
        return warnings

    def sources(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM sources ORDER BY imported_at_utc"))

    def _all_observations(self) -> list[Observation]:
        rows = self.conn.execute("SELECT * FROM observations").fetchall()
        return [
            Observation(
                source_id=row["source_id"],
                entity_type=row["entity_type"],
                artifact_type=row["artifact_type"],
                relation_type=row["relation_type"],
                display_name=row["display_name"],
                identifiers=json.loads(row["identifiers_json"]),
                properties=json.loads(row["properties_json"]),
                raw_reference=row["raw_reference"],
                observed_at_utc=row["observed_at_utc"],
            )
            for row in rows
        ]

    def entities(self) -> list[dict[str, Any]]:
        resolved = resolve_entities(self._all_observations())
        result: list[dict[str, Any]] = []
        for entity in resolved:
            existence_score, existence_confidence = score_existence_confidence(entity)
            priority_score, acquisition_priority = score_acquisition_priority(entity)
            row = self.conn.execute("SELECT status, note FROM entity_status WHERE entity_id=?", (entity.entity_id,)).fetchone()
            status = row["status"] if row else "POTENTIAL"
            note = row["note"] if row else ""
            result.append({
                "entity_id": entity.entity_id,
                "entity_type": entity.entity_type,
                "display_name": entity.display_name,
                "identity_strength": entity.identity_strength,
                "source_count": entity.source_count,
                "artifact_count": entity.artifact_count,
                "existence_score": existence_score,
                "existence_confidence": existence_confidence,
                "priority_score": priority_score,
                "acquisition_priority": acquisition_priority,
                "status": status,
                "note": note,
                "observations": entity.observations,
            })
        return sorted(result, key=lambda x: (x["priority_score"], x["existence_score"], x["source_count"]), reverse=True)

    def set_entity_status(self, entity_id: str, status: str, note: str = "") -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO entity_status(entity_id, status, note) VALUES (?, ?, ?)",
            (entity_id, status, note),
        )
        self.conn.commit()
