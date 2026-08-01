"""Terminal verdict / integrity evidence for preregistered session runner."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    CAPABILITY_ID,
    REVIEW_MODE_ID,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    PreregisteredSessionRunnerError,
)


def write_session_terminal_evidence_v1(
    *,
    session_manifest_path: Path,
    payload: Mapping[str, Any],
) -> Path:
    path = Path(session_manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "capability_id": CAPABILITY_ID,
        "review_mode": REVIEW_MODE_ID,
        "economic_validity_claimed": False,
        "promotion_authorized": False,
        **dict(payload),
    }
    text = json.dumps(body, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_TRUNC, 0o644)
    try:
        os.write(fd, text.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    if not path.is_file():
        raise PreregisteredSessionRunnerError("terminal_evidence_write_failed")
    return path


def build_integrity_manifest_v1(
    *,
    session_id: str,
    campaign_id: str,
    authorization_id: str,
    authorization_digest: str,
    preregistration_digest: str,
    repository_sha: str,
    authorization_consumed: bool,
    cycles_executed: int,
    records_appended: int,
    ledger_integrity: Mapping[str, Any] | None,
    terminal_state: str,
    terminal_verdict: str,
) -> dict[str, Any]:
    return {
        "schema": "canonical_volatility_numeric_max_age_preregistered_session_integrity/v1",
        "session_id": session_id,
        "campaign_id": campaign_id,
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "preregistration_digest": preregistration_digest,
        "repository_sha": repository_sha,
        "authorization_consumed": authorization_consumed,
        "cycles_executed": cycles_executed,
        "records_appended": records_appended,
        "ledger_integrity": dict(ledger_integrity or {}),
        "terminal_state": terminal_state,
        "terminal_verdict": terminal_verdict,
        "full_reconstruction_possible": bool(authorization_consumed and terminal_state),
        "economic_validity_claimed": False,
        "promotion_authorized": False,
    }
