"""DDO durable-evidence path resolution primitive v0.

Resolves a ledger path only from caller-supplied authoritative inputs.
Does not invent cwd, home, repo-root, or temp-dir fallbacks. Does not
import trading, ops, live, or ExecutionEnvironment (owner is reused by
token membership only). Productive host consumption is owned by the
observation-host binding module, not by this primitive.

TESTNET_EFFECT and CANARY_EFFECT remain NONE. Mentioning environment
member tokens here does not confer Testnet or Canary authority.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    CANARY_EFFECT,
    LIVE_EFFECT,
    TESTNET_EFFECT,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoPathResolutionError
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import LEDGER_FILENAME_DEFAULT

assert TESTNET_EFFECT == "NONE"
assert CANARY_EFFECT == "NONE"
assert LIVE_EFFECT == "NONE"

LOGICAL_CONFIG_KEY_DDO_DURABLE_EVIDENCE_RUNTIME_STATE_ROOT: Final[str] = (
    "ddo.durable_evidence.runtime_state_root"
)
DDO_EVIDENCE_ENVIRONMENT_OWNER: Final[str] = "EXISTING_GOVERNANCE_EXECUTION_ENVIRONMENT"
DDO_EVIDENCE_ACCOUNT_OWNER: Final[str] = "EXISTING_CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY"
DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN: Final[str] = "canonical_trading_path"
DDO_EVIDENCE_ENVIRONMENT_TOKENS: Final[frozenset[str]] = frozenset(
    {"dev", "shadow", "testnet", "prod"}
)
_ACCOUNT_SCOPE_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9._-]+$")
_FILENAME_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9._-]+$")


def resolve_ddo_durable_evidence_path_v1(
    *,
    runtime_state_root: str | Path,
    environment: str,
    account_scope: str,
    system_scope: str,
    filename: str | None = None,
) -> Path:
    """Derive the DDO ledger path from explicit scopes. Fail closed if any required input is missing.

    Productive hosts may call this only through the observation-host binding
    after the four scope inputs are already bound. This primitive still does
    not invent fallbacks or bind a host itself.
    """
    if runtime_state_root is None or str(runtime_state_root).strip() == "":
        raise DdoPathResolutionError("RUNTIME_STATE_ROOT_REQUIRED")
    if environment is None or str(environment).strip() == "":
        raise DdoPathResolutionError("ENVIRONMENT_SCOPE_REQUIRED")
    if account_scope is None or str(account_scope).strip() == "":
        raise DdoPathResolutionError("ACCOUNT_SCOPE_REQUIRED")
    if system_scope is None or str(system_scope).strip() == "":
        raise DdoPathResolutionError("SYSTEM_SCOPE_REQUIRED")

    root = Path(runtime_state_root)
    if not root.is_absolute():
        raise DdoPathResolutionError("RUNTIME_STATE_ROOT_MUST_BE_ABSOLUTE")
    if ".." in root.parts:
        raise DdoPathResolutionError("RUNTIME_STATE_ROOT_PATH_TRAVERSAL")

    env = str(environment).strip()
    if env not in DDO_EVIDENCE_ENVIRONMENT_TOKENS:
        raise DdoPathResolutionError("ENVIRONMENT_SCOPE_UNKNOWN")

    account = str(account_scope).strip()
    if account in {".", ".."} or not _ACCOUNT_SCOPE_RE.fullmatch(account):
        raise DdoPathResolutionError("ACCOUNT_SCOPE_INVALID")

    system = str(system_scope).strip()
    if system != DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN:
        raise DdoPathResolutionError("SYSTEM_SCOPE_INVALID")

    chosen_filename = LEDGER_FILENAME_DEFAULT if filename is None else str(filename).strip()
    if not chosen_filename or not _FILENAME_RE.fullmatch(chosen_filename):
        raise DdoPathResolutionError("LEDGER_FILENAME_INVALID")
    if chosen_filename in {".", ".."}:
        raise DdoPathResolutionError("LEDGER_FILENAME_INVALID")

    return root / "ddo" / env / account / system / chosen_filename
