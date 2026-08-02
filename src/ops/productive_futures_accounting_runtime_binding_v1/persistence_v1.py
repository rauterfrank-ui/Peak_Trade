"""Atomic persist + verify for Cap 3.1 accounting/portfolio/risk state."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    ACCOUNTING_STATE_FILENAME,
    EVIDENCE_FILENAME,
    FILL_LEDGER_FILENAME,
    MANIFEST_FILENAME,
    PORTFOLIO_STATE_FILENAME,
    RESULT_FILENAME,
    RISK_STATE_FILENAME,
    STAGING_DIRNAME_PREFIX,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
    ProductiveFuturesAccountingEvidenceV1,
    sha256_hex,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.reason_codes_v1 import (
    AccountingFailureCodeV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.single_writer_v1 import (
    ProductiveFuturesAccountingSingleWriterV1,
)


class PersistenceInterruptionError(RuntimeError):
    def __init__(self, detail: str = "") -> None:
        self.code = AccountingFailureCodeV1.PERSISTENCE_INTERRUPTION
        super().__init__(f"{self.code.value}:{detail}" if detail else self.code.value)


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
    manifest = Path(root) / MANIFEST_FILENAME
    if not manifest.is_file():
        raise PersistenceInterruptionError("MANIFEST_MISSING")
    errors: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        path = Path(root) / rel
        if not path.is_file():
            errors.append(f"MISSING:{rel}")
            continue
        actual = sha256_hex(path.read_bytes())
        if actual != digest:
            errors.append(f"DIGEST_MISMATCH:{rel}")
    if errors:
        raise PersistenceInterruptionError(";".join(errors))
    return {"ok": True, "manifest_path": str(manifest)}


def load_accounting_session(
    state_root: Path,
    *,
    require_present: bool = False,
) -> Optional[ProductiveFuturesAccountingSessionV1]:
    path = Path(state_root) / ACCOUNTING_STATE_FILENAME
    if not path.is_file():
        if require_present:
            raise PersistenceInterruptionError("ACCOUNTING_STATE_MISSING")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ProductiveFuturesAccountingSessionV1.from_durable_dict(payload)
    except Exception as exc:  # noqa: BLE001
        raise PersistenceInterruptionError(f"RESTART_LEDGER_CORRUPT:{exc}") from exc


def persist_accounting_bundle_atomic_v1(
    *,
    state_root: Path,
    session: ProductiveFuturesAccountingSessionV1,
    writer: ProductiveFuturesAccountingSingleWriterV1,
    evidence: ProductiveFuturesAccountingEvidenceV1 | Mapping[str, Any] | None = None,
    result: Mapping[str, Any] | None = None,
    interrupt_after_fill_before_accounting: bool = False,
) -> dict[str, Any]:
    """Atomically persist accounting + portfolio + risk derived solely from kernel session."""
    writer.assert_held()
    if interrupt_after_fill_before_accounting:
        raise PersistenceInterruptionError("INJECTED_INTERRUPT_AFTER_FILL_BEFORE_ACCOUNTING")

    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    staging = root / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        durable = session.to_durable_dict()
        portfolio = session.portfolio_state().to_dict()
        risk = session.risk_state().to_dict()
        (staging / ACCOUNTING_STATE_FILENAME).write_text(
            json.dumps(durable, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        (staging / PORTFOLIO_STATE_FILENAME).write_text(
            json.dumps(portfolio, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        (staging / RISK_STATE_FILENAME).write_text(
            json.dumps(risk, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        # Append-only fill ledger projection for restart/idempotency evidence.
        ledger_lines = []
        for fid in session.fill_order:
            applied = session.applied_fill_results[fid]
            ledger_lines.append(
                json.dumps(
                    {
                        "fill_id": fid,
                        "fill_input_digest": applied.fill_input_digest,
                        "accounting_output_digest": applied.accounting_output_digest,
                        "action_code": applied.action_code,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        (staging / FILL_LEDGER_FILENAME).write_text(
            ("\n".join(ledger_lines) + ("\n" if ledger_lines else "")),
            encoding="utf-8",
        )
        rels = [
            ACCOUNTING_STATE_FILENAME,
            PORTFOLIO_STATE_FILENAME,
            RISK_STATE_FILENAME,
            FILL_LEDGER_FILENAME,
        ]
        if evidence is not None:
            ev = evidence.to_dict() if hasattr(evidence, "to_dict") else dict(evidence)
            (staging / EVIDENCE_FILENAME).write_text(
                json.dumps(ev, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
            rels.append(EVIDENCE_FILENAME)
        if result is not None:
            (staging / RESULT_FILENAME).write_text(
                json.dumps(dict(result), sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
            rels.append(RESULT_FILENAME)
        write_manifest(staging, tuple(rels))
        for name in (*rels, MANIFEST_FILENAME):
            _atomic_write_text(root / name, (staging / name).read_text(encoding="utf-8"))
        verification = verify_manifest(root)
        return {
            "ok": True,
            "verification": verification,
            "state_root": str(root),
            "portfolio_state_digest": session.portfolio_state().digest(),
            "risk_state_digest": session.risk_state().digest(),
        }
    except PersistenceInterruptionError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PersistenceInterruptionError(str(exc)) from exc
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
