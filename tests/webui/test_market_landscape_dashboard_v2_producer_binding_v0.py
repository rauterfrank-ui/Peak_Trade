"""Phase 4.1 producer binding tests for Market Landscape V2."""

from __future__ import annotations

import json
import uuid
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp
from scripts.ops.primary_evidence_retention_v0 import (
    write_manifest_sha256 as _write_manifest_sha256,
)
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    DECISION_EVIDENCE_SCHEMA_VERSION,
    DECISION_PRODUCER_MODULE,
    DECISION_SOURCE_KIND,
    LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
    LANDSCAPE_PHASE42_MAX_AGE_SECONDS,
    LANDSCAPE_PHASE43A_MAX_AGE_SECONDS,
    REASON_ARCHIVE_ROOT_UNSET,
    REASON_DECISION_NOT_PERSISTED,
    REASON_MARKET_CONTEXT_NOT_PERSISTED,
    REASON_PRODUCER_DATA_STALE,
    REASON_PRODUCER_TIMESTAMP_INVALID,
    REASON_PRODUCER_TIMESTAMP_MISSING,
    REASON_SCOPE_NOT_PERSISTED,
    REASON_SELECTED_FORBIDDEN_SYMBOL,
    REASON_SOURCE_CONTRADICTION,
    SCOPE_PRODUCER_MODULE,
    SCOPE_SOURCE_KIND,
    bind_market_universe_slots,
    parse_producer_utc_timestamp,
)
from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
    project_market_instrument_snapshot_v1,
    project_universe_ranking_snapshot_v1,
    serialize_projection,
)
from src.webui.market_dashboard_landscape_v2.projections import (
    project_canonical_decision_snapshot_v1,
    project_dynamic_scope_snapshot_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.types import (
    SelectedFutureDisplayV1,
    UniverseSelectionDashboardSliceV1,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
)

STAMP = datetime(2026, 7, 23, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = datetime(2026, 7, 23, 17, 0, 0, tzinfo=timezone.utc)
PRODUCER_STALE = STAMP - timedelta(seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS + 3600)
SCOPE_PRODUCER_FRESH = datetime(2026, 7, 23, 16, 30, 0, tzinfo=timezone.utc)
SCOPE_PRODUCER_STALE = STAMP - timedelta(seconds=LANDSCAPE_PHASE42_MAX_AGE_SECONDS + 7200)
DECISION_PRODUCER_FRESH = datetime(2026, 7, 23, 16, 0, 0, tzinfo=timezone.utc)
DECISION_PRODUCER_STALE = STAMP - timedelta(seconds=LANDSCAPE_PHASE43A_MAX_AGE_SECONDS + 7200)
REPO = Path(__file__).resolve().parents[2]
SCRATCH_ROOT = REPO / "tests" / "_durable_archive_scratch"


@pytest.fixture
def archive_root(tmp_path: Path) -> Path:
    candidate = tmp_path / "archive_root"
    candidate.mkdir(parents=True, exist_ok=True)
    if not is_under_tmp(candidate):
        return candidate
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    durable = SCRATCH_ROOT / str(uuid.uuid4())
    durable.mkdir(parents=True, exist_ok=True)
    return durable


def test_project_market_universe_field_copy_immutable() -> None:
    market = project_market_instrument_snapshot_v1(
        instrument_id="BTC-USDT-SWAP",
        venue="OKX",
        market_type="perpetual",
        mark_price=65000.5,
        reason_codes=("CONTEXT_ACCEPTED",),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="context://btc",
    )
    assert market.availability is Availability.AVAILABLE
    assert market.instrument_id == "BTC-USDT-SWAP"
    assert market.provenance.generated_at == PRODUCER_FRESH
    with pytest.raises(FrozenInstanceError):
        market.instrument_id = "X"  # type: ignore[misc]

    universe = project_universe_ranking_snapshot_v1(
        ranking=(
            {"symbol": "ETHUSDT", "rank": 1},
            {"symbol": "SOLUSDT", "rank": 2},
        ),
        universe=({"symbol": "ETHUSDT", "rank": 1, "exchange": "okx"},),
        selected_instrument_id="ETHUSDT",
        reason_codes=("RANK_PROJECTED",),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="readmodels/universe_selection_readmodel.v1.json",
    )
    assert universe.availability is Availability.AVAILABLE
    assert [row["symbol"] for row in universe.ranking] == ["ETHUSDT", "SOLUSDT"]


def test_parse_producer_utc_timestamp_deterministic() -> None:
    assert parse_producer_utc_timestamp("2026-07-23T17:00:00Z") == PRODUCER_FRESH
    assert parse_producer_utc_timestamp("2026-07-23T17:00:00+00:00") == PRODUCER_FRESH
    assert parse_producer_utc_timestamp(None) is None
    with pytest.raises(ValueError, match=REASON_PRODUCER_TIMESTAMP_INVALID):
        parse_producer_utc_timestamp("2026-07-23T17:00:00")  # naive / no offset
    with pytest.raises(ValueError, match=REASON_PRODUCER_TIMESTAMP_INVALID):
        parse_producer_utc_timestamp("not-a-timestamp")


def test_bind_defaults_fail_closed_without_archive_or_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", raising=False)
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert set(slots) == {
        "market_instrument",
        "universe_ranking",
        "dynamic_scope",
        "canonical_decision",
    }
    assert slots["market_instrument"].availability is Availability.MISSING_SOURCE
    assert REASON_MARKET_CONTEXT_NOT_PERSISTED in slots["market_instrument"].reason_codes
    assert slots["universe_ranking"].availability is Availability.MISSING_SOURCE
    assert REASON_ARCHIVE_ROOT_UNSET in slots["universe_ranking"].reason_codes
    assert slots["dynamic_scope"].availability is Availability.MISSING_SOURCE
    assert REASON_SCOPE_NOT_PERSISTED in slots["dynamic_scope"].reason_codes
    assert slots["dynamic_scope"].scope_state is None
    assert slots["dynamic_scope"].current_scope_ref is None
    assert slots["dynamic_scope"].next_scope_ref is None
    assert slots["canonical_decision"].availability is Availability.MISSING_SOURCE
    assert REASON_DECISION_NOT_PERSISTED in slots["canonical_decision"].reason_codes
    assert slots["canonical_decision"].decision is None
    assert slots["canonical_decision"].direction is None
    assert slots["canonical_decision"].blockers == (REASON_DECISION_NOT_PERSISTED,)


def test_bind_rejects_inventing_market_without_required_fields() -> None:
    with pytest.raises(KeyError):
        bind_market_universe_slots(
            generated_at=STAMP,
            market_instrument_fields={"venue": "OKX"},
        )


def test_bind_available_when_producer_fields_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", raising=False)
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        market_instrument_fields={
            "instrument_id": "BTC-USDT-SWAP",
            "venue": "OKX",
            "market_type": "perpetual",
            "mark_price": 1.0,
            "reason_codes": ("OK",),
            "source_reference": "ctx://1",
            "effective_at": PRODUCER_FRESH,
        },
    )
    assert slots["market_instrument"].availability is Availability.AVAILABLE
    assert slots["market_instrument"].provenance.generated_at == PRODUCER_FRESH
    assert slots["market_instrument"].freshness.observed_at == PRODUCER_FRESH
    assert slots["universe_ranking"].availability is Availability.MISSING_SOURCE


def _write_truth_universe_archive(
    archive_root: Path,
    *,
    selected_symbol: str = "ETH-USDT-SWAP",
    include_ranking: bool = True,
    include_selected: bool = True,
    generated_at: str = "2026-07-23T17:00:00Z",
    captured_at: str | None = "2026-07-23T16:59:00Z",
    ranking_rows: list[dict[str, object]] | None = None,
    omit_generated_at: bool = False,
    naive_generated_at: bool = False,
) -> Path:
    readmodels = archive_root / READMODELS_DIRNAME
    readmodels.mkdir(parents=True, exist_ok=True)
    if ranking_rows is not None:
        ranking = ranking_rows
    elif include_ranking:
        ranking = [
            {
                "row_id": "r-eth",
                "symbol": selected_symbol,
                "rank": 1,
                "display_score": 0.9,
                "exchange": "OKX",
            },
            {
                "row_id": "r-sol",
                "symbol": "SOL-USDT-SWAP",
                "rank": 2,
                "display_score": 0.8,
                "exchange": "OKX",
            },
        ]
    else:
        ranking = []
    if include_selected:
        selected_future: dict[str, object] = {
            "row_id": "s-eth",
            "symbol": selected_symbol,
            "rank": 1,
            "truth_status": "PERSISTED",
            "selection_reason": "top_ranked",
        }
        selected_truth = "PERSISTED"
    else:
        selected_future = {"truth_status": "NOT_PERSISTED"}
        selected_truth = "SELECTED_FUTURE_NOT_PERSISTED"
    gen_at = "2026-07-23T17:00:00" if naive_generated_at else generated_at
    payload: dict[str, object] = {
        "schema_name": "universe_selection_readmodel.v1",
        "schema_version": 1,
        "source_run_id": "landscape_phase41_truth_v1",
        "source_stage": "paper",
        "non_authorizing": True,
        "fixture_marked": False,
        "universe": [
            {
                "row_id": "u-eth",
                "symbol": selected_symbol,
                "rank": 1,
                "exchange": "OKX",
            },
            {
                "row_id": "u-sol",
                "symbol": "SOL-USDT-SWAP",
                "rank": 2,
                "exchange": "OKX",
            },
        ],
        "ranking": ranking,
        "selected_future": selected_future,
        "market_snapshot": {
            "truth_status": "PERSISTED",
            "source_kind": "governed_producer",
            "snapshot_id": "snap-1",
            "exchange": "OKX",
            **({"captured_at": captured_at} if captured_at is not None else {}),
        },
        "evidence": {
            "producer_contract": "universe_selection_producer.v1",
            "storage_target": "readmodels/universe_selection_readmodel.v1.json",
            "links": [],
        },
        "missing_truth": {
            "universe": "PERSISTED",
            "ranking": "PERSISTED" if ranking else "TOP20_RANKING_NOT_PERSISTED",
            "selected_future": selected_truth,
            "future_detail": "AVAILABLE",
            "orders_fills_pnl": "NOT_PERSISTED",
        },
    }
    if not omit_generated_at:
        payload["generated_at"] = gen_at
    readmodel_path = readmodels / READMODEL_FILENAME
    readmodel_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_manifest_sha256(readmodels)
    return archive_root


def test_bind_preserves_producer_timestamps_not_page_assembly(archive_root: Path) -> None:
    archive = _write_truth_universe_archive(archive_root)
    later_as_of = STAMP + timedelta(hours=2)
    slots = bind_market_universe_slots(generated_at=later_as_of, archive_root=archive)
    assert slots["universe_ranking"].availability is Availability.AVAILABLE
    assert slots["universe_ranking"].provenance.generated_at == PRODUCER_FRESH
    assert slots["universe_ranking"].provenance.effective_at == PRODUCER_FRESH
    assert slots["universe_ranking"].freshness.observed_at == PRODUCER_FRESH
    assert slots["universe_ranking"].freshness.max_age_seconds == LANDSCAPE_PHASE41_MAX_AGE_SECONDS
    assert slots["market_instrument"].availability is Availability.AVAILABLE
    captured = datetime(2026, 7, 23, 16, 59, 0, tzinfo=timezone.utc)
    assert slots["market_instrument"].provenance.generated_at == captured
    assert slots["market_instrument"].freshness.observed_at == captured
    # Newer page assembly must not rewrite producer time.
    assert slots["universe_ranking"].provenance.generated_at != later_as_of
    payload = serialize_projection(slots["universe_ranking"])
    assert payload["provenance"]["generated_at"] == "2026-07-23T17:00:00Z"


def test_aged_universe_and_market_derive_stale(archive_root: Path) -> None:
    stale_gen = PRODUCER_STALE.isoformat().replace("+00:00", "Z")
    stale_cap = (PRODUCER_STALE - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    archive = _write_truth_universe_archive(
        archive_root,
        generated_at=stale_gen,
        captured_at=stale_cap,
    )
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive)
    assert slots["universe_ranking"].availability is Availability.STALE
    assert slots["universe_ranking"].freshness.is_stale is True
    assert REASON_PRODUCER_DATA_STALE in slots["universe_ranking"].reason_codes
    assert slots["universe_ranking"].selected_instrument_id == "ETH-USDT-SWAP"
    assert slots["market_instrument"].availability is Availability.STALE
    assert slots["market_instrument"].freshness.is_stale is True
    assert slots["market_instrument"].instrument_id == "ETH-USDT-SWAP"


def test_missing_and_invalid_timestamps_fail_closed(archive_root: Path) -> None:
    missing = _write_truth_universe_archive(
        archive_root / "missing",
        omit_generated_at=True,
    )
    # Contract validation requires generated_at — expect INVALID/MISSING fail-closed.
    slots_missing = bind_market_universe_slots(generated_at=STAMP, archive_root=missing)
    assert slots_missing["universe_ranking"].availability in {
        Availability.INVALID,
        Availability.MISSING_SOURCE,
    }
    assert slots_missing["universe_ranking"].availability is not Availability.AVAILABLE

    naive = _write_truth_universe_archive(
        archive_root / "naive",
        naive_generated_at=True,
    )
    slots_naive = bind_market_universe_slots(generated_at=STAMP, archive_root=naive)
    assert slots_naive["universe_ranking"].availability is Availability.INVALID
    assert REASON_PRODUCER_TIMESTAMP_INVALID in slots_naive["universe_ranking"].reason_codes

    no_capture = _write_truth_universe_archive(
        archive_root / "nocap",
        captured_at=None,
    )
    slots_nocap = bind_market_universe_slots(generated_at=STAMP, archive_root=no_capture)
    assert slots_nocap["universe_ranking"].availability is Availability.AVAILABLE
    assert slots_nocap["market_instrument"].availability is Availability.MISSING_SOURCE
    assert REASON_PRODUCER_TIMESTAMP_MISSING in slots_nocap["market_instrument"].reason_codes


def test_multi_row_ranking_order_preserved(archive_root: Path) -> None:
    archive = _write_truth_universe_archive(archive_root)
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive)
    assert [row["symbol"] for row in slots["universe_ranking"].ranking] == [
        "ETH-USDT-SWAP",
        "SOL-USDT-SWAP",
    ]
    assert [row["rank"] for row in slots["universe_ranking"].ranking] == [1, 2]


def test_forbidden_btc_usd_archive_fails_closed_exact_contract_invalid(
    archive_root: Path,
) -> None:
    archive = _write_truth_universe_archive(archive_root, selected_symbol="BTC/USD")
    u = bind_market_universe_slots(generated_at=STAMP, archive_root=archive)["universe_ranking"]
    assert u.availability is Availability.INVALID
    assert list(u.reason_codes) == ["CONTRACT_INVALID"]
    assert u.selected_instrument_id is None
    assert u.ranking == ()


def test_binder_forbidden_selected_symbol_exact_reason(
    monkeypatch: pytest.MonkeyPatch,
    archive_root: Path,
) -> None:
    poisoned = UniverseSelectionDashboardSliceV1(
        loaded=True,
        load_errors=(),
        generated_at=PRODUCER_FRESH.isoformat().replace("+00:00", "Z"),
        selected_future=SelectedFutureDisplayV1(
            row_id="s1",
            symbol="BTC/USD",
            rank=1,
            truth_status="PERSISTED",
        ),
    )
    monkeypatch.setattr(
        "src.webui.market_dashboard_landscape_producer_binding_v2."
        "try_load_universe_selection_for_dashboard",
        lambda _root: poisoned,
    )
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive_root)
    assert list(slots["universe_ranking"].reason_codes) == [REASON_SELECTED_FORBIDDEN_SYMBOL]


def test_source_contradiction_fails_closed(archive_root: Path) -> None:
    archive = _write_truth_universe_archive(archive_root)
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        archive_root=archive,
        market_instrument_fields={
            "instrument_id": "SOL-USDT-SWAP",
            "venue": "OKX",
            "market_type": "perpetual",
            "mark_price": 1.0,
            "reason_codes": ("OK",),
            "source_reference": "ctx://1",
            "effective_at": PRODUCER_FRESH,
        },
    )
    assert slots["market_instrument"].availability is Availability.INVALID
    assert slots["universe_ranking"].availability is Availability.INVALID
    assert REASON_SOURCE_CONTRADICTION in slots["market_instrument"].reason_codes


def test_missing_ranking_and_selected_still_fail_closed(archive_root: Path) -> None:
    no_rank = _write_truth_universe_archive(archive_root / "nr", include_ranking=False)
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=no_rank)
    assert slots["universe_ranking"].availability is Availability.AVAILABLE
    assert slots["universe_ranking"].ranking == ()
    assert "TOP20_RANKING_NOT_PRESENT_IN_READMODEL" in slots["universe_ranking"].reason_codes

    no_sel = _write_truth_universe_archive(archive_root / "ns", include_selected=False)
    slots2 = bind_market_universe_slots(generated_at=STAMP, archive_root=no_sel)
    assert slots2["universe_ranking"].selected_instrument_id is None
    assert slots2["market_instrument"].availability is Availability.MISSING_SOURCE


def test_page_aggregate_applies_phase41_and_phase42_scope_missing_without_injection() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        market_instrument_fields={
            "instrument_id": "BTC-USDT-SWAP",
            "venue": "OKX",
            "market_type": "perpetual",
            "mark_price": 10.0,
            "reason_codes": ("OK",),
            "source_reference": "ctx://1",
            "effective_at": PRODUCER_FRESH,
        },
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    assert page.market_instrument.availability is Availability.AVAILABLE
    assert page.dynamic_scope.availability is Availability.MISSING_SOURCE
    assert REASON_SCOPE_NOT_PERSISTED in page.dynamic_scope.reason_codes
    assert page.canonical_decision.availability is Availability.MISSING_SOURCE
    assert REASON_DECISION_NOT_PERSISTED in page.canonical_decision.reason_codes
    ctx = present_market_landscape_v2(page)
    assert ctx["phase"] == "PHASE_4_3A_CANONICAL_DECISION_PROJECTION_BINDING"
    assert ctx["chart"]["ohlcv"] is None
    assert ctx["scope"]["availability"] == "MISSING_SOURCE"
    assert ctx["decision"]["availability"] == "MISSING_SOURCE"
    assert ctx["double_play"]["availability"] == "NOT_BOUND"
    assert ctx["regime"]["availability"] == "NOT_BOUND"
    assert ctx["bull_bear"]["availability"] == "NOT_BOUND"
    assert ctx["switch"]["availability"] == "NOT_BOUND"
    assert "membership_label" in ctx["universe_rail"]


def _scope_fields(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "lifecycle_state": "scope_valid",
        "scope_id": "scope-btc-1",
        "reason_codes": ("SCOPE_INITIALIZED",),
        "generated_at": SCOPE_PRODUCER_FRESH,
        "effective_at": SCOPE_PRODUCER_FRESH,
        "semantic_digest": "a" * 64,
        "source_reference": "scope://btc-1",
    }
    base.update(overrides)
    return base


def _decision_fields(**overrides: object) -> dict[str, object]:
    """Bounded test-injection payload — not durable dashboard truth."""
    base: dict[str, object] = {
        "instrument_id": "BTC-USDT-SWAP",
        "decision_outcome": "observe",
        "next_direction_state": "neutral_observe",
        "reason_codes": ("WARMUP_ACTIVE", "NO_ENTRY"),
        "decision_id": "decision-abc123",
        "evidence_schema_version": DECISION_EVIDENCE_SCHEMA_VERSION,
        "semantic_digest": "c" * 64,
        "generated_at": DECISION_PRODUCER_FRESH,
        "effective_at": DECISION_PRODUCER_FRESH,
        "source_reference": "decision://bounded-test-injection",
    }
    base.update(overrides)
    return base


def test_project_dynamic_scope_field_copy_immutable() -> None:
    snap = project_dynamic_scope_snapshot_v1(
        scope_state="scope_valid",
        current_scope_ref="scope-btc-1",
        next_scope_ref="scope-btc-2",
        reason_codes=("SCOPE_INITIALIZED",),
        generated_at=SCOPE_PRODUCER_FRESH,
        effective_at=SCOPE_PRODUCER_FRESH,
        source_reference="scope://btc-1",
        evidence_digest="b" * 64,
    )
    assert snap.availability is Availability.AVAILABLE
    assert snap.scope_state == "scope_valid"
    assert snap.current_scope_ref == "scope-btc-1"
    assert snap.next_scope_ref == "scope-btc-2"
    assert snap.provenance.producer_module == SCOPE_PRODUCER_MODULE
    assert snap.provenance.source_kind == SCOPE_SOURCE_KIND
    assert snap.provenance.generated_at == SCOPE_PRODUCER_FRESH
    with pytest.raises(FrozenInstanceError):
        snap.scope_state = "x"  # type: ignore[misc]


def test_bind_dynamic_scope_available_exact_projection() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        dynamic_scope_fields=_scope_fields(next_scope_ref="scope-btc-2"),
    )
    scope = slots["dynamic_scope"]
    assert scope.availability is Availability.AVAILABLE
    assert scope.scope_state == "scope_valid"
    assert scope.current_scope_ref == "scope-btc-1"
    assert scope.next_scope_ref == "scope-btc-2"
    assert scope.reason_codes == ("SCOPE_INITIALIZED",)
    assert scope.provenance.producer_module == SCOPE_PRODUCER_MODULE
    assert scope.provenance.source_kind == SCOPE_SOURCE_KIND
    assert scope.provenance.evidence_digest == "a" * 64
    assert scope.provenance.generated_at == SCOPE_PRODUCER_FRESH
    assert scope.provenance.effective_at == SCOPE_PRODUCER_FRESH
    assert scope.freshness.observed_at == SCOPE_PRODUCER_FRESH
    assert scope.freshness.is_stale is False


def test_bind_dynamic_scope_null_next_scope_not_invented() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        dynamic_scope_fields=_scope_fields(),
    )
    assert slots["dynamic_scope"].next_scope_ref is None
    slots2 = bind_market_universe_slots(
        generated_at=STAMP,
        dynamic_scope_fields=_scope_fields(next_scope_ref=None),
    )
    assert slots2["dynamic_scope"].next_scope_ref is None


def test_bind_dynamic_scope_invalid_naive_timestamp() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        dynamic_scope_fields=_scope_fields(
            generated_at=datetime(2026, 7, 23, 16, 30, 0),  # naive
            effective_at=None,
        ),
    )
    scope = slots["dynamic_scope"]
    assert scope.availability is Availability.INVALID
    assert REASON_PRODUCER_TIMESTAMP_INVALID in scope.reason_codes
    assert scope.scope_state is None
    assert scope.provenance.generated_at == STAMP  # observation stamp on unavailable only


def test_bind_dynamic_scope_stale_retains_lifecycle_facts() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        dynamic_scope_fields=_scope_fields(
            generated_at=SCOPE_PRODUCER_STALE,
            effective_at=SCOPE_PRODUCER_STALE,
            next_scope_ref="scope-next",
        ),
    )
    scope = slots["dynamic_scope"]
    assert scope.availability is Availability.STALE
    assert scope.scope_state == "scope_valid"
    assert scope.current_scope_ref == "scope-btc-1"
    assert scope.next_scope_ref == "scope-next"
    assert scope.reason_codes == ("SCOPE_INITIALIZED",)
    assert scope.freshness.is_stale is True
    assert scope.freshness.stale_reason == REASON_PRODUCER_DATA_STALE
    assert scope.provenance.generated_at == SCOPE_PRODUCER_STALE


def test_regime_bull_bear_switch_remain_not_bound_for_all_scope_states() -> None:
    cases = (
        None,
        _scope_fields(),
        _scope_fields(generated_at=SCOPE_PRODUCER_STALE, effective_at=SCOPE_PRODUCER_STALE),
        _scope_fields(generated_at=datetime(2026, 7, 23, 16, 30, 0)),
    )
    for fields in cases:
        slots = bind_market_universe_slots(
            generated_at=STAMP,
            dynamic_scope_fields=fields,
        )
        page = MarketDashboardReadServiceV1().load_page_snapshot(
            generated_at=STAMP,
            slot_overrides=slots,
        )
        ctx = present_market_landscape_v2(page)
        assert ctx["regime"]["availability"] == "NOT_BOUND"
        assert ctx["bull_bear"]["availability"] == "NOT_BOUND"
        assert ctx["switch"]["availability"] == "NOT_BOUND"
        assert ctx["global_strip"]["regime"] == "NOT_BOUND"
        assert ctx["double_play"]["availability"] == "NOT_BOUND"


def test_project_canonical_decision_field_copy_immutable() -> None:
    snap = project_canonical_decision_snapshot_v1(
        instrument_id="BTC-USDT-SWAP",
        decision="observe",
        direction="neutral_observe",
        reason_codes=("WARMUP_ACTIVE", "NO_ENTRY"),
        blockers=(),
        decision_id="decision-abc123",
        evidence_schema_version=DECISION_EVIDENCE_SCHEMA_VERSION,
        evidence_digest="c" * 64,
        generated_at=DECISION_PRODUCER_FRESH,
        effective_at=DECISION_PRODUCER_FRESH,
        source_reference="decision://bounded-test-injection",
    )
    assert snap.availability is Availability.AVAILABLE
    assert snap.decision == "observe"
    assert snap.direction == "neutral_observe"
    assert snap.reason_codes == ("WARMUP_ACTIVE", "NO_ENTRY")
    assert snap.blockers == ()
    assert snap.provenance.producer_module == DECISION_PRODUCER_MODULE
    assert snap.provenance.source_kind == DECISION_SOURCE_KIND
    assert snap.provenance.generated_at == DECISION_PRODUCER_FRESH
    with pytest.raises(FrozenInstanceError):
        snap.decision = "x"  # type: ignore[misc]


def test_bind_canonical_decision_available_exact_projection() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        canonical_decision_fields=_decision_fields(),
    )
    decision = slots["canonical_decision"]
    assert decision.availability is Availability.AVAILABLE
    assert decision.decision == "observe"
    assert decision.direction == "neutral_observe"
    assert decision.reason_codes == ("WARMUP_ACTIVE", "NO_ENTRY")
    assert decision.blockers == ()
    assert decision.decision_id == "decision-abc123"
    assert decision.evidence_schema_version == DECISION_EVIDENCE_SCHEMA_VERSION
    assert decision.provenance.evidence_digest == "c" * 64
    assert decision.provenance.producer_module == DECISION_PRODUCER_MODULE
    assert decision.provenance.source_kind == DECISION_SOURCE_KIND
    assert decision.provenance.generated_at == DECISION_PRODUCER_FRESH
    assert decision.provenance.effective_at == DECISION_PRODUCER_FRESH
    assert decision.freshness.observed_at == DECISION_PRODUCER_FRESH
    assert decision.freshness.is_stale is False
    # reason_codes must not be copied into blockers
    assert set(decision.reason_codes).isdisjoint(set(decision.blockers))


def test_bind_canonical_decision_rejects_missing_required_keys() -> None:
    with pytest.raises(KeyError, match="canonical_decision_fields missing"):
        bind_market_universe_slots(
            generated_at=STAMP,
            canonical_decision_fields={"instrument_id": "BTC-USDT-SWAP"},
        )


def test_bind_canonical_decision_invalid_naive_timestamp() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        canonical_decision_fields=_decision_fields(
            generated_at=datetime(2026, 7, 23, 16, 0, 0),  # naive
            effective_at=None,
        ),
    )
    decision = slots["canonical_decision"]
    assert decision.availability is Availability.INVALID
    assert REASON_PRODUCER_TIMESTAMP_INVALID in decision.reason_codes
    assert decision.decision is None
    assert decision.direction is None


def test_bind_canonical_decision_stale_retains_canonical_facts() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        canonical_decision_fields=_decision_fields(
            generated_at=DECISION_PRODUCER_STALE,
            effective_at=DECISION_PRODUCER_STALE,
        ),
    )
    decision = slots["canonical_decision"]
    assert decision.availability is Availability.STALE
    assert decision.decision == "observe"
    assert decision.direction == "neutral_observe"
    assert decision.reason_codes == ("WARMUP_ACTIVE", "NO_ENTRY")
    assert decision.blockers == ()
    assert decision.freshness.is_stale is True
    assert decision.freshness.stale_reason == REASON_PRODUCER_DATA_STALE
    assert decision.provenance.generated_at == DECISION_PRODUCER_STALE
    # Observation clock must not replace producer timestamps.
    assert decision.provenance.generated_at != STAMP
    assert decision.freshness.observed_at == DECISION_PRODUCER_STALE


def test_bind_canonical_decision_does_not_bind_double_play() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        canonical_decision_fields=_decision_fields(),
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    ctx = present_market_landscape_v2(page)
    assert page.canonical_decision.availability is Availability.AVAILABLE
    assert page.double_play.availability is Availability.NOT_BOUND
    assert ctx["double_play"]["availability"] == "NOT_BOUND"
    assert ctx["phase"] == "PHASE_4_3A_CANONICAL_DECISION_PROJECTION_BINDING"
    assert ctx["product_flags"]["phase_4_3a_binding_active"] is True
    assert ctx["decision"]["fields"]["decision"] == "observe"
    assert ctx["decision"]["fields"]["direction"] == "neutral_observe"
    assert ctx["decision"]["blockers"] == []
