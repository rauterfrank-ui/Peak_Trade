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
import sys
import tomllib
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
        "--confirm-token",
        metavar="TOKEN",
        default="",
        help=(
            "Optional future governance token placeholder. Skeleton still exits "
            f"{EXIT_FAIL_CLOSED_DEFAULT} unless prestart-evidence-drycheck succeeds."
        ),
    )
    parser.add_argument(
        "--evidence-root",
        metavar="PATH",
        default="",
        help=(
            "Optional `/tmp/peak_trade_*`-style absolute path (convention-only), or required "
            "with `--prestart-evidence-drycheck`."
        ),
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default="",
        dest="ops_config_path",
        help=(
            "**With `--prestart-evidence-drycheck` only.** Read-only validate default-off Ops "
            "skeleton (`shadow_247_futures_wrapper_skeleton`) invariants via stdlib tomllib "
            "(path must lie under repo root)."
        ),
    )
    parser.add_argument(
        "--jobs-config",
        metavar="PATH",
        default="",
        dest="jobs_config_path",
        help=(
            "**With `--prestart-evidence-drycheck` only.** Read-only validate the disabled "
            "scheduler placeholder row (stdlib tomllib)."
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


def _read_git_sha_prefix(repo_root: Path, maxlen: int = 12) -> str:
    head_file = repo_root / ".git" / "HEAD"
    if not head_file.is_file():
        return "UNKNOWN"
    raw = head_file.read_text(encoding="utf-8", errors="replace").strip()
    if raw.startswith("ref: "):
        ref = raw[5:].strip()
        ref_path = repo_root / ".git" / ref
        if ref_path.is_file():
            sha = ref_path.read_text(encoding="utf-8", errors="replace").strip()
            return sha[:maxlen] if sha else "UNKNOWN_REF_EMPTY"
        return "UNKNOWN_REF_MISSING"
    # Detached HEAD or direct SHA digest string.
    cand40 = raw[:40].lower()
    if len(cand40) == 40 and all(ch in "0123456789abcdef" for ch in cand40):
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


def _canonical_json_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _drycheck_manifest(
    evidence_abs: Path,
    repo_sha: str,
    utc_now: datetime,
    readonly_cfg_block: Mapping[str, Any],
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
    return manifest


def _drycheck_markdown(
    utc_now: datetime,
    evidence_abs: Path,
    repo_sha: str,
    readonly_cfg_block: Mapping[str, Any],
) -> str:
    lines = (
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
    )
    return "".join(lines)


def _execute_prestart_drycheck(
    evidence_root_abs: Path,
    repo_root: Path,
    err: TextIO,
    readonly_cfg_block: Mapping[str, Any],
) -> int:
    utc_now = datetime.now(timezone.utc)
    repo_sha = _read_git_sha_prefix(repo_root)
    manifest = _drycheck_manifest(evidence_root_abs, repo_sha, utc_now, readonly_cfg_block)

    manifest_bytes = _canonical_json_bytes(manifest)
    digest_hex = hashlib.sha256(manifest_bytes).hexdigest()

    md_text = _drycheck_markdown(utc_now, evidence_root_abs, repo_sha, readonly_cfg_block)

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

    err.write(
        "PRESTART_EVIDENCE_DRYCHECK_WRITTEN=true\nEXIT_CODE={}\n".format(EXIT_DRYCHECK_SUCCESS)
    )
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

    if args.inspect and args.prestart_evidence_drycheck:
        err.write("--inspect combined with --prestart-evidence-drycheck is not allowed.\n")
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
    ):
        err.write(
            "`--config` / `--jobs-config` are invalid without `--prestart-evidence-drycheck` "
            "(read-only skeleton validation emits evidence only).\n",
        )
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(
            f"EXIT_REASON=config_validate_requires_drycheck\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n",
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    repo_root = _REPO_ROOT_CALC.resolve()

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

        path_v = validated

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

        return _execute_prestart_drycheck(path_v, repo_root, err, cfg_block)

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
