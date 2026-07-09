from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.linear_evidence.signal_orthogonality import (
    SignalOrthogonalityConfigV1,
    analyze_signal_orthogonality,
    evidence_to_dict,
    make_deterministic_signal_fixture,
)


def _read_csv(path: Path, features: Tuple[str, ...]) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in features if name not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"missing feature columns: {','.join(missing)}")
        return [dict(row) for row in reader]


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline signal orthogonality diagnostics v0")
    parser.add_argument("--out", required=True)
    parser.add_argument("--input-csv", default="")
    parser.add_argument(
        "--features", default="trend_following,momentum_1h,bollinger_bands,liquidity_context"
    )
    parser.add_argument("--correlation-threshold", type=float, default=0.85)
    parser.add_argument("--condition-number-threshold", type=float, default=1000.0)
    parser.add_argument("--min-samples", type=int, default=8)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    features = tuple(name.strip() for name in args.features.split(",") if name.strip())
    if args.input_csv:
        rows = _read_csv(Path(args.input_csv), features)
    else:
        rows, fixture_features = make_deterministic_signal_fixture()
        if args.features == "trend_following,momentum_1h,bollinger_bands,liquidity_context":
            features = fixture_features

    config = SignalOrthogonalityConfigV1(
        correlation_threshold=args.correlation_threshold,
        condition_number_threshold=args.condition_number_threshold,
        min_samples=args.min_samples,
    )
    evidence = analyze_signal_orthogonality(rows, features, config=config)
    payload = evidence_to_dict(evidence)

    report_json = out / "signal_orthogonality_evidence_v1.json"
    report_txt = out / "signal_orthogonality_report.txt"
    final_report = out / "final_report.txt"

    report_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    report_txt.write_text(
        "\n".join(
            [
                "VERDICT=OFFLINE_SIGNAL_ORTHOGONALITY_DIAGNOSTICS_V0_COLLECTED",
                "STATUS=" + str(payload["status"]),
                "AUTHORITY_EFFECT=" + str(payload["authority_effect"]),
                "RUNTIME_EFFECT=" + str(payload["runtime_effect"]),
                "OFFLINE_ONLY=true",
                "NO_STRATEGY_SELECTION_EFFECT=true",
                "NO_PROMOTION_PASS_AUTHORITY=true",
                "NO_RUNTIME_REWIRE=true",
                "REASON_CODES=" + ",".join(payload["reason_codes"]),
                "REDUNDANT_PAIR_COUNT=" + str(len(payload["diagnostics"]["redundant_pairs"])),
                "CONDITION_NUMBER=" + str(payload["diagnostics"]["condition_number"]),
                "RANK=" + str(payload["diagnostics"]["rank"]),
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
