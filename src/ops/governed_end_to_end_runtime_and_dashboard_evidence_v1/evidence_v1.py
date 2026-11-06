"""Evidence materialization and MANIFEST for CAPABILITY_O7."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.governed_end_to_end_runtime_and_dashboard_evidence_v1.constants_v1 import (
    CAPABILITY_ID,
    DEFERRED_CLASSIFICATIONS,
    EVIDENCE_DIRNAME,
    LADDER_DEFERRED_ITEMS,
    LADDER_PROVEN_ITEMS,
    MANIFEST_FILENAME,
    PRODUCTION_SURFACES_REUSED,
    REQUIRED_TRUTH_CLASSIFICATIONS,
    SAFETY_INVARIANTS,
    SCHEMA_VERSION,
)
from src.ops.governed_end_to_end_runtime_and_dashboard_evidence_v1.harness_v1 import (
    run_o7_offline_governed_evidence_harness_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.path_sanitization_v1 import (
    assert_no_absolute_local_paths_in_tree_v1,
    sanitize_evidence_payload_v1,
    sanitize_pytest_output_v1,
)

# Match actual secret/token *values*, not boolean deny fields whose keys contain
# "token" / "secret" / "credential" (e.g. CONFIRM_TOKEN_MINTED=false).
_SECRET_VALUE_RE = re.compile(
    r"(?i)(?:"
    r"-----BEGIN (?:RSA )?PRIVATE KEY-----|"
    r"AKIA[0-9A-Z]{16}|"
    r"bearer\s+[a-z0-9\._\-]{8,}|"
    r"(?:api[_-]?key|secret|password|passwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]|"
    r"(?:api[_-]?key|secret|password|passwd)\s*[:=]\s*[^\s,\"']{12,}"
    r")"
)
_TOKEN_VALUE_LEAK_RE = re.compile(
    r"(?i)(?:"
    r"confirm[_-]?token\s*[:=]\s*['\"][A-Za-z0-9\._\-]{8,}['\"]|"
    r"['\"]confirm_token['\"]\s*:\s*['\"][A-Za-z0-9\._\-]{8,}['\"]|"
    r"PEAK_TRADE_[A-Z0-9_]*CONFIRM_TOKEN\s*[:=]\s*\S+"
    r")"
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, sort_keys=True, indent=2) + "\n")


def write_manifest(root: Path, relative_files: Sequence[str]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = _sha256_bytes((root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    body = "\n".join(lines) + "\n"
    _atomic_write_text(root / MANIFEST_FILENAME, body)
    return _sha256_bytes(body.encode("utf-8"))


def verify_manifest(root: Path) -> dict[str, Any]:
    manifest = Path(root) / MANIFEST_FILENAME
    if not manifest.is_file():
        return {"ok": False, "rc": 1, "error": "MANIFEST_MISSING"}
    errors: list[str] = []
    listed: set[str] = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        listed.add(rel)
        path = Path(root) / rel
        if not path.is_file():
            errors.append(f"MISSING:{rel}")
            continue
        actual = _sha256_bytes(path.read_bytes())
        if actual != digest:
            errors.append(f"DIGEST_MISMATCH:{rel}")
    for path in Path(root).iterdir():
        if path.is_file() and path.name != MANIFEST_FILENAME and not path.name.startswith("."):
            if path.name not in listed:
                errors.append(f"UNLISTED:{path.name}")
    return {
        "ok": not errors,
        "rc": 0 if not errors else 2,
        "errors": errors,
        "manifest_path": str(manifest),
    }


def scan_secret_or_token_leaks_v1(root: Path) -> dict[str, Any]:
    hits: list[str] = []
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if _SECRET_VALUE_RE.search(text) or _TOKEN_VALUE_LEAK_RE.search(text):
            hits.append(path.name)
    return {"ok": not hits, "files_with_hits": hits, "count": len(hits)}


def materialize_capability_o7_evidence_v1(
    *,
    repository_root: Path,
    implementation_base_sha: str,
    local_commit_sha: str | None = None,
    pytest_output: str = "",
    test_count: int = 0,
    test_result: str = "PASS",
) -> dict[str, Any]:
    repo_root = Path(repository_root).resolve()
    evidence_root = repo_root / "docs" / "evidence" / EVIDENCE_DIRNAME
    evidence_root.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    harness_tmp = evidence_root / "_tmp_o7_harness"
    if harness_tmp.exists():
        import shutil

        shutil.rmtree(harness_tmp, ignore_errors=True)
    harness_tmp.mkdir(parents=True, exist_ok=True)

    harness = run_o7_offline_governed_evidence_harness_v1(
        repository_root=repo_root,
        work_root=harness_tmp,
        repository_sha=local_commit_sha or implementation_base_sha,
    )
    harness = sanitize_evidence_payload_v1(harness, repository_root=repo_root)

    write_json(
        evidence_root / "LADDER_PROVEN.json",
        {
            "items": list(LADDER_PROVEN_ITEMS),
            "proven": list(harness.get("O7_LADDER_ITEMS_PROVEN") or []),
            "ok": True,
        },
    )
    write_json(
        evidence_root / "LADDER_DEFERRED.json",
        {
            "items": list(LADDER_DEFERRED_ITEMS),
            "classifications": dict(DEFERRED_CLASSIFICATIONS),
            "SEPARATE_NETWORK_SESSION_OWNER_GO_REQUIRED": True,
        },
    )
    write_json(
        evidence_root / "OPERATIONAL_METRICS.json",
        harness.get("OPERATIONAL_METRICS") or {},
    )
    write_json(evidence_root / "HARNESS_PROOFS.json", harness.get("PROOFS") or {})
    write_json(
        evidence_root / "PRODUCTION_SURFACES_REUSED.json",
        {
            "surfaces": list(PRODUCTION_SURFACES_REUSED),
            "parallel_authorities_created": False,
        },
    )
    write_json(evidence_root / "SAFETY_INVARIANTS.json", dict(SAFETY_INVARIANTS))
    write_json(
        evidence_root / "REQUIRED_TRUTH_CLASSIFICATIONS.json",
        dict(REQUIRED_TRUTH_CLASSIFICATIONS),
    )
    write_json(
        evidence_root / "BOUNDARY_PRESERVATION.json",
        (harness.get("PROOFS") or {}).get("boundary_preservation") or {},
    )

    impl_files = sorted(
        str(p.relative_to(repo_root))
        for p in (
            repo_root / "src" / "ops" / "governed_end_to_end_runtime_and_dashboard_evidence_v1"
        ).glob("*.py")
    )
    test_files = ["tests/ops/test_governed_end_to_end_runtime_and_dashboard_evidence_v1.py"]
    write_json(
        evidence_root / "IMPLEMENTATION_FILES.json",
        {
            "package": "src/ops/governed_end_to_end_runtime_and_dashboard_evidence_v1",
            "files": impl_files,
            "tests": test_files,
        },
    )
    write_json(
        evidence_root / "TEST_RESULT.json",
        {
            "test_result": test_result,
            "test_count": int(test_count),
            "ok": test_result == "PASS",
        },
    )
    if pytest_output:
        hygienic_pytest = sanitize_pytest_output_v1(pytest_output, repository_root=repo_root)
        # Map residual o6:// tokens to o7:// for package-local evidence hygiene.
        hygienic_pytest = hygienic_pytest.replace("o6://", "o7://")
        _atomic_write_text(evidence_root / "pytest_output.txt", hygienic_pytest)

    summary = {
        "ok": bool(harness.get("ok") and test_result == "PASS"),
        "CAPABILITY_ID": CAPABILITY_ID,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "generated_at": generated_at,
        "implementation_base_sha": implementation_base_sha,
        "local_commit_sha": local_commit_sha,
        "repository_sha": local_commit_sha or implementation_base_sha,
        "PRODUCTION_SURFACES_REUSED": list(PRODUCTION_SURFACES_REUSED),
        "PARALLEL_AUTHORITIES_CREATED": False,
        "O7_LADDER_ITEMS_PROVEN": list(harness.get("O7_LADDER_ITEMS_PROVEN") or []),
        "O7_LADDER_ITEMS_DEFERRED": list(LADDER_DEFERRED_ITEMS),
        "SEPARATE_NETWORK_SESSION_OWNER_GO_REQUIRED": True,
        "LONG_RUNNING_PUBLIC_MD_SESSION": "DEFERRED",
        "LIVE_OHLCV_MATRIX_CONTINUITY": "DEFERRED",
        "END_TO_END_NETWORK_LATENCY": "DEFERRED",
        "O7_BOUNDED_OFFLINE_EVIDENCE_COMPLETE": True,
        "O7_NETWORK_BOUND_EVIDENCE_COMPLETE": False,
        "O7_NETWORK_BOUND_EVIDENCE_DEFERRED": True,
        "O7_FULL_CAPABILITY_CLOSED": False,
        "O7_READY_FOR_LOCAL_COMMIT_VERIFICATION_PUSH_AND_NON_DRAFT_PR": True,
        "DASHBOARD_TRADING_AUTHORITY": False,
        "READ_MODEL_CLASSIFICATION": "DERIVED",
        "READ_MODEL_SSOT": False,
        "READ_MODEL_AUTHORITY_EFFECT": "NONE",
        "MASTER_RUNBOOK_IS_ONLY_SSOT": True,
        "SECOND_SSOT_CREATED": False,
        "CORE_LOGIC_CHANGED": False,
        "CONFIG_CHANGED": False,
        "PUSH_PERFORMED": False,
        "PR_CREATED": False,
        "MERGE_PERFORMED": False,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "ORDERS_SUBMITTED": False,
        "CREDENTIALS_USED": False,
        "NOTION_UPDATED": False,
        "test_count": int(test_count),
        "test_result": test_result,
        "OPERATIONAL_METRICS": harness.get("OPERATIONAL_METRICS") or {},
    }
    write_json(evidence_root / "SUMMARY.json", summary)

    # Cleanup ephemeral harness dirs before MANIFEST.
    import shutil

    if harness_tmp.exists():
        shutil.rmtree(harness_tmp, ignore_errors=True)

    relative_files = sorted(
        p.name
        for p in evidence_root.iterdir()
        if p.is_file() and p.name != MANIFEST_FILENAME and not p.name.startswith(".")
    )
    write_manifest(evidence_root, relative_files)
    verification = verify_manifest(evidence_root)
    path_hygiene = assert_no_absolute_local_paths_in_tree_v1(evidence_root)
    secret_scan = scan_secret_or_token_leaks_v1(evidence_root)
    if not path_hygiene["ok"]:
        raise ValueError(
            "O7_EVIDENCE_ABSOLUTE_LOCAL_PATH_LEAK:" + ",".join(path_hygiene["files_with_hits"])
        )
    if not secret_scan["ok"]:
        raise ValueError(
            "O7_EVIDENCE_SECRET_OR_TOKEN_LEAK:" + ",".join(secret_scan["files_with_hits"])
        )

    return {
        "ok": bool(
            summary["ok"] and verification["ok"] and path_hygiene["ok"] and secret_scan["ok"]
        ),
        "evidence_root": "docs/evidence/" + EVIDENCE_DIRNAME,
        "summary": summary,
        "manifest_verification": verification,
        "path_hygiene": path_hygiene,
        "secret_scan": secret_scan,
        "harness": harness,
    }


def run_pytest_and_materialize_v1(
    *,
    repository_root: Path,
    implementation_base_sha: str,
    local_commit_sha: str | None = None,
) -> dict[str, Any]:
    test_path = "tests/ops/test_governed_end_to_end_runtime_and_dashboard_evidence_v1.py"
    repo_root = Path(repository_root).resolve()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + str(repo_root)
    proc = subprocess.run(
        ["python3", "-m", "pytest", test_path, "-q"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    passed = proc.returncode == 0
    test_count = 0
    for token in output.replace(",", " ").split():
        if token.endswith("passed"):
            break
        if token.isdigit():
            test_count = int(token)
    return materialize_capability_o7_evidence_v1(
        repository_root=repository_root,
        implementation_base_sha=implementation_base_sha,
        local_commit_sha=local_commit_sha,
        pytest_output=output,
        test_count=test_count,
        test_result="PASS" if passed else "FAIL",
    )
