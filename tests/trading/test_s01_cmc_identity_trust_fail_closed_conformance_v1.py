"""S01 CMC identity/trust fail-closed conformance vectors.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S01_CMC_IDENTITY_TRUST_FAIL_CLOSED
PRIMARY_OWNER=integrated_offline_trading_logic_replay_v1

Additive behavioral assertions only. No trading-semantics mutation.
CMC bind / Replay identity join is the productive owner. Mapper is not a
decision owner. FILEGATE / execution / Live are out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: Replay compute owner; CMC eligibility is_authority=false
- FORENSIC_RAW_EVIDENCE: Replay identity join on instrument_id / trading_epoch;
  invalid input_digest format; CMC bind blocks untrusted/nonfinal
- ALREADY_ADJUDICATED: S01 vector set; no Future-Reselection
- Not claimed: equality between replay input_digest and CMC input_digest as a
  productive identity gate (no such check exists on origin/main)

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Replay harness reuse stays via import of the existing owner test helpers.
"""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    CanonicalMarketContextBindingOutcome,
    CanonicalMarketContextBindingStateV1,
    CanonicalMarketContextBlockReason,
    ClockTrustStatus,
    DataIntegrityStatus,
    bind_canonical_market_context_event,
    evaluate_canonical_market_context_eligibility,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    run_integrated_offline_trading_logic_replay_v1,
)

from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _EPOCH,
    _INSTRUMENT,
    _market_context,
    _replay_input,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CMC_SOURCE = _REPO_ROOT / "src/trading/master_v2/canonical_market_context_v1.py"
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_MAPPER_MODULE = "intended_action_mapper_v1"
_CMC_IDENTITY_FAIL_REASONS = frozenset(
    {
        "instrument_mismatch",
        "trading_epoch_mismatch",
        "input_digest_invalid",
        "cmc_untrusted_or_nonfinal",
        CanonicalMarketContextBlockReason.DATA_INTEGRITY_UNTRUSTED.value,
        CanonicalMarketContextBlockReason.DATA_INTEGRITY_UNKNOWN.value,
        CanonicalMarketContextBlockReason.CLOCK_TRUST_UNTRUSTED.value,
        CanonicalMarketContextBlockReason.CLOCK_TRUST_UNKNOWN.value,
        CanonicalMarketContextBlockReason.BAR_UNFINALIZED.value,
        CanonicalMarketContextBlockReason.BAR_FINALITY_UNKNOWN.value,
    }
)


def _assert_no_trade_grant_and_no_reselect(
    result, *, instrument_id: str, trading_epoch: int
) -> None:
    assert result.replay_pass is False
    assert result.evidence.decision_outcome == "blocked"
    assert result.evidence.execution_eligible is False
    assert result.evidence.adapter_compatible is False
    assert result.evidence.authority_effect == "NONE"
    assert result.evidence.runtime_effect == "NONE"
    assert result.evidence.order_effect == "NONE"
    assert result.evidence.quantity_status == "NOT_BOUND"
    assert result.evidence.selected_side == "none"
    assert result.evidence.instrument_id == instrument_id
    assert result.evidence.trading_epoch == trading_epoch
    assert result.intermediate is None
    assert result.compute_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER


def test_v_cmc_01_trusted_pass_through_identity_join() -> None:
    """V-CMC-01: trusted/finalized CMC joins Replay identity; no reselect."""
    inp = _replay_input()
    cmc = inp.canonical_market_context
    assert cmc.instrument_id == inp.instrument_id == _INSTRUMENT
    assert cmc.trading_epoch == inp.trading_epoch == _EPOCH
    assert cmc.data_integrity_status is DataIntegrityStatus.TRUSTED
    assert cmc.clock_trust_status is ClockTrustStatus.TRUSTED
    assert cmc.bar_finality_status is BarFinalityStatus.FINALIZED
    # Fixture digest is independent of CMC digest; that is not a CMC identity gate.
    assert inp.input_digest != cmc.input_digest

    binding = bind_canonical_market_context_event(cmc, inp.market_context_binding_state)
    assert binding.eligibility.binding_outcome is CanonicalMarketContextBindingOutcome.ACCEPTED
    assert binding.eligibility.trading_decision_allowed is True
    assert binding.eligibility.is_authority is False
    assert binding.eligibility.execution_eligible is False
    assert binding.eligibility.live_authorization is False
    assert binding.context is not None
    assert binding.context.instrument_id == inp.instrument_id
    assert binding.context.trading_epoch == inp.trading_epoch

    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.compute_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert not (_CMC_IDENTITY_FAIL_REASONS & set(result.fail_reasons))
    assert result.evidence.instrument_id == inp.instrument_id == cmc.instrument_id
    assert result.evidence.trading_epoch == inp.trading_epoch == cmc.trading_epoch
    assert result.intermediate is not None
    assert result.intermediate.market_context.instrument_id == inp.instrument_id
    assert result.intermediate.market_context.trading_epoch == inp.trading_epoch
    assert result.evidence.execution_eligible is False
    assert result.evidence.adapter_compatible is False
    assert result.evidence.authority_effect == "NONE"


def test_v_cmc_02_untrusted_data_integrity_blocks_via_cmc_bind() -> None:
    """V-CMC-02: untrusted CMC bind is fail-closed BLOCKED; no reselect; no trade grant."""
    inp = _replay_input(
        canonical_market_context=_market_context(
            data_integrity_status=DataIntegrityStatus.UNTRUSTED
        )
    )
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert CanonicalMarketContextBlockReason.DATA_INTEGRITY_UNTRUSTED.value in result.fail_reasons
    assert "cmc_untrusted_or_nonfinal" not in result.fail_reasons
    _assert_no_trade_grant_and_no_reselect(result, instrument_id=_INSTRUMENT, trading_epoch=_EPOCH)


def test_v_cmc_02_unfinalized_bar_blocks_via_cmc_bind() -> None:
    """V-CMC-02: nonfinal CMC bind is fail-closed BLOCKED; no reselect; no trade grant."""
    inp = _replay_input(
        canonical_market_context=_market_context(bar_finality_status=BarFinalityStatus.UNFINALIZED)
    )
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert CanonicalMarketContextBlockReason.BAR_UNFINALIZED.value in result.fail_reasons
    _assert_no_trade_grant_and_no_reselect(result, instrument_id=_INSTRUMENT, trading_epoch=_EPOCH)


def test_v_cmc_03_instrument_mismatch_blocks_without_reselect() -> None:
    """V-CMC-03: instrument identity mismatch BLOCKED; CMC instrument is not adopted."""
    foreign = "inst-sol-usdt-perp"
    inp = _replay_input(canonical_market_context=_market_context(instrument_id=foreign))
    assert inp.instrument_id == _INSTRUMENT
    assert inp.canonical_market_context.instrument_id == foreign
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert "instrument_mismatch" in result.fail_reasons
    _assert_no_trade_grant_and_no_reselect(result, instrument_id=_INSTRUMENT, trading_epoch=_EPOCH)
    assert result.evidence.instrument_id != foreign


def test_v_cmc_03_trading_epoch_mismatch_blocks_without_reselect() -> None:
    """V-CMC-03: epoch identity mismatch BLOCKED; CMC epoch is not adopted."""
    inp = _replay_input(trading_epoch=99)
    assert inp.trading_epoch == 99
    assert inp.canonical_market_context.trading_epoch == _EPOCH
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert "trading_epoch_mismatch" in result.fail_reasons
    _assert_no_trade_grant_and_no_reselect(result, instrument_id=_INSTRUMENT, trading_epoch=99)
    assert result.evidence.trading_epoch != _EPOCH


def test_v_cmc_03_invalid_input_digest_blocks() -> None:
    """V-CMC-03: malformed replay input_digest fail-closed. Not a CMC-equality gate."""
    inp = _replay_input(input_digest="not-a-sha256-digest")
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert "input_digest_invalid" in result.fail_reasons
    _assert_no_trade_grant_and_no_reselect(result, instrument_id=_INSTRUMENT, trading_epoch=_EPOCH)


def test_v_neg_02_cmc_binding_is_not_decision_owner() -> None:
    """V-NEG-02: CMC eligibility/bind is not authority; mapper is not Replay CMC owner."""
    ctx = _market_context()
    elig = evaluate_canonical_market_context_eligibility(ctx)
    assert elig.is_authority is False
    assert elig.is_signal is False
    assert elig.execution_eligible is False
    assert elig.live_authorization is False
    assert elig.binding_outcome is CanonicalMarketContextBindingOutcome.ACCEPTED

    blocked = bind_canonical_market_context_event(
        _market_context(data_integrity_status=DataIntegrityStatus.UNTRUSTED),
        CanonicalMarketContextBindingStateV1(),
    )
    assert blocked.eligibility.binding_outcome is CanonicalMarketContextBindingOutcome.BLOCKED
    assert blocked.eligibility.trading_decision_allowed is False
    assert blocked.eligibility.is_authority is False
    assert blocked.eligibility.execution_eligible is False
    assert blocked.eligibility.live_authorization is False

    for source in (_CMC_SOURCE, _REPLAY_SOURCE):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            assert all(_MAPPER_MODULE not in name for name in names)
            assert all("src.execution" not in name for name in names)
            assert all(not name.startswith("src.live") for name in names)
