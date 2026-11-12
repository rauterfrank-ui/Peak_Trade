"""Join an already applied F1/M9 configuration to an original offline host observation."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any

from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    format_aware_utc_datetime_v1,
    parse_aware_utc_datetime_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    load_apply_ledger_entries_v1,
    parse_apply_ledger_entry_v1,
)
from src.governance.f1_m9_productive_runtime_apply_start_artifacts_v1 import (
    load_owner_runtime_apply_start_wp_decision_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    load_threshold_ledger_entries_v1,
    parse_threshold_ledger_entry_v1,
)
from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1 import (
    GovernedF1M9RuntimeApplyStartRequestV1,
    run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from trading.master_v2.integrated_offline_replay_evidence_writer_v1 import (
    read_f1_m9_replay_host_observation_v1,
    run_and_write_f1_m9_replay_host_observation_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
)

_SCHEMA_VERSION = "f1_m9_applied_offline_replay_v1"
_EVIDENCE_NAME = "f1_m9_apply_to_host_observation.json"


def _read_ledgers(paths: dict[str, Path]) -> dict[str, bytes]:
    snapshots = {}
    for name, path in paths.items():
        try:
            snapshots[name] = path.read_bytes()
        except FileNotFoundError as exc:
            raise ValueError(f"F1_M9_APPLIED_REPLAY_LEDGER_MISSING:{name}") from exc
    return snapshots


def _validate_ledger_join(
    apply_entry: dict[str, Any], threshold_entry: dict[str, Any], evaluation_time: datetime
) -> datetime:
    if any(
        apply_entry[key] != threshold_entry[key]
        for key in ("owner_apply_authorization_record_digest", "configuration_digest")
    ):
        raise ValueError("F1_M9_APPLIED_REPLAY_LEDGER_LINEAGE_MISMATCH")
    applied_at = parse_aware_utc_datetime_v1(apply_entry["applied_at"], field_name="applied_at")
    threshold_at = parse_aware_utc_datetime_v1(
        threshold_entry["authorized_at"], field_name="authorized_at"
    )
    if not applied_at <= threshold_at <= evaluation_time:
        raise ValueError("F1_M9_APPLIED_REPLAY_LEDGER_TIME_MISMATCH")
    return threshold_at


def _validate_replay_time(
    market_event_time: str, decision_time: str, threshold_at: datetime, evaluation_time: datetime
) -> None:
    market_at = parse_aware_utc_datetime_v1(market_event_time, field_name="market_event_time")
    decision_at = parse_aware_utc_datetime_v1(decision_time, field_name="decision_time")
    if not market_at <= decision_at <= evaluation_time or threshold_at > decision_at:
        raise ValueError("F1_M9_APPLIED_REPLAY_DECISION_TIME_MISMATCH")


def _read_bound_host(evidence: dict[str, Any], root: Path) -> dict[str, Any]:
    if evidence["schema_version"] != _SCHEMA_VERSION or evidence["authority"] != "NONE":
        raise ValueError("F1_M9_APPLIED_REPLAY_SCHEMA_MISMATCH")
    apply_entry = parse_apply_ledger_entry_v1(evidence["apply_ledger_entry"])
    threshold_entry = parse_threshold_ledger_entry_v1(evidence["threshold_ledger_entry"])
    evaluation_time = parse_aware_utc_datetime_v1(
        evidence["evaluation_time_utc"], field_name="evaluation_time_utc"
    )
    threshold_at = _validate_ledger_join(apply_entry, threshold_entry, evaluation_time)
    host = read_f1_m9_replay_host_observation_v1(
        manifest_path=root / "MANIFEST.sha256",
        expected_manifest_sha256=evidence["host_manifest_sha256"],
    )
    observation = host["observation"]
    _validate_replay_time(
        observation["submitted_market_event_time"],
        observation["submitted_decision_time"],
        threshold_at,
        evaluation_time,
    )
    if (
        observation["owner_apply_record_digest"]
        != apply_entry["owner_apply_authorization_record_digest"]
        or observation["owner_threshold_record_digest"]
        != threshold_entry["threshold_value_authorization_record_digest"]
        or observation["seam_digest"] != evidence["seam_digest"]
        or observation["configuration_digest"] != evidence["configuration_digest"]
        or observation["threshold_seconds"] != evidence["threshold_seconds"]
        or observation["configuration_runtime_applied"] is not True
    ):
        raise ValueError("F1_M9_APPLIED_REPLAY_HOST_LINEAGE_MISMATCH")
    return host


def run_and_write_f1_m9_applied_offline_replay_v1(
    *,
    repo_root: Path,
    apply_ledger_paths: F1M9ProductiveApplyLedgerPathsV1,
    threshold_ledger_paths: F1M9ThresholdValueAuthorizationLedgerPathsV1,
    evaluation_time_utc: datetime,
    replay_input: IntegratedOfflineReplayInputV1,
    out_dir: Path,
) -> tuple[Path, str]:
    """Revalidate existing owner state and observe that exact seam in offline replay."""
    if evaluation_time_utc.utcoffset() is None:
        raise ValueError("F1_M9_APPLIED_REPLAY_EVALUATION_TIME_MUST_BE_AWARE")
    evaluation_time = evaluation_time_utc.astimezone(timezone.utc)
    sources = {
        "apply.jsonl": apply_ledger_paths.apply_ledger_path,
        "apply_revocations.jsonl": apply_ledger_paths.revocation_ledger_path,
        "threshold.jsonl": threshold_ledger_paths.threshold_ledger_path,
        "threshold_revocations.jsonl": threshold_ledger_paths.threshold_revocation_ledger_path,
    }
    snapshots = _read_ledgers(sources)
    decision = load_owner_runtime_apply_start_wp_decision_v1(repo_root=repo_root)
    apply_digest = decision["authorized_owner_apply_record_digest"]
    threshold_digest = decision["ratified_threshold_record_digest_bound"]

    # The existing continuation can write. Give it private copies and only
    # accept its idempotent branch on complete, pre-existing owner entries.
    with TemporaryDirectory(prefix="f1-m9-offline-ledgers-") as workspace:
        root = Path(workspace)
        for name, data in snapshots.items():
            (root / name).write_bytes(data)
        applies = [
            row
            for row in load_apply_ledger_entries_v1(root / "apply.jsonl")
            if row["owner_apply_authorization_record_digest"] == apply_digest
        ]
        thresholds = [
            row
            for row in load_threshold_ledger_entries_v1(root / "threshold.jsonl")
            if row["threshold_value_authorization_record_digest"] == threshold_digest
        ]
        if len(applies) != 1 or len(thresholds) != 1:
            raise ValueError("F1_M9_APPLIED_REPLAY_REQUIRES_UNIQUE_OWNER_ENTRIES")
        apply_entry, threshold_entry = applies[0], thresholds[0]
        threshold_at = _validate_ledger_join(apply_entry, threshold_entry, evaluation_time)
        context = replay_input.canonical_market_context
        _validate_replay_time(
            context.market_event_time, context.decision_time, threshold_at, evaluation_time
        )
        resolved = run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
            GovernedF1M9RuntimeApplyStartRequestV1(
                apply_ledger_paths=F1M9ProductiveApplyLedgerPathsV1(
                    root / "apply.jsonl", root / "apply_revocations.jsonl"
                ),
                threshold_ledger_paths=F1M9ThresholdValueAuthorizationLedgerPathsV1(
                    root / "threshold.jsonl", root / "threshold_revocations.jsonl"
                ),
                repo_root=repo_root,
                persist_durable_evidence=False,
                evaluation_time_utc=evaluation_time,
            )
        )
        if resolved.status != "CONTINUATION_COMPLETE":
            reasons = ",".join(resolved.blocking_reasons)
            raise ValueError(f"F1_M9_APPLIED_REPLAY_OWNER_REJECTED:{reasons}")
        if (
            resolved.productive_apply_occurred
            or resolved.external_effect
            or any((root / name).read_bytes() != data for name, data in snapshots.items())
        ):
            raise ValueError("F1_M9_APPLIED_REPLAY_OWNER_READBACK_MUTATED")

    seam = resolved.bound_seam_record
    if (
        seam is None
        or not resolved.configuration_runtime_applied
        or seam.get("authorization_digest") != apply_entry["authorization_digest"]
        or seam.get("ingress_digest") != apply_entry["ingress_digest"]
    ):
        raise ValueError("F1_M9_APPLIED_REPLAY_SEAM_LINEAGE_MISMATCH")
    submitted_seam = replay_input.governed_authorized_productive_parameter_seam_record
    if submitted_seam is not None and submitted_seam != seam:
        raise ValueError("F1_M9_APPLIED_REPLAY_SUBMITTED_SEAM_CONFLICT")

    manifest, manifest_digest = run_and_write_f1_m9_replay_host_observation_v1(
        out_dir=out_dir,
        replay_input=replace(
            replay_input, governed_authorized_productive_parameter_seam_record=dict(seam)
        ),
    )
    if _read_ledgers(sources) != snapshots:
        raise ValueError("F1_M9_APPLIED_REPLAY_SOURCE_LEDGERS_CHANGED")
    evidence = {
        "schema_version": _SCHEMA_VERSION,
        "authority": "NONE",
        "evaluation_time_utc": format_aware_utc_datetime_v1(evaluation_time),
        "source_ledger_sha256": {
            name: hashlib.sha256(data).hexdigest() for name, data in snapshots.items()
        },
        "apply_ledger_entry": apply_entry,
        "threshold_ledger_entry": threshold_entry,
        "seam_digest": seam["seam_digest"],
        "configuration_digest": seam["configuration_digest"],
        "threshold_seconds": seam["threshold_numeric_max_age_seconds"],
        "host_manifest_sha256": manifest_digest,
    }
    _read_bound_host(evidence, manifest.parent)
    encoded = (deterministic_json_dumps(evidence) + "\n").encode("utf-8")
    destination = manifest.parent / _EVIDENCE_NAME
    with NamedTemporaryFile(dir=manifest.parent, prefix=".apply-observation-", delete=False) as out:
        staging = Path(out.name)
        try:
            out.write(encoded)
            out.flush()
            os.fsync(out.fileno())
            os.link(staging, destination)
        finally:
            staging.unlink()
    return destination, hashlib.sha256(encoded).hexdigest()


def read_f1_m9_applied_offline_replay_v1(
    *, evidence_path: Path, expected_sha256: str
) -> dict[str, Any]:
    """Read the archived owner-to-host join without accessing the source ledgers."""
    encoded = evidence_path.read_bytes()
    if hashlib.sha256(encoded).hexdigest() != expected_sha256:
        raise ValueError("F1_M9_APPLIED_REPLAY_EVIDENCE_DIGEST_MISMATCH")
    evidence = json.loads(encoded)
    return {"evidence": evidence, "host": _read_bound_host(evidence, evidence_path.parent)}
