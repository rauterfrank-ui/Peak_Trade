from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path("scripts/research/run_full_canonical_core_completion_plausibility_diagnostic_v0.py")
CONFIRM = "GO_FULL_CANONICAL_CORE_COMPLETION_AND_PLAUSIBILITY_EVALUATION_DIAGNOSTIC_V0"


def test_cli_rejects_invalid_confirm_token(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--confirm",
            "WRONG",
            "--repo-root",
            str(Path.cwd()),
            "--durable-evidence-root",
            str(tmp_path),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "INVALID_CONFIRM_TOKEN" in result.stderr or "INVALID_CONFIRM_TOKEN" in result.stdout


def test_cli_rejects_policy_without_digest(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"diagnostic_only": True}))
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--confirm",
            CONFIRM,
            "--repo-root",
            str(Path.cwd()),
            "--durable-evidence-root",
            str(tmp_path / "evidence"),
            "--policy",
            str(policy),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "POLICY_DIGEST_MISSING" in result.stderr or "POLICY_DIGEST_MISSING" in result.stdout


def test_cli_source_contains_exact_owner_signature_kwargs() -> None:
    source = SCRIPT.read_text()
    assert "confirm=args.confirm" in source
    assert "repo_root=repo_root" in source
    assert "durable_evidence_root=args.durable_evidence_root.resolve()" in source
    assert "confirm_token" not in source
    assert "value_by_name" not in source


def test_cli_source_forces_required_authority_fields_false() -> None:
    source = SCRIPT.read_text()
    for field in (
        "promotion_admissible",
        "runtime_admissible",
        "live_authorized",
        "orders_allowed",
        "economic_validity_claim_allowed",
    ):
        assert f'payload["{field}"] = False' in source
