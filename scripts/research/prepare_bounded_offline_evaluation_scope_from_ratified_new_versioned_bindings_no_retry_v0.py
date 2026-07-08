#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

STEP = "prepare_bounded_offline_evaluation_scope_from_ratified_new_versioned_bindings_no_retry_v0"
VERDICT_PREFIX = (
    "PREPARE_BOUNDED_OFFLINE_EVALUATION_SCOPE_FROM_RATIFIED_NEW_VERSIONED_BINDINGS_NO_RETRY_V0"
)
EXPECTED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_value(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _bool_env(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def _load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _walk_dicts(value: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(value, dict):
        out.append(value)
        for child in value.values():
            out.extend(_walk_dicts(child))
    elif isinstance(value, list):
        for child in value:
            out.extend(_walk_dicts(child))
    return out


def _candidate_name(item: dict[str, Any]) -> str | None:
    for key in ("candidate", "candidate_id", "strategy_id", "strategy", "name", "id"):
        value = item.get(key)
        if isinstance(value, str) and value in EXPECTED_CANDIDATES:
            return value
    return None


def _is_ratified(item: dict[str, Any]) -> bool:
    for key in ("ratified", "is_ratified", "binding_ratified"):
        if item.get(key) is True:
            return True
    status = item.get("status")
    if isinstance(status, str) and "ratified" in status.lower():
        return True
    return False


def _extract_ratified_candidates(source_evidence: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(source_evidence.rglob("*.json")):
        data = _load_json(path)
        if data is None:
            continue
        for item in _walk_dicts(data):
            name = _candidate_name(item)
            if name is None or not _is_ratified(item):
                continue
            digest = item.get("non_retry_provenance_digest")
            if not isinstance(digest, str) or not digest:
                digest = _sha256_file(path)
            found[name] = {
                "candidate": name,
                "ratified": True,
                "non_retry_provenance_digest": digest,
                "source_file": str(path),
            }
    return found


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> int:
    source_evidence = Path(os.environ.get("PEAK_TRADE_SOURCE_EVIDENCE", "")).expanduser()
    evidence_dir = Path(os.environ.get("PEAK_TRADE_EVIDENCE_DIR", "")).expanduser()

    if not source_evidence:
        print(f"VERDICT={VERDICT_PREFIX}_BLOCKED_SOURCE_EVIDENCE_ENV_MISSING")
        return 2
    if not evidence_dir:
        print(f"VERDICT={VERDICT_PREFIX}_BLOCKED_EVIDENCE_DIR_ENV_MISSING")
        return 2

    evidence_dir.mkdir(parents=True, exist_ok=True)

    blocked_reasons: list[str] = []

    if not source_evidence.exists():
        blocked_reasons.append("SOURCE_EVIDENCE_MISSING")
    if _bool_env("PEAK_TRADE_LIVE_AUTHORIZED"):
        blocked_reasons.append("LIVE_AUTHORIZED_TRUE")
    if _bool_env("PEAK_TRADE_ORDERS_ALLOWED"):
        blocked_reasons.append("ORDERS_ALLOWED_TRUE")
    if _bool_env("PEAK_TRADE_SCHEDULER_RUNTIME_ALLOWED"):
        blocked_reasons.append("SCHEDULER_RUNTIME_ALLOWED_TRUE")
    if _bool_env("PEAK_TRADE_EVALUATION_EXECUTED"):
        blocked_reasons.append("EVALUATION_EXECUTED_TRUE")
    if _bool_env("PEAK_TRADE_UNMODIFIED_BINDING_RETRY_ALLOWED"):
        blocked_reasons.append("UNMODIFIED_BINDING_RETRY_ALLOWED_TRUE")

    candidates: dict[str, dict[str, Any]] = {}
    if not blocked_reasons:
        candidates = _extract_ratified_candidates(source_evidence)
        missing = [name for name in EXPECTED_CANDIDATES if name not in candidates]
        if missing:
            blocked_reasons.append("RATIFIED_CANDIDATES_NOT_RESOLVED:" + ",".join(missing))

    head = _git_value(["rev-parse", "HEAD"])
    origin_main = _git_value(["rev-parse", "origin/main"])

    scope = {
        "step": STEP,
        "verdict": f"{VERDICT_PREFIX}_{'BLOCKED_' + '_'.join(blocked_reasons) if blocked_reasons else 'PASS'}",
        "head": head,
        "origin_main": origin_main,
        "head_equals_origin_main": head == origin_main,
        "source_evidence": str(source_evidence),
        "candidate_count": len(candidates),
        "candidates": [candidates[name] for name in EXPECTED_CANDIDATES if name in candidates],
        "scope_status": "PREPARED_FOR_SEPARATE_BOUNDED_OFFLINE_EVALUATION"
        if not blocked_reasons
        else "BLOCKED",
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "unmodified_binding_retry_allowed": False,
        "runtime_rewire_authorized": False,
        "shadow_authorized": False,
        "paper_authorized": False,
        "testnet_authorized": False,
        "scheduler_runtime_allowed": False,
        "orders_allowed": False,
        "live_authorized": False,
        "core_system_mutation_allowed": False,
        "canonical_trading_logic_mutation_allowed": False,
        "master_v2_mutation_allowed": False,
        "double_play_mutation_allowed": False,
        "risk_sizing_mutation_allowed": False,
        "safety_runtime_mutation_allowed": False,
        "no_runtime_authority": True,
        "no_order_authority": True,
        "no_live_authority": True,
        "blocked_reasons": blocked_reasons,
    }

    scope_path = (
        evidence_dir
        / "prepared_bounded_offline_evaluation_scope_from_ratified_new_versioned_bindings_no_retry_v0.json"
    )
    _write_text(scope_path, json.dumps(scope, indent=2, sort_keys=True) + "\n")

    final_report = [
        f"VERDICT={scope['verdict']}",
        f"STEP={STEP}",
        f"HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"HEAD_EQUALS_ORIGIN_MAIN={str(head == origin_main).lower()}",
        f"SOURCE_EVIDENCE={source_evidence}",
        f"CANDIDATE_COUNT={len(candidates)}",
        "FINAL_RESEARCH_FLEET=trend_following,bollinger_bands,momentum_1h",
        "SCOPE_STATUS=" + str(scope["scope_status"]),
        "EVALUATION_EXECUTED=false",
        "UNMODIFIED_BINDING_RETRY_ALLOWED=false",
        "RUNTIME_REWIRE_AUTHORIZED=false",
        "ORDERS_ALLOWED=false",
        "LIVE_AUTHORIZED=false",
        "NO_RUNTIME_AUTHORITY=true",
        "NO_ORDER_AUTHORITY=true",
        "NO_LIVE_AUTHORITY=true",
        f"DURABLE_SCOPE_FILE={scope_path}",
    ]
    if blocked_reasons:
        final_report.append("BLOCKED_REASONS=" + ",".join(blocked_reasons))

    _write_text(evidence_dir / "runner_final_report.txt", "\n".join(final_report) + "\n")
    print("\n".join(final_report))
    return 1 if blocked_reasons else 0


if __name__ == "__main__":
    sys.exit(main())
