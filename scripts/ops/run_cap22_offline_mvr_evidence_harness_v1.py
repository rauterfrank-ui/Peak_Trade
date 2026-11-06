#!/usr/bin/env python3
"""Standalone offline Cap 2.2 MVR evidence harness.

Injected or persisted snapshot replay only. No network. Not productively
scheduled. No ranking activation, Policy A, Active Set, or execution.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT,):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.cap22_offline_mvr_evidence_harness_v1.constants_v1 import (  # noqa: E402
    DEFAULT_EVIDENCE_CLASS,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.harness_v1 import (  # noqa: E402
    OfflineMvrHarnessError,
    run_offline_mvr_evidence_harness_v1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.threshold_set_v1 import (  # noqa: E402
    injected_test_only_non_canonical_policy_b_threshold_set_v1,
)
from src.ops.economic_md_input_producer_v1.models_v1 import (  # noqa: E402
    canonical_json_dumps,
)


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cap 2.2 offline MVR evidence harness (injected/file replay only)."
    )
    parser.add_argument("--economic-md-snapshot", required=True, type=Path)
    parser.add_argument("--universe-snapshot", required=True, type=Path)
    parser.add_argument("--threshold-set", type=Path, default=None)
    parser.add_argument(
        "--use-test-only-threshold-set",
        action="store_true",
        help="Use the explicit TEST_ONLY_NON_CANONICAL fixture grid. Not canonical.",
    )
    parser.add_argument("--evidence-class", default=DEFAULT_EVIDENCE_CLASS)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    economic = _load_json(args.economic_md_snapshot)
    universe = _load_json(args.universe_snapshot)
    if args.threshold_set is not None:
        threshold_set: Mapping[str, Any] | Any = _load_json(args.threshold_set)
    elif args.use_test_only_threshold_set:
        threshold_set = injected_test_only_non_canonical_policy_b_threshold_set_v1()
    else:
        threshold_set = None
    try:
        result = run_offline_mvr_evidence_harness_v1(
            economic_md_snapshot=economic,
            universe_snapshot=universe,
            policy_b_threshold_set=threshold_set,
            evidence_class=str(args.evidence_class),
        )
    except OfflineMvrHarnessError as exc:
        print(json.dumps({"ok": False, "failure_code": exc.failure_code, "detail": exc.detail}))
        return 2
    text = canonical_json_dumps(result)
    if args.output is not None:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
