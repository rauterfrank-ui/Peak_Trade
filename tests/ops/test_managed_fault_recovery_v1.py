"""Independent original feed and financial observations drive the managed Safety gate."""

from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256

import pytest
from nacl.signing import SigningKey

from src.ops.filegate_recovery_authority_v1 import (
    FilegateAuthorityError,
    FilegateRecoveryScopeV1,
    attest_filegate_owner_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    cursor_last_accepted_c1_venue_event_time_v1,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_governed_continuous_cycle_orchestrator_v1 as s6,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    build_s8_occupied_lane_pairs_v1,
    make_n1_occupied_lane_s5_runner_v1,
)
from src.ops.gates.risk_gate import RiskContext, RiskLimits, kill_switch_should_block_trading
from src.ops.managed_account_recovery_v1 import attest_managed_stopped_account_v1
from src.ops.managed_authorization_recovery_v1 import attest_managed_replacement_authority_v1
from src.ops.managed_fault_recovery_v1 import (
    ManagedFaultRecoveryV1,
    attest_managed_filegate_integrity_v1,
    build_standing_managed_fault_recovery_v1,
    publish_managed_owner_proof_v1,
)
from src.ops.managed_filegate_v1 import ROOT_ENV, ManagedFilegateV1
from src.ops.managed_public_feed_recovery_v1 import (
    ManagedPublicFeedRecoveryV1,
    attest_managed_public_feed_scope_v1,
)
from src.ops.managed_risk_recovery_v1 import attest_managed_risk_recovery_v1
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import (
    UnattendedHostBoundsV1,
    run_unattended_n1_host_v1,
)
from src.ops.offline_public_feed_recovery_v1 import OfflinePublicFeedRecoveryError
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    FUTURES_INVENTORY_REQUEST_COUNT,
)
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import InstrumentRefV1, fact_digest
from tests.ops.test_current_futures_simulated_dispatch_v1 import seeded
from tests.ops.test_current_scope_public_mark_source_v1 import push
from tests.ops.test_current_usdc_xperp_financial_admission_v1 import join, prepare, xperp_bound
from tests.ops.test_offline_public_feed_account_reconciliation_v1 import (
    _inventory_venue,
    _open_budget_host,
)
from tests.ops.test_offline_public_feed_recovery_v1 import FeedFixture
from tests.ops.test_offline_public_feed_restart_v1 import scenario
from tests.ops.test_canonical_durable_authorization_lifecycle_and_revocation_v1 import (
    _write_v2,
    issue_token_exposure_revocation_v1,
)

import json


def _proof(*, role, stop, now, key, digest="a" * 64, cause=None):
    return attest_filegate_owner_evidence_v1(
        role=role,
        cause=cause,
        stop=stop,
        evidence_sha256=digest,
        observed_at=now,
        expires_at=now + 4,
        key=key,
    )


def _provision(tmp_path, monkeypatch, scope, clock, causes, *, cause_keys=None):
    paths = {}
    for label in ("managed-state", "independent", "diagnostics"):
        paths[label] = tmp_path / label
        paths[label].mkdir(mode=0o700)
    writer = ManagedFilegateV1(
        state_path=paths["managed-state"] / "state.json",
        root=paths["independent"],
        clock=clock,
    )
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(writer.state_path))
    monkeypatch.setenv(ROOT_ENV, str(writer.root))
    issuer = SigningKey.generate()
    keys = {role: SigningKey.generate() for role in ("CAUSE", "ACCOUNT", "HOST")}
    cause_keys = cause_keys or {}
    stop = writer.provision_v1(
        scope=scope,
        issuer_public_key=bytes(issuer.verify_key),
        owner_public_keys={role: bytes(key.verify_key) for role, key in keys.items()},
        recoverable_causes=causes | {"R03"},
        cause_public_keys={cause: bytes(key.verify_key) for cause, key in cause_keys.items()},
    )
    # Test-only readiness grants establish the starting managed ACTIVE state.
    evidence = {
        role: _proof(role=role, stop=stop, now=clock(), key=key) for role, key in keys.items()
    }
    if "R03" in cause_keys:
        with pytest.raises(FilegateAuthorityError, match="CAUSE_EVIDENCE_COVERAGE_UNPROVEN"):
            writer.issue_release_v1(evidence=evidence, issuer_key=issuer)
        evidence["CAUSE"] = {
            "R03": _proof(role="CAUSE", stop=stop, now=clock(), key=cause_keys["R03"], cause="R03")
        }
    release = writer.issue_release_v1(evidence=evidence, issuer_key=issuer)
    writer.release_v1(release=release, evidence=evidence)
    return writer, issuer, keys, paths["diagnostics"]


@pytest.mark.parametrize("scenario", [False], indirect=True)
def test_managed_feed_and_original_account_drive_safety_release(scenario, tmp_path, monkeypatch):
    feed, common = scenario["feed"], scenario["common"]
    host, bound = common["host"], common["bound"]
    scope = FilegateRecoveryScopeV1(
        host.expected_account_identity,
        host.execution_environment,
        str(host.root),
        (bound.venue_native_id,),
        "c" * 64,
    )

    def clock():
        return feed.now.timestamp()

    writer, issuer, keys, journal_root = _provision(tmp_path, monkeypatch, scope, clock, {"R01"})
    writer.kill_v1(cause="R01", reason="native public feed lost")
    feed_owner = ManagedPublicFeedRecoveryV1(
        writer=writer,
        runtime=feed.runtime,
        session_id=feed.incident.session_id,
        journal_root=journal_root,
        clock=lambda: feed.now,
    )

    def attest_host(stop):
        raw = scenario["cursor_path"].read_bytes()
        assert raw == scenario["initial_cursor"]
        assert cursor_last_accepted_c1_venue_event_time_v1(json.loads(raw)) == (
            common["authorization"].expected_cursor_floor
        )
        return _proof(
            role="HOST", stop=stop, now=clock(), key=keys["HOST"], digest=sha256(raw).hexdigest()
        )

    mark = {}

    def attest_feed(stop):
        proof = feed_owner.attest_v1(stop, key=keys["CAUSE"])
        mark.update(feed_owner.read_verified_repair_v1()["mark"])
        return proof

    coordinator = ManagedFaultRecoveryV1(
        writer=writer,
        issuer_key=issuer,
        interval_seconds=1,
        observations={
            "CAUSE": attest_feed,
            "ACCOUNT": lambda stop: attest_managed_stopped_account_v1(
                writer=writer,
                stop=stop,
                host=host,
                bindings={"LANE_1": bound},
                transport_scope=feed.incident.root,
                key=keys["ACCOUNT"],
            ),
            "HOST": attest_host,
        },
    )
    result = coordinator.poll_v1()
    assert result["status"] == "SAFETY_RELEASE_CONFIRMED", result
    assert feed.transport.state.reconnect_count == 1
    assert not kill_switch_should_block_trading()
    assert scenario["send"]["simulated_transport"].post_count == 0
    assert scenario["cursor_path"].read_bytes() == scenario["initial_cursor"]
    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=feed.incident.root / "lanes",
        bound=bound,
    )

    def require_release(_):
        assert writer.read_v1()["filegate_release_sha256"] == result["release_sha256"]

    original = s6.run_current_productive_governed_continuous_cycle_run_v1(
        authorization=common["authorization"],
        origin_main_sha=host.repository_sha,
        cursor_store_root=scenario["cursor_path"].parent,
        lock_root=tmp_path / "recovered-host-lock",
        evidence_root=tmp_path / "recovered-host",
        observation_source=s6.ScriptedContinuousObservationSourceV1(
            [replace(scenario["observation"], mark_acquired_at_utc=mark["captured_at"])]
        ),
        s5_runner=make_n1_occupied_lane_s5_runner_v1(
            composed_pairs=pairs,
            g17_producers=scenario["producers"],
            cycle_id_prefix_base="managed-fault-recovery",
        ),
        iteration_authority_gate_v1=require_release,
    )
    assert original.disposition == s6.DISPOSITION_MAX_CYCLES, original.reason_code
    after = json.loads(scenario["cursor_path"].read_bytes())
    assert (
        cursor_last_accepted_c1_venue_event_time_v1(after)
        == common["authorization"].expected_cursor_floor + 60
    )
    assert scenario["send"]["simulated_transport"].post_count == 0


@pytest.mark.parametrize("fault", [None, "new-kill", "expired-first-mark", "missing-account-scope"])
def test_managed_feed_scope_requires_every_original_futures_mark(tmp_path, monkeypatch, fault):
    second_bound = xperp_bound("ETH")
    old_host, args, _ = prepare(tmp_path, monkeypatch, extra_bindings={"LANE_2": second_bound})
    bindings = {"LANE_1": args["bound_instrument"], "LANE_2": second_bound}
    started_at = datetime.fromtimestamp(old_host.clock(), tz=timezone.utc)
    original_entry = join(**args)
    assert original_entry.status == "PASS", original_entry.reason_codes
    original_commitments = old_host.owner.local_commitment_readback_v1().generation_digest
    old_host.close()
    feeds = {}
    for lane, bound in bindings.items():
        native = bound.venue_native_id
        root = tmp_path / lane
        root.mkdir(mode=0o700)
        feeds[native] = FeedFixture(
            root,
            monkeypatch,
            instrument=InstrumentRefV1(
                bound.instrument_id,
                native,
                "okx_eea",
                "FUTURES",
                "USD",
                bound.selection_integrity_digest,
            ),
            session_id=f"futures-{lane}",
            started_at=started_at,
        )
    scope = FilegateRecoveryScopeV1(
        old_host.expected_account_identity,
        old_host.execution_environment,
        str(old_host.root),
        tuple(feeds),
        "c" * 64,
    )

    def clock():
        return max(feed.now.timestamp() for feed in feeds.values())

    writer, issuer, keys, journal_root = _provision(tmp_path, monkeypatch, scope, clock, {"R01"})
    stop = writer.kill_v1(cause="R01", reason="managed futures feed scope lost")
    owners = tuple(
        ManagedPublicFeedRecoveryV1(
            writer=writer,
            runtime=feed.runtime,
            session_id=feed.incident.session_id,
            journal_root=journal_root,
            clock=lambda feed=feed: feed.now,
        )
        for feed in feeds.values()
    )
    with pytest.raises(OfflinePublicFeedRecoveryError, match="CAUSE_COVERAGE_UNPROVEN"):
        owners[0].attest_v1(stop, key=keys["CAUSE"])
    assert all(feed.transport.state.reconnect_count == 0 for feed in feeds.values())

    first, second = feeds.values()
    first.frames = [
        push(
            native=first.incident.instrument.venue_native_id,
            timestamp=first.event_ms(0.25),
            markPx="101",
        )
    ]
    second.frames = []
    proofs = {}

    def attest_scope(current):
        proof = attest_managed_public_feed_scope_v1(
            stop=current, recoveries=owners[::-1], key=keys["CAUSE"]
        )
        proofs.update(proof)
        return proof

    venue = _inventory_venue(old_host.account)

    def attest_account(current):
        with _open_budget_host(
            old_host,
            max(feeds.values(), key=lambda feed: feed.now),
            venue,
            monkeypatch,
            reads=FUTURES_INVENTORY_REQUEST_COUNT,
        ) as host:
            proof = attest_managed_stopped_account_v1(
                writer=writer,
                stop=current,
                host=host,
                bindings={"LANE_1": bindings["LANE_1"]}
                if fault == "missing-account-scope"
                else bindings,
                transport_scope=tmp_path.resolve(),
                key=keys["ACCOUNT"],
            )
            assert host.owner.budget_state_v1().recovery_required
            assert (
                host.owner.local_commitment_readback_v1().generation_digest == original_commitments
            )
            return proof

    service = ManagedFaultRecoveryV1(
        writer=writer,
        issuer_key=issuer,
        interval_seconds=1,
        observations={
            "CAUSE": attest_scope,
            "ACCOUNT": attest_account,
            "HOST": lambda current: _proof(
                role="HOST", stop=current, now=clock(), key=keys["HOST"]
            ),
        },
    )
    blocked = service.poll_v1()
    assert "CAUSE" in blocked["missing_proofs"] and kill_switch_should_block_trading()
    assert not proofs
    second.frames = [
        push(
            native=second.incident.instrument.venue_native_id,
            timestamp=second.event_ms(),
            markPx="201",
        )
    ]
    if fault in {"new-kill", "expired-first-mark"}:
        original = second.runtime.run_observation_cycle

        def observe_then_fault(**kwargs):
            result = original(**kwargs)
            if fault == "new-kill":
                writer.kill_v1(cause="R09", reason="fixture kill during final feed read")
            else:
                first.advance(PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS + 1)
            return result

        monkeypatch.setattr(second.runtime, "run_observation_cycle", observe_then_fault)
    result = service.poll_v1()
    if fault == "new-kill":
        assert result["status"] == "STOP_SUPERSEDED"
        assert writer.inspect_stop_v1()["causes"] == ["R01", "R09"]
        assert not proofs and kill_switch_should_block_trading()
    elif fault == "expired-first-mark":
        assert result["status"] == "BLOCKED_OBSERVING"
        assert result["missing_proofs"] == ["CAUSE"]
        assert not proofs and kill_switch_should_block_trading()
    elif fault == "missing-account-scope":
        assert result["status"] == "BLOCKED_OBSERVING"
        assert result["owner_blockers"] == {"ACCOUNT": "FAULT_ACCOUNT_ORIGINAL_SCOPE_CHANGED"}
        assert proofs and kill_switch_should_block_trading()
    else:
        assert result["status"] == "SAFETY_RELEASE_CONFIRMED", result
        assert proofs["body"]["expires_at"] == (
            int(first.frames[0]["data"][0]["ts"]) / 1000 + PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS
        )
        assert not kill_switch_should_block_trading()
        assert len(venue.requests) == 2 * FUTURES_INVENTORY_REQUEST_COUNT
    assert all(feed.transport.state.reconnect_count == 1 for feed in feeds.values())


def test_loss_and_emergency_hold_recovery_until_original_risk_rule_allows(tmp_path, monkeypatch):
    def clock():
        return 1000

    scope = FilegateRecoveryScopeV1("account", "SHADOW", "host", ("instrument",), "c" * 64)
    writer, issuer, keys, _ = _provision(tmp_path, monkeypatch, scope, clock, {"R05"})
    stop = writer.kill_v1(cause="R05", reason="session loss")
    limits = RiskLimits(max_session_loss_usd=10)
    limit_digest = fact_digest(asdict(limits))
    capital = [-11.0]

    def risk(current_stop):
        return attest_managed_risk_recovery_v1(
            stop=current_stop,
            limits=limits,
            context=RiskContext(clock(), 0, capital[0], 0, 1, 1),
            original_policy_sha256=limit_digest,
            original_observation_sha256="d" * 64,
            expires_at=clock() + 4,
            key=keys["CAUSE"],
        )

    coordinator = ManagedFaultRecoveryV1(
        writer=writer,
        issuer_key=issuer,
        interval_seconds=1,
        observations={
            "CAUSE": risk,
            "ACCOUNT": lambda stop: _proof(
                role="ACCOUNT", stop=stop, now=clock(), key=keys["ACCOUNT"]
            ),
            "HOST": lambda stop: _proof(role="HOST", stop=stop, now=clock(), key=keys["HOST"]),
        },
    )
    assert coordinator.poll_v1()["missing_proofs"] == ["CAUSE"]
    assert writer.inspect_stop_v1() == stop and kill_switch_should_block_trading()
    capital[0] = -9.0
    assert coordinator.poll_v1()["status"] == "SAFETY_RELEASE_CONFIRMED"
    writer.emergency_v1("explicit emergency")
    assert coordinator.poll_v1()["status"] == "BLOCKED_OBSERVING"
    assert kill_switch_should_block_trading()


def test_replacement_authority_uses_original_durable_revocation_registry(tmp_path):
    path, _, payload = _write_v2(tmp_path)
    stop = {"causes": ["R06"], "killed_at": payload["created_at"] - 1}
    arguments = dict(
        stop=stop,
        artifact_path=path,
        evidence_root=tmp_path,
        prior_authorization_id="original-revoked",
        repository_sha=payload["repository_sha"],
        runbook_sha256=payload["runbook_sha256"],
        preregistration_id=payload["preregistration_id"],
        preregistration_digest=payload["preregistration_digest"],
        original_session_config_digest=payload["session_config_digest"],
        now=payload["created_at"] + 1,
        key=SigningKey.generate(),
    )
    receipt = attest_managed_replacement_authority_v1(**arguments)
    assert receipt["body"]["evidence_sha256"] == payload["integrity_digest"]
    with pytest.raises(FilegateAuthorityError, match="REPLACEMENT_AUTHORIZATION_UNPROVEN"):
        attest_managed_replacement_authority_v1(
            **{**arguments, "prior_authorization_id": payload["authorization_id"]}
        )
    revocation = issue_token_exposure_revocation_v1(
        evidence_root=tmp_path,
        authorization_id=payload["authorization_id"],
        authorization_digest=payload["integrity_digest"],
        preregistration_id=payload["preregistration_id"],
        preregistration_digest=payload["preregistration_digest"],
        repository_sha=payload["repository_sha"],
        previous_state=payload["state"],
        capability=payload["capability"],
    )
    assert revocation.ok
    with pytest.raises(FilegateAuthorityError, match="REPLACEMENT_AUTHORIZATION_UNPROVEN"):
        attest_managed_replacement_authority_v1(**arguments)


def test_host_persists_observation_under_stop_without_opening_trading_ports(tmp_path, monkeypatch):
    import time

    scope = FilegateRecoveryScopeV1("account", "SHADOW", "host", ("instrument",), "c" * 64)
    writer, issuer, keys, proof_root = _provision(tmp_path, monkeypatch, scope, time.time, {"R01"})
    stop = writer.emergency_v1("explicit emergency")
    for role, key in keys.items():
        proof = _proof(role=role, stop=stop, now=time.time(), key=key)
        publish_managed_owner_proof_v1(root=proof_root, proof=proof)
    issuer_path = tmp_path / "test-issuer"
    issuer_path.write_bytes(bytes(issuer))
    issuer_path.chmod(0o600)
    state_root = tmp_path / "controller"
    config = {
        "proof_root": str(proof_root),
        "issuer_seed_path": str(issuer_path),
        "interval_seconds": 1,
    }
    bounds = UnattendedHostBoundsV1("host", "revision", "config", time.time() + 20, 1, 20, 1)

    def run(sleeper):
        return run_unattended_n1_host_v1(
            bounds=bounds,
            state_root=state_root,
            request_factory=lambda *_: pytest.fail("closed FILEGATE cannot open trading ports"),
            fault_recovery=build_standing_managed_fault_recovery_v1(
                state_root=state_root,
                runtime_config=config,
            ),
            sleeper=sleeper,
        )

    def interrupt(_):
        raise RuntimeError("controller interrupted")

    with pytest.raises(RuntimeError, match="controller interrupted"):
        run(interrupt)
    stored = json.loads((state_root / "host_restart_state_v1.json").read_bytes())
    assert stored["last_fault_observation"]["stop"] == stop
    assert stored["last_fault_observation"]["status"] == "BLOCKED_OBSERVING"
    resumed = run(lambda _: (state_root / "STOP").touch())
    assert resumed["status"] == "STOPPED"
    assert resumed["last_fault_observation"]["stop"] == stop
    assert resumed["attempts"] == 0
    assert kill_switch_should_block_trading()


def test_standing_recovery_requires_every_independent_cause_in_current_stop(tmp_path, monkeypatch):
    import time

    scope = FilegateRecoveryScopeV1("account", "SHADOW", "host", ("instrument",), "c" * 64)
    cause_keys = {cause: SigningKey.generate() for cause in ("R03", "R05")}
    writer, issuer, keys, proof_root = _provision(
        tmp_path, monkeypatch, scope, time.time, {"R05"}, cause_keys=cause_keys
    )
    writer.kill_v1(cause="R03", reason="FILEGATE state needed repair")
    stop = writer.kill_v1(cause="R05", reason="session loss")
    assert stop["causes"] == ["R03", "R05"]
    issuer_path = tmp_path / "test-issuer"
    issuer_path.write_bytes(bytes(issuer))
    issuer_path.chmod(0o600)
    service = build_standing_managed_fault_recovery_v1(
        state_root=tmp_path / "controller",
        runtime_config={
            "proof_root": str(proof_root),
            "issuer_seed_path": str(issuer_path),
            "interval_seconds": 1,
        },
    )

    def publish_other_owners(current_stop):
        for role in ("ACCOUNT", "HOST"):
            publish_managed_owner_proof_v1(
                root=proof_root,
                proof=_proof(role=role, stop=current_stop, now=time.time(), key=keys[role]),
            )

    def integrity(current_stop):
        return attest_managed_filegate_integrity_v1(
            writer=writer, stop=current_stop, expires_at=time.time() + 60, key=cause_keys["R03"]
        )

    def risk(current_stop, *, observed_at, expires_at):
        limits = RiskLimits(max_session_loss_usd=10)
        return attest_managed_risk_recovery_v1(
            stop=current_stop,
            limits=limits,
            context=RiskContext(observed_at, 0, -9, 0, 1, 1),
            original_policy_sha256=fact_digest(asdict(limits)),
            original_observation_sha256="d" * 64,
            expires_at=expires_at,
            key=cause_keys["R05"],
        )

    publish_other_owners(stop)
    publish_managed_owner_proof_v1(root=proof_root, proof=integrity(stop))
    assert service.poll_v1()["missing_proofs"] == ["CAUSE"]
    publish_managed_owner_proof_v1(
        root=proof_root,
        proof=_proof(role="CAUSE", stop=stop, now=time.time(), key=keys["CAUSE"], cause="R05"),
    )
    assert service.poll_v1()["status"] == "BLOCKED_OBSERVING"
    risk_proof = risk(stop, observed_at=stop["killed_at"], expires_at=time.time())
    publish_managed_owner_proof_v1(root=proof_root, proof=risk_proof)
    assert service.poll_v1()["status"] == "BLOCKED_OBSERVING"

    stop = writer.kill_v1(cause="R05", reason="new stop after risk observation")
    publish_other_owners(stop)
    publish_managed_owner_proof_v1(
        root=proof_root, proof=risk(stop, observed_at=time.time(), expires_at=time.time() + 60)
    )
    assert service.poll_v1()["missing_proofs"] == ["CAUSE"]
    assert kill_switch_should_block_trading()
    publish_managed_owner_proof_v1(root=proof_root, proof=integrity(stop))
    result = service.poll_v1()
    assert result["status"] == "SAFETY_RELEASE_CONFIRMED", result
    assert writer.read_v1()["filegate_release_sha256"] == result["release_sha256"]
    assert not kill_switch_should_block_trading()
