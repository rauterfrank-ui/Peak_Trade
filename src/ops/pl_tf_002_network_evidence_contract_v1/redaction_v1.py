"""Secret-bearing field detection for PL-TF-002 evidence bundles."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.pl_tf_002_network_evidence_contract_v1.constants_v1 import (
    FORBIDDEN_SECRET_FIELD_MARKERS,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.errors_v1 import PlTf002NetworkEvidenceError


def _walk_keys(obj: Any, path: str, hits: list[str]) -> None:
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            key_lower = str(key).lower()
            next_path = f"{path}.{key}" if path else str(key)
            for marker in FORBIDDEN_SECRET_FIELD_MARKERS:
                if marker in key_lower:
                    hits.append(next_path)
            _walk_keys(value, next_path, hits)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _walk_keys(item, f"{path}[{idx}]", hits)


def assert_evidence_redaction_invariant_v1(bundle: Mapping[str, Any]) -> None:
    hits: list[str] = []
    _walk_keys(bundle, "", hits)
    if hits:
        raise PlTf002NetworkEvidenceError(f"SECRET_FIELD_PRESENT:{hits[0]}")
