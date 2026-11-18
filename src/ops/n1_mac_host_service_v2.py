"""Prepare or dispatch the occupied N1 V2 Mac service through its scoped GET port."""

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import plistlib
import re
import sqlite3
import time

from src.governance.current_continuous_run_policy_v1 import standing_continuous_run_authorized_v1
from src.governance import f1_m9_productive_apply_durable_ledger_paths_v1 as ledger_paths
from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    GovernedF1M9ThresholdConsumerWiringRequestV1,
    run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1,
)
from src.ops.execution_reconciliation_proof_store_v1 import (
    find_authenticated_entry_sources_v1,
    require_booked_net_reversal_readback_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_run_owner_go_wiring_v1 import (
    validate_bounded_continuous_run_owner_go_decision_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
    _read_retained_net_reversal_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    build_s8_occupied_lane_pairs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    current_productive_cursor_digest_v1,
    load_current_productive_sidestate_confirmation_cursor_v1,
    parse_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    inspect_selection_v1,
)
from src.ops.n1_occupied_net_reversal_host_v2 import run_occupied_n1_net_reversal_host_v2
from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import startup_factory_v1
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    budget_owner_root_for_config_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import (
    UnattendedHostBoundsV1,
    _filegate_revision,
    unattended_request_digest_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
    read_occupied_scope_mark_snapshot_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    read_budget_revision_read_only_v1,
    require_budget_head_read_only_v1,
)

SCHEMA = "n1_unattended_host_service.v2"
LABEL = "de.peaktrade.n1-host.v2"
LANE = "LANE_1"
REPO = Path(__file__).resolve().parents[2]


def _canonical_path(value):
    path = Path(value)
    if not path.is_absolute() or path != path.resolve():
        raise ValueError("N1_MAC_V2_CANONICAL_PATH_REQUIRED")
    return path


def _require_digest(value):
    if not isinstance(value, str) or re.fullmatch("[a-f0-9]{64}", value) is None:
        raise ValueError("N1_MAC_V2_DIGEST_REQUIRED")


@dataclass(frozen=True)
class OccupiedCheckpoint:
    reservation_id: str
    episode_id: str
    budget_sequence: int
    budget_head: str
    cursor_digest: str

    def validate(self):
        for value in (self.reservation_id, self.budget_head, self.cursor_digest):
            _require_digest(value)
        if not isinstance(self.episode_id, str):
            raise ValueError("N1_MAC_V2_EPISODE_REQUIRED")
        _require_digest(self.episode_id.removeprefix("simulated-accounting:"))
        if type(self.budget_sequence) is not int or self.budget_sequence < 1:
            raise ValueError("N1_MAC_V2_BUDGET_SEQUENCE_INVALID")


@dataclass(frozen=True)
class MacHostManifestV2:
    bounds: UnattendedHostBoundsV1
    state_root: Path
    runtime_config: dict
    checkpoint: OccupiedCheckpoint
    filegate_path: Path
    filegate_revision: str

    def prepare_request(self, attempt, evidence):
        return startup_factory_v1.prepare_occupied_n1_request_v1(
            attempt_index=attempt,
            evidence_root=evidence,
            runtime_config=self.runtime_config,
        )


def build_mac_host_manifest_v2(
    *,
    host_id,
    state_root,
    expires_at_unix,
    runtime_config,
    checkpoint,
    filegate_path,
    filegate_revision,
):
    """Build explicitly bound deployment inputs without opening the prepared ports."""
    data = startup_factory_v1.build_occupied_n1_manifest_v1(
        host_id=host_id,
        state_root=state_root,
        expires_at_unix=expires_at_unix,
        runtime_config=runtime_config,
    )
    checkpoint.validate()
    _require_digest(filegate_revision)
    data.pop("runtime_factory")
    return {
        **data,
        "schema": SCHEMA,
        "checkpoint": asdict(checkpoint),
        "filegate": {"path": str(_canonical_path(filegate_path)), "revision": filegate_revision},
    }


def load_mac_host_manifest_v2(path: Path) -> MacHostManifestV2:
    value = json.loads(_canonical_path(path).read_bytes())
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "schema",
            "repository_root",
            "state_root",
            "bounds",
            "runtime_request_config",
            "checkpoint",
            "filegate",
        }
        or value["schema"] != SCHEMA
    ):
        raise ValueError("N1_MAC_V2_MANIFEST_INVALID")
    bounds = UnattendedHostBoundsV1(**value["bounds"])
    bounds.validate_v1()
    if _canonical_path(value["repository_root"]) != REPO:
        raise ValueError("N1_MAC_V2_CHECKOUT_MISMATCH")
    config = value["runtime_request_config"]
    if (
        not isinstance(config, dict)
        or config.get("repository_sha") != bounds.repository_sha
        or not isinstance(config.get("roots"), dict)
        or not isinstance(config.get("authorization"), dict)
    ):
        raise ValueError("N1_MAC_V2_REQUEST_REVISION_MISMATCH")
    limits = config["authorization"]
    if (bounds.max_total_cycles, bounds.max_total_seconds, bounds.wait_interval_seconds) != (
        limits.get("max_cycles_per_run"),
        limits.get("max_run_duration_seconds"),
        limits.get("wait_interval_seconds"),
    ):
        raise ValueError("N1_MAC_V2_BOUNDS_MISMATCH")
    _require_digest(bounds.runtime_config_digest)
    state_root = _canonical_path(value["state_root"])
    for name, root in config["roots"].items():
        other = _canonical_path(root)
        # The deployed checkout itself may contain the canonical F1/M9 ledgers.
        if state_root.is_relative_to(other) or other.is_relative_to(state_root):
            raise ValueError("N1_MAC_V2_STATE_ROOT_OVERLAP:" + name)
    filegate = value["filegate"]
    if not isinstance(filegate, dict) or set(filegate) != {"path", "revision"}:
        raise ValueError("N1_MAC_V2_FILEGATE_BINDING_REQUIRED")
    _require_digest(filegate["revision"])
    checkpoint = OccupiedCheckpoint(**value["checkpoint"])
    checkpoint.validate()
    return MacHostManifestV2(
        bounds,
        state_root,
        config,
        checkpoint,
        _canonical_path(filegate["path"]),
        filegate["revision"],
    )


def _require_cap24(config, bound, revision, *, now):
    current = inspect_selection_v1(
        productivity_root=config.cap24_productivity_root,
        repository_sha=revision,
        binding_epoch=datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    selection = current.selection
    if (
        selection.venue_native_id,
        selection.instrument_id,
        selection.selection_id,
        selection.integrity_digest,
        current.ranking.ranking_snapshot_id,
        current.ranking.integrity_digest,
        current.universe.snapshot_id,
    ) != (
        bound.venue_native_id,
        bound.instrument_id,
        bound.selection_id,
        bound.selection_integrity_digest,
        bound.ranking_snapshot_id,
        bound.ranking_integrity_digest,
        bound.universe_snapshot_id,
    ):
        raise ValueError("N1_MAC_V2_CAP24_BINDING_MISMATCH")


def _require_checkpoint(config, bound, proof_root, checkpoint):
    owner_root = budget_owner_root_for_config_v1(config) / "owner"
    account = config.expected_account_identity
    rid = checkpoint.reservation_id
    snapshot = read_budget_revision_read_only_v1(
        owner_root,
        account_identity=account,
        sequence=checkpoint.budget_sequence,
        expected_digest=checkpoint.budget_head,
    )["state"]
    require_budget_head_read_only_v1(
        owner_root,
        account_identity=account,
        expected_digest=checkpoint.budget_head,
    )
    hold = next((row for row in snapshot["reservations"] if row["reservation_id"] == rid), None)
    if (
        hold is None
        or hold["state"] != "COMMITTED"
        or hold["slot_id"] != LANE
        or snapshot["lane_bindings"].get(LANE, {}).get("bound") != bound.to_dict()
        or hold["binding"]["bound"] != bound.to_dict()
    ):
        raise ValueError("N1_MAC_V2_STORE_HOLD_BINDING_MISMATCH")
    if (
        snapshot.get("offline_v2_opening_fills")
        or snapshot.get("slot_capital_allocation", {}).get("schema")
        != "live_slot_capital_allocation.v1"
    ):
        raise ValueError("N1_MAC_V2_ORIGINAL_LIVE_STORE_REQUIRED")
    lane_pair = build_s8_occupied_lane_pairs_v1(
        lane_state_root=config.lane_state_root, bound=bound
    )[LANE]
    cursor_root = Path(lane_pair[0].lane_state_root)
    payload = load_current_productive_sidestate_confirmation_cursor_v1(cursor_root)
    if current_productive_cursor_digest_v1(payload) != checkpoint.cursor_digest:
        raise ValueError("N1_MAC_V2_CURSOR_DIGEST_MISMATCH")
    cursor = parse_current_productive_sidestate_confirmation_cursor_v1(payload)
    scope = read_occupied_scope_mark_snapshot_v1(cursor_root)
    if (
        (cursor.instrument_id, cursor.venue_native_id)
        != (bound.instrument_id, bound.venue_native_id)
        or scope is None
        or scope["mark"]["position_episode_id"] != checkpoint.episode_id
    ):
        raise ValueError("N1_MAC_V2_CURSOR_EPISODE_MISMATCH")
    reversals = snapshot.get("live_net_reversal_bookings", {}).get(rid, [])
    if reversals:
        last = reversals[-1]
        if (
            last["slot_id"] != LANE
            or last["reservation_id"] != rid
            or last["account"] != account
            or last["instrument_id"] != bound.instrument_id
            or last["native_id"] != bound.venue_native_id
            or last["selection_digest"] != bound.selection_integrity_digest
        ):
            raise ValueError("N1_MAC_V2_BOOKED_EPISODE_MISMATCH")
        if last["envelope_digest"] != checkpoint.episode_id:
            # Booking can commit before the next Mark publishes the successor.
            if (
                last["previous_episode_id"] != checkpoint.episode_id
                or scope["mark"].get("pending_reversal_episode_id") != checkpoint.episode_id
            ):
                raise ValueError("N1_MAC_V2_BOOKED_EPISODE_MISMATCH")
            retained, envelope = _read_retained_net_reversal_v1(lane_pair, scope)
            if (
                retained.old_reservation_id != rid
                or envelope.envelope_digest != last["envelope_digest"]
            ):
                raise ValueError("N1_MAC_V2_BOOKED_EPISODE_MISMATCH")
        require_booked_net_reversal_readback_v1(root=proof_root, booking=last)
    elif not any(
        source.identity.native_id == bound.venue_native_id
        and source.identity.execution_environment == "LIVE"
        and source.lane_binding.get("bound") == bound.to_dict()
        and source.identity.to_dict()
        == snapshot.get("execution_links", {}).get(rid, {}).get("identity")
        and source.reconciliation == snapshot["execution_links"][rid].get("reconciliation")
        and source.reconciliation.get("matched") is True
        and source.reconciliation.get("reservation_released") is False
        and source.reconciliation.get("decision", {}).get("reconciliation_complete") is True
        for source in find_authenticated_entry_sources_v1(
            root=proof_root,
            budget_owner_root=owner_root,
            account=account,
            reservation_id=rid,
            episode_id=checkpoint.episode_id,
        )
    ):
        raise ValueError("N1_MAC_V2_AUTHENTICATED_ENTRY_REQUIRED")
    return cursor.trading_epoch


def preflight_mac_host_v2(manifest, *, clock=time.time):
    """Read one prospective deployment and report every available admission result."""
    blocks = {}
    now = clock()
    if now >= manifest.bounds.expires_at_unix:
        blocks["runtime_window"] = ["N1_MAC_V2_RUNTIME_WINDOW_EXPIRED"]
    approved, reasons = validate_bounded_continuous_run_owner_go_decision_v1(
        repo_root=REPO,
        baseline_origin_main_sha=manifest.bounds.repository_sha,
    )
    if not approved or not standing_continuous_run_authorized_v1(repo_root=REPO):
        blocks["owner_go"] = list(reasons or ("N1_MAC_V2_STANDING_POLICY_REQUIRED",))
    if _filegate_revision(manifest.filegate_path) != manifest.filegate_revision:
        blocks["filegate"] = ["N1_MAC_V2_FILEGATE_REVISION_UNPROVEN"]
    ledgers = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
        GovernedF1M9ThresholdConsumerWiringRequestV1(
            ledger_paths.resolve_canonical_f1_m9_productive_apply_ledger_paths_v1(repo_root=REPO),
            ledger_paths.resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1(
                repo_root=REPO
            ),
            REPO,
        )
    )
    if ledgers.status != "CONTINUATION_COMPLETE":
        blocks["f1_m9"] = list(ledgers.blocking_reasons or ("N1_MAC_V2_F1_M9_UNPROVEN",))
    cursor_epoch = None
    try:
        prepared = manifest.prepare_request(1, manifest.state_root / "attempts/1")
        if unattended_request_digest_v1(prepared) != manifest.bounds.runtime_config_digest:
            raise ValueError("N1_MAC_V2_REQUEST_DIGEST_MISMATCH")
    except (ValueError, RuntimeError, OSError) as exc:
        blocks["request"] = [str(exc)]
    else:
        request = prepared.request
        config = request["config"]
        bound = request["bound"]
        try:
            _require_cap24(config, bound, manifest.bounds.repository_sha, now=now)
        except (ValueError, RuntimeError, OSError) as exc:
            blocks["cap24"] = [str(exc)]
        try:
            cursor_epoch = _require_checkpoint(
                config,
                bound,
                request["occupied_mark_proof_root"],
                manifest.checkpoint,
            )
        except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
            blocks["checkpoint"] = [str(exc)]
    return {
        "ok": not blocks,
        "blockers": blocks,
        "cursor_epoch": cursor_epoch,
        "revision": manifest.bounds.repository_sha,
        "f1_m9": ledgers.to_dict(),
        "runtime_ports_opened": False,
        "external_effect_authorized": False,
    }


def mac_host_service_v2(*, action, manifest_path, output_path=None, clock=time.time):
    manifest = load_mac_host_manifest_v2(manifest_path)
    if action == "prepare":
        if output_path is None:
            raise ValueError("N1_MAC_V2_PLIST_OUTPUT_REQUIRED")
        payload = {
            "Label": LABEL,
            "ProgramArguments": [
                str(REPO / "scripts/pt"),
                "-m",
                "src.ops.n1_mac_host_service_v2",
                "run",
                "--manifest",
                str(manifest_path),
            ],
            "WorkingDirectory": str(REPO),
            "RunAtLoad": False,
            "KeepAlive": False,
            "Umask": 0o077,
            "EnvironmentVariables": {"PEAK_KILL_SWITCH_STATE_PATH": str(manifest.filegate_path)},
        }
        with _canonical_path(output_path).open("xb") as target:
            plistlib.dump(payload, target)
        return {"ok": True, "plist_path": str(output_path), "service_activated": False}
    if action not in {"validate", "run"}:
        raise ValueError("N1_MAC_V2_ACTION_INVALID")
    checks = preflight_mac_host_v2(manifest, clock=clock)
    if action == "validate" or not checks["ok"]:
        return checks
    first_request = True

    def prepare_request(attempt, evidence):
        nonlocal first_request
        if _filegate_revision(manifest.filegate_path) != manifest.filegate_revision:
            raise ValueError("N1_MAC_V2_FILEGATE_REVISION_UNPROVEN")
        prepared = manifest.prepare_request(attempt, evidence)
        if first_request:
            request = prepared.request
            _require_cap24(
                request["config"], request["bound"], manifest.bounds.repository_sha, now=clock()
            )
            _require_checkpoint(
                request["config"],
                request["bound"],
                request["occupied_mark_proof_root"],
                manifest.checkpoint,
            )
            first_request = False
        return prepared

    state = run_occupied_n1_net_reversal_host_v2(
        bounds=manifest.bounds,
        state_root=manifest.state_root,
        request_factory=prepare_request,
        clock=clock,
    )
    return {
        "ok": state["status"] in {"COMPLETED", "BOUNDS_EXHAUSTED", "STOPPED"},
        "host_state": state,
        "external_effect_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "validate", "run"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-path", type=Path)
    args = parser.parse_args()
    try:
        result = mac_host_service_v2(
            action=args.action,
            manifest_path=args.manifest,
            output_path=args.output_path,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        result = {"ok": False, "error": str(exc), "service_activated": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 75


if __name__ == "__main__":
    raise SystemExit(main())
