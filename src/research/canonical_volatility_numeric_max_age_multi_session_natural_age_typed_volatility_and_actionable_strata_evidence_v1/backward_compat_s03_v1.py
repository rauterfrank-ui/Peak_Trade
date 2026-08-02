"""Backward verification that completed S03 evidence digests remain unchanged."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.constants_v1 import (
    S03_FROZEN_FILE_DIGESTS,
    S03_LEGACY_SESSION_REL,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.models_v1 import (
    MultiSessionTypedVolEvidenceError,
)


def sha256_file_v1(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_old_s03_evidence_digests_unchanged_v1(
    *,
    repo_root: Path,
    session_dir: Path | None = None,
    frozen_digests: dict[str, str] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root)
    session = Path(session_dir) if session_dir is not None else root / S03_LEGACY_SESSION_REL
    expected_map = dict(frozen_digests or S03_FROZEN_FILE_DIGESTS)
    if not session.is_dir():
        raise MultiSessionTypedVolEvidenceError("s03_session_missing_for_backward_verify")
    details = []
    all_ok = True
    for name, expected in sorted(expected_map.items()):
        path = session / name
        if not path.is_file():
            all_ok = False
            details.append({"file": name, "status": "MISSING"})
            continue
        actual = sha256_file_v1(path)
        match = actual == expected
        if not match:
            all_ok = False
        details.append(
            {
                "file": name,
                "expected": expected,
                "actual": actual,
                "match": match,
            }
        )
    if not all_ok:
        raise MultiSessionTypedVolEvidenceError("s03_evidence_digest_drift")
    return {
        "OLD_S03_EVIDENCE_DIGESTS_UNCHANGED": True,
        "OLD_S03_BACKWARD_VERIFICATION_PASS": True,
        "details": details,
    }
