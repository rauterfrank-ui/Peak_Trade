# tests/trading/master_v2/test_double_play_survival.py
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from trading.master_v2.double_play_survival import (
    DOUBLE_PLAY_SURVIVAL_LAYER_VERSION,
    ArithmeticFingerprint,
    DoublePlaySurvivalEnvelope,
    LayerArithmeticStatus,
    SequenceSurvivalMetrics,
    StateSwitchSurvivalLimits,
    SurvivalBlockReason,
    SurvivalEnvelopeStatus,
    arithmetic_complete,
    evaluate_survival_envelope,
)

GOOD_LIM = StateSwitchSurvivalLimits(
    min_path_survival_ratio=0.5,
    max_early_loss_toxicity=0.9,
    min_margin_buffer_at_risk_99=0.1,
    max_sequence_fragility_index=0.5,
    max_liquidation_near_miss_rate=0.2,
    max_governance_breach_frequency=0.05,
    min_chop_switch_survival_score=0.4,
    max_effective_leverage=20.0,
    min_liquidation_buffer=0.05,
    max_adverse_fill_loss=0.15,
    live_authorization=False,
)


def _layer() -> LayerArithmeticStatus:
    return LayerArithmeticStatus(
        max_effective_leverage=10.0,
        min_liquidation_buffer=0.1,
        fee_breakeven_bps=2.0,
        expected_adverse_fill_loss=0.05,
        funding_cost_profile="flat",
        is_perpetual=True,
    )


def _fp_ok() -> ArithmeticFingerprint:
    return ArithmeticFingerprint(
        contract_spec_complete=True,
        fee_model_complete=True,
        slippage_model_complete=True,
        funding_model_complete=True,
        margin_model_complete=True,
        liquidation_model_complete=True,
        rounding_model_complete=True,
    )


def _seq_ok() -> SequenceSurvivalMetrics:
    return SequenceSurvivalMetrics(
        path_survival_ratio=0.8,
        early_loss_toxicity=0.2,
        margin_buffer_at_risk_99=0.2,
        sequence_fragility_index=0.2,
        liquidation_near_miss_rate=0.05,
        governance_breach_frequency=0.01,
        chop_switch_survival_score=0.7,
    )


def _env(
    fp: ArithmeticFingerprint,
    long_layer: LayerArithmeticStatus | None = None,
    short_layer: LayerArithmeticStatus | None = None,
    seq: SequenceSurvivalMetrics | None = None,
    lim: StateSwitchSurvivalLimits | None = None,
) -> DoublePlaySurvivalEnvelope:
    return DoublePlaySurvivalEnvelope(
        fingerprint=fp,
        long_layer=long_layer or _layer(),
        short_layer=short_layer or _layer(),
        sequence=seq or _seq_ok(),
        limits=lim or GOOD_LIM,
    )


def test_version():
    assert DOUBLE_PLAY_SURVIVAL_LAYER_VERSION == "v0"


def test_1_incomplete_fingerprint_blocks():
    fp = replace(
        _fp_ok(),
        contract_spec_complete=False,
    )
    d = evaluate_survival_envelope(_env(fp))
    assert d.status == SurvivalEnvelopeStatus.BLOCKED
    assert SurvivalBlockReason.INCOMPLETE_FINGERPRINT in d.block_reasons
    assert not d.pre_authorization_eligible


def test_2_missing_funding_for_perp_blocks():
    fp = replace(_fp_ok(), funding_model_complete=False)
    d = evaluate_survival_envelope(_env(fp))
    assert SurvivalBlockReason.MISSING_FUNDING_FOR_PERP in d.block_reasons
    l = LayerArithmeticStatus(10, 0.1, 2, 0.05, "x", is_perpetual=False)
    d2 = evaluate_survival_envelope(
        _env(
            replace(_fp_ok(), funding_model_complete=False),
            long_layer=l,
            short_layer=l,
        )
    )
    assert SurvivalBlockReason.MISSING_FUNDING_FOR_PERP not in d2.block_reasons


def test_3_missing_liquidation_model_blocks():
    fp = replace(_fp_ok(), liquidation_model_complete=False)
    d = evaluate_survival_envelope(_env(fp))
    assert SurvivalBlockReason.MISSING_LIQUIDATION_MODEL in d.block_reasons


def test_4_missing_sequence_metrics_blocks():
    fp = _fp_ok()
    seq = SequenceSurvivalMetrics(path_survival_ratio=0.5, early_loss_toxicity=None)
    d = evaluate_survival_envelope(_env(fp, seq=seq))
    assert SurvivalBlockReason.INCOMPLETE_SEQUENCE_METRICS in d.block_reasons


def test_5_path_survival_too_low():
    seq = replace(_seq_ok(), path_survival_ratio=0.1)
    d = evaluate_survival_envelope(_env(_fp_ok(), seq=seq))
    assert SurvivalBlockReason.PATH_SURVIVAL_TOO_LOW in d.block_reasons


def test_6_early_loss_too_high():
    seq = replace(_seq_ok(), early_loss_toxicity=1.0)
    d = evaluate_survival_envelope(_env(_fp_ok(), seq=seq))
    assert SurvivalBlockReason.EARLY_LOSS_TOO_HIGH in d.block_reasons


def test_7_margin_buffer_at_risk_too_low():
    seq = replace(_seq_ok(), margin_buffer_at_risk_99=0.01)
    d = evaluate_survival_envelope(_env(_fp_ok(), seq=seq))
    assert SurvivalBlockReason.MARGIN_BUFFER_AT_RISK_TOO_LOW in d.block_reasons


def test_8_liquidation_near_miss_too_high():
    seq = replace(_seq_ok(), liquidation_near_miss_rate=0.9)
    d = evaluate_survival_envelope(_env(_fp_ok(), seq=seq))
    assert SurvivalBlockReason.LIQUIDATION_NEAR_MISS_TOO_HIGH in d.block_reasons


def test_9_governance_breach_too_high():
    seq = replace(_seq_ok(), governance_breach_frequency=0.2)
    d = evaluate_survival_envelope(_env(_fp_ok(), seq=seq))
    assert SurvivalBlockReason.GOVERNANCE_BREACH_TOO_HIGH in d.block_reasons


def test_10_sequence_fragility_too_high():
    seq = replace(_seq_ok(), sequence_fragility_index=0.9)
    d = evaluate_survival_envelope(_env(_fp_ok(), seq=seq))
    assert SurvivalBlockReason.SEQUENCE_FRAGILITY_TOO_HIGH in d.block_reasons


def test_11_chop_switch_survival_too_low():
    seq = replace(_seq_ok(), chop_switch_survival_score=0.1)
    d = evaluate_survival_envelope(_env(_fp_ok(), seq=seq))
    assert SurvivalBlockReason.CHOP_SWITCH_SURVIVAL_TOO_LOW in d.block_reasons


def test_12_leverage_too_high():
    lo = LayerArithmeticStatus(50.0, 0.1, 2, 0.05, "f", True)
    d = evaluate_survival_envelope(_env(_fp_ok(), long_layer=lo))
    assert SurvivalBlockReason.LONG_LEVERAGE_TOO_HIGH in d.block_reasons
    sh = LayerArithmeticStatus(50.0, 0.1, 2, 0.05, "f", True)
    d2 = evaluate_survival_envelope(_env(_fp_ok(), short_layer=sh))
    assert SurvivalBlockReason.SHORT_LEVERAGE_TOO_HIGH in d2.block_reasons


def test_13_liquidation_buffer_too_low():
    lo = LayerArithmeticStatus(10.0, 0.01, 2, 0.05, "f", True)
    d = evaluate_survival_envelope(_env(_fp_ok(), long_layer=lo))
    assert SurvivalBlockReason.LONG_LIQUIDATION_BUFFER_TOO_LOW in d.block_reasons
    sh = LayerArithmeticStatus(10.0, 0.01, 2, 0.05, "f", True)
    d2 = evaluate_survival_envelope(_env(_fp_ok(), short_layer=sh))
    assert SurvivalBlockReason.SHORT_LIQUIDATION_BUFFER_TOO_LOW in d2.block_reasons


def test_14_adverse_fill_too_high():
    lo = LayerArithmeticStatus(10.0, 0.1, 2, 0.3, "f", True)
    d = evaluate_survival_envelope(_env(_fp_ok(), long_layer=lo))
    assert SurvivalBlockReason.LONG_ADVERSE_FILL_LOSS_TOO_HIGH in d.block_reasons


def test_15_valid_complete_allows_model_pre_auth_only():
    d = evaluate_survival_envelope(_env(_fp_ok()))
    assert d.status == SurvivalEnvelopeStatus.OK
    assert d.pre_authorization_eligible is True
    assert d.block_reasons == ()
    assert d.live_authorization is False
    assert arithmetic_complete(_fp_ok())


def test_16_limits_live_auth_true_still_decision_false():
    lim = StateSwitchSurvivalLimits(
        min_path_survival_ratio=0.5,
        max_early_loss_toxicity=0.9,
        min_margin_buffer_at_risk_99=0.1,
        max_sequence_fragility_index=0.5,
        max_liquidation_near_miss_rate=0.2,
        max_governance_breach_frequency=0.05,
        min_chop_switch_survival_score=0.4,
        max_effective_leverage=20.0,
        min_liquidation_buffer=0.05,
        max_adverse_fill_loss=0.15,
        live_authorization=True,
    )
    d = evaluate_survival_envelope(_env(_fp_ok(), lim=lim))
    assert d.live_authorization is False
    assert d.pre_authorization_eligible is True


def test_17_no_network_imports_in_module():
    p = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "trading"
        / "master_v2"
        / "double_play_survival.py"
    )
    tree = ast.parse(p.read_text(encoding="utf-8"))
    bad = {"requests", "urllib3", "ccxt", "httpx", "socket", "aiohttp"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert n.name.split(".")[0] not in bad
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in bad
