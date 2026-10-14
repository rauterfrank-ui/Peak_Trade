"""Subprocess entrypoint for CURRENT POST hard-crash injection (test-only).

Invoked only from offline harness tests. Uses mock transport and fake K1.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

# Ensure repo root is importable when run as script.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tests.ops._current_productive_post_hard_crash_harness_v1 import (  # noqa: E402
    CRASH_EXIT,
    ValidOkxPostAckOpenerV1,
)
from tests.ops._pilot_guard_enter_post_test_helpers_v1 import (  # noqa: E402
    OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
    PilotGuardReadTransport,
    establish_new_risk_one_shot_admission_seal_for_tests_v1,
    mandatory_new_risk_execute_kwargs,
    ratified_pilot_guard_config_for_tests,
)
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (  # noqa: E402
    POST_OWNER_GO,
    OneShotJoinProbeV1,
    _FakeKeychainBackend,
    _TimeoutOpener,
    _new_risk_envelope,
    _persist_post_go,
)


def _crash(code: int) -> None:
    os._exit(code)


def _load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("CONFIG_MALFORMED")
    return payload


def _new_risk_plan_envelope(*, clordid: str = "pt-hard-crash-v1") -> Any:
    return _new_risk_envelope()


def _pilot_bind(store_root: Path, envelope: Any) -> Any:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_pilot_capital_guard_post_bind_v1 import (
        enforce_pilot_capital_guard_before_enter_post_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    )

    kwargs = mandatory_new_risk_execute_kwargs(store_root)
    return enforce_pilot_capital_guard_before_enter_post_v1(
        pilot_capital_guard_bind_go=OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
        envelope=envelope,
        read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
        pretrade_decision_id="hard-crash-pretrade",
        native_instrument_id=kwargs["pilot_native_instrument_id"],
        canonical_decision_id="hard-crash-decision",
        account_identity="acct-pilot-bind-1",
        origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        guard_config=kwargs["pilot_capital_guard_config"],
        atomic_state_dir=kwargs["pilot_atomic_state_dir"],
    )


def _persist_correlation(store_root: Path, envelope: Any, pilot_bind: Any) -> None:
    import src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 as adm_mod

    kwargs = mandatory_new_risk_execute_kwargs(store_root)
    adm_mod.persist_enter_post_lifecycle_correlation_v1(
        store_root=store_root,
        envelope=envelope,
        authorization_binding=pilot_bind.authorization_binding,
        pretrade_decision_id="hard-crash-pretrade",
        submit_attempt_id=f"enter-post:{envelope.client_order_id}",
        atomic_state_dir=kwargs["pilot_atomic_state_dir"],
    )


def _run_one_shot_join(
    store_root: Path,
    envelope: Any,
    *,
    opener_factory: Callable[[], Any] | None = None,
) -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
    )

    _persist_post_go(store_root)
    attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=POST_OWNER_GO,
        store_root=store_root,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=opener_factory or (lambda: _TimeoutOpener()),
        probe=OneShotJoinProbeV1(),
    )


def _run_execute_post(
    store_root: Path,
    envelope: Any,
    *,
    opener_factory: Callable[[], Any] | None = None,
) -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        OWNER_GO,
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1,
    )
    from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
        MockCurrentProductive29PIntegrityBackendV1,
    )

    kwargs = mandatory_new_risk_execute_kwargs(store_root)
    execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
        owner_go=OWNER_GO,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        envelope=envelope,
        store_root=store_root,
        evidence_root=store_root / "evidence",
        perform_real_venue_post=True,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=opener_factory or (lambda: _TimeoutOpener()),
        read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
        execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
            origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            drift="",
        ),
        **kwargs,
    )


def _scenario_c1(store_root: Path, envelope: Any) -> None:
    import src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 as join_mod

    orig = join_mod.full_core_atomic_reserve_owner_go_authorization_v1

    def _crash_before_reserve(*args: Any, **kwargs: Any) -> Any:
        _crash(CRASH_EXIT["C1"])

    with patch.object(
        join_mod, "full_core_atomic_reserve_owner_go_authorization_v1", _crash_before_reserve
    ):
        _pilot_bind(store_root, envelope)


def _scenario_c2(store_root: Path, envelope: Any) -> None:
    import src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 as adm

    pilot_bind = _pilot_bind(store_root, envelope)

    def _crash_before_correlation(*args: Any, **kwargs: Any) -> Any:
        _crash(CRASH_EXIT["C2"])

    with patch.object(
        adm, "persist_enter_post_lifecycle_correlation_v1", _crash_before_correlation
    ):
        _persist_correlation(store_root, envelope, pilot_bind)


def _scenario_c3(store_root: Path, envelope: Any) -> None:
    pilot_bind = _pilot_bind(store_root, envelope)
    _persist_correlation(store_root, envelope, pilot_bind)
    import src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as join_mod

    def _crash_before_admission_seal(*args: Any, **kwargs: Any) -> Any:
        _crash(CRASH_EXIT["C3"])

    with patch.object(
        join_mod,
        "prove_current_productive_one_shot_post_admission_seal_v1",
        _crash_before_admission_seal,
    ):
        _run_one_shot_join(store_root, envelope)


def _scenario_c4(store_root: Path, envelope: Any) -> None:
    pilot_bind = _pilot_bind(store_root, envelope)
    _persist_correlation(store_root, envelope, pilot_bind)
    import src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as join_mod

    def _crash_before_mint(*args: Any, **kwargs: Any) -> Any:
        _crash(CRASH_EXIT["C4"])

    with patch.object(join_mod, "issue_external_effect_permit_v1", _crash_before_mint):
        _run_one_shot_join(store_root, envelope)


def _scenario_c6(store_root: Path, envelope: Any) -> None:
    import src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 as consume_mod

    orig_replace = Path.replace

    def _crash_before_replace(self: Path, target: Path) -> None:
        if self.name.endswith(".json.tmp"):
            _crash(CRASH_EXIT["C6"])
        return orig_replace(self, target)

    establish_new_risk_one_shot_admission_seal_for_tests_v1(
        store_root=store_root, envelope=envelope
    )
    with patch.object(Path, "replace", _crash_before_replace):
        try:
            _run_one_shot_join(store_root, envelope)
        except Exception:
            _crash(CRASH_EXIT["C6"])


def _scenario_c9_http200(store_root: Path, envelope: Any, extra: dict[str, Any]) -> None:
    accept_path = Path(
        str(extra.get("mock_accept_evidence_path") or store_root / "mock_exchange_accept_v1.json")
    )
    import src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 as seam_mod
    from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
        classify_full_core_post_result_v1,
    )

    orig_join = seam_mod.join_full_core_post_result_to_lifecycle_v1
    clordid = str(envelope.client_order_id)

    def _crash_before_lifecycle_join(*args: Any, **kwargs: Any) -> Any:
        result = kwargs.get("result") if "result" in kwargs else (args[0] if args else None)
        if result is None:
            _crash(CRASH_EXIT["C9_HTTP200"])
        classified = classify_full_core_post_result_v1(
            result=result,
            sent_clordid=clordid,
            submit_count=1,
        )
        parent_stub: dict[str, Any] = {}
        if accept_path.is_file():
            try:
                loaded = json.loads(accept_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    parent_stub = loaded
            except json.JSONDecodeError:
                parent_stub = {}
        accept_path.write_text(
            json.dumps(
                {
                    **parent_stub,
                    "phase": "CHILD_POST_TRANSPORT_PRE_LIFECYCLE_JOIN",
                    "mapper_seam": "join_full_core_post_result_to_lifecycle_v1",
                    "http_status": int(getattr(result, "http_status", 0) or 0),
                    "classification": str(classified.get("classification") or ""),
                    "venue_order_id": str(classified.get("venue_order_id") or ""),
                    "clordid": clordid,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        _crash(CRASH_EXIT["C9_HTTP200"])
        return orig_join(*args, **kwargs)

    opener = ValidOkxPostAckOpenerV1(clordid=clordid)
    with patch.object(
        seam_mod, "join_full_core_post_result_to_lifecycle_v1", _crash_before_lifecycle_join
    ):
        _run_execute_post(store_root, envelope, opener_factory=lambda: opener)


def _scenario_c9(store_root: Path, envelope: Any, extra: dict[str, Any]) -> None:
    accept_path = Path(
        str(extra.get("mock_accept_evidence_path") or store_root / "mock_exchange_accept_v1.json")
    )
    import src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as join_mod

    orig_join_post = join_mod._DurableConsumeThenK1HttpTransportV1.post_trade_order

    def _join_post_accept_then_crash(self: Any, **kwargs: Any) -> Any:
        result = orig_join_post(self, **kwargs)
        accept_path.write_text(
            json.dumps(
                {
                    "accepted": True,
                    "http_status": getattr(result, "http_status", 200),
                    "clordid": envelope.client_order_id,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        _crash(CRASH_EXIT["C9"])
        return result

    with patch.object(
        join_mod._DurableConsumeThenK1HttpTransportV1,
        "post_trade_order",
        _join_post_accept_then_crash,
    ):
        # Timeout after send simulates venue accept with lost local response processing.
        _run_execute_post(store_root, envelope, opener_factory=lambda: _TimeoutOpener())


def _scenario_c10(store_root: Path, envelope: Any) -> None:
    import src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 as post_mod

    orig = post_mod._mark_pilot_guard_submit_boundary_when_send_evidenced_v1

    def _crash_before_mark(*args: Any, **kwargs: Any) -> None:
        _crash(CRASH_EXIT["C10"])

    with patch.object(
        post_mod, "_mark_pilot_guard_submit_boundary_when_send_evidenced_v1", _crash_before_mark
    ):
        _run_execute_post(store_root, envelope, opener_factory=lambda: _TimeoutOpener())


def _scenario_c11(store_root: Path, envelope: Any) -> None:
    import src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as join_mod

    def _crash_in_recon(*args: Any, **kwargs: Any) -> Any:
        _crash(CRASH_EXIT["C11"])

    with patch.object(
        join_mod,
        "run_dw_exchange_reconciliation_wiring_after_post_submit_v1",
        _crash_in_recon,
    ):
        _run_execute_post(store_root, envelope, opener_factory=lambda: _TimeoutOpener())


def _scenario_c12(store_root: Path, envelope: Any) -> None:
    import src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 as atomic_mod

    orig = atomic_mod._atomic_write_state_v1

    def _crash_mid_recovery_write(state_path: Path, payload: Any) -> None:
        orig(state_path, payload)
        if str(payload.get("state") or "") == "SUBMIT_MAY_HAVE_OCCURRED":
            _crash(CRASH_EXIT["C12"])

    with patch.object(atomic_mod, "_atomic_write_state_v1", _crash_mid_recovery_write):
        _run_execute_post(store_root, envelope, opener_factory=lambda: _TimeoutOpener())


_SCENARIOS: dict[str, Callable[..., None]] = {
    "C1": _scenario_c1,
    "C2": _scenario_c2,
    "C3": _scenario_c3,
    "C4": _scenario_c4,
    "C6": _scenario_c6,
    "C9": _scenario_c9,
    "C9_HTTP200": _scenario_c9_http200,
    "C10": _scenario_c10,
    "C11": _scenario_c11,
    "C12": _scenario_c12,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store-root", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    store_root = Path(args.store_root)
    config = _load_config(Path(args.config))
    point = str(config.get("crash_point") or "").strip()
    extra = config.get("extra") if isinstance(config.get("extra"), dict) else {}
    if point not in _SCENARIOS:
        _crash(1)
    envelope = _new_risk_plan_envelope()
    if point in {"C9", "C9_HTTP200"}:
        _SCENARIOS[point](store_root, envelope, extra)
    else:
        _SCENARIOS[point](store_root, envelope)
    _crash(2)


if __name__ == "__main__":
    main()
