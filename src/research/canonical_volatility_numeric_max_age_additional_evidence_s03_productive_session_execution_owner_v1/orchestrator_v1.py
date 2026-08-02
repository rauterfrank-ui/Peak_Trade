"""S03 productive session orchestrator: Auth-v2 consume-before-side-effects owner.

Supports offline probe / preflight and the gated productive real path
(Auth-v2 consume → lock → public-MD → 10860s natural-age S03 evidence).
"""

from __future__ import annotations

import json
import time
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
    AUTHORIZATION_CONSUMPTION_IN_THIS_CAPABILITY,
    BOUND_DURATION_SECONDS,
    DEFAULT_REAL_SESSION_MAXIMUM_CYCLES,
    DEFAULT_REAL_SESSION_MINIMUM_INTERVAL_SECONDS,
    PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY,
    READY_FOR_S03_AUTHORIZATION_CONSUMPTION_AND_EXECUTION,
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
    resolve_s03_session_dir_v1,
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
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.real_session_loop_v1 import (
    SampleProvider,
    assert_real_path_network_preconditions_v1,
    collect_natural_age_samples_until_duration_v1,
    default_mark_price_url_v1,
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
SleepFn = Callable[[float], None]


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
    """Delegate to typed-vol + full-alpha evidence cycle (no synthetic scaffolds)."""
    # Lazy import avoids S03 package <-> typed-evidence cycle circular import.
    from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.s03_typed_evidence_cycle_v1 import (
        write_typed_s03_session_cycle_evidence_v1,
    )

    return write_typed_s03_session_cycle_evidence_v1(
        session_dir=session_dir,
        bindings=bindings,
        samples=samples,
        duration=duration,
    )


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
    market_sample_provider: Optional[SampleProvider] = None,
    http_fetcher: Optional[Callable[..., object]] = None,
    pace_sleep: Optional[SleepFn] = None,
    preflight_only: bool = False,
    offline_probe: bool = False,
    enable_real_s03_session_execution: bool = False,
    enable_real_public_md_network: bool = False,
    preregistration_path: Optional[Path] = None,
    side_effect_probe: Optional[SideEffectProbeV1] = None,
    skip_second_consumption_check: bool = False,
) -> dict[str, Any]:
    """Canonical S03 execution owner entrypoint."""
    probe = side_effect_probe or SideEffectProbeV1()
    root = Path(repo_root)
    evi_root = Path(evidence_root) if evidence_root is not None else root
    mono = monotonic_clock or time.monotonic
    wall = wall_clock or time.time
    sleep_fn = pace_sleep or time.sleep
    session_dir = resolve_s03_session_dir_v1(evidence_root=evi_root)
    auth_consumed = False
    lock: Optional[S03SessionLockV1] = None
    lock_created = False
    lock_removed = False
    network_occurred = False
    evidence_mutated = False
    real_session_started = False
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

        real_path = bool(enable_real_s03_session_execution) and not bool(offline_probe)
        if real_path:
            if not (
                PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY
                and AUTHORIZATION_CONSUMPTION_IN_THIS_CAPABILITY
                and READY_FOR_S03_AUTHORIZATION_CONSUMPTION_AND_EXECUTION
            ):
                raise AdditionalEvidenceS03SessionExecutionOwnerError(
                    "productive_execution_capability_flags_not_enabled"
                )
            if enable_real_public_md_network and not REAL_NETWORK_IN_THIS_CAPABILITY:
                raise AdditionalEvidenceS03SessionExecutionOwnerError(
                    "real_network_capability_flag_not_enabled"
                )
            if confirm_token is not None:
                raise AdditionalEvidenceS03SessionExecutionOwnerError(
                    "confirm_token_parameter_forbidden_on_real_path"
                )
        elif not offline_probe:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "offline_probe_or_real_execution_or_preflight_required"
            )
        elif market_samples is None:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "offline_probe_market_samples_required"
            )

        artifact = load_additional_evidence_session_authorization_v2(Path(authorization_path))
        probe.record("INTERACTIVE_TOKEN_READ")
        if real_path:
            token_local = read_confirm_token_interactively_v1(
                expected_fingerprint=(
                    expected_confirm_token_fingerprint or artifact.confirm_token_fingerprint
                ),
                getpass_fn=getpass_fn,
            )
        elif token_local is None:
            token_local = read_confirm_token_interactively_v1(
                expected_fingerprint=(
                    expected_confirm_token_fingerprint or artifact.confirm_token_fingerprint
                ),
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
        probe.record("CONSUMPTION_DURABILITY_CHECK")

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
        assert_real_path_network_preconditions_v1()
        assert_public_md_request_allowed_v1(url=default_mark_price_url_v1(), method="GET")
        assert_no_credentials_v1({})
        probe.record(SIDE_EFFECT_NETWORK)
        assert_s03_consume_before_side_effects_v1(probe.events)

        samples_for_evidence: Sequence[MarketSampleV1]
        if offline_probe:
            network_occurred = False
            samples_for_evidence = market_samples or ()
            verdict = "S03_OFFLINE_PROBE_COMPLETE"
        else:
            real_session_started = True
            if not enable_real_public_md_network:
                raise AdditionalEvidenceS03SessionExecutionOwnerError(
                    "real_public_md_network_required_for_productive_session"
                )
            provider = market_sample_provider
            if provider is None:
                if http_fetcher is None:
                    raise AdditionalEvidenceS03SessionExecutionOwnerError(
                        "real_market_sample_provider_or_http_fetcher_required"
                    )
                from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.public_md_sample_provider_v1 import (
                    build_s03_public_md_sample_provider_v1,
                )

                provider = build_s03_public_md_sample_provider_v1(
                    session_id=bindings.session_id,
                    http_fetcher=http_fetcher,  # type: ignore[arg-type]
                    wall_clock=wall,
                    sleep=sleep_fn,
                    monotonic_clock=mono,
                )
            samples_for_evidence = collect_natural_age_samples_until_duration_v1(
                duration=duration,
                sample_provider=provider,
                pace_sleep=sleep_fn,
                minimum_interval_seconds=DEFAULT_REAL_SESSION_MINIMUM_INTERVAL_SECONDS,
                wall_clock=wall,
                max_cycles=DEFAULT_REAL_SESSION_MAXIMUM_CYCLES,
            )
            network_occurred = bool(enable_real_public_md_network)
            verdict = "S03_PRODUCTIVE_NATURAL_AGE_SESSION_COMPLETE"

        probe.record(SIDE_EFFECT_EVIDENCE_CREATION)
        _write_session_cycle_evidence_v1(
            session_dir=session_dir,
            bindings=bindings,
            samples=samples_for_evidence,
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
            real_session_started=real_session_started,
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
