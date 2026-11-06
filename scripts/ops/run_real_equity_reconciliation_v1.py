"""Explicit private equity capture or offline replay; no trading or capital mint.

Canonical invocation: scripts/pt -m scripts.ops.run_real_equity_reconciliation_v1
Default replay does not acquire a credential or contact the venue. Output is
sanitized; the optional full result must be a new private file outside Git.
"""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

from src.ops.governed_productive_account_equity_authority_producer_v1.real_equity_journal_v1 import (
    PrivateEquityJournalV1,
    collect_real_equity_journal_v1,
    collect_equity_funding_supplement_v1,
    load_real_equity_journal_v1,
    write_private_json_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.real_equity_replay_v1 import (
    load_historical_opening_v1,
    reconcile_real_equity_window_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    load_k1_account_source_config_v1,
    open_k1_account_observation_source_v1,
)


def _encoded(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"


def _private_outside_repo(path, repo_root):
    path = Path(path)
    if not path.is_absolute() or path.resolve().is_relative_to(repo_root.resolve()):
        raise ValueError("PRIVATE_EQUITY_OUTPUT_MUST_BE_ABSOLUTE_OUTSIDE_REPO")
    if not path.parent.is_dir() or path.parent.stat().st_mode & 0o077:
        raise ValueError("PRIVATE_EQUITY_PARENT_MUST_BE_PRIVATE")
    if path.exists() or path.is_symlink():
        raise ValueError("PRIVATE_EQUITY_OUTPUT_ALREADY_EXISTS")
    return path


def main(argv=None):
    root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--config", type=Path, default=root / "config/ops/treasury_k1_account_source_v1.json"
    )
    p.add_argument("--acquire", choices=("trading", "funding"))
    p.add_argument("--private-journal", type=Path)
    p.add_argument("--trading-journal", type=Path)
    p.add_argument("--trading-manifest-sha256")
    p.add_argument("--funding-journal", type=Path)
    p.add_argument("--funding-manifest-sha256")
    p.add_argument("--private-output", type=Path)
    p.add_argument("--expected-report-sha256")
    p.add_argument(
        "--verification-policy",
        type=Path,
        help="Explicit local comparison rule; runtime/capital remain blocked",
    )
    args = p.parse_args(argv)
    config = load_k1_account_source_config_v1(args.config)
    if args.acquire:
        if args.verification_policy:
            p.error("verification policy applies only to offline replay")
        if args.private_journal is None:
            p.error("--acquire requires --private-journal")
        target = _private_outside_repo(args.private_journal, root)
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        journal = PrivateEquityJournalV1(
            target,
            expected_account_identity=config["expected_account_identity"],
            source_commit=commit,
        )
        sources = [
            "src/ops/governed_productive_account_equity_authority_producer_v1/real_equity_journal_v1.py",
            "src/ops/okx_eea_private_account_state_runtime_v1/k1_source_v1.py",
            "src/ops/okx_eea_private_account_state_runtime_v1/startup_source_v1.py",
            "src/ops/full_core_live_path_composition_root_v1/productive_read_only_get_transport_v1.py",
        ]
        hashes = {}
        for i, name in enumerate(sources):
            data = (root / name).read_bytes()
            hashes[name] = sha256(data).hexdigest()
            file = target / f"source_{i:02d}.txt"
            # Exclusive private file creation also for source snapshots.
            fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(data)
        write_private_json_v1(
            target / "source_bindings.json", {"base_head": commit, "sources_sha256": hashes}
        )
        with open_k1_account_observation_source_v1(
            expected_account_identity=config["expected_account_identity"],
            session_id="private-equity-" + args.acquire,
            max_request_count=config["max_request_count"],
        ) as source:
            collect = (
                collect_real_equity_journal_v1
                if args.acquire == "trading"
                else collect_equity_funding_supplement_v1
            )
            manifest = collect(source, journal)
        print(
            json.dumps(
                {
                    "status": manifest["status"],
                    "profile": args.acquire,
                    "manifest_sha256": sha256((target / "manifest.json").read_bytes()).hexdigest(),
                    "private_get_count": len(manifest["entries"]),
                    "orders_or_transfers": 0,
                }
            )
        )
        return 0
    if not all(
        (
            args.trading_journal,
            args.trading_manifest_sha256,
            args.funding_journal,
            args.funding_manifest_sha256,
        )
    ):
        p.error(
            "offline replay requires both journal paths and independently pinned manifest hashes"
        )
    output = _private_outside_repo(args.private_output, root) if args.private_output else None
    tm, trading = load_real_equity_journal_v1(
        args.trading_journal, expected_manifest_sha256=args.trading_manifest_sha256
    )
    fm, funding = load_real_equity_journal_v1(
        args.funding_journal, expected_manifest_sha256=args.funding_manifest_sha256
    )
    opening = load_historical_opening_v1(
        root, expected_account_identity=config["expected_account_identity"]
    )
    result = reconcile_real_equity_window_v1(opening, tm, trading, fm, funding)
    assessment = None
    if args.verification_policy:
        from src.ops.governed_productive_account_equity_authority_producer_v1.equity_verification_policy_v1 import (
            load_equity_verification_policy_v1,
            assess_equity_window_v1,
        )

        assessment = assess_equity_window_v1(
            result, load_equity_verification_policy_v1(args.verification_policy)
        )
    report = (
        result
        if assessment is None
        else {"original_reconciliation": result, "internal_assessment": assessment}
    )
    data = _encoded(report)
    digest = sha256(data).hexdigest()
    if args.expected_report_sha256 and args.expected_report_sha256 != digest:
        raise ValueError("OFFLINE_REPLAY_RESULT_HASH_MISMATCH")
    if output is not None:
        write_private_json_v1(output, report)
    print(
        json.dumps(
            {
                "status": result["status"] if assessment is None else assessment["status"],
                "source_status": result["status"],
                "source_reconciliation_sha256": sha256(_encoded(result)).hexdigest(),
                "report_sha256": digest,
                "observed_at": result["observed_at"],
                "trading_window_posting_count": result["window_trading_posting_count"],
                "funding_window_posting_count": result["funding"]["observed_window_posting_count"],
                "internal_transfer_counterparts": result["funding"][
                    "unique_internal_transfer_counterparts"
                ],
                "funding_bilateral_reconstruction_exact": result["funding"][
                    "all_counterparty_flow_reconstructions_exact"
                ],
                "exact_snapshot_equality": result["exact_decimal_equality_to_all_snapshot_fields"],
                "exact_source_blockers": result["blocking_for_exact_authoritative_equity_source"],
                "credential_access_or_network_in_replay": False,
                "orders_or_transfers": 0,
                "capital_admitted": False,
                "internal_assessment": assessment,
            },
            indent=2,
        )
    )
    if assessment is not None:
        return 0 if not assessment["blockers"] else 3
    return 0 if result["exact_decimal_equality_to_all_snapshot_fields"] else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # Do not emit raw account rows/UIDs or exception payloads on failure.
        print(
            json.dumps(
                {"status": "FAILED", "error_type": type(exc).__name__, "capital_admitted": False}
            )
        )
        raise SystemExit(2)
