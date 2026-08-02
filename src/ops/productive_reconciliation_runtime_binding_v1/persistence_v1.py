"""Atomic persist + verify-after-write for productive portfolio/recon state."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    PORTFOLIO_STATE_FILENAME,
    STAGING_DIRNAME_PREFIX,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
    ProductiveReconciliationEvidenceV1,
    canonical_json_dumps,
    sha256_hex,
)
from src.ops.productive_reconciliation_runtime_binding_v1.single_writer_v1 import (
    ProductivePortfolioSingleWriterV1,
)


class PersistenceVerificationError(RuntimeError):
    """Persist/verify failure."""


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


def write_manifest(root: Path, relative_files: tuple[str, ...]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = sha256_hex((root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    body = "\n".join(lines) + "\n"
    _atomic_write_text(root / MANIFEST_FILENAME, body)
    return sha256_hex(body)


def verify_manifest(root: Path) -> dict[str, Any]:
    manifest = root / MANIFEST_FILENAME
    if not manifest.is_file():
        raise PersistenceVerificationError("MANIFEST_MISSING")
    errors: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        path = root / rel
        if not path.is_file():
            errors.append(f"MISSING:{rel}")
            continue
        actual = sha256_hex(path.read_bytes())
        if actual != digest:
            errors.append(f"DIGEST_MISMATCH:{rel}")
    if errors:
        raise PersistenceVerificationError(";".join(errors))
    return {"ok": True, "manifest_path": str(manifest)}


def snapshot_from_payload(payload: Mapping[str, Any]) -> PortfolioTruthSnapshotV1:
    positions = tuple(
        PositionTruthV1.from_signed(
            instrument_id=str(p["instrument_id"]),
            signed_quantity=p["signed_quantity"],
            source_id=str(p.get("source_id") or "persisted"),
            mark_price=p.get("mark_price"),
            event_time_unix=p.get("event_time_unix"),
            wall_time_unix=p.get("wall_time_unix"),
        )
        for p in (payload.get("positions") or [])
    )
    cash = payload.get("cash")
    return PortfolioTruthSnapshotV1(
        positions=positions,
        cash=None if cash is None else __import__("decimal").Decimal(str(cash)),
        source_id=str(payload.get("source_id") or "persisted"),
        event_time_unix=payload.get("event_time_unix"),
        wall_time_unix=payload.get("wall_time_unix"),
        missing=bool(payload.get("missing", False)),
        stale=bool(payload.get("stale", False)),
        duplicate=bool(payload.get("duplicate", False)),
        writer_conflict=bool(payload.get("writer_conflict", False)),
        max_age_seconds=payload.get("max_age_seconds"),
    )


def load_persisted_portfolio_state(
    state_root: Path,
    *,
    require_present: bool = False,
) -> PortfolioTruthSnapshotV1:
    path = Path(state_root) / PORTFOLIO_STATE_FILENAME
    if not path.is_file():
        if require_present:
            return PortfolioTruthSnapshotV1(missing=True, source_id="persisted")
        # Clean start: empty truth is valid MATCH candidate.
        return PortfolioTruthSnapshotV1(positions=(), source_id="persisted_absent_clean")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return PortfolioTruthSnapshotV1(missing=True, source_id="persisted_unreadable")
    return snapshot_from_payload(payload)


def detect_duplicate_portfolio_state(state_root: Path) -> bool:
    root = Path(state_root)
    candidates = list(root.glob("productive_portfolio_state_v1*.json"))
    # Canonical file + any alternate copy with same stem pattern beyond the canonical name.
    extras = [p for p in candidates if p.name != PORTFOLIO_STATE_FILENAME]
    return len(extras) > 0


def persist_reconciliation_bundle_atomic(
    *,
    state_root: Path,
    writer: ProductivePortfolioSingleWriterV1,
    portfolio: PortfolioTruthSnapshotV1,
    evidence: ProductiveReconciliationEvidenceV1,
    simulate_crash_after_persist_before_verify: bool = False,
) -> dict[str, Any]:
    """Atomically stage→publish portfolio + evidence + manifest, then verify."""
    writer.assert_held()
    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    staging = root / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        portfolio_payload = portfolio.to_dict()
        evidence_payload = evidence.to_dict()
        (staging / PORTFOLIO_STATE_FILENAME).write_text(
            json.dumps(portfolio_payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (staging / EVIDENCE_FILENAME).write_text(
            json.dumps(evidence_payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_manifest(staging, (PORTFOLIO_STATE_FILENAME, EVIDENCE_FILENAME))

        # Publish: replace files atomically from staging.
        for name in (PORTFOLIO_STATE_FILENAME, EVIDENCE_FILENAME, MANIFEST_FILENAME):
            src = staging / name
            dst = root / name
            _atomic_write_text(dst, src.read_text(encoding="utf-8"))

        if simulate_crash_after_persist_before_verify:
            return {
                "ok": False,
                "crashed_before_verify": True,
                "post_state_digest": portfolio.digest(),
                "evidence_digest": evidence.digest(),
            }

        verification = verify_manifest(root)
        reloaded = load_persisted_portfolio_state(root, require_present=True)
        if reloaded.missing:
            raise PersistenceVerificationError("RELOAD_MISSING_AFTER_PERSIST")
        if reloaded.digest() != portfolio.digest():
            raise PersistenceVerificationError("POST_DIGEST_MISMATCH_AFTER_RELOAD")
        return {
            "ok": True,
            "crashed_before_verify": False,
            "verification": verification,
            "post_state_digest": portfolio.digest(),
            "evidence_digest": evidence.digest(),
            "reloaded_digest": reloaded.digest(),
        }
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def config_digest_for_binding(*, repository_sha: str, max_open_positions: int = 1) -> str:
    payload = {
        "PRODUCTIVE_RECONCILIATION_BOUND": True,
        "max_open_positions": max_open_positions,
        "repository_sha": repository_sha,
        "LIVE_AUTHORIZED": False,
        "ORDERS_AUTHORIZED": False,
    }
    return sha256_hex(canonical_json_dumps(payload))
