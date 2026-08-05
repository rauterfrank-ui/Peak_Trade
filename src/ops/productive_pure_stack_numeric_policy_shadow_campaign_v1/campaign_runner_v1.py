"""Stage-2 Pure-Stack numeric policy shadow campaign runner (no-order / non-authorizing)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    CALIBRATION_PROTOCOL_REL,
    CAMPAIGN_SCAFFOLD_REL,
    GROUP_AUTO_RATIFICATION_AUTHORIZED,
    INPUT_AUTHORITY,
    MECHANICAL_COUPLING_RULE,
    MECHANICAL_COUPLING_TOKEN,
    OWNER_RATIFIED,
    PRODUCTIVE_ACTIVATION,
    PRODUCTIVE_NUMERIC_VALUES_SET,
    RUNTIME_IMPLEMENTED,
    SOLE_TRADING_AUTHORITY,
    STAGE1_MANIFEST_REL,
    STAGE2_TOKENS,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.fps_atr_or_range_wilder_atr_finalized_ohlcv_v1 import (
    FORMULA_ID as ATR_FORMULA_ID,
    compute_fps_atr_or_range_wilder_atr_finalized_ohlcv_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.fps_opportunity_score_fee_slippage_breakeven_movement_v1 import (
    FORMULA_ID as OPP_FORMULA_ID,
    compute_fps_opportunity_score_fee_slippage_breakeven_movement_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.fps_realized_volatility_population_stdev_mark_log_returns_v1 import (
    FORMULA_ID as RV_FORMULA_ID,
    compute_fps_realized_volatility_population_stdev_mark_log_returns_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.fps_sequence_path_survival_ratio_prearm_path_fraction_v1 import (
    FORMULA_ID as PATH_FORMULA_ID,
    compute_fps_sequence_path_survival_ratio_prearm_path_fraction_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.shadow_futures_input_freshness_age_collector_v1 import (
    collect_shadow_futures_input_freshness_age_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.shadow_sequence_survival_metrics_producer_v1 import (
    produce_shadow_sequence_survival_metrics_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.shadow_survival_envelope_assembler_v1 import (
    assemble_shadow_survival_envelope_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.evidence_emitter_v1 import (
    ShadowCampaignEmitError,
    assert_no_overwrite,
    build_evidence_pack,
    data_collection_groups_payload,
    decide_campaign_state,
    map_internal_state_to_pack_status,
    resolve_and_validate_output_dir,
    write_campaign_artifacts,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    CampaignStateV1,
    EmptyCapableManifestV1,
    ShadowAvailabilityV1,
    ShadowCampaignRequestV1,
    ShadowCampaignResultV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    canonical_json_text,
    sha256_file,
    sha256_hex,
)

# Explicit non-imports / non-wiring of order/live/testnet/dashboard writers.
# Documentation-only deny-list names (never invoked / imported by this runner).
_SHADOW_CAMPAIGN_DENIED_RUNTIME_CAPABILITY_NAMES = (
    "live_trading_capability",
    "order_submit_capability",
    "testnet_capability",
    "exchange_credential_capability",
)


def _load_scaffold_rows(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / CAMPAIGN_SCAFFOLD_REL
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("per_token_evidence")
    if not isinstance(rows, list) or len(rows) != 18:
        raise ShadowCampaignEmitError("scaffold_per_token_evidence_invalid")
    return [dict(r) for r in rows]


def _obs_note(
    status: ShadowAvailabilityV1, formula_id: str, reason: Optional[str]
) -> tuple[str, ...]:
    base = (
        f"shadow_observation_status={status.value}",
        f"formula_or_collector={formula_id}",
        "productive_activation=false",
        "provisional=true",
    )
    if reason:
        return base + (f"reason={reason}",)
    return base


def run_shadow_campaign_v1(request: ShadowCampaignRequestV1) -> ShadowCampaignResultV1:
    """Run an isolated hermetic shadow campaign and emit a schema-compatible evidence pack.

    Never sets productive_numeric_value, input_authority, runtime_implemented,
    owner_ratified, or productive_activation. Never writes dashboard/runtime archives.
    Never executes orders / testnet / live paths.
    """
    if PRODUCTIVE_ACTIVATION or INPUT_AUTHORITY or RUNTIME_IMPLEMENTED or OWNER_RATIFIED:
        raise ShadowCampaignEmitError("invariant_flags_must_remain_false")
    if GROUP_AUTO_RATIFICATION_AUTHORIZED:
        raise ShadowCampaignEmitError("group_auto_ratification_must_remain_false")
    if request.reproducibility.sole_trading_authority != SOLE_TRADING_AUTHORITY:
        raise ShadowCampaignEmitError("sole_trading_authority_mismatch")

    repo_root = Path(request.repo_root)
    output_root = Path(request.output_root)
    campaign_dir = resolve_and_validate_output_dir(
        repo_root=repo_root,
        output_root=output_root,
        campaign_id=request.campaign_id,
    )
    assert_no_overwrite(campaign_dir, allow_overwrite=request.allow_overwrite)

    stage1_digest_actual = sha256_file(repo_root / STAGE1_MANIFEST_REL)
    protocol_digest_actual = sha256_file(repo_root / CALIBRATION_PROTOCOL_REL)
    rejection: list[str] = list(request.force_reject_reasons)

    if request.reproducibility.stage1_manifest_digest != stage1_digest_actual:
        rejection.append("stage1_manifest_digest_mismatch")
    if request.reproducibility.calibration_protocol_digest != protocol_digest_actual:
        rejection.append("calibration_protocol_digest_mismatch")
    if len(request.origin_main_sha) != 40:
        rejection.append("origin_main_sha_invalid")

    # Shadow formula observations (hermetic inputs only; no external market fetch).
    rv = compute_fps_realized_volatility_population_stdev_mark_log_returns_v1(
        request.observation_bars
    )
    atr = compute_fps_atr_or_range_wilder_atr_finalized_ohlcv_v1(request.observation_bars)
    opp = compute_fps_opportunity_score_fee_slippage_breakeven_movement_v1(
        recent_abs_log_return=request.recent_abs_log_return,
        fee_bps=request.fee_bps,
        slippage_bps=request.slippage_bps,
        event_time_epoch_s=request.reproducibility.event_time_epoch_s,
    )
    path_ratio = compute_fps_sequence_path_survival_ratio_prearm_path_fraction_v1(
        request.path_above_barrier,
        event_time_epoch_s=request.reproducibility.event_time_epoch_s,
    )
    seq = produce_shadow_sequence_survival_metrics_v1(
        path_above_barrier=request.path_above_barrier,
        explicit_metrics=request.sequence_metric_inputs,
        event_time_epoch_s=request.reproducibility.event_time_epoch_s,
    )
    envelope = assemble_shadow_survival_envelope_v1(
        long_layer=request.layer_metric_inputs,
        short_layer=request.layer_metric_inputs,
        path_above_barrier=request.path_above_barrier,
        sequence_metric_inputs=request.sequence_metric_inputs,
        limits=None,
    )
    last_bar = request.observation_bars[-1] if request.observation_bars else None
    freshness = collect_shadow_futures_input_freshness_age_v1(
        bar=last_bar,
        as_of_event_time_epoch_s=request.reproducibility.event_time_epoch_s,
    )

    observation_notes: dict[str, tuple[str, ...]] = {
        "OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS": _obs_note(
            freshness.status,
            "shadow_futures_input_freshness_age_collector.v1",
            freshness.rejection_reason,
        ),
        "OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY": _obs_note(
            rv.status, RV_FORMULA_ID, rv.rejection_reason
        ),
        "OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE": _obs_note(
            atr.status, ATR_FORMULA_ID, atr.rejection_reason
        ),
        "OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE": _obs_note(
            opp.status, OPP_FORMULA_ID, opp.rejection_reason
        ),
        "OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO": _obs_note(
            path_ratio.status, PATH_FORMULA_ID, path_ratio.rejection_reason
        ),
    }
    for token in STAGE2_TOKENS:
        if token.startswith("OWNER_VALUE_SURVIVAL_LIMIT_") and token not in observation_notes:
            observation_notes[token] = _obs_note(
                seq.status,
                "fps_sequence_metric_set.double_play_survival_envelope_v0_fields.v1",
                seq.rejection_reason,
            )
        if token.startswith("OWNER_VALUE_CAPITAL_SLOT_") and token not in observation_notes:
            observation_notes[token] = (
                "shadow_observation_status=UNAVAILABLE",
                "reason=capital_slot_config_or_state_authority_absent",
                "productive_activation=false",
                "provisional=true",
            )

    blockers: dict[str, tuple[str, ...]] = {}
    # Semantic / authority blockers remain explicit; never invent thresholds.
    for token in (
        "OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_EARLY_LOSS_TOXICITY",
        "OWNER_VALUE_SURVIVAL_LIMIT_MIN_MARGIN_BUFFER_AT_RISK_99",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_SEQUENCE_FRAGILITY_INDEX",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_LIQUIDATION_NEAR_MISS_RATE",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_GOVERNANCE_BREACH_FREQUENCY",
        "OWNER_VALUE_SURVIVAL_LIMIT_MIN_CHOP_SWITCH_SURVIVAL_SCORE",
    ):
        if seq.status is not ShadowAvailabilityV1.AVAILABLE:
            blockers[token] = ("SEMANTICALLY_UNRESOLVED_OR_UNAVAILABLE_SEQUENCE_METRICS",)
    for token in (
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_EFFECTIVE_LEVERAGE",
        "OWNER_VALUE_SURVIVAL_LIMIT_MIN_LIQUIDATION_BUFFER",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_ADVERSE_FILL_LOSS",
    ):
        if envelope.status is not ShadowAvailabilityV1.AVAILABLE:
            blockers[token] = ("MISSING_AUTHORITY_ARITHMETIC_KERNEL_PROJECTION",)

    manifests = {
        "dataset_manifest": request.dataset_manifest,
        "train_calibration_validation_partition_manifest": (
            request.train_calibration_validation_partition_manifest
        ),
        "walk_forward_manifest": request.walk_forward_manifest,
        "bootstrap_monte_carlo_manifest": request.bootstrap_monte_carlo_manifest,
        "stress_pack_manifest": request.stress_pack_manifest,
    }

    # COMPLETE is unreachable unless all manifests are COMPLETE and no rejections.
    evidence_requirements_met = False
    state = decide_campaign_state(
        rejection_reasons=rejection,
        manifests=manifests,
        evidence_requirements_met=evidence_requirements_met,
    )
    # Shadow declaration with empty scaffolds is DECLARED → pack IN_PROGRESS.
    if state is CampaignStateV1.DECLARED and not rejection:
        # Runner execution implies progress beyond static scaffold NOT_STARTED.
        state = CampaignStateV1.IN_PROGRESS

    scaffold_rows = _load_scaffold_rows(repo_root)
    pack = build_evidence_pack(
        campaign_id=request.campaign_id,
        campaign_state=state,
        origin_main_sha=request.origin_main_sha,
        stage1_manifest_digest=stage1_digest_actual,
        calibration_protocol_digest=protocol_digest_actual,
        scaffold_rows=scaffold_rows,
        manifests=manifests,
        rejection_reasons=rejection,
        observation_notes=observation_notes,
        blockers=blockers,
    )

    # Hard invariants on emitted pack.
    assert pack["productive_numeric_values_set"] == 0
    assert pack["input_authority"] is False
    assert pack["runtime_implemented"] is False
    assert pack["owner_ratified"] is False
    assert pack["evidence_complete"] is False or state is CampaignStateV1.COMPLETE
    assert all(row["productive_numeric_value"] is None for row in pack["per_token_evidence"])
    assert MECHANICAL_COUPLING_TOKEN not in {row["token"] for row in pack["per_token_evidence"]}

    shadow_observations = {
        "realized_volatility": asdict(rv),
        "atr_or_range": asdict(atr),
        "opportunity_score": asdict(opp),
        "path_survival_ratio": asdict(path_ratio),
        "sequence_metrics": asdict(seq),
        "survival_envelope_assembly": {
            "status": envelope.status.value,
            "rejection_reason": envelope.rejection_reason,
            "input_digest": envelope.input_digest,
            "notes": list(envelope.notes),
            "productive_activation": envelope.productive_activation,
        },
        "freshness_age": asdict(freshness),
        "best_bid": request.best_bid,
        "best_ask": request.best_ask,
    }

    # Convert enums in nested asdict payloads.
    def _normalize(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _normalize(v) for k, v in obj.items()}
        if isinstance(obj, tuple):
            return list(obj)
        if hasattr(obj, "value") and obj.__class__.__name__.endswith("V1"):
            return obj.value
        return obj

    shadow_observations = _normalize(shadow_observations)

    pack_digest = sha256_hex((canonical_json_text(pack) + "\n").encode("utf-8"))
    result = ShadowCampaignResultV1(
        campaign_id=request.campaign_id,
        campaign_state=state,
        pack_campaign_status=map_internal_state_to_pack_status(state),
        evidence_complete=bool(pack["evidence_complete"]),
        owner_ratified=False,
        productive_numeric_values_set=PRODUCTIVE_NUMERIC_VALUES_SET,
        input_authority=False,
        runtime_implemented=False,
        productive_activation=False,
        sole_trading_authority=SOLE_TRADING_AUTHORITY,
        output_dir=str(campaign_dir),
        evidence_pack_path=str(campaign_dir / "evidence_pack.v1.json"),
        pack_digest=pack_digest,
        rejection_reasons=tuple(rejection),
        token_count=len(STAGE2_TOKENS),
        shadow_observations=shadow_observations,
        data_collection_groups_only=data_collection_groups_payload(),
        mechanical_couplings={MECHANICAL_COUPLING_TOKEN: MECHANICAL_COUPLING_RULE},
    )

    repro_payload = {
        **asdict(request.reproducibility),
        "stage1_manifest_digest_verified": stage1_digest_actual,
        "calibration_protocol_digest_verified": protocol_digest_actual,
        "forbidden_runtime_symbols_touched": [],
        "orders_testnet_live_paths": False,
        "dashboard_mutations": False,
        "archive_mutations": False,
        "trading_logic_changed": False,
        "group_auto_ratification": False,
    }
    write_campaign_artifacts(
        campaign_dir=campaign_dir,
        pack=pack,
        result_payload=result.to_dict(),
        reproducibility_payload=repro_payload,
    )
    return result


def empty_scaffold_manifest(notes: str) -> EmptyCapableManifestV1:
    return EmptyCapableManifestV1(
        status="EMPTY_SCAFFOLD",
        populated=False,
        entries=(),
        digest=None,
        notes=notes,
    )
