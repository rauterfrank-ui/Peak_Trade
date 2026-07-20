"""Acquisition adapter interface and OKX public scaffold (network gated)."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    ArchiveRootError,
    archive_layout,
    assert_path_under_archive,
)
from src.research.longer_chronological_pit_acquisition_v1.manifest import (
    expected_artifact_relpath,
)
from src.research.longer_chronological_pit_acquisition_v1.resume_state import (
    write_immutable_partition_bytes,
)


class NetworkDisabledError(RuntimeError):
    """Raised when network acquire is attempted without allow_network."""


class AcquisitionAdapter(Protocol):
    def acquire_partition(
        self,
        partition: Mapping[str, Any],
        *,
        allow_network: bool,
        archive_root: Path | None,
        write: bool,
    ) -> dict[str, Any]: ...


Fetcher = Callable[[str], bytes]


@dataclass
class OkxPublicHistoryAdapterV1:
    """Scaffold adapter. Default: no network. Probe-limited acquire behind flags."""

    fetcher: Fetcher | None = None
    max_retries: int = 3
    backoff_seconds: float = 0.01  # tests use tiny backoff
    sleep: Callable[[float], None] = time.sleep

    def acquire_partition(
        self,
        partition: Mapping[str, Any],
        *,
        allow_network: bool,
        archive_root: Path | None,
        write: bool,
        source_locator: str | None = None,
        expected_checksum: str | None = None,
    ) -> dict[str, Any]:
        if not allow_network:
            raise NetworkDisabledError("NETWORK_DISABLED_DEFAULT")
        if self.fetcher is None:
            raise NetworkDisabledError("FETCHER_NOT_CONFIGURED")
        locator = source_locator or str(partition.get("source_locator") or "")
        if not locator:
            raise ValueError("MISSING_SOURCE_LOCATOR")

        last_err: Exception | None = None
        body: bytes | None = None
        for attempt in range(self.max_retries + 1):
            try:
                body = self.fetcher(locator)
                break
            except Exception as exc:  # noqa: BLE001 — modeled retry boundary
                last_err = exc
                if "RATE_LIMIT" in str(exc).upper() and attempt < self.max_retries:
                    self.sleep(self.backoff_seconds * (2**attempt))
                    continue
                if attempt < self.max_retries:
                    self.sleep(self.backoff_seconds * (2**attempt))
                    continue
                raise
        if body is None:
            assert last_err is not None
            raise last_err

        checksum = hashlib.sha256(body).hexdigest()
        if expected_checksum is not None and checksum != expected_checksum:
            if write:
                if archive_root is None:
                    raise ArchiveRootError("MISSING_ARCHIVE_ROOT_FOR_QUARANTINE")
                qdir = archive_layout(archive_root)["quarantine"]
                qdir.mkdir(parents=True, exist_ok=True)
                qpath = assert_path_under_archive(
                    qdir / f"{partition['partition_id']}.checksum_mismatch.bin",
                    archive_root,
                )
                qpath.write_bytes(body)
            return {
                "status": "QUARANTINED",
                "error_code": "CHECKSUM_MISMATCH",
                "checksum": checksum,
                "expected_checksum": expected_checksum,
                "byte_size": len(body),
                "retry_count": self.max_retries,
            }

        rel = expected_artifact_relpath(partition)
        artifact_path = None
        if write:
            if archive_root is None:
                raise ArchiveRootError("MISSING_ARCHIVE_ROOT_FOR_WRITE")
            artifact_path = str(
                write_immutable_partition_bytes(
                    archive_root=archive_root,
                    relative_path=rel,
                    payload=body,
                )
            )

        return {
            "status": "ACQUIRED",
            "checksum": checksum,
            "byte_size": len(body),
            "expected_artifact_path": rel,
            "artifact_path": artifact_path,
            "retry_count": 0,
            "error_code": None,
        }
