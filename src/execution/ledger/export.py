from __future__ import annotations

import json
from typing import Any, Mapping

from .models import ValuationSnapshot


def export_snapshot(snapshot: ValuationSnapshot) -> str:
    """
    Stable JSON export for a ValuationSnapshot.

    Contract:
    - sort_keys=True
    - stable separators
    - snapshot is expected to already contain quantized Decimal strings
    """
    return json.dumps(snapshot.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def export_mapping(obj: Mapping[str, Any]) -> str:
    """
    Stable JSON export for already-normalized mappings.
    """
    return json.dumps(dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
