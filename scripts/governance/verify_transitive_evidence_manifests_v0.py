#!/usr/bin/env python3
"""Canonical offline transitive evidence MANIFEST verifier (v0).

Scope: offline-only bundle graph traversal + per-bundle MANIFEST.sha256 verification.
Hard boundary: does NOT perform any real archive traversal / extraction / economic evaluation.

Exit codes (stable):
0 = complete success
1 = manifest/reference verification failure
2 = invalid invocation or unsafe path
3 = bounded guard exceeded
4 = checkpoint invalid/corrupt
5 = internal deterministic contract violation
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Literal

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256


SCHEMA_VERSION = 1
PROGRESS_LOG_SCHEMA_VERSION = 1
MANIFEST_FILENAME = "MANIFEST.sha256"

DEFAULT_MAX_UNIQUE_BUNDLES = 5_000
DEFAULT_MAX_QUEUE_SIZE = 5_000
DEFAULT_MAX_REFERENCES_PER_BUNDLE = 500
DEFAULT_MAX_FILE_SIZE_BYTES = 512 * 1024  # conservative; bounded deterministic text parse
DEFAULT_PER_BUNDLE_TIMEOUT_SECONDS = 20

SUPPORTED_REFERENCE_BASENAMES = (
    "final_report.txt",
    "source_manifest_verification.txt",
    "preflight.txt",
    "closeout_report.txt",
    "manifest_verification.txt",
    "references.txt",
)
SUPPORTED_REFERENCE_SUFFIXES = (".json", ".jsonl", ".md")
SUPPORTED_REFERENCE_EXTRA_BASENAMES = (MANIFEST_FILENAME,)

CheckpointErrorCode = Literal[
    "CHECKPOINT_REFERENCE_NORMALIZED",
    "CHECKPOINT_CANONICAL_COLLISION_DEDUPLICATED",
    "CHECKPOINT_INVALID_REFERENCE_BLOCKED",
    "CHECKPOINT_ARCHIVE_ROOT_MISMATCH",
    "CHECKPOINT_ROOT_BUNDLE_MISMATCH",
    "CHECKPOINT_SCHEMA_UNSUPPORTED",
    "CHECKPOINT_ATOMIC_WRITE_FAILED",
]

CanonicalizeReasonCode = Literal[
    "NON_CANONICAL_REFERENCE_NORMALIZED",
    "NON_BUNDLE_REFERENCE_IGNORED",
    "RELATIVE_REFERENCE_BLOCKED",
    "REFERENCE_OUTSIDE_ARCHIVE_ROOT_BLOCKED",
    "URL_REFERENCE_IGNORED",
    "MANIFEST_FILE_REFERENCE_NORMALIZED",
    "DUPLICATE_CANONICAL_BUNDLE_REFERENCE_SKIPPED",
]

GuardReasonCode = Literal[
    "MAX_UNIQUE_BUNDLES_EXCEEDED",
    "MAX_QUEUE_SIZE_EXCEEDED",
    "MAX_REFERENCES_PER_BUNDLE_EXCEEDED",
    "FILE_SIZE_LIMIT_EXCEEDED",
    "CANONICAL_REFERENCE_EXPANSION_BLOCKED",
]

BundleStatus = Literal[
    "PASS",
    "MANIFEST_MISSING",
    "MANIFEST_VERIFY_FAILED",
    "MANIFEST_VERIFY_TIMEOUT",
    "REFERENCE_EXTRACTION_FAILED",
    "BLOCKED_UNSAFE_REFERENCE",
    "BLOCKED_LIMIT_EXCEEDED",
]


@dataclass(frozen=True)
class CanonicalizeDecision:
    canonical_dir: str | None
    reason_code: CanonicalizeReasonCode
    normalized: bool


@dataclass(frozen=True)
class BundleResult:
    canonical_key: str
    status: BundleStatus
    exit_code: int
    manifest_path: str
    verifier: str
    stdout: str
    stderr: str
    duration_ms: int
    references_found: int = 0
    references_accepted: int = 0
    normalized_reference_count: int = 0
    duplicate_reference_count: int = 0
    blocked_reference_count: int = 0
    blocked_reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunConfig:
    root_bundles: tuple[Path, ...]
    archive_root: Path
    output_dir: Path
    max_unique_bundles: int
    max_queue_size: int
    max_references_per_bundle: int
    max_file_size_bytes: int
    per_bundle_timeout_seconds: int
    resume_checkpoint: Path | None
    progress_log: Path | None
    reference_files: tuple[str, ...] | None


def _now_utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _is_probable_url(text: str) -> bool:
    lower = text.lower()
    return lower.startswith(("http://", "https://", "file://"))


_MD_CODE_WRAPPER_RE = re.compile(r"^\s*`{1,3}(.+?)`{1,3}\s*$")
_MD_LINK_RE = re.compile(r"^\s*\[(.*?)\]\((.+?)\)\s*$")
_QUOTE_WRAPPER_RE = re.compile(r"^\s*(['\"])(.*)\1\s*$")


def _strip_wrappers(raw: str) -> tuple[str, bool]:
    """Normalize common markdown/code wrappers. Returns (text, changed)."""
    before = raw
    text = raw.strip()
    changed = text != before

    # markdown link: [label](/abs/path)
    m = _MD_LINK_RE.match(text)
    if m:
        text = m.group(2).strip()
        changed = True

    # markdown code: `...` or ```...```
    m = _MD_CODE_WRAPPER_RE.match(text)
    if m:
        text = m.group(1).strip()
        changed = True

    # surrounding quotes
    m = _QUOTE_WRAPPER_RE.match(text)
    if m:
        text = m.group(2).strip()
        changed = True

    return text, changed


def _lexical_norm(path: str) -> str:
    # Expand ~, collapse //, normalize .. lexically.
    expanded = os.path.expanduser(path)
    return os.path.normpath(expanded)


def _is_within(root: Path, candidate: Path) -> bool:
    try:
        root_abs = root.absolute()
        cand_abs = candidate.absolute()
        return root_abs == cand_abs or root_abs in cand_abs.parents
    except OSError:
        return False


def canonicalize_bundle_reference(
    raw_reference: str,
    archive_root: Path,
    *,
    base_dir: Path | None = None,
) -> CanonicalizeDecision:
    """Canonicalize a raw bundle reference into an absolute directory key under archive_root.

    Contract: returns canonical absolute directory path (string) or None.
    """
    text, wrapper_changed = _strip_wrappers(raw_reference)
    normalized = wrapper_changed

    if not text:
        return CanonicalizeDecision(None, "NON_BUNDLE_REFERENCE_IGNORED", normalized)
    if _is_probable_url(text):
        return CanonicalizeDecision(None, "URL_REFERENCE_IGNORED", normalized)

    # Remove repeated trailing slashes
    stripped = text.rstrip("/")
    if stripped != text:
        text = stripped
        normalized = True

    # Resolve relative references deterministically against base_dir (when provided).
    if not text.startswith("/"):
        if base_dir is None:
            return CanonicalizeDecision(None, "RELATIVE_REFERENCE_BLOCKED", normalized)
        candidate = _lexical_norm(str((base_dir / text)))
        text = candidate
        normalized = True

    # Normalize MANIFEST file reference → parent dir
    if text.endswith("/" + MANIFEST_FILENAME) or text.endswith(os.sep + MANIFEST_FILENAME):
        text = str(Path(text).parent)
        normalized = True
        manifest_norm_reason: CanonicalizeReasonCode = "MANIFEST_FILE_REFERENCE_NORMALIZED"
    else:
        manifest_norm_reason = "NON_CANONICAL_REFERENCE_NORMALIZED"

    # Lexical normalize (no symlink resolution as identity)
    norm = _lexical_norm(text)
    if norm != text:
        normalized = True
    p = Path(norm)
    if not p.is_absolute():
        return CanonicalizeDecision(None, "RELATIVE_REFERENCE_BLOCKED", normalized)

    # Block escape via .. (lexical norm would have collapsed; enforce within root)
    if not _is_within(archive_root, p):
        return CanonicalizeDecision(None, "REFERENCE_OUTSIDE_ARCHIVE_ROOT_BLOCKED", normalized)

    # Only accept existing directories as bundles
    if not p.is_dir():
        # trailing punctuation normalization: only if the candidate doesn't exist,
        # and removing punctuation yields an existing directory under archive_root.
        candidate = str(p)
        trimmed = candidate.rstrip(".,);:!?]")
        if trimmed != candidate:
            p2 = Path(_lexical_norm(trimmed))
            if p2.is_absolute() and _is_within(archive_root, p2) and p2.is_dir():
                normalized = True
                return CanonicalizeDecision(str(p2.absolute()), manifest_norm_reason, normalized)
        return CanonicalizeDecision(None, "NON_BUNDLE_REFERENCE_IGNORED", normalized)

    return CanonicalizeDecision(str(p.absolute()), manifest_norm_reason, normalized)


_ABS_PATH_CANDIDATE_RE = re.compile(r"(/[^\s'\"`<>\)\]]+)")


def _supported_reference_files(
    bundle_dir: Path, reference_files: tuple[str, ...] | None
) -> list[Path]:
    files: list[Path] = []
    if reference_files:
        for name in reference_files:
            p = bundle_dir / name
            if p.is_file():
                files.append(p)
        return sorted(files, key=lambda x: x.name)

    # Default allowlist: explicit basenames and selected suffixes (deterministic)
    for name in SUPPORTED_REFERENCE_BASENAMES + SUPPORTED_REFERENCE_EXTRA_BASENAMES:
        p = bundle_dir / name
        if p.is_file():
            files.append(p)
    # deterministic scan: only direct children, by filename
    for p in sorted(bundle_dir.iterdir(), key=lambda x: x.name):
        if not p.is_file():
            continue
        if p.name in SUPPORTED_REFERENCE_BASENAMES or p.name in SUPPORTED_REFERENCE_EXTRA_BASENAMES:
            continue
        if any(p.name.endswith(sfx) for sfx in SUPPORTED_REFERENCE_SUFFIXES):
            files.append(p)
    return files


def _extract_raw_references_from_text(text: str) -> list[str]:
    # Deterministic order: find in file order, then match order.
    return [m.group(1) for m in _ABS_PATH_CANDIDATE_RE.finditer(text)]


def extract_bundle_references(
    *,
    bundle_dir: Path,
    archive_root: Path,
    max_references_per_bundle: int,
    max_file_size_bytes: int,
    reference_files: tuple[str, ...] | None,
) -> tuple[list[str], dict[str, Any]]:
    """Extract raw bundle reference strings from supported text artifacts within bundle_dir."""
    detail: dict[str, Any] = {
        "files_considered": [],
        "file_size_limit_bytes": max_file_size_bytes,
        "blocked_reason_codes": [],
    }
    refs: list[str] = []
    files = _supported_reference_files(bundle_dir, reference_files)
    detail["files_considered"] = [str(p) for p in files]

    for p in files:
        try:
            size = p.stat().st_size
        except OSError as exc:
            raise RuntimeError(f"stat_failed: {p}: {exc}") from exc
        if size > max_file_size_bytes:
            detail["blocked_reason_codes"].append("FILE_SIZE_LIMIT_EXCEEDED")
            raise ValueError(
                f"FILE_SIZE_LIMIT_EXCEEDED file={p} size={size} limit={max_file_size_bytes}"
            )

        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise RuntimeError(f"read_failed: {p}: {exc}") from exc
        if "\x00" in text:
            raise ValueError(f"REFERENCE_PARSE_FAILED nul_byte file={p}")

        for raw in _extract_raw_references_from_text(text):
            refs.append(raw)
            if len(refs) > max_references_per_bundle:
                detail["blocked_reason_codes"].append("MAX_REFERENCES_PER_BUNDLE_EXCEEDED")
                raise ValueError("MAX_REFERENCES_PER_BUNDLE_EXCEEDED")

    return refs, detail


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=path.name + ".tmp.",
            delete=False,
        ) as f:
            tmp = Path(f.name)
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    finally:
        # Best-effort cleanup if anything failed before replace.
        try:
            if "tmp" in locals() and tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


class ProgressLog:
    def __init__(self, path: Path, *, run_id: str) -> None:
        self._path = path
        self._run_id = run_id
        self._seq = 0

        if self._path.is_file():
            # Fail-closed on any corrupt existing line, and reject run_id reuse.
            for raw in self._path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"PROGRESS_LOG_INVALID corrupt_json: {exc}") from exc
                if not isinstance(obj, dict):
                    raise ValueError("PROGRESS_LOG_INVALID non_object_line")
                if obj.get("run_id") == self._run_id:
                    raise ValueError("PROGRESS_LOG_INVALID duplicate_run_id")

    def append(
        self,
        *,
        event_type: str,
        bundle_key: str | None = None,
        bundle_path: str | None = None,
        parent_bundle_key: str | None = None,
        result: str | None = None,
        reason_code: str | None = None,
        counts: dict[str, int] | None = None,
    ) -> None:
        self._seq += 1
        rec: dict[str, Any] = {
            "schema_version": PROGRESS_LOG_SCHEMA_VERSION,
            "timestamp_utc": _now_utc_iso(),
            "run_id": self._run_id,
            "sequence": self._seq,
            "event_type": event_type,
        }
        if bundle_key is not None:
            rec["bundle_key"] = bundle_key
        if bundle_path is not None:
            rec["bundle_path"] = bundle_path
        if parent_bundle_key is not None:
            rec["parent_bundle_key"] = parent_bundle_key
        if result is not None:
            rec["result"] = result
        if reason_code is not None:
            rec["reason_code"] = reason_code
        if counts is not None:
            rec["counts"] = dict(counts)
        _append_jsonl(self._path, rec)


def _default_output_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "run_contract": output_dir / "run_contract.json",
        "bundle_results": output_dir / "bundle_results.jsonl",
        "graph_summary": output_dir / "graph_summary.json",
        "checkpoint": output_dir / "checkpoint.json",
        "progress": output_dir / "progress.jsonl",
        "final_report": output_dir / "final_report.txt",
    }


def _load_checkpoint(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"checkpoint_read_failed: {exc}") from exc


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("expected list")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("expected list[str]")
        out.append(item)
    return out


def _validate_and_normalize_checkpoint(
    *,
    checkpoint: dict[str, Any],
    archive_root: Path,
    root_bundle: Path,
    expected_limits: dict[str, int],
) -> tuple[list[str], set[str], dict[str, Any], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    schema = checkpoint.get("schema_version")
    if schema != SCHEMA_VERSION:
        raise ValueError(f"CHECKPOINT_SCHEMA_UNSUPPORTED expected={SCHEMA_VERSION} got={schema!r}")

    if str(checkpoint.get("archive_root")) != str(archive_root.absolute()):
        raise ValueError("CHECKPOINT_ARCHIVE_ROOT_MISMATCH")
    if str(checkpoint.get("root_bundle")) != str(root_bundle.absolute()):
        raise ValueError("CHECKPOINT_ROOT_BUNDLE_MISMATCH")

    limits = checkpoint.get("limits") or {}
    if not isinstance(limits, dict):
        raise ValueError("CHECKPOINT_SCHEMA_UNSUPPORTED")
    for k, v in expected_limits.items():
        if limits.get(k) != v:
            raise ValueError("CHECKPOINT_SCHEMA_UNSUPPORTED")

    queue_raw = _coerce_str_list(checkpoint.get("queue"))
    visited_raw = _coerce_str_list(checkpoint.get("visited"))
    results_summary = checkpoint.get("results_summary") or {}
    if not isinstance(results_summary, dict):
        raise ValueError("checkpoint results_summary invalid")

    queue: list[str] = []
    visited: set[str] = set()

    def _accept_key(raw: str, kind: str) -> str:
        decision = canonicalize_bundle_reference(raw, archive_root=archive_root)
        if decision.canonical_dir is None:
            raise ValueError("CHECKPOINT_INVALID_REFERENCE_BLOCKED")
        if decision.normalized:
            events.append(
                {
                    "timestamp_utc": _now_utc_iso(),
                    "event": "CHECKPOINT_NORMALIZED",
                    "reason_code": "CHECKPOINT_REFERENCE_NORMALIZED",
                    "kind": kind,
                }
            )
        return decision.canonical_dir

    for raw in queue_raw:
        key = _accept_key(raw, "queue")
        if key in visited:
            continue
        if key in queue:
            events.append(
                {
                    "timestamp_utc": _now_utc_iso(),
                    "event": "CHECKPOINT_DEDUP",
                    "reason_code": "CHECKPOINT_CANONICAL_COLLISION_DEDUPLICATED",
                    "kind": "queue",
                }
            )
            continue
        queue.append(key)

    for raw in visited_raw:
        key = _accept_key(raw, "visited")
        visited.add(key)

    # Remove any queued keys that are already visited (deterministic)
    queue = [k for k in queue if k not in visited]

    return queue, visited, results_summary, events


def _write_checkpoint(
    *,
    path: Path,
    run_id: str,
    config: RunConfig,
    queue: list[str],
    visited: set[str],
    results_summary: dict[str, Any],
    implementation_sha_or_version: str,
) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "archive_root": str(config.archive_root.absolute()),
        "root_bundle": str(config.root_bundles[0].absolute()),
        "limits": {
            "max_unique_bundles": config.max_unique_bundles,
            "max_queue_size": config.max_queue_size,
            "max_references_per_bundle": config.max_references_per_bundle,
            "max_file_size_bytes": config.max_file_size_bytes,
            "per_bundle_timeout_seconds": config.per_bundle_timeout_seconds,
        },
        "queue": list(queue),
        "visited": sorted(visited),
        "results_summary": dict(results_summary),
        "created_at_utc": results_summary.get("created_at_utc") or _now_utc_iso(),
        "updated_at_utc": _now_utc_iso(),
        "implementation_sha_or_version": implementation_sha_or_version,
    }
    _atomic_write_json(path, payload)


def _write_run_contract(path: Path, *, run_id: str, config: RunConfig, implementation: str) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at_utc": _now_utc_iso(),
        "root_bundles": [str(p.absolute()) for p in config.root_bundles],
        "archive_root": str(config.archive_root.absolute()),
        "output_dir": str(config.output_dir.absolute()),
        "implementation_sha_or_version": implementation,
        "non_execution_attestation": {
            "REAL_ARCHIVE_TRAVERSAL_EXECUTED": False,
            "TRANSITIVE_MANIFEST_VERIFICATION_EXECUTED": False,
            "ECONOMIC_EVALUATION_EXECUTED": False,
            "RUNTIME_EFFECT": "NONE",
            "AUTHORITY_EFFECT": "NONE",
        },
        "guards": {
            "max_unique_bundles": config.max_unique_bundles,
            "max_queue_size": config.max_queue_size,
            "max_references_per_bundle": config.max_references_per_bundle,
            "max_file_size_bytes": config.max_file_size_bytes,
            "per_bundle_timeout_seconds": config.per_bundle_timeout_seconds,
        },
        "checkpoint_resume": {
            "resume_checkpoint": str(config.resume_checkpoint)
            if config.resume_checkpoint
            else None,
        },
        "progress_log": {
            "path": str(config.progress_log) if config.progress_log else None,
            "append_only": True,
            "truncation_allowed": False,
        },
    }
    _atomic_write_json(path, payload)


def _write_final_report(path: Path, *, summary: dict[str, Any]) -> None:
    lines: list[str] = []
    for k in (
        "VERDICT",
        "RUN_ID",
        "ROOT_BUNDLE",
        "ARCHIVE_ROOT",
        "IMPLEMENTATION_SHA",
        "TOTAL_DISCOVERED_CANONICAL_BUNDLES",
        "TOTAL_VISITED_BUNDLES",
        "TOTAL_PASS",
        "TOTAL_FAILED",
        "TOTAL_BLOCKED",
        "DUPLICATE_REFERENCE_COUNT",
        "NORMALIZED_REFERENCE_COUNT",
        "CHECKPOINT_USED",
        "BOUNDED_GUARD_TRIGGERED",
        "SOURCE_BUNDLES_MUTATED",
    ):
        lines.append(f"{k}={summary.get(k)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_graph_summary(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_json(path, payload)


def _iter_bundle_results_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        yield json.loads(line)


def _append_bundle_result(path: Path, result: BundleResult) -> None:
    rec = dataclasses.asdict(result)
    rec["timestamp_utc"] = _now_utc_iso()
    _append_jsonl(path, rec)


def verify_transitively(config: RunConfig) -> tuple[int, dict[str, Any]]:
    implementation = "verify_transitive_evidence_manifests_v0"
    run_id = uuid.uuid4().hex

    out_paths = _default_output_paths(config.output_dir)
    checkpoint_path = out_paths["checkpoint"]
    progress_path = config.progress_log or out_paths["progress"]
    bundle_results_path = out_paths["bundle_results"]
    graph_summary_path = out_paths["graph_summary"]
    final_report_path = out_paths["final_report"]
    run_contract_path = out_paths["run_contract"]

    # Pre-validate unsafe output location: must not be inside any root bundle.
    for rb in config.root_bundles:
        if _is_within(rb, config.output_dir):
            return 2, {"error": "unsafe output-dir (inside root bundle)", "exit_code": 2}

    _write_run_contract(
        run_contract_path, run_id=run_id, config=config, implementation=implementation
    )

    try:
        progress = ProgressLog(progress_path, run_id=run_id)
    except ValueError as exc:
        return 4, {"error": str(exc), "exit_code": 4}

    progress.append(event_type="RUN_BEGIN")

    # Canonicalize root bundles (deterministic order)
    root_keys: list[str] = []
    for raw in sorted([str(p) for p in config.root_bundles]):
        dec = canonicalize_bundle_reference(raw, archive_root=config.archive_root)
        if dec.canonical_dir is None:
            progress.append(event_type="RUN_FAILED", reason_code=dec.reason_code)
            return 2, {"error": "invalid root bundle", "exit_code": 2}
        root_keys.append(dec.canonical_dir)
        progress.append(
            event_type="ROOT_ACCEPTED",
            bundle_key=dec.canonical_dir,
            bundle_path=dec.canonical_dir,
            reason_code=dec.reason_code if dec.normalized else None,
        )

    checkpoint_used = False
    results_summary: dict[str, Any] = {"created_at_utc": _now_utc_iso()}

    if config.resume_checkpoint:
        checkpoint_used = True
        ck = _load_checkpoint(config.resume_checkpoint)
        try:
            queue, visited, results_summary_loaded, ck_events = _validate_and_normalize_checkpoint(
                checkpoint=ck,
                archive_root=config.archive_root,
                root_bundle=Path(root_keys[0]),
                expected_limits={
                    "max_unique_bundles": config.max_unique_bundles,
                    "max_queue_size": config.max_queue_size,
                    "max_references_per_bundle": config.max_references_per_bundle,
                    "max_file_size_bytes": config.max_file_size_bytes,
                    "per_bundle_timeout_seconds": config.per_bundle_timeout_seconds,
                },
            )
        except ValueError as exc:
            progress.append(event_type="RUN_FAILED", reason_code=str(exc))
            return 4, {"error": f"checkpoint invalid: {exc}", "exit_code": 4}
        results_summary = dict(results_summary_loaded)
        for ev in ck_events:
            progress.append(
                event_type=str(ev.get("event") or "CHECKPOINT_EVENT"),
                reason_code=str(ev.get("reason_code") or ""),
            )
    else:
        queue = list(sorted(set(root_keys)))
        visited = set()

    queued_keys = set(queue)

    normalized_reference_count = 0
    duplicate_reference_count = 0
    blocked_reference_count = 0
    bounded_guard_triggered = False
    guard_reason: GuardReasonCode | None = None

    total_pass = 0
    total_failed = 0
    total_blocked = 0

    while queue:
        if len(visited) >= config.max_unique_bundles:
            bounded_guard_triggered = True
            guard_reason = "MAX_UNIQUE_BUNDLES_EXCEEDED"
            break
        if len(queue) > config.max_queue_size:
            bounded_guard_triggered = True
            guard_reason = "MAX_QUEUE_SIZE_EXCEEDED"
            break

        key = queue.pop(0)
        queued_keys.discard(key)
        if key in visited:
            continue
        visited.add(key)

        progress.append(
            event_type="BUNDLE_DEQUEUED",
            bundle_key=key,
            bundle_path=key,
            counts={"queue": len(queue), "visited": len(visited)},
        )

        bundle_dir = Path(key)
        manifest_path = bundle_dir / MANIFEST_FILENAME
        if not manifest_path.is_file():
            result = BundleResult(
                canonical_key=key,
                status="MANIFEST_MISSING",
                exit_code=1,
                manifest_path=str(manifest_path),
                verifier="scripts/ops/primary_evidence_retention_v0.verify_manifest_sha256",
                stdout="",
                stderr="MANIFEST.sha256 missing",
                duration_ms=0,
            )
            total_failed += 1
            _append_bundle_result(bundle_results_path, result)
            progress.append(
                event_type="MANIFEST_VERIFY_RESULT",
                bundle_key=key,
                bundle_path=key,
                result=result.status,
            )
            continue

        # Reference extraction (bounded) before manifest verify; still read-only within bundle.
        try:
            raw_refs, extract_detail = extract_bundle_references(
                bundle_dir=bundle_dir,
                archive_root=config.archive_root,
                max_references_per_bundle=config.max_references_per_bundle,
                max_file_size_bytes=config.max_file_size_bytes,
                reference_files=config.reference_files,
            )
        except ValueError as exc:
            # guard exceeded (file size / max refs)
            bounded_guard_triggered = True
            guard_reason = (
                "FILE_SIZE_LIMIT_EXCEEDED" if "FILE_SIZE_LIMIT_EXCEEDED" in str(exc) else None
            )
            if guard_reason is None and "MAX_REFERENCES_PER_BUNDLE_EXCEEDED" in str(exc):
                guard_reason = "MAX_REFERENCES_PER_BUNDLE_EXCEEDED"
            blocked = BundleResult(
                canonical_key=key,
                status="BLOCKED_LIMIT_EXCEEDED",
                exit_code=3,
                manifest_path=str(manifest_path),
                verifier="shasum -a 256 -c MANIFEST.sha256",
                stdout="",
                stderr=str(exc),
                duration_ms=0,
                references_found=0,
                references_accepted=0,
                blocked_reference_count=0,
                blocked_reason_codes=tuple(extract_detail.get("blocked_reason_codes", []))
                if "extract_detail" in locals()
                else (),
            )
            total_blocked += 1
            _append_bundle_result(bundle_results_path, blocked)
            break
        except Exception as exc:
            failed = BundleResult(
                canonical_key=key,
                status="REFERENCE_EXTRACTION_FAILED",
                exit_code=1,
                manifest_path=str(manifest_path),
                verifier="shasum -a 256 -c MANIFEST.sha256",
                stdout="",
                stderr=str(exc),
                duration_ms=0,
            )
            total_failed += 1
            _append_bundle_result(bundle_results_path, failed)
            continue

        # Canonicalize + deduplicate
        accepted_keys: list[str] = []
        accepted_set: set[str] = set()
        normalized_here = 0
        dup_here = 0
        blocked_here = 0
        blocked_reason_codes: list[str] = []

        for raw in raw_refs:
            decision = canonicalize_bundle_reference(
                raw, archive_root=config.archive_root, base_dir=bundle_dir
            )
            if decision.canonical_dir is None:
                blocked_here += 1
                blocked_reason_codes.append(decision.reason_code)
                continue
            if decision.normalized:
                normalized_here += 1
            can = decision.canonical_dir
            if can == key:
                continue  # self reference does not requeue
            if can in accepted_set:
                dup_here += 1
                continue
            accepted_set.add(can)
            accepted_keys.append(can)

        # deterministic: sort before queue insertion
        accepted_keys = sorted(accepted_keys)

        # Enqueue newly discovered canonical keys (only once)
        for can in accepted_keys:
            if can in visited or can in queued_keys:
                continue
            queue.append(can)
            queued_keys.add(can)

        # Manifest verify (repo-canonical primitive; bounded by per-bundle wallclock guard)
        started = time.monotonic()
        ok, msg = verify_manifest_sha256(bundle_dir)
        dur_ms = int((time.monotonic() - started) * 1000)
        if dur_ms > config.per_bundle_timeout_seconds * 1000:
            result = BundleResult(
                canonical_key=key,
                status="MANIFEST_VERIFY_TIMEOUT",
                exit_code=1,
                manifest_path=str(manifest_path),
                verifier="scripts/ops/primary_evidence_retention_v0.verify_manifest_sha256",
                stdout="",
                stderr="timeout",
                duration_ms=dur_ms,
                references_found=len(raw_refs),
                references_accepted=len(accepted_keys),
                normalized_reference_count=normalized_here,
                duplicate_reference_count=dup_here,
                blocked_reference_count=blocked_here,
                blocked_reason_codes=tuple(sorted(set(blocked_reason_codes))),
            )
            total_failed += 1
        else:
            if ok:
                status = "PASS"
                total_pass += 1
            else:
                status = "MANIFEST_VERIFY_FAILED"
                total_failed += 1
            result = BundleResult(
                canonical_key=key,
                status=status,
                exit_code=0 if ok else 1,
                manifest_path=str(manifest_path),
                verifier="scripts/ops/primary_evidence_retention_v0.verify_manifest_sha256",
                stdout="",
                stderr=msg,
                duration_ms=dur_ms,
                references_found=len(raw_refs),
                references_accepted=len(accepted_keys),
                normalized_reference_count=normalized_here,
                duplicate_reference_count=dup_here,
                blocked_reference_count=blocked_here,
                blocked_reason_codes=tuple(sorted(set(blocked_reason_codes))),
            )

        normalized_reference_count += normalized_here
        duplicate_reference_count += dup_here
        blocked_reference_count += blocked_here

        _append_bundle_result(bundle_results_path, result)
        progress.append(
            event_type="REFERENCE_SUMMARY",
            bundle_key=key,
            bundle_path=key,
            counts={
                "raw": len(raw_refs),
                "accepted": len(accepted_keys),
                "normalized": normalized_here,
                "duplicate": dup_here,
                "blocked": blocked_here,
            },
        )
        progress.append(
            event_type="MANIFEST_VERIFY_RESULT",
            bundle_key=key,
            bundle_path=key,
            result=result.status,
            counts={"pass": total_pass, "failed": total_failed, "blocked": total_blocked},
        )

        # Checkpoint after each visited bundle (safe append-only progress + atomic checkpoint)
        try:
            results_summary = {
                **results_summary,
                "total_pass": total_pass,
                "total_failed": total_failed,
                "total_blocked": total_blocked,
            }
            _write_checkpoint(
                path=checkpoint_path,
                run_id=run_id,
                config=config,
                queue=queue,
                visited=visited,
                results_summary=results_summary,
                implementation_sha_or_version=implementation,
            )
        except Exception as exc:
            progress.append(event_type="RUN_FAILED", reason_code="CHECKPOINT_ATOMIC_WRITE_FAILED")
            return 4, {"error": "checkpoint write failed", "exit_code": 4}
        else:
            progress.append(
                event_type="CHECKPOINT_WRITTEN",
                counts={"queue": len(queue), "visited": len(visited)},
            )

    if bounded_guard_triggered:
        progress.append(
            event_type="LIMIT_BLOCKED",
            reason_code=str(guard_reason),
            counts={"queue": len(queue), "visited": len(visited)},
        )

    discovered = len(visited) + len(queue)
    verdict = (
        "PASS"
        if (total_failed == 0 and total_blocked == 0 and not bounded_guard_triggered)
        else "FAIL"
    )
    report_summary = {
        "VERDICT": verdict,
        "RUN_ID": run_id,
        "ROOT_BUNDLE": root_keys[0] if root_keys else None,
        "ARCHIVE_ROOT": str(config.archive_root.absolute()),
        "IMPLEMENTATION_SHA": implementation,
        "TOTAL_DISCOVERED_CANONICAL_BUNDLES": discovered,
        "TOTAL_VISITED_BUNDLES": len(visited),
        "TOTAL_PASS": total_pass,
        "TOTAL_FAILED": total_failed,
        "TOTAL_BLOCKED": total_blocked,
        "DUPLICATE_REFERENCE_COUNT": duplicate_reference_count,
        "NORMALIZED_REFERENCE_COUNT": normalized_reference_count,
        "CHECKPOINT_USED": checkpoint_used,
        "BOUNDED_GUARD_TRIGGERED": bounded_guard_triggered,
        "SOURCE_BUNDLES_MUTATED": False,
    }
    _write_final_report(final_report_path, summary=report_summary)
    _write_graph_summary(
        graph_summary_path,
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "root_bundle": root_keys[0] if root_keys else None,
            "archive_root": str(config.archive_root.absolute()),
            "queue_remaining": len(queue),
            "visited": len(visited),
            "pass": total_pass,
            "failed": total_failed,
            "blocked": total_blocked,
            "bounded_guard_triggered": bounded_guard_triggered,
            "guard_reason": guard_reason,
        },
    )

    progress.append(
        event_type="RUN_COMPLETE" if verdict == "PASS" else "RUN_FAILED",
        counts={
            "visited": len(visited),
            "queue_remaining": len(queue),
            "pass": total_pass,
            "failed": total_failed,
            "blocked": total_blocked,
        },
    )

    if bounded_guard_triggered:
        return 3, {
            "exit_code": 3,
            "run_id": run_id,
            "guard_reason": guard_reason,
            "summary": report_summary,
        }
    if verdict != "PASS":
        return 1, {"exit_code": 1, "run_id": run_id, "summary": report_summary}
    return 0, {"exit_code": 0, "run_id": run_id, "summary": report_summary}


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Canonical offline transitive evidence MANIFEST verifier (v0).",
    )
    p.add_argument(
        "--root-bundle",
        required=True,
        action="append",
        type=Path,
        help="Absolute path to a root bundle directory (repeatable).",
    )
    p.add_argument(
        "--archive-root", required=True, type=Path, help="Absolute archive root containing bundles."
    )
    p.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Absolute output directory (must not be source).",
    )
    p.add_argument("--max-unique-bundles", type=int, default=DEFAULT_MAX_UNIQUE_BUNDLES)
    p.add_argument("--max-queue-size", type=int, default=DEFAULT_MAX_QUEUE_SIZE)
    p.add_argument(
        "--max-references-per-bundle", type=int, default=DEFAULT_MAX_REFERENCES_PER_BUNDLE
    )
    p.add_argument("--resume-checkpoint", type=Path, default=None)
    p.add_argument("--progress-log", type=Path, default=None)
    p.add_argument(
        "--reference-files",
        type=str,
        default=None,
        help="Comma-separated basenames to scan (optional).",
    )
    return p


def _require_abs_dir(path: Path, *, name: str) -> tuple[bool, str]:
    if not path.is_absolute():
        return False, f"{name} must be absolute"
    if not path.is_dir():
        return False, f"{name} missing or not a directory: {path}"
    return True, ""


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    ok, msg = _require_abs_dir(args.archive_root, name="archive-root")
    if not ok:
        print(f"VERIFY_TRANSITIVE_MANIFESTS_FAIL: {msg}")
        return 2
    root_bundles: list[Path] = list(args.root_bundle or [])
    for rb in root_bundles:
        ok, msg = _require_abs_dir(rb, name="root-bundle")
        if not ok:
            print(f"VERIFY_TRANSITIVE_MANIFESTS_FAIL: {msg}")
            return 2
    ok, msg = _require_abs_dir(args.output_dir, name="output-dir")
    if not ok:
        # output-dir may be non-existent; allow creation if absolute and safe
        if not args.output_dir.is_absolute():
            print("VERIFY_TRANSITIVE_MANIFESTS_FAIL: output-dir must be absolute")
            return 2
        try:
            args.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"VERIFY_TRANSITIVE_MANIFESTS_FAIL: output-dir create failed: {exc}")
            return 2

    for rb in root_bundles:
        if not _is_within(args.archive_root, rb):
            print("VERIFY_TRANSITIVE_MANIFESTS_FAIL: root-bundle must be within archive-root")
            return 2

    ref_files: tuple[str, ...] | None
    if args.reference_files:
        items = [x.strip() for x in args.reference_files.split(",") if x.strip()]
        ref_files = tuple(items) if items else None
    else:
        ref_files = None

    config = RunConfig(
        root_bundles=tuple(root_bundles),
        archive_root=args.archive_root,
        output_dir=args.output_dir,
        max_unique_bundles=int(args.max_unique_bundles),
        max_queue_size=int(args.max_queue_size),
        max_references_per_bundle=int(args.max_references_per_bundle),
        max_file_size_bytes=DEFAULT_MAX_FILE_SIZE_BYTES,
        per_bundle_timeout_seconds=DEFAULT_PER_BUNDLE_TIMEOUT_SECONDS,
        resume_checkpoint=args.resume_checkpoint,
        progress_log=args.progress_log,
        reference_files=ref_files,
    )

    rc, _detail = verify_transitively(config)
    return int(rc)


if __name__ == "__main__":
    raise SystemExit(main())
