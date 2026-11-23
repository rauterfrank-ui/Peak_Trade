"""Read the N5 assignment and Cap24 selection for an isolated Shadow entry."""

import json
from decimal import Decimal, DecimalException
from hashlib import sha256
from pathlib import Path

from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    require_i17_shadow_instrument_v1,
)
from src.ops.ranked_slot_run_source_v1 import (
    read_ranked_run_slot_v1,
    read_shadow_entry_admission_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    BINDING_RESULT_FILENAME,
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    OWNER,
    SCHEMA_VERSION,
)
from src.ops.soph_slot_cap24_v1 import _active_binding


def inspect_ranked_shadow_entry_selection_v1(config_path, *, now, session_id=None, assignment=None):
    config = json.loads(Path(config_path).read_bytes())
    current, admission = _selection_context(config, session_id, assignment)
    return _inspect(config, now, current, admission)


def _selection_context(config, session_id, assignment):
    scope = require_i17_shadow_instrument_v1((config["native_instrument_id"],))
    if (
        scope.instrument_type != "SWAP"
        or (config["lane"], config["canonical_instrument_id"], config["surface"])
        != (scope.lane_id, scope.canonical_id, "SHADOW")
        or not config["session_id"]
        or (session_id is not None and config["session_id"] != session_id)
    ):
        raise ValueError("SHADOW_ENTRY_SESSION_SCOPE_MISMATCH")
    current = read_ranked_run_slot_v1(config)
    if assignment is not None and assignment.reference() != current.reference():
        raise ValueError("SHADOW_ENTRY_N5_ASSIGNMENT_CHANGED")
    return current, read_shadow_entry_admission_v1(config, current)


def _inspect(config, now, current, admission):
    ref = current.reference()
    blockers = []
    try:
        admission.require_current_v1(now)
    except ValueError as exc:
        blockers.append(str(exc))
    source = config.get("shadow_cap24")
    result = dict(
        session_id=config["session_id"],
        n5_assignment=ref,
        entry_admission=admission.reference(),
        cap24_evidence_sha256=None,
        blockers=blockers,
    )
    if source is None:
        blockers.append("SHADOW_ENTRY_CAP24_MISSING")
        return result
    try:
        root = Path(source["root"])
        if not root.is_absolute() or root != root.resolve():
            raise ValueError("SHADOW_ENTRY_CAP24_ROOT")
        manifest = (root / MANIFEST_FILENAME).read_bytes()
        files = {k: (root / k).read_bytes() for k in (EVIDENCE_FILENAME, BINDING_RESULT_FILENAME)}
        hashes = {k: sha256(v).hexdigest() for k, v in files.items()}
        if (
            set(manifest.decode().splitlines())
            != {f"{digest}  {name}" for name, digest in hashes.items()}
            or hashes[EVIDENCE_FILENAME] != source["evidence_sha256"]
            or manifest != (root / MANIFEST_FILENAME).read_bytes()
        ):
            raise ValueError("SHADOW_ENTRY_CAP24_MANIFEST_MISMATCH")
        evidence, receipt = (
            json.loads(files[k]) for k in (EVIDENCE_FILENAME, BINDING_RESULT_FILENAME)
        )
        gate = receipt["gate"]
        if (
            canonical_digest_v1(receipt) != source["result_digest"]
            or (receipt["session_id"], receipt["lane"], receipt["n5_assignment"])
            != (config["session_id"], current.lane_id, ref)
            or receipt.get("entry_admission", ref) != admission.reference()
            or gate["evidence"] != evidence
            or (
                evidence["owner"],
                evidence["capability_id"],
                evidence["schema_version"],
                evidence["repository_sha"],
            )
            != (OWNER, CAPABILITY_ID, SCHEMA_VERSION, current.selection.repository_sha)
            or not all(gate[k] is True for k in ("ok", "alpha_enabled", "new_alpha_allowed"))
            or gate["hard_stop"] is not False
        ):
            raise ValueError("SHADOW_ENTRY_CAP24_SCOPE_MISMATCH")
        bound = _active_binding(gate, evidence)
        if (bound.selected_future_count, bound.max_positions_effective) != (1, 1):
            raise ValueError("SHADOW_ENTRY_SINGLE_POSITION_REQUIRED")
        admission.require_binding_v1(bound)
        result["cap24_evidence_sha256"] = hashes[EVIDENCE_FILENAME]
    except (OSError, KeyError, TypeError, ValueError) as exc:
        blockers.append(f"SHADOW_ENTRY_CAP24_INVALID:{exc}")
    return result


def observe_ranked_shadow_positions_v1(state, assignment, *, session_id, now):
    """Read the Shadow owner's base quantities and express positions in native contracts."""
    from src.ops.productive_reconciliation_runtime_binding_v1 import (
        PortfolioTruthSnapshotV1,
        PositionTruthV1,
    )

    instrument = assignment.instrument
    scope = require_i17_shadow_instrument_v1((instrument.venue_native_inst_id,))
    if (
        (state.session_id, state.instrument_id, state.venue_instrument_id, assignment.lane_id)
        != (session_id, scope.canonical_id, scope.native_id, scope.lane_id)
        or instrument.canonical_instrument_id != scope.canonical_id
        or scope.instrument_type != "SWAP"
    ):
        raise ValueError("SHADOW_PORTFOLIO_SCOPE_MISMATCH")
    snapshot = state.portfolio.snapshot()
    if snapshot["orders_submitted"] is not False or snapshot["broker_writes"] is not False:
        raise ValueError("SHADOW_PORTFOLIO_ORIGINAL_REQUIRED")
    rows = snapshot["state"]["positions"]
    if not isinstance(rows, dict):
        raise ValueError("SHADOW_PORTFOLIO_POSITIONS_REQUIRED")
    source = f"SHADOW:{session_id}:{assignment.lane_id}:{canonical_digest_v1(snapshot)}"
    positions = []
    for name, row in rows.items():
        if (name, row["instrument_id"], instrument.contract_value_currency) != (
            scope.canonical_id,
            scope.canonical_id,
            instrument.base_currency,
        ):
            raise ValueError("SHADOW_POSITION_INSTRUMENT_OR_UNIT_MISMATCH")
        try:
            size, lot, base = map(
                Decimal, (instrument.contract_value, instrument.lot_size, row["quantity"])
            )
            if not all(n.is_finite() for n in (size, lot, base)) or min(size, lot) <= 0:
                raise ValueError("SHADOW_POSITION_CONTRACT_UNIT")
            if base % (size * lot):
                raise ValueError("SHADOW_POSITION_OFF_NATIVE_GRID")
            positions.append(
                PositionTruthV1.from_signed(
                    instrument_id=name,
                    signed_quantity=base / size,
                    source_id=source,
                    event_time_unix=now,
                    wall_time_unix=now,
                )
            )
        except DecimalException as exc:
            raise ValueError("SHADOW_POSITION_CONTRACT_UNIT") from exc
    return PortfolioTruthSnapshotV1(
        positions=tuple(positions),
        source_id=source,
        event_time_unix=now,
        wall_time_unix=now,
    )


def resolve_ranked_shadow_entry_selection_v1(
    config_path, *, session_id, assignment, state, market, decision_id, clock, reconciliation_root
):
    """Check the actual analytical position before Cap24. This grants no sizing or fill."""
    from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
        _fresh,
        _one,
    )
    from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
        classify_live_mark_price_freshness_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
        run_single_selected_future_runtime_binding_gate_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.persistence_v1 import (
        persist_binding_evidence_atomic_v1,
    )

    config = json.loads(Path(config_path).read_bytes())
    now = clock()
    current, admission = _selection_context(config, session_id, assignment)
    result = _inspect(config, now, current, admission)
    if result["blockers"] and result["blockers"] != ["SHADOW_ENTRY_CAP24_MISSING"]:
        return result, None
    observed = observe_ranked_shadow_positions_v1(state, current, session_id=session_id, now=now)
    if any(p.signed_quantity != 0 for p in observed.positions):
        return dict(result, blockers=["SHADOW_FIRST_PURCHASE_REQUIRES_FLAT_SLOT"]), None
    if not result["blockers"]:
        return result, admission
    source = config.get("shadow_entry_admission") or config["n5_source"]
    native = admission.instrument.venue_native_inst_id
    response = market.source_observations["mark"]
    row = _one(response.payload, native)
    original = (market.receipt_path.parent / "mark.json").read_bytes()
    mark_receipt = json.loads(market.receipt_path.read_bytes())["mark"]
    checksum = sha256(original).hexdigest()
    if (
        not decision_id
        or (market.canonical_id, market.native_id) != (state.instrument_id, native)
        or original != response.body
        or json.loads(original) != response.payload
        or response.status != 200
        or response.payload.get("code") != "0"
        or row.get("instType") != "SWAP"
        or float(row["markPx"]) != market.mark
        or not market.mark > 0
        or int(row["ts"]) / 1000 != market.market_event_unix
        or checksum != market.source_hashes["mark"]
        or (response.path, mark_receipt)
        != (
            "/api/v5/public/mark-price",
            dict(
                path=response.path,
                query={"instId": native, "instType": "SWAP"},
                sha256=checksum,
                received_at_unix=market.mark_acquired_unix,
            ),
        )
        or admission.selection_root is None
    ):
        raise ValueError("SHADOW_ENTRY_ORIGINAL_MARK_REQUIRED")
    _fresh(row, market.mark_acquired_unix, now, classify_live_mark_price_freshness_v1)
    root = market.receipt_path.parent / "cap24"
    root.mkdir(exist_ok=False)
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=admission.selection_root,
        ranking_state_root=Path(source["ranking_root"]),
        universe_state_root=Path(source["universe_root"]),
        repository_sha=admission.selection.repository_sha,
        session_id=session_id,
        now_unix=now,
        reconciliation_state_root=reconciliation_root,
        observed_portfolio=observed,
        expected_selection_integrity_digest=admission.selection.integrity_digest,
        mark_price_by_native_id={native: row["markPx"]},
    )
    evidence = gate.evidence.to_dict()
    receipt = dict(
        session_id=session_id,
        lane=assignment.lane_id,
        decision_id=decision_id,
        n5_assignment=assignment.reference(),
        entry_admission=admission.reference(),
        observed_portfolio=observed.to_dict(),
        mark_sha256=market.source_hashes["mark"],
        gate=gate.to_dict(),
    )
    persist_binding_evidence_atomic_v1(evidence_root=root, evidence=evidence, result=receipt)
    pointer = dict(
        root=str(root),
        evidence_sha256=sha256((root / EVIDENCE_FILENAME).read_bytes()).hexdigest(),
        result_digest=canonical_digest_v1(receipt),
    )
    if json.loads(Path(config_path).read_bytes()) != config:
        raise ValueError("SHADOW_ENTRY_CONFIG_CHANGED")
    if not gate.ok or not gate.alpha_enabled or gate.hard_stop:
        return dict(
            result,
            blockers=list(gate.blockers) or ["SHADOW_ENTRY_CAP24_DENIED"],
            shadow_cap24=pointer,
        ), None
    current, admission = _selection_context(config, session_id, assignment)
    checked = _inspect(dict(config, shadow_cap24=pointer), clock(), current, admission)
    return dict(checked, shadow_cap24=pointer), (None if checked["blockers"] else admission)
