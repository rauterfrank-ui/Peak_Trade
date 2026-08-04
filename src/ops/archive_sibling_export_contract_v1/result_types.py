"""Result types for CAPABILITY_ARCHIVE_SIBLING_EXPORT_CONTRACT_V1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ArchiveSiblingExportEffectV1(str, Enum):
    """Operator-facing dry-run / write effect classification."""

    CREATE = "CREATE"
    REPLACE = "REPLACE"
    NO_CHANGE = "NO_CHANGE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ArchiveSiblingExportResultV1:
    """Fail-closed, audit-friendly archive-sibling export outcome."""

    effect: ArchiveSiblingExportEffectV1
    write_performed: bool
    dry_run: bool
    contract_name: str
    target_path: str | None
    source_digest: str | None = None
    target_digest_before: str | None = None
    target_digest_after: str | None = None
    expected_target_digest: str | None = None
    block_reason: str | None = None
    schema_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Machine-readable summary with enum values as strings."""
        payload = asdict(self)
        payload["effect"] = self.effect.value
        return payload
