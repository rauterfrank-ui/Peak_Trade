"""Atomic S03 Auth-v2 reissue→consume→execute orchestration owner.

Lifecycle (single process):
  preflight → revoke unconsumable → mint ephemeral token → issue auth-v2 →
  verify → S03 owner consume+execute (same token via getpass handle) →
  clear token (finally).

No second authorization/consumption/execution authority. Productive mutation
requires explicit enable_productive_atomic_execution=True.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.constants_v1 import (
    BOUND_DURATION_SECONDS_V1,
    DEFAULT_UNCONSUMABLE_REVOCATION_REASON,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.ephemeral_token_v1 import (
    EphemeralConfirmTokenHandleV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.models_v1 import (
    AtomicOrchestratorResultV1,
    AtomicS03AuthV2ReissueConsumeExecuteError,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.confirm_token_stdin_v1 import (
    redact_confirm_token_from_mapping_v1,
    sha256_fingerprint_plaintext_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    MarketSampleV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.orchestrator_v1 import (
    preflight_s03_execution_owner_v1,
    run_additional_evidence_s03_productive_session_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
    build_additional_evidence_session_authorization_v2,
    load_additional_evidence_session_authorization_v2,
    verify_additional_evidence_session_authorization_v2,
    write_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    AUTHORIZATION_FILENAME,
    CONSUMPTION_LEDGER_FILENAME,
    DEFAULT_EVIDENCE_CAMPAIGN_ROOT,
    REVOCATION_LEDGER_FILENAME,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.consume_v2 import (
    revoke_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.discovery_v2 import (
    discover_unconsumed_additional_evidence_authorizations_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.issuance_v2 import (
    issue_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.ledgers_v2 import (
    authorization_is_consumed_v2,
    authorization_is_revoked_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.contract_v2 import (
    verify_additional_evidence_session_preregistration_contract_artifact_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.validate_v2 import (
    validate_additional_evidence_session_preregistration_candidate_v2,
)

SampleProvider = Callable[..., MarketSampleV1]
MonotonicClock = Callable[[], float]
WallClock = Callable[[], float]
SleepFn = Callable[[float], None]
HttpFetcher = Callable[..., object]


def _load_prereg(repo_root: Path) -> dict[str, Any]:
    path = (
        repo_root
        / "config/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_v2.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _authorization_path_for_campaign(*, repo_root: Path, campaign_id: str) -> Path:
    return (
        Path(repo_root)
        / DEFAULT_EVIDENCE_CAMPAIGN_ROOT
        / campaign_id
        / "authorization"
        / AUTHORIZATION_FILENAME
    )


def _issue_offline_isolated_v1(
    *,
    repo_root: Path,
    execution_sha: str,
    confirm_token: str,
    authorization_dir: Path,
    issued_at: Optional[datetime] = None,
) -> Any:
    """Issue via canonical build/write into an isolated authorization_dir (tests)."""
    root = Path(repo_root)
    contract = verify_additional_evidence_session_preregistration_contract_artifact_v2(
        repo_root=root
    )
    prereg = _load_prereg(root)
    validated = validate_additional_evidence_session_preregistration_candidate_v2(
        prereg,
        repo_root=root,
        verify_baseline_artifact_ordering=True,
    )
    auth_dir = Path(authorization_dir)
    auth_dir.mkdir(parents=True, exist_ok=True)
    rev_path = auth_dir / REVOCATION_LEDGER_FILENAME
    cons_path = auth_dir / CONSUMPTION_LEDGER_FILENAME
    artifact = build_additional_evidence_session_authorization_v2(
        preregistration_id=str(validated["session_id"]),
        preregistration_digest=str(validated["preregistration_digest"]),
        preregistration_contract_version=str(contract["capability_version"]),
        preregistration_contract_digest=str(contract["contract_digest"]),
        code_baseline_sha=str(validated["code_baseline_sha"]),
        execution_sha=execution_sha,
        critical_surface_digest=str(validated["critical_surface_manifest_digest"]),
        runbook_digest=str(prereg["runbook_digest"]),
        venue=str(validated["venue"]),
        instrument=str(validated["instrument"]),
        network_scope=str(validated["network_scope"]),
        session_scope=str(validated["session_scope"]),
        duration_seconds=int(prereg["duration_seconds"]),
        campaign_id=str(validated["campaign_id"]),
        confirm_token=confirm_token,
        revocation_ledger_path=str(rev_path.resolve()),
        consumption_ledger_path=str(cons_path.resolve()),
        issued_at=issued_at or datetime.now(timezone.utc),
    )
    out = auth_dir / AUTHORIZATION_FILENAME
    write_additional_evidence_session_authorization_v2(output_path=out, artifact=artifact)
    reloaded = load_additional_evidence_session_authorization_v2(out)
    verify_additional_evidence_session_authorization_v2(
        reloaded,
        repo_root=root,
        expected_execution_sha=execution_sha,
        require_unconsumed=True,
        require_unrevoked=True,
    )
    return reloaded, out


def run_s03_atomic_auth_v2_reissue_consume_and_execute_with_ephemeral_confirm_token_v1(
    *,
    repo_root: Path,
    execution_sha: str,
    unconsumable_authorization_path: Path,
    unconsumable_authorization_id: str,
    unconsumable_revocation_reason: str = DEFAULT_UNCONSUMABLE_REVOCATION_REASON,
    evidence_root: Optional[Path] = None,
    isolated_authorization_dir: Optional[Path] = None,
    enable_productive_atomic_execution: bool = False,
    offline_probe: bool = False,
    market_samples: Optional[Sequence[MarketSampleV1]] = None,
    market_sample_provider: Optional[SampleProvider] = None,
    http_fetcher: Optional[HttpFetcher] = None,
    monotonic_clock: Optional[MonotonicClock] = None,
    wall_clock: Optional[WallClock] = None,
    pace_sleep: Optional[SleepFn] = None,
    preflight_only: bool = False,
    skip_old_authorization_revoke: bool = False,
) -> dict[str, Any]:
    """Canonical atomic orchestration entrypoint (lifecycle authority only)."""
    root = Path(repo_root)
    evi_root = Path(evidence_root) if evidence_root is not None else root
    probe: list[str] = []
    token_handle: Optional[EphemeralConfirmTokenHandleV1] = None
    new_auth_path: Optional[Path] = None
    new_auth_id = ""
    old_revoked = False
    consumed = False
    revoked_new_on_failure = False
    s03_result: Optional[dict[str, Any]] = None
    status = "BLOCKED"
    verdict = "NOT_STARTED"
    blocker = ""
    notes = [
        "S03_ATOMIC_AUTH_V2_REISSUE_CONSUME_EXECUTE",
        "ISSUE_AND_CONSUME_SAME_PROCESS",
        "TOKEN_PLAINTEXT_MUST_NOT_CROSS_PROCESS_BOUNDARY",
        f"OFFLINE_PROBE={offline_probe}",
        f"PRODUCTIVE={enable_productive_atomic_execution}",
    ]

    try:
        if enable_productive_atomic_execution and offline_probe:
            raise AtomicS03AuthV2ReissueConsumeExecuteError(
                "productive_and_offline_probe_mutually_exclusive"
            )
        if not enable_productive_atomic_execution and not offline_probe and not preflight_only:
            raise AtomicS03AuthV2ReissueConsumeExecuteError(
                "offline_probe_or_productive_or_preflight_required"
            )

        old_path = Path(unconsumable_authorization_path)
        old = load_additional_evidence_session_authorization_v2(old_path)
        if old.authorization_id != unconsumable_authorization_id:
            raise AtomicS03AuthV2ReissueConsumeExecuteError(
                "unconsumable_authorization_id_mismatch"
            )
        if old.duration_seconds != BOUND_DURATION_SECONDS_V1:
            raise AtomicS03AuthV2ReissueConsumeExecuteError("duration_binding_mismatch")
        verify_additional_evidence_session_authorization_v2(
            old,
            repo_root=root,
            expected_execution_sha=None if offline_probe else execution_sha,
            require_unconsumed=True,
            require_unrevoked=True,
        )
        preflight_s03_execution_owner_v1(
            repo_root=root,
            authorization_path=old_path,
            authorization_id=old.authorization_id,
            authorization_digest=old.authorization_digest,
            repository_sha=old.execution_sha if offline_probe else execution_sha,
        )
        probe.append("PREFLIGHT_PASS")

        if preflight_only:
            return redact_confirm_token_from_mapping_v1(
                AtomicOrchestratorResultV1(
                    status="PREFLIGHT_PASS",
                    verdict="PREFLIGHT_ONLY_NO_MUTATION",
                    old_authorization_id=old.authorization_id,
                    notes=notes + ["PREFLIGHT_ONLY"],
                    side_effect_probe=probe,
                ).to_dict()
            )

        if not skip_old_authorization_revoke:
            rev = revoke_additional_evidence_session_authorization_v2(
                repo_root=root,
                authorization_path=old_path,
                reason=unconsumable_revocation_reason,
            )
            if not rev.get("ok"):
                raise AtomicS03AuthV2ReissueConsumeExecuteError("old_authorization_revoke_failed")
            rev_ledger = Path(old.revocation_ledger_path)
            if not rev_ledger.is_absolute():
                rev_ledger = root / rev_ledger
            if not authorization_is_revoked_v2(
                revocation_ledger_path=rev_ledger,
                authorization_id=old.authorization_id,
            ):
                raise AtomicS03AuthV2ReissueConsumeExecuteError(
                    "old_authorization_not_revoked_after_revoke"
                )
            old_revoked = True
            probe.append("OLD_AUTHORIZATION_REVOKED")

        token_handle = EphemeralConfirmTokenHandleV1.mint_canonical_v1()
        probe.append("EPHEMERAL_TOKEN_MINTED")
        expected_fp = token_handle.fingerprint_v1()

        if offline_probe:
            if isolated_authorization_dir is None:
                raise AtomicS03AuthV2ReissueConsumeExecuteError(
                    "isolated_authorization_dir_required_for_offline_probe"
                )
            if market_samples is None:
                raise AtomicS03AuthV2ReissueConsumeExecuteError(
                    "offline_probe_market_samples_required"
                )
            issued, new_auth_path = _issue_offline_isolated_v1(
                repo_root=root,
                execution_sha=execution_sha,
                confirm_token=token_handle.borrow_plaintext_v1(),
                authorization_dir=Path(isolated_authorization_dir),
            )
            new_auth_id = issued.authorization_id
            probe.append("NEW_AUTHORIZATION_ISSUED_OFFLINE_ISOLATED")
        else:
            # Productive path: revoke cleared scope conflict; issue via canonical issuer.
            issue_result = issue_additional_evidence_session_authorization_v2(
                repo_root=root,
                execution_sha=execution_sha,
                confirm_token=token_handle.borrow_plaintext_v1(),
                dry_run=False,
                require_head_equals_origin_main=True,
            )
            if not issue_result.ok or issue_result.artifact is None:
                raise AtomicS03AuthV2ReissueConsumeExecuteError(
                    "canonical_issuance_failed:" + ",".join(issue_result.blockers or ["unknown"])
                )
            issued = issue_result.artifact
            new_auth_id = issued.authorization_id
            new_auth_path = Path(issue_result.authorization_path)
            probe.append("NEW_AUTHORIZATION_ISSUED")

        if sha256_fingerprint_plaintext_v1(token_handle.borrow_plaintext_v1()) != (
            issued.confirm_token_fingerprint
        ):
            raise AtomicS03AuthV2ReissueConsumeExecuteError(
                "issued_confirm_token_fingerprint_mismatch"
            )
        if expected_fp != issued.confirm_token_fingerprint:
            raise AtomicS03AuthV2ReissueConsumeExecuteError(
                "handle_fingerprint_drift_after_issuance"
            )
        verify_additional_evidence_session_authorization_v2(
            issued,
            repo_root=root,
            expected_execution_sha=execution_sha,
            expected_preregistration_id=issued.preregistration_id,
            require_unconsumed=True,
            require_unrevoked=True,
        )
        if issued.duration_seconds != BOUND_DURATION_SECONDS_V1:
            raise AtomicS03AuthV2ReissueConsumeExecuteError("issued_duration_mismatch")
        probe.append("NEW_AUTHORIZATION_VERIFIED")

        # Immediate same-process consumption+execution via canonical S03 owner.
        # Real path forbids confirm_token= parameter; getpass handle supplies plaintext.
        s03_result = run_additional_evidence_s03_productive_session_v1(
            repo_root=root,
            authorization_path=Path(new_auth_path),
            authorization_id=issued.authorization_id,
            authorization_digest=issued.authorization_digest,
            repository_sha=execution_sha,
            evidence_root=evi_root,
            confirm_token=None if not offline_probe else None,
            expected_confirm_token_fingerprint=issued.confirm_token_fingerprint,
            getpass_fn=token_handle.as_getpass_fn_v1(),
            monotonic_clock=monotonic_clock,
            wall_clock=wall_clock,
            market_samples=market_samples,
            market_sample_provider=market_sample_provider,
            http_fetcher=http_fetcher,
            pace_sleep=pace_sleep,
            offline_probe=offline_probe,
            enable_real_s03_session_execution=bool(enable_productive_atomic_execution),
            enable_real_public_md_network=bool(enable_productive_atomic_execution),
        )
        consumed = bool(s03_result.get("authorization_consumed"))
        if consumed:
            probe.append("AUTHORIZATION_CONSUMED")
        # Token lifetime ends after successful consumption (best-effort clear).
        if consumed and token_handle is not None:
            token_handle.clear_v1()
            probe.append("EPHEMERAL_TOKEN_CLEARED_AFTER_CONSUMPTION")

        if not consumed:
            raise AtomicS03AuthV2ReissueConsumeExecuteError(
                f"s03_owner_did_not_consume:{s03_result.get('terminal_verdict')}"
                f":{s03_result.get('blocker')}"
            )

        cons_ledger = Path(issued.consumption_ledger_path)
        if not cons_ledger.is_absolute():
            cons_ledger = root / cons_ledger
        if not authorization_is_consumed_v2(
            consumption_ledger_path=cons_ledger,
            authorization_id=issued.authorization_id,
        ):
            raise AtomicS03AuthV2ReissueConsumeExecuteError("consumption_ledger_missing_after_s03")

        # Exactly one terminal consumed authorization for this id; no second active.
        active = discover_unconsumed_additional_evidence_authorizations_v2(
            repo_root=root,
            preregistration_id=issued.preregistration_id,
        )
        # Offline isolated auth may use absolute ledgers outside default campaign root.
        if not offline_probe and active:
            raise AtomicS03AuthV2ReissueConsumeExecuteError(
                "unexpected_unconsumed_authorization_after_consume"
            )

        if s03_result.get("status") != "PASS":
            status = "ABORTED"
            verdict = "FAIL_CLOSED_AFTER_AUTHORIZATION_CONSUMPTION"
            blocker = str(s03_result.get("blocker") or s03_result.get("terminal_verdict"))
        else:
            status = "PASS"
            verdict = "S03_ATOMIC_REISSUE_CONSUME_EXECUTE_COMPLETE"
            probe.append("S03_EXECUTION_COMPLETE")

    except Exception as exc:  # noqa: BLE001
        # Never include exc args that might hold token material beyond known safe codes.
        blocker = str(exc)
        if "GO_PSO_SESSION_PREREG_V1_" in blocker:
            blocker = "fail_closed_redacted_blocker"
        if consumed:
            status = "ABORTED"
            verdict = "FAIL_CLOSED_AFTER_AUTHORIZATION_CONSUMPTION"
        else:
            status = "BLOCKED"
            verdict = "FAIL_CLOSED_BEFORE_OR_DURING_ATOMIC_LIFECYCLE"
            if new_auth_path is not None and new_auth_id:
                try:
                    revoke_additional_evidence_session_authorization_v2(
                        repo_root=root,
                        authorization_path=Path(new_auth_path),
                        reason="atomic_preconsumption_failure_auto_revoke",
                    )
                    revoked_new_on_failure = True
                    probe.append("NEW_AUTHORIZATION_AUTO_REVOKED_PRECONSUMPTION")
                except Exception:  # noqa: BLE001
                    probe.append("NEW_AUTHORIZATION_AUTO_REVOKE_FAILED")
    finally:
        if token_handle is not None and not token_handle.cleared:
            token_handle.clear_v1()
            probe.append("EPHEMERAL_TOKEN_CLEARED_FINALLY")
        token_handle = None

    result = AtomicOrchestratorResultV1(
        status=status,
        verdict=verdict,
        old_authorization_id=unconsumable_authorization_id,
        old_authorization_revoked=old_revoked,
        new_authorization_id=new_auth_id,
        new_authorization_revoked_on_failure=revoked_new_on_failure,
        authorization_consumed=consumed,
        authorization_consumed_exactly_once=consumed,
        session_lock_created=bool((s03_result or {}).get("session_lock_created")),
        session_lock_removed=bool((s03_result or {}).get("session_lock_removed")),
        network_activity_occurred=bool((s03_result or {}).get("network_activity_occurred")),
        evidence_mutation_occurred=bool((s03_result or {}).get("evidence_mutation_occurred")),
        real_session_started=bool((s03_result or {}).get("real_session_started")),
        requested_duration_seconds=BOUND_DURATION_SECONDS_V1,
        actual_monotonic_duration_seconds=float(
            (s03_result or {}).get("actual_monotonic_duration_seconds") or 0.0
        ),
        evidence_root=str((s03_result or {}).get("evidence_root") or evi_root),
        integrity_manifest_path=str((s03_result or {}).get("integrity_manifest_path") or ""),
        terminal_verdict_path=str((s03_result or {}).get("terminal_verdict_path") or ""),
        blocker=blocker,
        side_effect_probe=probe,
        s03_result=s03_result,
        notes=notes,
    )
    return redact_confirm_token_from_mapping_v1(result.to_dict())
