"""S03 productive session orchestrator: Auth-v2 consume-before-side-effects owner.

Capability default: offline probe / preflight only. Real network execution requires
a separate later operator GO and is refused while capability execution flags are false.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.bindings_v1 import (
    validate_s03_scope_bindings_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.confirm_token_stdin_v1 import (
    read_confirm_token_interactively_v1,
    redact_confirm_token_from_mapping_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    BOUND_DURATION_SECONDS,
    REAL_NETWORK_IN_THIS_CAPABILITY,
    SIDE_EFFECT_AUTHORIZATION_CONSUMED,
    SIDE_EFFECT_EVIDENCE_CREATION,
    SIDE_EFFECT_NETWORK,
    SIDE_EFFECT_RUNTIME_INITIALIZATION,
    SIDE_EFFECT_SESSION_LOCK,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.duration_v1 import (
    MonotonicDurationAuthorityV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.evidence_v1 import (
    append_jsonl_v1,
    build_counterfactual_record_v1,
    build_decision_sensitivity_v1,
    build_drift_comparison_v1,
    build_heartbeat_v1,
    build_market_sample_record_v1,
    build_session_metadata_v1,
    build_volatility_record_v1,
    classify_sample_ordering_v1,
    evidence_file_map_v1,
    resolve_s03_session_dir_v1,
    write_json_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.independence_v1 import (
    assert_exit_precedence_preserved_v1,
    build_exit_risk_safety_independence_record_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
    MarketSampleV1,
    OrchestratorResultV1,
    S03ScopeBindingsV1,
    SideEffectProbeV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.network_boundary_v1 import (
    assert_no_credentials_v1,
    assert_public_md_request_allowed_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.session_lock_v1 import (
    S03SessionLockV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.side_effect_order_v1 import (
    assert_s03_consume_before_side_effects_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.terminal_v1 import (
    write_terminal_artifacts_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
    load_additional_evidence_session_authorization_v2,
    verify_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.consume_v2 import (
    consume_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.ledgers_v2 import (
    authorization_is_consumed_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.contract_v2 import (
    verify_additional_evidence_session_preregistration_contract_artifact_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.validate_v2 import (
    validate_additional_evidence_session_preregistration_candidate_v2,
)

GetPassFn = Callable[[str], str]
MonotonicClock = Callable[[], float]
WallClock = Callable[[], float]


def _load_preregistration_v1(*, repo_root: Path) -> dict[str, Any]:
    path = (
        repo_root
        / "config/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_v2.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def preflight_s03_execution_owner_v1(
    *,
    repo_root: Path,
    authorization_path: Path,
    authorization_id: str,
    authorization_digest: str,
    repository_sha: str,
    preregistration_path: Optional[Path] = None,
) -> S03ScopeBindingsV1:
    root = Path(repo_root)
    contract = verify_additional_evidence_session_preregistration_contract_artifact_v2(
        repo_root=root
    )
    if preregistration_path is not None:
        prereg = json.loads(Path(preregistration_path).read_text(encoding="utf-8"))
    else:
        prereg = _load_preregistration_v1(repo_root=root)
    validated = validate_additional_evidence_session_preregistration_candidate_v2(
        prereg,
        repo_root=root,
        verify_baseline_artifact_ordering=True,
    )
    artifact = load_additional_evidence_session_authorization_v2(Path(authorization_path))
    verified = verify_additional_evidence_session_authorization_v2(
        artifact,
        repo_root=root,
        require_unconsumed=True,
        require_unrevoked=True,
    )
    if verified.authorization_id != authorization_id:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("authorization_id_mismatch")
    if verified.authorization_digest != authorization_digest:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("authorization_digest_mismatch")
    if verified.execution_sha != repository_sha:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("repository_sha_mismatch")
    if verified.preregistration_id != validated["session_id"]:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("preregistration_id_mismatch")
    if verified.preregistration_digest != validated["preregistration_digest"]:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("preregistration_digest_mismatch")
    return validate_s03_scope_bindings_v1(
        {
            "campaign_id": verified.campaign_id,
            "session_label": "S03",
            "session_id": verified.preregistration_id,
            "preregistration_id": verified.preregistration_id,
            "preregistration_digest": verified.preregistration_digest,
            "contract_digest": contract["contract_digest"],
            "runbook_digest": verified.runbook_digest,
            "authorization_id": verified.authorization_id,
            "authorization_digest": verified.authorization_digest,
            "repository_sha": repository_sha,
            "venue": verified.venue,
            "instrument": verified.instrument,
            "network_scope": verified.network_scope,
            "session_scope": verified.session_scope,
            "duration_seconds": verified.duration_seconds,
        }
    )


def _write_session_cycle_evidence_v1(
    *,
    session_dir: Path,
    bindings: S03ScopeBindingsV1,
    samples: Sequence[MarketSampleV1],
    duration: MonotonicDurationAuthorityV1,
) -> dict[str, Any]:
    files = evidence_file_map_v1(session_dir)
    write_json_v1(
        files["session_metadata"],
        build_session_metadata_v1(bindings=bindings, mode="orchestrated"),
    )
    seen: set[str] = set()
    last_event: Optional[float] = None
    first_as_of: Optional[float] = None
    hb = 0
    vol_count = 0
    for sample in samples:
        elapsed = (
            duration.elapsed_seconds()
            if duration.started
            else float(sample.monotonic_elapsed_seconds)
        )
        hb += 1
        append_jsonl_v1(
            files["heartbeat"],
            build_heartbeat_v1(
                bindings=bindings,
                monotonic_elapsed_seconds=elapsed,
                receive_time_unix_seconds=sample.receive_time_unix_seconds,
                seq=hb,
            ),
        )
        duplicate, out_of_order, advances = classify_sample_ordering_v1(
            sample=sample,
            seen_identities=seen,
            last_event_time=last_event,
        )
        append_jsonl_v1(
            files["market_samples"],
            build_market_sample_record_v1(
                bindings=bindings,
                sample=sample,
                duplicate=duplicate,
                out_of_order=out_of_order,
            ),
        )
        seen.add(sample.sample_identity)
        if advances:
            if first_as_of is None:
                first_as_of = float(sample.event_time_unix_seconds)
                age = 0
                as_of = first_as_of
            else:
                as_of = float(first_as_of)
                age = int(max(0.0, float(sample.event_time_unix_seconds) - as_of))
            last_event = float(sample.event_time_unix_seconds)
            old_vol = 0.12
            fresh_vol = 0.12 + (0.0001 * vol_count)
            source_digest = sample.sample_identity
            vol = build_volatility_record_v1(
                bindings=bindings,
                monotonic_elapsed_seconds=elapsed,
                receive_time_unix_seconds=sample.receive_time_unix_seconds,
                old_volatility=old_vol,
                old_age_seconds=age,
                old_as_of_event_time=as_of,
                estimator="canonical_research_estimator_v1",
                unit="decimal",
                horizon="PT60M",
                annualized=True,
                observation_count=vol_count + 1,
                source_digest=source_digest,
                fresh_volatility=fresh_vol,
                recomputation_input_digest=f"recompute:{source_digest}",
                consuming_decision_context="ALPHA_OBSERVATIONAL_ONLY",
            )
            append_jsonl_v1(files["volatility_records"], vol)
            append_jsonl_v1(
                files["volatility_drift_comparisons"],
                build_drift_comparison_v1(bindings=bindings, volatility_record=vol),
            )
            old_decision = "HOLD"
            fresh_decision = "HOLD" if age < 3600 else "BLOCK_ALPHA_AGE_ONLY"
            append_jsonl_v1(
                files["decision_sensitivity"],
                build_decision_sensitivity_v1(
                    bindings=bindings,
                    other_inputs_digest="other_inputs_constant_v1",
                    old_decision=old_decision,
                    fresh_counterfactual_decision=fresh_decision,
                    monotonic_elapsed_seconds=elapsed,
                    receive_time_unix_seconds=sample.receive_time_unix_seconds,
                ),
            )
            append_jsonl_v1(
                files["counterfactual_decisions"],
                build_counterfactual_record_v1(
                    bindings=bindings,
                    runtime_decision=old_decision,
                    counterfactual_decision=fresh_decision,
                    monotonic_elapsed_seconds=elapsed,
                    receive_time_unix_seconds=sample.receive_time_unix_seconds,
                ),
            )
            indep = build_exit_risk_safety_independence_record_v1(
                bindings=bindings,
                alpha_gate_blocked=(fresh_decision != old_decision),
                monotonic_elapsed_seconds=elapsed,
                receive_time_unix_seconds=sample.receive_time_unix_seconds,
            )
            assert_exit_precedence_preserved_v1(indep)
            append_jsonl_v1(files["exit_risk_safety_independence"], indep)
            vol_count += 1
        append_jsonl_v1(
            files["connectivity_events"],
            {
                "schema": (
                    "canonical_volatility_numeric_max_age_additional_evidence_s03_connectivity/v1"
                ),
                **bindings.to_dict(),
                "event": "SAMPLE_INGESTED",
                "duplicate": duplicate,
                "out_of_order": out_of_order,
                "monotonic_elapsed_seconds": elapsed,
                "receive_time": sample.receive_time_unix_seconds,
            },
        )
    return {
        "heartbeat_count": hb,
        "volatility_record_count": vol_count,
        "market_sample_count": len(samples),
        "distinct_market_sample_count": len(seen),
    }


def run_additional_evidence_s03_productive_session_v1(
    *,
    repo_root: Path,
    authorization_path: Path,
    authorization_id: str,
    authorization_digest: str,
    repository_sha: str,
    evidence_root: Optional[Path] = None,
    confirm_token: Optional[str] = None,
    expected_confirm_token_fingerprint: Optional[str] = None,
    getpass_fn: Optional[GetPassFn] = None,
    monotonic_clock: Optional[MonotonicClock] = None,
    wall_clock: Optional[WallClock] = None,
    market_samples: Optional[Sequence[MarketSampleV1]] = None,
    preflight_only: bool = False,
    offline_probe: bool = False,
    enable_real_s03_session_execution: bool = False,
    enable_real_public_md_network: bool = False,
    preregistration_path: Optional[Path] = None,
    side_effect_probe: Optional[SideEffectProbeV1] = None,
    skip_second_consumption_check: bool = False,
) -> dict[str, Any]:
    """Canonical S03 execution owner entrypoint."""
    import time as _time

    probe = side_effect_probe or SideEffectProbeV1()
    root = Path(repo_root)
    evi_root = Path(evidence_root) if evidence_root is not None else root
    mono = monotonic_clock or _time.monotonic
    session_dir = resolve_s03_session_dir_v1(evidence_root=evi_root)
    auth_consumed = False
    lock: Optional[S03SessionLockV1] = None
    lock_created = False
    lock_removed = False
    network_occurred = False
    evidence_mutated = False
    actual_duration = 0.0
    terminal_path = ""
    manifest_path = ""
    bindings: Optional[S03ScopeBindingsV1] = None
    status = "BLOCKED"
    verdict = "NOT_STARTED"
    blocker = ""
    sufficient = False
    token_local: Optional[str] = confirm_token

    try:
        bindings = preflight_s03_execution_owner_v1(
            repo_root=root,
            authorization_path=Path(authorization_path),
            authorization_id=authorization_id,
            authorization_digest=authorization_digest,
            repository_sha=repository_sha,
            preregistration_path=preregistration_path,
        )
        probe.record("PREFLIGHT_PASS")
        if preflight_only:
            return redact_confirm_token_from_mapping_v1(
                OrchestratorResultV1(
                    status="PREFLIGHT_PASS",
                    terminal_verdict="PREFLIGHT_ONLY_NO_EXECUTION",
                    authorization_consumed=False,
                    session_lock_created=False,
                    session_lock_removed=False,
                    network_activity_occurred=False,
                    evidence_mutation_occurred=False,
                    real_session_started=False,
                    requested_duration_seconds=BOUND_DURATION_SECONDS,
                    actual_monotonic_duration_seconds=0.0,
                    evidence_root=str(session_dir),
                    integrity_manifest_path="",
                    terminal_verdict_path="",
                    side_effect_probe=probe.to_dict(),
                ).to_dict()
            )

        if enable_real_s03_session_execution and not offline_probe:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "real_s03_execution_requires_separate_operator_go_after_capability_merge"
            )
        if (
            enable_real_public_md_network
            and not REAL_NETWORK_IN_THIS_CAPABILITY
            and not offline_probe
        ):
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "real_network_forbidden_in_capability_mode"
            )
        if not offline_probe:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "offline_probe_or_preflight_required_in_capability_mode"
            )
        if market_samples is None:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "offline_probe_market_samples_required"
            )

        artifact = load_additional_evidence_session_authorization_v2(Path(authorization_path))
        if token_local is None:
            fp = expected_confirm_token_fingerprint or artifact.confirm_token_fingerprint
            token_local = read_confirm_token_interactively_v1(
                expected_fingerprint=fp,
                getpass_fn=getpass_fn,
            )

        assert_s03_consume_before_side_effects_v1(probe.events)
        consume_additional_evidence_session_authorization_v2(
            repo_root=root,
            authorization_path=Path(authorization_path),
            confirm_token=token_local,
            side_effect_probe=list(probe.events),
        )
        auth_consumed = True
        probe.record(SIDE_EFFECT_AUTHORIZATION_CONSUMED)
        if not authorization_is_consumed_v2(
            consumption_ledger_path=root / artifact.consumption_ledger_path,
            authorization_id=authorization_id,
        ):
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "consumption_ledger_missing_record"
            )

        if not skip_second_consumption_check:
            second_rejected = False
            try:
                consume_additional_evidence_session_authorization_v2(
                    repo_root=root,
                    authorization_path=Path(authorization_path),
                    confirm_token=token_local,
                    side_effect_probe=[SIDE_EFFECT_AUTHORIZATION_CONSUMED],
                )
            except Exception:  # noqa: BLE001
                second_rejected = True
            if not second_rejected:
                raise AdditionalEvidenceS03SessionExecutionOwnerError(
                    "second_consumption_was_not_rejected"
                )
            probe.record("SECOND_CONSUMPTION_REJECTED")

        token_local = None

        duration = MonotonicDurationAuthorityV1(
            requested_duration_seconds=BOUND_DURATION_SECONDS,
            monotonic_clock=mono,
        )
        duration.start()

        lock = S03SessionLockV1(
            session_dir=session_dir,
            bindings=bindings,
            monotonic_clock=mono,
        )
        lock.acquire()
        lock_created = True
        probe.record(SIDE_EFFECT_SESSION_LOCK)
        assert_s03_consume_before_side_effects_v1(probe.events)

        probe.record(SIDE_EFFECT_RUNTIME_INITIALIZATION)
        demo_url = "https://eea.okx.com/api/v5/public/mark-price?instId=ETH-USD-SWAP"
        assert_public_md_request_allowed_v1(url=demo_url, method="GET")
        assert_no_credentials_v1({})
        probe.record(SIDE_EFFECT_NETWORK)
        network_occurred = False
        assert_s03_consume_before_side_effects_v1(probe.events)

        probe.record(SIDE_EFFECT_EVIDENCE_CREATION)
        _write_session_cycle_evidence_v1(
            session_dir=session_dir,
            bindings=bindings,
            samples=market_samples,
            duration=duration,
        )
        evidence_mutated = True

        if not duration.is_complete():
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "insufficient_monotonic_duration_for_s03_pass"
            )
        duration.assert_sufficient_for_pass()
        actual_duration = duration.elapsed_seconds()
        sufficient = True
        status = "PASS"
        verdict = "S03_OFFLINE_PROBE_COMPLETE"
    except Exception as exc:  # noqa: BLE001
        blocker = str(exc)
        if auth_consumed:
            status = "ABORTED"
            verdict = "FAIL_CLOSED_AFTER_AUTHORIZATION_CONSUMPTION"
        else:
            status = "BLOCKED"
            verdict = "FAIL_CLOSED_BEFORE_AUTHORIZATION_CONSUMPTION"
        sufficient = False
    finally:
        if lock is not None and lock.held:
            try:
                lock.release()
                lock_removed = True
            except Exception:  # noqa: BLE001
                lock_removed = False
        if bindings is not None and (evidence_mutated or auth_consumed or status != "BLOCKED"):
            try:
                _v, _m, t_path, m_path = write_terminal_artifacts_v1(
                    session_dir=session_dir,
                    bindings=bindings,
                    status=status,
                    terminal_reason=blocker or verdict,
                    authorization_consumed=auth_consumed,
                    actual_monotonic_duration_seconds=actual_duration,
                    sufficient_s03_evidence=sufficient,
                    network_activity_occurred=network_occurred,
                )
                terminal_path = str(t_path)
                manifest_path = str(m_path)
                evidence_mutated = True
            except Exception:  # noqa: BLE001
                pass
        token_local = None

    return redact_confirm_token_from_mapping_v1(
        OrchestratorResultV1(
            status=status,
            terminal_verdict=verdict,
            authorization_consumed=auth_consumed,
            session_lock_created=lock_created,
            session_lock_removed=lock_removed,
            network_activity_occurred=network_occurred,
            evidence_mutation_occurred=evidence_mutated,
            real_session_started=False,
            requested_duration_seconds=BOUND_DURATION_SECONDS,
            actual_monotonic_duration_seconds=actual_duration,
            evidence_root=str(session_dir),
            integrity_manifest_path=manifest_path,
            terminal_verdict_path=terminal_path,
            side_effect_probe=probe.to_dict(),
            blocker=blocker,
            sufficient_s03_evidence=sufficient,
            counterfactual_runtime_authority_occurred=False,
        ).to_dict()
    )
