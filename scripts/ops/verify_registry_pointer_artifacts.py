#!/usr/bin/env python3
"""
Portable verifier: reads pointer, validates telemetry invariants (download optional).

NO-LIVE: local filesystem / optional gh artifact download for audit — not a trading path.

When --download is set, GitHub Actions artifact *metadata* is classified before
any download:

  REGISTRY_POINTER_STATUS=AVAILABLE
  REGISTRY_POINTER_STATUS=EXPIRED
  REGISTRY_POINTER_STATUS=INVALID
  REGISTRY_POINTER_STATUS=UNAVAILABLE_UNKNOWN

EXPIRED is proven only when the artifacts API returns a non-empty list and every
artifact has expired=true. Download-error text is never treated as expiry.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

FALLBACK_CODE = "AUDIT_MANIFEST_NO_DECISION_CONTEXT"
VALID_ACTIONS = {"ALLOW", "NO_TRADE"}

STATUS_AVAILABLE = "AVAILABLE"
STATUS_EXPIRED = "EXPIRED"
STATUS_INVALID = "INVALID"
STATUS_UNAVAILABLE_UNKNOWN = "UNAVAILABLE_UNKNOWN"

_HTTP_STATUS_RE = re.compile(r"HTTP\s+(\d{3})", re.IGNORECASE)


class ArtifactFetchError(Exception):
    """Metadata API failure. Never classified as EXPIRED."""

    def __init__(self, message: str, *, kind: str, http_status: Optional[int] = None) -> None:
        super().__init__(message)
        self.kind = kind
        self.http_status = http_status


class ArtifactDownloadError(Exception):
    """Download failure after metadata classified AVAILABLE."""

    def __init__(self, message: str, *, returncode: int) -> None:
        super().__init__(message)
        self.returncode = returncode


@dataclass(frozen=True)
class ArtifactRecord:
    name: str
    expired: bool
    artifact_id: Optional[int] = None
    expires_at: Optional[str] = None
    created_at: Optional[str] = None


FetchArtifacts = Callable[[str, str], List[ArtifactRecord]]
DownloadRun = Callable[[str, Path], None]


def parse_pointer(path: Path) -> Dict[str, str]:
    d: Dict[str, str] = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if "=" in ln:
            k, v = ln.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def resolve_repo(pointer: Dict[str, str]) -> str:
    repo = (pointer.get("repo") or "").strip()
    if repo:
        return repo
    env_repo = (os.environ.get("GITHUB_REPOSITORY") or "").strip()
    if env_repo:
        return env_repo
    return ""


def classify_artifact_records(records: Sequence[ArtifactRecord]) -> str:
    """Classify from metadata records only. Empty list is not expiry proof."""
    if not records:
        return STATUS_UNAVAILABLE_UNKNOWN
    if all(record.expired for record in records):
        return STATUS_EXPIRED
    return STATUS_AVAILABLE


def _http_status_from_gh_error(text: str) -> Optional[int]:
    match = _HTTP_STATUS_RE.search(text)
    if not match:
        return None
    return int(match.group(1))


def _fetch_error_kind(http_status: Optional[int], text: str) -> str:
    lowered = text.lower()
    if http_status in {401, 403}:
        return "auth"
    if http_status == 404:
        return "not_found"
    if "bad credentials" in lowered or "authentication" in lowered:
        return "auth"
    if http_status is not None:
        return "api"
    return "api"


def _records_from_payload_obj(obj: object) -> List[ArtifactRecord]:
    if isinstance(obj, dict) and "artifacts" in obj:
        items = obj["artifacts"]
    elif isinstance(obj, list):
        items = obj
    elif isinstance(obj, dict) and ("name" in obj or "expired" in obj):
        items = [obj]
    else:
        raise ArtifactFetchError(
            f"unexpected artifacts API payload type: {type(obj).__name__}",
            kind="parse",
        )
    if not isinstance(items, list):
        raise ArtifactFetchError("artifacts field is not a list", kind="parse")
    records: List[ArtifactRecord] = []
    for item in items:
        if not isinstance(item, dict):
            raise ArtifactFetchError("artifact entry is not an object", kind="parse")
        expired_raw = item.get("expired")
        # Only explicit JSON true counts as expired. Missing/false → available.
        expired = expired_raw is True
        artifact_id = item.get("id")
        records.append(
            ArtifactRecord(
                name=str(item.get("name") or ""),
                expired=expired,
                artifact_id=artifact_id if isinstance(artifact_id, int) else None,
                expires_at=str(item["expires_at"]) if item.get("expires_at") else None,
                created_at=str(item["created_at"]) if item.get("created_at") else None,
            )
        )
    return records


def parse_artifacts_api_payload(raw: str) -> List[ArtifactRecord]:
    text = raw.strip()
    if not text:
        raise ArtifactFetchError("empty artifacts API payload", kind="parse")
    decoder = json.JSONDecoder()
    idx = 0
    records: List[ArtifactRecord] = []
    length = len(text)
    while idx < length:
        while idx < length and text[idx].isspace():
            idx += 1
        if idx >= length:
            break
        try:
            obj, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError as exc:
            raise ArtifactFetchError(
                f"artifacts API JSON parse error: {exc}", kind="parse"
            ) from exc
        records.extend(_records_from_payload_obj(obj))
        idx = end
    return records


def fetch_run_artifact_records(run_id: str, repo: str) -> List[ArtifactRecord]:
    cmd = [
        "gh",
        "api",
        f"repos/{repo}/actions/runs/{run_id}/artifacts",
        "--paginate",
    ]
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if proc.returncode != 0:
        combined = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip()
        http_status = _http_status_from_gh_error(combined)
        kind = _fetch_error_kind(http_status, combined)
        raise ArtifactFetchError(
            combined or f"gh api exit {proc.returncode}",
            kind=kind,
            http_status=http_status,
        )
    return parse_artifacts_api_payload(proc.stdout)


def download_run_artifacts(run_id: str, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["gh", "run", "download", run_id, "-D", str(dest_dir)],
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        combined = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip()
        raise ArtifactDownloadError(
            combined or f"gh run download exit {proc.returncode}",
            returncode=proc.returncode,
        )


def find_telemetry_summaries(root: Path) -> List[Path]:
    return sorted(root.rglob("telemetry_summary.json"))


def validate_summary(path: Path) -> Tuple[bool, str]:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"json_load_error: {e}"
    policy = d.get("policy")
    if not isinstance(policy, dict) or not policy:
        return False, "policy missing/empty"
    action = policy.get("action")
    if action not in VALID_ACTIONS:
        return False, f"policy.action invalid: {action!r}"
    rc = policy.get("reason_codes")
    if not isinstance(rc, list):
        return False, f"policy.reason_codes not list: {type(rc).__name__}"
    if FALLBACK_CODE in rc:
        return False, "fallback code present in reason_codes"
    src = d.get("source")
    if src != "evidence_manifest":
        return False, f"source unexpected: {src!r} (expected 'evidence_manifest')"
    return True, "OK"


def write_sha256sums(pack_dir: Path) -> Path:
    sums = pack_dir / "SHA256SUMS.stable.txt"
    files = [p for p in pack_dir.rglob("*") if p.is_file() and p.name != sums.name]
    files_sorted = sorted([str(p.relative_to(pack_dir).as_posix()) for p in files])
    lines: List[str] = []
    for rel in files_sorted:
        p = pack_dir / rel
        sp = subprocess.run(
            ["shasum", "-a", "256", str(p)],
            capture_output=True,
            text=True,
            check=True,
        )
        h = sp.stdout.strip().split()[0]
        lines.append(f"{h}  {rel}")
    sums.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sums


def _emit_status_line(status: str) -> None:
    print(f"REGISTRY_POINTER_STATUS={status}")


def _emit_expired_diagnostics(run_id: str, records: Sequence[ArtifactRecord]) -> None:
    print("REGISTRY_POINTER_EXPIRED=true")
    print(f"REGISTRY_POINTER_RUN_ID={run_id}")
    print(f"REGISTRY_POINTER_EXPIRED_COUNT={sum(1 for r in records if r.expired)}")
    print(f"REGISTRY_POINTER_AVAILABLE_COUNT={sum(1 for r in records if not r.expired)}")
    expires_at = next((r.expires_at for r in records if r.expires_at), None)
    if expires_at:
        print(f"REGISTRY_POINTER_EXPIRES_AT={expires_at}")
    names = ",".join(r.name for r in records if r.name)
    if names:
        print(f"REGISTRY_POINTER_ARTIFACT_NAMES={names}")


def _gha_warning(title: str, message: str) -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning title={title}::{message}")


def _verify_summaries(artifacts_root: Path) -> int:
    summaries = find_telemetry_summaries(artifacts_root)
    if not summaries:
        print(
            f"ERR: no telemetry_summary.json found under {artifacts_root}",
            file=sys.stderr,
        )
        return 1

    bad: List[Tuple[Path, str]] = []
    for s in summaries:
        ok, msg = validate_summary(s)
        if not ok:
            bad.append((s, msg))

    if bad:
        sys.stderr.write("FAIL: telemetry invariants violated\n")
        for p, msg in bad[:200]:
            sys.stderr.write(f"- {p}: {msg}\n")
        return 3

    print(f"OK: {len(summaries)} telemetry_summary.json validated under {artifacts_root}")
    return 0


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    fetch_artifacts: Optional[FetchArtifacts] = None,
    download_run: Optional[DownloadRun] = None,
) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Verify registry pointer artifacts and telemetry_summary.json invariants. "
            "NO-LIVE: local audit helper — not a trading or execution path."
        ),
    )
    ap.add_argument("pointer", type=Path, help="docs/ops/registry/*.pointer")
    ap.add_argument(
        "--out-base",
        type=Path,
        default=Path("out/ops/gh_runs"),
        help="download base dir",
    )
    ap.add_argument(
        "--download",
        action="store_true",
        help="download artifacts via gh run download",
    )
    ap.add_argument(
        "--allow-expired",
        action="store_true",
        help=(
            "treat proven REGISTRY_POINTER_EXPIRED as a non-failing lifecycle state "
            "(pull_request hygiene). Default/manual/workflow_dispatch stays fail-closed."
        ),
    )
    ap.add_argument(
        "--pack-out",
        type=Path,
        default=None,
        help="optional evidence pack output dir",
    )
    args = ap.parse_args(argv)

    ptr = args.pointer
    if not ptr.exists():
        _emit_status_line(STATUS_INVALID)
        print(f"ERR: pointer not found: {ptr}", file=sys.stderr)
        return 1

    d = parse_pointer(ptr)
    run_id = d.get("run_id")
    if not run_id:
        _emit_status_line(STATUS_INVALID)
        print("ERR: pointer missing run_id=", file=sys.stderr)
        return 1

    artifacts_root = args.out_base / run_id
    fetcher = fetch_artifacts or fetch_run_artifact_records
    downloader = download_run or download_run_artifacts

    if args.download:
        repo = resolve_repo(d)
        if not repo:
            _emit_status_line(STATUS_INVALID)
            print(
                "ERR: pointer missing repo= and GITHUB_REPOSITORY is unset",
                file=sys.stderr,
            )
            return 1
        try:
            records = fetcher(run_id, repo)
        except ArtifactFetchError as exc:
            _emit_status_line(STATUS_UNAVAILABLE_UNKNOWN)
            print(
                f"ERR: artifact metadata fetch failed ({exc.kind}): {exc}",
                file=sys.stderr,
            )
            return 1

        status = classify_artifact_records(records)
        _emit_status_line(status)
        print(f"REGISTRY_POINTER_RUN_ID={run_id}")
        print(f"REGISTRY_POINTER_ARTIFACT_COUNT={len(records)}")
        print(f"REGISTRY_POINTER_EXPIRED_COUNT={sum(1 for r in records if r.expired)}")
        print(f"REGISTRY_POINTER_AVAILABLE_COUNT={sum(1 for r in records if not r.expired)}")

        if status == STATUS_EXPIRED:
            _emit_expired_diagnostics(run_id, records)
            expires_at = next((r.expires_at for r in records if r.expires_at), "unknown")
            detail = (
                f"pinned historical artifacts for run_id={run_id} are expired "
                f"(expires_at={expires_at}); not a product/verification regression"
            )
            if args.allow_expired:
                print("REGISTRY_POINTER_EXPIRED_ALLOWED=true")
                print(f"INFO: {detail}; skipping download and invariant verification")
                _gha_warning("REGISTRY_POINTER_EXPIRED", detail)
                return 0
            print(f"ERR: {detail}. Re-run with --allow-expired for PR hygiene.", file=sys.stderr)
            return 1

        if status != STATUS_AVAILABLE:
            print(
                "ERR: registry pointer artifacts are not available "
                f"(status={status}, count={len(records)})",
                file=sys.stderr,
            )
            return 1

        try:
            downloader(run_id, artifacts_root)
        except ArtifactDownloadError as exc:
            print(
                "ERR: artifact metadata AVAILABLE but download failed: " + str(exc),
                file=sys.stderr,
            )
            return 1
    elif not artifacts_root.exists():
        print(
            f"ERR: artifacts missing at {artifacts_root}. Re-run with --download.",
            file=sys.stderr,
        )
        return 1

    verify_rc = _verify_summaries(artifacts_root)
    if verify_rc != 0:
        return verify_rc

    if args.pack_out:
        pack = args.pack_out
        pack.mkdir(parents=True, exist_ok=True)
        dest = pack / f"gh_run_{run_id}"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(artifacts_root, dest)
        sums = write_sha256sums(pack)
        print(f"OK: wrote {sums}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
