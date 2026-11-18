"""Signed GET recovery and process-loss replay for the original net order."""

from base64 import b64encode
from contextlib import contextmanager
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hmac
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

import pytest

from src.governance import (
    f1_m9_productive_apply_durable_ledger_paths_v1 as ledger_resolution,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    productive_read_only_get_transport_v1 as wire,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_bounded_continuous_run_owner_go_wiring_v1 as owner_go,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    bind_already_held_k1_venue_auth_session_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
    recover_submitted_net_reversal_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    build_s8_occupied_lane_pairs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    load_external_effect_durable_consume_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CurrentProductive29PChainBaselineError,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import supervisor_v1 as supervisor
from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import startup_factory_v1, unattended_v1
from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
    restore_layered_core_episode_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    AuthenticatedEntryEpisodeRequestV1,
    PortfolioBudgetHostV1,
    StandingStartupAccountObservationPortV1,
    collect_host_account_observation_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
    FAKE_OPAQUE,
)
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    _continuous_auth,
)
from tests.ops.test_portfolio_budget_host_v1 import _fetch


class SignedNetReversalGetFixture:
    def __init__(self, data, scenario):
        self.data = data
        self.scenario = scenario
        self.clock = datetime.fromisoformat(data["observed_at"])
        self.calls = []
        self.secrets = json.loads(FAKE_OPAQUE)

    def position(self):
        stamp = self.data["socket_ms"]
        side = self.data["envelope"]["side"]
        opened = Decimal(self.data["envelope"]["quantity"]) - self.closing_size()
        return {
            "instId": self.data["envelope"]["instrument_id"],
            "instType": "SWAP",
            "pos": str(opened if side == "buy" else -opened),
            "posSide": "net",
            "mgnMode": "cross",
            "ccy": "USDT",
            "avgPx": "1994",
            "tradeId": self.data.get("opening_trade_id", "124"),
            "posId": self.data.get("position_id", "8923"),
            "fee": "-0.02",
            "cTime": str(stamp + 200),
            "uTime": str(stamp + 400),
        }

    def closing_size(self):
        return Decimal(self.data.get("closing_size", "1"))

    def body(self, path, query):
        envelope = self.data["envelope"]
        stamp = self.data["socket_ms"]
        order = {
            "instId": envelope["instrument_id"],
            "instType": "SWAP",
            "ordId": self.data.get("venue_order_id", "91234"),
            "clOrdId": envelope["client_order_id"],
            "side": envelope["side"],
            "posSide": "net",
            "tdMode": envelope["td_mode"],
            "ordType": envelope["order_type"],
            "reduceOnly": "false",
            "sz": envelope["quantity"],
            "accFillSz": envelope["quantity"],
            "state": "filled",
            "uTime": str(stamp + 300),
        }
        fill = {
            **{
                key: order[key]
                for key in ("instId", "instType", "ordId", "clOrdId", "side", "posSide")
            },
            "tradeId": self.data.get("closing_trade_id", "123"),
            "billId": "1001",
            "fillSz": str(self.closing_size()),
            "fillPx": "1995",
            "feeCcy": "USDT",
            "fee": "-0.02",
            "fillPnl": "0.20",
            "fillTime": str(stamp + 100),
        }
        if self.scenario == "partial":
            order.update(state="canceled", accFillSz="1")
        if path.endswith("/config"):
            assert query == {}
            return [{"uid": self.data["account"], "posMode": "net_mode"}]
        assert query["instId"] == [envelope["instrument_id"]]
        if path.endswith("/orders-pending"):
            if self.scenario == "open-order":
                return [{**order, "ordId": "91235", "clOrdId": "other-order", "state": "live"}]
            return []
        if path.endswith("/orders-history"):
            return [order]
        if path.endswith("/trade/order"):
            assert query["clOrdId"] == [envelope["client_order_id"]]
            return [order]
        if path.endswith("/fills"):
            if "after" not in query:
                return [
                    {**fill, "ordId": str(i), "clOrdId": f"other{i}", "billId": str(i)}
                    for i in range(2000, 1901, -1)
                ] + [fill]
            assert query["after"] == ["1001"]
            if self.scenario == "missing-page":
                raise TimeoutError("scripted missing page")
            if self.scenario == "partial":
                return []
            return [
                {
                    **fill,
                    "billId": "1000",
                    "tradeId": self.data.get("opening_trade_id", "124"),
                    "fillSz": str(Decimal(envelope["quantity"]) - self.closing_size()),
                    "fillPnl": "0",
                    "fillPx": "1994",
                    "fillTime": str(stamp + 200),
                    **({"instId": "NEAR-USDT-SWAP"} if self.scenario == "foreign-page" else {}),
                }
            ]
        if path.endswith("/positions"):
            return [
                {
                    **self.position(),
                    "markPx": "1993",
                    **({"pos": "0"} if self.scenario == "flat" else {}),
                }
            ]
        if path.endswith("/positions-history"):
            old_position_id = self.data.get("old_position_id", "8923")
            fee = Decimal(self.data.get("old_position_fee", "-0.03")) - Decimal("0.02")
            realized = Decimal("0.20") + fee - Decimal("0.01")
            if self.scenario == "bad-cash":
                realized += Decimal("0.01")
            assert query["posId"] == [old_position_id] and query["limit"] == ["100"]
            assert query["before"] == [str(stamp - 1)]
            return [
                {
                    "instId": envelope["instrument_id"],
                    "instType": "SWAP",
                    "direction": "short" if envelope["side"] == "buy" else "long",
                    "posSide": "net",
                    "mgnMode": "cross",
                    "ccy": "USDT",
                    "type": "2",
                    "posId": old_position_id,
                    "cTime": self.data["old_created_ms"],
                    "openMaxPos": str(self.closing_size()),
                    "closeTotalPos": str(self.closing_size()),
                    "pnl": "0.20",
                    "fee": str(fee),
                    "fundingFee": "-0.01",
                    "liqPenalty": "0",
                    "settledPnl": "",
                    "realizedPnl": str(realized),
                    "uTime": str(stamp + 350),
                }
            ]
        raise AssertionError(path)

    @contextmanager
    def open(self, request, timeout):
        url = urlsplit(request.full_url)
        assert request.get_method() == "GET" and url.hostname == wire.AUTHORIZED_HOST
        timestamp = request.get_header("Ok-access-timestamp")
        endpoint = url.path + (f"?{url.query}" if url.query else "")
        signature = hmac.digest(
            self.secrets["secretKey"].encode(), f"{timestamp}GET{endpoint}".encode(), "sha256"
        )
        assert request.get_header("Ok-access-sign").encode() == b64encode(signature)
        self.calls.append(endpoint)
        rows = self.body(url.path, parse_qs(url.query))
        raw = json.dumps({"code": "0", "data": rows}).encode()
        yield SimpleNamespace(status=200, url=request.full_url, read=lambda: raw)

    @contextmanager
    def port(self):
        handle = bind_already_held_k1_venue_auth_session_v1(
            api_key=self.secrets["apiKey"],
            api_secret=self.secrets["secretKey"],
            passphrase=self.secrets["passphrase"],
        )
        try:
            with (
                patch.object(wire, "build_opener", lambda *_: self),
                patch.object(wire, "utc_now_iso_v1", lambda: self.clock.isoformat()),
            ):
                yield wire.FullCoreProductiveReadOnlyGetTransportV1(
                    handle=handle, max_request_count=28
                )
        finally:
            release_k1_venue_auth_session_v1(handle)


def _write_host_manifest(root, data, scenario):
    roots = {
        "public_store_root": root / "public",
        "private_store_root": root / "private",
        "lane_state_root": root / "scope",
        "cap24_productivity_root": root / "test-selection-root",
        "lock_root": root / "test-host-locks",
        "occupied_mark_proof_root": Path(data["proof_root"]),
    }
    for path in roots.values():
        path.mkdir(exist_ok=True)
    canonical_apply = ledger_resolution.resolve_canonical_f1_m9_productive_apply_ledger_paths_v1()
    roots["f1_m9_ledger_root"] = canonical_apply.apply_ledger_path.parent
    auth = asdict(_continuous_auth(native_id=data["bound"]["venue_native_id"], max_cycles=1))
    for key in ("continuous_owner_go", "native_id", "bar", "expected_cursor_floor"):
        del auth[key]
    runtime_config = {
        "repository_sha": data["revision"],
        "roots": {key: str(value) for key, value in roots.items()},
        "expected_account_identity": data["account"],
        "bound": data["bound"],
        "authorization": auth,
    }
    path = root / f"host-manifest-{scenario}.json"
    if not path.exists():
        manifest = startup_factory_v1.build_occupied_n1_manifest_v1(
            host_id="offline-original-slot",
            state_root=root / "net-reversal-restart" / scenario,
            expires_at_unix=time.time() + 180,
            runtime_config=runtime_config,
        )
        path.write_text(json.dumps(manifest))
    return path


def _run_booking_supervisor(root, data, scenario, *, crash=False, v2=None):
    original_init = PortfolioBudgetHostV1.__init__
    original_save = PortfolioCapitalReservationBudgetOwnerV1._persist_locked
    fixture = SignedNetReversalGetFixture(data, scenario)
    manifest = _write_host_manifest(root, data, scenario)
    previous_go = owner_go.load_bounded_continuous_run_owner_go_decision_v1()
    local_go = {**previous_go, "baseline_origin_main_sha": data["revision"]}
    results = []
    contexts = []

    def init_host(self, **kwargs):
        original_init(self, **{**kwargs, "clock": fixture.clock.timestamp})

    def save(owner):
        original_save(owner)
        if crash and owner._live_net_reversal_bookings:
            os.kill(os.getpid(), signal.SIGKILL)

    @contextmanager
    def offline_get_only_transport(**_):
        with fixture.port() as port:
            contexts.append("open")
            yield port, {}
        contexts.append("close")

    def observe_supervisor(**kwargs):
        assert contexts == ["open"]
        result = supervisor.run_n1_standing_pre_external_supervisor_v1(**kwargs)
        results.append(result)
        return result

    with (
        patch.object(startup_factory_v1, "assert_current_productive_29p_execution_identity_v1"),
        patch.object(
            owner_go, "load_bounded_continuous_run_owner_go_decision_v1", return_value=local_go
        ),
        patch.object(
            startup_factory_v1,
            "open_governed_live_c1_get_only_fresh_pretrade_transport_v1",
            offline_get_only_transport,
        ),
        patch.object(
            unattended_v1, "run_n1_standing_pre_external_supervisor_v1", observe_supervisor
        ),
        patch.object(PortfolioBudgetHostV1, "__init__", init_host),
        patch.object(PortfolioCapitalReservationBudgetOwnerV1, "_persist_locked", save),
    ):
        if v2 is not None:
            from src.ops.n1_occupied_net_reversal_host_v2 import (
                run_occupied_n1_net_reversal_host_v2,
            )

            def factory(attempt, evidence):
                prepared = startup_factory_v1.prepare_occupied_n1_request_v1(
                    attempt_index=attempt,
                    evidence_root=evidence,
                    runtime_config=v2["runtime_config"],
                )
                # The process dies during booking, before the test POST port may open.
                return replace(prepared, runtime_config_digest=v2["runtime_config_digest"])

            run_occupied_n1_net_reversal_host_v2(
                bounds=unattended_v1.UnattendedHostBoundsV1(**v2["bounds"]),
                state_root=Path(v2["state_root"]),
                request_factory=factory,
                clock=fixture.clock.timestamp,
            )
            raise AssertionError("V2 reached the end without the intended process loss")
        receipt = unattended_v1.host_service_v1(manifest_path=manifest, action="run")
    assert receipt["result"]["attempts"] == 1, receipt
    assert contexts == ["open", "close"]
    return results[0], fixture.calls


def crash_after_net_reversal_commit_v1(root, *, v2=False):
    root = Path(root)
    data = json.loads((root / "net-reversal-test-input.json").read_bytes())
    registration = json.loads((root / "v2-test-registration.json").read_bytes()) if v2 else None
    result, _ = _run_booking_supervisor(root, data, "complete", crash=True, v2=registration)
    raise AssertionError(result.trace.extra.get("net_reversal_readback"))


def _kill_booking_process(root, ledger_root, *, v2=False):
    command = """
import sys
from pathlib import Path
from pytest import MonkeyPatch

def offline(event, args):
    if event.startswith("socket."):
        raise AssertionError("socket in net reversal test")
sys.addaudithook(offline)

from tests.ops.test_authenticated_net_reversal_booking_v1 import crash_after_net_reversal_commit_v1
from tests.ops._current_productive_pre_external_test_process_isolation_v1 import (
    establish_current_productive_pre_external_test_process_isolation_v1,
)

root, ledger_root = map(Path, sys.argv[1:3])
with MonkeyPatch.context() as patch:
    if ledger_root.is_relative_to(root):
        establish_current_productive_pre_external_test_process_isolation_v1(
            monkeypatch=patch, f1_root=ledger_root, reseed_workspace_f1_m9=False
        )
    crash_after_net_reversal_commit_v1(root, v2=sys.argv[3] == "v2")
"""
    env = os.environ.copy()
    if env.get("GITHUB_ACTIONS") == "true":
        env.update(PT_RUNTIME_MODE="provisioned", PT_PROVISIONED_PYTHON=sys.executable)
    child = subprocess.run(
        ["./scripts/pt", "-B", "-c", command, str(root), str(ledger_root), "v2" if v2 else "v1"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert child.returncode == -signal.SIGKILL, (child.stdout, child.stderr)


def assert_original_net_reversal_booking_v1(
    *,
    tmp_path,
    monkeypatch,
    bound,
    proof_root,
    reversal,
    envelope,
    record,
    submit_root,
    repository_sha,
    closes,
    occupied,
    first_authorization,
    signer,
    exceptional_close=False,
    automatic_continuation=False,
    crash_continuation=False,
    end_budget_continuation=False,
):
    from tests.ops.test_bounded_multislot_connected_cycle_v1 import ports
    from tests.ops.test_bounded_slot_connected_roundtrip_v1 import market
    from tests.ops.test_current_scope_mark_clock_v1 import provenance
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        read_occupied_scope_mark_snapshot_v1,
    )

    socket = datetime.fromisoformat(record["transport_attempt"]["socket_boundary_at_utc"])
    data = {
        "revision": repository_sha,
        "account": reversal.episode.account_scope.account_identity,
        "bound": bound.to_dict(),
        "proof_root": str(proof_root),
        "envelope": envelope.to_runtime_json_v1(),
        "socket_ms": int(socket.timestamp() * 1000),
        "old_created_ms": str(
            int(
                (datetime.fromisoformat(reversal.decision_epoch) - timedelta(seconds=1)).timestamp()
                * 1000
            )
        ),
        "observed_at": (socket + timedelta(seconds=1)).isoformat(),
    }
    (tmp_path / "net-reversal-test-input.json").write_text(json.dumps(data))
    if automatic_continuation:
        _assert_n1_continuation_v2(
            tmp_path,
            monkeypatch,
            data,
            bound,
            closes,
            first_authorization,
            signer,
            crash=crash_continuation,
            end_budget=end_budget_continuation,
        )
        return
    root = tmp_path / "private/portfolio_budget_host_v1"
    paths = {
        root / "owner" / "reservations.sqlite3",
        submit_root / "full_core_external_effect_permit_consume_v1.json",
        *[p for p in (tmp_path / "reversal-grant").rglob("*") if p.is_file()],
    }
    raw = {path: path.read_bytes() for path in paths}

    original_manifest = _write_host_manifest(tmp_path, data, "manifest-digest-original")
    tampered = json.loads(original_manifest.read_bytes())
    archive_root = tmp_path / "archived-f1-m9"
    archive_root.mkdir()
    for name in ("apply.jsonl", "apply_rev.jsonl", "threshold.jsonl", "threshold_rev.jsonl"):
        (archive_root / name).touch()
    config = tampered["runtime_request_config"]
    archive_config = {
        **config,
        "roots": {**config["roots"], "f1_m9_ledger_root": str(archive_root)},
    }
    with pytest.raises(ValueError, match="N1_STANDING_F1_M9_LEDGER_ROOT_MISMATCH"):
        startup_factory_v1.build_occupied_n1_manifest_v1(
            host_id="offline-original-slot",
            state_root=Path(tampered["state_root"]),
            expires_at_unix=tampered["bounds"]["expires_at_unix"],
            runtime_config=archive_config,
        )
    foreign_checkout = {**tampered["runtime_request_config"], "repository_sha": "0" * 40}
    with pytest.raises(CurrentProductive29PChainBaselineError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        startup_factory_v1.prepare_occupied_n1_request_v1(
            attempt_index=1,
            evidence_root=Path(tampered["state_root"]) / "attempts" / "1",
            runtime_config=foreign_checkout,
        )
    tampered["runtime_request_config"]["expected_account_identity"] += "-foreign"
    tampered_path = tmp_path / "host-manifest-foreign.json"
    tampered_path.write_text(json.dumps(tampered))

    def forbidden_ports(**_):
        pytest.fail("unproven request must not open ports or start a replacement order")

    previous_go = owner_go.load_bounded_continuous_run_owner_go_decision_v1()
    with (
        patch.object(startup_factory_v1, "assert_current_productive_29p_execution_identity_v1"),
        patch.object(
            owner_go,
            "load_bounded_continuous_run_owner_go_decision_v1",
            return_value={**previous_go, "baseline_origin_main_sha": data["revision"]},
        ),
        patch.object(
            startup_factory_v1,
            "open_governed_live_c1_get_only_fresh_pretrade_transport_v1",
            forbidden_ports,
        ),
        pytest.raises(ValueError, match="HOST_RESTART_REQUEST_BINDING_MISMATCH"),
    ):
        unattended_v1.host_service_v1(manifest_path=tampered_path, action="run")
    assert {path: path.read_bytes() for path in paths} == raw

    for scenario, reason in (
        ("missing-page", "RECONCILIATION_GET_RESPONSE_UNPROVEN"),
        ("foreign-page", "INSTRUMENT_IDENTITY_MISMATCH"),
        ("partial", "NET_REVERSAL_FULL_FILL_REQUIRED:CANCELED_AFTER_PARTIAL"),
        ("open-order", "NET_REVERSAL_OPEN_ORDERS"),
        ("flat", "NET_REVERSAL_TARGET_POSITION_UNPROVEN"),
        ("bad-cash", "NET_REVERSAL_SETTLEMENT_AMOUNT_UNPROVEN"),
    ):
        result, calls = _run_booking_supervisor(tmp_path, data, scenario)
        readback = result.trace.extra["net_reversal_readback"]
        assert not result.ok and result.policy_result is None and result.trace.post_count == 0
        assert reason in readback["reconciliation_blocker"], readback
        assert readback["client_order_id"] == envelope.client_order_id
        assert "booking_digest" not in readback and len(calls) >= 5
        assert {path: path.read_bytes() for path in paths} == raw

    _kill_booking_process(tmp_path, config["roots"]["f1_m9_ledger_root"])
    assert all(
        path.read_bytes() == original
        for path, original in raw.items()
        if path.suffix != ".sqlite3" or path.parent.name != "owner"
    )

    with patch.object(
        startup_factory_v1,
        "open_governed_live_c1_get_only_fresh_pretrade_transport_v1",
        forbidden_ports,
    ):
        continued = unattended_v1.host_service_v1(
            manifest_path=tmp_path / "host-manifest-complete.json", action="run"
        )["result"]
    assert continued["status"] == "RECOVERY_CHECKPOINT_REQUIRED"
    assert continued["checkpoint_blocker"] == "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"
    assert continued["attempts"] == 1

    manifest = json.loads((tmp_path / "host-manifest-complete.json").read_bytes())
    with patch.object(startup_factory_v1, "assert_current_productive_29p_execution_identity_v1"):
        recovered_request = startup_factory_v1.prepare_occupied_n1_request_v1(
            attempt_index=2,
            evidence_root=Path(manifest["state_root"]) / "attempts" / "2",
            runtime_config=manifest["runtime_request_config"],
        )
    assert (
        unattended_v1.unattended_request_digest_v1(recovered_request)
        == manifest["bounds"]["runtime_config_digest"]
    )
    config = recovered_request.request["config"]
    assert supervisor.budget_owner_root_for_config_v1(config) == root
    assert recovered_request.request["bound"] == bound

    fixture = SignedNetReversalGetFixture(data, "complete")
    with fixture.port() as port:
        resumed = PortfolioBudgetHostV1(
            root=supervisor.budget_owner_root_for_config_v1(config),
            private_rest_fetch=_fetch(uid=data["account"], positions=(fixture.position(),)),
            repository_sha=repository_sha,
            session_id="booked-net-fresh-process",
            expected_account_identity=config.expected_account_identity,
            clock=fixture.clock.timestamp,
            reconciliation_transport=port,
            execution_incident_state_path=Path(os.environ["PEAK_KILL_SWITCH_STATE_PATH"]),
        )
        try:
            pairs = build_s8_occupied_lane_pairs_v1(
                lane_state_root=config.lane_state_root, bound=bound
            )
            rid = reversal.old_reservation_id
            replay = recover_submitted_net_reversal_v1(
                lane_pair=pairs["LANE_1"], get_budget_host=lambda: resumed, proof_root=proof_root
            )
            assert not fixture.calls and replay.reservation_id == rid
            owner = resumed.owner
            row = owner.read_authenticated_net_reversal_v1(rid)
            assert row["booking_digest"] == replay.booking_digest
            receipt = proof_root / f"net-reversal-{row['settlement_digest']}.json"
            raw_proof = json.loads(receipt.read_bytes())["record"]
            assert raw_proof["binding"]["claim_id"] == record["transport_attempt"]["claim_id"]
            assert raw_proof["gets"][-1]["endpoint"].startswith(
                "/api/v5/account/positions-history?"
            )
            assert any("after=1001" in page["endpoint"] for page in raw_proof["gets"])
            hidden = receipt.rename(receipt.with_suffix(".held"))
            try:
                with pytest.raises(FileNotFoundError):
                    recover_submitted_net_reversal_v1(
                        lane_pair=pairs["LANE_1"],
                        get_budget_host=lambda: resumed,
                        proof_root=proof_root,
                    )
            finally:
                hidden.rename(receipt)
            assert Decimal(row["settlement_native"]) == Decimal("0.12")
            expected_capital = Decimal(25) + Decimal("0.12") * reversal.quote_to_usdc
            assert (
                owner.live_reversal_slot_basis_v1(
                    slot_id="LANE_1", reservation_id=rid, bound=bound
                ).net_basis_usdc
                == expected_capital
            )
            assert len(owner.risk_snapshot_v1()["state"]["live_net_reversal_bookings"][rid]) == 1
            collect_host_account_observation_v1(
                private_rest_fetch=StandingStartupAccountObservationPortV1(
                    fetch=resumed.fetch,
                    reconcile=lambda observation: resumed.reconcile_standing_startup_observation_v1(
                        {"LANE_1": bound}, observation, net_reversal_proof_root=proof_root
                    ),
                ),
                instrument_ids_by_native_id={bound.venue_native_id: bound.instrument_id},
                session_id=resumed.session_id,
                clock=fixture.clock.timestamp,
                expected_account=data["account"],
            )
            recovered, proofs = resumed.observe_authenticated_execution_reconciliation_v1(
                {"LANE_1": bound}, proof_root=proof_root, deliver_authenticated_incidents=True
            )
            assert recovered.position_side_v1(bound) == "SHORT"
            proof = proofs[rid]
            assert proof.identity_digest == envelope.envelope_digest
            assert (
                recovered.execution_reconciliation[rid]["net_reversal_booking_digest"]
                == replay.booking_digest
            )

            def current_clock(cls, tz=None):
                return fixture.clock if tz is None else fixture.clock.astimezone(tz)

            class Clock(datetime):
                now = classmethod(current_clock)

            monkeypatch.setattr(occupied, "datetime", Clock)
            now = fixture.clock.timestamp()
            cursor = Path(pairs["LANE_1"][0].lane_state_root)
            current_core = restore_layered_core_episode_v1(
                cursor, expected_instrument_id=bound.instrument_id
            )
            current_mark = current_core.running_reference.reference_price_r_t
            if not exceptional_close:
                current_mark += 1.5 * current_core.scope.d_t
            new = market(
                {"LANE_1": bound}, closes, now - 1, "booked-net-next", tmp_path / "next-g17"
            )
            side_input = ports(
                bound, fixture.clock.isoformat(), "booked-net-next:LANE_1", account=data["account"]
            )
            limits = side_input.venue_quantity_limits
            limits = replace(
                limits,
                public_source=replace(
                    limits.public_source, acquired_at_utc=fixture.clock.isoformat()
                ),
                private_source=replace(
                    limits.private_source, acquired_at_utc=fixture.clock.isoformat()
                ),
            )
            side_input = replace(
                side_input,
                observed_at=fixture.clock.isoformat(),
                acquisition_decision_id=limits.acquisition_decision_id,
                venue_quantity_limits=replace(limits, integrity_digest=limits.digest_v1()),
            )
            new.update(
                observed_unix=now,
                canonical_price_provenance_by_lane={
                    "LANE_1": provenance(
                        native=bound.venue_native_id,
                        mark=current_mark,
                        index=current_mark * 0.995,
                        event=now - 0.125,
                        captured=now,
                    )
                },
                live_29p_injected_by_lane={"LANE_1": side_input},
                portfolio_budget_owner=owner,
                host_budget_recovery=recovered,
                occupied_scope_mark_lane_id="LANE_1",
                authenticated_entry=AuthenticatedEntryEpisodeRequestV1(proof_root, proof),
            )
            if exceptional_close:
                _assert_exceptional_close_v1(pairs, new, resumed, rid, row, side_input)
                return
            lane = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **new)[
                "LANE_1"
            ]
            result = lane.governed_cycle_result
            assert result.post_count == 0 and result.position_management_execution_handoff is None
            assert result.reason_code == "DIRECT_REVERSAL_EXECUTION_ADMISSION_REQUIRED", result
            next_reversal = result.position_management_reversal
            assert next_reversal.current_contracts == Decimal(-1)
            assert next_reversal.target_contracts > 0
            assert next_reversal.slot_capital_basis_usdc == expected_capital
            assert next_reversal.old_reservation_id == rid
            assert lane.lane_id == "LANE_1" and lane.bound_instrument == bound
            mark = read_occupied_scope_mark_snapshot_v1(cursor)["mark"]
            assert mark["position_episode_id"] == envelope.envelope_digest, mark
            assert not any("/trade/order?" in endpoint for endpoint in fixture.calls)
            assert (
                owner.live_reversal_slot_basis_v1(
                    slot_id="LANE_1", reservation_id=rid, bound=bound
                ).net_basis_usdc
                == expected_capital
            )
            next_order, next_send = _assert_follow_on_net_reversal_dispatch_v1(
                lane_pair=pairs["LANE_1"],
                recovery=recovered,
                entry=new["authenticated_entry"],
                first_authorization=first_authorization,
                signer=signer,
            )
            assert (
                load_external_effect_durable_consume_v1(store_root=submit_root)["record"] == record
            )
        finally:
            resumed.close()

    second_socket = datetime.fromisoformat(next_send["transport_attempt"]["socket_boundary_at_utc"])
    second_gets = SignedNetReversalGetFixture(
        {
            **data,
            "envelope": next_order.to_runtime_json_v1(),
            "socket_ms": int(second_socket.timestamp() * 1000),
            "observed_at": (second_socket + timedelta(seconds=1)).isoformat(),
            "closing_size": str(abs(next_reversal.current_contracts)),
            "old_position_id": row["position_id"],
            "old_created_ms": row["position_created_ms"],
            "old_position_fee": row["position_fee"],
            "position_id": "8924",
            "venue_order_id": "91236",
            "closing_trade_id": "125",
            "opening_trade_id": "126",
        },
        "complete",
    )
    with second_gets.port() as port:
        cold = PortfolioBudgetHostV1(
            root=root,
            private_rest_fetch=_fetch(uid=data["account"], positions=(second_gets.position(),)),
            repository_sha=repository_sha,
            session_id="booked-return-fresh-process",
            expected_account_identity=data["account"],
            clock=second_gets.clock.timestamp,
            reconciliation_transport=port,
        )
        try:
            returned = recover_submitted_net_reversal_v1(
                lane_pair=pairs["LANE_1"], get_budget_host=lambda: cold, proof_root=proof_root
            )
            assert returned.reconciliation_blocker is None, returned
            prior, latest = cold.owner.risk_snapshot_v1()["state"]["live_net_reversal_bookings"][
                rid
            ]
            assert prior == row
            assert latest["booking_digest"] == returned.booking_digest
            assert latest["previous_episode_id"] == envelope.envelope_digest
            assert latest["envelope_digest"] == next_order.envelope_digest
            assert latest["reservation_id"] == rid and latest["slot_id"] == "LANE_1"
            assert Decimal(latest["position_contracts"]) == next_reversal.target_contracts > 0
            assert Decimal(latest["settlement_native"]) == Decimal("0.15")
            basis = cold.owner.live_reversal_slot_basis_v1(
                slot_id="LANE_1", reservation_id=rid, bound=bound
            )
            assert basis.booked_net_usdc == sum(
                (Decimal(booking["net_result_usdc"]) for booking in (prior, latest)),
                Decimal(0),
            )
            assert basis.latest_booking_digest == latest["booking_digest"]
            get_count = len(second_gets.calls)
            assert get_count > 0
            assert (
                recover_submitted_net_reversal_v1(
                    lane_pair=pairs["LANE_1"], get_budget_host=lambda: cold, proof_root=proof_root
                )
                == returned
            )
            assert len(second_gets.calls) == get_count
        finally:
            cold.close()


def _assert_n1_continuation_v2(
    root, monkeypatch, data, bound, closes, first_authorization, signer, *, crash, end_budget
):
    from src.ops import n1_occupied_net_reversal_host_v2 as continuation
    from src.ops import n1_post_authority_startup_v1
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_governed_continuous_cycle_orchestrator_v1 as s6,
        current_productive_persistent_natural_enter_convergence_v1 as convergence,
        external_effect_permit_durable_consume_v1 as send_receipt,
    )
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import startup_binding_v1
    from tests.ops.test_bounded_multislot_connected_cycle_v1 import ports
    from tests.ops.test_bounded_slot_connected_roundtrip_v1 import market
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _FakeKeychainBackend,
        _clean_post_integrity,
    )
    from tests.ops.test_current_productive_persistent_natural_enter_policy_governed_live_c1_v1 import (
        _f1_m9_evaluator_factory,
    )
    from tests.ops.test_current_productive_shared_post_owner_authority_v1 import _claim_rows

    first = SignedNetReversalGetFixture(data, "complete")
    fixtures = [first]
    orders = []
    runs = []
    root_v2 = root / "continuous-net-reversal"
    manifest = json.loads(_write_host_manifest(root, data, "v2").read_bytes())
    runtime_config = manifest["runtime_request_config"]

    class ReplayDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixtures[-1].clock if tz is None else fixtures[-1].clock.astimezone(tz)

    def signed_authorization(envelope):
        assert not orders
        grant = replace(
            first_authorization.grant,
            grant_id="automatic-return",
            envelope_digest=envelope.envelope_digest,
        )
        orders.append(envelope)
        return replace(
            first_authorization,
            grant=replace(grant, signature=signer.sign(grant.signing_bytes_v1()).signature),
        )

    class OfflineOpener:
        def open(self, request, timeout):
            assert len(fixtures) == 1
            payload = json.loads(request.data)
            envelope = orders[0]
            assert request.get_method() == "POST" and payload["side"] == "buy"
            assert payload["clOrdId"] == envelope.client_order_id
            assert payload["posSide"] == "net" and "reduceOnly" not in payload
            next_socket = fixtures[0].clock
            fixtures.append(
                SignedNetReversalGetFixture(
                    {
                        **data,
                        "envelope": envelope.to_runtime_json_v1(),
                        "socket_ms": int(next_socket.timestamp() * 1000),
                        "observed_at": (next_socket + timedelta(seconds=1)).isoformat(),
                        "closing_size": str(abs(Decimal(first.position()["pos"]))),
                        "old_position_id": first.position()["posId"],
                        "old_position_fee": first.position()["fee"],
                        "old_created_ms": first.position()["cTime"],
                        "position_id": "8924",
                        "venue_order_id": "91236",
                        "closing_trade_id": "125",
                        "opening_trade_id": "126",
                    },
                    "complete",
                )
            )
            raise TimeoutError("second simulated POST")

    def factory(attempt, evidence):
        prepared = startup_factory_v1.prepare_occupied_n1_request_v1(
            attempt_index=attempt, evidence_root=evidence, runtime_config=runtime_config
        )
        active = fixtures[-1]
        now = active.clock.timestamp()
        cursor = Path(runtime_config["roots"]["lane_state_root"]) / "LANE_1"
        core = restore_layered_core_episode_v1(cursor, expected_instrument_id=bound.instrument_id)
        mark = core.running_reference.reference_price_r_t
        if active is first:
            mark += 1.5 * core.scope.d_t
        inputs = market({"LANE_1": bound}, closes, now - 1, f"v2-{attempt}", root / "v2-g17")
        source = s6.ScriptedContinuousObservationSourceV1(
            [
                s6.InjectedContinuousObservationV1(
                    candles_payload=inputs["candles_payload_by_lane"]["LANE_1"],
                    occupancy_payloads={},
                    mark_price_payload={
                        "code": "0",
                        "data": [
                            {
                                "instId": bound.venue_native_id,
                                "markPx": str(mark),
                                "idxPx": str(mark * 0.995),
                                "ts": str(int((now - 0.125) * 1000)),
                            }
                        ],
                    },
                    mark_acquired_at_utc=active.clock.isoformat(),
                )
            ]
        )
        if end_budget and active is not first:
            source.poll = lambda: pytest.fail("mark polling exceeded the registered cycle budget")

        @contextmanager
        def open_ports(_):
            with active.port() as transport:
                yield {
                    "pretrade_transport": transport,
                    "private_rest_fetch": _fetch(
                        uid=data["account"], positions=(active.position(),)
                    ),
                    "public_rest_fetch": lambda *_args, **_kwargs: pytest.fail(
                        "unexpected public GET"
                    ),
                    "observation_source": source,
                    "g17_producers": inputs["g17_typed_vol_producers"],
                    "f1_m9_cycle_evaluator": _f1_m9_evaluator_factory(root),
                }

        return n1_post_authority_startup_v1.bind_occupied_n1_post_authority_v1(
            replace(prepared, open_ports=open_ports),
            authority=first_authorization.authority,
            port=supervisor.OccupiedNetReversalPostPortV1(
                ready_authorization=signed_authorization,
                k1_backend=_FakeKeychainBackend(),
                opener_factory=OfflineOpener,
                execution_integrity_backend=_clean_post_integrity(),
            ),
        )

    original_init = PortfolioBudgetHostV1.__init__

    def init_host(self, **kwargs):
        original_init(self, **{**kwargs, "clock": fixtures[-1].clock.timestamp})

    def startup(**kwargs):
        collect_host_account_observation_v1(
            private_rest_fetch=kwargs["private_rest_fetch"],
            instrument_ids_by_native_id={bound.venue_native_id: bound.instrument_id},
            session_id=kwargs["session_id"],
            clock=fixtures[-1].clock.timestamp,
            expected_account=data["account"],
        )
        return SimpleNamespace(
            handoff=SimpleNamespace(bound_instrument=bound, selection_id=bound.selection_id)
        )

    def pretrade(**kwargs):
        epoch = kwargs["decision_epoch"]
        inputs = ports(bound, epoch, kwargs["pretrade_cycle_id"], account=data["account"])
        limits = inputs.venue_quantity_limits
        limits = replace(
            limits,
            public_source=replace(limits.public_source, acquired_at_utc=epoch),
            private_source=replace(limits.private_source, acquired_at_utc=epoch),
        )
        return replace(
            inputs,
            acquisition_decision_id=limits.acquisition_decision_id,
            venue_quantity_limits=replace(limits, integrity_digest=limits.digest_v1()),
        )

    class InterruptedAfterSend(BaseException):
        pass

    def observe(**kwargs):
        result = supervisor.run_n1_standing_pre_external_supervisor_v1(**kwargs)
        runs.append(result)
        if crash and result.trace.post_count:
            raise InterruptedAfterSend
        return result

    local_go = {
        **owner_go.load_bounded_continuous_run_owner_go_decision_v1(),
        "baseline_origin_main_sha": data["revision"],
    }
    monkeypatch.setattr(
        startup_factory_v1, "assert_current_productive_29p_execution_identity_v1", lambda **_: None
    )
    monkeypatch.setattr(
        owner_go, "load_bounded_continuous_run_owner_go_decision_v1", lambda: local_go
    )
    monkeypatch.setattr(
        supervisor,
        "_run_unified_recovery_v1",
        lambda **_: SimpleNamespace(
            ok=True,
            runtime_owner_recovery_complete=True,
            steps_completed=(),
            evidence_scope="OFFLINE_FIXTURE",
            pending_runtime_steps=(),
        ),
    )
    monkeypatch.setattr(supervisor, "_refresh_public_supply_v1", lambda **_: 0)
    monkeypatch.setattr(supervisor, "_refresh_pretrade_truth_v1", lambda **_: "OFFLINE_FIXTURE")
    monkeypatch.setattr(supervisor, "public_instrument_ref_for_binding_v1", lambda _: None)
    monkeypatch.setattr(startup_binding_v1, "acquire_account_bound_n1_startup_v1", startup)
    monkeypatch.setattr(convergence, "datetime", ReplayDateTime)
    monkeypatch.setattr(
        convergence, "resolve_live_29p_injected_for_productive_s5_cycle_v1", pretrade
    )
    monkeypatch.setattr(s6.time, "time", lambda: fixtures[-1].clock.timestamp())
    monkeypatch.setattr(PortfolioBudgetHostV1, "__init__", init_host)
    monkeypatch.setattr(continuation, "run_n1_standing_pre_external_supervisor_v1", observe)
    monkeypatch.setattr(
        send_receipt,
        "_utc_now_iso_v1",
        lambda: fixtures[-1].clock.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    )
    bounds = unattended_v1.UnattendedHostBoundsV1(
        host_id="offline-net-reversal-continuation",
        repository_sha=data["revision"],
        runtime_config_digest=unattended_v1.unattended_request_digest_v1(
            factory(1, root_v2 / "attempts" / "1")
        ),
        expires_at_unix=first.clock.timestamp() + 100,
        max_total_cycles=1 if end_budget else 2,
        max_total_seconds=90,
        wait_interval_seconds=1,
    )
    args = dict(
        bounds=bounds,
        state_root=root_v2,
        request_factory=factory,
        clock=lambda: fixtures[-1].clock.timestamp(),
    )
    scope_root = Path(runtime_config["roots"]["lane_state_root"]) / "LANE_1"
    cursor = scope_root / s6.CURSOR_FILENAME
    original_cursor = cursor.read_bytes()
    budget_db = Path(runtime_config["roots"]["private_store_root"]) / (
        "portfolio_budget_host_v1/owner/reservations.sqlite3"
    )
    original_inode = budget_db.stat().st_ino
    if crash:
        (root / "v2-test-registration.json").write_text(
            json.dumps(
                {
                    "runtime_config_digest": factory(
                        1, root_v2 / "attempts" / "1"
                    ).runtime_config_digest,
                    "runtime_config": runtime_config,
                    "state_root": str(root_v2),
                    "bounds": asdict(bounds),
                }
            )
        )
        _kill_booking_process(root, runtime_config["roots"]["f1_m9_ledger_root"], v2=True)
        interrupted = json.loads((root_v2 / "occupied_host_state_v2.json").read_bytes())
        assert interrupted["status"] == "RUNNING" and interrupted["attempt"] == 1
        assert interrupted["awaiting"]["envelope_digest"] == data["envelope"]["envelope_digest"]
        assert not (root_v2 / "attempts" / "1" / s6.LEDGER_FILENAME).exists()
        with pytest.raises(InterruptedAfterSend):
            continuation.run_occupied_n1_net_reversal_host_v2(**args)
        after_send = json.loads((root_v2 / "occupied_host_state_v2.json").read_bytes())
        assert after_send["status"] == "RUNNING" and after_send["attempt"] == 2
        assert after_send["cycles_used"] == 0 and len(orders) == 1
    elif not end_budget:
        first.scenario = "partial"
        waiting = continuation.run_occupied_n1_net_reversal_host_v2(**args)
        assert waiting["status"] == "AWAITING_BOOKING" and waiting["cycles_used"] == 0
        assert waiting["awaiting"]["envelope_digest"] == data["envelope"]["envelope_digest"]
        assert not orders and runs.pop().policy_result is None
        first.scenario = "complete"
    state = continuation.run_occupied_n1_net_reversal_host_v2(**args)
    assert state["status"] == ("BOUNDS_EXHAUSTED" if end_budget else "COMPLETED"), (
        state,
        [run.trace.extra for run in runs],
    )
    assert (
        state["cycles_used"] == bounds.max_total_cycles
        and state["attempt"] == (2 if end_budget else 3)
        and state["awaiting"] is None
    )
    assert state["interrupted_retries"] == int(crash)
    if crash:
        assert not first.calls
        assert state["started_at"] == interrupted["started_at"]
    assert len(orders) == 1
    first_book = runs[0].trace.extra["net_reversal_readback"]
    second_book = state["last_booking"]
    assert first_book["booking_digest"] != second_book["booking_digest"]
    assert second_book["envelope_digest"] == orders[0].envelope_digest
    assert first_book["reservation_id"] == second_book["reservation_id"]
    assert second_book["episode_id"] == first_book["envelope_digest"]
    assert [run.trace.post_count for run in runs] == [1, 0]
    assert cursor.read_bytes() == original_cursor
    assert budget_db.stat().st_ino == original_inode
    assert _claim_rows(first_authorization) == [
        (first_authorization.grant.grant_id, 1),
        ("automatic-return", 1),
    ]
    assert continuation.run_occupied_n1_net_reversal_host_v2(**args) == state
    assert len(runs) == 2


def _assert_follow_on_net_reversal_dispatch_v1(
    *, lane_pair, recovery, entry, first_authorization, signer
):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
        read_retained_net_reversal_post_context_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        execute_authenticated_net_reversal_post_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        external_effect_permit_durable_consume_v1 as send_receipt,
    )
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        _FakeKeychainBackend,
        _clean_post_integrity,
    )
    from tests.ops.test_current_productive_shared_post_owner_authority_v1 import _claim_rows

    context = read_retained_net_reversal_post_context_v1(
        lane_pair=lane_pair, recovery=recovery, authenticated_entry=entry
    )
    reversal, envelope = context.reversal, context.envelope
    assert reversal.episode.episode_id == first_authorization.grant.envelope_digest
    original_owner = recovery.host.owner
    before = original_owner.risk_snapshot_v1()
    first_grant = first_authorization.grant
    second_grant = replace(
        first_grant, grant_id="second-reversal", envelope_digest=envelope.envelope_digest
    )
    authorization = replace(
        first_authorization,
        grant=replace(
            second_grant, signature=signer.sign(second_grant.signing_bytes_v1()).signature
        ),
    )
    requests = []

    class OfflineOpener:
        def open(self, request, timeout):
            assert not requests and request.get_method() == "POST"
            payload = json.loads(request.data)
            assert request.full_url == "https://eea.okx.com/api/v5/trade/order"
            assert payload["instId"] == lane_pair[1].venue_native_id
            assert payload["side"] == "buy" and payload["posSide"] == "net"
            assert "reduceOnly" not in payload
            assert Decimal(payload["sz"]) == reversal.target_contracts - reversal.current_contracts
            persisted = load_external_effect_durable_consume_v1(store_root=context.store_root_v1())
            assert persisted["record"]["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
            assert persisted["record"]["envelope_digest"] == envelope.envelope_digest
            assert original_owner.risk_snapshot_v1() == before
            requests.append(payload)
            raise TimeoutError("simulated timeout of the second net order")

    post_inputs = {
        "lane_pair": lane_pair,
        "recovery": recovery,
        "authenticated_entry": entry,
        "authorization": authorization,
        "baseline_origin_main_sha": EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        "perform_real_venue_post": True,
        "k1_backend": _FakeKeychainBackend(),
        "execution_integrity_backend": _clean_post_integrity(),
        "opener_factory": OfflineOpener,
    }
    # Replay timestamps advance past the previously confirmed position update.
    with patch.object(
        send_receipt,
        "_utc_now_iso_v1",
        lambda: datetime.fromtimestamp(recovery.host.clock(), timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ),
    ):
        result = execute_authenticated_net_reversal_post_v1(**post_inputs)
    assert result.post_attempted and result.unknown_outcome and not result.venue_live_contact
    assert len(requests) == 1
    assert _claim_rows(authorization) == [(first_grant.grant_id, 1), ("second-reversal", 1)]
    with pytest.raises(ValueError, match="POST_AUTHORITY_REVERSAL_ALREADY_CONSUMED"):
        execute_authenticated_net_reversal_post_v1(**post_inputs)
    assert original_owner.risk_snapshot_v1() == before
    return envelope, load_external_effect_durable_consume_v1(store_root=context.store_root_v1())[
        "record"
    ]


def _assert_exceptional_close_v1(pairs, inputs, host, rid, row, side_input):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_master_v2_runtime_cycle_v1 as core,
        current_productive_persistent_natural_enter_convergence_v1 as n1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_position_close_v1 import (
        CurrentPostPositionCloseError,
        inspect_current_post_position_close_v1,
    )

    mk = dict(inputs)
    candles = mk.pop("candles_payload")
    entry = mk.pop("authenticated_entry")
    for key in (
        "host_budget_recovery",
        "portfolio_budget_owner",
        "occupied_scope_mark_lane_id",
        "live_29p_injected_by_lane",
    ):
        mk.pop(key)

    def market_observation(**kwargs):
        return {**mk, "cycle_id_prefix": kwargs["cycle_id_prefix"]}

    resolver = core.resolve_durable_kill_switch_for_mv2_host_v1
    slot, bound = pairs["LANE_1"]
    root = Path(slot.lane_state_root)
    with (
        patch.object(
            core,
            "resolve_durable_kill_switch_for_mv2_host_v1",
            lambda **kw: resolver(**{**kw, "explicit_active": True}),
        ),
        patch.object(n1, "_market_kwargs_from_observation_v1", market_observation),
        patch.object(
            n1, "resolve_live_29p_injected_for_productive_s5_cycle_v1", return_value=side_input
        ),
    ):
        reads = n1._OccupiedMarkReadsV1(
            host=host,
            bound=bound,
            proof_root=entry.proof_root,
            transport=None,
            productivity_root=None,
        )
        try:
            reads.before_poll()
            runner = n1.make_n1_occupied_lane_s5_runner_v1(
                composed_pairs=pairs,
                g17_producers=mk["g17_typed_vol_producers"],
                cycle_id_prefix_base="booked-net-exception",
                portfolio_budget_host=host,
                occupied_mark_proof_root=entry.proof_root,
                occupied_mark_reads=reads,
            )
            result = runner(
                authorization=SimpleNamespace(native_id=bound.venue_native_id),
                origin_main_sha=host.repository_sha,
                cursor_store_root=root,
                lock_root=root.parent / "exception-lock",
                evidence_root=root.parent / "exception-evidence",
                candles_payload=candles,
                mark_price_payload={},
            )
        finally:
            reads.close()
    context = result.position_close_post_context
    assert context is not None, result
    binding = context.execution.exceptional_close
    envelope = context.execution.envelope
    assert context.execution.l10_close is None
    assert (binding.episode.lane_id, binding.episode.position_side) == ("LANE_1", "short")
    assert binding.episode.episode_id == row["envelope_digest"]
    assert binding.reservation_id == rid and binding.booking_digest == row["booking_digest"]
    assert envelope.reduce_only and envelope.side == "buy" and envelope.quantity == "1"
    assert result.post_count == 0 and result.permit_created is False
    assert result.disposition == "PRE_EXTERNAL_EFFECT"
    assert result.reason_code == "ACTUAL_EXCEPTIONAL_CLOSE_NOT_ADMITTED"
    inspect_current_post_position_close_v1(
        context, envelope=envelope, stage="OFFLINE_CLOSE_SENDER", require_post_go=False
    )
    with pytest.raises(
        CurrentPostPositionCloseError, match="ACTUAL_EXCEPTIONAL_CLOSE_NOT_ADMITTED"
    ):
        inspect_current_post_position_close_v1(context, envelope=envelope, stage="BEFORE_POST")
    foreign_entry = replace(
        context.authenticated_entry,
        proof=replace(context.authenticated_entry.proof, reservation_id="foreign-reservation"),
    )
    with pytest.raises(
        CurrentPostPositionCloseError, match="AUTHENTICATED_CLOSE_ACCOUNT_SCOPE_UNPROVEN"
    ):
        inspect_current_post_position_close_v1(
            replace(context, authenticated_entry=foreign_entry),
            envelope=envelope,
            stage="OFFLINE_CLOSE_SENDER",
            require_post_go=False,
        )
    with pytest.raises(
        CurrentPostPositionCloseError, match="EXCEPTIONAL_CLOSE_ORIGINAL_PLAN_ROOT_UNPROVEN"
    ):
        inspect_current_post_position_close_v1(
            replace(context, evidence_root=context.evidence_root.parent),
            envelope=envelope,
            stage="OFFLINE_CLOSE_SENDER",
            require_post_go=False,
        )
    assert host.owner.read_authenticated_net_reversal_v1(rid) == row
