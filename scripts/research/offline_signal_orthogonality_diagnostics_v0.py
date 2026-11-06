from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve()


def discover_repo_root_from_script() -> Path | None:
    for parent in [_SCRIPT_PATH, *_SCRIPT_PATH.parents]:
        if (parent / "src").is_dir() and (parent / ".git").exists():
            return parent.resolve()
    return None


def validate_peak_trade_repo_root(repo_root: Path) -> Path:
    resolved = repo_root.expanduser().resolve()
    if not resolved.is_dir():
        raise SystemExit(f"REPO_ROOT_INVALID_NOT_DIRECTORY: {resolved}")
    if not (resolved / "src").is_dir():
        raise SystemExit(f"REPO_ROOT_INVALID_MISSING_SRC: {resolved}")
    if not (resolved / ".git").exists():
        raise SystemExit(f"REPO_ROOT_INVALID_MISSING_GIT: {resolved}")
    return resolved


def resolve_repo_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return validate_peak_trade_repo_root(explicit)
    discovered = discover_repo_root_from_script()
    if discovered is None:
        raise SystemExit("REPO_ROOT_DISCOVERY_FAILED: not inside Peak_Trade repo")
    return discovered


_discovered_repo_root = discover_repo_root_from_script()
if _discovered_repo_root is not None:
    repo_s = str(_discovered_repo_root)
    if repo_s not in sys.path:
        sys.path.insert(0, repo_s)

from src.research.linear_evidence.signal_orthogonality import (  # noqa: E402
    SignalOrthogonalityConfigV1,
    analyze_signal_orthogonality,
    evidence_to_dict,
    make_deterministic_signal_fixture,
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
DEFAULT_FEATURES = "trend_following,momentum_1h,bollinger_bands,liquidity_context"


def _read_csv(path: Path, features: tuple[str, ...]) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in features if name not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"missing feature columns: {','.join(missing)}")
        return [dict(row) for row in reader]


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline signal orthogonality diagnostics v0")
    parser.add_argument("--out", required=True)
    parser.add_argument("--input-csv", type=Path, default=None)
    parser.add_argument("--features", default=DEFAULT_FEATURES)
    parser.add_argument("--correlation-threshold", type=float, default=0.85)
    parser.add_argument("--condition-number-threshold", type=float, default=1000.0)
    parser.add_argument("--min-samples", type=int, default=8)
    parser.add_argument(
        "--fixture-scaffold",
        action="store_true",
        help="Use deterministic fixture truth-pack when no productive binding is supplied.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Peak_Trade repo root; defaults to script discovery.",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    features = tuple(name.strip() for name in args.features.split(",") if name.strip())
    productive_binding_found = False
    fixture_truth_pack_used = False

    if args.input_csv is not None:
        rows = _read_csv(args.input_csv, features)
        productive_binding_found = True
    elif args.fixture_scaffold or args.features == DEFAULT_FEATURES:
        rows, fixture_features = make_deterministic_signal_fixture()
        if args.features == DEFAULT_FEATURES:
            features = fixture_features
        fixture_truth_pack_used = True
    else:
        rows = []
        fixture_truth_pack_used = False

    config = SignalOrthogonalityConfigV1(
        correlation_threshold=args.correlation_threshold,
        condition_number_threshold=args.condition_number_threshold,
        min_samples=args.min_samples,
    )
    evidence = analyze_signal_orthogonality(
        rows,
        features,
        config=config,
        productive_binding_gap=not productive_binding_found and not fixture_truth_pack_used,
    )
    payload = evidence_to_dict(evidence)
    payload.update(
        {
            "offline_only": True,
            "runtime_authority": False,
            "order_authority": False,
            "promotion_pass_authority": False,
            "strategy_selection_changed": False,
            "economic_evaluation_executed": False,
            "system_economic_evidence_admissible": False,
            "runtime_rewire_admissible": False,
            "productive_binding_found": productive_binding_found,
            "fixture_truth_pack_used": fixture_truth_pack_used,
            "repo_root": str(repo_root),
            "signal_orthogonality_diagnostic_only": True,
            "signal_orthogonality_does_not_prove_profitability": True,
            "redundancy_does_not_delete_signal_automatically": True,
            "redundancy_can_downweight_evidence_only": True,
            "do_not_bind_signal_orthogonality_into_strategy_selection": True,
        }
    )

    report_json = out / "signal_orthogonality_evidence_v1.json"
    report_txt = out / "signal_orthogonality_report.txt"
    final_report = out / "final_report.txt"

    report_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_txt.write_text(
        "\n".join(
            [
                "VERDICT=OFFLINE_SIGNAL_ORTHOGONALITY_DIAGNOSTICS_V0_COLLECTED",
                "STATUS=" + str(payload["status"]),
                "AUTHORITY_EFFECT=" + AUTHORITY_EFFECT,
                "RUNTIME_EFFECT=" + RUNTIME_EFFECT,
                "OFFLINE_ONLY=true",
                "NO_STRATEGY_SELECTION_EFFECT=true",
                "NO_PROMOTION_PASS_AUTHORITY=true",
                "NO_RUNTIME_REWIRE=true",
                "PRODUCTIVE_BINDING_FOUND=" + str(productive_binding_found).lower(),
                "FIXTURE_TRUTH_PACK_USED=" + str(fixture_truth_pack_used).lower(),
                "REASON_CODES=" + ",".join(payload["reason_codes"]),
                "REDUNDANT_PAIR_COUNT="
                + str(len(payload["diagnostics"].get("redundant_pairs", []))),
                "DIAGNOSTICS_COMPUTED="
                + str(payload["diagnostics"].get("computed", False)).lower(),
                "",
            ]
        ),
        encoding="utf-8",
    )
    final_report.write_text(report_txt.read_text(encoding="utf-8"), encoding="utf-8")
    print(final_report.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
