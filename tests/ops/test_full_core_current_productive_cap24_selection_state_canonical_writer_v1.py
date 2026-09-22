"""Canonical Cap-24 selection-state productivity root writer tests (tmp only)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionResultV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    MARK_PRICES_FILENAME,
    RUNTIME_STATE_DIRNAME,
    CurrentProductive29PCap24ProvenanceHandoffError,
    acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap21_to_cap23_productive_persistence_v1 import (
    CurrentProductiveCap21ToCap23PersistenceError,
    build_cap24_mark_prices_sidecar_from_acquisition_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap24_selection_state_canonical_writer_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PUBLISH_MANIFEST_FILENAME,
    THIS_SLICE,
    CurrentProductiveCap24SelectionStateWriterError,
    execute_current_productive_cap24_selection_state_canonical_write_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    SELECTION_FILENAME,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    _eligible_rows,
    _okx_envelope,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA
HISTORICAL_EEA_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops/full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1/"
    "20260915T140000Z/runtime_state/universe/governed_futures_universe_snapshot_v1.json"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER_V1.md"
)
WRITER_SOURCE = (
    REPO_ROOT / "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_cap24_selection_state_canonical_writer_v1.py"
)


def _epoch_rfc(unix: float) -> str:
    return datetime.fromtimestamp(unix, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _mark_rows(ids: list[str]) -> dict:
    return _okx_envelope(
        rows=[{"instId": i, "markPx": "100.5"} for i in ids],
        ts="1700000000000",
    )


_OBSERVED_UNIX = 1_700_000_100.0


def _acquisition(*, include_mark_for: str | None = None) -> EeaUniverseAcquisitionResultV1:
    rows = _eligible_rows()
    ids = [r["instId"] for r in rows]
    mark_ids = ids if include_mark_for is None else [include_mark_for]
    return EeaUniverseAcquisitionResultV1(
        ok=True,
        host="eea.okx.com",
        venue="okx_eea",
        source_kind="okx_eea_public_instruments",
        source_event_time="1700000000000",
        instruments_payload=_okx_envelope(rows=rows),
        mark_price_payload=_mark_rows(mark_ids),
        endpoints_used=("/api/v5/public/instruments",),
        methods_used=("GET",),
        post_count="0",
        request_count=2,
        venue_live_contact=False,
        failure_codes=(),
        provenance={"test": True},
    )


def test_standing_constants_and_spec() -> None:
    assert CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER_CREATED is True
    assert EXPECTED_ORIGIN_MAIN_SHA == BASE_SHA
    assert OWNER_GO == "CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITE_V1"
    assert THIS_SLICE.endswith("CAP24_SELECTION_STATE_CANONICAL_WRITER")
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert SPEC_PATH.is_file()
    text = WRITER_SOURCE.read_text(encoding="utf-8")
    assert "run_single_selected_future_policy_v1" not in text
    assert "from src.ops.productive_futures_ranking_producer_v1.ranking_v1" not in text


def test_writer_reuses_cap21_to_cap23_chain(tmp_path: Path) -> None:
    acq = _acquisition()
    with patch(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_cap24_selection_state_canonical_writer_v1."
        "run_cap21_to_cap23_persist_productive_v1"
    ) as mock_chain:
        from src.ops.governed_productive_account_equity_authority_producer_v1 import (
            current_productive_cap21_to_cap23_productive_persistence_v1 as shared,
        )

        mock_chain.side_effect = shared.run_cap21_to_cap23_persist_productive_v1
        result = execute_current_productive_cap24_selection_state_canonical_write_v1(
            owner_go=OWNER_GO,
            origin_main_sha=BASE_SHA,
            acquisition_result=acq,
            productivity_root=tmp_path / "prod",
            repository_sha=BASE_SHA,
            producer_observed_at_unix=_OBSERVED_UNIX,
        )
        assert result.ok is True
        mock_chain.assert_called_once()


def test_productivity_layout_and_handoff(tmp_path: Path) -> None:
    observed = _OBSERVED_UNIX
    acq = _acquisition()
    prod = tmp_path / "cap24_productivity"
    result = execute_current_productive_cap24_selection_state_canonical_write_v1(
        owner_go=OWNER_GO,
        origin_main_sha=BASE_SHA,
        acquisition_result=acq,
        productivity_root=prod,
        repository_sha=BASE_SHA,
        producer_observed_at_unix=observed,
        decision_epoch=_epoch_rfc(observed),
    )
    assert result.repository_sha == BASE_SHA
    state = prod / RUNTIME_STATE_DIRNAME
    assert (state / "universe").is_dir()
    assert (state / "ranking").is_dir()
    assert (state / "selection" / SELECTION_FILENAME).is_file()
    assert (state / "recon").is_dir()
    assert (prod / MARK_PRICES_FILENAME).is_file()
    assert (prod / PUBLISH_MANIFEST_FILENAME).is_file()
    selection = json.loads((state / "selection" / SELECTION_FILENAME).read_text())
    assert selection["state"] == STATE_SELECTED_ACTIVE
    assert selection["repository_sha"] == BASE_SHA
    marks = json.loads((prod / MARK_PRICES_FILENAME).read_text())
    assert set(marks.keys()) == {selection["venue_native_id"]}
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=prod,
        repository_sha=BASE_SHA,
        binding_epoch=_epoch_rfc(observed),
    )
    assert handoff.reselection_performed is False
    assert handoff.repository_sha == BASE_SHA


def test_origin_main_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveCap24SelectionStateWriterError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_current_productive_cap24_selection_state_canonical_write_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef" * 5,
            acquisition_result=_acquisition(),
            productivity_root=tmp_path / "prod",
            repository_sha=BASE_SHA,
        )


def test_repository_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveCap24SelectionStateWriterError,
        match="REPOSITORY_SHA_BASELINE_MISMATCH",
    ):
        execute_current_productive_cap24_selection_state_canonical_write_v1(
            owner_go=OWNER_GO,
            origin_main_sha=BASE_SHA,
            acquisition_result=_acquisition(),
            productivity_root=tmp_path / "prod",
            repository_sha="deadbeef" * 5,
        )


def test_stale_selection_handoff_fail_closed(tmp_path: Path) -> None:
    observed = _OBSERVED_UNIX
    prod = tmp_path / "prod"
    execute_current_productive_cap24_selection_state_canonical_write_v1(
        owner_go=OWNER_GO,
        origin_main_sha=BASE_SHA,
        acquisition_result=_acquisition(),
        productivity_root=prod,
        repository_sha=BASE_SHA,
        producer_observed_at_unix=observed,
        decision_epoch=_epoch_rfc(observed),
    )
    sel_path = prod / RUNTIME_STATE_DIRNAME / "selection" / SELECTION_FILENAME
    payload = json.loads(sel_path.read_text(encoding="utf-8"))
    payload["valid_until"] = "2020-01-01T00:00:00Z"
    sel_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(
        CurrentProductive29PCap24ProvenanceHandoffError,
        match="SELECTION_STALE_FOR_BINDING_EPOCH|CORRUPT_PERSISTED_SELECTION",
    ):
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            productivity_root=prod,
            repository_sha=BASE_SHA,
            binding_epoch=_epoch_rfc(observed),
        )


def test_mark_price_missing_for_selected_fail_closed() -> None:
    acq = _acquisition(include_mark_for="SOL-USDT-SWAP")
    with pytest.raises(
        CurrentProductiveCap21ToCap23PersistenceError,
        match="MARK_PRICE_MISSING_FOR_SELECTED_VENUE_NATIVE_ID",
    ):
        build_cap24_mark_prices_sidecar_from_acquisition_v1(
            mark_price_payload=acq.mark_price_payload,
            venue_native_id="ADA-USDT-SWAP",
        )


def test_historical_evidence_root_forbidden(tmp_path: Path) -> None:
    evidence_root = REPO_ROOT / "evidence" / "ops" / "cap24_writer_forbidden_test"
    evidence_root.mkdir(parents=True, exist_ok=True)
    try:
        with pytest.raises(
            CurrentProductiveCap24SelectionStateWriterError,
            match="HISTORICAL_EVIDENCE_PRODUCTIVITY_ROOT_FORBIDDEN",
        ):
            execute_current_productive_cap24_selection_state_canonical_write_v1(
                owner_go=OWNER_GO,
                origin_main_sha=BASE_SHA,
                acquisition_result=_acquisition(),
                productivity_root=evidence_root,
                repository_sha=BASE_SHA,
            )
    finally:
        shutil.rmtree(evidence_root, ignore_errors=True)


def test_handoff_no_reselection(tmp_path: Path) -> None:
    observed = _OBSERVED_UNIX
    prod = tmp_path / "prod"
    execute_current_productive_cap24_selection_state_canonical_write_v1(
        owner_go=OWNER_GO,
        origin_main_sha=BASE_SHA,
        acquisition_result=_acquisition(),
        productivity_root=prod,
        repository_sha=BASE_SHA,
        producer_observed_at_unix=observed,
    )
    with patch(
        "src.ops.single_selected_future_policy_v1.producer_v1.run_single_selected_future_policy_v1"
    ) as mock_policy:
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            productivity_root=prod,
            repository_sha=BASE_SHA,
            binding_epoch=_epoch_rfc(observed),
        )
        mock_policy.assert_not_called()


def test_historical_provenance_sha_not_rewritten() -> None:
    assert HISTORICAL_EEA_EVIDENCE.is_file()
    payload = json.loads(HISTORICAL_EEA_EVIDENCE.read_text(encoding="utf-8"))
    assert payload.get("repository_sha") == "ee3850128e01378f4b480f4ab1b5e57dd8ee24a3"


def test_default_productivity_root_requires_explicit_allow() -> None:
    with pytest.raises(
        CurrentProductiveCap24SelectionStateWriterError,
        match="DEFAULT_PRODUCTIVITY_ROOT_REQUIRES_EXPLICIT_ALLOW",
    ):
        execute_current_productive_cap24_selection_state_canonical_write_v1(
            owner_go=OWNER_GO,
            origin_main_sha=BASE_SHA,
            acquisition_result=_acquisition(),
            productivity_root=None,
            repository_sha=BASE_SHA,
        )
