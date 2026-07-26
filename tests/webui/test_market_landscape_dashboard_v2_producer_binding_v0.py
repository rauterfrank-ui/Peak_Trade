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
    DOUBLE_PLAY_PRODUCER_MODULE,
    DOUBLE_PLAY_SOURCE_KIND,
    LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
    LANDSCAPE_PHASE42_MAX_AGE_SECONDS,
    LANDSCAPE_PHASE43A_MAX_AGE_SECONDS,
    LANDSCAPE_PHASE43B_MAX_AGE_SECONDS,
    LANDSCAPE_PHASE44A_MAX_AGE_SECONDS,
    REASON_ARCHIVE_ROOT_UNSET,
    REASON_DECISION_NOT_PERSISTED,
    REASON_DOUBLE_PLAY_NOT_PERSISTED,
    REASON_ECONOMIC_NOT_PERSISTED,
    REASON_MARKET_CONTEXT_NOT_PERSISTED,
    REASON_PRODUCER_DATA_STALE,
    REASON_PRODUCER_TIMESTAMP_INVALID,
    REASON_PRODUCER_TIMESTAMP_MISSING,
    REASON_SAFETY_NOT_PERSISTED,
    REASON_SCOPE_NOT_PERSISTED,
    REASON_SELECTED_FORBIDDEN_SYMBOL,
    REASON_SOURCE_CONTRADICTION,
    REASON_UNIVERSE_ABSENT,
    SAFETY_AUTHORITY_OWNER_MODULE,
    SAFETY_EVIDENCE_PRODUCER_MODULE,
    SAFETY_SOURCE_KIND,
    SCOPE_PRODUCER_MODULE,
    SCOPE_SOURCE_KIND,
    bind_market_universe_slots,
    economic_viability_evidence_fields_from_v1,
    parse_producer_utc_timestamp,
    project_economic_viability_evidence_v1,
    REASON_RISK_SIZING_NOT_PERSISTED,
    REASON_EXECUTION_NOT_PERSISTED,
    REASON_SCHEMA_MISMATCH,
    REASON_INVALID_PROVENANCE,
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
    project_double_play_snapshot_v1,
    project_dynamic_scope_snapshot_v1,
    project_safety_authority_snapshot_v1,
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
DP_PRODUCER_FRESH = datetime(2026, 7, 23, 15, 30, 0, tzinfo=timezone.utc)
DP_PRODUCER_STALE = STAMP - timedelta(seconds=LANDSCAPE_PHASE43B_MAX_AGE_SECONDS + 7200)
SAFETY_PRODUCER_FRESH = datetime(2026, 7, 23, 15, 0, 0, tzinfo=timezone.utc)
SAFETY_PRODUCER_STALE = STAMP - timedelta(seconds=LANDSCAPE_PHASE44A_MAX_AGE_SECONDS + 7200)
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
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", raising=False)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert set(slots) == {
        "market_instrument",
        "universe_ranking",
        "dynamic_scope",
        "canonical_decision",
        "double_play",
        "risk_sizing_capital",
        "safety_authority",
        "execution_reconciliation",
        "economic_summary",
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
    assert slots["double_play"].availability is Availability.MISSING_SOURCE
    assert REASON_DOUBLE_PLAY_NOT_PERSISTED in slots["double_play"].blockers
    assert slots["double_play"].overall_status is None
    assert slots["double_play"].panel_summaries == ()
    assert slots["double_play"].live_authorization is False
    assert slots["double_play"].display_only is True
    assert slots["safety_authority"].availability is Availability.MISSING_SOURCE
    assert REASON_SAFETY_NOT_PERSISTED in slots["safety_authority"].reason_codes
    assert slots["safety_authority"].kill_switch_state is None
    assert slots["safety_authority"].veto_active is None
    assert slots["economic_summary"].availability is Availability.MISSING_SOURCE
    assert REASON_ECONOMIC_NOT_PERSISTED in slots["economic_summary"].reason_codes
    assert slots["economic_summary"].economic_viability_status is None
    assert slots["economic_summary"].profit_factor is None
    assert slots["risk_sizing_capital"].availability is Availability.MISSING_SOURCE
    assert REASON_RISK_SIZING_NOT_PERSISTED in slots["risk_sizing_capital"].reason_codes
    assert slots["risk_sizing_capital"].risk_status is None
    assert slots["risk_sizing_capital"].quantity is None
    assert slots["execution_reconciliation"].availability is Availability.MISSING_SOURCE
    assert REASON_EXECUTION_NOT_PERSISTED in slots["execution_reconciliation"].reason_codes
    assert slots["execution_reconciliation"].execution_status is None
    assert slots["execution_reconciliation"].order_intent_ref is None


def test_bind_rejects_inventing_market_without_required_fields() -> None:
    with pytest.raises(KeyError):
        bind_market_universe_slots(
            generated_at=STAMP,
            market_instrument_fields={"venue": "OKX"},
        )


def test_bind_available_when_producer_fields_supplied(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", raising=False)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
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
    # captured_at may be null in canonical OKX intake; fall back to readmodel generated_at.
    assert slots_nocap["market_instrument"].availability is Availability.AVAILABLE
    assert slots_nocap["market_instrument"].venue in {"OKX", "okx"}
    assert slots_nocap["market_instrument"].instrument_id == "ETH-USDT-SWAP"
    assert slots_nocap["market_instrument"].provenance.generated_at == PRODUCER_FRESH


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
    assert ctx["phase"] == "PHASE_4_5_RISK_SIZING_AND_EXECUTION_RECONCILIATION_BINDING"
    assert ctx["chart"]["ohlcv"] is None
    assert ctx["scope"]["availability"] == "MISSING_SOURCE"
    assert ctx["decision"]["availability"] == "MISSING_SOURCE"
    assert ctx["double_play"]["availability"] == "MISSING_SOURCE"
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
        assert "regime" not in ctx["global_strip"]
        assert "scope" not in ctx["global_strip"]
        assert ctx["double_play"]["availability"] == "MISSING_SOURCE"


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
    assert page.double_play.availability is Availability.MISSING_SOURCE
    assert REASON_DOUBLE_PLAY_NOT_PERSISTED in page.double_play.blockers
    assert ctx["double_play"]["availability"] == "MISSING_SOURCE"
    assert ctx["phase"] == "PHASE_4_5_RISK_SIZING_AND_EXECUTION_RECONCILIATION_BINDING"
    assert ctx["product_flags"]["phase_4_3a_binding_active"] is True
    assert ctx["product_flags"]["phase_4_3b_binding_active"] is True
    assert ctx["product_flags"]["phase_4_4a_binding_active"] is True
    assert ctx["decision"]["fields"]["decision"] == "observe"
    assert ctx["decision"]["fields"]["direction"] == "neutral_observe"
    assert ctx["decision"]["blockers"] == []


def _double_play_fields(**overrides: object) -> dict[str, object]:
    """Bounded test-injection payload — not durable dashboard truth."""
    base: dict[str, object] = {
        "overall_status": "display_ready",
        "panel_summaries": (
            {
                "name": "composition",
                "status": "display_ready",
                "summary": "Composition: ELIGIBLE_MODEL_ONLY — data-only; not trading-ready.",
                "blockers": (),
            },
            {
                "name": "state_transition",
                "status": "display_ready",
                "summary": "Transition allowed (model label): NOOP",
                "blockers": (),
            },
        ),
        "blockers": (),
        "display_only": True,
        "live_authorization": False,
        "generated_at": DP_PRODUCER_FRESH,
        "effective_at": DP_PRODUCER_FRESH,
        "source_reference": "double-play://bounded-test-injection",
        "evidence_digest": "d" * 64,
    }
    base.update(overrides)
    return base


def test_project_double_play_field_copy_immutable() -> None:
    snap = project_double_play_snapshot_v1(
        overall_status="display_ready",
        panel_summaries=({"name": "composition", "status": "display_ready"},),
        blockers=(),
        generated_at=DP_PRODUCER_FRESH,
        source_reference="double-play://bounded-test-injection",
        evidence_digest="d" * 64,
    )
    assert snap.availability is Availability.AVAILABLE
    assert snap.overall_status == "display_ready"
    assert snap.panel_summaries[0]["name"] == "composition"
    assert snap.blockers == ()
    assert snap.display_only is True
    assert snap.live_authorization is False
    assert snap.provenance.producer_module == DOUBLE_PLAY_PRODUCER_MODULE
    assert snap.provenance.source_kind == DOUBLE_PLAY_SOURCE_KIND
    with pytest.raises(FrozenInstanceError):
        snap.overall_status = "x"  # type: ignore[misc]


def test_bind_double_play_available_exact_projection() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        double_play_fields=_double_play_fields(),
    )
    dp = slots["double_play"]
    assert dp.availability is Availability.AVAILABLE
    assert dp.overall_status == "display_ready"
    assert dp.panel_summaries[0]["name"] == "composition"
    assert dp.panel_summaries[0]["status"] == "display_ready"
    assert dp.panel_summaries[1]["name"] == "state_transition"
    assert dp.blockers == ()
    assert dp.display_only is True
    assert dp.live_authorization is False
    assert dp.provenance.producer_module == DOUBLE_PLAY_PRODUCER_MODULE
    assert dp.provenance.source_kind == DOUBLE_PLAY_SOURCE_KIND
    assert dp.provenance.evidence_digest == "d" * 64
    assert dp.provenance.generated_at == DP_PRODUCER_FRESH
    assert dp.freshness.observed_at == DP_PRODUCER_FRESH
    assert dp.freshness.is_stale is False


def test_bind_double_play_rejects_missing_required_keys() -> None:
    with pytest.raises(KeyError, match="double_play_fields missing"):
        bind_market_universe_slots(
            generated_at=STAMP,
            double_play_fields={"overall_status": "display_ready"},
        )


def test_bind_double_play_invalid_naive_timestamp() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        double_play_fields=_double_play_fields(
            generated_at=datetime(2026, 7, 23, 15, 30, 0),  # naive
            effective_at=None,
        ),
    )
    dp = slots["double_play"]
    assert dp.availability is Availability.INVALID
    assert REASON_PRODUCER_TIMESTAMP_INVALID in dp.blockers
    assert dp.overall_status is None


def test_bind_double_play_rejects_live_authorization_true() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        double_play_fields=_double_play_fields(live_authorization=True),
    )
    dp = slots["double_play"]
    assert dp.availability is Availability.INVALID
    assert "CANONICAL_DOUBLE_PLAY_LIVE_AUTHORIZATION_FORBIDDEN" in dp.blockers
    assert dp.overall_status is None


def test_bind_double_play_stale_retains_display_facts() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        double_play_fields=_double_play_fields(
            generated_at=DP_PRODUCER_STALE,
            effective_at=DP_PRODUCER_STALE,
        ),
    )
    dp = slots["double_play"]
    assert dp.availability is Availability.STALE
    assert dp.overall_status == "display_ready"
    assert dp.panel_summaries[0]["name"] == "composition"
    assert dp.blockers == ()
    assert dp.freshness.is_stale is True
    assert dp.freshness.stale_reason == REASON_PRODUCER_DATA_STALE
    assert dp.provenance.generated_at == DP_PRODUCER_STALE
    assert dp.provenance.generated_at != STAMP


def test_decision_and_double_play_remain_separate_projections() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        canonical_decision_fields=_decision_fields(),
        double_play_fields=_double_play_fields(
            blockers=("survival_blocked",),
            panel_summaries=(
                {
                    "name": "composition",
                    "status": "display_blocked",
                    "summary": "Composition blocked (data-only).",
                    "blockers": ("survival_blocked",),
                },
            ),
            overall_status="display_blocked",
        ),
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    ctx = present_market_landscape_v2(page)
    assert page.canonical_decision.availability is Availability.AVAILABLE
    assert page.double_play.availability is Availability.AVAILABLE
    # No cross-enrichment: Decision reason codes stay Decision-only.
    assert page.canonical_decision.reason_codes == ("WARMUP_ACTIVE", "NO_ENTRY")
    assert page.canonical_decision.blockers == ()
    assert "survival_blocked" not in page.canonical_decision.reason_codes
    assert "WARMUP_ACTIVE" not in page.double_play.blockers
    assert page.double_play.blockers == ("survival_blocked",)
    assert page.double_play.overall_status == "display_blocked"
    assert ctx["decision"]["fields"]["decision"] == "observe"
    assert ctx["double_play"]["fields"]["overall_status"] == "display_blocked"
    assert ctx["phase"] == "PHASE_4_5_RISK_SIZING_AND_EXECUTION_RECONCILIATION_BINDING"


def _safety_authority_fields(**overrides: object) -> dict[str, object]:
    """Bounded test-injection payload — not durable dashboard truth."""
    base: dict[str, object] = {
        "kill_switch_state": "KILLED",
        "veto_active": True,
        "reason_codes": ("killswitch_block_new", "reconciliation_required"),
        "generated_at": SAFETY_PRODUCER_FRESH,
        "saved_at": SAFETY_PRODUCER_FRESH,
        "killswitch_owner_ref": SAFETY_AUTHORITY_OWNER_MODULE,
        "semantic_digest": "e" * 64,
    }
    base.update(overrides)
    return base


def test_project_safety_authority_field_copy_immutable() -> None:
    snap = project_safety_authority_snapshot_v1(
        kill_switch_state="KILLED",
        veto_active=True,
        reason_codes=("killswitch_block_new",),
        generated_at=SAFETY_PRODUCER_FRESH,
        source_reference=SAFETY_AUTHORITY_OWNER_MODULE,
        evidence_digest="e" * 64,
    )
    assert snap.availability is Availability.AVAILABLE
    assert snap.kill_switch_state == "KILLED"
    assert snap.veto_active is True
    assert snap.reason_codes == ("killswitch_block_new",)
    assert snap.provenance.producer_module == SAFETY_EVIDENCE_PRODUCER_MODULE
    assert snap.provenance.source_kind == SAFETY_SOURCE_KIND
    with pytest.raises(FrozenInstanceError):
        snap.kill_switch_state = "ACTIVE"  # type: ignore[misc]


def test_bind_safety_available_exact_projection() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        safety_authority_fields=_safety_authority_fields(),
    )
    safety = slots["safety_authority"]
    assert safety.availability is Availability.AVAILABLE
    assert safety.kill_switch_state == "KILLED"
    assert safety.veto_active is True
    assert safety.reason_codes == ("killswitch_block_new", "reconciliation_required")
    assert safety.provenance.producer_module == SAFETY_EVIDENCE_PRODUCER_MODULE
    assert safety.provenance.source_kind == SAFETY_SOURCE_KIND
    assert safety.provenance.source_reference == SAFETY_AUTHORITY_OWNER_MODULE
    assert safety.provenance.evidence_digest == "e" * 64
    assert safety.provenance.generated_at == SAFETY_PRODUCER_FRESH
    assert safety.provenance.effective_at == SAFETY_PRODUCER_FRESH
    assert safety.freshness.is_stale is False
    # Risk / capital / sizing wired but absent without injection.
    assert slots["risk_sizing_capital"].availability is Availability.MISSING_SOURCE
    assert slots["execution_reconciliation"].availability is Availability.MISSING_SOURCE


def test_bind_safety_rejects_missing_required_keys() -> None:
    with pytest.raises(KeyError, match="safety_authority_fields missing"):
        bind_market_universe_slots(
            generated_at=STAMP,
            safety_authority_fields={"kill_switch_state": "KILLED"},
        )


def test_bind_safety_rejects_non_bool_veto() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        safety_authority_fields=_safety_authority_fields(veto_active="yes"),
    )
    safety = slots["safety_authority"]
    assert safety.availability is Availability.INVALID
    assert "CANONICAL_SAFETY_VETO_ACTIVE_INVALID" in safety.reason_codes
    assert safety.kill_switch_state is None
    assert safety.veto_active is None


def test_bind_safety_no_healthy_default_invented() -> None:
    slots = bind_market_universe_slots(generated_at=STAMP)
    safety = slots["safety_authority"]
    assert safety.availability is Availability.MISSING_SOURCE
    assert safety.kill_switch_state is None
    assert safety.veto_active is None
    assert safety.kill_switch_state != "ACTIVE"
    assert safety.kill_switch_state != "normal"


def test_bind_safety_stale_retains_exact_fields() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        safety_authority_fields=_safety_authority_fields(
            generated_at=SAFETY_PRODUCER_STALE,
            saved_at=SAFETY_PRODUCER_STALE,
        ),
    )
    safety = slots["safety_authority"]
    assert safety.availability is Availability.STALE
    assert safety.kill_switch_state == "KILLED"
    assert safety.veto_active is True
    assert safety.reason_codes == ("killswitch_block_new", "reconciliation_required")
    assert REASON_PRODUCER_DATA_STALE in safety.freshness.stale_reason


def test_safety_does_not_bind_risk_capital_sizing() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        safety_authority_fields=_safety_authority_fields(),
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    ctx = present_market_landscape_v2(page)
    assert page.safety_authority.availability is Availability.AVAILABLE
    assert page.risk_sizing_capital.availability is Availability.MISSING_SOURCE
    assert page.risk_sizing_capital.risk_status is None
    assert page.risk_sizing_capital.sizing_status is None
    assert page.risk_sizing_capital.capital_status is None
    assert page.risk_sizing_capital.quantity is None
    assert ctx["risk"]["availability"] == "MISSING_SOURCE"
    assert page.execution_reconciliation.availability is Availability.MISSING_SOURCE
    assert ctx["execution"]["availability"] == "MISSING_SOURCE"
    assert ctx["global_strip"]["safety_status"] == "KILLED · veto=True"
    assert ctx["phase"] == "PHASE_4_5_RISK_SIZING_AND_EXECUTION_RECONCILIATION_BINDING"
    assert ctx["product_flags"]["phase_4_4a_binding_active"] is True
    assert ctx["product_flags"]["phase_4_4b_binding_active"] is True
    assert ctx["product_flags"]["phase_4_5_binding_active"] is True
    assert ctx["product_flags"]["phase_4_6b_binding_active"] is True
    assert ctx["product_flags"]["dashboard_authority"] is False


def _metric(*, value: float | None = None, semantic: str = "COMPUTED") -> dict[str, object]:
    payload: dict[str, object] = {"semantic": semantic}
    if value is not None:
        payload["value"] = value
    return payload


def _economic_fields(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "status": "ECONOMICALLY_VIABLE_OFFLINE",
        "economic_validity_proven": True,
        "profitability_claim_allowed": False,
        "policy_threshold_status": "PASS",
        "policy_version": "economic_validity_policy_v1",
        "authority_effect": "NONE",
        "runtime_effect": False,
        "order_effect": False,
        "reason_codes": ("SENTINEL_REASON_A", "SENTINEL_REASON_B"),
        "profit_factor": _metric(value=1.77),
        "net_return": _metric(value=0.123),
        "max_drawdown": _metric(value=-0.045),
        "sharpe": _metric(value=0.88),
        "trade_count": _metric(value=42.0),
        "funding_drag": _metric(value=-0.003),
        "contract_version": "v1",
        "owner": "backtest.economic_viability_evidence_v1",
        "strategy_id": "sentinel_strategy",
        "strategy_version": "sentinel_v9",
        "config_digest": "c" * 64,
        "implementation_digest": "i" * 64,
        "data_digest": "d" * 64,
        "manifest_digest": "m" * 64,
        "wiring_chain_digest": "w" * 64,
        "policy_digest": "p" * 64,
        "generated_at": SAFETY_PRODUCER_FRESH,
        "source_reference": "evidence://economic/sentinel",
        "evidence_digest": "m" * 64,
    }
    base.update(overrides)
    return base


def _make_economic_evidence(**overrides: object):
    from src.backtest.economic_viability_evidence_v1 import (
        EconomicViabilityEvidenceV1,
        EconomicViabilityStatus,
        MetricFieldV1,
        MetricSemantic,
    )

    def mf(value: float | None = None) -> MetricFieldV1:
        if value is None:
            return MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED)
        return MetricFieldV1(semantic=MetricSemantic.COMPUTED, value=value)

    kwargs: dict[str, object] = {
        "contract_version": "v1",
        "owner": "backtest.economic_viability_evidence_v1",
        "strategy_id": "sentinel_strategy",
        "strategy_version": "sentinel_v9",
        "instrument_id_or_universe": "ETH-USDT-SWAP",
        "canonical_trading_logic_version": "v1",
        "data_period": "p",
        "training_period": "p",
        "validation_period": "p",
        "out_of_sample_period": "p",
        "fee_model_version": "backtest_cost_v0",
        "slippage_model_version": "backtest_cost_v0",
        "funding_model_version": "funding_v1",
        "execution_model_version": "research_conservative_bps_v1",
        "config_digest": "c" * 64,
        "implementation_digest": "i" * 64,
        "data_digest": "d" * 64,
        "gross_return": mf(0.2),
        "net_return": mf(0.123),
        "net_expectancy": mf(0.01),
        "profit_factor": mf(1.77),
        "sharpe": mf(0.88),
        "sortino": mf(),
        "max_drawdown": mf(-0.045),
        "calmar": mf(),
        "trade_count": mf(42.0),
        "turnover": mf(),
        "fee_drag": mf(),
        "funding_drag": mf(-0.003),
        "slippage_impact": mf(),
        "tail_loss": mf(),
        "time_in_market": mf(),
        "long_contribution": mf(),
        "short_contribution": mf(),
        "regime_breakdown": {},
        "portfolio_contribution": {},
        "walk_forward_results": {},
        "monte_carlo_results": {},
        "stress_results": {},
        "parameter_sensitivity_results": {},
        "parameter_neighbor_degradation": mf(),
        "single_trade_profit_contribution": mf(),
        "single_regime_profit_contribution": mf(),
        "status": EconomicViabilityStatus.ECONOMICALLY_VIABLE_OFFLINE,
        "reason_codes": ("SENTINEL_REASON_A", "SENTINEL_REASON_B"),
        "manifest_digest": "m" * 64,
        "wiring_chain_digest": "w" * 64,
        "randomness_seed": 7,
        "data_admissibility": {},
        "cost_binding": {},
        "policy_version": "economic_validity_policy_v1",
        "policy_digest": "p" * 64,
        "policy_threshold_status": "PASS",
        "economic_validity_proven": True,
        "profitability_claim_allowed": False,
        "authority_effect": "NONE",
        "runtime_effect": False,
        "order_effect": False,
    }
    kwargs.update(overrides)
    return EconomicViabilityEvidenceV1(**kwargs)


def test_economic_missing_source_without_injection() -> None:
    slots = bind_market_universe_slots(generated_at=STAMP)
    economic = slots["economic_summary"]
    assert economic.availability is Availability.MISSING_SOURCE
    assert REASON_ECONOMIC_NOT_PERSISTED in economic.reason_codes
    assert economic.economic_viability_status is None
    assert economic.economic_validity_proven is None
    assert economic.policy_threshold_status is None
    assert economic.profit_factor is None
    assert economic.evidence_ref is None


def test_economic_field_for_field_injection_via_fields() -> None:
    fields = _economic_fields()
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        economic_viability_evidence_fields=fields,
    )
    economic = slots["economic_summary"]
    assert economic.availability is Availability.AVAILABLE
    assert economic.economic_viability_status == "ECONOMICALLY_VIABLE_OFFLINE"
    assert economic.economic_validity_proven is True
    assert economic.profitability_claim_allowed is False
    assert economic.policy_threshold_status == "PASS"
    assert economic.policy_version == "economic_validity_policy_v1"
    assert economic.authority_effect == "NONE"
    assert economic.runtime_effect is False
    assert economic.order_effect is False
    assert economic.reason_codes == ("SENTINEL_REASON_A", "SENTINEL_REASON_B")
    assert economic.profit_factor == {"semantic": "COMPUTED", "value": 1.77}
    assert economic.net_return == {"semantic": "COMPUTED", "value": 0.123}
    assert economic.max_drawdown == {"semantic": "COMPUTED", "value": -0.045}
    assert economic.sharpe == {"semantic": "COMPUTED", "value": 0.88}
    assert economic.trade_count == {"semantic": "COMPUTED", "value": 42.0}
    assert economic.funding_drag == {"semantic": "COMPUTED", "value": -0.003}
    assert economic.contract_version == "v1"
    assert economic.owner == "backtest.economic_viability_evidence_v1"
    assert economic.strategy_id == "sentinel_strategy"
    assert economic.strategy_version == "sentinel_v9"
    assert economic.config_digest == "c" * 64
    assert economic.implementation_digest == "i" * 64
    assert economic.data_digest == "d" * 64
    assert economic.manifest_digest == "m" * 64
    assert economic.wiring_chain_digest == "w" * 64
    assert economic.policy_digest == "p" * 64
    assert economic.provenance.evidence_digest == "m" * 64
    assert economic.provenance.source_reference == "evidence://economic/sentinel"
    assert economic.provenance.producer_module.endswith("economic_viability_evidence_v1")
    payload = serialize_projection(economic)
    assert "economic_gate_status" not in payload
    assert "promotion" not in payload
    assert "HOLDOUT" not in payload
    assert "DEVELOPMENT" not in payload
    assert "SEALED" not in payload


def test_economic_explicit_evidence_object_projection_immutable() -> None:
    evidence = _make_economic_evidence()
    before = (
        evidence.status.value,
        evidence.economic_validity_proven,
        evidence.profit_factor.to_dict(),
        evidence.reason_codes,
        evidence.manifest_digest,
    )
    snap = project_economic_viability_evidence_v1(
        evidence,
        generated_at=SAFETY_PRODUCER_FRESH,
        as_of=STAMP,
        source_reference="path/DEVELOPMENT/HOLDOUT/SEALED/artifact.json",
    )
    assert snap.availability is Availability.AVAILABLE
    assert snap.economic_viability_status == "ECONOMICALLY_VIABLE_OFFLINE"
    assert snap.economic_validity_proven is True
    assert snap.profit_factor == {"semantic": "COMPUTED", "value": 1.77}
    assert snap.reason_codes == ("SENTINEL_REASON_A", "SENTINEL_REASON_B")
    payload = serialize_projection(snap)
    assert payload.get("lifecycle_label") is None
    assert "DEVELOPMENT_ONLY" not in payload
    assert "HOLDOUT" not in payload
    assert "SEALED_LONG_PANEL" not in payload
    assert before == (
        evidence.status.value,
        evidence.economic_validity_proven,
        evidence.profit_factor.to_dict(),
        evidence.reason_codes,
        evidence.manifest_digest,
    )
    with pytest.raises(FrozenInstanceError):
        snap.economic_viability_status = "RESEARCH_ONLY"  # type: ignore[misc]


def test_economic_validity_proven_not_recomputed_from_status() -> None:
    fields = _economic_fields(
        status="RESEARCH_ONLY",
        economic_validity_proven=True,
        policy_threshold_status="BELOW_THRESHOLD",
    )
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        economic_viability_evidence_fields=fields,
    )
    economic = slots["economic_summary"]
    assert economic.economic_viability_status == "RESEARCH_ONLY"
    assert economic.economic_validity_proven is True
    assert economic.policy_threshold_status == "BELOW_THRESHOLD"


def test_economic_promotion_isolation() -> None:
    fields = _economic_fields()
    fields["promotion_economic_gate_status"] = "PASS"
    fields["promotion_eligibility"] = True
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        economic_viability_evidence_fields=fields,
    )
    economic = slots["economic_summary"]
    payload = serialize_projection(economic)
    assert "promotion_economic_gate_status" not in payload
    assert "promotion_eligibility" not in payload
    assert economic.economic_viability_status == "ECONOMICALLY_VIABLE_OFFLINE"
    assert economic.authority_effect == "NONE"


def test_economic_no_lifecycle_inference_from_source_reference() -> None:
    fields = _economic_fields(
        source_reference="artifacts/DEVELOPMENT/HOLDOUT/SEALED/run.json",
        status="PROMISING",
        economic_validity_proven=False,
        policy_threshold_status="BELOW_THRESHOLD",
    )
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        economic_viability_evidence_fields=fields,
    )
    economic = slots["economic_summary"]
    payload = serialize_projection(economic)
    for forbidden in (
        "DEVELOPMENT_ONLY",
        "HOLDOUT",
        "SEALED_LONG_PANEL",
        "TERMINAL",
        "PREREGISTRATION_ONLY",
        "NOT_EVALUATED",
        "lifecycle_label",
        "research_lifecycle",
    ):
        assert forbidden not in payload
    assert economic.provenance.source_reference == ("artifacts/DEVELOPMENT/HOLDOUT/SEALED/run.json")


def test_economic_page_aggregate_and_presenter_injection() -> None:
    evidence = _make_economic_evidence()
    fields = economic_viability_evidence_fields_from_v1(
        evidence,
        generated_at=SAFETY_PRODUCER_FRESH,
        source_reference="evidence://economic/page",
    )
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        economic_viability_evidence_fields=fields,
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    ctx = present_market_landscape_v2(page)
    assert page.economic_summary.availability is Availability.AVAILABLE
    assert page.economic_summary.economic_viability_status == ("ECONOMICALLY_VIABLE_OFFLINE")
    assert ctx["economic"]["availability"] == "AVAILABLE"
    assert ctx["economic"]["status_display"] == "ECONOMICALLY_VIABLE_OFFLINE"
    assert ctx["product_flags"]["phase_4_6b_binding_active"] is True
    assert ctx["phase"] == "PHASE_4_5_RISK_SIZING_AND_EXECUTION_RECONCILIATION_BINDING"
    assert page.risk_sizing_capital.availability is Availability.MISSING_SOURCE


def _isolate_home_without_archive_env(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Path:
    """Isolate HOME for no-env canonical-default assertions (not under /tmp)."""
    from tests.webui.archive_root_durable_home_v1 import durable_isolated_home

    return durable_isolated_home(monkeypatch, request, label="producer_binding_default_path")


def test_exact_canonical_default_path_resolution_without_env(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    import sys

    from src.webui.workflow_dashboard_archive_root_v1 import (
        canonical_default_workflow_dashboard_archive_root,
        resolve_workflow_dashboard_archive_root,
    )

    home = _isolate_home_without_archive_env(monkeypatch, request)
    expected = canonical_default_workflow_dashboard_archive_root(
        home=home, platform=sys.platform, environ={}, repo_root=REPO
    )
    assert expected.is_absolute()
    assert expected.name == "workflow_dashboard_v1"
    assert "Peak_Trade" in expected.parts or "peak_trade" in expected.parts
    assert resolve_workflow_dashboard_archive_root(require_existing_directory=True) is None
    expected.mkdir(parents=True)
    resolved = resolve_workflow_dashboard_archive_root(require_existing_directory=True)
    assert resolved == expected.resolve()
    assert resolved is not None
    readmodel = resolved / READMODELS_DIRNAME / READMODEL_FILENAME
    assert readmodel.name == "universe_selection_readmodel.v1.json"
    assert readmodel.parent.name == "readmodels"


def test_default_path_binds_selected_instrument_and_venue_without_env(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    import sys

    from src.webui.workflow_dashboard_archive_root_v1 import (
        canonical_default_workflow_dashboard_archive_root,
    )

    home = _isolate_home_without_archive_env(monkeypatch, request)
    default_root = canonical_default_workflow_dashboard_archive_root(
        home=home, platform=sys.platform, environ={}, repo_root=REPO
    )
    archive = _write_truth_universe_archive(
        default_root,
        selected_symbol="ETH-USDT-SWAP",
    )
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["universe_ranking"].availability is Availability.AVAILABLE
    assert slots["universe_ranking"].selected_instrument_id == "ETH-USDT-SWAP"
    assert slots["market_instrument"].availability is Availability.AVAILABLE
    assert slots["market_instrument"].instrument_id == "ETH-USDT-SWAP"
    assert slots["market_instrument"].venue == "OKX"
    assert slots["market_instrument"].mark_price is None
    assert "SELECTED_INSTRUMENT_IDENTITY_FROM_UNIVERSE_SELECTION" in (
        slots["market_instrument"].reason_codes
    )
    ctx = present_market_landscape_v2(
        MarketDashboardReadServiceV1().load_page_snapshot(
            generated_at=STAMP,
            slot_overrides=slots,
        )
    )
    assert ctx["global_strip"]["instrument"] == "ETH-USDT-SWAP"
    assert ctx["global_strip"]["venue"] == "OKX"
    assert ctx["selected_instrument_id"] == "ETH-USDT-SWAP"
    assert ctx["source_health"]["slot_availability"]["universe_ranking"] == "AVAILABLE"
    assert "OHLCV" in ctx["chart"]["message"].upper() or "ohlcv" in ctx["chart"]["message"].lower()
    assert "unbound" in ctx["chart"]["message"].lower()
    # Explicit injection still unused; default path alone sufficed.
    assert archive == default_root


def test_default_path_missing_archive_remains_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    _isolate_home_without_archive_env(monkeypatch, request)
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["universe_ranking"].availability is Availability.MISSING_SOURCE
    assert REASON_ARCHIVE_ROOT_UNSET in slots["universe_ranking"].reason_codes
    assert slots["market_instrument"].availability is Availability.MISSING_SOURCE


def test_default_path_missing_readmodel_remains_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    import sys

    from src.webui.workflow_dashboard_archive_root_v1 import (
        canonical_default_workflow_dashboard_archive_root,
    )

    home = _isolate_home_without_archive_env(monkeypatch, request)
    default_root = canonical_default_workflow_dashboard_archive_root(
        home=home, platform=sys.platform, environ={}, repo_root=REPO
    )
    default_root.mkdir(parents=True)
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["universe_ranking"].availability is Availability.MISSING_SOURCE
    assert REASON_UNIVERSE_ABSENT in slots["universe_ranking"].reason_codes


def test_default_path_invalid_schema_remains_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    import sys

    from src.webui.workflow_dashboard_archive_root_v1 import (
        canonical_default_workflow_dashboard_archive_root,
    )

    home = _isolate_home_without_archive_env(monkeypatch, request)
    default_root = canonical_default_workflow_dashboard_archive_root(
        home=home, platform=sys.platform, environ={}, repo_root=REPO
    )
    readmodels = default_root / READMODELS_DIRNAME
    readmodels.mkdir(parents=True)
    bad = {
        "schema_name": "universe_selection_readmodel.v1",
        "schema_version": 1,
        "generated_at": "2026-07-23T17:00:00Z",
        "source_run_id": "bad",
        "source_stage": "paper",
        "non_authorizing": True,
        "universe": [],
        "ranking": [],
        "selected_future": {
            "row_id": "s-btc",
            "symbol": "BTC/USD",
            "rank": 1,
            "truth_status": "PERSISTED",
        },
        "market_snapshot": {
            "truth_status": "PERSISTED",
            "source_kind": "governed_producer",
            "snapshot_id": "snap-bad",
            "exchange": "OKX",
            "captured_at": "2026-07-23T16:59:00Z",
        },
        "evidence": {
            "producer_contract": "universe_selection_producer.v1",
            "storage_target": "readmodels/universe_selection_readmodel.v1.json",
            "links": [],
        },
        "missing_truth": {
            "universe": "UNIVERSE_SOURCE_NOT_PERSISTED",
            "ranking": "TOP20_RANKING_NOT_PERSISTED",
            "selected_future": "PERSISTED",
            "future_detail": "AVAILABLE",
            "orders_fills_pnl": "NOT_PERSISTED",
        },
    }
    (readmodels / READMODEL_FILENAME).write_text(
        json.dumps(bad, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_manifest_sha256(readmodels)
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["universe_ranking"].availability is Availability.INVALID


def test_bind_market_universe_slots_has_no_write_capability() -> None:
    import inspect

    from src.webui import market_dashboard_landscape_producer_binding_v2 as mod

    source = inspect.getsource(mod)
    for token in (
        "write_universe_selection_readmodel",
        "write_missing_truth_universe_selection_readmodel",
        "os.replace",
        "Path.write_text",
        "open(",
    ):
        assert token not in source
    assert "try_load_universe_selection_for_dashboard" in source


RISK_PRODUCER_FRESH = datetime(2026, 7, 23, 15, 0, 0, tzinfo=timezone.utc)
RISK_PRODUCER_STALE = STAMP - timedelta(seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS + 3600)
EXEC_PRODUCER_FRESH = datetime(2026, 7, 23, 15, 30, 0, tzinfo=timezone.utc)


def _risk_sizing_capital_fields(**overrides: object) -> dict[str, object]:
    """Bounded test-injection payload — not durable dashboard truth."""
    payload: dict[str, object] = {
        "risk_status": "PASS",
        "sizing_status": "PASS",
        "capital_status": "PASS",
        "quantity": 0.25,
        "reason_codes": ("PASS",),
        "generated_at": RISK_PRODUCER_FRESH,
        "effective_at": RISK_PRODUCER_FRESH,
        "source_reference": "risk://bounded-test-injection",
        "risk_sizing_ref": "r" * 64,
        "schema_version": "v1",
    }
    payload.update(overrides)
    return payload


def _execution_reconciliation_fields(**overrides: object) -> dict[str, object]:
    """Bounded test-injection payload — not durable dashboard truth."""
    payload: dict[str, object] = {
        "execution_status": "BOUND_OFFLINE",
        "reconciliation_status": "RECONCILED",
        "order_intent_ref": "intent://" + ("a" * 16),
        "reason_codes": ("PASS",),
        "generated_at": EXEC_PRODUCER_FRESH,
        "effective_at": EXEC_PRODUCER_FRESH,
        "source_reference": "execution://bounded-test-injection",
        "semantic_digest": "b" * 64,
        "schema_version": "v1",
    }
    payload.update(overrides)
    return payload


def test_risk_and_execution_field_for_field_injection() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        risk_sizing_capital_fields=_risk_sizing_capital_fields(),
        execution_reconciliation_fields=_execution_reconciliation_fields(),
    )
    risk = slots["risk_sizing_capital"]
    execution = slots["execution_reconciliation"]
    assert risk.availability is Availability.AVAILABLE
    assert risk.risk_status == "PASS"
    assert risk.sizing_status == "PASS"
    assert risk.capital_status == "PASS"
    assert risk.quantity == 0.25
    assert risk.reason_codes == ("PASS",)
    assert risk.provenance.source_reference == "risk://bounded-test-injection"
    assert execution.availability is Availability.AVAILABLE
    assert execution.execution_status == "BOUND_OFFLINE"
    assert execution.reconciliation_status == "RECONCILED"
    assert execution.order_intent_ref == "intent://" + ("a" * 16)
    assert execution.reason_codes == ("PASS",)
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    ctx = present_market_landscape_v2(page)
    assert ctx["risk"]["availability"] == "AVAILABLE"
    assert ctx["risk"]["risk_status_display"] == "PASS"
    assert ctx["risk"]["quantity_display"] == "0.25"
    assert ctx["execution"]["availability"] == "AVAILABLE"
    assert ctx["execution"]["execution_status_display"] == "BOUND_OFFLINE"
    assert ctx["execution"]["reconciliation_status_display"] == "RECONCILED"
    assert ctx["product_flags"]["phase_4_4b_binding_active"] is True
    assert ctx["product_flags"]["phase_4_5_binding_active"] is True


def test_risk_absent_execution_available() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        execution_reconciliation_fields=_execution_reconciliation_fields(),
    )
    assert slots["risk_sizing_capital"].availability is Availability.MISSING_SOURCE
    assert slots["execution_reconciliation"].availability is Availability.AVAILABLE
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    ctx = present_market_landscape_v2(page)
    assert ctx["risk"]["availability"] == "MISSING_SOURCE"
    assert ctx["execution"]["availability"] == "AVAILABLE"


def test_execution_absent_risk_available() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        risk_sizing_capital_fields=_risk_sizing_capital_fields(),
    )
    assert slots["risk_sizing_capital"].availability is Availability.AVAILABLE
    assert slots["execution_reconciliation"].availability is Availability.MISSING_SOURCE


def test_risk_stale_hides_quantity() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        risk_sizing_capital_fields=_risk_sizing_capital_fields(
            generated_at=RISK_PRODUCER_STALE,
            effective_at=RISK_PRODUCER_STALE,
        ),
    )
    risk = slots["risk_sizing_capital"]
    assert risk.availability is Availability.STALE
    assert risk.risk_status == "PASS"
    assert risk.quantity is None
    assert risk.freshness.is_stale is True
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    ctx = present_market_landscape_v2(page)
    assert ctx["risk"]["availability"] == "STALE"
    assert ctx["risk"]["quantity_display"] == "—"


def test_execution_partial_without_reconciliation_status() -> None:
    fields = _execution_reconciliation_fields()
    del fields["reconciliation_status"]
    del fields["order_intent_ref"]
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        execution_reconciliation_fields=fields,
    )
    execution = slots["execution_reconciliation"]
    assert execution.availability is Availability.AVAILABLE
    assert execution.execution_status == "BOUND_OFFLINE"
    assert execution.reconciliation_status is None
    assert execution.order_intent_ref is None
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    ctx = present_market_landscape_v2(page)
    assert ctx["execution"]["reconciliation_status_display"] == "—"
    assert ctx["execution"]["order_intent_ref_display"] == "—"


def test_risk_schema_mismatch_fail_closed() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        risk_sizing_capital_fields=_risk_sizing_capital_fields(schema_version="v9"),
    )
    risk = slots["risk_sizing_capital"]
    assert risk.availability is Availability.INVALID
    assert REASON_SCHEMA_MISMATCH in risk.reason_codes
    assert risk.quantity is None


def test_execution_invalid_provenance_empty_status() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        execution_reconciliation_fields=_execution_reconciliation_fields(execution_status=""),
    )
    execution = slots["execution_reconciliation"]
    assert execution.availability is Availability.INVALID
    assert REASON_INVALID_PROVENANCE in execution.reason_codes


def test_risk_rejects_missing_required_keys() -> None:
    with pytest.raises(KeyError, match="risk_sizing_capital_fields missing"):
        bind_market_universe_slots(
            generated_at=STAMP,
            risk_sizing_capital_fields={
                "risk_status": "PASS",
                "generated_at": RISK_PRODUCER_FRESH,
            },
        )


def test_execution_rejects_missing_required_keys() -> None:
    with pytest.raises(KeyError, match="execution_reconciliation_fields missing"):
        bind_market_universe_slots(
            generated_at=STAMP,
            execution_reconciliation_fields={"generated_at": EXEC_PRODUCER_FRESH},
        )


def test_no_silent_defaults_for_uninjected_operative_slots() -> None:
    slots = bind_market_universe_slots(generated_at=STAMP)
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    ctx = present_market_landscape_v2(page)
    assert page.risk_sizing_capital.availability is Availability.MISSING_SOURCE
    assert page.execution_reconciliation.availability is Availability.MISSING_SOURCE
    assert page.risk_sizing_capital.quantity is None
    assert page.execution_reconciliation.order_intent_ref is None
    assert ctx["risk"]["summary_display"] == "MISSING_SOURCE"
    assert ctx["execution"]["summary_display"] == "MISSING_SOURCE"
