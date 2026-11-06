"""Evidence sink protocol for the v2 gatekeeper (no dependency on session runtime)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class AuthorizationEvidenceSinkV1(Protocol):
    """Minimal write surface used after successful authorization consumption."""

    @property
    def evidence_root(self) -> Path: ...

    def write_immutable_json(self, name: str, payload: Mapping[str, Any]) -> None: ...

    def write_immutable_text(self, name: str, text: str) -> None: ...
