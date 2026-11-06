"""Deterministic decision-input fingerprint for offline decision equivalence v1 (B2)."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    DECISION_INPUT_FINGERPRINT_KEYS,
)


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def compute_productive_gate_bindings_digest_sha256_v1(
    *,
    productive_gate_binding_v1: Mapping[str, Any] | None,
) -> str:
    if not isinstance(productive_gate_binding_v1, Mapping):
        return hashlib.sha256(b"MISSING_PRODUCTIVE_GATE_BINDING_V1").hexdigest()
    return hashlib.sha256(_canonical_json_bytes(dict(productive_gate_binding_v1))).hexdigest()


def compute_decision_input_fingerprint_digest_sha256_v1(
    *,
    binding: Mapping[str, Any],
) -> str:
    """Recomputable digest; must not trust self-asserted fingerprint on compared artifacts."""
    material: dict[str, str] = {}
    for key in DECISION_INPUT_FINGERPRINT_KEYS:
        raw = binding.get(key)
        if raw is None or str(raw).strip() == "":
            continue
        material[key] = str(raw)
    if binding.get("capital_context_decision_affecting") is True:
        if not material.get("capital_context_digest_sha256"):
            material["__capital_context_required_missing__"] = "true"
    if binding.get("host_confirmation_decision_affecting") is True:
        if not material.get("host_confirmation_binding_digest_sha256"):
            material["__host_confirmation_required_missing__"] = "true"
    return hashlib.sha256(_canonical_json_bytes(material)).hexdigest()
