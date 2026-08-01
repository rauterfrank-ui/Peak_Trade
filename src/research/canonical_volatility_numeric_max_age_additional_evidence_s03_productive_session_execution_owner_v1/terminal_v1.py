"""Terminal verdict and integrity manifest for S03 evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    SCHEMA_INTEGRITY_MANIFEST,
    SCHEMA_TERMINAL_VERDICT,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.evidence_v1 import (
    evidence_file_map_v1,
    write_json_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    S03ScopeBindingsV1,
    sha256_hex_canonical,
)


def build_terminal_verdict_v1(
    *,
    bindings: S03ScopeBindingsV1,
    status: str,
    terminal_reason: str,
    authorization_consumed: bool,
    actual_monotonic_duration_seconds: float,
    sufficient_s03_evidence: bool,
    network_activity_occurred: bool,
    counterfactual_runtime_authority_occurred: bool = False,
) -> dict[str, Any]:
    payload = {
        "schema": SCHEMA_TERMINAL_VERDICT,
        **bindings.to_dict(),
        "status": status,
        "terminal_reason": terminal_reason,
        "authorization_consumed": bool(authorization_consumed),
        "actual_monotonic_duration_seconds": float(actual_monotonic_duration_seconds),
        "requested_duration_seconds": int(bindings.duration_seconds),
        "sufficient_s03_evidence": bool(sufficient_s03_evidence),
        "network_activity_occurred": bool(network_activity_occurred),
        "COUNTERFACTUAL_RUNTIME_AUTHORITY_OCCURRED": bool(
            counterfactual_runtime_authority_occurred
        ),
        "NUMERIC_MAX_AGE_SELECTED": False,
        "POLICY_ENFORCEMENT_ADDED": False,
    }
    payload["record_digest"] = sha256_hex_canonical(payload)
    return payload


def build_integrity_manifest_v1(
    *,
    bindings: S03ScopeBindingsV1,
    session_dir: Path,
    terminal_verdict: Mapping[str, Any],
    file_digests: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    files = evidence_file_map_v1(session_dir)
    digests: dict[str, str] = dict(file_digests or {})
    for key, path in files.items():
        if key in digests:
            continue
        if path.is_file():
            digests[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    payload = {
        "schema": SCHEMA_INTEGRITY_MANIFEST,
        **bindings.to_dict(),
        "terminal_verdict_digest": terminal_verdict.get("record_digest"),
        "file_digests": dict(sorted(digests.items())),
        "evidence_root": str(session_dir),
    }
    payload["manifest_digest"] = sha256_hex_canonical(payload)
    return payload


def write_terminal_artifacts_v1(
    *,
    session_dir: Path,
    bindings: S03ScopeBindingsV1,
    status: str,
    terminal_reason: str,
    authorization_consumed: bool,
    actual_monotonic_duration_seconds: float,
    sufficient_s03_evidence: bool,
    network_activity_occurred: bool,
    counterfactual_runtime_authority_occurred: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    files = evidence_file_map_v1(session_dir)
    verdict = build_terminal_verdict_v1(
        bindings=bindings,
        status=status,
        terminal_reason=terminal_reason,
        authorization_consumed=authorization_consumed,
        actual_monotonic_duration_seconds=actual_monotonic_duration_seconds,
        sufficient_s03_evidence=sufficient_s03_evidence,
        network_activity_occurred=network_activity_occurred,
        counterfactual_runtime_authority_occurred=counterfactual_runtime_authority_occurred,
    )
    write_json_v1(files["terminal_verdict"], verdict)
    manifest = build_integrity_manifest_v1(
        bindings=bindings,
        session_dir=session_dir,
        terminal_verdict=verdict,
    )
    write_json_v1(files["integrity_manifest"], manifest)
    return verdict, manifest, files["terminal_verdict"], files["integrity_manifest"]
