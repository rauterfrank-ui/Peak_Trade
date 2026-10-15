"""Owner grant identity (non-secret binding digest). No network."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.owner_scoped_get_budget_enforcement_v1.constants_v1 import HTTP_METHOD_GET
from src.ops.owner_scoped_get_budget_enforcement_v1.errors_v1 import OwnerScopedGetBudgetError


@dataclass(frozen=True)
class OwnerScopedGetBudgetGrantBindingV1:
    """Closed-world binding for one bounded Owner GET operation."""

    owner_go: str
    work_package_id: str
    origin_main_sha: str
    cumulative_request_budget: int
    authorized_host: str
    http_method_allowlist: tuple[str, ...] = (HTTP_METHOD_GET,)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authorized_host": str(self.authorized_host or "").strip(),
            "cumulative_request_budget": int(self.cumulative_request_budget),
            "http_method_allowlist": sorted(
                {str(m or "").upper() for m in self.http_method_allowlist if str(m or "").strip()}
            ),
            "origin_main_sha": str(self.origin_main_sha or "").strip().lower(),
            "owner_go": str(self.owner_go or "").strip(),
            "work_package_id": str(self.work_package_id or "").strip(),
        }


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_owner_grant_identity_digest_v1(binding: OwnerScopedGetBudgetGrantBindingV1) -> str:
    canonical = binding.to_canonical_dict()
    if canonical["cumulative_request_budget"] < 1:
        raise OwnerScopedGetBudgetError("CUMULATIVE_REQUEST_BUDGET_INVALID")
    if not canonical["owner_go"] or not canonical["work_package_id"]:
        raise OwnerScopedGetBudgetError("GRANT_BINDING_INCOMPLETE")
    if len(canonical["origin_main_sha"]) != 40:
        raise OwnerScopedGetBudgetError("ORIGIN_MAIN_SHA_INVALID")
    if HTTP_METHOD_GET not in canonical["http_method_allowlist"]:
        raise OwnerScopedGetBudgetError("GET_ONLY_ALLOWLIST_REQUIRED")
    if any(m != HTTP_METHOD_GET for m in canonical["http_method_allowlist"]):
        raise OwnerScopedGetBudgetError("NON_GET_METHOD_FORBIDDEN_IN_BINDING")
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def owner_grant_id_from_identity_v1(identity_digest: str) -> str:
    token = str(identity_digest or "").strip().lower()
    if len(token) != 64:
        raise OwnerScopedGetBudgetError("GRANT_IDENTITY_DIGEST_INVALID")
    return token
