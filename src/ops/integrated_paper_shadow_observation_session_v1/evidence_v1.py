"""Durable evidence builder for Integrated Paper-Shadow Observation v1.

Writes only when explicitly invoked with a caller-provided evidence root.
Never starts sessions or grants authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    PACKAGE_MARKER,
    SCHEMA_VERSION,
)
from src.ops.integrated_paper_shadow_observation_session_v1.entrypoint_v1 import (
    ObservationCycleResultV1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.no_order_guard_v1 import (
    NoOrderAttestationV1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.session_lifecycle_v1 import (
    ObservationLifecyclePlanV1,
)

EVIDENCE_SCHEMA_ID = "ops.integrated_paper_shadow_observation_evidence_v1"
EVIDENCE_SCHEMA_VERSION = "v1"

REQUIRED_EVIDENCE_ARTIFACTS: tuple[str, ...] = (
    "session_manifest.json",
    "config_snapshot.json",
    "portfolio_snapshot.json",
    "decision_trace.json",
    "risk_telemetry.json",
    "no_order_attestation.json",
    "economic_metrics.json",
    "replay_metadata.json",
    "lifecycle_plan.json",
    "integrity_manifest.json",
    "evidence_manifest.sha256",
)


class ObservationEvidenceError(ValueError):
    """Fail-closed evidence error."""


@dataclass
class ObservationEvidenceBundleV1:
    evidence_root: str
    artifacts: list[str] = field(default_factory=list)
    digests: dict[str, str] = field(default_factory=dict)
    authority_effect: str = AUTHORITY_EFFECT_NONE
    session_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_json(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_observation_evidence_payloads_v1(
    *,
    cycle: ObservationCycleResultV1,
    lifecycle: ObservationLifecyclePlanV1,
    no_order: NoOrderAttestationV1,
    config_snapshot: Mapping[str, Any],
    code_identity: Mapping[str, Any],
    session_identity: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        "session_manifest.json": {
            "schema_id": EVIDENCE_SCHEMA_ID,
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "capability_id": CAPABILITY_ID,
            "package_marker": PACKAGE_MARKER,
            "session_identity": dict(session_identity),
            "code_identity": dict(code_identity),
            "terminal_status": cycle.terminal_status,
            "authority_effect": AUTHORITY_EFFECT_NONE,
            "paper_shadow_observation_authorized": False,
            "wallclock_session_started": False,
        },
        "config_snapshot.json": dict(config_snapshot),
        "portfolio_snapshot.json": dict(cycle.portfolio_snapshot),
        "decision_trace.json": {
            "decision_result": cycle.decision_result,
            "direction": cycle.direction,
            "reason_codes": list(cycle.reason_codes),
            "instrument_id": cycle.instrument_id,
            "venue": cycle.venue,
        },
        "risk_telemetry.json": {
            "risk_sizing_result": cycle.risk_sizing_result,
            "safety_result": cycle.safety_result,
            "futures_only": cycle.futures_only,
            "btc_excluded": cycle.btc_excluded,
            "spot_excluded": cycle.spot_excluded,
        },
        "no_order_attestation.json": no_order.to_dict(),
        "economic_metrics.json": dict(cycle.economic_metrics),
        "replay_metadata.json": {
            "schema_version": SCHEMA_VERSION,
            "entrypoint_owner": cycle.entrypoint_owner,
            "portfolio_model_id": cycle.portfolio_model_id,
            "market_data_policy_ok": cycle.market_data_policy_ok,
            "orders_submitted": False,
            "broker_writes_performed": False,
            "network_used": False,
            "credentials_used": False,
            "replayable": True,
        },
        "lifecycle_plan.json": lifecycle.to_dict(),
    }


def write_observation_evidence_bundle_v1(
    *,
    evidence_root: Path,
    cycle: ObservationCycleResultV1,
    lifecycle: ObservationLifecyclePlanV1,
    no_order: NoOrderAttestationV1,
    config_snapshot: Mapping[str, Any],
    code_identity: Mapping[str, Any],
    session_identity: Mapping[str, Any],
) -> ObservationEvidenceBundleV1:
    """Persist a durable evidence bundle. Caller owns the directory lifecycle."""
    root = evidence_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    payloads = build_observation_evidence_payloads_v1(
        cycle=cycle,
        lifecycle=lifecycle,
        no_order=no_order,
        config_snapshot=config_snapshot,
        code_identity=code_identity,
        session_identity=session_identity,
    )
    digests: dict[str, str] = {}
    artifacts: list[str] = []
    for name, payload in payloads.items():
        text = _canonical_json(payload)
        path = root / name
        path.write_text(text + "\n", encoding="utf-8")
        digests[name] = _sha256_text(text + "\n")
        artifacts.append(name)

    integrity = {
        "schema_id": "ops.integrated_paper_shadow_observation_integrity_v1",
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "digests": digests,
        "artifact_count": len(artifacts),
        "authority_effect": AUTHORITY_EFFECT_NONE,
    }
    integrity_text = _canonical_json(integrity) + "\n"
    (root / "integrity_manifest.json").write_text(integrity_text, encoding="utf-8")
    digests["integrity_manifest.json"] = _sha256_text(integrity_text)
    artifacts.append("integrity_manifest.json")

    manifest_lines = [f"{digests[name]}  {name}" for name in sorted(digests)]
    manifest_body = "\n".join(manifest_lines) + "\n"
    (root / "evidence_manifest.sha256").write_text(manifest_body, encoding="utf-8")
    artifacts.append("evidence_manifest.sha256")

    return ObservationEvidenceBundleV1(
        evidence_root=str(root),
        artifacts=artifacts,
        digests=digests,
        authority_effect=AUTHORITY_EFFECT_NONE,
        session_authorized=False,
    )
