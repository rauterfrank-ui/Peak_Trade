#!/usr/bin/env python3
"""CLI: productive max-age research evidence accumulation (non-enforcing)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "src"):
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.coverage_v1 import (  # noqa: E402
    evaluate_coverage_from_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.runtime_v1 import (  # noqa: E402
    accumulate_from_cycles_batch_v1,
    bind_accumulation_state_v1,
    reconstruct_coverage_from_ledgers_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (  # noqa: E402
    coverage_summary_v1,
    load_research_evidence_records_v1,
)


def _git_sha(repo_root: Path) -> str:
    out = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        text=True,
    ).strip()
    return out


def _synthetic_probe_cycles_v1() -> list[dict]:
    """Deterministic offline probe cycles for operator-controlled dry accumulation.

    These are typed fixture cycles (event-time based), not wallclock/poll inventions.
    """
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def _cycle(
        *,
        session_id: str,
        cycle_id: str,
        regime_id: str,
        slope: float,
        age: float,
        offset: int,
        estimate_id: str,
        observation_count: int,
    ) -> dict:
        ref = t0.timestamp() + offset
        as_of = ref - age
        ref_iso = datetime.fromtimestamp(ref, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        as_of_iso = (
            datetime.fromtimestamp(as_of, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        )
        source = f"src_{estimate_id}"
        return {
            "session_id": session_id,
            "cycle_id": cycle_id,
            "instrument_id": "ETH-USD_UM_XPERP-310404",
            "venue": "OKX",
            "venue_instrument_id": "ETH-USD-SWAP",
            "market_event_time": ref_iso,
            "decision_outcome": "HOLD",
            "selected_side": "FLAT",
            "economic_metrics": {"net_pnl": 0.0},
            "feature_regime": {
                "ok": True,
                "warmup_complete": True,
                "regime_id": regime_id,
                "regime_state_source": "CANONICAL_RUNTIME_PIPELINE",
                "trend_features": {"slope": slope, "strength": 0.2},
                "momentum_features": {"rsi": 50.0, "roc": slope},
                "liquidity_features": {"depth_score": 1.0},
                "market_structure_features": {"range_ratio": 0.01},
                "volatility_estimate": 0.02,
                "mark_price": 3500.0,
                "blockers": [],
                "default_regime_fallback_active": False,
            },
            "canonical_volatility_typed_binding": {
                "session_id": session_id,
                "cycle_id": cycle_id,
                "instrument_id": "ETH-USD_UM_XPERP-310404",
                "venue": "OKX",
                "venue_instrument_id": "ETH-USD-SWAP",
                "producer_outcome": "PRODUCED",
                "estimate_present": True,
                "observation_count": observation_count,
                "source_digest": source,
                "source_estimate_id": estimate_id,
                "estimate_id": estimate_id,
                "volatility_value": 0.02,
                "volatility_unit": "DECIMAL_FRACTION",
                "volatility_horizon_seconds": 3600.0,
                "volatility_estimator": "TYPED_RUNTIME_PRODUCER",
                "reuse_status": "FRESHLY_PRODUCED",
                "restart_status": "NOT_APPLICABLE",
                "fallback_used": False,
            },
            "double_play_typed_volatility_presence_gate": {
                "session_id": session_id,
                "cycle_id": cycle_id,
                "instrument_id": "ETH-USD_UM_XPERP-310404",
                "regime_id": regime_id,
                "max_age_policy_evidence": {
                    "estimate_as_of_event_time": as_of_iso,
                    "reference_event_time": ref_iso,
                    "computed_age_seconds": float(age),
                    "max_age_status": "AGE_COMPUTED_THRESHOLD_UNRESOLVED",
                    "threshold_status": "UNRESOLVED_MAX_AGE",
                    "presence_status": "PRESENT",
                    "clock_trust_status": "TRUSTED",
                    "data_integrity_status": "TRUSTED",
                    "reuse_status": "FRESHLY_PRODUCED",
                    "restart_status": "NOT_APPLICABLE",
                    "source_digest": source,
                    "decision": "AGE_COMPUTED",
                    "reason_code": "VOLATILITY_ESTIMATE_AGE_UNRESOLVED",
                    "enforcement_applied": False,
                    "numeric_threshold_selected": False,
                    "session_id": session_id,
                    "cycle_id": cycle_id,
                    "instrument_id": "ETH-USD_UM_XPERP-310404",
                    "regime_id": regime_id,
                },
            },
        }

    cycles = [
        _cycle(
            session_id="sess-a",
            cycle_id="c-a1",
            regime_id="trending",
            slope=0.01,
            age=60,
            offset=0,
            estimate_id="est-a1",
            observation_count=60,
        ),
        _cycle(
            session_id="sess-a",
            cycle_id="c-a2",
            regime_id="trending",
            slope=0.01,
            age=120,
            offset=120,
            estimate_id="est-a1",
            observation_count=60,
        ),
        _cycle(
            session_id="sess-a",
            cycle_id="c-a3",
            regime_id="ranging",
            slope=0.0,
            age=180,
            offset=240,
            estimate_id="est-a2",
            observation_count=60,
        ),
        _cycle(
            session_id="sess-a",
            cycle_id="c-a4",
            regime_id="volatile",
            slope=0.0,
            age=240,
            offset=360,
            estimate_id="est-a3",
            observation_count=60,
        ),
    ]
    # Second independent session.
    for i, age in enumerate((90, 150, 210, 270), start=1):
        cycles.append(
            _cycle(
                session_id="sess-b",
                cycle_id=f"c-b{i}",
                regime_id="ranging" if i % 2 else "trending",
                slope=-0.01 if i % 2 == 0 else 0.0,
                age=age,
                offset=1000 + i * 120,
                estimate_id=f"est-b{i}",
                observation_count=60,
            )
        )
    return cycles


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Accumulate productive canonical-volatility max-age research evidence. "
            "Never selects or enforces a numeric threshold."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--productive-ledger-path", type=Path, default=None)
    parser.add_argument("--join-ledger-path", type=Path, default=None)
    parser.add_argument("--quarantine-ledger-path", type=Path, default=None)
    parser.add_argument("--repository-sha", type=str, default=None)
    parser.add_argument(
        "--mode",
        choices=(
            "probe-accumulate",
            "productive-bridge-accumulate",
            "coverage-only",
            "verify-join-load",
            "evaluability-report",
            "render-session-preregistration",
            "verify-session-preregistration",
            "render-campaign-authorization",
            "verify-campaign-authorization",
            "revoke-campaign-authorization",
            "consume-campaign-authorization",
            "productive-preregistered-session-run",
            "additional-evidence-s03-session-run",
        ),
        default="probe-accumulate",
    )
    parser.add_argument(
        "--session-preregistration-artifact",
        type=Path,
        default=None,
        help="Optional artifact path for verify-session-preregistration.",
    )
    parser.add_argument(
        "--campaign-authorization-artifact",
        type=Path,
        default=None,
        help="Campaign authorization artifact path (no productive default).",
    )
    parser.add_argument(
        "--campaign-authorization-output",
        type=Path,
        default=None,
        help="Output path for render-campaign-authorization (required; no default).",
    )
    parser.add_argument(
        "--issued-at",
        type=str,
        default=None,
        help="UTC issued_at for render-campaign-authorization (required; no default).",
    )
    parser.add_argument(
        "--earliest-start",
        type=str,
        default=None,
        help="UTC earliest_start for render-campaign-authorization (required; no default).",
    )
    parser.add_argument(
        "--preregistration-digest",
        type=str,
        default=None,
        help="Preregistration digest binding (required for render; no default).",
    )
    parser.add_argument(
        "--session-ids",
        type=str,
        default=None,
        help="Comma-separated authorized session IDs (required for render; no default).",
    )
    parser.add_argument(
        "--authorization-evidence-root",
        type=Path,
        default=None,
        help="Root for resolving revocation/consumption ledger relative paths.",
    )
    parser.add_argument(
        "--revocation-reason",
        type=str,
        default=None,
        help="Reason for revoke-campaign-authorization.",
    )
    parser.add_argument(
        "--operator-reference",
        type=str,
        default=None,
        help="Operator reference for revoke-campaign-authorization.",
    )
    parser.add_argument(
        "--preregistration-id",
        type=str,
        default=None,
        help="Preregistration capability id for productive-preregistered-session-run.",
    )
    parser.add_argument(
        "--authorization-id",
        type=str,
        default=None,
        help="Authorization id binding for productive-preregistered-session-run.",
    )
    parser.add_argument(
        "--authorization-digest",
        type=str,
        default=None,
        help="Authorization artifact digest for productive-preregistered-session-run.",
    )
    parser.add_argument(
        "--expected-branch",
        type=str,
        default="main",
        help="Expected git branch for productive-preregistered-session-run.",
    )
    parser.add_argument(
        "--venue",
        type=str,
        default=None,
        help="Venue binding for productive-preregistered-session-run (required in that mode).",
    )
    parser.add_argument(
        "--instrument-id",
        type=str,
        default=None,
        help="Instrument binding for productive-preregistered-session-run.",
    )
    parser.add_argument(
        "--market-data-scope",
        type=str,
        default=None,
        help="Market-data scope for productive-preregistered-session-run.",
    )
    parser.add_argument(
        "--evidence-scope",
        type=str,
        default=None,
        help="Evidence scope for productive-preregistered-session-run.",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="Optional cycle bound (<= preregistered session maximum) for session-run.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run productive-preregistered-session-run preflight without consume/execute.",
    )
    parser.add_argument(
        "--enable-real-public-md-fetcher",
        action="store_true",
        help=(
            "Explicitly enable real OKX-EEA public GET fetcher for "
            "productive-preregistered-session-run (forbidden during capability merge)."
        ),
    )
    parser.add_argument(
        "--s03-offline-capability-probe",
        action="store_true",
        help=(
            "Run Additional-Evidence S03 offline capability probe "
            "(no production auth consume / no real network)."
        ),
    )
    parser.add_argument(
        "--s03-authorization-artifact",
        type=Path,
        default=None,
        help="Auth-v2 artifact path for additional-evidence-s03-session-run.",
    )
    parser.add_argument(
        "--s03-offline-probe-tmp-root",
        type=Path,
        default=None,
        help="Temporary root for S03 offline capability probe artifacts.",
    )
    parser.add_argument("--session-id", type=str, default="operator-probe-session")
    parser.add_argument(
        "--campaign-id",
        type=str,
        default=None,
        help="Required for productive-bridge-accumulate / campaign authorization modes.",
    )
    parser.add_argument(
        "--samples-per-session",
        type=int,
        default=62,
        help="Deterministic productive mark samples per session (bridge path).",
    )
    parser.add_argument(
        "--session-count",
        type=int,
        default=2,
        help="Independent productive sessions for productive-bridge-accumulate.",
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=None,
        help="Optional isolated evidence root (defaults to repo default ledger paths).",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    sha = args.repository_sha or _git_sha(repo_root)

    if args.mode == "render-session-preregistration":
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
            SESSION_PREREGISTRATION_RENDER_CLI_MODE,
        )
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_campaign_preregistration_v1 import (
            render_session_preregistration_v1,
        )

        payload = render_session_preregistration_v1()
        payload["cli_mode"] = SESSION_PREREGISTRATION_RENDER_CLI_MODE
        print(json.dumps(payload, sort_keys=True, indent=2, default=str))
        return 0

    if args.mode == "verify-session-preregistration":
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
            SESSION_PREREGISTRATION_ARTIFACT_REL_PATH,
            SESSION_PREREGISTRATION_VERIFY_CLI_MODE,
        )
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_campaign_preregistration_v1 import (
            load_and_verify_session_preregistration_artifact_v1,
            verify_productive_evidence_campaign_session_preregistration_v1,
        )

        artifact = args.session_preregistration_artifact or (
            repo_root / SESSION_PREREGISTRATION_ARTIFACT_REL_PATH
        )
        if artifact.is_file():
            result = load_and_verify_session_preregistration_artifact_v1(artifact_path=artifact)
            result["artifact_path"] = str(artifact)
        else:
            result = verify_productive_evidence_campaign_session_preregistration_v1()
            result["artifact_path"] = None
        result["cli_mode"] = SESSION_PREREGISTRATION_VERIFY_CLI_MODE
        print(json.dumps(result, sort_keys=True, indent=2, default=str))
        return 0 if result.get("status") == "PASS" else 1

    if args.mode == "render-campaign-authorization":
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
            build_campaign_authorization_artifact_v1,
            write_campaign_authorization_artifact_v1,
        )
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
            RENDER_CLI_MODE,
        )

        if not args.campaign_authorization_output:
            raise SystemExit("campaign_authorization_output_required")
        if not args.repository_sha:
            raise SystemExit("repository_sha_required_no_default")
        if not args.campaign_id:
            raise SystemExit("campaign_id_required_no_default")
        if not args.session_ids:
            raise SystemExit("session_ids_required_no_default")
        if not args.preregistration_digest:
            raise SystemExit("preregistration_digest_required_no_default")
        if not args.issued_at:
            raise SystemExit("issued_at_required_no_default")
        if not args.earliest_start:
            raise SystemExit("earliest_start_required_no_default")
        session_ids = [s.strip() for s in str(args.session_ids).split(",") if s.strip()]
        artifact = build_campaign_authorization_artifact_v1(
            repository_sha=str(args.repository_sha),
            campaign_id=str(args.campaign_id),
            session_ids=session_ids,
            preregistration_digest=str(args.preregistration_digest),
            issued_at=str(args.issued_at),
            earliest_start=str(args.earliest_start),
        )
        written = write_campaign_authorization_artifact_v1(
            output_path=Path(args.campaign_authorization_output),
            artifact=artifact,
        )
        result = {
            "cli_mode": RENDER_CLI_MODE,
            "status": "PASS",
            "output_path": str(args.campaign_authorization_output),
            "artifact_digest": written.artifact_digest,
            "authorization_id": written.authorization_id,
            "productive_authorization_issued": False,
            "note": "Capability render only; not a productive issuance GO.",
        }
        print(json.dumps(result, sort_keys=True, indent=2, default=str))
        return 0

    if args.mode == "verify-campaign-authorization":
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
            load_campaign_authorization_artifact_v1,
            verify_campaign_authorization_artifact_v1,
        )
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
            VERIFY_CLI_MODE,
        )
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
            CampaignAuthorizationError,
        )

        if not args.campaign_authorization_artifact:
            raise SystemExit("campaign_authorization_artifact_required")
        try:
            artifact = verify_campaign_authorization_artifact_v1(
                load_campaign_authorization_artifact_v1(Path(args.campaign_authorization_artifact)),
                expected_repository_sha=args.repository_sha,
                expected_campaign_id=args.campaign_id,
                expected_session_ids=(
                    [s.strip() for s in str(args.session_ids).split(",") if s.strip()]
                    if args.session_ids
                    else None
                ),
                expected_preregistration_digest=args.preregistration_digest,
            )
            result = {
                "cli_mode": VERIFY_CLI_MODE,
                "status": "PASS",
                "artifact_digest": artifact.artifact_digest,
                "authorization_id": artifact.authorization_id,
                "campaign_id": artifact.campaign_id,
                "session_ids": list(artifact.session_ids),
            }
            print(json.dumps(result, sort_keys=True, indent=2, default=str))
            return 0
        except CampaignAuthorizationError as exc:
            print(
                json.dumps(
                    {"cli_mode": VERIFY_CLI_MODE, "status": "FAIL", "blocker": str(exc)},
                    sort_keys=True,
                    indent=2,
                )
            )
            return 1

    if args.mode == "revoke-campaign-authorization":
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
            REVOKE_CLI_MODE,
        )
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.consume_v1 import (
            revoke_campaign_authorization_v1,
        )
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
            CampaignAuthorizationError,
        )

        if not args.campaign_authorization_artifact:
            raise SystemExit("campaign_authorization_artifact_required")
        if not args.revocation_reason:
            raise SystemExit("revocation_reason_required")
        if not args.operator_reference:
            raise SystemExit("operator_reference_required")
        evidence_root = (
            args.authorization_evidence_root.resolve()
            if args.authorization_evidence_root
            else repo_root
        )
        try:
            record = revoke_campaign_authorization_v1(
                authorization_artifact_path=Path(args.campaign_authorization_artifact),
                evidence_root=evidence_root,
                reason=str(args.revocation_reason),
                operator_reference=str(args.operator_reference),
            )
            result = {
                "cli_mode": REVOKE_CLI_MODE,
                "status": "PASS",
                "revocation": record,
                "authorization_source_mutated": False,
            }
            print(json.dumps(result, sort_keys=True, indent=2, default=str))
            return 0
        except CampaignAuthorizationError as exc:
            print(
                json.dumps(
                    {"cli_mode": REVOKE_CLI_MODE, "status": "FAIL", "blocker": str(exc)},
                    sort_keys=True,
                    indent=2,
                )
            )
            return 1

    if args.mode == "consume-campaign-authorization":
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
            CONSUME_CLI_MODE,
        )
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.consume_v1 import (
            consume_campaign_authorization_session_v1,
        )
        from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
            CampaignAuthorizationError,
        )

        if not args.campaign_authorization_artifact:
            raise SystemExit("campaign_authorization_artifact_required")
        if not args.session_id or args.session_id == "operator-probe-session":
            raise SystemExit("session_id_required_no_default_for_consume")
        if not args.campaign_id:
            raise SystemExit("campaign_id_required_no_default")
        evidence_root = (
            args.authorization_evidence_root.resolve()
            if args.authorization_evidence_root
            else repo_root
        )
        try:
            release = consume_campaign_authorization_session_v1(
                authorization_artifact_path=Path(args.campaign_authorization_artifact),
                session_id=str(args.session_id),
                evidence_root=evidence_root,
                expected_repository_sha=args.repository_sha,
                expected_campaign_id=str(args.campaign_id),
                expected_preregistration_digest=args.preregistration_digest,
            )
            result = {
                "cli_mode": CONSUME_CLI_MODE,
                "status": "PASS",
                "runtime_release": release.to_dict(),
                "network_side_effect_occurred": False,
                "evidence_mutation_occurred": False,
                "runtime_session_started": False,
            }
            print(json.dumps(result, sort_keys=True, indent=2, default=str))
            return 0
        except CampaignAuthorizationError as exc:
            print(
                json.dumps(
                    {"cli_mode": CONSUME_CLI_MODE, "status": "FAIL", "blocker": str(exc)},
                    sort_keys=True,
                    indent=2,
                )
            )
            return 1

    if args.mode == "additional-evidence-s03-session-run":
        from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
            CLI_MODE as S03_CLI_MODE,
        )
        from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.offline_probe_v1 import (
            run_offline_capability_probe_v1,
        )
        from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.orchestrator_v1 import (
            run_additional_evidence_s03_productive_session_v1,
        )

        if args.s03_offline_capability_probe:
            tmp_root = args.s03_offline_probe_tmp_root or (repo_root / ".tmp_s03_offline_probe")
            result = run_offline_capability_probe_v1(
                repo_root=repo_root,
                tmp_root=Path(tmp_root),
                execution_sha=str(args.repository_sha or ""),
            )
            result["cli_mode"] = S03_CLI_MODE
            print(json.dumps(result, sort_keys=True, indent=2, default=str))
            return 0 if result.get("ok") else 1
        required = {
            "authorization_id": args.authorization_id,
            "authorization_digest": args.authorization_digest,
            "s03_authorization_artifact": args.s03_authorization_artifact,
            "repository_sha": args.repository_sha,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise SystemExit("s03_session_run_missing:" + ",".join(missing))
        result = run_additional_evidence_s03_productive_session_v1(
            repo_root=repo_root,
            authorization_path=Path(args.s03_authorization_artifact),
            authorization_id=str(args.authorization_id),
            authorization_digest=str(args.authorization_digest),
            repository_sha=str(args.repository_sha),
            evidence_root=args.evidence_root.resolve() if args.evidence_root else repo_root,
            preflight_only=bool(args.preflight_only),
            offline_probe=False,
            enable_real_s03_session_execution=False,
        )
        result["cli_mode"] = S03_CLI_MODE
        print(json.dumps(result, sort_keys=True, indent=2, default=str))
        return 0 if result.get("status") in {"PASS", "PREFLIGHT_PASS"} else 1

    if args.mode == "productive-preregistered-session-run":
        from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
            CLI_MODE as PREREG_SESSION_CLI_MODE,
        )
        from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
            PreregisteredSessionRunnerError,
        )
        from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.runner_v1 import (
            run_preregistered_productive_session_v1,
        )

        required = {
            "campaign_id": args.campaign_id,
            "preregistration_id": args.preregistration_id,
            "preregistration_digest": args.preregistration_digest,
            "session_id": None if args.session_id == "operator-probe-session" else args.session_id,
            "authorization_id": args.authorization_id,
            "authorization_digest": args.authorization_digest,
            "campaign_authorization_artifact": args.campaign_authorization_artifact,
            "repository_sha": args.repository_sha,
            "venue": args.venue,
            "instrument_id": args.instrument_id,
            "market_data_scope": args.market_data_scope,
            "evidence_scope": args.evidence_scope,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise SystemExit("preregistered_session_run_missing:" + ",".join(missing))
        evidence_root = args.evidence_root.resolve() if args.evidence_root else repo_root
        http_fetcher = None
        if args.enable_real_public_md_fetcher:
            if args.preflight_only:
                raise SystemExit("real_public_md_fetcher_incompatible_with_preflight_only")
            from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.real_http_fetcher_v1 import (
                make_real_eea_public_md_fetcher_v1,
            )

            http_fetcher, _telemetry = make_real_eea_public_md_fetcher_v1()
        try:
            result = run_preregistered_productive_session_v1(
                repo_root=repo_root,
                campaign_id=str(args.campaign_id),
                preregistration_id=str(args.preregistration_id),
                preregistration_digest=str(args.preregistration_digest),
                session_id=str(args.session_id),
                authorization_id=str(args.authorization_id),
                authorization_digest=str(args.authorization_digest),
                authorization_artifact_path=Path(args.campaign_authorization_artifact),
                repository_sha=str(args.repository_sha),
                expected_branch=str(args.expected_branch),
                venue=str(args.venue),
                instrument_id=str(args.instrument_id),
                market_data_scope=str(args.market_data_scope),
                evidence_scope=str(args.evidence_scope),
                max_cycles=args.max_cycles,
                evidence_root=evidence_root,
                http_fetcher=http_fetcher,
                preflight_only=bool(args.preflight_only),
            )
            result["cli_mode"] = PREREG_SESSION_CLI_MODE
            print(json.dumps(result, sort_keys=True, indent=2, default=str))
            return 0 if result.get("status") in {"PASS", "PREFLIGHT_PASS"} else 1
        except PreregisteredSessionRunnerError as exc:
            print(
                json.dumps(
                    {
                        "cli_mode": PREREG_SESSION_CLI_MODE,
                        "status": "BLOCKED",
                        "blocker": str(exc),
                        "authorization_consumed": False,
                        "session_started": False,
                        "market_data_request_occurred": False,
                    },
                    sort_keys=True,
                    indent=2,
                )
            )
            return 1

    if args.mode == "productive-bridge-accumulate":
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
            DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
            DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
            DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
            PRODUCTIVE_CLI_MODE,
        )
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
            deterministic_productive_mark_path_v1,
            run_productive_bridge_accumulate_v1,
        )
        from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
            build_ratified_max_age_research_design_contract_v1,
        )

        if not args.campaign_id:
            raise SystemExit("campaign_id_required_for_productive_bridge_accumulate")
        design = build_ratified_max_age_research_design_contract_v1()
        evidence_root = args.evidence_root.resolve() if args.evidence_root else repo_root
        productive = args.productive_ledger_path or (
            evidence_root / DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH
        )
        join = args.join_ledger_path or (evidence_root / DEFAULT_JOIN_LEDGER_RELATIVE_PATH)
        quarantine = args.quarantine_ledger_path or (
            evidence_root / DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH
        )
        session_plans = []
        for idx in range(max(0, int(args.session_count))):
            samples = deterministic_productive_mark_path_v1(
                count=int(args.samples_per_session),
                start_unix=1_700_000_000.0 + idx * 100_000.0,
            )
            session_plans.append(
                {
                    "session_id": f"{args.session_id}-productive-{idx + 1}",
                    "samples": [
                        {
                            "mark_price": s.mark_price,
                            "event_time_unix_seconds": s.event_time_unix_seconds,
                            "receive_time_unix_seconds": s.receive_time_unix_seconds,
                        }
                        for s in samples
                    ],
                    "typed_volatility_persistence_path": str(
                        evidence_root
                        / "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
                        / f"typed_vol_persistence_{idx + 1}.json"
                    ),
                }
            )
        auth_evidence_root = (
            args.authorization_evidence_root.resolve()
            if args.authorization_evidence_root
            else evidence_root
        )
        result = run_productive_bridge_accumulate_v1(
            campaign_id=str(args.campaign_id),
            repository_sha=sha,
            session_plans=session_plans,
            repo_root=repo_root,
            productive_ledger_path=Path(productive),
            join_ledger_path=Path(join),
            quarantine_ledger_path=Path(quarantine),
            campaign_authorization_artifact_path=args.campaign_authorization_artifact,
            campaign_authorization_evidence_root=auth_evidence_root,
            require_campaign_authorization=(
                True if args.campaign_authorization_artifact is not None else None
            ),
        )
        result["cli_mode"] = PRODUCTIVE_CLI_MODE
        result["expected_preregistration_digest"] = design.preregistration_digest
        result["synthetic_probe_used"] = False
        print(json.dumps(result, sort_keys=True, indent=2, default=str))
        return 0 if result.get("status") in {"PASS", "NO_ELIGIBLE_PRODUCTIVE_INPUT"} else 1

    if args.mode == "coverage-only":
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
            DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
            DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
        )

        productive = args.productive_ledger_path or (
            repo_root / DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH
        )
        quarantine = args.quarantine_ledger_path or (
            repo_root / DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH
        )
        result = reconstruct_coverage_from_ledgers_v1(
            productive_ledger_path=productive,
            quarantine_ledger_path=quarantine,
        )
        print(json.dumps(result, sort_keys=True, indent=2, default=str))
        return 0

    if args.mode == "evaluability-report":
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
            DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
            DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
            EVALUABILITY_CLI_MODE,
            REVIEW_MODE_ID,
        )
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.evaluability_v1 import (
            evaluate_productive_evidence_evaluability_v1,
            parameter_decision_prerequisites_v1,
        )
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.ledger_v1 import (
            valid_productive_records_from_ledger_v1,
        )
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.preregistration_v1 import (
            build_productive_evidence_accumulation_preregistration_v1,
            preregistration_matrix_v1,
        )

        productive = args.productive_ledger_path or (
            repo_root / DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH
        )
        quarantine = args.quarantine_ledger_path or (
            repo_root / DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH
        )
        records = (
            valid_productive_records_from_ledger_v1(productive) if Path(productive).exists() else []
        )
        prereg = build_productive_evidence_accumulation_preregistration_v1()
        evaluability = evaluate_productive_evidence_evaluability_v1(records)
        result = {
            "cli_mode": EVALUABILITY_CLI_MODE,
            "review_mode": REVIEW_MODE_ID,
            "status": "PASS",
            "productive_evidence_present": bool(records),
            "evidence_session_count": len(evaluability["session_metrics"]["session_ids"]),
            "blocked_for_parameter_decision": True,
            "evidence_sufficient_for_parameter_decision": False,
            "productive_preregistration_digest": prereg.productive_preregistration_digest,
            "preregistration_matrix": preregistration_matrix_v1(prereg),
            "evaluability": evaluability,
            "parameter_decision_prerequisites": parameter_decision_prerequisites_v1(),
            "quarantine_ledger_path": str(quarantine),
            "productive_ledger_path": str(productive),
            "threshold_status": "UNRESOLVED_MAX_AGE",
            "numeric_threshold_selected": False,
            "enforcement_applied": False,
        }
        print(json.dumps(result, sort_keys=True, indent=2, default=str))
        return 0

    if args.mode == "verify-join-load":
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
            DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
        )

        join_path = args.join_ledger_path or (repo_root / DEFAULT_JOIN_LEDGER_RELATIVE_PATH)
        records = load_research_evidence_records_v1(join_path)
        summary = coverage_summary_v1(records)
        print(
            json.dumps(
                {"join_coverage": summary, "status": "PASS"},
                sort_keys=True,
                indent=2,
                default=str,
            )
        )
        return 0

    # probe-accumulate: two independent sessions for multi-session coverage
    all_cycles = _synthetic_probe_cycles_v1()
    by_session: dict[str, list[dict]] = {}
    for cycle in all_cycles:
        by_session.setdefault(str(cycle["session_id"]), []).append(cycle)

    session_reports = []
    join_path = None
    productive_path = None
    quarantine_path = None
    for session_id, cycles in by_session.items():
        state = bind_accumulation_state_v1(
            session_id=session_id,
            session_start_event_time=str(cycles[0]["market_event_time"]),
            repository_sha=sha,
            venue="OKX",
            canonical_instrument_id="ETH-USD_UM_XPERP-310404",
            venue_instrument_id="ETH-USD-SWAP",
            repo_root=repo_root,
            productive_ledger_path=args.productive_ledger_path,
            join_ledger_path=args.join_ledger_path,
            quarantine_ledger_path=args.quarantine_ledger_path,
        )
        report = accumulate_from_cycles_batch_v1(cycles, state=state, complete_session=True)
        session_reports.append(report)
        join_path = state.join_ledger_path
        productive_path = state.productive_ledger_path
        quarantine_path = state.quarantine_ledger_path

    coverage = evaluate_coverage_from_ledger_v1(
        productive_ledger_path=productive_path,
        quarantine_ledger_path=quarantine_path,
    )
    join_records = load_research_evidence_records_v1(join_path)
    join_coverage = coverage_summary_v1(join_records)
    result = {
        "coverage": coverage.to_dict(),
        "join_coverage": join_coverage,
        "join_ledger_path": str(join_path),
        "productive_ledger_path": str(productive_path),
        "ready_for_research_execution": coverage.ready_for_research_execution,
        "repository_sha": sha,
        "session_reports": session_reports,
        "status": "PASS",
        "threshold_status": "UNRESOLVED_MAX_AGE",
        "numeric_threshold_selected": False,
        "enforcement_applied": False,
    }
    print(json.dumps(result, sort_keys=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
