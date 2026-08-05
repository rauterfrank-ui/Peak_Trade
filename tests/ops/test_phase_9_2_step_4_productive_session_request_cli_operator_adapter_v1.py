"""Tests for Step-4 productive session_request CLI/operator adapter (no network)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    CONFIRM_TOKEN_PREFIX,
    compute_confirm_token_binding_sha256,
    fingerprint_confirm_token,
    sha256_text,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    CLI_OWNER_SESSION_PERMIT_DEFAULT,
    NETWORK_SESSION_ALLOWED,
    SESSION_REQUEST_ADAPTER_CAPABILITY_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.runner_invoke_binding_v1 import (
    REQUIRED_RUNNER_KWARGS,
    discover_canonical_wallclock_runner_signature_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_request_cli_adapter_v1 import (
    CANONICAL_SESSION_REQUEST_OWNER,
    build_canonical_session_request_from_issuance_artifacts_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.py"
)
FIXTURE_DIR = (
    REPO_ROOT
    / "tests/fixtures/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1"
)
TOKEN = CONFIRM_TOKEN_PREFIX + ("ADAPTERTESTTOKENV1" + "X" * 24)


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _write_issuance_bundle(tmp_path: Path, *, sha: str) -> dict[str, Path]:
    evidence_root = tmp_path / "evidence_root"
    evidence_root.mkdir(parents=True, exist_ok=True)
    ledger = tmp_path / "fingerprint_ledger.txt"
    ledger.write_text("", encoding="utf-8")
    token_file = tmp_path / "confirm_token.txt"
    token_file.write_text(TOKEN, encoding="utf-8")
    token_file.chmod(0o600)

    prereg_raw = json.loads(
        (FIXTURE_DIR / "preregistration_wallclock_valid_non_authoritative.json").read_text(
            encoding="utf-8"
        )
    )
    go_raw = json.loads(
        (FIXTURE_DIR / "operator_go_wallclock_valid_non_authoritative.json").read_text(
            encoding="utf-8"
        )
    )
    session_id = "phase_9_2_adapter_dry_probe_session_v1"
    prereg_raw["session_id"] = session_id
    prereg_raw["expected_repository_sha"] = sha
    prereg_raw["evidence_root"] = str(evidence_root)
    # Recompute binding after identity changes.
    provisional = parse_preregistration_contract_v1(prereg_raw)
    binding = compute_confirm_token_binding_sha256(
        session_id=session_id,
        scope_digest=provisional.scope_digest(),
        expires_at=float(prereg_raw["expires_at"]),
        repository_sha=sha,
        confirm_token=TOKEN,
    )
    prereg_raw["confirm_token_binding_sha256"] = binding
    prereg_raw["confirm_token_hash_reference"] = "sha256:" + sha256_text(TOKEN)

    go_raw["session_id"] = session_id
    go_raw["expected_repository_sha"] = sha
    go_raw["confirm_token_binding_sha256"] = binding
    go_raw["confirm_token_hash_reference"] = prereg_raw["confirm_token_hash_reference"]
    go_raw["scope_digest"] = provisional.scope_digest()

    prereg_path = tmp_path / "preregistration.json"
    go_path = tmp_path / "operator_go.json"
    art_path = tmp_path / "authorization_artifact.json"
    write_json_atomic_v1(prereg_path, prereg_raw)
    write_json_atomic_v1(go_path, go_raw)
    write_json_atomic_v1(
        art_path,
        {
            "schema": "authorization_artifact_binding_probe_v1",
            "preregistration_id": session_id,
            "repository_sha": sha,
            "confirm_token_fingerprint": fingerprint_confirm_token(TOKEN),
            "notes": ["ADAPTER_UNIT_BINDING_ONLY", "NOT_A_FULL_V2_ARTIFACT"],
        },
    )
    return {
        "preregistration": prereg_path,
        "operator_go": go_path,
        "authorization_artifact": art_path,
        "confirm_token_file": token_file,
        "fingerprint_ledger": ledger,
        "evidence_root": evidence_root,
    }


def test_adapter_capability_constants_fail_closed() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert CLI_OWNER_SESSION_PERMIT_DEFAULT is False
    assert SESSION_REQUEST_ADAPTER_CAPABILITY_ID.endswith("SESSION_REQUEST_CLI_OPERATOR_ADAPTER_V1")
    assert "runner_invoke_binding_v1" in CANONICAL_SESSION_REQUEST_OWNER


def test_runner_signature_still_matches_repository() -> None:
    discovered = discover_canonical_wallclock_runner_signature_v1()
    assert discovered["ok"] is True
    assert discovered["required_kwargs"] == list(REQUIRED_RUNNER_KWARGS)
    assert "session_request" in discovered["forbidden_legacy_keys"]


def test_full_artifacts_build_session_request(tmp_path: Path) -> None:
    sha = _sha()
    paths = _write_issuance_bundle(tmp_path, sha=sha)
    result = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=paths["confirm_token_file"],
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        use_real_network=False,
    )
    assert result.ok is True
    assert result.session_request is not None
    for key in REQUIRED_RUNNER_KWARGS:
        assert key in result.session_request
    assert result.session_request["use_real_network"] is False
    assert result.claims["SESSION_REQUEST_REQUIRED_FIELDS_COMPLETE"] is True
    assert result.claims["RUNNER_SIGNATURE_MATCH"] is True
    assert result.claims["NETWORK_SESSION_STARTED"] is False
    assert result.claims["AUTHORIZATION_CONSUMED"] is False
    assert result.claims["CONFIRM_TOKEN_CONSUMED"] is False
    redacted = result.to_dict()
    assert redacted["session_request"]["confirm_token"] == "[REDACTED]"
    assert TOKEN not in json.dumps(redacted)


@pytest.mark.parametrize(
    "missing",
    [
        "preregistration",
        "operator_go",
        "authorization_artifact",
        "confirm_token_file",
        "fingerprint_ledger",
    ],
)
def test_missing_required_artifact_fail_closed(tmp_path: Path, missing: str) -> None:
    sha = _sha()
    paths = _write_issuance_bundle(tmp_path, sha=sha)
    kwargs: dict[str, Any] = {
        "preregistration_path": paths["preregistration"],
        "operator_go_path": paths["operator_go"],
        "authorization_artifact_path": paths["authorization_artifact"],
        "confirm_token_file": paths["confirm_token_file"],
        "fingerprint_ledger_path": paths["fingerprint_ledger"],
        "expected_repository_sha": sha,
        "permit_canonical_runner_invoke": True,
    }
    key_map = {
        "preregistration": "preregistration_path",
        "operator_go": "operator_go_path",
        "authorization_artifact": "authorization_artifact_path",
        "confirm_token_file": "confirm_token_file",
        "fingerprint_ledger": "fingerprint_ledger_path",
    }
    kwargs[key_map[missing]] = None
    result = build_canonical_session_request_from_issuance_artifacts_v1(**kwargs)
    assert result.ok is False
    assert result.session_request is None
    assert result.claims["AUTHORIZATION_CONSUMED"] is False
    assert result.claims["CONFIRM_TOKEN_CONSUMED"] is False


def test_repository_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    sha = _sha()
    paths = _write_issuance_bundle(tmp_path, sha=sha)
    result = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=paths["confirm_token_file"],
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha="0" * 40,
        permit_canonical_runner_invoke=True,
    )
    assert result.ok is False
    assert "CLI_EXPECTED_REPOSITORY_SHA_MISMATCH" in result.blockers


def test_artifact_binding_mismatch_fail_closed(tmp_path: Path) -> None:
    sha = _sha()
    paths = _write_issuance_bundle(tmp_path, sha=sha)
    bad = json.loads(paths["authorization_artifact"].read_text(encoding="utf-8"))
    bad["preregistration_id"] = "wrong_session"
    write_json_atomic_v1(paths["authorization_artifact"], bad)
    result = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=paths["confirm_token_file"],
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
    )
    assert result.ok is False
    assert "AUTHORIZATION_ARTIFACT_PREREGISTRATION_ID_MISMATCH" in result.blockers


def test_stale_artifact_path_fail_closed(tmp_path: Path) -> None:
    sha = _sha()
    paths = _write_issuance_bundle(tmp_path, sha=sha)
    result = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=tmp_path / "missing_auth.json",
        confirm_token_file=paths["confirm_token_file"],
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
    )
    assert result.ok is False
    assert any("AUTHORIZATION_ARTIFACT_PATH_NOT_A_FILE" in b for b in result.blockers)


def test_permit_missing_fail_closed(tmp_path: Path) -> None:
    sha = _sha()
    paths = _write_issuance_bundle(tmp_path, sha=sha)
    result = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=paths["confirm_token_file"],
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=False,
    )
    assert result.ok is False
    assert "OWNER_SESSION_PERMIT_REQUIRED" in result.blockers


def test_no_plaintext_in_adapter_dict(tmp_path: Path) -> None:
    sha = _sha()
    paths = _write_issuance_bundle(tmp_path, sha=sha)
    result = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=paths["confirm_token_file"],
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
    )
    blob = json.dumps(result.to_dict())
    assert TOKEN not in blob
    assert "confirm_token_fingerprint" in result.to_dict()


def test_cli_dry_probe_integration_no_network_no_consume(tmp_path: Path) -> None:
    sha = _sha()
    paths = _write_issuance_bundle(tmp_path, sha=sha)
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-productive-session",
            "--execute",
            "--owner-go",
            "--owner-session-go",
            "--request-real-network",
            "--permit-canonical-runner-invoke",
            "--authorization-present",
            "--confirm-token-present",
            f"--preregistration={paths['preregistration']}",
            f"--operator-go={paths['operator_go']}",
            f"--authorization-artifact={paths['authorization_artifact']}",
            f"--confirm-token-file={paths['confirm_token_file']}",
            f"--fingerprint-ledger={paths['fingerprint_ledger']}",
            f"--expected-repository-sha={sha}",
            "--json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert TOKEN not in proc.stdout
    assert TOKEN not in proc.stderr
    assert "--confirm-token=" not in " ".join(proc.args)
    payload = json.loads(proc.stdout)
    assert proc.returncode == 2  # dry path returns ok=False with NETWORK_SESSION_ALLOWED_REQUIRED
    assert payload.get("wallclock_runner_invoked") is False
    assert payload.get("authorization_consumed") is False
    adapter = payload.get("session_request_adapter") or {}
    assert adapter.get("ok") is True
    claims = payload.get("claims") or {}
    assert claims.get("NETWORK_SESSION_STARTED") is False
    assert claims.get("DRY_NO_NETWORK") is True
    assert claims.get("CLI_OWNER_SESSION_PERMIT_EXPLICIT") is True
    assert claims.get("RUNNER_SIGNATURE_MATCH") is True
    assert claims.get("SESSION_REQUEST_REQUIRED_FIELDS_COMPLETE") is True
    assert claims.get("PRODUCTIVE_SESSION_PATH_DRY_PROBE_REACHABLE") is True


def test_cli_network_requires_governed_binding_only_flag(tmp_path: Path) -> None:
    sha = _sha()
    paths = _write_issuance_bundle(tmp_path, sha=sha)
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-productive-session",
            "--execute",
            "--owner-go",
            "--owner-session-go",
            "--request-real-network",
            "--network-session-allowed",
            "--permit-canonical-runner-invoke",
            f"--preregistration={paths['preregistration']}",
            f"--operator-go={paths['operator_go']}",
            f"--authorization-artifact={paths['authorization_artifact']}",
            f"--confirm-token-file={paths['confirm_token_file']}",
            f"--fingerprint-ledger={paths['fingerprint_ledger']}",
            f"--expected-repository-sha={sha}",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert "GOVERNED_EXECUTION_BINDING_ONLY_REQUIRED" in payload["blockers"]
    assert payload["network_session_started"] is False
    assert payload["authorization_consumed"] is False


def test_regression_permit_wiring_still_present() -> None:
    """PR #5755 regression: permit flag and signature discovery remain bound."""
    from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
        CLI_OWNER_SESSION_PERMIT_FLAG,
        OWNER_PERMIT_WIRING_CAPABILITY_ID,
        PRODUCTIVE_SESSION_PATH_STRUCTURALLY_RUNTIME_REACHABLE,
    )

    assert CLI_OWNER_SESSION_PERMIT_FLAG == "--permit-canonical-runner-invoke"
    assert OWNER_PERMIT_WIRING_CAPABILITY_ID.endswith("OWNER_PERMIT_WIRING_V1")
    assert PRODUCTIVE_SESSION_PATH_STRUCTURALLY_RUNTIME_REACHABLE is True
    text = CLI.read_text(encoding="utf-8")
    assert "--permit-canonical-runner-invoke" in text
    assert "session_request=session_request" in text
    assert "build_canonical_session_request_from_issuance_artifacts_v1" in text
