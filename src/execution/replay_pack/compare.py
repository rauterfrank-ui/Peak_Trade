from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple

from src.execution.beta_bridge.schema import normalize_beta_exec_v1_event, sort_key_beta_exec_v1

from .canonical import write_json_canonical
from .contract import (
    ContractViolationError,
    HashMismatchError,
    ReplayMismatchError,
    SchemaValidationError,
)
from .datarefs import (
    DataRefHashMismatchError,
    MissingRequiredDataRefError,
    ResolutionMode,
    embed_resolution_report_into_bundle,
    enforce_resolution_mode,
    parse_market_data_refs_document,
    resolve_market_data_refs,
)
from .hashing import collect_files_for_hashing, write_sha256sums
from .loader import ReplayBundle, load_replay_pack
from .runner import _replay_events  # reuse identical replay semantics
from .validator import validate_replay_pack


COMPARE_REPORT_SCHEMA_VERSION: Literal["REPLAY_COMPARE_REPORT_V1"] = "REPLAY_COMPARE_REPORT_V1"
COMPARE_VERSION: Literal["1"] = "1"

CompareStatus = Literal["PASS", "FAIL"]
CheckMode = Literal["enabled", "disabled"]
InvariantStatus = Literal["PASS", "FAIL", "SKIP"]

DataRefsSourceStatus = Literal["PRESENT", "ABSENT"]


EXIT_OK = 0
EXIT_CONTRACT = 2
EXIT_HASH = 3
EXIT_REPLAY_MISMATCH = 4
EXIT_UNEXPECTED = 5
EXIT_MISSING_REQUIRED_DATAREF = 6


def _safe_str(x: Any) -> str:
    return str(x) if x is not None else ""


def _read_json_if_exists(path: Path) -> Optional[object]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _datarefs_summary_from_report_doc(doc: Mapping[str, Any]) -> Optional[Dict[str, int]]:
    summary = doc.get("summary")
    if not isinstance(summary, Mapping):
        return None
    try:
        return {
            "total": int(summary.get("total", 0)),
            "resolved": int(summary.get("resolved", 0)),
            "missing": int(summary.get("missing", 0)),
            "hash_mismatch": int(summary.get("hash_mismatch", 0)),
        }
    except Exception:
        return None


def _fills_diff(
    expected: Sequence[Mapping[str, Any]], got: Sequence[Mapping[str, Any]], *, sample_n: int
) -> Dict[str, Any]:
    """
    Deterministic diff keyed by event_id (unique, stable).
    """
    exp_by_id = {
        str(e.get("event_id") or ""): dict(e) for e in expected if e.get("event_id") is not None
    }
    got_by_id = {
        str(e.get("event_id") or ""): dict(e) for e in got if e.get("event_id") is not None
    }

    exp_ids = sorted([k for k in exp_by_id.keys() if k])
    got_ids = sorted([k for k in got_by_id.keys() if k])

    exp_set = set(exp_ids)
    got_set = set(got_ids)

    added_ids = sorted(got_set - exp_set)
    removed_ids = sorted(exp_set - got_set)
    changed_ids = sorted([i for i in sorted(exp_set & got_set) if exp_by_id[i] != got_by_id[i]])

    def _sample_event(e: Mapping[str, Any]) -> Dict[str, Any]:
        # Keep samples compact and deterministic.
        return {
            "event_id": _safe_str(e.get("event_id")),
            "event_type": _safe_str(e.get("event_type")),
            "symbol": _safe_str(e.get("symbol")),
            "ts_sim": int(e.get("ts_sim", 0)) if isinstance(e.get("ts_sim"), int) else 0,
        }

    sample: List[Dict[str, Any]] = []
    for i in added_ids[:sample_n]:
        sample.append({"kind": "ADDED", "event_id": i, "got": _sample_event(got_by_id[i])})
    for i in removed_ids[:sample_n]:
        sample.append({"kind": "REMOVED", "event_id": i, "expected": _sample_event(exp_by_id[i])})
    for i in changed_ids[:sample_n]:
        sample.append(
            {
                "kind": "CHANGED",
                "event_id": i,
                "expected": _sample_event(exp_by_id[i]),
                "got": _sample_event(got_by_id[i]),
            }
        )

    sample = sorted(sample, key=lambda x: (str(x.get("kind")), str(x.get("event_id"))))
    return {
        "added": int(len(added_ids)),
        "removed": int(len(removed_ids)),
        "changed": int(len(changed_ids)),
        "sample": sample[:sample_n],
    }


def _positions_diff(
    expected: Mapping[str, Mapping[str, Any]],
    got: Mapping[str, Mapping[str, Any]],
    *,
    sample_n: int,
) -> Dict[str, Any]:
    exp_syms = sorted(expected.keys())
    got_syms = sorted(got.keys())
    exp_set = set(exp_syms)
    got_set = set(got_syms)

    added = sorted(got_set - exp_set)
    removed = sorted(exp_set - got_set)
    changed = sorted([s for s in sorted(exp_set & got_set) if dict(expected[s]) != dict(got[s])])

    def _sample_pos(p: Mapping[str, Any]) -> Dict[str, str]:
        # Expected positions are JSON-safe strings; keep it that way.
        out: Dict[str, str] = {}
        for k in sorted(p.keys()):
            out[str(k)] = _safe_str(p.get(k))
        return out

    sample: List[Dict[str, Any]] = []
    for s in added[:sample_n]:
        sample.append({"kind": "ADDED", "symbol": s, "got": _sample_pos(got[s])})
    for s in removed[:sample_n]:
        sample.append({"kind": "REMOVED", "symbol": s, "expected": _sample_pos(expected[s])})
    for s in changed[:sample_n]:
        sample.append(
            {
                "kind": "CHANGED",
                "symbol": s,
                "expected": _sample_pos(expected[s]),
                "got": _sample_pos(got[s]),
            }
        )

    sample = sorted(sample, key=lambda x: (str(x.get("kind")), str(x.get("symbol"))))
    return {
        "added": int(len(added)),
        "removed": int(len(removed)),
        "changed": int(len(changed)),
        "sample": sample[:sample_n],
    }


def _write_compare_report_into_bundle(
    bundle_root: Path, relpath: str, report_obj: Mapping[str, Any]
) -> Path:
    out_path = bundle_root / relpath
    write_json_canonical(out_path, report_obj)
    # Update sha256sums to cover all files except itself.
    write_sha256sums(bundle_root, collect_files_for_hashing(bundle_root))
    return out_path


def generate_compare_report(
    bundle_path: str | Path,
    *,
    check_outputs: bool,
    resolve_datarefs: Optional[ResolutionMode] = None,
    cache_root: Optional[str | Path] = None,
    generated_at_utc: Optional[str] = None,
    out_path: Optional[str | Path] = None,
    sample_n: int = 5,
) -> Tuple[int, Dict[str, Any]]:
    """
    Generate deterministic compare_report.json (baseline vs replay).
    """
    bundle_root = Path(bundle_path)

    reasons: List[str] = []
    exit_code = EXIT_OK

    bundle: Optional[ReplayBundle] = None
    manifest: Dict[str, Any] = {}
    validate_status: CompareStatus = "PASS"

    try:
        validate_replay_pack(bundle_root)
        bundle = load_replay_pack(bundle_root)
        manifest = dict(bundle.manifest)
    except HashMismatchError as e:
        validate_status = "FAIL"
        reasons.append(f"HASH_MISMATCH:{type(e).__name__}")
        exit_code = EXIT_HASH
    except (SchemaValidationError, ContractViolationError) as e:
        validate_status = "FAIL"
        reasons.append(f"CONTRACT:{type(e).__name__}")
        exit_code = EXIT_CONTRACT
    except Exception as e:
        validate_status = "FAIL"
        reasons.append(f"UNEXPECTED:{type(e).__name__}")
        exit_code = EXIT_UNEXPECTED

    # Derive deterministic timestamp (no wall-clock).
    created_at = _safe_str(manifest.get("created_at_utc"))
    generated_at = _safe_str(generated_at_utc) or created_at

    datarefs_block: Optional[Dict[str, Any]] = None
    datarefs_mode: Literal["best_effort", "strict", "none"] = "none"

    if bundle is not None:
        # Prefer any existing resolution report.
        rr_rel = "meta/resolution_report.json"
        rr_path = bundle.root / rr_rel
        rr_doc = _read_json_if_exists(rr_path)
        rr_summary: Optional[Dict[str, int]] = None
        if isinstance(rr_doc, Mapping):
            rr_summary = _datarefs_summary_from_report_doc(rr_doc)

        # Optionally run resolver (offline) and embed its report for CI artifacts.
        if resolve_datarefs is not None:
            datarefs_mode = resolve_datarefs
            cache_root_s = (
                str(cache_root)
                if cache_root is not None
                else str(os.environ.get("PEAK_TRADE_DATA_CACHE_ROOT") or "")
            )
            if not cache_root_s:
                reasons.append("CONTRACT:MISSING_CACHE_ROOT")
                exit_code = EXIT_CONTRACT
            else:
                try:
                    doc = bundle.market_data_refs()
                    refs = parse_market_data_refs_document(doc) if doc is not None else []
                    rr = resolve_market_data_refs(
                        bundle.root,
                        refs,
                        cache_root_s,
                        mode=resolve_datarefs,
                        bundle_id=_safe_str(bundle.manifest.get("bundle_id")),
                        run_id=_safe_str(bundle.manifest.get("run_id")),
                        generated_at_utc=generated_at,
                        run_id_for_report=_safe_str(bundle.manifest.get("run_id")),
                    )
                    embed_resolution_report_into_bundle(
                        bundle_root=bundle.root, report=rr, relpath=rr_rel
                    )
                    rr_summary = {
                        "total": rr.summary.total,
                        "resolved": rr.summary.resolved,
                        "missing": rr.summary.missing,
                        "hash_mismatch": rr.summary.hash_mismatch,
                    }
                    enforce_resolution_mode(mode=resolve_datarefs, refs=refs, report=rr)
                except MissingRequiredDataRefError:
                    reasons.append("DATAREFS:MISSING_REQUIRED")
                    exit_code = EXIT_MISSING_REQUIRED_DATAREF
                except DataRefHashMismatchError:
                    reasons.append("DATAREFS:HASH_MISMATCH")
                    exit_code = EXIT_HASH
                except (SchemaValidationError, ContractViolationError, ValueError) as e:
                    reasons.append(f"CONTRACT:{type(e).__name__}")
                    exit_code = EXIT_CONTRACT
                except Exception as e:
                    reasons.append(f"UNEXPECTED:{type(e).__name__}")
                    exit_code = EXIT_UNEXPECTED
        else:
            datarefs_mode = "none"

        # Only include block if resolver was run OR a report exists.
        if resolve_datarefs is not None or rr_doc is not None:
            datarefs_block = {
                "mode": datarefs_mode,
                "summary": rr_summary
                or {"total": 0, "resolved": 0, "missing": 0, "hash_mismatch": 0},
                "source": {
                    "status": "PRESENT" if rr_path.exists() else "ABSENT",
                    "path": rr_rel,
                },
            }

    # Replay and invariants.
    replay_exit_code = 0
    fills_status: InvariantStatus = "SKIP"
    pos_status: InvariantStatus = "SKIP"
    fills_diff: Dict[str, Any] = {"added": 0, "removed": 0, "changed": 0, "sample": []}
    positions_diff: Dict[str, Any] = {"added": 0, "removed": 0, "changed": 0, "sample": []}

    if bundle is None:
        replay_exit_code = exit_code
    else:
        try:
            events = list(bundle.execution_events())
            if not events:
                reasons.append("CONTRACT:NO_EVENTS")
                replay_exit_code = EXIT_CONTRACT
            else:
                result = _replay_events(events)
                replay_exit_code = EXIT_OK

                if check_outputs:
                    expected_fills_iter = bundle.expected_fills()
                    expected_positions = bundle.expected_positions()

                    if expected_fills_iter is None and expected_positions is None:
                        fills_status = "SKIP"
                        pos_status = "SKIP"
                    else:
                        got_fills = sorted(
                            [normalize_beta_exec_v1_event(e) for e in result.fills],
                            key=sort_key_beta_exec_v1,
                        )
                        exp_fills = (
                            sorted(
                                [normalize_beta_exec_v1_event(e) for e in expected_fills_iter],
                                key=sort_key_beta_exec_v1,
                            )
                            if expected_fills_iter is not None
                            else []
                        )
                        got_pos = result.positions
                        exp_pos = expected_positions or {}

                        if expected_fills_iter is None:
                            fills_status = "SKIP"
                        else:
                            fills_status = "PASS" if exp_fills == got_fills else "FAIL"
                            fills_diff = _fills_diff(exp_fills, got_fills, sample_n=sample_n)

                        if expected_positions is None:
                            pos_status = "SKIP"
                        else:
                            pos_status = "PASS" if exp_pos == got_pos else "FAIL"
                            positions_diff = _positions_diff(exp_pos, got_pos, sample_n=sample_n)

                        if fills_status == "FAIL" or pos_status == "FAIL":
                            reasons.append("REPLAY_MISMATCH:EXPECTED_OUTPUTS")
                            replay_exit_code = EXIT_REPLAY_MISMATCH
                else:
                    fills_status = "SKIP"
                    pos_status = "SKIP"
        except ReplayMismatchError:
            # Defensive: should not occur because we don't call runner check path that raises.
            reasons.append("REPLAY_MISMATCH:EXPECTED_OUTPUTS")
            replay_exit_code = EXIT_REPLAY_MISMATCH
        except HashMismatchError:
            reasons.append("HASH_MISMATCH")
            replay_exit_code = EXIT_HASH
        except (SchemaValidationError, ContractViolationError) as e:
            reasons.append(f"CONTRACT:{type(e).__name__}")
            replay_exit_code = EXIT_CONTRACT
        except Exception as e:
            reasons.append(f"UNEXPECTED:{type(e).__name__}")
            replay_exit_code = EXIT_UNEXPECTED

    # Final exit code is the max-severity by explicit mapping rules.
    # Priority: unexpected(5) > missing required(6) > hash(3) > mismatch(4) > contract(2) > ok(0)
    # But we must preserve exact codes per failure path; compute deterministically.
    candidates = [exit_code, replay_exit_code]
    # If either is unexpected -> 5
    if EXIT_UNEXPECTED in candidates:
        final_code = EXIT_UNEXPECTED
    elif EXIT_MISSING_REQUIRED_DATAREF in candidates:
        final_code = EXIT_MISSING_REQUIRED_DATAREF
    elif EXIT_HASH in candidates:
        final_code = EXIT_HASH
    elif EXIT_REPLAY_MISMATCH in candidates:
        final_code = EXIT_REPLAY_MISMATCH
    elif EXIT_CONTRACT in candidates:
        final_code = EXIT_CONTRACT
    else:
        final_code = EXIT_OK

    status: CompareStatus = "PASS" if final_code == EXIT_OK else "FAIL"
    reasons = sorted(set(reasons))

    report: Dict[str, Any] = {
        "schema_version": COMPARE_REPORT_SCHEMA_VERSION,
        "meta": {
            "bundle_id": _safe_str(manifest.get("bundle_id")),
            "run_id": _safe_str(manifest.get("run_id")),
            "generated_at_utc": generated_at,
            "tool": "pt_replay_pack",
            "tool_version": _safe_str((manifest.get("producer") or {}).get("version")),
            "compare_version": COMPARE_VERSION,
        },
        "replay": {
            "validate_bundle": validate_status,
            "replay_exit_code": int(replay_exit_code),
            "check_outputs": "enabled" if check_outputs else "disabled",
            "invariants": {"fills": fills_status, "positions": pos_status},
            "diffs": {"fills_diff": fills_diff, "positions_diff": positions_diff},
        },
        "summary": {"status": status, "reasons": reasons, "exit_code": int(final_code)},
    }
    if datarefs_block is not None:
        report["datarefs"] = datarefs_block

    # Write report
    if out_path is None:
        if bundle is not None:
            _write_compare_report_into_bundle(bundle.root, "meta/compare_report.json", report)
    else:
        out_p = Path(out_path)
        if bundle is not None and not out_p.is_absolute():
            out_p = bundle.root / out_p
        if bundle is not None:
            try:
                rel = out_p.resolve().relative_to(bundle.root.resolve()).as_posix()
                _write_compare_report_into_bundle(bundle.root, rel, report)
            except Exception:
                write_json_canonical(out_p, report)
        else:
            write_json_canonical(out_p, report)

    return int(final_code), report
