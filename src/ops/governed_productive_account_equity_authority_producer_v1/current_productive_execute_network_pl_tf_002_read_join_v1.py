"""#6806 execute_network READ join via proven PL-TF-002 K1 session (GET-only).

Reuses PL-TF-002 productive read-only session executor. Does not create a
parallel credential authority. Does not authorize POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
    OWNER_GO as PL_TF_002_SESSION_OWNER_GO,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 import (
    PlTf002ProductiveReadOnlySessionError,
    open_pl_tf_002_productive_read_only_get_session_v1,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_EXECUTE_NETWORK_PL_TF_002_READ_JOIN_V1"


@dataclass
class ProductivePlTf002ReadSessionBorrowV1:
    """Keeps PL-TF-002 session alive until release_productive_credential_handle_v1."""

    _ctx: Any
    session: Any
    origin_main_sha: str

    def transport(self) -> FullCoreProductiveReadOnlyGetTransportV1:
        transport = getattr(self.session, "transport", None)
        if transport is None:
            raise PlTf002ProductiveReadOnlySessionError("PLTF002_TRANSPORT_RELEASED")
        return transport


def try_bind_pl_tf_002_read_transport_for_execute_network_v1(
    *,
    origin_main_sha: str,
    repo_root: Path,
) -> tuple[FullCoreFreshPretradeGetTransportV1 | None, ProductivePlTf002ReadSessionBorrowV1 | None]:
    """Open ephemeral PL-TF-002 read session or fail closed (no secrets returned)."""
    del repo_root
    bound_sha = str(origin_main_sha or "").strip()
    if not bound_sha:
        return None, None
    ctx = open_pl_tf_002_productive_read_only_get_session_v1(
        owner_go=PL_TF_002_SESSION_OWNER_GO,
        origin_main_sha=bound_sha,
        acquire_credential=True,
    )
    try:
        session = ctx.__enter__()
    except PlTf002ProductiveReadOnlySessionError:
        return None, None
    except Exception:
        try:
            ctx.__exit__(None, None, None)
        except Exception:
            pass
        return None, None
    borrow = ProductivePlTf002ReadSessionBorrowV1(
        _ctx=ctx,
        session=session,
        origin_main_sha=bound_sha,
    )
    return borrow.transport(), borrow


def release_pl_tf_002_read_session_borrow_v1(
    borrow: ProductivePlTf002ReadSessionBorrowV1 | None,
    *,
    exc_type: type[BaseException] | None = None,
    exc: BaseException | None = None,
    tb: TracebackType | None = None,
) -> None:
    if borrow is None:
        return
    try:
        borrow._ctx.__exit__(exc_type, exc, tb)
    finally:
        borrow.session = None


__all__ = [
    "JOIN_SEAM_ID",
    "ProductivePlTf002ReadSessionBorrowV1",
    "release_pl_tf_002_read_session_borrow_v1",
    "try_bind_pl_tf_002_read_transport_for_execute_network_v1",
]
