"""Deterministic archive-universe session identity (content pin, TOCTOU guard)."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.productive_decision_host_active_archive_three_family_binding_v1.authorization_v1 import (
    ProductiveHostAuthorizationError,
)
from src.ops.workflow_archive_readmodel_projections_v1.universe_selection_contract_v1 import (
    STORAGE_RELATIVE_PATH,
    UniverseSelectionContractV1,
)
from src.ops.workflow_archive_readmodel_projections_v1.universe_selection_producer_v1 import (
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
)
from src.ops.workflow_archive_readmodel_projections_v1.universe_selection_reader_v1 import (
    UniverseSelectionVerifiedLoadError,
    load_universe_selection_contract_verified_v1,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class ArchiveUniverseSessionPinV1:
    """Pinned verified snapshot of universe_selection_readmodel.v1 for one smoke session."""

    archive_root: str
    readmodel_relative_path: str
    universe_file_sha256: str
    source_run_id: str
    generated_at: str
    selected_symbol: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_archive_universe_session_pin_v1(
    *,
    archive_root: str | Path,
    payload: Mapping[str, Any],
    contract: UniverseSelectionContractV1,
) -> ArchiveUniverseSessionPinV1:
    root = Path(archive_root).expanduser().resolve()
    readmodels = root / READMODELS_DIRNAME
    readmodel_path = readmodels / READMODEL_FILENAME
    if contract.selected_future is None or not str(contract.selected_future.symbol).strip():
        raise ProductiveHostAuthorizationError(
            "SELECTED_INSTRUMENT_MISSING",
            "pin requires selected_future.symbol",
        )
    return ArchiveUniverseSessionPinV1(
        archive_root=str(root),
        readmodel_relative_path=STORAGE_RELATIVE_PATH,
        universe_file_sha256=_sha256_file(readmodel_path),
        source_run_id=str(contract.source_run_id),
        generated_at=str(contract.generated_at),
        selected_symbol=str(contract.selected_future.symbol).strip(),
    )


def establish_archive_universe_session_pin_v1(
    *,
    archive_root: str | Path,
) -> ArchiveUniverseSessionPinV1:
    """Verify-before-trust load and pin universe identity for archive-smoke."""
    try:
        payload, contract = load_universe_selection_contract_verified_v1(
            archive_root,
            require_non_authorizing=True,
            reject_fixture_marked=False,
        )
    except UniverseSelectionVerifiedLoadError as exc:
        raise ProductiveHostAuthorizationError(
            "ARCHIVE_UNIVERSE_VERIFY_FAILED",
            str(exc),
        ) from exc
    return build_archive_universe_session_pin_v1(
        archive_root=archive_root,
        payload=payload,
        contract=contract,
    )


def assert_archive_universe_session_pin_unchanged_v1(pin: ArchiveUniverseSessionPinV1) -> None:
    """Re-verify manifest + universe file identity before consumption (TOCTOU guard).

    Sibling exports may extend readmodels/ and rewrite MANIFEST.sha256; the pin tracks
    only the bound universe_selection readmodel bytes and contract identity fields.
    """
    current = establish_archive_universe_session_pin_v1(archive_root=pin.archive_root)
    if current != pin:
        raise ProductiveHostAuthorizationError(
            "ARCHIVE_SESSION_PIN_DRIFT",
            f"expected={pin.to_dict()}:current={current.to_dict()}",
        )


__all__ = [
    "ArchiveUniverseSessionPinV1",
    "assert_archive_universe_session_pin_unchanged_v1",
    "build_archive_universe_session_pin_v1",
    "establish_archive_universe_session_pin_v1",
]
