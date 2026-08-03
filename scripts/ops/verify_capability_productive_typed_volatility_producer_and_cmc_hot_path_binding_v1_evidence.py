#!/usr/bin/env python3
"""Fail-closed verifier for productive typed-vol producer + CMC hot-path evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIRNAME = "capability_productive_typed_volatility_producer_and_cmc_hot_path_binding_v1"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fail(msg: str) -> int:
    print(json.dumps({"ok": False, "error": msg}, sort_keys=True))
    return 2


def main() -> int:
    evidence_root = _REPO_ROOT / "docs" / "evidence" / EVIDENCE_DIRNAME
    productive = evidence_root / "productive_binding"
    summary_path = evidence_root / "SUMMARY.json"
    manifest_path = evidence_root / "MANIFEST.sha256"
    if not summary_path.is_file():
        return _fail("SUMMARY_MISSING")
    if not manifest_path.is_file():
        return _fail("MANIFEST_MISSING")

    # Manifest verify
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=str(evidence_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return _fail(f"MANIFEST_VERIFY_FAILED:{proc.stderr.strip()}")

    summary = _load(summary_path)
    claims = summary.get("claims") or {}
    probe = _load(productive / "productive_offline_probe.json")
    proxy = _load(productive / "legacy_proxy_non_authority_proof.json")
    negative = _load(productive / "negative_boundary_results.json")
    warmup = _load(productive / "warmup_transition_trace.json")
    typed = _load(productive / "typed_estimate_trace.json")
    progression = _load(productive / "decision_stage_progression.json")

    required_files = [
        "producer_consumer_state_matrix.json",
        "call_graph_before.json",
        "call_graph_after.json",
        "warmup_transition_trace.json",
        "distinct_observation_trace.json",
        "typed_estimate_trace.json",
        "CMC_binding_trace.json",
        "presence_gate_trace.json",
        "decision_stage_progression.json",
        "legacy_proxy_non_authority_proof.json",
        "core_logic_parity.json",
        "risk_safety_exit_independence.json",
        "restart_semantics.json",
        "config_digest.json",
        "repository_sha.json",
        "test_results.json",
        "negative_boundary_results.json",
        "productive_offline_probe.json",
        "claims.json",
    ]
    for name in required_files:
        if not (productive / name).is_file():
            return _fail(f"MISSING_EVIDENCE_FILE:{name}")

    checks = {
        "typed_estimate_absent_during_legitimate_warmup": any(
            row.get("producer_outcome") == "WARMUP" for row in warmup
        )
        and any(row.get("estimate_present") is False for row in typed),
        "typed_estimate_present_after_sufficient_distinct_observations": bool(
            probe.get("canonical_market_context_typed_estimate_present")
        )
        and int(
            -1
            if probe.get("typed_volatility_estimate_missing_count_after_warmup") is None
            else probe.get("typed_volatility_estimate_missing_count_after_warmup")
        )
        == 0,
        "typed_estimate_has_canonical_semantics_and_provenance": bool(
            (probe.get("canonical_volatility_typed_binding") or {}).get("source_digest")
        )
        and bool((probe.get("canonical_volatility_typed_binding") or {}).get("history_digest")),
        "no_silent_fallback": claims.get("SILENT_DEFAULT_ADDED") is False,
        "no_proxy_promotion": proxy.get("feature_regime_volatility_estimate_productive_authority")
        is False
        and claims.get("LEGACY_PROXY_PROMOTED") is False,
        "no_duplicate_advancement": int(probe.get("finalizer_finalized_count") or 0)
        <= int(probe.get("history_observation_count") or 0) + 1,
        "no_core_logic_mutation": claims.get("CORE_LOGIC_CHANGE") is False,
        "no_live_testnet_order_credential_path": all(
            [
                claims.get("LIVE_PATH_CHANGED") is False,
                claims.get("TESTNET_PATH_CHANGED") is False,
                claims.get("ORDER_PATH_CHANGED") is False,
                claims.get("EXCHANGE_CREDENTIAL_PATH_CHANGED") is False,
                claims.get("NETWORK_USED") is False,
                negative.get("execution_eligible_false") is True,
                negative.get("orders_submitted_false") is True,
            ]
        ),
        "claims_match_telemetry": (
            claims.get("TYPED_ESTIMATE_PRESENT_AFTER_WARMUP")
            == probe.get("canonical_market_context_typed_estimate_present")
            and claims.get("TYPED_VOL_MISSING_AFTER_WARMUP_COUNT")
            == probe.get("typed_volatility_estimate_missing_count_after_warmup")
            and claims.get("DECISION_GRAPH_PROGRESS_AFTER_VOL_STAGE")
            == probe.get("decision_graph_progress_after_vol_stage")
        ),
        "decision_graph_progressed": any(
            "master_v2_double_play_integrated_offline_replay" in (row.get("call_graph") or [])
            for row in progression
        ),
        "summary_ok": bool(summary.get("ok")),
    }
    if not all(checks.values()):
        failed = [k for k, v in checks.items() if not v]
        return _fail(f"VERIFIER_CHECKS_FAILED:{','.join(failed)}")

    # Optional pytest confirmation for local gate ownership.
    test_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/trading/master_v2/test_canonical_volatility_pt1m_mark_observation_finalizer_v1.py",
        "tests/ops/test_productive_typed_volatility_producer_and_cmc_hot_path_binding_v1.py",
        "-q",
    ]
    test_proc = subprocess.run(
        test_cmd,
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={
            **dict(**{k: v for k, v in __import__("os").environ.items()}),
            "PYTHONPATH": f"{_REPO_ROOT}:{_REPO_ROOT / 'src'}",
        },
    )
    test_payload = {
        "ok": test_proc.returncode == 0,
        "returncode": test_proc.returncode,
        "stdout_tail": test_proc.stdout[-2000:],
        "stderr_tail": test_proc.stderr[-2000:],
        "command": test_cmd,
    }
    (productive / "test_results.json").write_text(
        json.dumps(test_payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    # Refresh manifest after rewriting test_results.
    rows: list[str] = []
    for path in sorted(evidence_root.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rel = path.relative_to(evidence_root).as_posix()
            rows.append(f"{_sha256_file(path)}  {rel}")
    manifest_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    proc2 = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=str(evidence_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc2.returncode != 0:
        return _fail("MANIFEST_REVERIFY_FAILED")
    if test_proc.returncode != 0:
        return _fail("TESTS_FAILED")

    print(
        json.dumps(
            {
                "ok": True,
                "MANIFEST_VERIFY_RC": 0,
                "checks": checks,
                "TESTS_PASS": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
