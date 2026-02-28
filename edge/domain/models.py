"""Domain models for edge telemetry readings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class SensorReading:
    """Represents a validated sensor reading payload."""

    temperature: float
    humidity: float
    timestamp: str
    device_id: str

    def to_dict(self) -> dict[str, object]:
        """Return the reading as a dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Return a deterministic JSON representation of the reading."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
