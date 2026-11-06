"""Reproducibility digests and deterministic serialization helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def canonical_json_bytes(payload: Mapping[str, Any] | list[Any] | dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_text(payload: Mapping[str, Any] | list[Any] | dict[str, Any]) -> str:
    return canonical_json_bytes(payload).decode("utf-8")


def digest_mapping(payload: Mapping[str, Any] | dict[str, Any]) -> str:
    return sha256_hex(canonical_json_bytes(payload))


def compute_config_digest(*, seed: int, scenario_id: str, campaign_id: str) -> str:
    return digest_mapping(
        {
            "campaign_id": campaign_id,
            "scenario_id": scenario_id,
            "seed": int(seed),
            "productive_activation": False,
            "input_authority": False,
            "runtime_implemented": False,
        }
    )
