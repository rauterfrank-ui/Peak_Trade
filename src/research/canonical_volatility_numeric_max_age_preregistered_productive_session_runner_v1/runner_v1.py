"""Preregistered productive session runner: consume-before-side-effects lifecycle."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
    ProductiveBridgeMarketSampleV1,
    assert_ledger_integrity_matrix_v1,
    run_productive_bridge_accumulation_session_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.consume_v1 import (
    consume_campaign_authorization_session_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.ledgers_v1 import (
    load_consumption_records_v1,
    resolve_ledger_path_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    BOUND_CAMPAIGN_ID_V1,
    BOUND_EVIDENCE_SCOPE,
    BOUND_INSTRUMENT_ID,
    BOUND_PREREGISTRATION_DIGEST_V1,
    BOUND_PREREGISTRATION_ID,
    BOUND_SESSION_IDS_V1,
    BOUND_VENUE,
    BOUND_VENUE_INSTRUMENT_ID,
    BOUND_VENUE_SCOPE,
    BRIDGE_SAMPLE_VENUE,
    EXPECTED_BRANCH_DEFAULT,
    SESSION_01_ID,
    SESSION_02_ID,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    GitBaselineSnapshotV1,
    PreregisteredSessionRunnerError,
    RunnerResultV1,
    SideEffectProbeV1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.preflight_v1 import (
    run_static_preflight_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.instrument_binding_v1 import (
    binding_evidence_v1,
    resolve_preregistered_session_venue_instrument_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (
    default_public_md_request_pacing_policy_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_source_v1 import (
    PublicMdSourceTelemetryV1,
    assert_no_orders_or_credentials_v1,
    build_preregistered_public_md_transport_v1,
    collect_public_mark_samples_v1,
    initialize_session_md_controls_v1,
    reject_offline_synthetic_mark_source_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.terminal_v1 import (
    build_integrity_manifest_v1,
    write_session_terminal_evidence_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    HttpFetcher,
)


def _session_02_paths_snapshot_v1(evidence_root: Path) -> dict[str, str]:
    base = (
        evidence_root
        / "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
        / "campaigns"
        / BOUND_CAMPAIGN_ID_V1
        / "sessions"
    )
    paths = {
        "session_02_manifest": base / "session_02_manifest.json",
        "session_02_lock": base / "session_02_manifest.lock",
    }
    snap: dict[str, str] = {}
    for key, path in paths.items():
        if path.exists():
            snap[key] = path.read_text(encoding="utf-8")
        else:
            snap[key] = ""
    return snap


def _assert_session_02_unchanged_v1(before: Mapping[str, str], evidence_root: Path) -> bool:
    after = _session_02_paths_snapshot_v1(evidence_root)
    return dict(before) == dict(after)


class _SessionExclusiveLockV1:
    def __init__(self, lock_path: Path) -> None:
        self.lock_path = Path(lock_path)
        self.fd: Optional[int] = None

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise PreregisteredSessionRunnerError(f"session_lock_busy:{exc}") from exc

    def release(self) -> None:
        if self.fd is None:
            return
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass
        self.fd = None


def run_preregistered_productive_session_v1(
    *,
    repo_root: Path,
    campaign_id: str,
    preregistration_id: str,
    preregistration_digest: str,
    session_id: str,
    authorization_id: str,
    authorization_digest: str,
    authorization_artifact_path: Path,
    repository_sha: str,
    expected_branch: str = EXPECTED_BRANCH_DEFAULT,
    venue: str = BOUND_VENUE,
    instrument_id: str = BOUND_INSTRUMENT_ID,
    market_data_scope: str = BOUND_VENUE_SCOPE,
    evidence_scope: str = BOUND_EVIDENCE_SCOPE,
    max_cycles: Optional[int] = None,
    evidence_root: Optional[Path] = None,
    git_baseline: Optional[GitBaselineSnapshotV1] = None,
    http_fetcher: Optional[HttpFetcher] = None,
    mark_source_kind: str = "okx_eea_public_rest",
    poll_interval_seconds: float = 0.0,
    side_effect_probe: Optional[SideEffectProbeV1] = None,
    preflight_only: bool = False,
    require_exact_session_id: Optional[str] = None,
    instruments_inventory: Optional[Any] = None,
    md_sleep: Optional[Any] = None,
    md_monotonic_clock: Optional[Any] = None,
) -> dict[str, Any]:
    """Execute one preregistered productive evidence session fail-closed.

    Lifecycle:
      1-7) static preflight (no mutation / network)
      8) atomic authorization consumption for exact session_id
      9) session lock + start
      9b) canonical venue instrument resolution (no network inventory by default)
      9c) request pacing/budget initialization
      10) paced public MD fetch + accumulation via existing productive bridge consumer
      11) terminal evidence
    """
    probe = side_effect_probe or SideEffectProbeV1()
    root = Path(repo_root)
    evi_root = Path(evidence_root) if evidence_root is not None else root
    reject_offline_synthetic_mark_source_v1(mark_source_kind)

    # Steps 1–7
    preflight = run_static_preflight_v1(
        repo_root=root,
        campaign_id=campaign_id,
        preregistration_id=preregistration_id,
        preregistration_digest=preregistration_digest,
        session_id=session_id,
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        authorization_artifact_path=authorization_artifact_path,
        repository_sha=repository_sha,
        expected_branch=expected_branch,
        venue=venue,
        instrument_id=instrument_id,
        market_data_scope=market_data_scope,
        evidence_scope=evidence_scope,
        max_cycles=max_cycles,
        git_baseline=git_baseline,
        allow_offline_synthetic_mark_source=False,
        evidence_root=evi_root,
        require_exact_session_id=require_exact_session_id,
    )
    probe.record("PREFLIGHT_PASS")

    if preflight_only:
        return {
            "status": "PREFLIGHT_PASS",
            "terminal_state": "PREFLIGHT_ONLY",
            "terminal_verdict": "PREFLIGHT_PASS_NO_EXECUTION",
            "authorization_consumed": False,
            "authorization_consumption_count": 0,
            "session_started": False,
            "market_data_request_occurred": False,
            "session_01_evidence_mutation_occurred": False,
            "productive_ledger_mutation_occurred": False,
            "session_02_mutation_occurred": False,
            "preflight": preflight.to_dict(),
            "side_effect_probe": probe.to_dict(),
            "economic_validity_claimed": False,
            "promotion_authorized": False,
        }

    if http_fetcher is None:
        raise PreregisteredSessionRunnerError("http_fetcher_required_no_silent_real_network")

    if preflight.session_id not in BOUND_SESSION_IDS_V1:
        raise PreregisteredSessionRunnerError("session_id_not_bound")
    # Exact session id — never derive.
    if preflight.session_id != session_id:
        raise PreregisteredSessionRunnerError("session_id_rewritten_forbidden")

    s02_before = _session_02_paths_snapshot_v1(evi_root)
    auth_consumed = False
    consumed_at: Optional[str] = None
    consumption_count = 0
    session_started = False
    md_requested = False
    cycles_executed = 0
    records_appended = 0
    accumulation_report: dict[str, Any] = {}
    integrity: dict[str, Any] = {}
    md_telemetry = PublicMdSourceTelemetryV1()
    lock: Optional[_SessionExclusiveLockV1] = None
    terminal_state = "NOT_STARTED"
    terminal_verdict = "NOT_STARTED"
    blocker = ""
    resolved_venue_instrument_id = BOUND_VENUE_INSTRUMENT_ID
    import time as _time

    sleep_fn = md_sleep or _time.sleep
    mono_fn = md_monotonic_clock or _time.monotonic

    try:
        # Step 8 — consume immediately before irreversible session side effects.
        consume_probe: list[str] = []
        release = consume_campaign_authorization_session_v1(
            authorization_artifact_path=Path(authorization_artifact_path),
            session_id=preflight.session_id,
            evidence_root=evi_root,
            expected_repository_sha=repository_sha,
            expected_campaign_id=campaign_id,
            expected_preregistration_digest=preregistration_digest,
            side_effect_probe=consume_probe,
        )
        if release.session_id != preflight.session_id:
            raise PreregisteredSessionRunnerError("consumption_session_mismatch")
        if release.authorization_id != authorization_id:
            raise PreregisteredSessionRunnerError("consumption_authorization_id_mismatch")
        if release.authorization_digest != authorization_digest:
            raise PreregisteredSessionRunnerError("consumption_authorization_digest_mismatch")
        auth_consumed = True
        consumed_at = release.released_at
        consumption_count = int(release.consumption_index)
        # Re-read consumption ledger for durable count confirmation.
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
            load_campaign_authorization_artifact_v1,
        )

        artifact = load_campaign_authorization_artifact_v1(Path(authorization_artifact_path))
        cons_path = resolve_ledger_path_v1(
            evidence_root=evi_root, relative_or_absolute=artifact.consumption_ledger_path
        )
        durable_count = len(
            [
                r
                for r in load_consumption_records_v1(cons_path)
                if r.get("authorization_id") == authorization_id
            ]
        )
        if durable_count != consumption_count:
            raise PreregisteredSessionRunnerError("consumption_count_mismatch")
        probe.record("AUTHORIZATION_CONSUMED")
        for item in consume_probe:
            probe.record(item)

        # Step 9 — session lock / start (first session-owned side effect after consume)
        lock = _SessionExclusiveLockV1(Path(preflight.session_manifest_path + ".lock"))
        lock.acquire()
        session_started = True
        probe.record("SESSION_STARTED")

        # Step 9b — canonical venue instrument resolution (sealed inventory; no network)
        mapping = resolve_preregistered_session_venue_instrument_v1(
            canonical_instrument_id=instrument_id,
            instruments_inventory=instruments_inventory,
            expected_canonical_instrument_id=BOUND_INSTRUMENT_ID,
        )
        resolved_venue_instrument_id = mapping.venue_instrument_id
        md_telemetry.instrument_binding = binding_evidence_v1(mapping)
        probe.record("VENUE_INSTRUMENT_BOUND")

        # Step 9c — pacing / budget initialization before any network request
        pacing_policy = default_public_md_request_pacing_policy_v1()
        _policy, _budget, attempt_gate = initialize_session_md_controls_v1(
            session_id=preflight.session_id,
            max_cycles=preflight.max_cycles,
            venue_instrument_id=resolved_venue_instrument_id,
            telemetry=md_telemetry,
            policy=pacing_policy,
            sleep=sleep_fn,
            monotonic_clock=mono_fn,
        )
        probe.record("REQUEST_PACING_BUDGET_INITIALIZED")

        # Step 10 — paced public MD + accumulation through existing consumer
        transport, md_telemetry = build_preregistered_public_md_transport_v1(
            fetcher=http_fetcher,
            telemetry=md_telemetry,
            rate_limit_policy=pacing_policy,
            attempt_gate=attempt_gate,
            sleep=sleep_fn,
            monotonic_clock=mono_fn,
            session_id=preflight.session_id,
        )
        transport.open()
        probe.record("TRANSPORT_OPENED")
        samples = collect_public_mark_samples_v1(
            transport=transport,
            cycle_count=preflight.max_cycles,
            venue_instrument_id=resolved_venue_instrument_id,
            canonical_instrument_id=instrument_id,
            poll_interval_seconds=poll_interval_seconds,
            session_id=preflight.session_id,
            telemetry=md_telemetry,
            rate_limit_policy=pacing_policy,
            attempt_gate=attempt_gate,
            sleep=sleep_fn,
            monotonic_clock=mono_fn,
        )
        md_requested = bool(
            md_telemetry.market_data_request_occurred or md_telemetry.fetch_count > 0
        )
        probe.record("MARKET_DATA_FETCHED")
        assert_no_orders_or_credentials_v1(md_telemetry)
        if not samples:
            raise PreregisteredSessionRunnerError("no_public_mark_samples")
        if any(
            not isinstance(s, ProductiveBridgeMarketSampleV1) for s in samples
        ):  # pragma: no cover
            raise PreregisteredSessionRunnerError("invalid_sample_type")

        accumulation_report = run_productive_bridge_accumulation_session_v1(
            session_id=preflight.session_id,
            campaign_id=campaign_id,
            repository_sha=repository_sha,
            samples=samples,
            repo_root=root,
            productive_ledger_path=Path(preflight.productive_ledger_path),
            join_ledger_path=Path(preflight.join_ledger_path),
            quarantine_ledger_path=Path(preflight.quarantine_ledger_path),
            venue=BRIDGE_SAMPLE_VENUE,
            canonical_instrument_id=instrument_id,
            venue_instrument_id=resolved_venue_instrument_id,
            typed_volatility_persistence_path=Path(preflight.typed_volatility_persistence_path),
            campaign_authorization_artifact_path=Path(authorization_artifact_path),
            campaign_authorization_evidence_root=evi_root,
            require_campaign_authorization=True,
        )
        probe.record("ACCUMULATION_COMPLETE")
        cycles_executed = int(accumulation_report.get("cycles_executed") or 0)
        records_appended = int(accumulation_report.get("records_appended") or 0)
        md_telemetry.counters.completed_accumulation_cycle_count = cycles_executed
        integrity = dict(accumulation_report.get("integrity") or {})
        transport.close()

        terminal_state = "COMPLETED"
        terminal_verdict = "SESSION_EVIDENCE_ACCUMULATED"
        status = "PASS"
    except Exception as exc:  # noqa: BLE001
        blocker = str(exc)
        md_requested = bool(
            md_requested
            or md_telemetry.market_data_request_occurred
            or md_telemetry.fetch_count > 0
        )
        if auth_consumed:
            terminal_state = "FAIL_CLOSED_AFTER_CONSUMPTION"
            terminal_verdict = "FAIL_CLOSED_AFTER_AUTHORIZATION_CONSUMPTION"
            status = "FAIL"
            probe.record("FAIL_CLOSED_AFTER_CONSUMPTION")
        else:
            terminal_state = "FAIL_CLOSED_BEFORE_CONSUMPTION"
            terminal_verdict = "FAIL_CLOSED_BEFORE_AUTHORIZATION_CONSUMPTION"
            status = "BLOCKED"
            probe.record("FAIL_CLOSED_BEFORE_CONSUMPTION")
    finally:
        if lock is not None:
            lock.release()

    session_02_mutated = not _assert_session_02_unchanged_v1(s02_before, evi_root)
    if session_02_mutated:
        status = "FAIL"
        terminal_state = "FAIL_CLOSED_SESSION_02_ISOLATION"
        terminal_verdict = "SESSION_02_MUTATION_DETECTED"
        blocker = (blocker + ";session_02_mutation_detected").strip(";")

    prod_path = Path(preflight.productive_ledger_path)
    join_path = Path(preflight.join_ledger_path)
    productive_mutated = prod_path.exists() and prod_path.stat().st_size > 0
    session_01_mutated = bool(
        productive_mutated
        or Path(preflight.typed_volatility_persistence_path).exists()
        or Path(preflight.session_manifest_path).exists()
    )
    # Prefer ledger integrity when ledgers exist.
    if prod_path.exists() or join_path.exists():
        try:
            integrity = assert_ledger_integrity_matrix_v1(
                productive_ledger_path=prod_path, join_ledger_path=join_path
            )
        except Exception as exc:  # noqa: BLE001
            integrity = {"ledger_integrity_error": str(exc)}
            if status == "PASS":
                status = "FAIL"
                terminal_state = "FAIL_CLOSED_INTEGRITY"
                terminal_verdict = "LEDGER_INTEGRITY_FAILED"

    integrity_manifest = build_integrity_manifest_v1(
        session_id=preflight.session_id,
        campaign_id=campaign_id,
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        preregistration_digest=preregistration_digest,
        repository_sha=repository_sha,
        authorization_consumed=auth_consumed,
        cycles_executed=cycles_executed,
        records_appended=records_appended,
        ledger_integrity=integrity,
        terminal_state=terminal_state,
        terminal_verdict=terminal_verdict,
    )
    if auth_consumed or session_started:
        write_session_terminal_evidence_v1(
            session_manifest_path=Path(preflight.session_manifest_path),
            payload={
                "session_id": preflight.session_id,
                "campaign_id": campaign_id,
                "preregistration_id": BOUND_PREREGISTRATION_ID,
                "preregistration_digest": BOUND_PREREGISTRATION_DIGEST_V1,
                "authorization_id": authorization_id,
                "authorization_digest": authorization_digest,
                "authorization_consumed": auth_consumed,
                "authorization_consumed_at": consumed_at,
                "authorization_consumption_count": consumption_count,
                "session_started": session_started,
                "market_data_request_occurred": md_requested,
                "terminal_state": terminal_state,
                "terminal_verdict": terminal_verdict,
                "blocker": blocker,
                "integrity_manifest": integrity_manifest,
                "md_telemetry": md_telemetry.to_dict(),
                "side_effect_probe": probe.to_dict(),
                "session_02_id": SESSION_02_ID,
                "session_02_mutation_occurred": session_02_mutated,
                "target_was_session_01": preflight.session_id == SESSION_01_ID,
            },
        )

    result = RunnerResultV1(
        status=status,
        terminal_state=terminal_state,
        terminal_verdict=terminal_verdict,
        session_id=preflight.session_id,
        campaign_id=campaign_id,
        authorization_consumed=auth_consumed,
        authorization_consumed_at=consumed_at,
        authorization_consumption_count=consumption_count,
        session_started=session_started,
        market_data_request_occurred=md_requested,
        session_01_evidence_mutation_occurred=(
            session_01_mutated if preflight.session_id == SESSION_01_ID else False
        ),
        productive_ledger_mutation_occurred=productive_mutated,
        session_02_mutation_occurred=session_02_mutated,
        cycles_executed=cycles_executed,
        records_appended=records_appended,
        public_endpoints_only=not md_telemetry.private_endpoint_request_occurred,
        private_endpoint_request_occurred=md_telemetry.private_endpoint_request_occurred,
        order_request_occurred=md_telemetry.order_request_occurred,
        credential_access_occurred=md_telemetry.credential_access_occurred,
        integrity=integrity_manifest,
        side_effect_probe=probe.to_dict(),
        blocker=blocker,
        accumulation_report=accumulation_report,
    )
    out = result.to_dict()
    out["preflight"] = preflight.to_dict()
    out["cli_mode_owner"] = "productive-preregistered-session-run"
    out["productive_bridge_accumulate_is_not_preregistered_session_runner"] = True
    return out
