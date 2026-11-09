"""Seal one simulated episode at explicit observed flat; retain all old roots.

Not order acknowledgement, global custody release, capital release or Outcome
completion. A successor uses new roots and an extended original fill journal.
"""

import base64
from copy import deepcopy
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace

from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    EXIT_STATE_FILENAME,
    COMMIT_MARKER_FILENAME,
    MANIFEST_FILENAME,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import IDENTITY_FILENAME
from src.ops.exit_policy_producer_binding_v1.models_v1 import (
    CanonicalExitPolicyStateV1,
    canonical_digest_v1,
)
from src.ops.exit_policy_producer_binding_v1.persistence_v1 import load_exit_policy_state_v1
from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
    require_current_cursor_continuity_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
    _source,
    _same_accounting_domain,
    verify_simulated_accounting_progress_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    FLAT_SCHEMA,
    _verify,
    _load_source,
    _retain_payload_v1,
    _archive_verified_source_v1,
    create_position_episode_from_simulated_accounting_v1,
    require_economic_history_extension_v1,
    latest_economic_event_time_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.position_truth_v1 import (
    resolve_per_lane_position_truth_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.reconciliation_admission_v1 import (
    build_per_lane_reconciliation_admission_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
    restore_current_productive_sidestate_confirmation_cursor_v1,
)

SCHEMA = "simulated_accounting_episode_close.v1"


def _reference(schema, path, digest):
    return f"{schema}:{digest}:{Path(path).resolve()}"


def _read_reference(ref, schema):
    parts = ref.split(":", 2) if isinstance(ref, str) else []
    if len(parts) != 3 or parts[0] != schema or not re.fullmatch("[0-9a-f]{64}", parts[1]):
        raise ValueError("SIMULATED_CLOSE_REFERENCE_INVALID")
    path = Path(parts[2])
    if not path.is_absolute() or str(path.resolve()) != parts[2]:
        raise ValueError("SIMULATED_CLOSE_REFERENCE_PATH_INVALID")
    return path, parts[1]


def _flat_observation(identity, bound, occupancy, portfolio, observed_unix, close_time):
    if not isinstance(bound, BoundInstrumentV1) or (
        bound.instrument_id != identity.instrument_id
        or bound.venue_native_id != identity.venue_native_id
    ):
        raise ValueError("SIMULATED_CLOSE_BOUND_INSTRUMENT_MISMATCH")
    for key in ("POSITIONS", "PENDING"):
        raw = occupancy.get(key) if isinstance(occupancy, dict) else None
        if (
            not isinstance(raw, dict)
            or str(raw.get("code")) != "0"
            or not isinstance(raw.get("data"), list)
        ):
            raise ValueError("SIMULATED_CLOSE_EXPLICIT_OBSERVATION_REQUIRED")
    rows = occupancy["POSITIONS"]["data"]
    matched = [
        r for r in rows if isinstance(r, dict) and r.get("instId") == identity.venue_native_id
    ]
    if len(matched) != 1 or isinstance(matched[0].get("pos"), bool):
        raise ValueError("SIMULATED_CLOSE_EXPLICIT_ZERO_ROW_REQUIRED")
    try:
        quantity = Decimal(str(matched[0].get("pos")))
    except InvalidOperation as exc:
        raise ValueError("SIMULATED_CLOSE_EXPLICIT_ZERO_ROW_REQUIRED") from exc
    if not quantity.is_finite() or quantity != 0 or occupancy["PENDING"]["data"]:
        raise ValueError("SIMULATED_CLOSE_POSITION_OR_PENDING_UNRESOLVED")
    if not isinstance(portfolio, PortfolioTruthSnapshotV1) or any(
        type(v) is not bool or v
        for v in (
            portfolio.missing,
            portfolio.stale,
            portfolio.duplicate,
            portfolio.writer_conflict,
        )
    ):
        raise ValueError("SIMULATED_CLOSE_PORTFOLIO_UNPROVEN")
    times = (
        close_time,
        portfolio.event_time_unix,
        portfolio.wall_time_unix,
        observed_unix,
        portfolio.max_age_seconds,
    )
    if any(type(t) not in (int, float) or not math.isfinite(t) or t <= 0 for t in times) or not (
        close_time <= portfolio.event_time_unix <= portfolio.wall_time_unix <= observed_unix
        and observed_unix - portfolio.event_time_unix <= portfolio.max_age_seconds
    ):
        raise ValueError("SIMULATED_CLOSE_OBSERVATION_TIME_UNPROVEN")
    positions = [p for p in portfolio.positions if p.instrument_id == identity.instrument_id]
    if len(positions) != 1 or any(
        not isinstance(p.signed_quantity, Decimal)
        or not p.signed_quantity.is_finite()
        or p.signed_quantity != 0
        or p.side != "FLAT"
        for p in portfolio.positions
    ):
        raise ValueError("SIMULATED_CLOSE_EXPLICIT_PORTFOLIO_FLAT_REQUIRED")
    lane_identity = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id=identity.lane_id, bound=bound
    )
    truth = resolve_per_lane_position_truth_v1(
        identity=lane_identity, occupancy_payloads=occupancy, allow_global_fallback=False
    )
    admitted = build_per_lane_reconciliation_admission_v1(
        identity=lane_identity, portfolio=portfolio
    )
    if not truth.venue_flat or not admitted.admitted:
        raise ValueError("SIMULATED_CLOSE_RECONCILIATION_REQUIRED")


def _closed_state(prior, ref):
    result = deepcopy(prior)
    result.update(
        has_open_position=False,
        existing_position_side="none",
        entry_price=None,
        entry_event_time=None,
        entry_trading_epoch=None,
        pending_exit_class="",
        pending_exit_reason="",
        pending_exit_identity="",
        last_exit_intent_identity="",
        commit_sequence=prior["commit_sequence"] + 1,
    )
    result.pop("current_cursor_publication", None)
    result.pop("simulated_accounting_progress", None)
    result["simulated_accounting_close"] = {"schema": SCHEMA, "closure_ref": ref}
    return result


def seal_simulated_accounting_episode_flat_v1(
    *,
    episode,
    accounting_session,
    fills,
    bound,
    occupancy_payloads,
    observed_portfolio,
    observed_unix,
    expected_scope,
    source_archive_root,
    cursor_store_root,
    writer_session_id,
):
    occupancy_payloads = deepcopy(occupancy_payloads)
    observed_portfolio = deepcopy(observed_portfolio)
    if episode.identity.account_scope != expected_scope or episode.binding.alpha_blocked:
        raise ValueError("SIMULATED_CLOSE_SCOPE_OR_HANDLE_MISMATCH")
    state = load_exit_policy_state_v1(
        Path(episode.binding.state_root),
        expected_repository_sha=episode.binding.repository_sha,
        expected_config_digest=episode.binding.config_digest,
        expected_instrument_id=episode.identity.instrument_id,
    )
    if (
        state.to_dict() != episode.binding.to_canonical_state().to_dict()
        or not state.has_open_position
    ):
        raise ValueError("SIMULATED_CLOSE_STALE_OR_CLOSED_HANDLE")
    if episode.binding.simulated_accounting_progress is None:
        old, _ = _source(episode.entry_source_ref, episode.identity)
    else:
        old = verify_simulated_accounting_progress_v1(episode)["payload"]
    payload, anchors = _verify(
        identity=episode.identity, session=accounting_session, fills=fills, closed=True
    )
    _same_accounting_domain(old, payload)
    if (
        len(payload["fills"]) <= len(old["fills"])
        or payload["fills"][: len(old["fills"])] != old["fills"]
    ):
        raise ValueError("SIMULATED_CLOSE_HISTORY_REWRITE")
    require_economic_history_extension_v1(old, payload)
    if any(r["event_time_unix"] is None for r in payload["fills"][len(old["fills"]) :]):
        raise ValueError("SIMULATED_CLOSE_NEW_FILL_TIME_REQUIRED")
    _flat_observation(
        episode.identity,
        bound,
        occupancy_payloads,
        observed_portfolio,
        observed_unix,
        latest_economic_event_time_v1(payload)
        if payload["accounting_checkpoint"]["funding_events"]
        else anchors["close_event_time"],
    )
    cursor_root = Path(cursor_store_root)
    if not cursor_root.is_absolute():
        raise ValueError("SIMULATED_CLOSE_ABSOLUTE_CURSOR_ROOT_REQUIRED")
    incoming = load_current_productive_sidestate_confirmation_cursor_v1(cursor_root)
    restored = restore_current_productive_sidestate_confirmation_cursor_v1(
        incoming,
        expected_instrument_id=episode.identity.instrument_id,
        expected_venue_native_id=episode.identity.venue_native_id,
        venue_flat=False,
    )
    if restored.disposition.value != "restored" or restored.cursor.existing_scope is None:
        raise ValueError("SIMULATED_CLOSE_PRIOR_SCOPE_CURSOR_REQUIRED")
    require_current_cursor_continuity_v1(episode=episode, incoming=incoming, store_root=cursor_root)
    source_path, source_digest = _archive_verified_source_v1(
        payload=payload,
        anchors=anchors,
        identity=episode.identity,
        source_archive_root=source_archive_root,
        closed=True,
    )
    prior_files = {}
    for name in (EXIT_STATE_FILENAME, COMMIT_MARKER_FILENAME, MANIFEST_FILENAME, IDENTITY_FILENAME):
        data = (Path(episode.binding.state_root) / name).read_bytes()
        prior_files[name] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "base64": base64.b64encode(data).decode(),
        }
    closure = {
        "schema": SCHEMA,
        "identity": asdict(episode.identity),
        "initial_source_ref": episode.entry_source_ref,
        "flat_source_ref": _reference(FLAT_SCHEMA, source_path, source_digest),
        "prior_exit_state": state.to_dict(),
        "prior_owner_files": prior_files,
        "bound_instrument": bound.to_dict(),
        "occupancy_payloads": occupancy_payloads,
        "portfolio": observed_portfolio.to_dict(),
        "observed_unix": observed_unix,
        "cursor_root": str(cursor_root.resolve()),
        "resolution": "OBSERVED_SIMULATED_FLAT_NOT_ORDER_ACK",
    }
    archive_path, digest = _retain_payload_v1(
        payload=closure, source_archive_root=source_archive_root
    )
    ref = _reference(SCHEMA, archive_path, digest)
    evaluated = deepcopy(episode.binding)
    evaluated.last_bundle = {}
    updated = CanonicalExitPolicyStateV1.from_dict(_closed_state(state.to_dict(), ref))
    for name in updated.__dataclass_fields__:
        if hasattr(evaluated, name):
            setattr(evaluated, name, deepcopy(getattr(updated, name)))
    evaluated.commit_sequence = state.commit_sequence  # original writer advances once
    episode._persist_checked_generation_v1(evaluated, writer_session_id=writer_session_id)
    return inspect_sealed_simulated_episode_v1(
        identity=episode.identity,
        state_root=Path(episode.binding.state_root),
        repository_sha=episode.binding.repository_sha,
        config_digest=episode.binding.config_digest,
        expected_initial_source_ref=episode.entry_source_ref,
    )


def inspect_sealed_simulated_episode_v1(
    *, identity, state_root, repository_sha, config_digest, expected_initial_source_ref
):
    state = load_exit_policy_state_v1(
        Path(state_root),
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        expected_instrument_id=identity.instrument_id,
    )
    record = state.simulated_accounting_close
    if (
        not isinstance(record, dict)
        or set(record) != {"schema", "closure_ref"}
        or record["schema"] != SCHEMA
    ):
        raise ValueError("SIMULATED_CLOSE_SEAL_REQUIRED")
    path, digest = _read_reference(record["closure_ref"], SCHEMA)
    envelope = json.loads(path.read_text())
    payload = envelope["payload"]
    if (
        set(envelope) != {"payload", "content_digest"}
        or envelope["content_digest"] != digest
        or canonical_digest_v1(payload) != digest
    ):
        raise ValueError("SIMULATED_CLOSE_SEAL_DIGEST_MISMATCH")
    if (
        payload["schema"] != SCHEMA
        or payload["identity"] != asdict(identity)
        or payload["initial_source_ref"] != expected_initial_source_ref
    ):
        raise ValueError("SIMULATED_CLOSE_SEAL_IDENTITY_MISMATCH")
    if (
        set(payload)
        != {
            "schema",
            "identity",
            "initial_source_ref",
            "flat_source_ref",
            "prior_exit_state",
            "prior_owner_files",
            "bound_instrument",
            "occupancy_payloads",
            "portfolio",
            "observed_unix",
            "cursor_root",
            "resolution",
        }
        or payload["resolution"] != "OBSERVED_SIMULATED_FLAT_NOT_ORDER_ACK"
    ):
        raise ValueError("SIMULATED_CLOSE_SEAL_SCHEMA_MISMATCH")
    flat_path, flat_digest = _read_reference(payload["flat_source_ref"], FLAT_SCHEMA)
    actual, anchors, flat = _load_source(flat_path, identity, closed=True, include_payload=True)
    if actual != flat_digest or state.to_dict() != _closed_state(
        payload["prior_exit_state"], record["closure_ref"]
    ):
        raise ValueError("SIMULATED_CLOSE_SEAL_STATE_MISMATCH")
    if set(payload["prior_owner_files"]) != {
        EXIT_STATE_FILENAME,
        COMMIT_MARKER_FILENAME,
        MANIFEST_FILENAME,
        IDENTITY_FILENAME,
    }:
        raise ValueError("SIMULATED_CLOSE_RETAINED_FILES_MISSING")
    retained = {}
    for name, item in payload["prior_owner_files"].items():
        data = base64.b64decode(item["base64"], validate=True)
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("SIMULATED_CLOSE_RETAINED_BYTES_MISMATCH")
        if name == IDENTITY_FILENAME and data != (Path(state_root) / name).read_bytes():
            raise ValueError("SIMULATED_CLOSE_IMMUTABLE_IDENTITY_CHANGED")
        retained[name] = data
    raw_prior = json.loads(retained[EXIT_STATE_FILENAME])
    prior = CanonicalExitPolicyStateV1.from_dict(raw_prior)
    if (
        prior.to_dict() != payload["prior_exit_state"]
        or not prior.has_open_position
        or prior.existing_position_side != identity.position_side
    ):
        raise ValueError("SIMULATED_CLOSE_RETAINED_STATE_MISMATCH")
    marker = json.loads(retained[COMMIT_MARKER_FILENAME])
    if marker != {
        "commit_sequence": prior.commit_sequence,
        "state_digest": canonical_digest_v1(raw_prior),
        "instrument_id": identity.instrument_id,
        "owner": prior.owner,
    }:
        raise ValueError("SIMULATED_CLOSE_RETAINED_MARKER_MISMATCH")
    manifest = retained[MANIFEST_FILENAME].decode().splitlines()
    expected = {
        f"{hashlib.sha256(retained[n]).hexdigest()}  {n}"
        for n in (EXIT_STATE_FILENAME, COMMIT_MARKER_FILENAME)
    }
    if len(manifest) != 2 or set(manifest) != expected:
        raise ValueError("SIMULATED_CLOSE_RETAINED_MANIFEST_MISMATCH")
    old, old_anchors = _source(expected_initial_source_ref, identity)
    if prior.simulated_accounting_progress is not None:
        old = verify_simulated_accounting_progress_v1(
            SimpleNamespace(
                identity=identity, binding=prior, entry_source_ref=expected_initial_source_ref
            )
        )["payload"]
    elif any(
        getattr(prior, k) != old_anchors[k]
        for k in ("entry_price", "entry_event_time", "entry_trading_epoch")
    ):
        raise ValueError("SIMULATED_CLOSE_RETAINED_ANCHOR_MISMATCH")
    _same_accounting_domain(old, flat)
    require_economic_history_extension_v1(old, flat)
    if (
        len(flat["fills"]) <= len(old["fills"])
        or flat["fills"][: len(old["fills"])] != old["fills"]
    ):
        raise ValueError("SIMULATED_CLOSE_RETAINED_HISTORY_MISMATCH")
    portfolio = dict(payload["portfolio"])
    portfolio["cash"] = None if portfolio["cash"] is None else Decimal(portfolio["cash"])
    positions = []
    for raw in portfolio["positions"]:
        position = dict(raw)
        position["signed_quantity"] = Decimal(position["signed_quantity"])
        position["mark_price"] = (
            None if position["mark_price"] is None else Decimal(position["mark_price"])
        )
        positions.append(PositionTruthV1(**position))
    portfolio["positions"] = tuple(positions)
    _flat_observation(
        identity,
        BoundInstrumentV1(**payload["bound_instrument"]),
        payload["occupancy_payloads"],
        PortfolioTruthSnapshotV1(**portfolio),
        payload["observed_unix"],
        latest_economic_event_time_v1(flat)
        if flat["accounting_checkpoint"]["funding_events"]
        else anchors["close_event_time"],
    )
    return {
        "status": "SEALED",
        "closure_ref": record["closure_ref"],
        "close_event_time": anchors["close_event_time"],
        "source_payload": flat,
        "retained_cursor_root": payload["cursor_root"],
    }


def create_successor_after_sealed_simulated_episode_v1(
    *,
    prior_identity,
    prior_state_root,
    prior_repository_sha,
    prior_config_digest,
    prior_initial_source_ref,
    identity,
    accounting_session,
    fills,
    source_archive_root,
    state_root,
    repository_sha,
    config_digest,
    writer_session_id,
):
    sealed = inspect_sealed_simulated_episode_v1(
        identity=prior_identity,
        state_root=prior_state_root,
        repository_sha=prior_repository_sha,
        config_digest=prior_config_digest,
        expected_initial_source_ref=prior_initial_source_ref,
    )
    if (
        any(
            getattr(identity, k) != getattr(prior_identity, k)
            for k in ("account_scope", "lane_id", "instrument_id", "venue_native_id")
        )
        or identity.episode_id == prior_identity.episode_id
    ):
        raise ValueError("SIMULATED_CLOSE_SUCCESSOR_IDENTITY_INVALID")
    payload, _ = _verify(identity=identity, session=accounting_session, fills=fills)
    old = sealed["source_payload"]
    _same_accounting_domain(old, payload)
    require_economic_history_extension_v1(old, payload)
    if (
        len(payload["fills"]) <= len(old["fills"])
        or payload["fills"][: len(old["fills"])] != old["fills"]
    ):
        raise ValueError("SIMULATED_CLOSE_SUCCESSOR_HISTORY_REWRITE")
    old_roots = (Path(prior_state_root).resolve(), Path(sealed["retained_cursor_root"]).resolve())
    if any(
        Path(value).resolve() == old or old in Path(value).resolve().parents
        for value in (state_root, source_archive_root)
        for old in old_roots
    ):
        raise ValueError("SIMULATED_CLOSE_SUCCESSOR_NEW_ROOT_REQUIRED")
    return create_position_episode_from_simulated_accounting_v1(
        identity=identity,
        session=accounting_session,
        fills=fills,
        source_archive_root=source_archive_root,
        state_root=state_root,
        repository_sha=repository_sha,
        config_digest=config_digest,
        writer_session_id=writer_session_id,
    )
