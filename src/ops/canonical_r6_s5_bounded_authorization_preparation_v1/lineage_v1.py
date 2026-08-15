"""Deterministic lineage helpers for R6 S5 bounded-authorization preparation v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.constants_v1 import (
    CANONICAL_SERIALIZATION_VERSION,
    CONTRACT_CONFIG_REL_PATH,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.models_v1 import (
    R6S5BoundedAuthorizationPreparationError,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def contract_config_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / CONTRACT_CONFIG_REL_PATH


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_mapping(payload: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_dumps(payload))


def envelope_digest(*, kind: str, payload: Mapping[str, Any]) -> str:
    return digest_mapping(
        {
            "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
            "kind": kind,
            "payload": dict(payload),
        }
    )


def load_layer_config_v1(root: Path | None = None) -> dict[str, Any]:
    path = contract_config_path(root)
    if not path.is_file():
        raise R6S5BoundedAuthorizationPreparationError(f"contract_config_missing:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise R6S5BoundedAuthorizationPreparationError("contract_config_not_object")
    return payload
