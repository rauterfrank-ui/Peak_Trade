"""Single baseline contract for the CURRENT_PRODUCTIVE 29P dependency chain.

Slices 11.2.1.EI–EK (common-epoch, Cap-2.4 provenance handoff, Cap-24 writer)
and their composition imports share ``CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA``
instead of per-slice post-merge repin loops.

Persisted Cap-2.1–2.3 ``repository_sha`` values remain bound at the merge that
introduced the Cap-24 writer until republished; handoff resolves them from
manifest or selection and checks ``AUTHORIZED_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS``.

Update ``CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA`` only on
dependency-ordered chain completion PRs.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.single_selected_future_policy_v1.constants_v1 import SELECTION_FILENAME

CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA = "8379a278517b23240ca1cdad02fe041b7d618874"
AUTHORIZED_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS = frozenset(
    {
        CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA,
        "e5396206530415b469fa345ec04322613c953c44",
    }
)
CAP24_PUBLISH_MANIFEST_FILENAME = "cap24_selection_state_publish_manifest_v1.json"
CAP24_RUNTIME_STATE_DIRNAME = "runtime_state"
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductive29PChainBaselineError(RuntimeError):
    """Fail-closed CURRENT_PRODUCTIVE 29P chain baseline violation."""


def resolve_cap24_persisted_repository_sha_v1(*, productivity_root: Path) -> str:
    """Resolve persisted repository_sha for Cap-2.4 provenance handoff (fail-closed)."""

    prod_root = Path(productivity_root)
    if not prod_root.exists():
        raise CurrentProductive29PChainBaselineError("CAP24_PRODUCTIVITY_ROOT_MISSING")

    manifest_path = prod_root / CAP24_PUBLISH_MANIFEST_FILENAME
    if manifest_path.is_file():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            sha = str(payload.get("repository_sha") or "").strip()
            if sha:
                return _assert_authorized_repository_sha_v1(sha)

    state_root = prod_root / CAP24_RUNTIME_STATE_DIRNAME
    if not state_root.is_dir():
        if (prod_root / "selection").is_dir():
            state_root = prod_root
        else:
            raise CurrentProductive29PChainBaselineError("CAP24_RUNTIME_STATE_LAYOUT_MISSING")

    sel_path = state_root / "selection" / SELECTION_FILENAME
    if not sel_path.is_file():
        raise CurrentProductive29PChainBaselineError("CAP24_SELECTION_ARTIFACT_MISSING")
    selection = json.loads(sel_path.read_text(encoding="utf-8"))
    if not isinstance(selection, dict):
        raise CurrentProductive29PChainBaselineError("CAP24_SELECTION_MALFORMED")
    sha = str(selection.get("repository_sha") or "").strip()
    if not sha:
        raise CurrentProductive29PChainBaselineError("CAP24_REPOSITORY_SHA_MISSING")
    return _assert_authorized_repository_sha_v1(sha)


def _assert_authorized_repository_sha_v1(repository_sha: str) -> str:
    sha = str(repository_sha or "").strip()
    if sha not in AUTHORIZED_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS:
        raise CurrentProductive29PChainBaselineError("CAP24_REPOSITORY_SHA_NOT_AUTHORIZED")
    return sha
