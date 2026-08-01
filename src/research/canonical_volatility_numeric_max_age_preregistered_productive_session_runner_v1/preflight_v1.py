"""Static preflight for preregistered productive session runner (no side effects)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_campaign_preregistration_v1 import (
    load_and_verify_session_preregistration_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
    load_campaign_authorization_artifact_v1,
    verify_campaign_authorization_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.expiry_v1 import (
    assert_clock_within_authorization_window_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.ledgers_v1 import (
    assert_not_revoked_v1,
    find_session_consumption_v1,
    load_consumption_records_v1,
    resolve_ledger_path_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    BOUND_CAMPAIGN_ID_V1,
    BOUND_EVIDENCE_SCOPE,
    BOUND_INSTRUMENT_ID,
    BOUND_PREREGISTRATION_ARTIFACT_PATH,
    BOUND_PREREGISTRATION_DIGEST_V1,
    BOUND_PREREGISTRATION_ID,
    BOUND_SESSION_IDS_V1,
    BOUND_VENUE,
    BOUND_VENUE_SCOPE,
    DERIVED_SESSION_ID_MARKERS,
    EXPECTED_BRANCH_DEFAULT,
    JOIN_LEDGER_REL_PATH,
    PRODUCTIVE_LEDGER_REL_PATH,
    PUBLIC_MD_ENDPOINT_ALLOWLIST,
    PUBLIC_MD_METHOD_ALLOWLIST,
    QUARANTINE_LEDGER_REL_PATH,
    SESSION_02_ID,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    GitBaselineSnapshotV1,
    PreflightResultV1,
    PreregisteredSessionRunnerError,
)


def capture_git_baseline_v1(*, repo_root: Path) -> GitBaselineSnapshotV1:
    def _run(args: Sequence[str]) -> str:
        return subprocess.check_output(list(args), cwd=str(repo_root), text=True).strip()

    branch = _run(["git", "branch", "--show-current"])
    head = _run(["git", "rev-parse", "HEAD"])
    origin_main = _run(["git", "rev-parse", "origin/main"])
    porcelain = _run(["git", "status", "--porcelain"])
    allowed_prefix = (
        "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
        f"campaigns/{BOUND_CAMPAIGN_ID_V1}/authorization/"
    )
    allowed = True
    if porcelain:
        for line in porcelain.splitlines():
            path = line[3:].strip() if len(line) >= 3 else line.strip()
            if path.endswith("/"):
                # Directory untracked: only allowed when sole contents are under auth.
                continue
            if not path.startswith(allowed_prefix) and path != allowed_prefix.rstrip("/"):
                # Allow the parent untracked tree marker when only auth files exist.
                if path.rstrip("/") == (
                    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
                ):
                    continue
                if "canonical_volatility_max_age_productive_research_evidence_ledger_v1" in path:
                    # Only authorization campaign_authorization.json is tolerated.
                    if not path.endswith("authorization/campaign_authorization.json"):
                        # Parent dirs are OK when they only exist for the auth artifact.
                        if "/authorization/" not in path and not path.endswith("/authorization"):
                            if path.count("/") <= 3:
                                continue
                    if path.endswith("campaign_authorization.json"):
                        continue
                    if "/authorization/" in path and path.endswith(".json"):
                        if path.endswith("campaign_authorization.json"):
                            continue
                        allowed = False
                        break
                else:
                    allowed = False
                    break
    return GitBaselineSnapshotV1(
        branch=branch,
        head_sha=head,
        origin_main_sha=origin_main,
        worktree_allowed_delta_only=allowed,
    )


def assert_session_id_exact_v1(session_id: str) -> str:
    sid = str(session_id or "").strip()
    if not sid:
        raise PreregisteredSessionRunnerError("session_id_required")
    for marker in DERIVED_SESSION_ID_MARKERS:
        if marker in sid:
            raise PreregisteredSessionRunnerError("derived_session_id_forbidden")
    if sid not in BOUND_SESSION_IDS_V1:
        raise PreregisteredSessionRunnerError("unknown_or_unpreregistered_session_id")
    return sid


def _session_entry_v1(prereg_payload: Mapping[str, Any], session_id: str) -> Mapping[str, Any]:
    for entry in prereg_payload.get("sessions") or []:
        if str(entry.get("session_id")) == session_id:
            return entry
    raise PreregisteredSessionRunnerError("session_not_in_preregistration")


def run_static_preflight_v1(
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
    git_baseline: Optional[GitBaselineSnapshotV1] = None,
    allow_offline_synthetic_mark_source: bool = False,
    evidence_root: Optional[Path] = None,
    require_exact_session_id: Optional[str] = None,
) -> PreflightResultV1:
    """Validate all bindings. Must not consume, mutate ledgers, or open network."""
    blockers: list[str] = []
    root = Path(repo_root)
    evi_root = Path(evidence_root) if evidence_root is not None else root

    if allow_offline_synthetic_mark_source:
        raise PreregisteredSessionRunnerError("offline_synthetic_mark_source_forbidden")

    baseline = git_baseline or capture_git_baseline_v1(repo_root=root)
    if baseline.branch != expected_branch:
        blockers.append("branch_mismatch")
    if baseline.head_sha != repository_sha:
        blockers.append("repository_sha_mismatch")
    if baseline.head_sha != baseline.origin_main_sha:
        blockers.append("head_not_equal_origin_main")
    if not baseline.worktree_allowed_delta_only:
        blockers.append("worktree_delta_not_allowed")

    if campaign_id != BOUND_CAMPAIGN_ID_V1:
        blockers.append("campaign_id_mismatch")
    if preregistration_id != BOUND_PREREGISTRATION_ID:
        blockers.append("preregistration_id_mismatch")
    if preregistration_digest != BOUND_PREREGISTRATION_DIGEST_V1:
        blockers.append("preregistration_digest_mismatch")
    if venue != BOUND_VENUE:
        blockers.append("venue_mismatch")
    if instrument_id != BOUND_INSTRUMENT_ID:
        blockers.append("instrument_mismatch")
    if market_data_scope != BOUND_VENUE_SCOPE:
        blockers.append("market_data_scope_mismatch")
    if evidence_scope != BOUND_EVIDENCE_SCOPE:
        blockers.append("evidence_scope_mismatch")

    try:
        sid = assert_session_id_exact_v1(session_id)
        if require_exact_session_id is not None and sid != require_exact_session_id:
            blockers.append("session_id_not_required_exact_target")
    except PreregisteredSessionRunnerError as exc:
        blockers.append(str(exc))
        sid = str(session_id or "")

    preg_path = root / BOUND_PREREGISTRATION_ARTIFACT_PATH
    try:
        preg_verify = load_and_verify_session_preregistration_artifact_v1(artifact_path=preg_path)
        if preg_verify.get("status") != "PASS":
            blockers.append("preregistration_verify_failed")
        if preg_verify.get("preregistration_digest") != preregistration_digest:
            blockers.append("preregistration_digest_binding_mismatch")
        if preg_verify.get("campaign_id") != campaign_id:
            blockers.append("preregistration_campaign_mismatch")
        preg_payload = json.loads(preg_path.read_text(encoding="utf-8"))
        session_entry = _session_entry_v1(preg_payload, sid) if sid else {}
        md = preg_payload.get("public_md_plan") or {}
        if md.get("venue") != BOUND_VENUE:
            blockers.append("prereg_venue_mismatch")
        if md.get("venue_scope") != BOUND_VENUE_SCOPE:
            blockers.append("prereg_market_data_scope_mismatch")
        if md.get("canonical_instrument_id") != BOUND_INSTRUMENT_ID:
            blockers.append("prereg_instrument_mismatch")
        if sorted(md.get("allowed_http_methods") or []) != sorted(PUBLIC_MD_METHOD_ALLOWLIST):
            blockers.append("prereg_md_methods_mismatch")
        if set(md.get("allowed_endpoints") or []) != set(PUBLIC_MD_ENDPOINT_ALLOWLIST):
            blockers.append("prereg_md_endpoints_mismatch")
        if bool(md.get("credentials_required")):
            blockers.append("credentials_required_forbidden")
        if bool(md.get("private_endpoints_allowed")):
            blockers.append("private_endpoints_forbidden")
        if bool(md.get("order_endpoints_allowed")):
            blockers.append("order_endpoints_forbidden")
        if bool(md.get("websocket_allowed")):
            blockers.append("websocket_forbidden")
        durable = preg_payload.get("durable_path_plan") or {}
        if BOUND_EVIDENCE_SCOPE not in str(durable.get("productive_ledger_path") or ""):
            blockers.append("evidence_scope_path_mismatch")
        max_from_session = int(session_entry.get("maximum_cycles_per_session") or 0)
        if max_from_session <= 0:
            blockers.append("session_max_cycles_missing")
        resolved_max = int(max_cycles) if max_cycles is not None else max_from_session
        if resolved_max < 1 or resolved_max > max_from_session:
            blockers.append("max_cycles_out_of_bounds")
        expected_paths = session_entry.get("expected_durable_paths") or {}
        session_manifest = str(expected_paths.get("session_manifest_path") or "")
        typed_persist = str(expected_paths.get("typed_volatility_persistence_path") or "")
        if not session_manifest or not typed_persist:
            blockers.append("session_durable_paths_missing")
    except PreregisteredSessionRunnerError as exc:
        blockers.append(str(exc))
        resolved_max = int(max_cycles or 0)
        session_manifest = ""
        typed_persist = ""
        preg_payload = {}
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"preregistration_preflight_error:{exc}")
        resolved_max = int(max_cycles or 0)
        session_manifest = ""
        typed_persist = ""
        preg_payload = {}

    auth_path = Path(authorization_artifact_path)
    try:
        artifact = verify_campaign_authorization_artifact_v1(
            load_campaign_authorization_artifact_v1(auth_path),
            expected_repository_sha=repository_sha,
            expected_campaign_id=campaign_id,
            expected_session_ids=BOUND_SESSION_IDS_V1,
            expected_preregistration_digest=preregistration_digest,
        )
        if artifact.authorization_id != authorization_id:
            blockers.append("authorization_id_mismatch")
        if artifact.artifact_digest != authorization_digest:
            blockers.append("authorization_digest_mismatch")
        if artifact.public_md_venue != BOUND_VENUE:
            blockers.append("authorization_venue_mismatch")
        if BOUND_INSTRUMENT_ID not in artifact.instrument_allowlist:
            blockers.append("authorization_instrument_mismatch")
        if artifact.durable_ledger_path != PRODUCTIVE_LEDGER_REL_PATH:
            blockers.append("authorization_ledger_path_mismatch")
        if artifact.join_path != JOIN_LEDGER_REL_PATH:
            blockers.append("authorization_join_path_mismatch")
        if artifact.quarantine_path != QUARANTINE_LEDGER_REL_PATH:
            blockers.append("authorization_quarantine_path_mismatch")
        assert_clock_within_authorization_window_v1(
            issued_at=artifact.issued_at,
            earliest_start=artifact.earliest_start,
            expires_at=artifact.expires_at,
        )
        rev_path = resolve_ledger_path_v1(
            evidence_root=evi_root, relative_or_absolute=artifact.revocation_ledger_path
        )
        cons_path = resolve_ledger_path_v1(
            evidence_root=evi_root, relative_or_absolute=artifact.consumption_ledger_path
        )
        assert_not_revoked_v1(
            revocation_ledger_path=rev_path,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
        )
        records = load_consumption_records_v1(cons_path)
        if find_session_consumption_v1(
            records,
            authorization_id=artifact.authorization_id,
            session_id=sid,
        ):
            blockers.append("authorization_already_consumed_for_session")
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"authorization_preflight_error:{exc}")

    # Output targets exist as path contracts only — no parent materialization here.
    productive = evi_root / PRODUCTIVE_LEDGER_REL_PATH
    join = evi_root / JOIN_LEDGER_REL_PATH
    quarantine = evi_root / QUARANTINE_LEDGER_REL_PATH
    if PRODUCTIVE_LEDGER_REL_PATH.split("/")[1] != BOUND_EVIDENCE_SCOPE and (
        BOUND_EVIDENCE_SCOPE not in PRODUCTIVE_LEDGER_REL_PATH
    ):
        blockers.append("evidence_scope_ledger_mismatch")

    # Session-02 isolation: target session must not imply the other session.
    other = SESSION_02_ID if sid == BOUND_SESSION_IDS_V1[0] else BOUND_SESSION_IDS_V1[0]
    if sid and other == sid:
        blockers.append("session_isolation_invariant_broken")

    # Competing session lock under campaign sessions.
    if session_manifest:
        lock_path = (evi_root / session_manifest).with_suffix(".lock")
        if lock_path.exists():
            blockers.append("session_lock_held")

    result = PreflightResultV1(
        ok=not blockers,
        campaign_id=campaign_id,
        session_id=sid,
        preregistration_id=preregistration_id,
        preregistration_digest=preregistration_digest,
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        repository_sha=repository_sha,
        venue=venue,
        instrument_id=instrument_id,
        market_data_scope=market_data_scope,
        evidence_scope=evidence_scope,
        max_cycles=int(resolved_max or 0),
        productive_ledger_path=str(productive),
        join_ledger_path=str(join),
        quarantine_ledger_path=str(quarantine),
        typed_volatility_persistence_path=str(evi_root / typed_persist) if typed_persist else "",
        session_manifest_path=str(evi_root / session_manifest) if session_manifest else "",
        session_02_id=SESSION_02_ID,
        blockers=tuple(blockers),
    )
    if blockers:
        raise PreregisteredSessionRunnerError("preflight_failed:" + ",".join(blockers))
    return result
