"""Cap-2.4 provenance handoff for CURRENT_PRODUCTIVE 29P common-epoch consumer."""

from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.governed_futures_universe_producer_v1.single_writer_v1 import (
    GovernedUniverseSingleWriterV1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    persist_universe_bundle_atomic_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_CAP24_PROVENANCE_HANDOFF_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    SCHEMA_CLASS,
    THIS_SLICE,
    CurrentProductive29PCap24ProvenanceHandoffError,
    acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    resolve_current_productive_29p_cap24_bound_instrument_for_common_epoch_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    OWNER_GO,
    PIN_OWNER_GO,
    execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
    TRUSTED_TEST_ORIGIN_MAIN_SHA,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    persist_ranking_bundle_atomic_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (
    ProductiveRankingSingleWriterV1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import SELECTION_FILENAME
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    CAPABILITY_ID as CAP24_CAPABILITY_ID,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    OWNER as CAP24_OWNER,
    SELECTION_AUTHORITY_OWNER,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    CountingInjectedFreshGetTransportV1,
    _identity_payloads,
)
from tests.ops.test_single_selected_future_runtime_binding_v1 import (
    REPO_SHA,
    _build_chain,
    _empty_portfolio,
    _marks,
    _payload,
    _perp,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_INTEGRITY = MockCurrentProductive29PIntegrityBackendV1()
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_29P_CAP24_BOUND_INSTRUMENT_PROVENANCE_HANDOFF_V1.md"
)


def _epoch_rfc(unix: float) -> str:
    return datetime.fromtimestamp(unix, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_fresh_chain(tmp: Path, *, repository_sha: str = REPO_SHA) -> dict:
    tmp.mkdir(parents=True, exist_ok=True)
    observed = time.time() - 30.0
    source_event = str(int(observed * 1000))
    rows = [
        _perp("SOL-USDT-SWAP", base="SOL"),
        _perp("ETH-USDT-SWAP"),
        _perp("ADA-USDT-SWAP", base="ADA"),
    ]
    mark_ids = [r["instId"] for r in rows]
    uni_root = tmp / "universe"
    rank_root = tmp / "ranking"
    sel_root = tmp / "selection"
    recon_root = tmp / "recon"
    for d in (uni_root, rank_root, sel_root, recon_root):
        d.mkdir()

    uni = produce_governed_futures_universe_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*mark_ids),
        repository_sha=repository_sha,
        producer_observed_at_unix=observed,
        source_event_time=source_event,
    )
    uni_writer = GovernedUniverseSingleWriterV1(
        state_root=uni_root, writer_identity="test_uni", session_id="s"
    )
    uni_writer.acquire(now_unix=observed)
    persist_universe_bundle_atomic_v1(
        state_root=uni_root,
        writer=uni_writer,
        snapshot=uni.snapshot,
        evidence={"ok": True},
    )
    uni_writer.release()

    ranking = produce_productive_futures_ranking_v1(
        universe_snapshot=uni.snapshot.to_dict(),
        repository_sha=repository_sha,
        producer_observed_at_unix=observed,
    )
    rank_writer = ProductiveRankingSingleWriterV1(
        state_root=rank_root, writer_identity="test_rank", session_id="s"
    )
    rank_writer.acquire(now_unix=observed)
    persist_ranking_bundle_atomic_v1(
        state_root=rank_root,
        writer=rank_writer,
        snapshot=ranking.snapshot,
        evidence={"ok": True},
    )
    rank_writer.release()

    sel = run_single_selected_future_policy_v1(
        state_root=sel_root,
        ranking_state_root=rank_root,
        repository_sha=repository_sha,
        producer_observed_at_unix=observed,
        session_id="sel",
    )
    assert sel.get("ok") is True
    selection = SingleSelectedFutureSelectionV1.from_dict(
        json.loads((sel_root / SELECTION_FILENAME).read_text(encoding="utf-8"))
    )
    return {
        "universe_root": uni_root,
        "ranking_root": rank_root,
        "selection_root": sel_root,
        "recon_root": recon_root,
        "selection": selection,
        "venue_native_id": selection.venue_native_id,
        "instrument_id": selection.instrument_id,
        "binding_epoch": _epoch_rfc(observed),
        "repository_sha": repository_sha,
    }


def _materialize_productivity_root(tmp: Path, chain: dict) -> Path:
    prod = tmp / "cap24_productivity"
    state = prod / "runtime_state"
    for key, sub in (
        ("universe_root", "universe"),
        ("ranking_root", "ranking"),
        ("selection_root", "selection"),
        ("recon_root", "recon"),
    ):
        shutil.copytree(chain[key], state / sub)
    marks = {str(chain["venue_native_id"]): "100.5"}
    (prod / "mark_prices_by_native_id_v1.json").write_text(json.dumps(marks), encoding="utf-8")
    return prod


def test_standing_constants_and_spec() -> None:
    assert CURRENT_PRODUCTIVE_29P_CAP24_PROVENANCE_HANDOFF_CREATED is True
    assert THIS_SLICE.endswith("CAP24_BOUND_INSTRUMENT_PROVENANCE_HANDOFF")
    assert SCHEMA_CLASS == "CURRENT_PRODUCTIVE_29P_CAP24_BOUND_INSTRUMENT_PROVENANCE_HANDOFF_V1"
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert SELECTION_AUTHORITY_OWNER == "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
    assert CAP24_CAPABILITY_ID == "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1"
    assert CAP24_CAPABILITY_ID == "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1"
    assert SPEC_PATH.is_file()


def test_valid_current_cap24_handoff_accepted(tmp_path: Path) -> None:
    chain = _build_fresh_chain(tmp_path / "build", repository_sha=REPO_SHA)
    prod = _materialize_productivity_root(tmp_path, chain)
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=prod,
        repository_sha=REPO_SHA,
        binding_epoch=chain["binding_epoch"],
    )
    assert handoff.reselection_performed is False
    assert handoff.historical_substitution is False
    assert handoff.venue_native_id == chain["venue_native_id"]
    assert handoff.instrument_id == chain["instrument_id"]
    assert handoff.bound_instrument.venue_native_id == chain["venue_native_id"]
    assert handoff.cap23_authority_owner == SELECTION_AUTHORITY_OWNER
    assert handoff.cap24_authority_owner == CAP24_OWNER


def test_missing_runtime_root_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductive29PCap24ProvenanceHandoffError,
        match="CAP24_RUNTIME_STATE_ROOT_MISSING",
    ):
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            productivity_root=tmp_path / "missing",
            repository_sha=REPO_SHA,
            binding_epoch="2026-01-01T00:00:00Z",
        )


def test_mark_prices_missing_fail_closed(tmp_path: Path) -> None:
    chain = _build_fresh_chain(tmp_path / "build")
    prod = tmp_path / "prod"
    state = prod / "runtime_state"
    for key, sub in (
        ("universe_root", "universe"),
        ("ranking_root", "ranking"),
        ("selection_root", "selection"),
        ("recon_root", "recon"),
    ):
        shutil.copytree(chain[key], state / sub)
    with pytest.raises(
        CurrentProductive29PCap24ProvenanceHandoffError,
        match="MARK_PRICES_PROVENANCE_MISSING",
    ):
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            productivity_root=prod,
            repository_sha=REPO_SHA,
            binding_epoch=chain["binding_epoch"],
        )


def test_historical_evidence_path_forbidden(tmp_path: Path) -> None:
    chain = _build_fresh_chain(tmp_path / "build")
    evidence_root = REPO_ROOT / "evidence" / "ops" / "cap24_handoff_test_forbidden"
    evidence_root.mkdir(parents=True, exist_ok=True)
    prod = _materialize_productivity_root(evidence_root, chain)
    try:
        with pytest.raises(
            CurrentProductive29PCap24ProvenanceHandoffError,
            match="HISTORICAL_EVIDENCE_RUNTIME_INPUT_FORBIDDEN",
        ):
            acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
                productivity_root=prod,
                repository_sha=REPO_SHA,
                binding_epoch=chain["binding_epoch"],
            )
    finally:
        shutil.rmtree(evidence_root, ignore_errors=True)


def test_contradictory_ranking_provenance_fail_closed(tmp_path: Path) -> None:
    chain = _build_fresh_chain(tmp_path / "build")
    prod = _materialize_productivity_root(tmp_path, chain)
    sel_path = prod / "runtime_state" / "selection" / SELECTION_FILENAME
    payload = json.loads(sel_path.read_text(encoding="utf-8"))
    payload["ranking_snapshot_id"] = "contradictory-ranking-snapshot-id"
    sel_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(
        CurrentProductive29PCap24ProvenanceHandoffError,
        match="RANKING_SNAPSHOT_ID_MISMATCH|CORRUPT_PERSISTED_SELECTION",
    ):
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            productivity_root=prod,
            repository_sha=REPO_SHA,
            binding_epoch=chain["binding_epoch"],
        )


def test_repository_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    chain = _build_fresh_chain(tmp_path / "build")
    prod = _materialize_productivity_root(tmp_path, chain)
    with pytest.raises(
        CurrentProductive29PCap24ProvenanceHandoffError,
        match="REPOSITORY_SHA_MISMATCH",
    ):
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            productivity_root=prod,
            repository_sha="deadbeef" * 5,
            binding_epoch=chain["binding_epoch"],
        )


def test_no_cap23_reselection_during_handoff(tmp_path: Path) -> None:
    chain = _build_fresh_chain(tmp_path / "build")
    prod = _materialize_productivity_root(tmp_path, chain)
    with patch(
        "src.ops.single_selected_future_policy_v1.producer_v1.run_single_selected_future_policy_v1"
    ) as mock_policy:
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            productivity_root=prod,
            repository_sha=REPO_SHA,
            binding_epoch=chain["binding_epoch"],
        )
        mock_policy.assert_not_called()


def test_resolve_returns_none_without_root_or_bound() -> None:
    assert (
        resolve_current_productive_29p_cap24_bound_instrument_for_common_epoch_v1(
            bound_instrument=None,
            cap24_productivity_root=None,
            repository_sha=REPO_SHA,
            binding_epoch="2026-01-01T00:00:00Z",
        )
        is None
    )


def test_execute_acquires_cap24_without_manual_bound(tmp_path: Path) -> None:
    chain = _build_fresh_chain(
        tmp_path / "build",
        repository_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
    )
    prod = _materialize_productivity_root(tmp_path, chain)
    inst = str(chain["venue_native_id"])
    transport = CountingInjectedFreshGetTransportV1(payloads=_identity_payloads(instrument_id=inst))
    fixed_epoch = chain["binding_epoch"]
    with patch(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_29p_common_epoch_handoff_v1._utc_now_iso_v1",
        return_value=fixed_epoch,
    ):
        result = execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1(
            owner_go=PIN_OWNER_GO,
            origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
            bound_instrument=None,
            fresh_get_transport=transport,
            evidence_root=tmp_path / "pack",
            cap24_productivity_root=prod,
            execution_integrity_backend=_INTEGRITY,
        )
    assert result.bound_instrument_id == chain["instrument_id"]
    assert result.deduplicated_get_count == 7
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert claims["CAP24_PROVENANCE_HANDOFF_STATUS"] == "ACQUIRED"
    assert claims["CAP24_BOUND_INSTRUMENT_ID"] == chain["instrument_id"]


def test_execute_cap24_fail_closed_when_handoff_invalid(tmp_path: Path) -> None:
    chain = _build_fresh_chain(
        tmp_path / "build",
        repository_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
    )
    prod = _materialize_productivity_root(tmp_path, chain)
    shutil.rmtree(prod / "runtime_state" / "selection")
    transport = CountingInjectedFreshGetTransportV1(payloads=_identity_payloads())
    fixed_epoch = chain["binding_epoch"]
    with patch(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_29p_common_epoch_handoff_v1._utc_now_iso_v1",
        return_value=fixed_epoch,
    ):
        result = execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1(
            owner_go=OWNER_GO,
            origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
            bound_instrument=None,
            fresh_get_transport=transport,
            evidence_root=tmp_path / "pack2",
            cap24_productivity_root=prod,
            execution_integrity_backend=_INTEGRITY,
        )
    assert result.first_real_blocker == "CAP24_BOUND_INSTRUMENT_FAIL_CLOSED"
    assert result.deduplicated_get_count == 0


def test_legacy_build_chain_still_binds_via_gate(tmp_path: Path) -> None:
    """Fixture parity: persisted Cap-2.1–2.3 + gate only (no policy re-run)."""

    chain = _build_chain(tmp_path)
    prod = _materialize_productivity_root(tmp_path, chain)
    marks = {str(chain["venue_native_id"]): "100.5"}
    selection = chain["selection"]
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=prod,
        repository_sha=REPO_SHA,
        binding_epoch=selection.valid_until,
        mark_price_by_native_id=marks,
    )
    assert handoff.bound_instrument.venue_native_id == chain["venue_native_id"]
    _ = _empty_portfolio()
