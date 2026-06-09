"""Tests for Path-C private-readonly connectivity evidence review v1."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
REVIEW_SCRIPT = (
    ROOT / "scripts" / "ops" / "review_testnet_private_readonly_connectivity_evidence_v1.py"
)
PROOF_CONTRACT_DOC = "docs/ops/specs/FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md"


def _load_review():
    spec = importlib.util.spec_from_file_location(
        "review_testnet_private_readonly_connectivity_evidence_v1", REVIEW_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_path_c_bundle(staging: Path, *, connectivity_proven: bool = True) -> None:
    evidence = staging / "wrapper_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "TESTNET_BOUNDED_OBSERVATION.md").write_text(
        "\n".join(
            [
                "# Path-C",
                "SESSION_CLASS=path_c_private_readonly_connectivity_v0",
                "TESTNET_SANDBOX_ONLY",
                "NO_PRODUCTION_FALLBACK",
                "NO_LIVE_ORDER_SUBMISSION",
                "PATH_B_IS_NOT_PATH_C=true",
                "primary_evidence_required=true",
                "closeout_required=true",
                PROOF_CONTRACT_DOC,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence / "steps.jsonl").write_text(
        json.dumps({"step": 1, "http_method": "GET", "no_orders": True, "no_cancel": True})
        + "\n",
        encoding="utf-8",
    )
    endpoints = [
        "/derivatives/api/v3/accounts",
        "/derivatives/api/v3/openpositions",
        "/derivatives/api/v3/openorders",
    ]
    (evidence / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "testnet_path_c_private_readonly_connectivity.v1",
                "session_class": "path_c_private_readonly_connectivity_v0",
                "TESTNET_SANDBOX_ONLY": True,
                "NO_PRODUCTION_FALLBACK": True,
                "NO_LIVE_ORDER_SUBMISSION": True,
                "path_b_is_not_path_c": True,
                "connectivity_mode": "private-readonly-connectivity",
                "private_readonly_reachability_proven": connectivity_proven,
                "testnet_connectivity_proven": connectivity_proven,
                "broker_connected": connectivity_proven,
                "production_fallback": False,
                "order_submission_allowed": False,
                "real_orders_executed": False,
                "max_orders": 0,
                "max_cancel": 0,
                "get_only": True,
                "primary_evidence_required": True,
                "closeout_required": True,
                "credential_values_logged": False,
                "network_request_count": 3 if connectivity_proven else 0,
                "endpoints_called": endpoints if connectivity_proven else [],
                "proof_contract_doc": PROOF_CONTRACT_DOC,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    logs = staging / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "wrapper_stdout.log").write_text("ok\n", encoding="utf-8")
    (logs / "wrapper_stderr.log").write_text("ok\n", encoding="utf-8")


def test_review_pass_on_complete_bundle(tmp_path: Path) -> None:
    mod = _load_review()
    staging = tmp_path / "staging"
    staging.mkdir()
    _write_path_c_bundle(staging)
    result = mod.review_evidence(staging)
    assert result["verdict"] == mod.PASS
    assert result["issues"] == []


def test_review_fail_when_connectivity_not_proven(tmp_path: Path) -> None:
    mod = _load_review()
    staging = tmp_path / "staging"
    staging.mkdir()
    _write_path_c_bundle(staging, connectivity_proven=False)
    result = mod.review_evidence(staging)
    assert result["verdict"] != mod.PASS
    assert result["issues"]


def test_review_fail_on_forbidden_endpoint(tmp_path: Path) -> None:
    mod = _load_review()
    staging = tmp_path / "staging"
    staging.mkdir()
    _write_path_c_bundle(staging)
    manifest = json.loads((staging / "wrapper_evidence" / "manifest.json").read_text())
    manifest["endpoints_called"] = ["/derivatives/api/v3/sendorder"]
    (staging / "wrapper_evidence" / "manifest.json").write_text(
        json.dumps(manifest) + "\n", encoding="utf-8"
    )
    result = mod.review_evidence(staging)
    assert result["verdict"] != mod.PASS


def test_review_fail_on_secret_marker_in_logs(tmp_path: Path) -> None:
    mod = _load_review()
    staging = tmp_path / "staging"
    staging.mkdir()
    _write_path_c_bundle(staging)
    (staging / "logs" / "wrapper_stderr.log").write_text(
        "KRAKEN_FUTURES_DEMO_API_SECRET leaked\n",
        encoding="utf-8",
    )
    result = mod.review_evidence(staging)
    assert result["verdict"] != mod.PASS


def test_review_fail_on_non_get_step(tmp_path: Path) -> None:
    mod = _load_review()
    staging = tmp_path / "staging"
    staging.mkdir()
    _write_path_c_bundle(staging)
    (staging / "wrapper_evidence" / "steps.jsonl").write_text(
        json.dumps({"step": 1, "http_method": "POST"}) + "\n",
        encoding="utf-8",
    )
    result = mod.review_evidence(staging)
    assert result["verdict"] != mod.PASS
