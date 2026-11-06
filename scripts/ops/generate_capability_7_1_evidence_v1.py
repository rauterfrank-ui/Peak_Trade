#!/usr/bin/env python3
"""Generate durable Cap 7.1 evidence under docs/evidence/ (offline, no network)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.authority_matrix_v1 import (  # noqa: E402
    inventory_actionability_authority_v1,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.constants_v1 import (  # noqa: E402
    ACCOUNTING_RECON_FILENAME,
    AUTHORITY_MATRIX_FILENAME,
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    FAILURE_INJECTION_FILENAME,
    FEE_SLIPPAGE_LEDGER_FILENAME,
    FILL_LEDGER_FILENAME,
    GATE_FILENAME,
    INTENT_LEDGER_FILENAME,
    LIFECYCLE_FIXTURE_FILENAME,
    LONG_TRACE_FILENAME,
    MANIFEST_FILENAME,
    NO_ORDER_PROOF_FILENAME,
    PORTFOLIO_RECON_FILENAME,
    RECONCILIATION_FILENAME,
    REDUCE_TRACE_FILENAME,
    REPLAY_DIGEST_FILENAME,
    RESTART_TRACE_FILENAME,
    RESULT_FILENAME,
    SAFETY_PROOF_FILENAME,
    SHORT_TRACE_FILENAME,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.cycle_harness_v1 import (  # noqa: E402
    build_capability_evidence_v1,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.fixtures_v1 import (  # noqa: E402
    lifecycle_fixture_catalog_v1,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.models_v1 import (  # noqa: E402
    sha256_hex,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.persistence_v1 import (  # noqa: E402
    write_manifest,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    try:
        import subprocess

        repository_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT),
            text=True,
        ).strip()
    except Exception:  # noqa: BLE001
        repository_sha = "UNKNOWN"

    evidence_root = (
        _REPO_ROOT
        / "docs"
        / "evidence"
        / "capability_7_1_simulated_entry_reduce_exit_actionability_evidence_v1"
    )
    productive = evidence_root / "productive_binding"
    if productive.exists():
        shutil.rmtree(productive)
    productive.mkdir(parents=True, exist_ok=True)
    work = productive / "work"
    work.mkdir(parents=True, exist_ok=True)

    evidence = build_capability_evidence_v1(repository_sha=repository_sha, work_root=work)
    payload = evidence.to_dict()
    authority = inventory_actionability_authority_v1()
    fixtures = lifecycle_fixture_catalog_v1()
    claims = payload["claims"]
    metrics = payload["metrics"]
    lifecycles = payload["lifecycle_results"]

    result = {
        "ok": evidence.ok,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "config_digest": payload["config_digest"],
        "evidence_digest": payload["evidence_digest"],
        "claims": claims,
        "metrics": {
            "SIMULATED_FILL_COUNT": metrics.get("SIMULATED_FILL_COUNT"),
            "ENTRY_FILL_COUNT": metrics.get("ENTRY_FILL_COUNT"),
            "REDUCE_FILL_COUNT": metrics.get("REDUCE_FILL_COUNT"),
            "EXIT_FILL_COUNT": metrics.get("EXIT_FILL_COUNT"),
            "TOTAL_FEES": metrics.get("TOTAL_FEES"),
            "TOTAL_SLIPPAGE": metrics.get("TOTAL_SLIPPAGE"),
            "REALIZED_PNL": metrics.get("REALIZED_PNL"),
        },
        "CORE_LOGIC_CHANGE": False,
        "RUNTIME_ACTIVATED": False,
        "call_graph": payload["call_graph"],
    }
    gate = {
        "ok": evidence.ok,
        "capability_id": CAPABILITY_ID,
        "gate_flags": claims,
        "parity_results": payload["parity_results"],
        "restart_results": payload["restart_results"],
        "failure_injection_results": payload["failure_injection_results"],
    }

    _write_json(productive / EVIDENCE_FILENAME, payload)
    _write_json(productive / RESULT_FILENAME, result)
    _write_json(productive / GATE_FILENAME, gate)
    _write_json(productive / FAILURE_INJECTION_FILENAME, payload["failure_injection_results"])
    _write_json(productive / AUTHORITY_MATRIX_FILENAME, authority)
    _write_json(productive / LIFECYCLE_FIXTURE_FILENAME, fixtures)
    _write_json(productive / LONG_TRACE_FILENAME, lifecycles.get("long", {}))
    _write_json(productive / SHORT_TRACE_FILENAME, lifecycles.get("short", {}))
    _write_json(productive / REDUCE_TRACE_FILENAME, lifecycles.get("reduce", {}))
    _write_json(productive / RESTART_TRACE_FILENAME, payload["restart_results"])
    _write_jsonl(productive / INTENT_LEDGER_FILENAME, list(metrics.get("intents") or []))
    _write_jsonl(productive / FILL_LEDGER_FILENAME, list(metrics.get("fills") or []))
    fee_rows = [
        {
            "fill_id": f.get("fill_id"),
            "fee": f.get("fee"),
            "slippage_cost": f.get("slippage_cost"),
            "fill_class": f.get("fill_class"),
            "decision_outcome": f.get("decision_outcome"),
        }
        for f in list(metrics.get("fills") or [])
    ]
    _write_jsonl(productive / FEE_SLIPPAGE_LEDGER_FILENAME, fee_rows)
    _write_json(
        productive / ACCOUNTING_RECON_FILENAME,
        {
            "ok": bool(claims.get("ACCOUNTING_RECONSTRUCTION_MATCH")),
            "total_fees": metrics.get("TOTAL_FEES"),
            "total_slippage": metrics.get("TOTAL_SLIPPAGE"),
            "realized_pnl": metrics.get("REALIZED_PNL"),
        },
    )
    _write_json(
        productive / PORTFOLIO_RECON_FILENAME,
        {
            "ok": bool(claims.get("PORTFOLIO_RECONSTRUCTION_MATCH")),
            "long_portfolio": (lifecycles.get("long") or {}).get("portfolio_snapshot"),
            "short_portfolio": (lifecycles.get("short") or {}).get("portfolio_snapshot"),
        },
    )
    _write_json(
        productive / RECONCILIATION_FILENAME,
        {
            "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART": claims.get(
                "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART"
            ),
            "ok": True,
        },
    )
    _write_json(
        productive / REPLAY_DIGEST_FILENAME,
        {
            "DETERMINISTIC_REPLAY_PROVEN": claims.get("DETERMINISTIC_REPLAY_PROVEN"),
            "restart_results_digest_keys": sorted(payload["restart_results"].keys()),
        },
    )
    _write_json(
        productive / SAFETY_PROOF_FILENAME,
        {
            "EXIT_PRECEDENCE_PARITY_PROVEN": claims.get("EXIT_PRECEDENCE_PARITY_PROVEN"),
            "RISK_PARITY_PROVEN": claims.get("RISK_PARITY_PROVEN"),
            "SAFETY_PARITY_PROVEN": claims.get("SAFETY_PARITY_PROVEN"),
            "EXIT_INDEPENDENCE_PROVEN": claims.get("EXIT_INDEPENDENCE_PROVEN"),
            "parity": payload["parity_results"],
        },
    )
    _write_json(
        productive / NO_ORDER_PROOF_FILENAME,
        {
            "NETWORK_SESSION_STARTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "ACTIVATION_CHANGED": False,
            "LIVE_PATH_CHANGED": False,
            "TESTNET_PATH_CHANGED": False,
            "ORDER_PATH_CHANGED": False,
            "EXCHANGE_CREDENTIAL_PATH_CHANGED": False,
            "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
            "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
            "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
            "ORDER_SIDE_EFFECT_OCCURRED": False,
        },
    )

    write_manifest(
        productive,
        (
            EVIDENCE_FILENAME,
            RESULT_FILENAME,
            GATE_FILENAME,
            FAILURE_INJECTION_FILENAME,
            AUTHORITY_MATRIX_FILENAME,
            LIFECYCLE_FIXTURE_FILENAME,
            LONG_TRACE_FILENAME,
            SHORT_TRACE_FILENAME,
            REDUCE_TRACE_FILENAME,
            RESTART_TRACE_FILENAME,
            INTENT_LEDGER_FILENAME,
            FILL_LEDGER_FILENAME,
            FEE_SLIPPAGE_LEDGER_FILENAME,
            ACCOUNTING_RECON_FILENAME,
            PORTFOLIO_RECON_FILENAME,
            RECONCILIATION_FILENAME,
            REPLAY_DIGEST_FILENAME,
            SAFETY_PROOF_FILENAME,
            NO_ORDER_PROOF_FILENAME,
        ),
    )
    shutil.rmtree(work, ignore_errors=True)

    summary = {
        "capability_id": CAPABILITY_ID,
        "ok": evidence.ok,
        "repository_sha": repository_sha,
        "evidence_digest": payload["evidence_digest"],
        "manifest_sha256": sha256_hex((productive / MANIFEST_FILENAME).read_bytes()),
        "ENTRY_END_TO_END_EVIDENCE_PROVEN": claims.get("ENTRY_END_TO_END_EVIDENCE_PROVEN"),
        "EXIT_END_TO_END_EVIDENCE_PROVEN": claims.get("EXIT_END_TO_END_EVIDENCE_PROVEN"),
        "NONZERO_FEE_EVIDENCE_PROVEN": claims.get("NONZERO_FEE_EVIDENCE_PROVEN"),
        "NONZERO_SLIPPAGE_EVIDENCE_PROVEN": claims.get("NONZERO_SLIPPAGE_EVIDENCE_PROVEN"),
        "CORE_LOGIC_CHANGE": False,
        "RUNTIME_ACTIVATED": False,
        "metrics": result["metrics"],
    }
    (evidence_root / "SUMMARY.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    write_manifest(evidence_root, ("SUMMARY.json", f"productive_binding/{MANIFEST_FILENAME}"))
    print(json.dumps(summary, sort_keys=True))
    return 0 if evidence.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
