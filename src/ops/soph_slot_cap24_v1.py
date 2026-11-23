"""Carry the original N5 Cap24 result for SOPH's assigned lane into shadow reads."""

import json
import logging
import re
from contextlib import ExitStack
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    load_completed_selection_publication_v1,
    load_pending_selection_publication_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import lane_state_root_for
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    SOPH_I17,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
    SCHEMA_VERSION,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


def _source(topology_root, selection):
    root = lane_state_root_for(topology_state_root_base=topology_root, lane_id=SOPH_I17.lane_id)
    if not re.fullmatch(r"[0-9a-f]{64}", selection.integrity_digest):
        raise ValueError("SOPH_SLOT_CAP24_SELECTION_DIGEST_INVALID")
    path = Path(root) / "soph_slot_cap24_v1" / (selection.integrity_digest + ".json")
    identity = dict(
        schema="soph_slot_cap24.v1",
        lane_id=SOPH_I17.lane_id,
        lane_state_root=root,
        repository_sha=selection.repository_sha,
        selection_id=selection.selection_id,
        selection_integrity_digest=selection.integrity_digest,
        instrument_id=selection.instrument_id,
        venue_native_id=selection.venue_native_id,
    )
    return path, identity


def evaluate_assigned_lane_gate_v1(gate, *, lane_id, selection, topology_root, **inputs):
    """Run the original gate once and retain its result for a published SOPH slot."""
    if (lane_id, selection.instrument_id, selection.venue_native_id) != (
        SOPH_I17.lane_id,
        SOPH_I17.canonical_id,
        SOPH_I17.native_id,
    ):
        return gate(**inputs)

    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
        durable_bytes_v1,
        exclusive_v1,
        immutable_json_v1,
    )

    path, identity = _source(topology_root, selection)
    if (
        Path(inputs["selection_state_root"]).resolve() != Path(identity["lane_state_root"])
        or inputs["expected_selection_integrity_digest"] != selection.integrity_digest
        or inputs["repository_sha"] != selection.repository_sha
    ):
        raise ValueError("SOPH_SLOT_CAP24_REFERENCE_MISMATCH")

    def publish(status, result, publication_digest):
        body = dict(
            identity,
            status=status,
            session_id=inputs["session_id"],
            checked_at_unix=inputs["now_unix"],
            publication_digest=publication_digest,
            gate=result,
        )
        digest = canonical_digest_v1(body)
        if status == "COMPLETED":
            immutable_json_v1(path.parent / "receipts" / (digest + ".json"), body)
        record = dict(body=body, sha256=digest)
        durable_bytes_v1(path, json.dumps(record, sort_keys=True, allow_nan=False).encode())

    with ExitStack() as locks:
        try:
            locks.enter_context(exclusive_v1(path.with_suffix(".lock")))
            publication = load_completed_selection_publication_v1(topology_root)
            assigned = (
                publication is not None
                and publication["selection_digests"].get(lane_id) == selection.integrity_digest
                and load_pending_selection_publication_v1(topology_root) is None
            )
            if assigned:
                publish("PENDING", None, publication["receipt_digest"])
        except (OSError, ValueError, RuntimeError) as exc:
            # The lane cannot begin a new checked bind. Other lanes can still bind.
            logging.getLogger(__name__).warning("SOPH_SLOT_CAP24_RECEIPT_UNAVAILABLE: %s", exc)
            return None
        result = gate(**inputs)
        if assigned:
            try:
                if (
                    load_completed_selection_publication_v1(topology_root) == publication
                    and load_pending_selection_publication_v1(topology_root) is None
                ):
                    publish("COMPLETED", result.to_dict(), publication["receipt_digest"])
            except (OSError, ValueError, RuntimeError) as exc:
                # The pending marker denies a shadow entry even if the original bind succeeded.
                logging.getLogger(__name__).warning("SOPH_SLOT_CAP24_RECEIPT_INCOMPLETE: %s", exc)
        return result


@dataclass(frozen=True)
class SophSlotCap24V1:
    status: str
    digest: str | None = None
    checked_at_unix: float | None = None
    bound: BoundInstrumentV1 | None = None


def _active_binding(gate, evidence):
    bound = BoundInstrumentV1(**gate["bound"])
    recon = gate["reconciliation_result"]
    if (
        bound.to_dict() != evidence["bound"]
        or gate["bound"] != evidence["bound"]
        or gate["selection_state"] != "SELECTED_ACTIVE"
        or bound.selection_state != "SELECTED_ACTIVE"
        or gate["blockers"] != []
        or evidence["failure_codes"] != []
        or not all(
            evidence[k] is True
            for k in (
                "ok",
                "new_alpha_allowed",
                "alpha_enabled",
                "reconciliation_before_alpha",
                "reconciliation_alpha_enabled",
            )
        )
        or evidence["hard_stop"] is not False
        or any(
            evidence[k] != getattr(bound, k)
            for k in (
                "selection_state",
                "selection_id",
                "selection_integrity_digest",
                "instrument_id",
                "venue_native_id",
                "ranking_snapshot_id",
                "ranking_integrity_digest",
                "universe_snapshot_id",
            )
        )
        or recon["ok"] is not True
        or recon["alpha_enabled"] is not True
        or recon["hard_stop"] is not False
        or recon["blockers"] != []
        or not re.fullmatch(r"[0-9a-f]{64}", recon["evidence_digest"])
    ):
        raise ValueError("SOPH_SLOT_CAP24_ENTRY_EVIDENCE_MISMATCH")
    return bound


def read_soph_slot_cap24_v1(topology_root, selection, *, publication_digest, retained):
    path, identity = _source(topology_root, selection)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return SophSlotCap24V1("MISSING")
    try:
        record = json.loads(raw)
        body, digest = record["body"], record["sha256"]
        checked = body["checked_at_unix"]
        if (
            canonical_digest_v1(body) != digest
            or any(body[k] != value for k, value in identity.items())
            or not re.fullmatch(r"[0-9a-f]{64}", body["publication_digest"])
            or type(checked) not in (int, float)
            or not isfinite(checked)
            or not isinstance(body["session_id"], str)
            or not body["session_id"]
        ):
            raise ValueError("SOPH_SLOT_CAP24_REFERENCE_MISMATCH")
        if not retained and body["publication_digest"] != publication_digest:
            return SophSlotCap24V1("SUPERSEDED", digest, checked)
        gate = body["gate"]
        if body["status"] == "PENDING" and gate is None:
            return SophSlotCap24V1("PENDING", digest, checked)
        if body["status"] != "COMPLETED":
            raise ValueError("SOPH_SLOT_CAP24_RECORD_INVALID")
        evidence = gate["evidence"]
        if (
            evidence["capability_id"] != CAPABILITY_ID
            or evidence["schema_version"] != SCHEMA_VERSION
            or evidence["owner"] != OWNER
            or evidence["repository_sha"] != selection.repository_sha
        ):
            raise ValueError("SOPH_SLOT_CAP24_OWNER_MISMATCH")
        if (
            not all(gate[k] is True for k in ("ok", "alpha_enabled", "new_alpha_allowed"))
            or gate["hard_stop"] is not False
        ):
            return SophSlotCap24V1("ENTRY_BLOCKED", digest, checked)
        bound = _active_binding(gate, evidence)
        retained = path.parent / "receipts" / (digest + ".json")
        if (
            not retained.is_file()
            or canonical_digest_v1(json.loads(retained.read_bytes())) != digest
        ):
            raise ValueError("SOPH_SLOT_CAP24_ORIGINAL_RECEIPT_REQUIRED")
        if path.read_bytes() != raw:
            raise ValueError("SOPH_SLOT_CAP24_CHANGED_DURING_READ")
        return SophSlotCap24V1("ACTIVE", digest, checked, bound)
    except (KeyError, TypeError, AttributeError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("SOPH_SLOT_CAP24_RECORD_INVALID") from exc
