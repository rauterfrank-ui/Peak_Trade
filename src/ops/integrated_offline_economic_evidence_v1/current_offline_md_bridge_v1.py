"""CURRENT_OFFLINE_MD_BRIDGE_V1 — semantic lineage between CURRENT MD and offline dataset (B2)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    MD_BRIDGE_ARTIFACT,
    MD_BRIDGE_CONTRACT_ID,
    MD_BRIDGE_SCHEMA_ID,
    MD_BRIDGE_SCHEMA_VERSION,
    MD_BRIDGE_SEMANTIC_BINDING_KEYS,
    MD_BRIDGE_VERIFIER_ID,
    OFFLINE_DATASET_OWNER,
)
from src.ops.integrated_offline_economic_evidence_v1.domain_contracts_v1 import (
    load_json_object,
    safe_resolve_under_repo,
    sha256_file,
)

_SHA64 = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass
class CurrentOfflineMdBridgeVerificationResultV1:
    bridge_verified: bool
    blockers: list[str] = field(default_factory=list)
    unresolved_predicates: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bridge_verified": self.bridge_verified,
            "blockers": list(self.blockers),
            "unresolved_predicates": list(self.unresolved_predicates),
            "notes": list(self.notes),
            "verifier_id": MD_BRIDGE_VERIFIER_ID,
            "bridge_contract_id": MD_BRIDGE_CONTRACT_ID,
            "artifact_name": MD_BRIDGE_ARTIFACT,
        }


def _require_sha64(value: str, label: str) -> list[str]:
    if not _SHA64.match(str(value or "")):
        return [f"{label}_INVALID"]
    return []


def _compare_semantic_pair(
    *,
    key: str,
    current: Mapping[str, Any],
    dataset: Mapping[str, Any],
    blockers: list[str],
    unresolved: list[str],
) -> None:
    cur_val = current.get(key)
    ds_val = dataset.get(key)
    if cur_val is None or str(cur_val).strip() == "":
        unresolved.append(f"CURRENT:{key.upper()}_UNRESOLVED")
        return
    if ds_val is None or str(ds_val).strip() == "":
        unresolved.append(f"DATASET:{key.upper()}_UNRESOLVED")
        return
    if str(cur_val) != str(ds_val):
        blockers.append(f"MD_SEMANTIC_MISMATCH:{key.upper()}")


def _coverage_sufficient(
    *, required_start: str, required_end: str, ds_start: str, ds_end: str
) -> bool:
    return required_start >= ds_start and required_end <= ds_end


def verify_current_offline_md_bridge_v1(
    *,
    repo_root: Path | None = None,
    artifact_relpath: str | None = None,
    bridge_document: Mapping[str, Any] | None = None,
    expected_dataset_content_digest_sha256: str | None = None,
    expected_instrument_mapping_digest_sha256: str | None = None,
) -> CurrentOfflineMdBridgeVerificationResultV1:
    """Fail-closed semantic compatibility verifier; never claims byte identity."""
    blockers: list[str] = []
    unresolved: list[str] = []
    notes = ["B2_MD_BRIDGE_VERIFIER", f"VERIFIER_ID={MD_BRIDGE_VERIFIER_ID}"]

    doc: dict[str, Any] = {}
    if bridge_document is not None:
        doc = dict(bridge_document)
    elif repo_root is not None and artifact_relpath:
        root = repo_root.resolve()
        target = safe_resolve_under_repo(repo_root=root, relpath=artifact_relpath)
        if target is None:
            blockers.append("ARTIFACT_RELPATH_FORBIDDEN")
        else:
            loaded, load_blockers = load_json_object(target)
            blockers.extend(load_blockers)
            doc = loaded
            if not load_blockers:
                digest = sha256_file(target)
                notes.append(f"ARTIFACT_DIGEST={digest}")
    else:
        blockers.append("BRIDGE_DOCUMENT_MISSING")

    if doc:
        if doc.get("schema_id") != MD_BRIDGE_SCHEMA_ID:
            blockers.append("SCHEMA_ID_MISMATCH")
        if str(doc.get("schema_version") or "") != MD_BRIDGE_SCHEMA_VERSION:
            blockers.append("SCHEMA_VERSION_MISMATCH")
        if doc.get("authority_effect") != AUTHORITY_EFFECT_NONE:
            blockers.append("AUTHORITY_EFFECT_NOT_NONE")
        if doc.get("verifier_id") != MD_BRIDGE_VERIFIER_ID:
            blockers.append("VERIFIER_ID_MISMATCH")
        if doc.get("bridge_contract_id") != MD_BRIDGE_CONTRACT_ID:
            blockers.append("BRIDGE_CONTRACT_ID_MISMATCH")
        if doc.get("byte_identity_claimed") is True:
            blockers.append("FORBIDDEN_BYTE_IDENTITY_CLAIM")
        offline_owner = str(doc.get("offline_dataset_owner") or "")
        if offline_owner and offline_owner != OFFLINE_DATASET_OWNER:
            blockers.append("OFFLINE_DATASET_OWNER_MISMATCH")

        dataset_digest = str(doc.get("dataset_content_digest_sha256") or "")
        blockers.extend(_require_sha64(dataset_digest, "DATASET_CONTENT_DIGEST"))
        if expected_dataset_content_digest_sha256:
            if dataset_digest.lower() != expected_dataset_content_digest_sha256.lower():
                blockers.append("DATASET_CONTENT_DIGEST_MISMATCH")

        mapping_digest = str(doc.get("instrument_mapping_digest_sha256") or "")
        blockers.extend(_require_sha64(mapping_digest, "INSTRUMENT_MAPPING_DIGEST"))
        if expected_instrument_mapping_digest_sha256:
            if mapping_digest.lower() != expected_instrument_mapping_digest_sha256.lower():
                blockers.append("INSTRUMENT_MAPPING_DIGEST_MISMATCH")

        if not str(doc.get("dataset_version") or "").strip():
            blockers.append("DATASET_VERSION_MISSING")

        current = doc.get("current_offline_md_semantics_v1")
        dataset = doc.get("offline_dataset_semantics_v1")
        if not isinstance(current, Mapping):
            blockers.append("CURRENT_OFFLINE_MD_SEMANTICS_V1_MISSING")
            current = {}
        if not isinstance(dataset, Mapping):
            blockers.append("OFFLINE_DATASET_SEMANTICS_V1_MISSING")
            dataset = {}

        display_symbol = str(current.get("display_symbol") or "")
        ds_display = str(dataset.get("display_symbol") or "")
        canonical_id = str(current.get("canonical_instrument_id") or "")
        ds_canonical = str(dataset.get("canonical_instrument_id") or "")
        if (
            display_symbol
            and ds_display
            and display_symbol == ds_display
            and canonical_id != ds_canonical
        ):
            blockers.append("SAME_DISPLAY_SYMBOL_DIFFERENT_CANONICAL_INSTRUMENT")
        if canonical_id and ds_canonical and canonical_id != ds_canonical:
            blockers.append("CANONICAL_INSTRUMENT_MISMATCH")

        for key in MD_BRIDGE_SEMANTIC_BINDING_KEYS:
            _compare_semantic_pair(
                key=key,
                current=current,
                dataset=dataset,
                blockers=blockers,
                unresolved=unresolved,
            )

        coverage = doc.get("time_range_coverage_v1")
        if not isinstance(coverage, Mapping):
            blockers.append("TIME_RANGE_COVERAGE_V1_MISSING")
        else:
            req_start = str(coverage.get("required_start_time") or "")
            req_end = str(coverage.get("required_end_time") or "")
            ds_start = str(coverage.get("dataset_start_time") or "")
            ds_end = str(coverage.get("dataset_end_time") or "")
            if not all((req_start, req_end, ds_start, ds_end)):
                blockers.append("TIME_RANGE_COVERAGE_INCOMPLETE")
            elif not _coverage_sufficient(
                required_start=req_start,
                required_end=req_end,
                ds_start=ds_start,
                ds_end=ds_end,
            ):
                blockers.append("INSUFFICIENT_TIME_RANGE_COVERAGE")

        if doc.get("bridge_verified") is True:
            notes.append("IGNORED_SELF_ASSERTED_BRIDGE_VERIFIED_BOOLEAN")

    unique_blockers = sorted(set(blockers))
    unique_unresolved = sorted(set(unresolved))
    if unique_unresolved:
        unique_blockers.extend(f"UNRESOLVED:{u}" for u in unique_unresolved)
    bridge_verified = not unique_blockers
    return CurrentOfflineMdBridgeVerificationResultV1(
        bridge_verified=bridge_verified,
        blockers=sorted(set(unique_blockers)),
        unresolved_predicates=unique_unresolved,
        notes=notes,
    )
