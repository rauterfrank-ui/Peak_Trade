"""Canonical serialization, digests, and deterministic execution identity."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def canonical_json_dumps(payload: Mapping[str, Any]) -> str:
    return canonical_json_bytes(payload).decode("utf-8")


def sha256_hex(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_excluding_keys(payload: Mapping[str, Any], *, exclude: set[str]) -> str:
    body = {k: v for k, v in payload.items() if k not in exclude}
    return sha256_hex(body)


def build_execution_id_v1(
    *,
    repository_sha: str,
    preregistration_digest: str,
    candidate_domain_digest: str,
    hypothesis_contract_digest: str,
    split_contract_digest: str,
    robustness_contract_digest: str,
    input_evidence_manifest_digest: str,
) -> str:
    """Deterministic execution identity — no random / wallclock component."""
    material = {
        "candidate_domain_digest": candidate_domain_digest,
        "hypothesis_contract_digest": hypothesis_contract_digest,
        "input_evidence_manifest_digest": input_evidence_manifest_digest,
        "preregistration_digest": preregistration_digest,
        "repository_sha": repository_sha,
        "robustness_contract_digest": robustness_contract_digest,
        "split_contract_digest": split_contract_digest,
    }
    return "maxage_research_exec_" + sha256_hex(material)[:32]
