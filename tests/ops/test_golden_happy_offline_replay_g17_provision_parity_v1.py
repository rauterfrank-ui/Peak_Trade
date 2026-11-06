"""Forensic offline replay G17 provision parity (harness vs natural checkpoint)."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _productive_root(ghv) -> Path:
    prod = REPO / ghv.RUNTIME_PRODUCTIVITY_REL
    if not prod.is_dir():
        prod.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(REPO / ghv.PRODUCTIVITY_TEMPLATE_REL, prod)
    return prod


def _load_adjudication_module():
    spec = importlib.util.spec_from_file_location(
        "ghv_adj",
        REPO / "scripts/ops/run_golden_happy_natural_data_offline_witness_adjudication_v1.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_synthetic_g17_producer_yields_near_zero_volatility() -> None:
    ghv = _load_adjudication_module()
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        build_s8_occupied_lane_pairs_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.cap24_runtime_binding_witness_epoch_v1 import (
        resolve_cap24_runtime_binding_witness_epoch_v1,
    )
    from src.ops.single_selected_future_policy_v1.persistence_v1 import (
        load_and_validate_selection_v1,
    )

    prod = _productive_root(ghv)
    sel = load_and_validate_selection_v1(prod / "runtime_state/selection", require_manifest=True)
    manifest = json.loads((prod / "cap24_selection_state_publish_manifest_v1.json").read_text())
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=prod,
        repository_sha=str(manifest["repository_sha"]),
        binding_epoch=resolve_cap24_runtime_binding_witness_epoch_v1(
            selection=sel.selection,
            decision_epoch="2026-10-01T21:33:35Z",
        ),
    )
    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=REPO / "runtime/test_g17_parity_synthetic_lane",
        bound=handoff.bound_instrument,
    )
    g17, meta = ghv._build_g17_producers_for_replay_v1(
        pairs,
        provision=ghv.G17_PROVISION_SYNTHETIC_HARNESS,
        dataset_root=None,
        instrument_id=str(handoff.bound_instrument.instrument_id),
        venue_native_id="ON-USDT-SWAP",
    )
    producer = g17["LANE_1"]
    vol = ghv._g17_typed_volatility_from_producer_v1(producer)
    assert meta["G17_PROVISION"] == ghv.G17_PROVISION_SYNTHETIC_HARNESS
    assert vol is not None
    assert vol < 1e-10


def test_natural_checkpoint_g17_produces_positive_volatility_after_ingest() -> None:
    ghv = _load_adjudication_module()
    root = REPO / ghv.DATASETS[0]["SOURCE_PATH"]
    checkpoint = ghv._dataset_natural_g17_checkpoint_path(root)
    assert checkpoint is not None
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        build_s8_occupied_lane_pairs_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.cap24_runtime_binding_witness_epoch_v1 import (
        resolve_cap24_runtime_binding_witness_epoch_v1,
    )
    from src.ops.single_selected_future_policy_v1.persistence_v1 import (
        load_and_validate_selection_v1,
    )

    prod = _productive_root(ghv)
    sel = load_and_validate_selection_v1(prod / "runtime_state/selection", require_manifest=True)
    manifest = json.loads((prod / "cap24_selection_state_publish_manifest_v1.json").read_text())
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=prod,
        repository_sha=str(manifest["repository_sha"]),
        binding_epoch=resolve_cap24_runtime_binding_witness_epoch_v1(
            selection=sel.selection,
            decision_epoch="2026-10-01T21:33:35Z",
        ),
    )
    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=REPO / "runtime/test_g17_parity_natural_lane",
        bound=handoff.bound_instrument,
    )
    g17, meta = ghv._build_g17_producers_for_replay_v1(
        pairs,
        provision=ghv.G17_PROVISION_NATURAL_CHECKPOINT,
        dataset_root=root,
        instrument_id=str(handoff.bound_instrument.instrument_id),
        venue_native_id="ON-USDT-SWAP",
    )
    assert meta["NATURAL_SOURCE_MATCHES_G17_CONTRACT"] is not False
    assert meta["NATURAL_G17_SOURCE_SAMPLE_COUNT"] >= 61
    producer = g17["LANE_1"]
    rows = ghv._load_jsonl(root / "natural_market_data_get_capture_v1.jsonl")
    run_id = json.loads((root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").read_text())["RUN_ID"]
    injections = ghv._build_injections(ghv._bundle_polls(rows, run_id), "ON-USDT-SWAP")
    bootstrap = ghv._sort_injections_chronologically(injections)[0]
    records = list(meta.get("NATURAL_G17_CHECKPOINT_RECORDS") or [])
    state: dict[str, int] = {"next_index": 0}
    ghv._ingest_g17_replay_observation_v1(
        producer,
        injection=bootstrap,
        natural_g17_records=records,
        ingest_state=state,
        venue_native_id="ON-USDT-SWAP",
        instrument_id=str(handoff.bound_instrument.instrument_id),
    )
    vol = ghv._g17_typed_volatility_from_producer_v1(producer)
    assert vol is not None
    assert abs(vol - 0.009850574636883797) < 1e-12


def test_natural_g17_cmc_resolver_chain_matches_typed_estimate() -> None:
    ghv = _load_adjudication_module()
    from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
        bind_typed_canonical_volatility_estimate_into_market_context_v1,
        resolve_legacy_volatility_float_for_consumer_v1,
    )
    from trading.master_v2.canonical_market_context_v1 import (
        BarFinalityStatus,
        CanonicalMarketContextV1,
        ClockTrustStatus,
        DataIntegrityStatus,
        FuturesMarketType,
        WarmupStatus,
        with_computed_input_digest,
    )

    root = REPO / ghv.DATASETS[0]["SOURCE_PATH"]
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        build_s8_occupied_lane_pairs_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.cap24_runtime_binding_witness_epoch_v1 import (
        resolve_cap24_runtime_binding_witness_epoch_v1,
    )
    from src.ops.single_selected_future_policy_v1.persistence_v1 import (
        load_and_validate_selection_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    )

    prod = _productive_root(ghv)
    sel = load_and_validate_selection_v1(prod / "runtime_state/selection", require_manifest=True)
    manifest = json.loads((prod / "cap24_selection_state_publish_manifest_v1.json").read_text())
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=prod,
        repository_sha=str(manifest["repository_sha"]),
        binding_epoch=resolve_cap24_runtime_binding_witness_epoch_v1(
            selection=sel.selection,
            decision_epoch="2026-10-01T21:33:35Z",
        ),
    )
    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=REPO / "runtime/test_g17_parity_natural_cmc_lane",
        bound=handoff.bound_instrument,
    )
    g17, meta = ghv._build_g17_producers_for_replay_v1(
        pairs,
        provision=ghv.G17_PROVISION_NATURAL_CHECKPOINT,
        dataset_root=root,
        instrument_id=str(handoff.bound_instrument.instrument_id),
        venue_native_id="ON-USDT-SWAP",
    )
    producer = g17["LANE_1"]
    rows = ghv._load_jsonl(root / "natural_market_data_get_capture_v1.jsonl")
    run_id = json.loads((root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").read_text())["RUN_ID"]
    bootstrap = ghv._sort_injections_chronologically(
        ghv._build_injections(ghv._bundle_polls(rows, run_id), "ON-USDT-SWAP")
    )[0]
    records = list(meta.get("NATURAL_G17_CHECKPOINT_RECORDS") or [])
    ghv._ingest_g17_replay_observation_v1(
        producer,
        injection=bootstrap,
        natural_g17_records=records,
        ingest_state={"next_index": 0},
        venue_native_id="ON-USDT-SWAP",
        instrument_id=str(handoff.bound_instrument.instrument_id),
    )
    typed_vol = ghv._g17_typed_volatility_from_producer_v1(producer)
    assert typed_vol is not None
    prov = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=bootstrap.mark_price_payload,
        venue_native_id="ON-USDT-SWAP",
        index_from_index_tickers=bootstrap.index_tickers_payload,
    )
    mark = float(prov.mark_px)
    ctx = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id="parity-test",
            instrument_id=str(handoff.bound_instrument.instrument_id),
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=1,
            market_event_time="2026-10-01T21:31:00Z",
            decision_time="2026-10-01T21:31:01Z",
            bar_interval="1m",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=mark,
            index_price=mark,
            best_bid=mark - 0.01,
            best_ask=mark + 0.01,
            spread=0.02,
            volume=1.0,
            open_interest=1.0,
            funding_rate=0.0,
            volatility_estimate=0.08,
            trend_feature_set={},
            momentum_feature_set={},
            liquidity_feature_set={},
            market_structure_feature_set={},
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=WarmupStatus.WARMUP_COMPLETE,
            feature_contract_version="v1",
            input_digest="",
        )
    )
    port = producer.output_port_v1()
    assert port.estimate is not None
    ctx_bound = bind_typed_canonical_volatility_estimate_into_market_context_v1(ctx, port.estimate)
    resolved = resolve_legacy_volatility_float_for_consumer_v1(ctx_bound)
    assert typed_vol == ctx_bound.volatility_estimate == resolved


def test_synthetic_g17_causes_adverse_match_natural_does_not_at_bootstrap_mark() -> None:
    """Proves prior ADVERSE was synthetic provisioning, not Scope semantic change."""
    from trading.master_v2.deterministic_scope_event_generator_v1 import (
        ScopeCandidateKind,
        ScopeDirectionState,
        _matched_directional_conditions,
        compute_evaluated_thresholds,
    )
    from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
        resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1,
    )

    ghv = _load_adjudication_module()
    root = REPO / ghv.DATASETS[0]["SOURCE_PATH"]
    rows = ghv._load_jsonl(root / "natural_market_data_get_capture_v1.jsonl")
    run_id = json.loads((root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").read_text())["RUN_ID"]
    bootstrap = ghv._sort_injections_chronologically(
        ghv._build_injections(ghv._bundle_polls(rows, run_id), "ON-USDT-SWAP")
    )[0]
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    )

    prov = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=bootstrap.mark_price_payload,
        venue_native_id="ON-USDT-SWAP",
        index_from_index_tickers=bootstrap.index_tickers_payload,
    )
    mark = float(prov.mark_px)
    anchor = mark

    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        build_s8_occupied_lane_pairs_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.cap24_runtime_binding_witness_epoch_v1 import (
        resolve_cap24_runtime_binding_witness_epoch_v1,
    )
    from src.ops.single_selected_future_policy_v1.persistence_v1 import (
        load_and_validate_selection_v1,
    )

    prod = _productive_root(ghv)
    sel = load_and_validate_selection_v1(prod / "runtime_state/selection", require_manifest=True)
    manifest = json.loads((prod / "cap24_selection_state_publish_manifest_v1.json").read_text())
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=prod,
        repository_sha=str(manifest["repository_sha"]),
        binding_epoch=resolve_cap24_runtime_binding_witness_epoch_v1(
            selection=sel.selection,
            decision_epoch="2026-10-01T21:33:35Z",
        ),
    )
    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=REPO / "runtime/test_g17_parity_scope_lane",
        bound=handoff.bound_instrument,
    )
    syn_g17, _ = ghv._build_g17_producers_for_replay_v1(
        pairs,
        provision=ghv.G17_PROVISION_SYNTHETIC_HARNESS,
        dataset_root=None,
        instrument_id=str(handoff.bound_instrument.instrument_id),
        venue_native_id="ON-USDT-SWAP",
    )
    nat_g17, nat_meta = ghv._build_g17_producers_for_replay_v1(
        pairs,
        provision=ghv.G17_PROVISION_NATURAL_CHECKPOINT,
        dataset_root=root,
        instrument_id=str(handoff.bound_instrument.instrument_id),
        venue_native_id="ON-USDT-SWAP",
    )
    syn_vol = ghv._g17_typed_volatility_from_producer_v1(syn_g17["LANE_1"])
    nat_prod = nat_g17["LANE_1"]
    ghv._ingest_g17_replay_observation_v1(
        nat_prod,
        injection=bootstrap,
        natural_g17_records=list(nat_meta.get("NATURAL_G17_CHECKPOINT_RECORDS") or []),
        ingest_state={"next_index": 0},
        venue_native_id="ON-USDT-SWAP",
        instrument_id=str(handoff.bound_instrument.instrument_id),
    )
    nat_vol = ghv._g17_typed_volatility_from_producer_v1(nat_prod)
    assert syn_vol is not None and nat_vol is not None

    def _matched(vol: float) -> tuple:
        dt = vol * mark
        lc = resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(dt)
        assert lc.ok
        th = compute_evaluated_thresholds(
            direction=ScopeDirectionState.LONG,
            trailing_anchor=anchor,
            up_distance=float(lc.up_distance),
            adverse_exit_distance=float(lc.adverse_exit_distance),
            reversal_distance=float(lc.reversal_distance),
        )
        matched = _matched_directional_conditions(
            direction=ScopeDirectionState.LONG,
            current_price=mark,
            thresholds=th,
        )
        return matched, th

    syn_matched, _ = _matched(float(syn_vol))
    nat_matched, nat_th = _matched(float(nat_vol))
    assert ScopeCandidateKind.ADVERSE_EXIT in syn_matched
    assert ScopeCandidateKind.ADVERSE_EXIT not in nat_matched
    assert ScopeCandidateKind.UPSCOPE not in nat_matched
    assert mark < nat_th.up_candidate_threshold
