"""Read-only dashboard loader for universe_selection_readmodel.v1 (Slice 3 — no writes)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .types import (
    MarketSnapshotDisplayV1,
    SelectedFutureDisplayV1,
    UniverseSelectionDashboardSliceV1,
    UniverseSelectionRowDisplayV1,
)
from .universe_selection_contract_v1 import (
    STORAGE_RELATIVE_PATH,
    UniverseSelectionContractError,
    UniverseSelectionContractV1,
    UniverseSelectionRowV1,
    validate_universe_selection_payload,
)
from .universe_selection_producer_v1 import (
    MANIFEST_FILENAME,
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
)

LOAD_ERROR_MANIFEST_NOT_FOUND = "MANIFEST_NOT_FOUND"
LOAD_ERROR_MANIFEST_VERIFY_FAILED = "MANIFEST_VERIFY_FAILED"
LOAD_ERROR_INVALID_JSON = "INVALID_JSON"
LOAD_ERROR_CONTRACT_INVALID = "CONTRACT_INVALID"
LOAD_ERROR_FIXTURE_MARKED_NOT_OBSERVABILITY_TRUTH = "FIXTURE_MARKED_NOT_OBSERVABILITY_TRUTH"
LOAD_ERROR_REAL_METADATA_NOT_OBSERVABILITY_TRUTH = "REAL_METADATA_NOT_OBSERVABILITY_TRUTH"
LOAD_ERROR_NOT_CVC_PROJECTION = "NOT_CVC_PROJECTION"
LOAD_ERROR_PROJECTION_NOT_CVC_ONLY = "PROJECTION_NOT_CVC_ONLY"
LOAD_ERROR_SELECTED_FUTURE_PERSISTED_NOT_PROJECTION = "SELECTED_FUTURE_PERSISTED_NOT_PROJECTION"
LOAD_ERROR_NON_AUTHORIZING_REQUIRED = "NON_AUTHORIZING_REQUIRED"

PROJECTION_COVERAGE_LOAD_MODE = "projection_coverage"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _import_verify_manifest() -> Any:
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    return verify_manifest_sha256


def _empty_slice(*, load_errors: tuple[str, ...]) -> UniverseSelectionDashboardSliceV1:
    return UniverseSelectionDashboardSliceV1(loaded=False, load_errors=load_errors)


def _normalize_evidence_links(evidence: dict[str, Any]) -> tuple[str, ...]:
    raw_links = evidence.get("links")
    if not isinstance(raw_links, list):
        return ()
    out: list[str] = []
    for item in raw_links:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, dict):
            path = item.get("path")
            label = item.get("label")
            if isinstance(path, str) and path.strip():
                text = path.strip()
                if isinstance(label, str) and label.strip():
                    text = f"{label.strip()}: {text}"
                out.append(text)
    return tuple(out)


def _row_display(row: UniverseSelectionRowV1) -> UniverseSelectionRowDisplayV1:
    return UniverseSelectionRowDisplayV1(
        row_id=row.row_id,
        symbol=row.symbol,
        rank=row.rank,
        exchange=row.exchange,
        display_score=row.display_score,
        notes=row.notes,
    )


def _contract_to_slice(
    contract: UniverseSelectionContractV1,
    *,
    load_mode: str | None = None,
) -> UniverseSelectionDashboardSliceV1:
    selected = None
    if contract.selected_future is not None:
        sf = contract.selected_future
        selected = SelectedFutureDisplayV1(
            row_id=sf.row_id,
            symbol=sf.symbol,
            rank=sf.rank,
            truth_status=sf.truth_status,
            selection_reason=sf.selection_reason,
            notes=sf.notes,
        )
    snapshot_raw = contract.market_snapshot
    market_snapshot = MarketSnapshotDisplayV1(
        truth_status=str(snapshot_raw.get("truth_status", "NOT_PERSISTED")),
        source_kind=(
            str(snapshot_raw["source_kind"])
            if isinstance(snapshot_raw.get("source_kind"), str)
            else None
        ),
        snapshot_id=(
            str(snapshot_raw["snapshot_id"])
            if isinstance(snapshot_raw.get("snapshot_id"), str)
            else None
        ),
        exchange=(
            str(snapshot_raw["exchange"]) if isinstance(snapshot_raw.get("exchange"), str) else None
        ),
        captured_at=(
            str(snapshot_raw["captured_at"])
            if isinstance(snapshot_raw.get("captured_at"), str)
            else None
        ),
    )
    return UniverseSelectionDashboardSliceV1(
        loaded=True,
        load_errors=(),
        source_run_id=contract.source_run_id,
        source_stage=contract.source_stage,
        generated_at=contract.generated_at,
        universe=tuple(_row_display(row) for row in contract.universe),
        ranking=tuple(_row_display(row) for row in contract.ranking),
        selected_future=selected,
        market_snapshot=market_snapshot,
        evidence_links=_normalize_evidence_links(contract.evidence),
        load_mode=load_mode,
    )


def _load_manifest_verified_readmodel(
    archive_root: str | Path,
) -> UniverseSelectionDashboardSliceV1 | tuple[dict[str, Any], UniverseSelectionContractV1]:
    """Shared verify-before-trust load path (read-only, no writes)."""
    root = Path(archive_root).expanduser().resolve()
    readmodels_dir = root / READMODELS_DIRNAME
    readmodel_path = readmodels_dir / READMODEL_FILENAME

    if not readmodel_path.is_file():
        return _empty_slice(load_errors=())

    manifest_path = readmodels_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return _empty_slice(load_errors=(LOAD_ERROR_MANIFEST_NOT_FOUND,))

    verify_manifest_sha256 = _import_verify_manifest()
    verify_ok, _ = verify_manifest_sha256(readmodels_dir)
    if not verify_ok:
        return _empty_slice(load_errors=(LOAD_ERROR_MANIFEST_VERIFY_FAILED,))

    try:
        raw = readmodel_path.read_text(encoding="utf-8")
    except OSError:
        return _empty_slice(load_errors=(LOAD_ERROR_CONTRACT_INVALID,))

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return _empty_slice(load_errors=(LOAD_ERROR_INVALID_JSON,))

    if not isinstance(payload, dict):
        return _empty_slice(load_errors=(LOAD_ERROR_INVALID_JSON,))

    try:
        contract = validate_universe_selection_payload(payload)
    except UniverseSelectionContractError:
        return _empty_slice(load_errors=(LOAD_ERROR_CONTRACT_INVALID,))

    return payload, contract


def _selected_future_persisted_in_payload(payload: dict[str, Any]) -> bool:
    selected_raw = payload.get("selected_future")
    if not isinstance(selected_raw, dict):
        return False
    truth_status = selected_raw.get("truth_status")
    if truth_status == "PERSISTED":
        return True
    if isinstance(selected_raw.get("symbol"), str) and selected_raw.get("symbol").strip():
        return True
    return False


def try_load_universe_selection_for_dashboard(
    archive_root: str | Path,
) -> UniverseSelectionDashboardSliceV1:
    """Verify-before-trust read of universe_selection_readmodel.v1 (read-only, no writes)."""
    loaded = _load_manifest_verified_readmodel(archive_root)
    if not isinstance(loaded, tuple):
        return loaded

    payload, contract = loaded

    if contract.fixture_marked:
        return _empty_slice(load_errors=(LOAD_ERROR_FIXTURE_MARKED_NOT_OBSERVABILITY_TRUTH,))

    if payload.get("real_metadata_source_marked") is True:
        if payload.get("observability_truth_allowed") is not True:
            return _empty_slice(load_errors=(LOAD_ERROR_REAL_METADATA_NOT_OBSERVABILITY_TRUTH,))

    _ = STORAGE_RELATIVE_PATH
    return _contract_to_slice(contract)


def try_load_universe_selection_projection_coverage_for_dashboard(
    archive_root: str | Path,
) -> UniverseSelectionDashboardSliceV1:
    """Read-only candidate_validation projection coverage (non-truth, non-selection)."""
    loaded = _load_manifest_verified_readmodel(archive_root)
    if not isinstance(loaded, tuple):
        return loaded

    payload, contract = loaded

    if contract.fixture_marked:
        return _empty_slice(load_errors=(LOAD_ERROR_FIXTURE_MARKED_NOT_OBSERVABILITY_TRUTH,))

    if payload.get("non_authorizing") is not True:
        return _empty_slice(load_errors=(LOAD_ERROR_NON_AUTHORIZING_REQUIRED,))

    if payload.get("observability_truth_allowed") is True:
        return _empty_slice(load_errors=(LOAD_ERROR_PROJECTION_NOT_CVC_ONLY,))

    if payload.get("observability_truth_allowed") is not False:
        return _empty_slice(load_errors=(LOAD_ERROR_NOT_CVC_PROJECTION,))

    evidence = payload.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("candidate_validation_projection") is not True:
        return _empty_slice(load_errors=(LOAD_ERROR_NOT_CVC_PROJECTION,))

    if contract.selected_future is not None or _selected_future_persisted_in_payload(payload):
        return _empty_slice(load_errors=(LOAD_ERROR_SELECTED_FUTURE_PERSISTED_NOT_PROJECTION,))

    _ = STORAGE_RELATIVE_PATH
    return _contract_to_slice(contract, load_mode=PROJECTION_COVERAGE_LOAD_MODE)
