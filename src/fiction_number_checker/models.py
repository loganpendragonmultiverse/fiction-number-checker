from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Mention:
    value: str
    kind: str
    normalized_value: float
    normalized_unit: str
    subject: str
    context: str
    offset: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewGroup:
    subject: str
    kind: str
    values: tuple[str, ...]
    mentions: tuple[Mention, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "kind": self.kind,
            "values": list(self.values),
            "mentions": [mention.to_dict() for mention in self.mentions],
        }


@dataclass(frozen=True)
class Report:
    source: Path
    mentions: tuple[Mention, ...]
    review_groups: tuple[ReviewGroup, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "source": str(self.source),
            "summary": {
                "mentions": len(self.mentions),
                "reviewGroups": len(self.review_groups),
            },
            "mentions": [mention.to_dict() for mention in self.mentions],
            "reviewGroups": [group.to_dict() for group in self.review_groups],
            "limitations": [
                "Review groups are not proof of contradiction.",
                "Narrative context, time changes, estimates, and different subjects require human interpretation.",
            ],
        }
