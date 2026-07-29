"""Issuance / ordering evidence helpers for productive wallclock runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E501
    CANONICAL_HOST,
    ISSUANCE_MANIFEST_SCHEMA,
    PRODUCER_FAMILY,
    SCHEMA_VERSION,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
)


def write_issuance_runtime_evidence_v1(
    *,
    evidence_root: Path,
    session_id: str,
    preregistration_fingerprint: str,
    authorization_fingerprint: str,
    confirm_token_fingerprint: str,
    consumed_at: float,
    transport_open_at: float | None,
    host: str = CANONICAL_HOST,
    method: str = "GET",
    paths: list[str] | None = None,
) -> dict[str, Any]:
    if transport_open_at is not None and transport_open_at < consumed_at:
        raise ValueError("TRANSPORT_BEFORE_CONSUMPTION")
    payload: dict[str, Any] = {
        "schema": ISSUANCE_MANIFEST_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "producer_family": PRODUCER_FAMILY,
        "session_id": session_id,
        "preregistration_fingerprint": preregistration_fingerprint,
        "authorization_fingerprint": authorization_fingerprint,
        "confirm_token_fingerprint": confirm_token_fingerprint,
        "consumed_at": consumed_at,
        "transport_open_at": transport_open_at,
        "transport_after_consumption": (
            True if transport_open_at is None else bool(transport_open_at >= consumed_at)
        ),
        "host_attestation": host,
        "method_attestation": method,
        "path_attestation": list(paths or []),
        "redaction_attestation": True,
        "credentials_used": False,
        "durable_artifacts_omit_confirm_token": True,
        "orders_submitted": False,
        "fixture_non_authoritative": False,
    }
    assert_no_plaintext_token_fields(payload)
    evidence_root.mkdir(parents=True, exist_ok=True)
    path = evidence_root / "issuance_manifest.json"
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return payload


def assert_no_plaintext_token_in_text_v1(text: str) -> list[str]:
    blockers: list[str] = []
    if "GO_PSO_SESSION_PREREG_V1_" in text and "FIXTURE_NON_AUTHORITATIVE" not in text:
        # Allow hashed/fingerprint references; block long token-looking blobs after prefix.
        for line in text.splitlines():
            if "GO_PSO_SESSION_PREREG_V1_" in line and "[REDACTED]" not in line:
                # Fingerprints/hashes are hex; plaintext tokens include urlsafe body.
                if "sha256:" not in line.lower() and "fingerprint" not in line.lower():
                    if len(line.strip()) > 40 and "binding" not in line.lower():
                        blockers.append("PLAINTEXT_TOKEN_LEAK_SUSPECT")
    return blockers
