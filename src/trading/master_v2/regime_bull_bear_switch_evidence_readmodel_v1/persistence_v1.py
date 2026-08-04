"""Atomic durable write / explicit-path load for evidence readmodel (non-restart)."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1.constants_v1 import (
    ERROR_LOAD_FAILED,
    ERROR_PATH_REQUIRED,
    ERROR_WRITE_FAILED,
)
from trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1.models_v1 import (
    RegimeBullBearSwitchEvidenceError,
    RegimeBullBearSwitchEvidenceReadmodelV1,
)

_LOG = logging.getLogger(__name__)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def write_regime_bull_bear_switch_evidence_readmodel_v1(
    path: str | Path,
    evidence: RegimeBullBearSwitchEvidenceReadmodelV1,
) -> Path:
    """Atomically write evidence JSON to an explicit path. No latest discovery."""
    if path is None or (isinstance(path, str) and not path.strip()):
        raise RegimeBullBearSwitchEvidenceError(ERROR_PATH_REQUIRED, "path")
    target = Path(path).expanduser().resolve()
    if not isinstance(evidence, RegimeBullBearSwitchEvidenceReadmodelV1):
        raise RegimeBullBearSwitchEvidenceError(ERROR_WRITE_FAILED, "evidence_type")
    try:
        body = json.dumps(evidence.to_dict(), sort_keys=True, indent=2, allow_nan=False) + "\n"
        _atomic_write_text(target, body)
    except RegimeBullBearSwitchEvidenceError:
        raise
    except OSError as exc:
        _LOG.warning(
            "regime_bbs_evidence_write_failed path=%s code=%s",
            str(target),
            ERROR_WRITE_FAILED,
        )
        raise RegimeBullBearSwitchEvidenceError(ERROR_WRITE_FAILED, type(exc).__name__) from exc
    _LOG.info(
        "regime_bbs_evidence_written classification=%s restart_authority=%s path=%s digest=%s",
        evidence.evidence_classification,
        evidence.restart_authority,
        str(target),
        evidence.content_digest(),
    )
    return target


def load_regime_bull_bear_switch_evidence_readmodel_v1(
    path: str | Path,
) -> RegimeBullBearSwitchEvidenceReadmodelV1:
    """Load evidence from an explicit path. Never scans for latest artifacts."""
    if path is None or (isinstance(path, str) and not path.strip()):
        raise RegimeBullBearSwitchEvidenceError(ERROR_PATH_REQUIRED, "path")
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise RegimeBullBearSwitchEvidenceError(ERROR_LOAD_FAILED, "missing")
    try:
        raw = target.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise RegimeBullBearSwitchEvidenceError(ERROR_LOAD_FAILED, type(exc).__name__) from exc
    if not isinstance(payload, dict):
        raise RegimeBullBearSwitchEvidenceError(ERROR_LOAD_FAILED, "not_object")
    return RegimeBullBearSwitchEvidenceReadmodelV1.from_dict(payload)
