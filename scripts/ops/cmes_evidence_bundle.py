#!/usr/bin/env python3
"""
One-shot CMES evidence bundle (Runbook M): ingress + L3 artifacts, pointer-only scan, facts hash.
Produces tarball + sha256 in ~/Downloads (local, non-repo).

Usage (from repo root):
    python scripts/ops/cmes_evidence_bundle.py

Output:
    ~/Downloads/cmes-risk-strat-<ID>.tgz
    ~/Downloads/cmes-risk-strat-<ID>.tgz.sha256
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "ops"))

FORBIDDEN_PATTERN = re.compile(
    r"payload|raw|transcript|api_key|secret|token|content",
    re.IGNORECASE,
)


def _run(cmd: list[str], *, cwd: str | Path | None = None) -> tuple[int, str]:
    """Run command; return (returncode, combined stdout/stderr)."""
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out


def _verify_sidecar(
    *,
    base_dir: Path,
    sidecar_rel: str,
    audit_path: Path,
) -> None:
    """
    Verify <hex>  <filename> sidecar using shasum -a 256 -c.
    Runs with cwd=base_dir so basename in sidecar resolves. Writes output to audit_path.
    Fail-closed on non-zero exit.
    """
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    rc, out = _run(
        ["shasum", "-a", "256", "-c", sidecar_rel],
        cwd=str(base_dir),
    )
    audit_path.write_text(out, encoding="utf-8")
    if rc != 0:
        raise RuntimeError(
            f"Sidecar verification failed: {sidecar_rel} (rc={rc}). See {audit_path}"
        )


def main() -> int:
    evid_id = f"cmes-risk-strat-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%SZ')}"
    tmp_base = REPO_ROOT / "out" / f"_tmp_cmes_{evid_id}"
    tmp_base.mkdir(parents=True, exist_ok=True)

    # 1) Ingress (empty input)
    from src.ingress.orchestrator import OrchestratorConfig, run_ingress

    config = OrchestratorConfig(
        base_dir=tmp_base,
        run_id=evid_id,
        input_jsonl_path="",
    )
    try:
        fv_path, cap_path = run_ingress(config)
    except Exception as e:
        print(f"Ingress failed: {e}", file=sys.stderr)
        return 1

    paths_file = tmp_base / f"{evid_id}_ingress_paths.txt"
    paths_file.write_text(f"{fv_path.resolve()}\n{cap_path.resolve()}\n", encoding="utf-8")

    # 2) L3 dry-run with capsule (optional; may fail if deps/path not set)
    l3_out = tmp_base / "l3_out"
    l3_out.mkdir(parents=True, exist_ok=True)
    cap_data = json.loads(cap_path.read_text(encoding="utf-8"))
    try:
        from src.ai_orchestration.l3_runner import L3Runner

        runner = L3Runner(clock=datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc))
        runner.run(inputs=cap_data, mode="dry-run", out_dir=l3_out)
    except Exception:
        pass  # L3 may fail in minimal env; we still bundle

    # 3) Pointer-only scan (text search in generated files)
    scan_lines: list[str] = []
    for p in tmp_base.rglob("*"):
        if p.is_file() and p.suffix in (".json", ".md", ".txt"):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(text.splitlines(), 1):
                    if FORBIDDEN_PATTERN.search(line):
                        scan_lines.append(f"{p.relative_to(tmp_base)}:{i}:{line[:80]}")
            except Exception:
                pass
    scan_file = tmp_base / f"{evid_id}_pointer_only_scan.txt"
    scan_file.write_text("\n".join(scan_lines) if scan_lines else "no matches\n", encoding="utf-8")

    # 4) Facts hash from capsule
    facts = cap_data.get("facts") or cap_data.get("inputs", {}).get("facts") or {}
    from src.risk.cmes import canonical_facts_sha256

    try:
        h = canonical_facts_sha256(facts)
        fact_keys = sorted(facts.keys())
    except Exception:
        h = ""
        fact_keys = []
    hash_file = tmp_base / f"{evid_id}_facts_hash.txt"
    hash_file.write_text(
        f"facts_sha256: {h}\nfacts_keys: {fact_keys}\n",
        encoding="utf-8",
    )

    # 4b) Strict sidecar format gate (fail-closed), then shasum -c + audit logs
    from sidecar_verify import validate_json_and_sidecar

    views_dir = tmp_base / "views"
    capsules_dir = tmp_base / "capsules"
    view_json = views_dir / f"{evid_id}.feature_view.json"
    view_sha = views_dir / f"{evid_id}.feature_view.json.sha256"
    cap_json = capsules_dir / f"{evid_id}.capsule.json"
    cap_sha = capsules_dir / f"{evid_id}.capsule.json.sha256"
    validate_json_and_sidecar(view_json, view_sha)
    validate_json_and_sidecar(cap_json, cap_sha)

    audit_dir = tmp_base / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    _verify_sidecar(
        base_dir=views_dir,
        sidecar_rel=f"{evid_id}.feature_view.json.sha256",
        audit_path=audit_dir / f"{evid_id}_sidecar_verify_views.txt",
    )
    _verify_sidecar(
        base_dir=capsules_dir,
        sidecar_rel=f"{evid_id}.capsule.json.sha256",
        audit_path=audit_dir / f"{evid_id}_sidecar_verify_capsules.txt",
    )

    # 5) Bundle (selected files that exist)
    to_bundle = [
        f"{evid_id}_ingress_paths.txt",
        f"{evid_id}_pointer_only_scan.txt",
        f"{evid_id}_facts_hash.txt",
        f"audit/{evid_id}_sidecar_verify_views.txt",
        f"audit/{evid_id}_sidecar_verify_capsules.txt",
    ]
    for name in ("views", "capsules"):
        d = tmp_base / name
        if d.is_dir():
            for f in d.iterdir():
                to_bundle.append(str(f.relative_to(tmp_base)))
    l3_manifest = l3_out / "run_manifest.json"
    l3_md = l3_out / "operator_output.md"
    if l3_manifest.exists():
        to_bundle.append("l3_out/run_manifest.json")
    if l3_md.exists():
        to_bundle.append("l3_out/operator_output.md")
    to_bundle = [p for p in to_bundle if (tmp_base / p).exists()]

    tgz_path = Path("/tmp") / f"{evid_id}.tgz"
    subprocess.run(
        ["tar", "-C", str(tmp_base), "-czf", str(tgz_path)] + to_bundle,
        check=False,
        capture_output=True,
    )
    if not tgz_path.exists():
        tgz_path = tmp_base.parent / f"{evid_id}.tgz"
        subprocess.run(
            ["tar", "-C", str(tmp_base), "-czf", str(tgz_path)] + to_bundle,
            check=False,
            capture_output=True,
        )
    shasum = hashlib.sha256(tgz_path.read_bytes()).hexdigest()
    (tgz_path.with_suffix(tgz_path.suffix + ".sha256")).write_text(f"{shasum}  {tgz_path.name}\n")

    # Copy to Downloads (optional; may fail in restricted env)
    import shutil

    sha_path = tgz_path.with_suffix(tgz_path.suffix + ".sha256")
    try:
        downloads = Path(os.path.expanduser("~/Downloads"))
        downloads.mkdir(parents=True, exist_ok=True)
        dest_tgz = downloads / tgz_path.name
        dest_sha = downloads / f"{tgz_path.name}.sha256"
        shutil.copy2(tgz_path, dest_tgz)
        shutil.copy2(sha_path, dest_sha)
        print(f"Downloads: {dest_tgz} {dest_sha}")
    except OSError:
        print(f"Bundle (local): {tgz_path} {sha_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
