#!/usr/bin/env python3
"""Default-off skeleton for a future Shadow 24/7 Futures *perpetual* start wrapper.

This module is intentionally **not** a daemon, does not touch the scheduler at runtime,
does not open network or broker paths, and **always** exits fail-closed until a separate
governance implementation replaces this placeholder.

Importing this file has no side effects beyond loading this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import tempfile
import time

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python < 3.11 in CI
    import tomli as tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence, TextIO, Tuple

# -----------------------------------------------------------------------------
# Safety / scope constants (documentation + static-test anchors; not authority)
# -----------------------------------------------------------------------------

BOUNDARY_NO_LIVE = "NO_LIVE"
BOUNDARY_NO_TESTNET_UNLESS_APPROVED = "NO_TESTNET_UNLESS_SEPARATELY_APPROVED"
BOUNDARY_NO_BROKER = "NO_BROKER"
BOUNDARY_NO_PRIVATE_EXCHANGE = "NO_PRIVATE_EXCHANGE_ENDPOINT"
# Verbatim governance substring anchors (aliases; not additional policy).
NO_EXCHANGE = BOUNDARY_NO_PRIVATE_EXCHANGE
BOUNDARY_NO_ORDER_SUBMISSION = "NO_ORDER_SUBMISSION"
BOUNDARY_NO_NETWORK = "NO_NETWORK"
BOUNDARY_FUTURES_PERP_SCOPE = "FUTURES_OR_PERPETUAL_SCOPE_REQUIRED"
BOUNDARY_EVIDENCE_ROOT_TMP = "/tmp/peak_trade_* evidence root convention"
BOUNDARY_SUPERVISOR_LATER = "SUPERVISOR_TIMEOUT_REQUIRED_IN_FUTURE_GATE"
BOUNDARY_ABORT_LATER = "ABORT_STOP_CRITERIA_REQUIRED_IN_FUTURE_GATE"

EXIT_FAIL_CLOSED_DEFAULT = 64
EXIT_CODE_FAIL_CLOSED = EXIT_FAIL_CLOSED_DEFAULT
EXIT_DRYCHECK_SUCCESS = 0

PRESTART_SCHEMA_V0 = "shadow_247_futures_prestart_evidence_drycheck_v0"
PRESTART_MARKDOWN_ARTIFACT_V0 = "SHADOW_247_FUTURES_PRESTART_EVIDENCE_DRYCHECK.md"
PRESTART_MANIFEST_JSON_V0 = "manifest.json"
PRESTART_MANIFEST_SHA256_V0 = "MANIFEST.sha256"

# Bounded-runtime contract placeholder (non-executing; manifest/markdown annotations only).
BOUNDED_RUNTIME_CONTRACT_VERSION_EMBEDDED = "shadow_247_futures_bounded_runtime_contract.v0"
BOUNDED_RUNTIME_CONTRACT_DURATION_CAP_MINUTES = 30

# Local bounded Shadow dry-run (simulated steps only; no broker/network/exchange/orders).
BOUNDED_SHADOW_DRY_RUN_SCHEMA_V0 = "shadow_247_futures_bounded_shadow_dry_run.v0"
BOUNDED_SHADOW_DRY_RUN_MARKDOWN_V0 = "SHADOW_247_FUTURES_BOUNDED_SHADOW_DRY_RUN.md"
BOUNDED_SHADOW_STEPS_JSONL_V0 = "steps.jsonl"
BOUNDED_SHADOW_DURATION_CAP_MINUTES = 10
BOUNDED_SHADOW_MAX_STEPS_CAP = 600
BOUNDED_SHADOW_STEP_INTERVAL_MAX_SECONDS = 60.0

# Governed extended tier: longer wall-clock bounded dry-run only (explicit flags + token).
BOUNDED_SHADOW_EXTENDED_DURATION_CAP_MINUTES = 60
BOUNDED_SHADOW_EXTENDED_MAX_STEPS_CAP = 3600
EXTENDED_BOUNDED_SHADOW_CONFIRM_TOKEN_V0 = (
    "I_EXPLICITLY_CONFIRM_SHADOW_247_EXTENDED_BOUNDED_SHADOW_60M_TIER_V0"
)

# Governed 24h candidate tier: capped bounded dry-run only (explicit flag + distinct token; default-off).
BOUNDED_SHADOW_24H_CANDIDATE_DURATION_CAP_MINUTES = 1440
BOUNDED_SHADOW_24H_CANDIDATE_MAX_STEPS_CAP = 86400
CANDIDATE_24H_BOUNDED_SHADOW_CONFIRM_TOKEN_V0 = (
    "I_EXPLICITLY_CONFIRM_SHADOW_247_CANDIDATE_24H_BOUNDED_SHADOW_TIER_V0"
)

BOUNDED_SHADOW_RECORDED_PUBLIC_REST_REPLAY_HEARTBEAT_KIND = (
    "bounded_shadow_dry_run_recorded_public_rest_replay_heartbeat"
)
_RECORDED_PUBLIC_REST_SOURCE_JSON_SCAN_CAP = 512

_BOUNDED_SHADOW_ALLOWED_ENTRIES = frozenset(
    {
        BOUNDED_SHADOW_DRY_RUN_MARKDOWN_V0,
        BOUNDED_SHADOW_STEPS_JSONL_V0,
        PRESTART_MANIFEST_JSON_V0,
        PRESTART_MANIFEST_SHA256_V0,
    },
)

_DRYCHECK_ALLOWED_ENTRIES = frozenset(
    {PRESTART_MARKDOWN_ARTIFACT_V0, PRESTART_MANIFEST_JSON_V0, PRESTART_MANIFEST_SHA256_V0},
)

_OPS_CFG_EXPECT_BOOLS: Mapping[str, bool] = {
    "enabled": False,
    "armed": False,
    "dry_run": True,
    "shadow_mode": True,
    "live_allowed": False,
    "testnet_allowed": False,
    "network_allowed": False,
    "broker_allowed": False,
    "exchange_allowed": False,
    "order_submission_allowed": False,
    "private_exchange_endpoint_allowed": False,
    "credentials_allowed": False,
}
_OPS_EXPECT_STR = {"instrument": "BTCUSDT", "market_type": "futures"}
_OPS_EXPECT_SCRIPT = "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"

_SHADOW_FUTURES_SCHEDULER_JOB_V0 = "shadow_247_futures_prestart_evidence_drycheck_placeholder_v0"

# Future-only gate token (explicit operator string). **Presence does NOT enable runtime.**
FUTURE_OPERATOR_CONFIRMATION_TOKEN_V0 = (
    "I_EXPLICITLY_CONFIRM_SHADOW_247_FUTURES_START_WRAPPER_BEYOND_DEFAULT_OFF_SKELETON_V0"
)

_REPO_ROOT_CALC = Path(__file__).resolve().parents[2]

_MACHINE_LINES_ALWAYS = """\
RUN_STARTED=false
SCHEDULER_STARTED=false
RUNTIME_STARTED=false
READY_TO_START_FUTURES_SHADOW_247_DAEMON=false
SKELETON_ONLY=true
NETWORK_USED=false
BROKER_USED=false
EXCHANGE_USED=false
ORDER_SUBMISSION_USED=false
"""

# Local bounded Shadow dry-run only (verbatim machine block written into that mode's manifest/Markdown).
_BOUNDED_SHADOW_MACHINE_LINES = """\
RUN_STARTED=true
SCHEDULER_STARTED=false
RUNTIME_STARTED=false
SHADOW_STARTED=true
TESTNET_STARTED=false
LIVE_STARTED=false
NETWORK_USED=false
BROKER_USED=false
EXCHANGE_USED=false
ORDER_SUBMISSION_USED=false
CREDENTIALS_USED=false
EXECUTION_APPROVED=false
DRY_RUN=true
SHADOW_MODE=true
READY_TO_START_FUTURES_SHADOW_247_DAEMON=false
SKELETON_ONLY=true
"""


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Shadow 24/7 Futures start-wrapper **skeleton** (fail-closed, no runtime)."),
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Print documented boundaries and diagnostic machine lines only.",
    )
    parser.add_argument(
        "--prestart-evidence-drycheck",
        action="store_true",
        dest="prestart_evidence_drycheck",
        help=("Write local prestart evidence under --evidence-root only (still no daemon start)."),
    )
    parser.add_argument(
        "--bounded-runtime-contract-check",
        action="store_true",
        dest="bounded_runtime_contract_check",
        help=(
            "Write the same local prestart evidence artefacts with bounded-runtime contract "
            "metadata only (non-executing; requires --duration-minutes and confirm-token)."
        ),
    )
    parser.add_argument(
        "--bounded-shadow-dry-run",
        action="store_true",
        dest="bounded_shadow_dry_run",
        help=(
            "Local bounded Shadow dry-run simulation (no scheduler, broker, exchange, network, "
            "orders, or credentials; requires confirm-token, dual config, evidence-root)."
        ),
    )
    parser.add_argument(
        "--duration-minutes",
        type=int,
        default=None,
        help=(
            "With `--bounded-runtime-contract-check`: duration (1–"
            f"{BOUNDED_RUNTIME_CONTRACT_DURATION_CAP_MINUTES}). "
            "With `--bounded-shadow-dry-run` (default tier): duration (1–"
            f"{BOUNDED_SHADOW_DURATION_CAP_MINUTES}). "
            "With `--bounded-shadow-dry-run` plus `--extended-bounded-shadow-validation`: duration (1–"
            f"{BOUNDED_SHADOW_EXTENDED_DURATION_CAP_MINUTES}). "
            "With `--bounded-shadow-dry-run` plus `--candidate-24h-bounded-shadow-validation`: duration (1–"
            f"{BOUNDED_SHADOW_24H_CANDIDATE_DURATION_CAP_MINUTES}). "
            "Otherwise invalid."
        ),
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help=(
            "With `--bounded-shadow-dry-run` only: step budget; default tier 1–"
            f"{BOUNDED_SHADOW_MAX_STEPS_CAP}, extended tier 1–{BOUNDED_SHADOW_EXTENDED_MAX_STEPS_CAP}, "
            f"24h candidate tier 1–{BOUNDED_SHADOW_24H_CANDIDATE_MAX_STEPS_CAP} "
            "(default ~12× duration minutes, capped to active tier)."
        ),
    )
    parser.add_argument(
        "--step-interval-seconds",
        type=float,
        default=None,
        metavar="SECONDS",
        dest="step_interval_seconds",
        help=(
            "`--bounded-shadow-dry-run` only: wall-clock seconds between simulated steps "
            f"(0–{BOUNDED_SHADOW_STEP_INTERVAL_MAX_SECONDS:g}; default 0 for fast local tests)."
        ),
    )
    parser.add_argument(
        "--confirm-token",
        metavar="TOKEN",
        default="",
        help=(
            "Optional future governance token placeholder. Skeleton still exits "
            f"{EXIT_FAIL_CLOSED_DEFAULT} unless a gated evidence / bounded-shadow mode succeeds. "
            "Bounded modes require an exact token match."
        ),
    )
    parser.add_argument(
        "--extended-bounded-shadow-validation",
        action="store_true",
        dest="extended_bounded_shadow_validation",
        help=(
            "With `--bounded-shadow-dry-run` only: enable governed extended tier (dry-run only; "
            f"duration ≤{BOUNDED_SHADOW_EXTENDED_DURATION_CAP_MINUTES}m; max-steps ≤"
            f"{BOUNDED_SHADOW_EXTENDED_MAX_STEPS_CAP}). Requires `--extended-confirm-token`. "
            "Default-off; standard tier caps remain 10m / 600 steps when omitted."
        ),
    )
    parser.add_argument(
        "--extended-confirm-token",
        metavar="TOKEN",
        default="",
        dest="extended_confirm_token",
        help=(
            "With `--bounded-shadow-dry-run` + `--extended-bounded-shadow-validation` only. "
            "Must match the extended-tier governance literal (distinct from `--confirm-token`)."
        ),
    )
    parser.add_argument(
        "--candidate-24h-bounded-shadow-validation",
        action="store_true",
        dest="candidate_24h_bounded_shadow_validation",
        help=(
            "With `--bounded-shadow-dry-run` only: enable governed 24h **candidate** tier (dry-run only; "
            f"duration ≤{BOUNDED_SHADOW_24H_CANDIDATE_DURATION_CAP_MINUTES}m; max-steps ≤"
            f"{BOUNDED_SHADOW_24H_CANDIDATE_MAX_STEPS_CAP}). Mutually exclusive with "
            "`--extended-bounded-shadow-validation`. Requires `--candidate-24h-confirm-token`."
        ),
    )
    parser.add_argument(
        "--candidate-24h-confirm-token",
        metavar="TOKEN",
        default="",
        dest="candidate_24h_confirm_token",
        help=(
            "With `--bounded-shadow-dry-run` + `--candidate-24h-bounded-shadow-validation` only. "
            "Must match the 24h-candidate-tier governance literal (distinct from other confirm tokens)."
        ),
    )
    parser.add_argument(
        "--evidence-root",
        metavar="PATH",
        default="",
        help=(
            "Optional `/tmp/peak_trade_*`-style absolute path, or required with evidence / "
            "bounded modes (`--prestart-evidence-drycheck`, `--bounded-runtime-contract-check`, "
            "`--bounded-shadow-dry-run`)."
        ),
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default="",
        dest="ops_config_path",
        help=(
            "**With `--prestart-evidence-drycheck`, `--bounded-runtime-contract-check`, or "
            "`--bounded-shadow-dry-run`.** "
            "Read-only validate default-off Ops skeleton (`shadow_247_futures_wrapper_skeleton`) "
            "invariants via stdlib tomllib (path must lie under repo root)."
        ),
    )
    parser.add_argument(
        "--jobs-config",
        metavar="PATH",
        default="",
        dest="jobs_config_path",
        help=(
            "**With `--prestart-evidence-drycheck`, `--bounded-runtime-contract-check`, or "
            "`--bounded-shadow-dry-run`.** "
            "Read-only validate the disabled scheduler placeholder row (stdlib tomllib)."
        ),
    )
    parser.add_argument(
        "--recorded-public-rest-source",
        metavar="PATH",
        default="",
        dest="recorded_public_rest_source",
        help=(
            "`--bounded-shadow-dry-run` only: absolute path to an existing directory of local "
            "public-REST gate artefacts (read-only inventory; no network, capture, bridge, "
            "nor supervised observer)."
        ),
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _resolve_repo_relative_file(repo_root: Path, path_str: str) -> Tuple[Path | None, str | None]:
    """Resolve a filesystem path strictly under ``repo_root``; return (path, None) or (None, err)."""
    trimmed = path_str.strip()
    if not trimmed:
        return None, "empty configuration path argument"
    if ".." in Path(trimmed).parts:
        return None, "config path must not contain path traversal segments"
    candidate = Path(trimmed).expanduser()
    repo_resolved = repo_root.resolve()
    merged = candidate if candidate.is_absolute() else (repo_resolved / candidate)
    try:
        resolved = merged.resolve(strict=True)
    except (FileNotFoundError, OSError, RuntimeError):
        return None, f"cannot resolve readable file under repo: {candidate}"
    if not resolved.is_relative_to(repo_resolved):
        return None, "config files must reside under the repository checkout root"
    if not resolved.is_file():
        return None, "config path must be a regular existing file inside the repo"
    return resolved, None


def _validate_shadow_futures_ops_doc(doc: Mapping[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(doc, Mapping):
        return ["ops config root document is not a TOML table"]

    if doc.get("schema_version") != "shadow_247_futures_wrapper_skeleton.v0":
        errs.append(
            f"schema_version must be shadow_247_futures_wrapper_skeleton.v0 "
            f"(got {doc.get('schema_version')!r})"
        )

    for key, expect in _OPS_CFG_EXPECT_BOOLS.items():
        if key not in doc:
            errs.append(f"missing ops key `{key}`")
            continue
        obs = doc[key]
        if not isinstance(obs, bool):
            errs.append(f"expected boolean for `{key}` (got `{type(obs).__name__}`)")
            continue
        if obs != expect:
            errs.append(f"`{key}` mismatch: requires {expect!r}, observed {obs!r}")

    if "paper_allowed" in doc:
        pa = doc["paper_allowed"]
        if isinstance(pa, bool):
            if pa is not False:
                errs.append("`paper_allowed` must be false when present")
        else:
            errs.append("`paper_allowed` must be boolean when present")

    for key, expect in _OPS_EXPECT_STR.items():
        obs = doc.get(key)
        if not isinstance(obs, str):
            errs.append(f"expected string for `{key}` (got {type(obs).__name__})")
        elif obs != expect:
            errs.append(f"`{key}` mismatch: requires {expect!r}, observed {obs!r}")

    if doc.get("perpetual_scope") is not True:
        errs.append(f"`perpetual_scope` must be true (got {doc.get('perpetual_scope')!r})")

    obs_script = doc.get("wrapper_script")
    if obs_script != _OPS_EXPECT_SCRIPT:
        errs.append(
            f"`wrapper_script` mismatch: requires {_OPS_EXPECT_SCRIPT!r}, observed {obs_script!r}",
        )

    if "wrapper_daemon_start_allowed" in doc:
        wds = doc["wrapper_daemon_start_allowed"]
        if isinstance(wds, bool):
            if wds is not False:
                errs.append("`wrapper_daemon_start_allowed` must be false when present")
        else:
            errs.append("`wrapper_daemon_start_allowed` must be boolean when present")

    if "immediate_execution_approved" in doc:
        ie = doc["immediate_execution_approved"]
        if isinstance(ie, bool):
            if ie is not False:
                errs.append("`immediate_execution_approved` must be false when present")
        else:
            errs.append("`immediate_execution_approved` must be boolean when present")

    conv = doc.get("evidence_root_convention")
    if not isinstance(conv, str) or "/tmp/peak_trade_" not in conv:
        errs.append("`evidence_root_convention` must mention `/tmp/peak_trade_*` convention")

    return errs


def _validate_shadow_futures_jobs_placeholder(doc: Mapping[str, Any]) -> list[str]:
    errs: list[str] = []
    rows = doc.get("job")
    if rows is None:
        return ["`jobs.toml` missing `job` tables"]
    if not isinstance(rows, list):
        return [f"`job` tables must decode to a list (got `{type(rows).__name__}`)"]

    found: Mapping[str, Any] | None = None
    for row in rows:
        if isinstance(row, Mapping) and row.get("name") == _SHADOW_FUTURES_SCHEDULER_JOB_V0:
            found = row
            break
    if found is None:
        return [
            (
                "scheduler placeholder job "
                f"{_SHADOW_FUTURES_SCHEDULER_JOB_V0!r} not present in `--jobs-config` tables"
            ),
        ]

    if found.get("enabled") is not False:
        errs.append(
            "`enabled` mismatch for Futures placeholder job: requires false, observed "
            f"{found.get('enabled')!r}",
        )

    args = found.get("args")
    if not isinstance(args, Mapping):
        errs.append("placeholder job `args` missing or not a table")
        return errs
    scr = args.get("script")
    if scr != _OPS_EXPECT_SCRIPT:
        errs.append(
            f"placeholder args.script mismatch: requires {_OPS_EXPECT_SCRIPT!r}, observed {scr!r}",
        )
    return errs


def _build_readonly_validation_block(
    repo_root: Path,
    ops_path_arg: str,
    jobs_path_arg: str,
) -> Tuple[dict[str, Any], list[str]]:
    """Produce JSON-serializable validation summary plus combined blocking errors."""

    blk: dict[str, Any] = {
        "ops_config_provided": bool(ops_path_arg.strip()),
        "ops_config_absolute": None,
        "ops_validation_errors": [],
        "jobs_config_provided": bool(jobs_path_arg.strip()),
        "jobs_config_absolute": None,
        "jobs_validation_errors": [],
        "combined_validation_ok": True,
    }
    errs: list[str] = []

    if blk["ops_config_provided"]:
        p, perr = _resolve_repo_relative_file(repo_root, ops_path_arg)
        if perr or p is None:
            assert perr is not None
            blk["ops_validation_errors"] = [perr]
            errs.append(perr)
            blk["combined_validation_ok"] = False
        else:
            blk["ops_config_absolute"] = str(p)
            raw = p.read_bytes()
            try:
                doc = tomllib.loads(raw.decode("utf-8"))
            except tomllib.TOMLDecodeError as exc:
                msg = f"ops TOML decode error: {exc}"
                blk["ops_validation_errors"] = [msg]
                errs.append(msg)
                blk["combined_validation_ok"] = False
            else:
                oerrs = _validate_shadow_futures_ops_doc(doc)
                blk["ops_validation_errors"] = oerrs
                if oerrs:
                    errs.extend(oerrs)
                    blk["combined_validation_ok"] = False

    if blk["jobs_config_provided"]:
        p, perr = _resolve_repo_relative_file(repo_root, jobs_path_arg)
        if perr or p is None:
            assert perr is not None
            blk["jobs_validation_errors"] = [perr]
            errs.append(perr)
            blk["combined_validation_ok"] = False
        else:
            blk["jobs_config_absolute"] = str(p)
            raw = p.read_bytes()
            try:
                doc = tomllib.loads(raw.decode("utf-8"))
            except tomllib.TOMLDecodeError as exc:
                msg = f"jobs TOML decode error: {exc}"
                blk["jobs_validation_errors"] = [msg]
                errs.append(msg)
                blk["combined_validation_ok"] = False
            else:
                jerrs = _validate_shadow_futures_jobs_placeholder(doc)
                blk["jobs_validation_errors"] = jerrs
                if jerrs:
                    errs.extend(jerrs)
                    blk["combined_validation_ok"] = False

    return blk, errs


def _readonly_validation_markdown_lines(val: Mapping[str, Any]) -> list[str]:
    lines: list[str] = [
        "## Read-only config validation (local; not an execution approval)\n\n",
    ]
    if not val["ops_config_provided"] and not val["jobs_config_provided"]:
        lines.append(
            "- Config paths not supplied — validation **skipped** (drycheck evidence only).\n\n",
        )
        return lines

    if val["ops_config_provided"]:
        ap = val["ops_config_absolute"]
        oerrs = val["ops_validation_errors"]
        state = "PASS" if not oerrs else "FAIL"
        lines.append(f"- Ops skeleton (`--config`): **{state}** — `{ap}`\n")
        if oerrs:
            for e in oerrs:
                lines.append(f"  - Error: `{e}`\n")
        lines.append("\n")

    if val["jobs_config_provided"]:
        jp = val["jobs_config_absolute"]
        jerrs = val["jobs_validation_errors"]
        state = "PASS" if not jerrs else "FAIL"
        lines.append(
            f"- Scheduler placeholder (`--jobs-config`): **{state}** — `{jp}`\n",
        )
        if jerrs:
            for e in jerrs:
                lines.append(f"  - Error: `{e}`\n")
        lines.append("\n")

    assert isinstance(val["combined_validation_ok"], bool)
    lines.append(
        f"- Combined validation OK: **{str(val['combined_validation_ok']).lower()}**\n\n",
    )
    return lines


def _validate_evidence_root(path_str: str) -> str | None:
    """Return error message string if invalid for non-starting modes, else None."""
    if not path_str:
        return None
    normalized = path_str.strip()
    if ".." in normalized:
        return "evidence-root must not contain path traversal"
    probe = Path(normalized).expanduser()
    if not probe.is_absolute():
        return "evidence-root must be absolute for convention checks when supplied"
    try:
        resolved = probe.resolve()
        tmp_anchor = Path("/tmp").resolve()
        rel = resolved.relative_to(tmp_anchor)
    except (ValueError, OSError, RuntimeError):
        return "evidence-root must use /tmp/peak_trade_* operator convention when supplied"
    if not rel.parts or not rel.parts[0].lower().startswith("peak_trade"):
        return "evidence-root must use /tmp/peak_trade_* operator convention when supplied"
    return None


def _is_hex_sha40(value: str) -> bool:
    cand = value[:40].lower()
    return len(cand) == 40 and all(ch in "0123456789abcdef" for ch in cand)


def _resolve_git_metadata_dirs(
    repo_root: Path,
) -> Tuple[Path | None, Path | None, str | None]:
    """Resolve per-worktree git dir and shared commondir (filesystem-only)."""
    dot_git = repo_root / ".git"
    if dot_git.is_dir():
        return dot_git.resolve(), dot_git.resolve(), None
    if dot_git.is_file():
        raw = dot_git.read_text(encoding="utf-8", errors="replace").strip()
        if not raw.startswith("gitdir:"):
            return None, None, "UNKNOWN_GITFILE_LAYOUT"
        gitdir_raw = raw[len("gitdir:") :].strip()
        if not gitdir_raw:
            return None, None, "UNKNOWN_GITDIR_MISSING"
        gitdir_path = Path(gitdir_raw)
        if not gitdir_path.is_absolute():
            gitdir_path = (repo_root / gitdir_path).resolve()
        else:
            try:
                gitdir_path = gitdir_path.resolve()
            except (OSError, RuntimeError):
                return None, None, "UNKNOWN_GITDIR_UNRESOLVABLE"
        if not gitdir_path.is_dir():
            return None, None, "UNKNOWN_GITDIR_MISSING"
        common_dir = gitdir_path
        commondir_file = gitdir_path / "commondir"
        if commondir_file.is_file():
            common_raw = commondir_file.read_text(encoding="utf-8", errors="replace").strip()
            if common_raw:
                common_path = Path(common_raw)
                if not common_path.is_absolute():
                    common_path = (gitdir_path / common_path).resolve()
                else:
                    try:
                        common_path = common_path.resolve()
                    except (OSError, RuntimeError):
                        return None, None, "UNKNOWN_COMMONDIR_UNRESOLVABLE"
                if not common_path.is_dir():
                    return None, None, "UNKNOWN_COMMONDIR_MISSING"
                common_dir = common_path
        return gitdir_path, common_dir, None
    return None, None, "UNKNOWN"


def _read_packed_ref_sha(git_dir: Path, ref: str) -> str | None:
    packed = git_dir / "packed-refs"
    if not packed.is_file():
        return None
    for line in packed.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("^"):
            continue
        parts = stripped.split()
        if len(parts) >= 2 and parts[1] == ref and _is_hex_sha40(parts[0]):
            return parts[0][:40].lower()
    return None


def _read_loose_or_packed_ref_sha(
    git_dir: Path,
    common_dir: Path,
    ref: str,
) -> str | None:
    for base in (git_dir, common_dir):
        ref_path = base / ref
        if ref_path.is_file():
            sha = ref_path.read_text(encoding="utf-8", errors="replace").strip()
            if not sha:
                return None
            if sha.startswith("ref: "):
                return _read_loose_or_packed_ref_sha(git_dir, common_dir, sha[5:].strip())
            if _is_hex_sha40(sha):
                return sha[:40].lower()
            return None
        packed_sha = _read_packed_ref_sha(base, ref)
        if packed_sha is not None:
            return packed_sha
    return None


def _git_incomplete_state_token(git_dir: Path, common_dir: Path) -> str | None:
    for base in (git_dir, common_dir):
        for marker in (
            "MERGE_HEAD",
            "CHERRY_PICK_HEAD",
            "REBASE_HEAD",
            "REBASE_MERGE",
        ):
            if (base / marker).exists():
                return "UNKNOWN_INCOMPLETE_GIT_STATE"
        if (base / "index.lock").is_file():
            return "UNKNOWN_GIT_INDEX_LOCKED"
    return None


def _read_git_sha_prefix(repo_root: Path, maxlen: int = 12) -> str:
    git_dir, common_dir, layout_err = _resolve_git_metadata_dirs(repo_root)
    if layout_err is not None:
        return layout_err
    assert git_dir is not None and common_dir is not None

    incomplete = _git_incomplete_state_token(git_dir, common_dir)
    if incomplete is not None:
        return incomplete

    head_file = git_dir / "HEAD"
    if not head_file.is_file():
        return "UNKNOWN_HEAD_MISSING"
    raw = head_file.read_text(encoding="utf-8", errors="replace").strip()
    if raw.startswith("ref: "):
        ref = raw[5:].strip()
        if not ref:
            return "UNKNOWN_REF_MISSING"
        sha = _read_loose_or_packed_ref_sha(git_dir, common_dir, ref)
        if sha is None:
            return "UNKNOWN_REF_MISSING"
        return sha[:maxlen]
    if _is_hex_sha40(raw):
        return raw[:maxlen]
    return "UNKNOWN_RAW_HEAD_LAYOUT"


def _evidence_has_paper_or_test_hints(path_chars: str) -> bool:
    lower = path_chars.lower()
    hints = (
        "/paper/",
        "/paper_trade",
        "paper_trading/",
        "/test_data/",
        "/testdata/",
        "/fixtures/",
        "pytest_legacy",
        "live_trading",
    )
    return any(part in lower for part in hints)


def _validate_evidence_root_for_drycheck(
    path_str: str, repo_root: Path
) -> Tuple[Path | None, str | None]:
    trimmed = path_str.strip()
    if not trimmed:
        return None, "prestart-evidence-drycheck requires a non-empty --evidence-root"
    probe = Path(trimmed).expanduser()
    if not probe.is_absolute():
        return None, "evidence-root must be an absolute path for prestart-evidence-drycheck"
    try:
        resolved = probe.resolve()
    except (OSError, RuntimeError):
        return None, "evidence-root cannot be resolved safely"

    rr = repo_root.resolve()
    try:
        tmp_anchor = Path("/tmp").resolve()
        rel_to_tmp = resolved.relative_to(tmp_anchor)
    except (ValueError, OSError, RuntimeError):
        return None, (
            "evidence-root must resolve somewhere under filesystem `/tmp` after symlink normalization."
        )
    if not rel_to_tmp.parts:
        return None, "evidence-root has empty relative path under `/tmp`."
    top_seg = rel_to_tmp.parts[0].lower()
    if not top_seg.startswith("peak_trade_"):
        return (
            None,
            "evidence-root first directory segment under `/tmp` must start with "
            "`peak_trade_` for prestart-evidence-drycheck.",
        )
    rstr = str(resolved)

    if resolved == rr:
        return None, "evidence-root must not equal the Peak_Trade repository root"
    if resolved.is_relative_to(rr):
        return None, "evidence-root must not reside inside the repository tree"

    if ".git" in resolved.parts:
        return None, "evidence-root must not traverse a `.git` path segment"

    if _evidence_has_paper_or_test_hints(rstr):
        return None, "evidence-root path hints at paper/test fixtures — forbidden for this drycheck"

    if resolved.is_file():
        return None, "evidence-root must be a directory, not an existing file"

    if resolved.exists():
        entries = sorted(p.name for p in resolved.iterdir())
        if entries and set(entries) != _DRYCHECK_ALLOWED_ENTRIES:
            bad = sorted(set(entries) - _DRYCHECK_ALLOWED_ENTRIES)
            return (
                None,
                f"evidence-root directory is non-empty with unexpected entries: {bad!r}",
            )

    return resolved, None


def _validate_evidence_root_for_bounded_shadow(
    path_str: str, repo_root: Path
) -> Tuple[Path | None, str | None]:
    """Same hygiene as `/tmp` drycheck, but allow bounded-shadow artefact filenames."""
    trimmed = path_str.strip()
    if not trimmed:
        return None, "bounded-shadow-dry-run requires a non-empty --evidence-root"
    probe = Path(trimmed).expanduser()
    if not probe.is_absolute():
        return None, "evidence-root must be an absolute path for bounded-shadow-dry-run"
    try:
        resolved = probe.resolve()
    except (OSError, RuntimeError):
        return None, "evidence-root cannot be resolved safely"

    rr = repo_root.resolve()
    try:
        tmp_anchor = Path("/tmp").resolve()
        rel_to_tmp = resolved.relative_to(tmp_anchor)
    except (ValueError, OSError, RuntimeError):
        return None, (
            "evidence-root must resolve somewhere under filesystem `/tmp` after symlink normalization."
        )
    if not rel_to_tmp.parts:
        return None, "evidence-root has empty relative path under `/tmp`."
    top_seg = rel_to_tmp.parts[0].lower()
    if not top_seg.startswith("peak_trade_"):
        return (
            None,
            "evidence-root first directory segment under `/tmp` must start with "
            "`peak_trade_` for bounded-shadow-dry-run.",
        )
    rstr = str(resolved)

    if resolved == rr:
        return None, "evidence-root must not equal the Peak_Trade repository root"
    if resolved.is_relative_to(rr):
        return None, "evidence-root must not reside inside the repository tree"

    if ".git" in resolved.parts:
        return None, "evidence-root must not traverse a `.git` path segment"

    if _evidence_has_paper_or_test_hints(rstr):
        return (
            None,
            "evidence-root path hints at paper/test fixtures — forbidden for bounded-shadow",
        )

    if resolved.is_file():
        return None, "evidence-root must be a directory, not an existing file"

    if resolved.exists():
        entries = sorted(p.name for p in resolved.iterdir())
        if entries and set(entries) != _BOUNDED_SHADOW_ALLOWED_ENTRIES:
            bad = sorted(set(entries) - _BOUNDED_SHADOW_ALLOWED_ENTRIES)
            return (
                None,
                f"evidence-root directory is non-empty with unexpected entries: {bad!r}",
            )

    return resolved, None


def _is_allowed_recorded_public_rest_source_root(path: Path) -> bool:
    """Allow `/tmp/peak_trade_*` and `/tmp/pytest-*`, else non-`/tmp` paths under `tempfile`."""
    resolved = path.resolve()
    tmp_root = Path("/tmp").resolve()
    tempfile_root = Path(tempfile.gettempdir()).resolve()

    try:
        relative_to_tmp = resolved.relative_to(tmp_root)
    except ValueError:
        relative_to_tmp = None

    if relative_to_tmp is not None:
        if not relative_to_tmp.parts:
            return False
        top_segment = relative_to_tmp.parts[0].lower()
        return top_segment.startswith("peak_trade_") or top_segment.startswith("pytest-")

    if tempfile_root == tmp_root:
        return False

    try:
        resolved.relative_to(tempfile_root)
    except ValueError:
        return False
    return True


def _validate_recorded_public_rest_source(
    path_str: str, repo_root: Path
) -> Tuple[Path | None, str | None]:
    """Local directory only: under `/tmp` (`peak_trade_*` / `pytest-*`) or stdlib temp dir."""
    trimmed = path_str.strip()
    if not trimmed:
        return None, "`--recorded-public-rest-source` must be non-empty when provided"
    if ".." in Path(trimmed).parts:
        return None, "recorded-public-rest-source must not contain path traversal segments"

    probe = Path(trimmed).expanduser()
    if not probe.is_absolute():
        return None, "recorded-public-rest-source must be an absolute path"
    try:
        resolved = probe.resolve(strict=True)
    except FileNotFoundError:
        return None, "recorded-public-rest-source path does not exist"
    except (OSError, RuntimeError):
        return None, "recorded-public-rest-source cannot be resolved safely"

    if not resolved.is_dir():
        return None, "recorded-public-rest-source must be a directory"

    rr = repo_root.resolve()
    if resolved == rr or resolved.is_relative_to(rr):
        return None, "recorded-public-rest-source must not reside inside the repository tree"

    if ".git" in resolved.parts:
        return None, "recorded-public-rest-source must not traverse a `.git` path segment"

    if not _is_allowed_recorded_public_rest_source_root(resolved):
        return (
            None,
            "recorded-public-rest-source must resolve under `/tmp` with a top-level segment "
            "starting with `peak_trade_` or `pytest-`, or resolve under the process temporary "
            "directory (stdlib `tempfile`) when it is not the filesystem `/tmp`.",
        )

    return resolved, None


def _inventory_recorded_public_rest_source(source_dir: Path) -> dict[str, Any]:
    manifest_paths = sorted({p for p in source_dir.rglob("manifest.json") if p.is_file()})
    json_paths = sorted({p for p in source_dir.rglob("*.json") if p.is_file()})
    truncated = len(json_paths) > _RECORDED_PUBLIC_REST_SOURCE_JSON_SCAN_CAP
    subset = json_paths[:_RECORDED_PUBLIC_REST_SOURCE_JSON_SCAN_CAP]
    rows: list[dict[str, str]] = []
    for p in subset:
        rel = p.relative_to(source_dir).as_posix()
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        rows.append({"relative_path": rel, "sha256": digest})
    rows.sort(key=lambda r: r["relative_path"])
    files_digest = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "recorded_public_rest_source_path": str(source_dir),
        "recorded_public_rest_source_exists": True,
        "recorded_public_rest_source_manifest_count": len(manifest_paths),
        "recorded_public_rest_source_json_count": len(json_paths),
        "recorded_public_rest_source_json_scan_truncated": truncated,
        "recorded_public_rest_source_files_digest_sha256": files_digest,
    }


def _canonical_json_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _drycheck_manifest(
    evidence_abs: Path,
    repo_sha: str,
    utc_now: datetime,
    readonly_cfg_block: Mapping[str, Any],
    bounded_extra: Mapping[str, Any] | None = None,
) -> dict:
    base_claim = (
        "No run, scheduler, daemon, network, broker, exchange, orders, shadow/paper/testnet/live "
        "workloads — evidence only."
    )
    if readonly_cfg_block.get("ops_config_provided") or readonly_cfg_block.get(
        "jobs_config_provided"
    ):
        claim = (
            base_claim + " Read-only Ops / scheduler-placeholder TOML invariants asserted locally."
        )
    else:
        claim = base_claim

    manifest: MutableMapping[str, Any] = {
        "artifact": PRESTART_SCHEMA_V0,
        "broker_used": False,
        "daemon_run_approved": False,
        "evidence_root_absolute": str(evidence_abs),
        "exchange_used": False,
        "executor": "peak_trade/scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py",
        "futures_perpetual_planning_scope_only": True,
        "git_sha_prefix": repo_sha,
        "markdown_artifact_filename": PRESTART_MARKDOWN_ARTIFACT_V0,
        "network_used": False,
        "order_submission_used": False,
        "prestart_claims_summary": claim,
        "readonly_local_config_skeleton_validation": dict(readonly_cfg_block),
        "ready_to_start_futures_shadow_247_daemon": False,
        "run_started": False,
        "runtime_started": False,
        "scheduler_started": False,
        "utc_generated": utc_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verbatim_machine_summary": _MACHINE_LINES_ALWAYS.rstrip("\n"),
        "wrapper_requires_future_gate_before_execution": True,
    }
    if bounded_extra is not None:
        manifest["bounded_runtime_contract_check"] = True
        manifest["duration_minutes_requested"] = int(bounded_extra["duration_minutes"])
        manifest["duration_minutes_cap_enforced"] = int(bounded_extra["duration_cap"])
        manifest["bounded_runtime_contract_version"] = str(bounded_extra["contract_version"])
    return manifest


def _drycheck_markdown(
    utc_now: datetime,
    evidence_abs: Path,
    repo_sha: str,
    readonly_cfg_block: Mapping[str, Any],
    bounded_extra: Mapping[str, Any] | None = None,
) -> str:
    core = "".join(
        (
            "# Shadow 24-7 Futures — Prestart Evidence Drycheck (Local)\n\n",
            f"UTC: `{utc_now.strftime('%Y-%m-%dT%H:%M:%SZ')}`  \n",
            f"Evidence root: `{evidence_abs}`  \n",
            f"Repository git SHA prefix hint: `{repo_sha}` (best-effort, filesystem read).\n\n",
            "## Statements (non-binding; planning evidence only)\n\n",
            "- No live, testnet, paper, shadow, or production runtime started.\n",
            "- No scheduler or daemon spawned.\n",
            "- No network, broker API, exchange private endpoint access, nor order submission.\n",
            "- Futures/perpetual execution scope remains planning-only pending future gates.\n",
            "- Wrapper is **not** `READY_TO_START` for Futures Shadow 24/7 daemon.\n\n",
            "## Operator machine summary (verbatim keys)\n\n",
            "```text\n",
            _MACHINE_LINES_ALWAYS,
            "```\n\n",
            *_readonly_validation_markdown_lines(readonly_cfg_block),
            "## Appendix\n\n",
            "Drycheck artefacts: `manifest.json`, `MANIFEST.sha256`. "
            "`MANIFEST.sha256` covers canonical UTF-8 bytes of sorted-key pretty JSON manifest.\n",
        ),
    )
    if bounded_extra is None:
        return core
    insert = (
        "## Bounded runtime contract check (placeholder; non-executing)\n\n"
        f"- Duration requested: `{bounded_extra['duration_minutes']}` minute(s) "
        f"(cap `{bounded_extra['duration_cap']}`).\n"
        f"- Contract version: `{bounded_extra['contract_version']}`.\n"
        "- No scheduler, daemon, runtime, shadow, testnet, or live workloads started.\n\n"
    )
    anchor = "## Operator machine summary (verbatim keys)\n\n"
    if anchor not in core:
        return core
    return core.replace(anchor, insert + anchor, 1)


def _execute_prestart_drycheck(
    evidence_root_abs: Path,
    repo_root: Path,
    err: TextIO,
    readonly_cfg_block: Mapping[str, Any],
    bounded_extra: Mapping[str, Any] | None = None,
) -> int:
    utc_now = datetime.now(timezone.utc)
    repo_sha = _read_git_sha_prefix(repo_root)
    manifest = _drycheck_manifest(
        evidence_root_abs, repo_sha, utc_now, readonly_cfg_block, bounded_extra
    )

    manifest_bytes = _canonical_json_bytes(manifest)
    digest_hex = hashlib.sha256(manifest_bytes).hexdigest()

    md_text = _drycheck_markdown(
        utc_now, evidence_root_abs, repo_sha, readonly_cfg_block, bounded_extra
    )

    evidence_root_abs.mkdir(parents=True, exist_ok=True)
    md_path = evidence_root_abs / PRESTART_MARKDOWN_ARTIFACT_V0
    mj_path = evidence_root_abs / PRESTART_MANIFEST_JSON_V0
    sh_path = evidence_root_abs / PRESTART_MANIFEST_SHA256_V0

    md_path.write_text(md_text, encoding="utf-8")
    mj_path.write_bytes(manifest_bytes)
    sh_path.write_text(digest_hex + "\n", encoding="utf-8")

    err.write(_MACHINE_LINES_ALWAYS)
    if readonly_cfg_block.get("ops_config_provided") or readonly_cfg_block.get(
        "jobs_config_provided"
    ):
        err.write("READONLY_OPS_OR_JOBS_CONFIG_VALIDATED=true\n")
        err.write("READONLY_CONFIG_VALIDATION_OK=true\n")
    else:
        err.write("READONLY_OPS_OR_JOBS_CONFIG_VALIDATED=false\n")
        err.write("READONLY_CONFIG_VALIDATION_OK=skipped\n")

    if bounded_extra is not None:
        err.write("BOUNDED_RUNTIME_CONTRACT_CHECK_WRITTEN=true\n")

    err.write(
        "PRESTART_EVIDENCE_DRYCHECK_WRITTEN=true\nEXIT_CODE={}\n".format(EXIT_DRYCHECK_SUCCESS)
    )
    return EXIT_DRYCHECK_SUCCESS


def _bounded_shadow_markdown(
    utc_now: datetime,
    evidence_abs: Path,
    repo_sha: str,
    readonly_cfg_block: Mapping[str, Any],
    run_meta: Mapping[str, Any],
    recorded_meta: Mapping[str, Any] | None = None,
) -> str:
    recorded_block: tuple[str, ...] = ()
    if recorded_meta is not None:
        recorded_block = (
            "## Recorded public REST replay source (local cross-link; read-only)\n\n",
            f"- Source path: `{recorded_meta['recorded_public_rest_source_path']}`  \n",
            f"- Exists: `{recorded_meta['recorded_public_rest_source_exists']}`\n",
            f"- `manifest.json` files found: `{recorded_meta['recorded_public_rest_source_manifest_count']}`\n",
            f"- JSON files found: `{recorded_meta['recorded_public_rest_source_json_count']}`\n",
            f"- JSON inventory scan truncated: `{recorded_meta['recorded_public_rest_source_json_scan_truncated']}`\n",
            f"- Per-file digest summary SHA-256: `{recorded_meta['recorded_public_rest_source_files_digest_sha256']}`\n",
            "- No network, capture, bridge, nor supervised-observer scripts are invoked in this mode.\n\n",
        )
    return "".join(
        (
            "# Shadow 24-7 Futures — Bounded Shadow Dry-Run (Local Simulation)\n\n",
            f"UTC start: `{utc_now.strftime('%Y-%m-%dT%H:%M:%SZ')}`  \n",
            f"Evidence root: `{evidence_abs}`  \n",
            f"Repository git SHA prefix hint: `{repo_sha}` (best-effort, filesystem read).\n\n",
            "## Statements (non-binding; local simulation only)\n\n",
            "- No live, testnet, broker, exchange, private endpoints, credentials, or network I/O.\n",
            "- No scheduler or daemon spawned; no execution session; no order submission.\n",
            "- Simulated bounded step loop only — not an exchange/broker runtime.\n\n",
            "## Safety boundary markers (canonical)\n\n",
            f"- {BOUNDARY_NO_BROKER}\n",
            f"- {BOUNDARY_NO_NETWORK}\n",
            f"- {BOUNDARY_NO_ORDER_SUBMISSION}\n\n",
            "## Operator machine summary (verbatim keys)\n\n",
            "```text\n",
            _BOUNDED_SHADOW_MACHINE_LINES,
            "```\n\n",
            "## Run parameters\n\n",
            f"- Duration requested (minutes): `{run_meta['duration_minutes']}`\n",
            f"- Duration cap enforced (minutes): `{run_meta['duration_minutes_cap_enforced']}`\n",
            f"- Extended bounded tier: `{run_meta.get('extended_bounded_shadow_validation', False)}`\n",
            f"- Candidate 24h bounded tier: `{run_meta.get('candidate_24h_bounded_shadow_validation', False)}`\n",
            f"- Step budget: `{run_meta['max_steps']}`\n",
            f"- Step budget cap enforced: `{run_meta['max_steps_cap_enforced']}`\n",
            f"- Step interval (seconds): `{run_meta['step_interval_seconds']}`\n",
            f"- Steps emitted: `{run_meta['steps_emitted']}`\n",
            f"- UTC end: `{run_meta['utc_end']}`\n\n",
            *recorded_block,
            *_readonly_validation_markdown_lines(readonly_cfg_block),
            "## Appendix\n\n",
            "Artefacts: `manifest.json`, `MANIFEST.sha256`, "
            f"`{BOUNDED_SHADOW_DRY_RUN_MARKDOWN_V0}`, optional `{BOUNDED_SHADOW_STEPS_JSONL_V0}`. "
            "`MANIFEST.sha256` covers canonical UTF-8 bytes of sorted-key pretty JSON manifest.\n",
        ),
    )


def _bounded_shadow_manifest(
    evidence_abs: Path,
    repo_sha: str,
    utc_started: datetime,
    utc_ended: datetime,
    readonly_cfg_block: Mapping[str, Any],
    run_meta: Mapping[str, Any],
    recorded_meta: Mapping[str, Any] | None = None,
) -> dict:
    manifest: dict[str, Any] = {
        "artifact": BOUNDED_SHADOW_DRY_RUN_SCHEMA_V0,
        "schema": BOUNDED_SHADOW_DRY_RUN_SCHEMA_V0,
        BOUNDARY_NO_BROKER: True,
        BOUNDARY_NO_NETWORK: True,
        BOUNDARY_NO_ORDER_SUBMISSION: True,
        "bounded_local_shadow_dry_run": True,
        "broker_used": False,
        "credentials_used": False,
        "daemon_run_approved": False,
        "dry_run": True,
        "duration_minutes_requested": int(run_meta["duration_minutes"]),
        "duration_minutes_cap_enforced": int(run_meta["duration_minutes_cap_enforced"]),
        "elapsed_monotonic_seconds": float(run_meta["elapsed_monotonic_seconds"]),
        "end_monotonic_seconds": float(run_meta["end_monotonic_seconds"]),
        "extended_bounded_shadow_validation": bool(
            run_meta.get("extended_bounded_shadow_validation", False),
        ),
        "candidate_24h_bounded_shadow_validation": bool(
            run_meta.get("candidate_24h_bounded_shadow_validation", False),
        ),
        "evidence_root_absolute": str(evidence_abs),
        "exchange_used": False,
        "execution_approved": False,
        "executor": "peak_trade/scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py",
        "futures_perpetual_planning_scope_only": True,
        "git_sha_prefix": repo_sha,
        "live_started": False,
        "markdown_artifact_filename": BOUNDED_SHADOW_DRY_RUN_MARKDOWN_V0,
        "max_steps_budget": int(run_meta["max_steps"]),
        "max_steps_cap_enforced": int(run_meta["max_steps_cap_enforced"]),
        "network_used": False,
        "order_submission_used": False,
        "prestart_claims_summary": (
            "Local bounded Shadow **dry-run** simulation only — no scheduler, daemon, runtime "
            "session, network, broker, exchange, orders, credentials, testnet, or live."
        ),
        "readonly_local_config_skeleton_validation": dict(readonly_cfg_block),
        "ready_to_start_futures_shadow_247_daemon": False,
        "run_started": True,
        "runtime_started": False,
        "scheduler_started": False,
        "shadow_mode": True,
        "shadow_started": True,
        "start_monotonic_seconds": float(run_meta["start_monotonic_seconds"]),
        "step_interval_seconds": float(run_meta["step_interval_seconds"]),
        "steps_emitted": int(run_meta["steps_emitted"]),
        "steps_jsonl_filename": BOUNDED_SHADOW_STEPS_JSONL_V0,
        "testnet_started": False,
        "utc_completed": utc_ended.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "utc_started": utc_started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verbatim_machine_summary": _BOUNDED_SHADOW_MACHINE_LINES.rstrip("\n"),
        "wrapper_requires_future_gate_before_execution": True,
    }
    if recorded_meta is not None:
        manifest.update(dict(recorded_meta))
    return manifest


def _execute_bounded_shadow_dry_run(
    evidence_root_abs: Path,
    repo_root: Path,
    err: TextIO,
    readonly_cfg_block: Mapping[str, Any],
    duration_minutes: int,
    max_steps: int,
    step_interval_seconds: float,
    recorded_public_rest_source: Path | None = None,
    *,
    duration_cap_minutes: int = BOUNDED_SHADOW_DURATION_CAP_MINUTES,
    max_steps_cap: int = BOUNDED_SHADOW_MAX_STEPS_CAP,
    extended_bounded_shadow_validation: bool = False,
    candidate_24h_bounded_shadow_validation: bool = False,
) -> int:
    recorded_meta: dict[str, Any] | None = None
    if recorded_public_rest_source is not None:
        recorded_meta = _inventory_recorded_public_rest_source(recorded_public_rest_source)

    utc_started = datetime.now(timezone.utc)
    start_monotonic_seconds = time.monotonic()
    deadline = start_monotonic_seconds + float(duration_minutes) * 60.0
    steps_emitted = 0
    lines: list[str] = []

    while steps_emitted < max_steps and time.monotonic() < deadline:
        step_ts = datetime.now(timezone.utc)
        if steps_emitted == 0 and recorded_meta is not None:
            payload = {
                "kind": BOUNDED_SHADOW_RECORDED_PUBLIC_REST_REPLAY_HEARTBEAT_KIND,
                "recorded_public_rest_source_files_digest_sha256": recorded_meta[
                    "recorded_public_rest_source_files_digest_sha256"
                ],
                "recorded_public_rest_source_manifest_count": recorded_meta[
                    "recorded_public_rest_source_manifest_count"
                ],
                "recorded_public_rest_source_path": recorded_meta[
                    "recorded_public_rest_source_path"
                ],
                "step_index": steps_emitted + 1,
                "utc": step_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        else:
            payload = {
                "step_index": steps_emitted + 1,
                "utc": step_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "kind": "bounded_shadow_dry_run_simulated_heartbeat",
            }
        lines.append(json.dumps(payload, sort_keys=True) + "\n")
        steps_emitted += 1
        if steps_emitted >= max_steps or time.monotonic() >= deadline:
            break
        if step_interval_seconds > 0.0:
            remaining_deadline = deadline - time.monotonic()
            if remaining_deadline > 0.0:
                time.sleep(min(step_interval_seconds, remaining_deadline))

    end_monotonic_seconds = time.monotonic()
    utc_ended = datetime.now(timezone.utc)
    elapsed_monotonic_seconds = round(end_monotonic_seconds - start_monotonic_seconds, 6)
    run_meta: dict[str, Any] = {
        "duration_minutes": duration_minutes,
        "duration_minutes_cap_enforced": int(duration_cap_minutes),
        "elapsed_monotonic_seconds": elapsed_monotonic_seconds,
        "end_monotonic_seconds": end_monotonic_seconds,
        "extended_bounded_shadow_validation": extended_bounded_shadow_validation,
        "candidate_24h_bounded_shadow_validation": candidate_24h_bounded_shadow_validation,
        "max_steps": max_steps,
        "max_steps_cap_enforced": int(max_steps_cap),
        "start_monotonic_seconds": start_monotonic_seconds,
        "step_interval_seconds": step_interval_seconds,
        "steps_emitted": steps_emitted,
        "utc_end": utc_ended.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    repo_sha = _read_git_sha_prefix(repo_root)
    manifest = _bounded_shadow_manifest(
        evidence_root_abs,
        repo_sha,
        utc_started,
        utc_ended,
        readonly_cfg_block,
        run_meta,
        recorded_meta,
    )
    manifest_bytes = _canonical_json_bytes(manifest)
    digest_hex = hashlib.sha256(manifest_bytes).hexdigest()
    md_text = _bounded_shadow_markdown(
        utc_started,
        evidence_root_abs,
        repo_sha,
        readonly_cfg_block,
        run_meta,
        recorded_meta,
    )

    evidence_root_abs.mkdir(parents=True, exist_ok=True)
    (evidence_root_abs / BOUNDED_SHADOW_DRY_RUN_MARKDOWN_V0).write_text(md_text, encoding="utf-8")
    (evidence_root_abs / PRESTART_MANIFEST_JSON_V0).write_bytes(manifest_bytes)
    (evidence_root_abs / PRESTART_MANIFEST_SHA256_V0).write_text(
        digest_hex + "\n", encoding="utf-8"
    )
    (evidence_root_abs / BOUNDED_SHADOW_STEPS_JSONL_V0).write_text("".join(lines), encoding="utf-8")

    err.write(_BOUNDED_SHADOW_MACHINE_LINES)
    err.write("READONLY_OPS_OR_JOBS_CONFIG_VALIDATED=true\n")
    err.write("READONLY_CONFIG_VALIDATION_OK=true\n")
    err.write(f"STEP_INTERVAL_SECONDS={step_interval_seconds}\n")
    err.write(f"BOUNDED_SHADOW_DRY_RUN_STEPS_EMITTED={steps_emitted}\n")
    if recorded_meta is not None:
        err.write("RECORDED_PUBLIC_REST_REPLAY_SOURCE_ATTACHED=true\n")
    if candidate_24h_bounded_shadow_validation:
        err.write("CANDIDATE_24H_BOUNDED_SHADOW_VALIDATION_TIER=true\n")
    elif extended_bounded_shadow_validation:
        err.write("EXTENDED_BOUNDED_SHADOW_VALIDATION_TIER=true\n")
    err.write("BOUNDED_SHADOW_DRY_RUN_WRITTEN=true\n")
    err.write(f"EXIT_CODE={EXIT_DRYCHECK_SUCCESS}\n")
    return EXIT_DRYCHECK_SUCCESS


def _emit_banner(out: TextIO) -> None:
    out.write(
        "peak_trade shadow_247_futures_start_wrapper_skeleton_v0: "
        "FAIL-CLOSED SKELETON — no scheduler, daemon, runtime, broker, exchange, orders, "
        "or network in this artifact.\n"
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    out = sys.stdout
    err = sys.stderr

    mode_flags_active = sum(
        1
        for flag in (
            args.inspect,
            args.prestart_evidence_drycheck,
            args.bounded_runtime_contract_check,
            args.bounded_shadow_dry_run,
        )
        if flag
    )
    if mode_flags_active > 1:
        err.write(
            "At most one of --inspect, --prestart-evidence-drycheck, "
            "--bounded-runtime-contract-check, and --bounded-shadow-dry-run may be set.\n",
        )
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(f"EXIT_REASON=mutually_exclusive_flags\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n")
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.inspect and (args.ops_config_path.strip() or args.jobs_config_path.strip()):
        err.write("--inspect cannot be combined with --config/--jobs-config.\n")
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=mutually_exclusive_inspect_vs_config_validate\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    if (args.ops_config_path.strip() or args.jobs_config_path.strip()) and (
        not args.prestart_evidence_drycheck
        and not args.bounded_runtime_contract_check
        and not args.bounded_shadow_dry_run
    ):
        err.write(
            "`--config` / `--jobs-config` are invalid without `--prestart-evidence-drycheck`, "
            "`--bounded-runtime-contract-check`, or `--bounded-shadow-dry-run` "
            "(read-only skeleton validation emits evidence only).\n",
        )
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=config_validate_requires_evidence_mode\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.duration_minutes is not None and (
        not args.bounded_runtime_contract_check and not args.bounded_shadow_dry_run
    ):
        err.write(
            "`--duration-minutes` is only valid with `--bounded-runtime-contract-check` or "
            "`--bounded-shadow-dry-run`.\n",
        )
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=duration_requires_bounded_mode\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.max_steps is not None and not args.bounded_shadow_dry_run:
        err.write("`--max-steps` is only valid with `--bounded-shadow-dry-run`.\n")
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=max_steps_requires_bounded_shadow\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.step_interval_seconds is not None and not args.bounded_shadow_dry_run:
        err.write("`--step-interval-seconds` is only valid with `--bounded-shadow-dry-run`.\n")
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=step_interval_requires_bounded_shadow\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.recorded_public_rest_source.strip() and not args.bounded_shadow_dry_run:
        err.write(
            "`--recorded-public-rest-source` is only valid with `--bounded-shadow-dry-run`.\n",
        )
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=recorded_public_rest_source_requires_bounded_shadow\n"
            f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.extended_bounded_shadow_validation and not args.bounded_shadow_dry_run:
        err.write(
            "`--extended-bounded-shadow-validation` requires `--bounded-shadow-dry-run`.\n",
        )
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=extended_bounded_shadow_requires_bounded_shadow_mode\n"
            f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.extended_confirm_token.strip() and not args.bounded_shadow_dry_run:
        err.write("`--extended-confirm-token` is only valid with `--bounded-shadow-dry-run`.\n")
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=extended_confirm_requires_bounded_shadow_mode\n"
            f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.candidate_24h_bounded_shadow_validation and not args.bounded_shadow_dry_run:
        err.write(
            "`--candidate-24h-bounded-shadow-validation` requires `--bounded-shadow-dry-run`.\n",
        )
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=candidate_24h_bounded_shadow_requires_bounded_shadow_mode\n"
            f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.candidate_24h_confirm_token.strip() and not args.bounded_shadow_dry_run:
        err.write(
            "`--candidate-24h-confirm-token` is only valid with `--bounded-shadow-dry-run`.\n"
        )
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=candidate_24h_confirm_requires_bounded_shadow_mode\n"
            f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    repo_root = _REPO_ROOT_CALC.resolve()

    def _drycheck_from_valid_evidence(
        path_v: Path,
        bounded_extra: Mapping[str, Any] | None,
    ) -> int:
        cfg_block, ferr_list = _build_readonly_validation_block(
            repo_root,
            args.ops_config_path,
            args.jobs_config_path,
        )
        if not cfg_block["combined_validation_ok"]:
            err.write(
                "Read-only shadow futures ops/jobs TOML validation failed — evidence artefacts "
                "were not written.\n",
            )
            for msg in ferr_list:
                err.write(f"- {msg}\n")
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                "READONLY_OPS_OR_JOBS_CONFIG_VALIDATED="
                + str(cfg_block["ops_config_provided"] or cfg_block["jobs_config_provided"]).lower()
                + "\n",
            )
            err.write(
                f"EXIT_REASON=readonly_config_skeleton_validation_failed\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        return _execute_prestart_drycheck(path_v, repo_root, err, cfg_block, bounded_extra)

    if args.bounded_runtime_contract_check:
        token = args.confirm_token.strip()
        if token != FUTURE_OPERATOR_CONFIRMATION_TOKEN_V0:
            err.write(
                "bounded-runtime-contract-check requires `--confirm-token` matching the future "
                "governance literal (still non-executing).\n",
            )
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_check_token_invalid\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT
        if args.duration_minutes is None:
            err.write("`--duration-minutes` is required with `--bounded-runtime-contract-check`.\n")
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_check_duration_missing\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT
        dm = args.duration_minutes
        if dm < 1 or dm > BOUNDED_RUNTIME_CONTRACT_DURATION_CAP_MINUTES:
            err.write(
                "`--duration-minutes` must be between 1 and "
                f"{BOUNDED_RUNTIME_CONTRACT_DURATION_CAP_MINUTES} inclusive.\n",
            )
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_check_duration_out_of_range\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT
        if not args.ops_config_path.strip() or not args.jobs_config_path.strip():
            err.write(
                "`--bounded-runtime-contract-check` requires both `--config` and `--jobs-config`.\n",
            )
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_check_requires_dual_config\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        validated, ferr = _validate_evidence_root_for_drycheck(args.evidence_root, repo_root)
        if ferr or validated is None:
            assert ferr is not None
            err.write(ferr + "\n")
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=invalid_evidence_root_drycheck\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        bounded_extra: dict[str, Any] = {
            "duration_minutes": dm,
            "duration_cap": BOUNDED_RUNTIME_CONTRACT_DURATION_CAP_MINUTES,
            "contract_version": BOUNDED_RUNTIME_CONTRACT_VERSION_EMBEDDED,
        }
        return _drycheck_from_valid_evidence(validated, bounded_extra)

    if args.bounded_shadow_dry_run:
        token = args.confirm_token.strip()
        if token != FUTURE_OPERATOR_CONFIRMATION_TOKEN_V0:
            err.write(
                "bounded-shadow-dry-run requires `--confirm-token` matching the future governance literal.\n",
            )
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_shadow_token_invalid\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        cand_active = args.candidate_24h_bounded_shadow_validation
        ext_active = args.extended_bounded_shadow_validation

        if cand_active and ext_active:
            err.write(
                "`--extended-bounded-shadow-validation` cannot be combined with "
                "`--candidate-24h-bounded-shadow-validation`.\n",
            )
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_shadow_tier_mutex_violation\n"
                f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        if cand_active:
            c24_tok = args.candidate_24h_confirm_token.strip()
            if c24_tok != CANDIDATE_24H_BOUNDED_SHADOW_CONFIRM_TOKEN_V0:
                err.write(
                    "24h candidate bounded-shadow tier requires `--candidate-24h-confirm-token` matching "
                    "the 24h candidate governance literal.\n",
                )
                _emit_banner(err)
                err.write(_MACHINE_LINES_ALWAYS)
                err.write(
                    f"EXIT_REASON=bounded_shadow_candidate_24h_token_invalid\n"
                    f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
                )
                return EXIT_FAIL_CLOSED_DEFAULT
        elif args.candidate_24h_confirm_token.strip():
            err.write(
                "`--candidate-24h-confirm-token` requires `--candidate-24h-bounded-shadow-validation`.\n",
            )
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=candidate_24h_confirm_requires_candidate_flag\n"
                f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        if ext_active:
            ext_tok = args.extended_confirm_token.strip()
            if ext_tok != EXTENDED_BOUNDED_SHADOW_CONFIRM_TOKEN_V0:
                err.write(
                    "extended bounded-shadow tier requires `--extended-confirm-token` matching "
                    "the extended governance literal.\n",
                )
                _emit_banner(err)
                err.write(_MACHINE_LINES_ALWAYS)
                err.write(
                    f"EXIT_REASON=bounded_shadow_extended_token_invalid\n"
                    f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
                )
                return EXIT_FAIL_CLOSED_DEFAULT
        elif args.extended_confirm_token.strip():
            err.write(
                "`--extended-confirm-token` requires `--extended-bounded-shadow-validation`.\n",
            )
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=extended_confirm_requires_extended_flag\n"
                f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        if args.duration_minutes is None:
            err.write("`--duration-minutes` is required with `--bounded-shadow-dry-run`.\n")
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_shadow_duration_missing\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT
        dm = args.duration_minutes
        if cand_active:
            duration_cap = BOUNDED_SHADOW_24H_CANDIDATE_DURATION_CAP_MINUTES
            max_steps_cap = BOUNDED_SHADOW_24H_CANDIDATE_MAX_STEPS_CAP
        elif ext_active:
            duration_cap = BOUNDED_SHADOW_EXTENDED_DURATION_CAP_MINUTES
            max_steps_cap = BOUNDED_SHADOW_EXTENDED_MAX_STEPS_CAP
        else:
            duration_cap = BOUNDED_SHADOW_DURATION_CAP_MINUTES
            max_steps_cap = BOUNDED_SHADOW_MAX_STEPS_CAP
        if dm < 1 or dm > duration_cap:
            err.write(
                "with `--bounded-shadow-dry-run`, `--duration-minutes` must be between 1 and "
                f"{duration_cap} inclusive for the active tier.\n",
            )
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_shadow_duration_out_of_range\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT
        if args.max_steps is not None:
            ms = args.max_steps
            if ms < 1 or ms > max_steps_cap:
                err.write(
                    f"`--max-steps` must be between 1 and {max_steps_cap} inclusive.\n",
                )
                _emit_banner(err)
                err.write(_MACHINE_LINES_ALWAYS)
                err.write(
                    f"EXIT_REASON=bounded_shadow_max_steps_out_of_range\n"
                    f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
                )
                return EXIT_FAIL_CLOSED_DEFAULT
        else:
            ms = min(12 * dm, max_steps_cap)

        if not args.ops_config_path.strip() or not args.jobs_config_path.strip():
            err.write(
                "`--bounded-shadow-dry-run` requires both `--config` and `--jobs-config`.\n",
            )
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_shadow_requires_dual_config\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        validated, ferr = _validate_evidence_root_for_bounded_shadow(args.evidence_root, repo_root)
        if ferr or validated is None:
            assert ferr is not None
            err.write(ferr + "\n")
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=invalid_evidence_root_bounded_shadow\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        cfg_block, ferr_list = _build_readonly_validation_block(
            repo_root,
            args.ops_config_path,
            args.jobs_config_path,
        )
        if not cfg_block["combined_validation_ok"]:
            err.write(
                "Read-only shadow futures ops/jobs TOML validation failed — bounded-shadow evidence "
                "was not written.\n",
            )
            for msg in ferr_list:
                err.write(f"- {msg}\n")
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                "READONLY_OPS_OR_JOBS_CONFIG_VALIDATED="
                + str(cfg_block["ops_config_provided"] or cfg_block["jobs_config_provided"]).lower()
                + "\n",
            )
            err.write(
                f"EXIT_REASON=readonly_config_skeleton_validation_failed\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        recorded_resolved: Path | None = None
        if args.recorded_public_rest_source.strip():
            rec_val, rec_err = _validate_recorded_public_rest_source(
                args.recorded_public_rest_source, repo_root
            )
            if rec_err or rec_val is None:
                assert rec_err is not None
                err.write(rec_err + "\n")
                _emit_banner(err)
                err.write(_MACHINE_LINES_ALWAYS)
                err.write(
                    f"EXIT_REASON=invalid_recorded_public_rest_source\n"
                    f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
                )
                return EXIT_FAIL_CLOSED_DEFAULT
            recorded_resolved = rec_val

        step_iv = 0.0 if args.step_interval_seconds is None else float(args.step_interval_seconds)
        if not math.isfinite(step_iv):
            err.write("`--step-interval-seconds` must be a finite number.\n")
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_shadow_step_interval_non_finite\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT
        if step_iv < 0.0 or step_iv > BOUNDED_SHADOW_STEP_INTERVAL_MAX_SECONDS:
            err.write(
                "`--step-interval-seconds` must be between 0 and "
                f"{BOUNDED_SHADOW_STEP_INTERVAL_MAX_SECONDS:g} inclusive.\n",
            )
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=bounded_shadow_step_interval_out_of_range\n"
                f"EXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        return _execute_bounded_shadow_dry_run(
            validated,
            repo_root,
            err,
            cfg_block,
            dm,
            int(ms),
            step_iv,
            recorded_resolved,
            duration_cap_minutes=duration_cap,
            max_steps_cap=max_steps_cap,
            extended_bounded_shadow_validation=ext_active,
            candidate_24h_bounded_shadow_validation=cand_active,
        )

    if args.prestart_evidence_drycheck:
        validated, ferr = _validate_evidence_root_for_drycheck(args.evidence_root, repo_root)
        if ferr or validated is None:
            assert ferr is not None
            err.write(ferr + "\n")
            _emit_banner(err)
            err.write(_MACHINE_LINES_ALWAYS)
            err.write(
                f"EXIT_REASON=invalid_evidence_root_drycheck\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
            )
            return EXIT_FAIL_CLOSED_DEFAULT

        return _drycheck_from_valid_evidence(validated, None)

    ev_err = _validate_evidence_root(args.evidence_root)
    if ev_err:
        err.write(ev_err + "\n")
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(f"EXIT_REASON=invalid_evidence_root\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n")
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.inspect:
        _emit_banner(out)
        out.write("\nBoundary markers:\n")
        boundary_rows = (
            ("BOUNDARY_ABORT_LATER", BOUNDARY_ABORT_LATER),
            ("BOUNDARY_EVIDENCE_ROOT_TMP", BOUNDARY_EVIDENCE_ROOT_TMP),
            ("BOUNDARY_FUTURES_PERP_SCOPE", BOUNDARY_FUTURES_PERP_SCOPE),
            ("BOUNDARY_NO_BROKER", BOUNDARY_NO_BROKER),
            ("BOUNDARY_NO_LIVE", BOUNDARY_NO_LIVE),
            ("BOUNDARY_NO_NETWORK", BOUNDARY_NO_NETWORK),
            ("BOUNDARY_NO_ORDER_SUBMISSION", BOUNDARY_NO_ORDER_SUBMISSION),
            ("BOUNDARY_NO_PRIVATE_EXCHANGE", BOUNDARY_NO_PRIVATE_EXCHANGE),
            ("BOUNDARY_NO_TESTNET_UNLESS_APPROVED", BOUNDARY_NO_TESTNET_UNLESS_APPROVED),
            ("BOUNDARY_SUPERVISOR_LATER", BOUNDARY_SUPERVISOR_LATER),
        )
        for label, marker in boundary_rows:
            out.write(f"  {label}={marker}\n")
        out.write("\nMachine summary:\n")
        out.write(_MACHINE_LINES_ALWAYS)
        out.write(
            f"EXIT_REASON=inspect_mode_fail_closed_skeleton\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    token = args.confirm_token.strip()

    _emit_banner(err)
    if not token:
        err.write(
            "No --confirm-token provided. This skeleton does not execute any start path "
            "(default-off).\n"
        )
    elif token != FUTURE_OPERATOR_CONFIRMATION_TOKEN_V0:
        err.write(
            "confirm-token mismatch: future governance gate not satisfied for any implementation "
            "beyond skeleton (still fail-closed for this artifact).\n"
        )
    else:
        err.write(
            "Future confirmation token accepted for bookkeeping only — this PR skeleton still "
            "does not schedule, supervise, network, broker, exchange, submit orders, "
            "or mutate trading state.\n"
        )

    if args.evidence_root:
        err.write(f"Validated evidence-root convention hint: '{args.evidence_root.strip()}'\n")

    err.write(_MACHINE_LINES_ALWAYS)
    err.write(
        f"EXIT_REASON=default_fail_closed_skeleton_v0\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
    )
    return EXIT_FAIL_CLOSED_DEFAULT


if __name__ == "__main__":
    raise SystemExit(main())
