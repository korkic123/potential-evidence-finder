from __future__ import annotations

from datetime import datetime, timezone
from entity_resolver import ResolvedEntity

IDENTITY_POINTS = {"strong": 50, "medium": 35, "weak": 15}

def _level(score: int, high: int = 70, medium: int = 45) -> str:
    if score >= high: return "HIGH"
    if score >= medium: return "MEDIUM"
    return "LOW"

def score_existence_confidence(entity: ResolvedEntity) -> tuple[int, str]:
    identity_points = IDENTITY_POINTS.get(entity.identity_strength, 0)
    source_points = min(entity.source_count, 3) / 3 * 30
    artifact_points = min(entity.artifact_count, 3) / 3 * 20
    score = int(round(identity_points + source_points + artifact_points))
    return score, _level(score)

def _parse_iso(value: str | None) -> datetime | None:
    if not value: return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError: return None

def _recency_points(entity: ResolvedEntity) -> float:
    times = [_parse_iso(o.observed_at_utc) for o in entity.observations]
    times = [t for t in times if t is not None]
    if not times: return 0.0
    age_days = max(0.0, (datetime.now(timezone.utc) - max(times)).total_seconds() / 86400)
    if age_days <= 7: return 30.0
    if age_days <= 30: return 24.0
    if age_days <= 90: return 18.0
    if age_days <= 365: return 10.0
    return 4.0

def score_acquisition_priority(entity: ResolvedEntity) -> tuple[int, str]:
    source_points = min(entity.source_count, 4) / 4 * 40
    artifact_points = min(entity.artifact_count, 4) / 4 * 20
    recency_points = _recency_points(entity)
    relevance_values = [o.properties.get("case_relevance_score") for o in entity.observations]
    numeric_relevance = [float(v) for v in relevance_values if isinstance(v, (int, float))]
    relevance_points = min(max(numeric_relevance, default=0.0), 10.0)
    score = int(round(source_points + artifact_points + recency_points + relevance_points))
    return score, _level(score, high=65, medium=35)

def score_entity(entity: ResolvedEntity) -> tuple[int, str]:
    return score_acquisition_priority(entity)
