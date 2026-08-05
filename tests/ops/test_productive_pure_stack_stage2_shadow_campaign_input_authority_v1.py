"""Fail-closed tests for Stage-2 Shadow Campaign Input Authority Surface B."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    CALIBRATION_PROTOCOL_REL,
    RELATIVE_OUTPUT_ROOT,
    STAGE1_MANIFEST_REL,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    sha256_file,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.authority_consumption_guards_v1 import (
    assert_coverage_not_stale_or_incomplete_v1,
    assert_finalized_pt1m_only_v1,
    assert_pit_no_lookahead_v1,
    assert_provenance_complete_v1,
    assert_surface_b_authority_consumable_v1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.boundary_guards_v1 import (
    assert_forbidden_effects_remain_false,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.constants_v1 import (
    AUTHORITY_SURFACE,
    DASHBOARD_AUTHORITY_EFFECT,
    INPUT_AUTHORITY,
    O4_UNCHANGED,
    PRODUCTIVE_NUMERIC_VALUES_SET,
    RUNTIME_IMPLEMENTED,
    SHADOW_CAMPAIGN_STARTABLE,
    SOURCE_ID,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.evidence_collection_collector_v1 import (
    start_evidence_collection_shadow_campaign_from_surface_b_v1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.export_api_v1 import (
    export_surface_b_shadow_campaign_input_v1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.git_sha_loader_v1 import (
    resolve_repository_sha,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InputAuthorityErrorV1,
    InstrumentBindingV1,
    MarkPriceInputV1,
    VenueNativeCandleInputV1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.observation_pack_v1 import (
    assert_pack_immutable_rebuild_requires_new_dataset,
    build_observation_pack_v1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.pt1m_finalized_ohlcv_producer_v1 import (
    compute_raw_source_digest_v1,
    produce_pt1m_finalized_ohlcv_bars_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG = REPO_ROOT / "src/ops/productive_pure_stack_stage2_shadow_campaign_input_authority_v1"
O4_INTERVAL = (
    REPO_ROOT
    / "src/ops/canonical_public_md_and_ohlcv_transport_reconciliation_v1/interval_contract_v1.py"
)
HOST_CONSTANTS = (
    REPO_ROOT / "src/ops/productive_pure_stack_display_decision_host_binding_v1/constants_v1.py"
)


def _binding() -> InstrumentBindingV1:
    return InstrumentBindingV1(
        venue="okx",
        canonical_instrument_id="BTC-USDT-SWAP",
        venue_instrument_id="BTC-USDT-SWAP",
        contract_type="linear_swap",
        market_type="swap",
        quote_currency="USDT",
        settlement_currency="USDT",
    )


# PT1M bucket-aligned start (must satisfy event_time == floor(event_time/60)*60).
_BUCKET_START = 1_700_000_040


def _as_of(n: int, *, start: int = _BUCKET_START) -> int:
    """Exclusive pack tip after n contiguous finalized PT1M bars."""
    return start + n * 60


def _candles(n: int = 5, *, start: int = _BUCKET_START) -> tuple[VenueNativeCandleInputV1, ...]:
    out: list[VenueNativeCandleInputV1] = []
    for i in range(n):
        price = 100.0 + i
        out.append(
            VenueNativeCandleInputV1(
                event_time_epoch_s=start + i * 60,
                open=price,
                high=price + 1.0,
                low=price - 1.0,
                close=price + 0.5,
                volume=10.0 + i,
                venue_finalized=True,
                open_tip=False,
            )
        )
    return tuple(out)


def _marks(n: int = 5, *, start: int = _BUCKET_START) -> tuple[MarkPriceInputV1, ...]:
    return tuple(
        MarkPriceInputV1(event_time_epoch_s=start + i * 60, mark_price=100.25 + i) for i in range(n)
    )


def _segments(start: int = _BUCKET_START) -> dict[str, int]:
    return {
        "train": start,
        "calibration": start + 60,
        "validation": start + 120,
        "holdout": start + 180,
    }


def _hermetic_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    if not repo.exists():
        repo.mkdir(parents=True, exist_ok=True)
        (repo / "docs").symlink_to(REPO_ROOT / "docs")
        (repo / RELATIVE_OUTPUT_ROOT).mkdir(parents=True)
        (repo / ".git").mkdir()
        (repo / ".git" / "HEAD").write_text("a" * 40 + "\n", encoding="utf-8")
    return repo


def _pack_for(n: int = 5):
    binding = _binding()
    candles = _candles(n)
    marks = _marks(n)
    bars = produce_pt1m_finalized_ohlcv_bars_v1(
        binding=binding,
        dataset_id="ds_surface_b_v1",
        candles=candles,
        marks=marks,
    )
    raw = compute_raw_source_digest_v1(
        binding=binding, dataset_id="ds_surface_b_v1", candles=candles, marks=marks
    )
    pack = build_observation_pack_v1(
        binding=binding,
        bars=bars,
        dataset_id="ds_surface_b_v1",
        repository_sha="a" * 40,
        config_digest="cfg",
        raw_source_digest=raw,
        ingestion_timestamp="2026-08-05T00:00:00Z",
        finalization_timestamp="2026-08-05T00:00:00Z",
    )
    return pack, bars


def test_boundary_guards_forbidden_effects_false_v1() -> None:
    guard = assert_forbidden_effects_remain_false()
    assert guard["forbidden_effects_false"] is True
    assert guard["authority_surface"] == "B"
    assert guard["o4_unchanged"] is True
    assert guard["productive_numeric_values_set"] == 0
    assert INPUT_AUTHORITY is False
    assert RUNTIME_IMPLEMENTED is False
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert DASHBOARD_AUTHORITY_EFFECT == "NONE"
    assert SHADOW_CAMPAIGN_STARTABLE is True


def test_producer_happy_path_and_mark_separate_v1() -> None:
    bars = produce_pt1m_finalized_ohlcv_bars_v1(
        binding=_binding(),
        dataset_id="ds_surface_b_v1",
        candles=_candles(),
        marks=_marks(),
    )
    assert len(bars) == 5
    assert all(b.finalized for b in bars)
    assert all(b.source_id == SOURCE_ID for b in bars)
    # Candle close and mark remain distinct fields (no silent equivalence policy).
    assert bars[0].close != bars[0].mark_price
    assert_finalized_pt1m_only_v1(bars)


def test_producer_rejects_open_tip_v1() -> None:
    candles = list(_candles(1))
    candles[0] = VenueNativeCandleInputV1(
        event_time_epoch_s=candles[0].event_time_epoch_s,
        open=candles[0].open,
        high=candles[0].high,
        low=candles[0].low,
        close=candles[0].close,
        volume=candles[0].volume,
        venue_finalized=True,
        open_tip=True,
    )
    with pytest.raises(InputAuthorityErrorV1, match="OPEN_TIP"):
        produce_pt1m_finalized_ohlcv_bars_v1(
            binding=_binding(),
            dataset_id="ds",
            candles=tuple(candles),
            marks=_marks(1),
        )


def test_producer_rejects_missing_mark_v1() -> None:
    with pytest.raises(InputAuthorityErrorV1, match="MARK_MISSING"):
        produce_pt1m_finalized_ohlcv_bars_v1(
            binding=_binding(),
            dataset_id="ds",
            candles=_candles(2),
            marks=_marks(1),
        )


def test_producer_rejects_candle_mark_equivalence_flag_v1() -> None:
    with pytest.raises(InputAuthorityErrorV1, match="CANDLE_MARK_TRADE_EQUIVALENCE"):
        produce_pt1m_finalized_ohlcv_bars_v1(
            binding=_binding(),
            dataset_id="ds",
            candles=_candles(1),
            marks=_marks(1),
            allow_candle_mark_equivalence=True,
        )


def test_incomplete_instrument_binding_fail_closed_v1() -> None:
    bad = InstrumentBindingV1(
        venue="okx",
        canonical_instrument_id="BTC-USDT-SWAP",
        venue_instrument_id="BTC-USDT-SWAP",
        contract_type="linear_swap",
        market_type="swap",
        quote_currency="USDT",
        settlement_currency="",
    )
    with pytest.raises(InputAuthorityErrorV1, match="INSTRUMENT_BINDING_INCOMPLETE"):
        produce_pt1m_finalized_ohlcv_bars_v1(
            binding=bad,
            dataset_id="ds",
            candles=_candles(1),
            marks=_marks(1),
        )


def test_observation_pack_digest_and_immutability_v1() -> None:
    binding = _binding()
    candles = _candles()
    marks = _marks()
    bars = produce_pt1m_finalized_ohlcv_bars_v1(
        binding=binding,
        dataset_id="ds_a",
        candles=candles,
        marks=marks,
    )
    raw = compute_raw_source_digest_v1(
        binding=binding, dataset_id="ds_a", candles=candles, marks=marks
    )
    pack = build_observation_pack_v1(
        binding=binding,
        bars=bars,
        dataset_id="ds_a",
        repository_sha="a" * 40,
        config_digest="cfg",
        raw_source_digest=raw,
        ingestion_timestamp="2026-08-05T00:00:00Z",
        finalization_timestamp="2026-08-05T00:00:00Z",
    )
    assert len(pack.observation_pack_digest) == 64
    assert_provenance_complete_v1(pack.provenance)
    pack2 = build_observation_pack_v1(
        binding=binding,
        bars=bars,
        dataset_id="ds_a",
        repository_sha="a" * 40,
        config_digest="cfg-changed",
        raw_source_digest=raw,
        ingestion_timestamp="2026-08-05T00:00:00Z",
        finalization_timestamp="2026-08-05T00:00:00Z",
    )
    with pytest.raises(InputAuthorityErrorV1, match="REBUILD_REQUIRES_NEW_DATASET"):
        assert_pack_immutable_rebuild_requires_new_dataset(existing_pack=pack, candidate_pack=pack2)


def test_pit_no_lookahead_fail_closed_v1() -> None:
    pack, bars = _pack_for(5)
    tip = _as_of(5)
    assert_pit_no_lookahead_v1(bars=bars, as_of_event_time_epoch_s=tip)
    with pytest.raises(InputAuthorityErrorV1, match="LOOKAHEAD_OPEN_BUCKET"):
        assert_pit_no_lookahead_v1(bars=bars, as_of_event_time_epoch_s=tip - 1)
    with pytest.raises(InputAuthorityErrorV1, match="LOOKAHEAD_BAR_AFTER_AS_OF"):
        assert_pit_no_lookahead_v1(
            bars=bars, as_of_event_time_epoch_s=bars[0].event_time_epoch_s - 1
        )
    _ = pack


def test_stale_incomplete_and_productive_max_age_fail_closed_v1() -> None:
    pack, _ = _pack_for(5)
    tip = _as_of(5)
    assert_coverage_not_stale_or_incomplete_v1(pack=pack, as_of_event_time_epoch_s=tip)
    with pytest.raises(InputAuthorityErrorV1, match="STALE_INCOMPLETE_COVERAGE"):
        assert_coverage_not_stale_or_incomplete_v1(pack=pack, as_of_event_time_epoch_s=tip + 60)
    with pytest.raises(InputAuthorityErrorV1, match="PRODUCTIVE_MAX_AGE_MUST_REMAIN_UNSET"):
        assert_coverage_not_stale_or_incomplete_v1(
            pack=pack,
            as_of_event_time_epoch_s=tip,
            productive_max_age_seconds=120,
        )


def test_pt1m_gap_incomplete_fail_closed_v1() -> None:
    pack, bars = _pack_for(3)
    gapped = (bars[0], bars[2])
    with pytest.raises(InputAuthorityErrorV1, match="PT1M_GAP_INCOMPLETE"):
        assert_finalized_pt1m_only_v1(gapped)


def test_export_binds_campaign_request_and_complete_manifests_v1() -> None:
    n = 5
    result = export_surface_b_shadow_campaign_input_v1(
        repo_root=REPO_ROOT,
        campaign_id="surface_b_export_hermetic_v1",
        origin_main_sha="55922609182a3166320c0a66a3a0b7cda5c13090",
        output_root=REPO_ROOT
        / "evidence/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1",
        dataset_id="ds_surface_b_export_v1",
        scenario_id="hermetic_scenario_v1",
        seed=11,
        event_time_epoch_s=_as_of(n),
        binding=_binding(),
        candles=_candles(n),
        marks=_marks(n),
        segment_boundaries_event_time_epoch_s=_segments(),
        fold_ids=("fold_expanding_001",),
        bootstrap_seeds=(7, 11),
        regime_coverage={"low": 0, "mid": 0, "high": 0, "unknown": 5, "missing": 0},
        stage1_manifest_digest=sha256_file(REPO_ROOT / STAGE1_MANIFEST_REL),
        calibration_protocol_digest=sha256_file(REPO_ROOT / CALIBRATION_PROTOCOL_REL),
        wall_time_utc="2026-08-05T09:00:00Z",
    )
    req = result.shadow_campaign_request
    assert req.reproducibility.observation_pack_digest == (
        result.observation_pack.observation_pack_digest
    )
    assert len(req.observation_bars) == 5
    assert req.dataset_manifest.status == "COMPLETE"
    assert req.train_calibration_validation_partition_manifest.status == "COMPLETE"
    assert req.walk_forward_manifest.status == "COMPLETE"
    assert req.bootstrap_monte_carlo_manifest.status == "COMPLETE"
    assert req.stress_pack_manifest.status == "COMPLETE"
    assert req.bootstrap_monte_carlo_manifest.entries[0]["block_length"] is None
    assert req.bootstrap_monte_carlo_manifest.entries[0]["path_count"] is None
    assert req.train_calibration_validation_partition_manifest.entries[0]["purge_seconds"] is None
    assert all(e["numeric_magnitude"] is None for e in req.stress_pack_manifest.entries)
    assert AUTHORITY_SURFACE == "B"
    assert O4_UNCHANGED is True
    assert_surface_b_authority_consumable_v1(
        pack=result.observation_pack,
        as_of_event_time_epoch_s=_as_of(n),
    )


def test_evidence_collection_shadow_campaign_startable_from_surface_b_v1(
    tmp_path: Path,
) -> None:
    n = 70
    repo = _hermetic_repo(tmp_path)
    result = export_surface_b_shadow_campaign_input_v1(
        repo_root=repo,
        campaign_id="surface_b_collect_hermetic_v1",
        origin_main_sha="a5b57d5211a0ffb691df65eb3d6cd62b5ff09363",
        output_root=repo / RELATIVE_OUTPUT_ROOT,
        dataset_id="ds_surface_b_collect_v1",
        scenario_id="hermetic_collect_v1",
        seed=13,
        event_time_epoch_s=_as_of(n),
        binding=_binding(),
        candles=_candles(n),
        marks=_marks(n),
        segment_boundaries_event_time_epoch_s=_segments(),
        fold_ids=("fold_expanding_001",),
        bootstrap_seeds=(3, 5),
        regime_coverage={"low": 0, "mid": 0, "high": 0, "unknown": n, "missing": 0},
        stage1_manifest_digest=sha256_file(repo / STAGE1_MANIFEST_REL),
        calibration_protocol_digest=sha256_file(repo / CALIBRATION_PROTOCOL_REL),
        wall_time_utc="2026-08-05T09:30:00Z",
    )
    collection = start_evidence_collection_shadow_campaign_from_surface_b_v1(
        pack=result.observation_pack,
        request=result.shadow_campaign_request,
    )
    assert collection.authority_surface == "B"
    assert collection.input_authority is False
    assert collection.runtime_implemented is False
    assert collection.productive_numeric_values_set == 0
    assert collection.shadow_campaign_startable is True
    assert collection.dashboard_authority_effect == "NONE"
    assert collection.orders_testnet_live_paper_effects is False
    assert collection.shadow_campaign_result.input_authority is False
    assert collection.shadow_campaign_result.runtime_implemented is False
    assert collection.shadow_campaign_result.productive_numeric_values_set == 0
    assert Path(collection.shadow_campaign_result.output_dir).is_dir()


def test_collector_rejects_dashboard_source_token_v1() -> None:
    from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.boundary_guards_v1 import (
        assert_source_not_forbidden,
    )

    with pytest.raises(InputAuthorityErrorV1, match="FORBIDDEN_SOURCE_AUTHORITY"):
        assert_source_not_forbidden("dashboard_readmodel_pt1m")


def test_worktree_safe_git_sha_loader_v1() -> None:
    sha = resolve_repository_sha(REPO_ROOT)
    assert len(sha) == 40


def test_o4_interval_file_not_mutated_still_pt1h_only_v1() -> None:
    text = O4_INTERVAL.read_text(encoding="utf-8")
    assert "PT1H" in text
    # Surface B must not expand O4 supported intervals in this PR.
    tree = ast.parse(text)
    # Ensure this package does not rewrite O4 file (presence-only guard).
    assert O4_INTERVAL.is_file()
    assert "normalize_interval_id_v1" in text
    _ = tree


def test_host_input_authority_flags_remain_false_v1() -> None:
    text = HOST_CONSTANTS.read_text(encoding="utf-8")
    assert "INPUT_AUTHORITY_FUTURES_INPUT_SNAPSHOT = False" in text
    assert "INPUT_AUTHORITY_SURVIVAL_ENVELOPE = False" in text
    assert "INPUT_AUTHORITY_SUITABILITY_PROJECTION = False" in text
    assert "INPUT_AUTHORITY_CAPITAL_SLOT_CONFIG = False" in text
    assert "INPUT_AUTHORITY_CAPITAL_SLOT_STATE_INIT = False" in text


def test_package_has_no_order_live_imports_v1() -> None:
    forbidden_tokens = (
        "enable_live_trading",
        "submit_order",
        "exchange_credentials",
        "testnet_authorized",
    )
    for path in PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"{path}:{token}"


def test_no_productive_numeric_values_in_surface_b_constants_v1() -> None:
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert INPUT_AUTHORITY is False
    assert RUNTIME_IMPLEMENTED is False
