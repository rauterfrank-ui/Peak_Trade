"""Contract tests for LayeredCoreAuthoritySealV1."""

from __future__ import annotations

from trading.master_v2.layered_core_authority_seal_v1 import (
    P4_PRODUCTIVE_BINDING,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    build_layered_core_authority_seal_v1,
    validate_layered_core_authority_seal_v1,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1


def test_seal_validation_fail_closed_on_tamper() -> None:
    seal = build_layered_core_authority_seal_v1(
        seal_id="abc",
        instrument_id="ETH-PERP",
        episode_snapshot_id="a" * 64,
        store_manifest_digest="b" * 64,
        regime_pre=NakedRegimeV1.BULL,
        regime_post=NakedRegimeV1.BULL,
        nullline_price=100.0,
        d_t=10.0,
        r_t=100.0,
        cm_t=1.0,
        switch_condition_met=False,
        mechanical_step_count=1,
    )
    result = validate_layered_core_authority_seal_v1(seal, instrument_id="ETH-PERP")
    assert result.ok is True

    tampered = build_layered_core_authority_seal_v1(
        seal_id="abc",
        instrument_id="ETH-PERP",
        episode_snapshot_id="a" * 64,
        store_manifest_digest="b" * 64,
        regime_pre=NakedRegimeV1.BULL,
        regime_post=NakedRegimeV1.BULL,
        nullline_price=100.0,
        d_t=10.0,
        r_t=100.0,
        cm_t=1.0,
        switch_condition_met=False,
        mechanical_step_count=1,
    )
    bad = tampered.__class__(
        **{
            **tampered.__dict__,
            "seal_digest": "c" * 64,
        }
    )
    bad_result = validate_layered_core_authority_seal_v1(bad, instrument_id="ETH-PERP")
    assert bad_result.ok is False
    assert "seal_digest_mismatch" in bad_result.failure_codes


def test_activation_guards_remain_false() -> None:
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
    assert P4_PRODUCTIVE_BINDING is False
