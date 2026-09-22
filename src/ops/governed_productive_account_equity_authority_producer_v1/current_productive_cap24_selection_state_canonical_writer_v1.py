"""Canonical CURRENT productivity root writer for Cap-2.4 selection state.

Persists Cap-2.1→2.3 under ``runtime/current_productive/cap24_selection_state``
via existing producers only. Cap-2.4 provenance handoff remains consumer-only.
Requires separate Owner-GO and injected/fresh EEA acquisition input; no network
in this module.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionResultV1,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import ECONOMIC_RANK_ACTIVATED
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED,
    CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER_CREATED,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap21_to_cap23_productive_persistence_v1 import (
    CurrentProductiveCap21ToCap23PersistenceError,
    build_cap24_mark_prices_sidecar_from_acquisition_v1,
    run_cap21_to_cap23_persist_productive_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    MARK_PRICES_FILENAME,
    RUNTIME_STATE_DIRNAME,
    default_current_productive_cap24_runtime_state_root_v1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import RANKING_POLICY_ID
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAPABILITY_ID as CAP23_ID,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.persistence_v1 import (
    load_and_validate_selection_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SELECTION_AUTHORITY_OWNER,
)

OWNER_GO = "CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITE_V1"
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, f"OWNER_GO_{OWNER_GO}"})
EXPECTED_ORIGIN_MAIN_SHA = "87f4f2143af72b648a73c24d340574388c39aa0f"
THIS_SLICE = "11.2.1.EK.FULL_CORE_CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER"
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER_V1"
CONTRACT_VERSION = "v1"
PUBLISH_MANIFEST_FILENAME = "cap24_selection_state_publish_manifest_v1.json"
HISTORICAL_EVIDENCE_PREFIXES = (
    ("evidence", "ops"),
    ("docs", "evidence"),
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductiveCap24SelectionStateWriterError(RuntimeError):
    """Fail-closed Cap-24 selection-state writer violation."""


@dataclass(frozen=True)
class CurrentProductiveCap24SelectionStateWriteResultV1:
    ok: bool
    status: str
    productivity_root: str
    repository_sha: str
    decision_epoch: str
    cap23_selected_instrument_id: str
    cap23_selection_decision_id: str
    publish_manifest_path: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _assert_not_historical_productivity_root_v1(path: Path) -> None:
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(_REPO_ROOT.resolve())
    except ValueError:
        return
    parts = rel.parts
    for prefix in HISTORICAL_EVIDENCE_PREFIXES:
        if len(parts) >= len(prefix) and parts[: len(prefix)] == prefix:
            raise CurrentProductiveCap24SelectionStateWriterError(
                "HISTORICAL_EVIDENCE_PRODUCTIVITY_ROOT_FORBIDDEN"
            )


def _assert_protected_surfaces_v1() -> None:
    if CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER_CREATED is not True:
        raise CurrentProductiveCap24SelectionStateWriterError("WRITER_NOT_CREATED")
    if CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED is not False:
        raise CurrentProductiveCap24SelectionStateWriterError(
            "CANARY_INSTRUMENT_AUTHORITY_IMPORTED"
        )
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductiveCap24SelectionStateWriterError(
            "SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED"
        )
    if P01_RUNTIME_INSTANCE_PRESENT is not False:
        raise CurrentProductiveCap24SelectionStateWriterError(
            "RECONSTRUCTION_P01_RUNTIME_INSTANCE_MUST_REMAIN_FALSE"
        )
    if RANKING_POLICY_ID != "productive_futures_universe_structural_ranking_v1":
        raise CurrentProductiveCap24SelectionStateWriterError("RANKING_POLICY_DRIFT")
    if SELECTION_AUTHORITY_OWNER != CAP23_ID:
        raise CurrentProductiveCap24SelectionStateWriterError("SELECTION_OWNER_DRIFT")
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductiveCap24SelectionStateWriterError("MAX_POSITIONS_NOT_ONE")
    if MULTI_FUTURE_RUNTIME_AUTHORIZED is not False:
        raise CurrentProductiveCap24SelectionStateWriterError(
            "MULTI_FUTURE_RUNTIME_MUST_REMAIN_FALSE"
        )
    if ECONOMIC_RANK_ACTIVATED is not False:
        raise CurrentProductiveCap24SelectionStateWriterError("ECONOMIC_RANK_MUST_REMAIN_FALSE")


def _validate_persisted_cap21_cap23_v1(
    *,
    productivity_root: Path,
    repository_sha: str,
) -> None:
    state_root = productivity_root / RUNTIME_STATE_DIRNAME
    uni_load = load_and_validate_universe_snapshot_v1(
        state_root / "universe",
        expected_repository_sha=repository_sha,
        require_manifest=True,
    )
    if uni_load.ok is not True or uni_load.snapshot is None:
        raise CurrentProductiveCap24SelectionStateWriterError("CAP21_VALIDATE_FAIL_CLOSED")
    rank_load = load_and_validate_ranking_snapshot_v1(
        state_root / "ranking",
        expected_repository_sha=repository_sha,
        require_manifest=True,
    )
    if rank_load.ok is not True or rank_load.snapshot is None:
        raise CurrentProductiveCap24SelectionStateWriterError("CAP22_VALIDATE_FAIL_CLOSED")
    sel_load = load_and_validate_selection_v1(
        state_root / "selection",
        expected_repository_sha=repository_sha,
        require_manifest=True,
    )
    if sel_load.ok is not True or sel_load.selection is None:
        raise CurrentProductiveCap24SelectionStateWriterError("CAP23_VALIDATE_FAIL_CLOSED")
    selection = sel_load.selection
    if selection.state != STATE_SELECTED_ACTIVE:
        raise CurrentProductiveCap24SelectionStateWriterError("CAP23_SELECTION_NOT_ACTIVE")
    if selection.ranking_snapshot_id != rank_load.snapshot.ranking_snapshot_id:
        raise CurrentProductiveCap24SelectionStateWriterError("RANKING_SNAPSHOT_ID_MISMATCH")
    if selection.ranking_integrity_digest != rank_load.snapshot.integrity_digest:
        raise CurrentProductiveCap24SelectionStateWriterError("RANKING_INTEGRITY_MISMATCH")


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


def _atomic_publish_productivity_root_v1(
    *,
    staging_root: Path,
    productivity_root: Path,
    manifest_payload: Mapping[str, Any],
) -> None:
    productivity_root.mkdir(parents=True, exist_ok=True)
    staging_state = staging_root / RUNTIME_STATE_DIRNAME
    if not staging_state.is_dir():
        raise CurrentProductiveCap24SelectionStateWriterError("STAGING_RUNTIME_STATE_MISSING")
    mark_src = staging_root / MARK_PRICES_FILENAME
    if not mark_src.is_file():
        raise CurrentProductiveCap24SelectionStateWriterError("STAGING_MARK_PRICES_MISSING")

    target_state = productivity_root / RUNTIME_STATE_DIRNAME
    backup = productivity_root / f".{RUNTIME_STATE_DIRNAME}.rollback_{uuid.uuid4().hex}"
    had_state = target_state.exists()
    if had_state:
        shutil.move(str(target_state), str(backup))
    try:
        shutil.move(str(staging_state), str(target_state))
        mark_dst = productivity_root / MARK_PRICES_FILENAME
        _atomic_write_text(mark_dst, mark_src.read_text(encoding="utf-8"))
        manifest_path = productivity_root / PUBLISH_MANIFEST_FILENAME
        _atomic_write_text(manifest_path, _canonical_json(manifest_payload) + "\n")
    except Exception:
        if backup.exists():
            if target_state.exists():
                shutil.rmtree(target_state, ignore_errors=True)
            shutil.move(str(backup), str(target_state))
        raise
    finally:
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)


def execute_current_productive_cap24_selection_state_canonical_write_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    acquisition_result: EeaUniverseAcquisitionResultV1,
    productivity_root: Path | None = None,
    repository_sha: str | None = None,
    producer_observed_at_unix: float | None = None,
    decision_epoch: str | None = None,
    allow_default_productivity_root: bool = False,
) -> CurrentProductiveCap24SelectionStateWriteResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise CurrentProductiveCap24SelectionStateWriterError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveCap24SelectionStateWriterError("ORIGIN_MAIN_SHA_MISMATCH")
    if acquisition_result.ok is not True:
        raise CurrentProductiveCap24SelectionStateWriterError("ACQUISITION_INPUT_NOT_OK")
    _assert_protected_surfaces_v1()

    repo_sha = str(repository_sha or origin_main_sha).strip()
    if repo_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveCap24SelectionStateWriterError("REPOSITORY_SHA_BASELINE_MISMATCH")

    prod_root = (
        Path(productivity_root)
        if productivity_root is not None
        else default_current_productive_cap24_runtime_state_root_v1()
    )
    if productivity_root is None and allow_default_productivity_root is not True:
        raise CurrentProductiveCap24SelectionStateWriterError(
            "DEFAULT_PRODUCTIVITY_ROOT_REQUIRES_EXPLICIT_ALLOW"
        )
    _assert_not_historical_productivity_root_v1(prod_root)

    observed_unix = (
        float(producer_observed_at_unix)
        if producer_observed_at_unix is not None
        else datetime.now(timezone.utc).timestamp()
    )
    epoch = str(decision_epoch or "").strip() or datetime.fromtimestamp(
        observed_unix, tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    staging_root = prod_root.parent / f".cap24_selection_state_staging_{uuid.uuid4().hex}"
    staging_root.mkdir(parents=True, exist_ok=True)
    try:
        cap21_23 = run_cap21_to_cap23_persist_productive_v1(
            acquisition=acquisition_result,
            store=staging_root,
            repository_sha=repo_sha,
            observed_unix=observed_unix,
            session_id_prefix="current-productive-cap24-writer",
        )
        if cap21_23.ok is not True or cap21_23.selection is None:
            raise CurrentProductiveCap24SelectionStateWriterError(cap21_23.status)

        sidecar = build_cap24_mark_prices_sidecar_from_acquisition_v1(
            mark_price_payload=acquisition_result.mark_price_payload,
            venue_native_id=cap21_23.cap23_selected_instrument_id,
        )
        _atomic_write_text(
            staging_root / MARK_PRICES_FILENAME,
            _canonical_json(sidecar) + "\n",
        )
        _validate_persisted_cap21_cap23_v1(
            productivity_root=staging_root,
            repository_sha=repo_sha,
        )
        manifest = {
            "schema_class": SCHEMA_CLASS,
            "contract_version": CONTRACT_VERSION,
            "this_slice": THIS_SLICE,
            "owner_go": OWNER_GO,
            "repository_sha": repo_sha,
            "decision_epoch": epoch,
            "cap23_selection_decision_id": cap21_23.cap23_selection_decision_id,
            "cap23_selected_instrument_id": cap21_23.cap23_selected_instrument_id,
            "cap21_snapshot_id": cap21_23.cap21_snapshot_id,
            "cap22_ranking_id": cap21_23.cap22_ranking_id,
            "mark_price_sidecar": MARK_PRICES_FILENAME,
            "publish_digest": _sha256_text(
                _canonical_json(
                    {
                        "repository_sha": repo_sha,
                        "selection_id": cap21_23.cap23_selection_decision_id,
                        "venue_native_id": cap21_23.cap23_selected_instrument_id,
                    }
                )
            ),
        }
        _atomic_publish_productivity_root_v1(
            staging_root=staging_root,
            productivity_root=prod_root,
            manifest_payload=manifest,
        )
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)

    return CurrentProductiveCap24SelectionStateWriteResultV1(
        ok=True,
        status="PASS",
        productivity_root=str(prod_root),
        repository_sha=repo_sha,
        decision_epoch=epoch,
        cap23_selected_instrument_id=cap21_23.cap23_selected_instrument_id,
        cap23_selection_decision_id=cap21_23.cap23_selection_decision_id,
        publish_manifest_path=str(prod_root / PUBLISH_MANIFEST_FILENAME),
    )


def main(argv: list[str] | None = None) -> int:
    raise SystemExit(
        "FAIL_CLOSED: productive write requires Owner-GO and injected acquisition; "
        "use execute_current_productive_cap24_selection_state_canonical_write_v1"
    )
