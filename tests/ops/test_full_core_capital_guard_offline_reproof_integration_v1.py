"""Offline reproof: productive PRE_EXTERNAL handoff → Full-Core Capital Guard (OFFLINE_STUB).

ACTUAL_PRODUCTIVE_PATH_FIXTURE via closure executor + governed-cycle orchestrator join hook.
No POST. Isolated atomic state via PEAK_TRADE_FULL_CORE_CAPITAL_GUARD_ATOMIC_STATE_DIR.
"""

from __future__ import annotations

import json
import multiprocessing as mp
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    ATOMIC_STATE_DIR_ENV_VAR,
    JOIN_ENV_VAR,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    OWNER_GO,
    execute_current_productive_full_core_pre_external_closure_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_aligned_g17_dk_producer_v1,
    governed_c1_candles_payload_from_enter_closes_v1,
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
    prepare_layered_short_armed_seed_for_pre_external_invoke_v1,
)
from tests.ops._pre_external_cap21_inst_type_test_helpers_v1 import (
    write_cap21_productivity_root_for_inst_v1,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    _TEST_INST,
    _bound,
    _origin_main_sha,
    _productive_transport,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide


def _run_productive_pre_external_closure_v1(
    tmp_path: Path,
    *,
    seed: str,
) -> tuple[object, dict[str, object]]:
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    lanes_root = tmp_path / "lanes"
    if seed == "long":
        _arm, enter_closes, mark_px, event_ts, aligned_g17 = (
            prepare_layered_long_armed_seed_for_pre_external_invoke_v1(
                bound=bound,
                g17_typed_vol_producer=object(),
                lane_state_root=lanes_root,
            )
        )
    elif seed == "short":
        _arm, enter_closes, mark_px, event_ts, aligned_g17 = (
            prepare_layered_short_armed_seed_for_pre_external_invoke_v1(
                bound=bound,
                g17_typed_vol_producer=object(),
                lane_state_root=lanes_root,
            )
        )
    else:
        raise ValueError(seed)
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=enter_closes,
        last_event_ts_unix=event_ts,
    )
    cap24_root = write_cap21_productivity_root_for_inst_v1(tmp_path, venue_native_id=_TEST_INST)
    result = execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_sha,
        bound_instrument=bound,
        lane_state_root=lanes_root,
        fresh_get_transport=_productive_transport(),
        execute_network=False,
        evidence_root=tmp_path / "evidence",
        candles_payload=candles,
        cap24_productivity_root=cap24_root,
        market_kwargs={
            "cycle_id_prefix": f"reproof-pre-ext-{seed}",
            "mark_px": mark_px,
            "index_px": mark_px,
            "bid_px": mark_px - 0.5,
            "ask_px": mark_px + 0.5,
            "finalized_closes": enter_closes,
            "last_finalized_event_ts_unix": event_ts,
            "observed_unix": event_ts + 100.0,
            "venue_flat": True,
            "existing_position_side": ExistingPositionSide.NONE,
            "volume": 10.0,
            "open_interest": 20.0,
            "funding_rate": 0.0001,
        },
        g17_typed_vol_producers={"LANE_1": aligned_g17},
        execution_integrity_backend=integrity,
    )
    claims_path = Path(result.store_root) / "claims.json"
    claims = json.loads(claims_path.read_text(encoding="utf-8"))
    return result, claims


def test_productive_long_offline_stub_guard_veto_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    atomic_dir = tmp_path / "atomic-long-pass"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    result, claims = _run_productive_pre_external_closure_v1(tmp_path, seed="long")
    assert result.wp2_status == "PASS"
    assert result.terminal_disposition == "PRE_EXTERNAL_EFFECT"
    assert result.post_count == 0
    assert claims.get("FULL_CORE_CAPITAL_GUARD_JOIN_MODE") == "OFFLINE_STUB"
    assert claims.get("FULL_CORE_CAPITAL_GUARD_BLOCKED") == "false"
    assert claims.get("FULL_CORE_CAPITAL_GUARD_POST_COUNT") == "0"
    assert claims.get("FULL_CORE_CAPITAL_GUARD_OBSERVE_STATUS") == "PASS"
    assert claims.get("MASTER_V2_DECISION") == "enter_long"
    assert list(atomic_dir.glob("*.state.json"))


def test_productive_short_offline_stub_guard_veto_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    atomic_dir = tmp_path / "atomic-short-pass"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    result, claims = _run_productive_pre_external_closure_v1(tmp_path, seed="short")
    assert result.wp2_status == "PASS"
    assert result.post_count == 0
    assert claims.get("FULL_CORE_CAPITAL_GUARD_JOIN_MODE") == "OFFLINE_STUB"
    assert claims.get("FULL_CORE_CAPITAL_GUARD_BLOCKED") == "false"
    assert claims.get("MASTER_V2_DECISION") == "enter_short"


def test_productive_long_offline_stub_guard_blocks_unratified_caps(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_full_core_capital_guard_v1 as guard_mod,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        full_core_pre_post_capital_guard_join_v1 as join_mod,
    )

    unratified = guard_mod.offline_proof_full_core_guard_config_v1(
        config_digest="offline-unratified-productive-block",
    )
    monkeypatch.setattr(
        join_mod,
        "ratified_offline_full_core_guard_config_v1",
        lambda: unratified,
    )
    atomic_dir = tmp_path / "atomic-block"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    result, claims = _run_productive_pre_external_closure_v1(tmp_path, seed="long")
    assert result.wp2_status == "PASS"
    assert claims.get("FULL_CORE_CAPITAL_GUARD_JOIN_MODE") == "OFFLINE_STUB"
    assert claims.get("FULL_CORE_CAPITAL_GUARD_BLOCKED") == "true"
    assert claims.get("FULL_CORE_CAPITAL_GUARD_POST_COUNT") == "0"
    reasons = str(claims.get("FULL_CORE_CAPITAL_GUARD_REASONS") or "")
    assert "UNRATIFIED" in reasons or "RATIFIED" in reasons.upper()


def test_default_join_mode_disabled_no_orchestrator_guard_claims(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv(JOIN_ENV_VAR, raising=False)
    monkeypatch.delenv(ATOMIC_STATE_DIR_ENV_VAR, raising=False)
    _result, claims = _run_productive_pre_external_closure_v1(tmp_path, seed="long")
    assert "FULL_CORE_CAPITAL_GUARD_JOIN_MODE" not in claims
    assert claims.get("FULL_CORE_CAPITAL_GUARD_OBSERVE_STATUS") == "PASS"


def _subprocess_offline_stub_worker(work_root: str, atomic_dir: str) -> None:
    import os
    from pathlib import Path as _Path

    os.environ[JOIN_ENV_VAR] = "OFFLINE_STUB"
    os.environ[ATOMIC_STATE_DIR_ENV_VAR] = atomic_dir
    from tests.ops.test_full_core_capital_guard_offline_reproof_integration_v1 import (
        _run_productive_pre_external_closure_v1,
    )

    _run_productive_pre_external_closure_v1(_Path(work_root), seed="long")


def test_offline_stub_env_only_in_subprocess_isolated(tmp_path: Path) -> None:
    atomic = tmp_path / "mp-atomic"
    atomic.mkdir()
    proc = mp.Process(
        target=_subprocess_offline_stub_worker,
        args=(str(tmp_path), str(atomic)),
    )
    proc.start()
    proc.join(timeout=120)
    assert proc.exitcode == 0
    assert list(atomic.glob("*.state.json"))


def test_handoff_contextvar_cleanup_after_invoke(tmp_path: Path) -> None:
    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
        FullCoreCapitalGuardHandoffContextV1,
        active_full_core_capital_guard_handoff_context_v1,
        bind_full_core_capital_guard_handoff_context_v1,
        reset_full_core_capital_guard_handoff_context_v1,
    )

    assert active_full_core_capital_guard_handoff_context_v1() is None
    bound = _bound()
    handoff_ctx_reset = bind_full_core_capital_guard_handoff_context_v1(
        FullCoreCapitalGuardHandoffContextV1(
            bound_instrument=bound,
            canonical_decision_id="dec-isolation",
            account_identity="acct-iso",
            environment="PRODUCTIVE_READ_ONLY",
            origin_main_sha=_origin_main_sha(),
            instrument_metadata=None,
        )
    )
    try:
        assert active_full_core_capital_guard_handoff_context_v1() is not None
    finally:
        reset_full_core_capital_guard_handoff_context_v1(handoff_ctx_reset)
    assert active_full_core_capital_guard_handoff_context_v1() is None
