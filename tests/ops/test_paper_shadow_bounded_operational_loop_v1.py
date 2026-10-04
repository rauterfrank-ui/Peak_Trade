"""Offline operational bounded-loop reproof (same loop code as production)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    SHADOW_ACTIVATION_OPERATOR_GO,
    SHADOW_OBSERVATION_OPERATOR_GO,
)
from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    ObservationMarketTickV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    MARKET_TYPE_FUTURES,
    VENUE_OKX,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.observation_tick_source_v1 import (
    InjectedObservationTickSourceV1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.operational_run_v1 import (
    OperationalRunHooksV1,
    run_paper_shadow_bounded_operational_run_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.owner_go_validator_v1 import (
    validate_owner_go_authorization_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.productive_cycle_step_v1 import (
    ProductiveCycleStepOutcomeV1,
    default_productive_cycle_step_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
    PaperShadowRunContractV1,
    load_paper_shadow_run_contract_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
)
from tests.ops._paper_shadow_bounded_orchestrator_offline_reproof_v1 import (
    _representative_ghv_pre_external_event_v1,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_DIR = REPO / "evidence/research/paper_shadow_run_contract_v1/20261004T211710Z"
GHV_TAIL = (
    REPO
    / "evidence/research/ghv_guided_shadow_runtime_closure_v2/20261004T205516Z/ghv_post_change/productive_tail_observations.jsonl"
)


def _tick(
    seq: int = 1, mid: float = 3500.0, ts: float = 1_700_000_000.0
) -> ObservationMarketTickV1:
    return ObservationMarketTickV1(
        instrument_id=CANONICAL_INSTRUMENT_ID,
        venue=VENUE_OKX,
        market_type=MARKET_TYPE_FUTURES,
        sequence=seq,
        event_ts_unix=ts,
        receive_ts_unix=ts,
        mono_ts=float(seq),
        mid_price=mid,
        source="operational_loop_test",
    )


def _write_auth(tmp_path: Path, contract: PaperShadowRunContractV1) -> Path:
    p = tmp_path / "auth.json"
    p.write_text(
        json.dumps(
            {
                "BOUND_TO": {
                    "RUN_ID": contract.run_id,
                    "FIXPOINT_SHA": contract.fixpoint_sha,
                    "SETTINGS_DIGEST": contract.settings_digest,
                    "RUN_DURATION_SECONDS": contract.run_duration_seconds,
                    "MAX_OBSERVATION_COUNT": contract.max_observation_count,
                    "MAX_CYCLE_COUNT": contract.max_cycle_count,
                    "MAX_SIMULATED_EXECUTION_COUNT": contract.max_simulated_execution_count,
                    "EXECUTION_SINK": contract.execution_sink,
                },
                "OBSERVATION_TOKEN": SHADOW_OBSERVATION_OPERATOR_GO,
                "ACTIVATION_TOKEN": SHADOW_ACTIVATION_OPERATOR_GO,
            }
        ),
        encoding="utf-8",
    )
    return p


def _contract_with_overrides(**overrides: int) -> PaperShadowRunContractV1:
    import subprocess

    from src.ops.paper_shadow_bounded_orchestrator_v1.run_settings_manifest_v1 import (
        build_run_settings_manifest_v1,
    )

    manifest = build_run_settings_manifest_v1(repo_root=REPO)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=REPO, text=True).strip()
    raw = {
        "RUN_ID": "PAPER_SHADOW_RUN_001",
        "RUN_TYPE": "BOUNDED_PAPER_SHADOW",
        "RUN_DURATION_SECONDS": 3600,
        "MAX_OBSERVATION_COUNT": 2000,
        "MAX_CYCLE_COUNT": 2000,
        "MAX_SIMULATED_EXECUTION_COUNT": 120,
        "MAX_SIMULATED_OPEN_POSITION_COUNT": 1,
        "ENTER_REQUIRED_FOR_SUCCESS": False,
        "FIXPOINT_SHA": head,
        "FIXPOINT_TREE": tree,
        "SETTINGS_DIGEST": str(manifest["RUN_SETTINGS_DIGEST"]),
        "OBSERVATION_SOURCE": "wallclock_public_md_observe_v1",
        "EXECUTION_SINK": "SIMULATED_ONLY",
    }
    raw.update(overrides)
    tmp = Path("/tmp") / "paper_shadow_contract_override.json"
    tmp.write_text(json.dumps(raw), encoding="utf-8")
    return load_paper_shadow_run_contract_v1(
        contract_path=tmp,
        settings_digest_path=CONTRACT_DIR / "run_settings_digest.json",
    )


class _FakeClock:
    def __init__(self) -> None:
        self._mono = 0.0
        self._wall = 1_700_000_000.0

    def mono(self) -> float:
        return self._mono

    def wall(self) -> float:
        return self._wall

    def sleep(self, seconds: float) -> None:
        self._mono += seconds
        self._wall += seconds


def _hooks(
    *,
    clock: _FakeClock,
    ticks: tuple[ObservationMarketTickV1, ...] = (_tick(),),
    productive_step=None,
    kill_switch=None,
) -> OperationalRunHooksV1:
    return OperationalRunHooksV1(
        tick_source=InjectedObservationTickSourceV1(ticks=ticks, repeat_last=True),
        productive_step=productive_step,
        clock_mono=clock.mono,
        clock_wall=clock.wall,
        sleep_fn=clock.sleep,
        poll_interval_seconds=0.01,
        kill_switch=kill_switch or (lambda: False),
    )


def _pre_external_step_factory(event):
    def step(
        bridge_state: HardenedBridgeSessionStateV2,
        tick: ObservationMarketTickV1,
        reference_price: Decimal,
        wall_now_unix: float,
        session_id: str,
        cycle_index: int,
    ) -> ProductiveCycleStepOutcomeV1:
        base = default_productive_cycle_step_v1(
            bridge_state,
            tick,
            reference_price,
            wall_now_unix,
            session_id,
            cycle_index,
        )
        if cycle_index == 1:
            return ProductiveCycleStepOutcomeV1(
                ok=True,
                productive_cycle_ran=True,
                bridge_cycle=base.bridge_cycle,
                pre_external_event=event,
                md_blockers=(),
                fail_fatal=False,
                labels=base.labels,
            )
        return base

    return step


def test_operational_loop_duration_bound(tmp_path: Path) -> None:
    contract = _contract_with_overrides(RUN_DURATION_SECONDS=2)
    auth = _write_auth(tmp_path, contract)
    clock = _FakeClock()
    result = run_paper_shadow_bounded_operational_run_v1(
        contract=contract,
        repo_root=REPO,
        authorization_path=auth,
        hooks=_hooks(clock=clock),
    )
    assert result.run_started is True
    assert result.stop_reason == "NORMAL_DURATION_COMPLETE"
    assert result.counters.observation_count >= 1
    assert result.owner_go_consumed is False


def test_operational_loop_observation_bound(tmp_path: Path) -> None:
    contract = _contract_with_overrides(
        RUN_DURATION_SECONDS=3600,
        MAX_OBSERVATION_COUNT=3,
    )
    auth = _write_auth(tmp_path, contract)
    clock = _FakeClock()
    result = run_paper_shadow_bounded_operational_run_v1(
        contract=contract,
        repo_root=REPO,
        authorization_path=auth,
        hooks=_hooks(clock=clock),
    )
    assert result.stop_reason == "MAX_OBSERVATION_BOUND"
    assert result.counters.observation_count == 3


def test_operational_loop_cycle_bound(tmp_path: Path) -> None:
    contract = _contract_with_overrides(
        RUN_DURATION_SECONDS=3600,
        MAX_CYCLE_COUNT=2,
        MAX_OBSERVATION_COUNT=2000,
    )
    auth = _write_auth(tmp_path, contract)
    clock = _FakeClock()
    result = run_paper_shadow_bounded_operational_run_v1(
        contract=contract,
        repo_root=REPO,
        authorization_path=auth,
        hooks=_hooks(clock=clock),
    )
    assert result.stop_reason == "MAX_CYCLE_BOUND"
    assert result.counters.cycle_count == 2


def test_operational_loop_simulation_bound(tmp_path: Path) -> None:
    event = _representative_ghv_pre_external_event_v1(tail_path=GHV_TAIL)
    contract = _contract_with_overrides(
        RUN_DURATION_SECONDS=3600,
        MAX_SIMULATED_EXECUTION_COUNT=1,
        MAX_OBSERVATION_COUNT=50,
    )
    auth = _write_auth(tmp_path, contract)
    clock = _FakeClock()
    result = run_paper_shadow_bounded_operational_run_v1(
        contract=contract,
        repo_root=REPO,
        authorization_path=auth,
        hooks=_hooks(
            clock=clock,
            productive_step=_pre_external_step_factory(event),
        ),
    )
    assert result.stop_reason == "MAX_SIMULATED_EXECUTION_BOUND"
    assert result.counters.simulated_execution_count == 1
    assert result.evidence["pre_external_count"] >= 1
    assert result.evidence["shadow_continuation_count"] >= 1


def test_operational_loop_kill_switch(tmp_path: Path) -> None:
    contract = _contract_with_overrides(RUN_DURATION_SECONDS=3600)
    auth = _write_auth(tmp_path, contract)
    clock = _FakeClock()
    trips = {"n": 0}

    def kill() -> bool:
        trips["n"] += 1
        return trips["n"] >= 2

    result = run_paper_shadow_bounded_operational_run_v1(
        contract=contract,
        repo_root=REPO,
        authorization_path=auth,
        hooks=_hooks(clock=clock, kill_switch=kill),
    )
    assert result.stop_reason == "KILL_SWITCH_FAIL_CLOSED"


def test_authorization_fail_closed_before_run(tmp_path: Path) -> None:
    contract = load_paper_shadow_run_contract_v1(
        contract_path=CONTRACT_DIR / "run_contract_v1.json",
        settings_digest_path=CONTRACT_DIR / "run_settings_digest.json",
    )
    bad = tmp_path / "bad_auth.json"
    bad.write_text("{}", encoding="utf-8")
    go = validate_owner_go_authorization_v1(contract=contract, authorization_path=bad)
    assert go.ok is False
    result = run_paper_shadow_bounded_operational_run_v1(
        contract=contract,
        repo_root=REPO,
        authorization_path=bad,
        go_validation=go,
        hooks=OperationalRunHooksV1(
            tick_source=InjectedObservationTickSourceV1(ticks=(_tick(),)),
        ),
    )
    assert result.run_started is False


def test_offline_operational_loop_reproof_summary(tmp_path: Path) -> None:
    """Aggregate reproof flag for evidence bundle."""
    event = _representative_ghv_pre_external_event_v1(tail_path=GHV_TAIL)
    contract = _contract_with_overrides(
        RUN_DURATION_SECONDS=1,
        MAX_OBSERVATION_COUNT=5,
        MAX_CYCLE_COUNT=5,
        MAX_SIMULATED_EXECUTION_COUNT=2,
    )
    auth = _write_auth(tmp_path, contract)
    clock = _FakeClock()
    result = run_paper_shadow_bounded_operational_run_v1(
        contract=contract,
        repo_root=REPO,
        authorization_path=auth,
        hooks=_hooks(
            clock=clock,
            productive_step=_pre_external_step_factory(event),
        ),
    )
    assert result.run_started
    assert result.evidence["REAL_POST_COUNT"] == 0
    assert result.evidence["EXTERNAL_EFFECT_COUNT"] == 0
