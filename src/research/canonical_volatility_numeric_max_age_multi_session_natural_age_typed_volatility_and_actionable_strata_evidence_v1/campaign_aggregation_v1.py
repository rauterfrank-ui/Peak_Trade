"""Append-only multi-session campaign aggregation (session evidence immutable)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.constants_v1 import (
    CAMPAIGN_AGGREGATION_FILENAME,
    SCHEMA_CAMPAIGN_AGGREGATION,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.models_v1 import (
    MultiSessionTypedVolEvidenceError,
    sha256_hex_canonical,
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _age_bucket_counts_v1(ages: Sequence[float]) -> dict[str, int]:
    buckets = {
        "0-60": 0,
        "61-120": 0,
        "121-300": 0,
        "301-900": 0,
        "901-1800": 0,
        "1801-3600": 0,
        "3601-7200": 0,
        "7201-plus": 0,
    }
    for age in ages:
        a = float(age)
        if a <= 60:
            buckets["0-60"] += 1
        elif a <= 120:
            buckets["61-120"] += 1
        elif a <= 300:
            buckets["121-300"] += 1
        elif a <= 900:
            buckets["301-900"] += 1
        elif a <= 1800:
            buckets["901-1800"] += 1
        elif a <= 3600:
            buckets["1801-3600"] += 1
        elif a <= 7200:
            buckets["3601-7200"] += 1
        else:
            buckets["7201-plus"] += 1
    return buckets


def aggregate_session_dir_v1(session_dir: Path) -> dict[str, Any]:
    """Derive aggregation fields from an immutable session directory."""
    root = Path(session_dir)
    if not root.is_dir():
        raise MultiSessionTypedVolEvidenceError(f"session_dir_missing:{root}")
    terminal_path = root / "terminal_verdict.json"
    terminal = (
        json.loads(terminal_path.read_text(encoding="utf-8")) if terminal_path.is_file() else {}
    )
    samples = _load_jsonl(root / "market_samples.jsonl")
    vols = _load_jsonl(root / "volatility_records.jsonl")
    typed = _load_jsonl(root / "typed_volatility_comparisons.jsonl")
    cfs = _load_jsonl(root / "full_alpha_counterfactuals.jsonl")
    strata = _load_jsonl(root / "opportunity_strata.jsonl")

    ages: list[float] = []
    for rec in typed or vols:
        if "age_seconds" in rec:
            ages.append(float(rec["age_seconds"]))
        elif "old_volatility_age_seconds" in rec:
            ages.append(float(rec["old_volatility_age_seconds"]))
        elif "VOLATILITY_AGE_SECONDS" in rec:
            ages.append(float(rec["VOLATILITY_AGE_SECONDS"]))

    regimes = sorted(
        {
            str(r.get("regime_label") or r.get("market_regime_state") or "")
            for r in (strata or samples)
            if str(r.get("regime_label") or r.get("market_regime_state") or "").strip()
        }
    )
    return {
        "session_id": str(terminal.get("session_id") or root.name),
        "terminal_status": str(terminal.get("status") or "UNKNOWN"),
        "sample_count": len(samples),
        "ages": ages,
        "typed_vol_comparison_count": len(typed),
        "comparable_counterfactual_count": sum(
            1
            for c in cfs
            if c.get("classification") not in {"NOT_COMPARABLE", "FRESH_ESTIMATE_UNAVAILABLE", None}
        ),
        "age_only_decision_change_count": sum(
            1
            for c in cfs
            if c.get("AGE_ONLY_CAUSALITY_SUPPORTED") and c.get("FINAL_OUTCOME_CHANGED")
        ),
        "long_opportunity_count": sum(
            1 for s in strata if str(s.get("OPPORTUNITY_STRATUM", "")).startswith("LONG_")
        ),
        "short_opportunity_count": sum(
            1 for s in strata if str(s.get("OPPORTUNITY_STRATUM", "")).startswith("SHORT_")
        ),
        "long_entry_eligible_count": sum(
            1 for s in strata if s.get("OPPORTUNITY_STRATUM") == "LONG_ENTRY_ELIGIBLE"
        ),
        "short_entry_eligible_count": sum(
            1 for s in strata if s.get("OPPORTUNITY_STRATUM") == "SHORT_ENTRY_ELIGIBLE"
        ),
        "regime_labels": regimes,
        "session_dir": str(root),
    }


def build_campaign_aggregation_v1(
    *,
    campaign_id: str,
    session_dirs: Sequence[Path],
    coverage_plan_requirements_met: bool = False,
) -> dict[str, Any]:
    sessions = [aggregate_session_dir_v1(Path(p)) for p in session_dirs]
    all_ages: list[float] = []
    for s in sessions:
        all_ages.extend(list(s["ages"]))
    buckets = _age_bucket_counts_v1(all_ages)
    session_ids = [str(s["session_id"]) for s in sessions]
    regimes = sorted({r for s in sessions for r in s["regime_labels"]})
    payload = {
        "schema": SCHEMA_CAMPAIGN_AGGREGATION,
        "schema_version": "v1",
        "CAMPAIGN_ID": campaign_id,
        "SESSION_IDS": session_ids,
        "PRODUCTIVE_SESSION_COUNT": len(sessions),
        "TERMINAL_PASS_SESSION_COUNT": sum(1 for s in sessions if s["terminal_status"] == "PASS"),
        "FAILED_SESSION_COUNT": sum(1 for s in sessions if s["terminal_status"] != "PASS"),
        "TOTAL_SAMPLE_COUNT": sum(int(s["sample_count"]) for s in sessions),
        "AGE_BUCKET_COUNTS": buckets,
        "LOW_AGE_0_60_COUNT": buckets["0-60"],
        "LOW_AGE_61_120_COUNT": buckets["61-120"],
        "LOW_AGE_121_300_COUNT": buckets["121-300"],
        "HIGH_AGE_3600_PLUS_COUNT": buckets["3601-7200"] + buckets["7201-plus"],
        "HIGH_AGE_7200_PLUS_COUNT": buckets["7201-plus"],
        "TYPED_VOL_COMPARISON_COUNT": sum(int(s["typed_vol_comparison_count"]) for s in sessions),
        "COMPARABLE_COUNTERFACTUAL_COUNT": sum(
            int(s["comparable_counterfactual_count"]) for s in sessions
        ),
        "AGE_ONLY_DECISION_CHANGE_COUNT": sum(
            int(s["age_only_decision_change_count"]) for s in sessions
        ),
        "LONG_OPPORTUNITY_COUNT": sum(int(s["long_opportunity_count"]) for s in sessions),
        "SHORT_OPPORTUNITY_COUNT": sum(int(s["short_opportunity_count"]) for s in sessions),
        "LONG_ENTRY_ELIGIBLE_COUNT": sum(int(s["long_entry_eligible_count"]) for s in sessions),
        "SHORT_ENTRY_ELIGIBLE_COUNT": sum(int(s["short_entry_eligible_count"]) for s in sessions),
        "DISTINCT_MARKET_REGIME_LABELS": regimes,
        "CROSS_SESSION_REPLICATION_AVAILABLE": len(sessions) >= 2,
        "COVERAGE_PLAN_REQUIREMENTS_MET": bool(coverage_plan_requirements_met),
        "SESSION_EVIDENCE_IMMUTABLE": True,
        "sessions": [{k: v for k, v in s.items() if k != "ages"} for s in sessions],
    }
    payload["aggregation_digest"] = sha256_hex_canonical(
        {k: v for k, v in payload.items() if k not in {"aggregation_digest", "sessions"}}
    )
    return payload


def write_campaign_aggregation_v1(*, campaign_dir: Path, aggregation: Mapping[str, Any]) -> Path:
    """Write aggregation beside sessions; never rewrite session artifacts."""
    out = Path(campaign_dir) / CAMPAIGN_AGGREGATION_FILENAME
    out.parent.mkdir(parents=True, exist_ok=True)
    # Refuse writing into a session directory.
    if out.parent.name == "S03" or (out.parent / "terminal_verdict.json").exists():
        raise MultiSessionTypedVolEvidenceError("refuse_write_inside_session_dir")
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(dict(aggregation), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(out)
    return out
