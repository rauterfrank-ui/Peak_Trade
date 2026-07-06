#!/usr/bin/env python3
"""Run post-no-pass STEP31F promotion metric materialization path execution gap diagnostics scope v0."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.research.post_no_pass_step31f_promotion_metric_materialization_path_execution_gap_diagnostics_scope_v0 import (  # noqa: E402
    CONFIRM_GO,
    run_scope_definition_materialization_v0,
)


def main() -> None:
    report = run_scope_definition_materialization_v0(
        confirm_go_token=CONFIRM_GO,
    )
    print(f"MANIFEST_VERIFY_RC={report['manifest_verify_rc']}")
    print(f"EVIDENCE_DIR={report['new_evidence_dir']}")


if __name__ == "__main__":
    main()
