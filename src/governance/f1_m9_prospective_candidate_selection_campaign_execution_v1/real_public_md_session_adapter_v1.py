"""REAL public-MD session adapter binding for F1/M9 campaign orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    REAL_MD_SUPPLIER_ID,
    REAL_MD_SUPPLIER_MODULE,
)


@dataclass(frozen=True, slots=True)
class RealPublicMdSessionResultV1:
    session_id: str
    work_unit_index: int
    evidence_source_class: str
    public_md_fetch_count: int
    private_api_effect: bool
    credential_access: bool
    order_effect: bool
    supplier_id: str
    supplier_module: str
    sample_digest: str


class RealPublicMdSessionAdapterV1(Protocol):
    def execute_work_unit_v1(
        self,
        *,
        work_unit: Mapping[str, Any],
        authorization: Mapping[str, Any],
    ) -> RealPublicMdSessionResultV1: ...


def resolve_canonical_real_md_supplier_runtime_binding_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    module_path = REAL_MD_SUPPLIER_MODULE.replace(".", "/")
    py_path = root / "src" / f"{module_path}.py"
    return {
        "real_md_supplier_runtime_bound": py_path.is_file(),
        "real_md_supplier_id": REAL_MD_SUPPLIER_ID,
        "real_md_supplier_module": REAL_MD_SUPPLIER_MODULE,
    }


class FakeRealPublicMdSessionAdapterV1:
    """Test-only adapter: REAL-path wiring without network (not REAL runtime evidence)."""

    def __init__(self, *, evidence_source_class: str = "REAL_PUBLIC_MARKET_DATA") -> None:
        self._evidence_source_class = evidence_source_class
        self.executed_session_ids: list[str] = []

    def execute_work_unit_v1(
        self,
        *,
        work_unit: Mapping[str, Any],
        authorization: Mapping[str, Any],
    ) -> RealPublicMdSessionResultV1:
        session_id = str(work_unit.get("session_id") or "")
        self.executed_session_ids.append(session_id)
        digest = f"fake-real-md:{session_id}:{authorization.get('authorization_id')}"
        return RealPublicMdSessionResultV1(
            session_id=session_id,
            work_unit_index=int(work_unit.get("work_unit_index") or 0),
            evidence_source_class=self._evidence_source_class,
            public_md_fetch_count=1,
            private_api_effect=False,
            credential_access=False,
            order_effect=False,
            supplier_id=REAL_MD_SUPPLIER_ID,
            supplier_module=REAL_MD_SUPPLIER_MODULE,
            sample_digest=digest,
        )


__all__ = [
    "FakeRealPublicMdSessionAdapterV1",
    "RealPublicMdSessionAdapterV1",
    "RealPublicMdSessionResultV1",
    "resolve_canonical_real_md_supplier_runtime_binding_v1",
]
