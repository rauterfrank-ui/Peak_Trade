"""CURRENT_PRODUCTIVE 29P Cap-2.4 bound-instrument provenance handoff v1.

Loads persisted Cap-2.1–2.3 runtime state and invokes
``run_single_selected_future_runtime_binding_gate_v1`` only. No ranking,
no Cap-2.3 reselection, no network, no venue I/O.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_CAP24_PROVENANCE_HANDOFF_CREATED,
    CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_live_account_bound_and_instrument_scope_v1 import (
    require_current_productive_29p_bound_instrument_v1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    assert_handoff_invariants_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import STATE_SELECTED_ACTIVE
from src.ops.single_selected_future_policy_v1.persistence_v1 import (
    load_and_validate_selection_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    CAPABILITY_ID as CAP24_CAPABILITY_ID,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    OWNER as CAP24_AUTHORITY_OWNER,
    SELECTION_AUTHORITY_OWNER as CAP23_AUTHORITY_OWNER,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

EXPECTED_ORIGIN_MAIN_SHA = "8cde3d98fc5869daf43819c262b0ef3b61247454"
THIS_SLICE = "11.2.1.EJ.FULL_CORE_CURRENT_PRODUCTIVE_29P_CAP24_BOUND_INSTRUMENT_PROVENANCE_HANDOFF"
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_29P_CAP24_BOUND_INSTRUMENT_PROVENANCE_HANDOFF_V1"
CONTRACT_VERSION = "v1"
RUNTIME_STATE_DIRNAME = "runtime_state"
MARK_PRICES_FILENAME = "mark_prices_by_native_id_v1.json"
HISTORICAL_EVIDENCE_PREFIXES = (
    ("evidence", "ops"),
    ("docs", "evidence"),
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductive29PCap24ProvenanceHandoffError(RuntimeError):
    """Fail-closed Cap-2.4 provenance handoff violation."""


@dataclass(frozen=True)
class CurrentProductive29PCap24BoundInstrumentProvenanceHandoffV1:
    bound_instrument: BoundInstrumentV1
    selection_id: str
    venue_native_id: str
    instrument_id: str
    cap24_capability_id: str
    cap23_authority_owner: str
    cap24_authority_owner: str
    universe_snapshot_id: str
    ranking_snapshot_id: str
    selection_integrity_digest: str
    ranking_integrity_digest: str
    repository_sha: str
    binding_epoch: str
    runtime_state_root: str
    reselection_performed: bool
    historical_substitution: bool


def default_current_productive_cap24_runtime_state_root_v1() -> Path:
    """Operator-populated CURRENT Cap-2.4 persistence root (not evidence/ops)."""

    return _REPO_ROOT / "runtime" / "current_productive" / "cap24_selection_state"


def _resolve_runtime_state_root_v1(
    *,
    productivity_root: Path,
) -> Path:
    root = Path(productivity_root)
    nested = root / RUNTIME_STATE_DIRNAME
    if nested.is_dir():
        return nested
    if (root / "selection").is_dir() and (root / "universe").is_dir():
        return root
    raise CurrentProductive29PCap24ProvenanceHandoffError("RUNTIME_STATE_LAYOUT_MISSING")


def _assert_not_historical_evidence_runtime_input_v1(path: Path) -> None:
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(_REPO_ROOT.resolve())
    except ValueError:
        return
    parts = rel.parts
    for prefix in HISTORICAL_EVIDENCE_PREFIXES:
        if len(parts) >= len(prefix) and parts[: len(prefix)] == prefix:
            raise CurrentProductive29PCap24ProvenanceHandoffError(
                "HISTORICAL_EVIDENCE_RUNTIME_INPUT_FORBIDDEN"
            )


def _load_mark_prices_v1(*, productivity_root: Path, venue_native_id: str) -> dict[str, str]:
    for candidate in (
        productivity_root / MARK_PRICES_FILENAME,
        productivity_root / RUNTIME_STATE_DIRNAME / MARK_PRICES_FILENAME,
    ):
        if not candidate.is_file():
            continue
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise CurrentProductive29PCap24ProvenanceHandoffError("MARK_PRICES_MALFORMED")
        out = {str(k): str(v) for k, v in payload.items()}
        if venue_native_id not in out or not str(out[venue_native_id]).strip():
            raise CurrentProductive29PCap24ProvenanceHandoffError(
                "MARK_PRICE_MISSING_FOR_SELECTION"
            )
        return out
    raise CurrentProductive29PCap24ProvenanceHandoffError("MARK_PRICES_PROVENANCE_MISSING")


def _binding_epoch_unix_v1(binding_epoch: str) -> float:
    epoch = str(binding_epoch or "").strip()
    if not epoch:
        raise CurrentProductive29PCap24ProvenanceHandoffError("BINDING_EPOCH_MALFORMED")
    try:
        return (
            datetime.strptime(epoch, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        )
    except ValueError as exc:
        raise CurrentProductive29PCap24ProvenanceHandoffError("BINDING_EPOCH_MALFORMED") from exc


def _assert_selection_current_for_epoch_v1(
    *,
    valid_until: str,
    binding_epoch: str,
) -> None:
    until = str(valid_until or "").strip()
    if not until:
        return
    try:
        until_ts = datetime.strptime(until, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        epoch_ts = datetime.strptime(binding_epoch, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise CurrentProductive29PCap24ProvenanceHandoffError(
            "SELECTION_VALIDITY_MALFORMED"
        ) from exc
    if epoch_ts > until_ts:
        raise CurrentProductive29PCap24ProvenanceHandoffError("SELECTION_STALE_FOR_BINDING_EPOCH")


def acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
    *,
    productivity_root: Path | None = None,
    repository_sha: str,
    binding_epoch: str,
    mark_price_by_native_id: Mapping[str, Any] | None = None,
) -> CurrentProductive29PCap24BoundInstrumentProvenanceHandoffV1:
    if CURRENT_PRODUCTIVE_29P_CAP24_PROVENANCE_HANDOFF_CREATED is not True:
        raise CurrentProductive29PCap24ProvenanceHandoffError(
            "CAP24_PROVENANCE_HANDOFF_NOT_CREATED"
        )
    if CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED is not False:
        raise CurrentProductive29PCap24ProvenanceHandoffError(
            "CANARY_INSTRUMENT_AUTHORITY_IMPORTED"
        )
    if MULTI_FUTURE_RUNTIME_AUTHORIZED is not False:
        raise CurrentProductive29PCap24ProvenanceHandoffError(
            "MULTI_FUTURE_RUNTIME_MUST_REMAIN_FALSE"
        )
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductive29PCap24ProvenanceHandoffError("MAX_POSITIONS_NOT_ONE")
    repo_sha = str(repository_sha or "").strip()
    if not repo_sha:
        raise CurrentProductive29PCap24ProvenanceHandoffError("REPOSITORY_SHA_MISSING")

    prod_root = (
        Path(productivity_root)
        if productivity_root is not None
        else default_current_productive_cap24_runtime_state_root_v1()
    )
    _assert_not_historical_evidence_runtime_input_v1(prod_root)
    if not prod_root.exists():
        raise CurrentProductive29PCap24ProvenanceHandoffError("CAP24_RUNTIME_STATE_ROOT_MISSING")

    state_root = _resolve_runtime_state_root_v1(productivity_root=prod_root)
    uni_root = state_root / "universe"
    rank_root = state_root / "ranking"
    sel_root = state_root / "selection"
    recon_root = state_root / "recon"

    sel_load = load_and_validate_selection_v1(
        sel_root,
        expected_repository_sha=None,
        require_manifest=True,
    )
    if sel_load.ok is not True or sel_load.selection is None:
        codes = (
            ",".join(sel_load.failure_codes) if sel_load.failure_codes else "SELECTION_LOAD_FAIL"
        )
        raise CurrentProductive29PCap24ProvenanceHandoffError(
            f"CAP23_SELECTION_LOAD_FAIL_CLOSED:{codes}"
        )
    selection = sel_load.selection
    if selection.repository_sha != repo_sha:
        raise CurrentProductive29PCap24ProvenanceHandoffError("REPOSITORY_SHA_MISMATCH")
    if selection.state != STATE_SELECTED_ACTIVE:
        raise CurrentProductive29PCap24ProvenanceHandoffError("CAP23_SELECTION_NOT_ACTIVE")
    if not str(selection.venue_native_id or "").strip():
        raise CurrentProductive29PCap24ProvenanceHandoffError("CAP23_VENUE_NATIVE_ID_MISSING")
    if str(selection.venue_native_id) == CANARY_DEFAULT_INSTRUMENT_ID:
        raise CurrentProductive29PCap24ProvenanceHandoffError(
            "CANARY_INSTRUMENT_AUTHORITY_IMPORTED"
        )

    rank_load = load_and_validate_ranking_snapshot_v1(
        rank_root,
        expected_repository_sha=None,
        require_manifest=True,
    )
    if rank_load.ok is not True or rank_load.snapshot is None:
        raise CurrentProductive29PCap24ProvenanceHandoffError("CAP22_RANKING_LOAD_FAIL_CLOSED")
    ranking = rank_load.snapshot

    uni_load = load_and_validate_universe_snapshot_v1(
        uni_root,
        expected_repository_sha=None,
        require_manifest=True,
    )
    if uni_load.ok is not True or uni_load.snapshot is None:
        raise CurrentProductive29PCap24ProvenanceHandoffError("CAP21_UNIVERSE_LOAD_FAIL_CLOSED")
    universe = uni_load.snapshot
    if universe.repository_sha != repo_sha:
        raise CurrentProductive29PCap24ProvenanceHandoffError("REPOSITORY_SHA_MISMATCH")

    if selection.ranking_snapshot_id != ranking.ranking_snapshot_id:
        raise CurrentProductive29PCap24ProvenanceHandoffError("RANKING_SNAPSHOT_ID_MISMATCH")
    if selection.ranking_integrity_digest != ranking.integrity_digest:
        raise CurrentProductive29PCap24ProvenanceHandoffError("RANKING_INTEGRITY_MISMATCH")

    _assert_selection_current_for_epoch_v1(
        valid_until=selection.valid_until,
        binding_epoch=binding_epoch,
    )
    now_unix = _binding_epoch_unix_v1(binding_epoch)

    marks = dict(mark_price_by_native_id) if mark_price_by_native_id is not None else None
    if marks is None:
        marks = _load_mark_prices_v1(
            productivity_root=prod_root,
            venue_native_id=str(selection.venue_native_id),
        )

    observed_portfolio = PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=now_unix,
        wall_time_unix=now_unix,
        source_id="current_productive_29p_cap24_provenance_handoff_v1",
    )
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=sel_root,
        ranking_state_root=rank_root,
        universe_state_root=uni_root,
        repository_sha=repo_sha,
        session_id="current-productive-29p-cap24-provenance-handoff",
        now_unix=now_unix,
        reconciliation_state_root=recon_root,
        observed_portfolio=observed_portfolio,
        mark_price_by_native_id=marks,
        expected_selection_config_digest=selection.config_digest,
        expected_selection_integrity_digest=selection.integrity_digest,
        dashboard_available=False,
        dashboard_selected_instrument=None,
        direct_instrument_override=None,
        skip_reconciliation=False,
    )
    bound = gate.bound
    if gate.ok is not True or bound is None or not isinstance(bound, BoundInstrumentV1):
        blockers = ",".join(gate.blockers) if gate.blockers else "CAP24_GATE_FAIL_CLOSED"
        raise CurrentProductive29PCap24ProvenanceHandoffError(f"CAP24_BIND_FAIL_CLOSED:{blockers}")

    assert_handoff_invariants_v1(
        selection,
        bound,
        ranking_snapshot_id=ranking.ranking_snapshot_id,
        ranking_universe_snapshot_id=universe.snapshot_id,
        universe_snapshot_id=universe.snapshot_id,
    )
    bound = require_current_productive_29p_bound_instrument_v1(bound)

    return CurrentProductive29PCap24BoundInstrumentProvenanceHandoffV1(
        bound_instrument=bound,
        selection_id=bound.selection_id,
        venue_native_id=bound.venue_native_id,
        instrument_id=bound.instrument_id,
        cap24_capability_id=CAP24_CAPABILITY_ID,
        cap23_authority_owner=CAP23_AUTHORITY_OWNER,
        cap24_authority_owner=CAP24_AUTHORITY_OWNER,
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        selection_integrity_digest=bound.selection_integrity_digest,
        ranking_integrity_digest=bound.ranking_integrity_digest,
        repository_sha=repo_sha,
        binding_epoch=binding_epoch,
        runtime_state_root=str(state_root),
        reselection_performed=False,
        historical_substitution=False,
    )


def resolve_current_productive_29p_cap24_bound_instrument_for_common_epoch_v1(
    *,
    bound_instrument: BoundInstrumentV1 | None,
    cap24_productivity_root: Path | None,
    repository_sha: str,
    binding_epoch: str,
) -> BoundInstrumentV1 | None:
    """Resolve Cap-2.4 instance for common-epoch compose (no manual instrument id)."""

    if bound_instrument is not None:
        return require_current_productive_29p_bound_instrument_v1(bound_instrument)
    root = cap24_productivity_root
    if root is None:
        default = default_current_productive_cap24_runtime_state_root_v1()
        if not default.exists():
            return None
        root = default
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=root,
        repository_sha=repository_sha,
        binding_epoch=binding_epoch,
    )
    return handoff.bound_instrument
