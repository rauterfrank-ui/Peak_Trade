#!/usr/bin/env python3
"""Run post-no-pass metric materialization path activation binding ratification v0."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.materialize_post_no_pass_metric_materialization_path_activation_binding_ratification_v0 import (  # noqa: E402
    CONFIRM_GO,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    run_materialization,
)


def main() -> None:
    report = run_materialization(
        confirm=CONFIRM_GO,
        durable_evidence_root=DEFAULT_DURABLE_ARCHIVE_ROOT,
        write_repo_config=True,
    )
    print(f"MANIFEST_VERIFY_RC={report['manifest_verify_rc']}")
    print(f"EVIDENCE_DIR={report['evidence_dir']}")


if __name__ == "__main__":
    main()
