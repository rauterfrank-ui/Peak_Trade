"""Sole productive wallclock authorization consumption gatekeeper (v2 only)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Set

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.consumption_gate_v1 import (
    ConsumptionGateResultV1,
    consume_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_artifact_v2 import (
    parse_authorization_artifact_v2,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA_REJECTED_LEGACY,
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.effective_session_config_digest_v1 import (
    assert_session_config_digest_match_v1,
    compute_effective_session_config_digest_v1,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.v1_quarantine_v1 import (
    classify_authorization_schema_for_wallclock_v1,
    quarantine_authorization_artifact_v1_result,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    WallclockEvidenceWriterV1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    OperatorGoContractV1,
    validate_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    SessionPreregistrationContractV1,
    validate_preregistration_contract_v1,
)


@dataclass
class WallclockV2GatekeeperResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    consumption_id: str = ""
    confirm_token_fingerprint: str = ""
    transport_open_allowed: bool = False
    session_side_effects: int = 0
    notes: list[str] = field(default_factory=list)
    consumption: Optional[ConsumptionGateResultV1] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "consumption_id": self.consumption_id,
            "confirm_token_fingerprint": self.confirm_token_fingerprint,
            "transport_open_allowed": self.transport_open_allowed,
            "session_side_effects": self.session_side_effects,
            "session_started": False,
            "notes": list(self.notes),
        }


def consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
    *,
    prereg: SessionPreregistrationContractV1,
    go: OperatorGoContractV1,
    confirm_token: str,
    evidence_writer: WallclockEvidenceWriterV1,
    artifact_path: Path,
    now_unix: float,
    expected_repository_sha: str,
    fingerprint_ledger_path: Path,
    known_session_ids: Optional[Set[str]] = None,
    runtime_overrides: Optional[Mapping[str, Any]] = None,
    cli_overrides: Optional[Mapping[str, Any]] = None,
    env_overrides: Optional[Mapping[str, Any]] = None,
    defaults: Optional[Mapping[str, Any]] = None,
    config_files: Optional[Mapping[str, str]] = None,
    active_session_found: bool = False,
    resumable_session_found: bool = False,
    stale_session_lock_found: bool = False,
) -> WallclockV2GatekeeperResultV1:
    """Canonical sole productive wallclock consumption authority.

    No session lock, transport, or start marking occurs here.
    transport_open_allowed is set only after durable v2 consumption succeeds.
    """
    notes = [
        "CANONICAL_V2_WALLCLOCK_GATEKEEPER",
        "SINGLE_PRODUCTIVE_AUTHORIZATION_AUTHORITY",
        "NO_SESSION_SIDE_EFFECTS_BEFORE_CONSUMPTION",
    ]
    side_effects = 0
    blockers: list[str] = []

    if not artifact_path.is_file():
        return WallclockV2GatekeeperResultV1(
            ok=False, blockers=["AUTHORIZATION_ARTIFACT_MISSING"], notes=notes
        )

    try:
        raw = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return WallclockV2GatekeeperResultV1(
            ok=False, blockers=["AUTHORIZATION_PARSE_ERROR"], notes=notes
        )
    if not isinstance(raw, dict):
        return WallclockV2GatekeeperResultV1(
            ok=False, blockers=["AUTHORIZATION_NOT_OBJECT"], notes=notes
        )

    kind, kind_blockers = classify_authorization_schema_for_wallclock_v1(raw)
    if kind != "v2":
        quarantined = quarantine_authorization_artifact_v1_result(notes=notes)
        return WallclockV2GatekeeperResultV1(
            ok=False,
            blockers=list(quarantined["blockers"]) or kind_blockers,
            notes=list(quarantined["notes"]),
            transport_open_allowed=False,
            session_side_effects=0,
        )

    pr = validate_preregistration_contract_v1(
        prereg, now_unix=now_unix, expected_repository_sha=expected_repository_sha
    )
    blockers.extend(pr.blockers)
    gr = validate_operator_go_contract_v1(
        go, prereg=prereg, now_unix=now_unix, expected_repository_sha=expected_repository_sha
    )
    blockers.extend(gr.blockers)
    known = known_session_ids or set()
    if go.session_id in known:
        blockers.append("ABORT_DUPLICATE_SESSION")
    if go.consumed or prereg.consumed:
        blockers.append("ALREADY_CONSUMED")
    if go.revoked or prereg.revoked:
        blockers.append("REVOKED")

    try:
        artifact = parse_authorization_artifact_v2(raw)
    except Exception as exc:  # noqa: BLE001
        return WallclockV2GatekeeperResultV1(
            ok=False,
            blockers=sorted(set(blockers + [f"AUTHORIZATION_PARSE_FAILED:{type(exc).__name__}"])),
            notes=notes,
        )

    live_digest = compute_effective_session_config_digest_v1(
        capability=artifact.capability or TARGET_RUNTIME_CAPABILITY,
        session_duration_seconds=artifact.session_duration_seconds,
        safety_boundaries=artifact.safety_boundaries,
        runtime_overrides=runtime_overrides,
        cli_overrides=cli_overrides,
        env_overrides=env_overrides,
        defaults=defaults,
        config_files=config_files
        or {k: v for k, v in artifact.config_digests.items() if k != "effective_session_config"},
    )
    blockers.extend(
        assert_session_config_digest_match_v1(
            authorization_digest=artifact.session_config_digest,
            live_digest=live_digest,
        )
    )

    if blockers:
        return WallclockV2GatekeeperResultV1(
            ok=False, blockers=sorted(set(blockers)), notes=notes, session_side_effects=0
        )

    # Load previously seen fingerprints for replay protection at wallclock layer.
    seen: set[str] = set()
    if fingerprint_ledger_path.is_file():
        for line in fingerprint_ledger_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                seen.add(line)
    fp = fingerprint_confirm_token(confirm_token)
    if fp in seen:
        return WallclockV2GatekeeperResultV1(
            ok=False,
            blockers=["CONFIRM_TOKEN_REPLAY"],
            notes=notes,
            session_side_effects=0,
        )

    # Bind preregistration via session_id + scope_digest (fail-closed).
    if artifact.preregistration_id != prereg.session_id:
        blockers.append("PREREGISTRATION_ID_MISMATCH")
    if artifact.preregistration_digest != prereg.scope_digest():
        blockers.append("PREREGISTRATION_DIGEST_MISMATCH")
    if artifact.repository_sha != expected_repository_sha:
        blockers.append("REPOSITORY_SHA_MISMATCH")
    if blockers:
        return WallclockV2GatekeeperResultV1(
            ok=False, blockers=sorted(set(blockers)), notes=notes, session_side_effects=0
        )

    consumption = consume_authorization_artifact_v2(
        evidence_root=evidence_writer.evidence_root,
        artifact_path=artifact_path,
        confirm_token=confirm_token,
        expected_repository_sha=expected_repository_sha,
        expected_preregistration_id=artifact.preregistration_id,
        expected_preregistration_digest=artifact.preregistration_digest,
        expected_runbook_sha256=artifact.runbook_sha256,
        expected_capability=artifact.capability,
        now_unix=now_unix,
        active_session_found=active_session_found,
        resumable_session_found=resumable_session_found,
        stale_session_lock_found=stale_session_lock_found,
        config_digests_live={
            **dict(sorted(artifact.config_digests.items())),
        },
    )
    if not consumption.ok:
        return WallclockV2GatekeeperResultV1(
            ok=False,
            blockers=list(consumption.blockers),
            notes=notes + list(consumption.notes),
            consumption=consumption,
            session_side_effects=0,
        )

    # Persist wallclock evidence AFTER durable v2 consumption only.
    record = {
        "session_id": go.session_id,
        "go_id": go.go_id,
        "authorization_id": artifact.authorization_id,
        "consumed_at": float(now_unix if now_unix is not None else time.time()),
        "confirm_token_fingerprint": fp,
        "scope_digest": prereg.scope_digest(),
        "expected_repository_sha": expected_repository_sha,
        "canonical_schema": "authorization_artifact_v2",
        "consumption_id": consumption.consumption_id,
        "transport_open_allowed_after_persist": True,
        "revocation_checked_before_consumption": True,
        "session_config_digest": artifact.session_config_digest,
    }
    evidence_writer.write_immutable_json("prereg.json", prereg.to_dict())
    evidence_writer.write_immutable_json("operator_go.json", go.to_dict())
    evidence_writer.write_immutable_json(
        "authorization_artifact.json",
        json.loads(artifact_path.read_text(encoding="utf-8")),
    )
    evidence_writer.write_immutable_json("authorization_consumption_record.json", record)
    evidence_writer.write_immutable_json(
        "authorization_consumption.json",
        {
            "status": "CONSUMED",
            "consumed": True,
            "productive_authorization": True,
            "mode": "productive_wallclock_v2",
            "forced_wiring_fixture": False,
            "session_id": go.session_id,
            "authorization_id": artifact.authorization_id,
            "confirm_token_fingerprint": fp,
            "canonical_schema": "authorization_artifact_v2",
        },
    )
    evidence_writer.write_immutable_text("scope_digest.txt", prereg.scope_digest())
    evidence_writer.write_immutable_text("repo_sha.txt", expected_repository_sha)
    fingerprint_ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with fingerprint_ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(fp + "\n")
        fh.flush()

    return WallclockV2GatekeeperResultV1(
        ok=True,
        consumption_id=consumption.consumption_id,
        confirm_token_fingerprint=fp,
        transport_open_allowed=True,
        session_side_effects=side_effects,
        notes=notes + ["V2_CONSUMPTION_COMPLETE_TRANSPORT_MAY_OPEN"],
        consumption=consumption,
    )


def reject_legacy_authorization_for_wallclock_v1(
    *,
    artifact_path: Path,
) -> WallclockV2GatekeeperResultV1:
    """Explicit rejection helper for V1/legacy paths (zero side effects)."""
    if not artifact_path.is_file():
        return WallclockV2GatekeeperResultV1(
            ok=False, blockers=["AUTHORIZATION_ARTIFACT_MISSING"], session_side_effects=0
        )
    raw = json.loads(artifact_path.read_text(encoding="utf-8"))
    kind, _ = classify_authorization_schema_for_wallclock_v1(raw if isinstance(raw, dict) else {})
    if kind == "v2":
        return WallclockV2GatekeeperResultV1(
            ok=False,
            blockers=["EXPECTED_LEGACY_FOR_QUARANTINE_PROBE"],
            session_side_effects=0,
        )
    return WallclockV2GatekeeperResultV1(
        ok=False,
        blockers=[AUTHORIZATION_SCHEMA_REJECTED_LEGACY],
        notes=["LEGACY_PRODUCTIVE_AUTHORITY_RETIRED"],
        transport_open_allowed=False,
        session_side_effects=0,
    )
