"""Canonical Forensic Identity (CFI/v1) helpers."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import CFI_SCHEMA

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def normalize_native_id(raw: str) -> str:
    text = str(raw).strip()
    if _CONTROL_CHARS.search(text):
        raise ValueError(f"native_id contains control characters: {raw!r}")
    return text


def build_cfi_v1(
    *,
    entity_type: str,
    snapshot_id: str,
    source_system: str,
    source_native_id: str,
) -> str:
    native = normalize_native_id(source_native_id)
    snap = normalize_native_id(snapshot_id)
    sys_name = normalize_native_id(source_system)
    et = normalize_native_id(entity_type)
    return f"CFI/v1/{et}/{snap}/{sys_name}/{native}"


def snapshot_id_from_bindings(bindings: Mapping[str, Any]) -> str:
    payload = json.dumps(bindings, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class ProvenanceRecordV1:
    source_tool: str
    source_artifact: str
    source_revision: str
    code_revision: str
    native_id: str
    canonical_id: str
    evidence_type: str
    proof_class: str
    observed_or_inferred: str
    activation_conditions: tuple[str, ...]
    validation_status: str
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "SOURCE_TOOL": self.source_tool,
            "SOURCE_ARTIFACT": self.source_artifact,
            "SOURCE_REVISION": self.source_revision,
            "CODE_REVISION": self.code_revision,
            "NATIVE_ID": self.native_id,
            "CANONICAL_ID": self.canonical_id,
            "EVIDENCE_TYPE": self.evidence_type,
            "PROOF_CLASS": self.proof_class,
            "OBSERVED_OR_INFERRED": self.observed_or_inferred,
            "ACTIVATION_CONDITIONS": list(self.activation_conditions),
            "VALIDATION_STATUS": self.validation_status,
            "LIMITATIONS": list(self.limitations),
            "SCHEMA": CFI_SCHEMA,
        }
