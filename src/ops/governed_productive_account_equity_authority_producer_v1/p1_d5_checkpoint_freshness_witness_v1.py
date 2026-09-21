"""P1 D5 checkpoint-bound observation freshness witness (offline).

Proves P1-bound interest-accrued GET observations lie under the ratified
checkpoint lineage and explicit capture-timestamp freshness contract.
Genesis-point window binding alone is insufficient. No GET. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_acquisition_contract_v1 import (
    FRESHNESS_EVIDENCE_STATUS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_liability_event_class_governance_and_ratified_query_class_set_v1 import (
    RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_surface_or_embedding_witness_qualification_v1 import (
    SELECTED_SURFACE_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_primary_proof_bound_interest_accrued_get_acquisition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CD_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_USDC_P1_PACK_ROOT,
)

CANONICAL_USDC_P1_PACK_RELPATH = f"{CANONICAL_USDC_P1_PACK_ROOT}/2026-09-20T233000Z"
CANONICAL_CD_PACK = CANONICAL_CD_PACK_RELPATH

WP_ID = "FULL_CORE_P1_FINAL_CLOSEOUT_PR1_OF_2_V1"
SCHEMA_CLASS = "P1_D5_CHECKPOINT_FRESHNESS_WITNESS_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_MAX_TRANSPORT_STALE_SECONDS = 120
_FRESHNESS_SEMANTICS = (
    "P1_EXPLICIT_CAPTURE_TIMESTAMPS_BOUND_TO_CHECKPOINT_LINEAGE_"
    "NOT_GENESIS_POINT_WINDOW_COMPLETENESS"
)


class P1D5CheckpointFreshnessWitnessError(ValueError):
    """Fail-closed P1 D5 checkpoint freshness witness violation."""


@dataclass(frozen=True)
class P1BoundObservationCaptureV1:
    pack_label: str
    request_surface: str
    request_utc: str
    response_utc: str
    d4_identity_digest: str
    d5_binding_id: str
    genesis_id: str
    http_status: str
    query: str
    payload_sha256: str
    observation_id: str


def _parse_iso_z(raw: str) -> datetime:
    text = str(raw or "").strip()
    if _ISO_Z.fullmatch(text) is None:
        raise P1D5CheckpointFreshnessWitnessError(f"TIMESTAMP_NOT_ISO_Z:{text}")
    body = text[:-1]
    if "." in body:
        parsed = datetime.strptime(body, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        parsed = datetime.strptime(body, "%Y-%m-%dT%H:%M:%S")
    return parsed.replace(tzinfo=timezone.utc)


def _observation_id_v1(
    *, request_surface: str, request_utc: str, query: str, d5_binding_id: str
) -> str:
    payload = f"{request_surface}|{request_utc}|{query}|{d5_binding_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise P1D5CheckpointFreshnessWitnessError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _capture_from_raw_http(
    *, pack_label: str, raw_http: Mapping[str, Any]
) -> P1BoundObservationCaptureV1:
    request_surface = str(raw_http.get("request_surface", ""))
    request_utc = str(raw_http.get("request_utc", ""))
    response_utc = str(raw_http.get("response_utc", ""))
    d4_digest = str(raw_http.get("d4_identity_digest", ""))
    d5_binding_id = str(raw_http.get("d5_binding_id", ""))
    genesis_id = str(raw_http.get("genesis_id", ""))
    http_status = str(raw_http.get("http_status", ""))
    query = str(raw_http.get("query", ""))
    payload_sha256 = str(raw_http.get("payload_sha256", ""))
    if not all(
        (
            request_surface,
            request_utc,
            response_utc,
            d4_digest,
            d5_binding_id,
            genesis_id,
            http_status,
            query,
            payload_sha256,
        )
    ):
        raise P1D5CheckpointFreshnessWitnessError(f"RAW_HTTP_INCOMPLETE:{pack_label}")
    obs_id = _observation_id_v1(
        request_surface=request_surface,
        request_utc=request_utc,
        query=query,
        d5_binding_id=d5_binding_id,
    )
    return P1BoundObservationCaptureV1(
        pack_label=pack_label,
        request_surface=request_surface,
        request_utc=request_utc,
        response_utc=response_utc,
        d4_identity_digest=d4_digest,
        d5_binding_id=d5_binding_id,
        genesis_id=genesis_id,
        http_status=http_status,
        query=query,
        payload_sha256=payload_sha256,
        observation_id=obs_id,
    )


def _validate_capture_against_checkpoint_v1(
    *,
    capture: P1BoundObservationCaptureV1,
    checkpoint_id: str,
    checkpoint_binding_id: str,
    checkpoint_observed_at: str,
    bound_identity_digest: str,
    claims_raw_persisted: bool,
    claims_raw_sha256: str,
) -> str | None:
    if capture.http_status != "200":
        return f"{capture.pack_label}_HTTP_NOT_200"
    if capture.request_surface != SELECTED_SURFACE_ID:
        return f"{capture.pack_label}_REQUEST_SURFACE_MISMATCH"
    if capture.d5_binding_id != checkpoint_binding_id:
        return f"{capture.pack_label}_D5_BINDING_ID_MISMATCH"
    if capture.d4_identity_digest != bound_identity_digest:
        return f"{capture.pack_label}_D4_DIGEST_MISMATCH"
    if not claims_raw_persisted or len(claims_raw_sha256) != 64:
        return f"{capture.pack_label}_RAW_PROVENANCE_INCOMPLETE"
    if claims_raw_sha256 != capture.payload_sha256:
        return f"{capture.pack_label}_RAW_SHA256_MISMATCH"
    req = _parse_iso_z(capture.request_utc)
    resp = _parse_iso_z(capture.response_utc)
    checkpoint_as_of = _parse_iso_z(checkpoint_observed_at)
    if req <= checkpoint_as_of:
        return f"{capture.pack_label}_OBSERVATION_NOT_AFTER_CHECKPOINT_AS_OF"
    transport_age = (resp - req).total_seconds()
    if transport_age < 0 or transport_age > _MAX_TRANSPORT_STALE_SECONDS:
        return f"{capture.pack_label}_TRANSPORT_TIMESTAMP_STALE_OR_INVERTED"
    if capture.genesis_id == "":
        return f"{capture.pack_label}_GENESIS_ID_MISSING"
    del checkpoint_id
    return None


def build_p1_d5_checkpoint_freshness_witness_adjudication_v1(
    *,
    repo_root: Path | str,
    traversal_pagination_proven: bool,
) -> dict[str, Any]:
    repo = Path(repo_root)
    if not traversal_pagination_proven:
        return {
            "layer": "CANONICAL_AUTHORITY",
            "WP_ID": WP_ID,
            "SCHEMA_CLASS": SCHEMA_CLASS,
            "P1_OBSERVATION_FRESHNESS_COMPLETENESS_PROVEN": FALSE_TOKEN,
            "P1_OBSERVATION_FRESHNESS_DETAIL": "PAGINATION_COMPLETE_REQUIRED_FOR_FRESHNESS",
            "FRESHNESS_MISSING_FACT": "PAGINATION_COMPLETE_REQUIRED",
            "CHECKPOINT_ID": "",
            "CHECKPOINT_BINDING_ID": "",
            "FRESHNESS_SEMANTICS": _FRESHNESS_SEMANTICS,
            "FRESHNESS_POLICY_STATUS": FRESHNESS_EVIDENCE_STATUS,
        }

    genesis_root = resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    if genesis_root is None:
        return _freshness_fail("D5_GENESIS_RUNTIME_STORE_ABSENT")

    d5 = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)
    if str(d5.event_completeness_from_window).lower() == TRUE_TOKEN:
        return _freshness_fail("D5_EVENT_COMPLETENESS_FROM_WINDOW_MUST_BE_FALSE")

    usdc_pack = repo / CANONICAL_USDC_P1_PACK_RELPATH
    cd_pack = repo / CANONICAL_CD_PACK
    usdc_raw_path = usdc_pack / "raw_http_capture_v1.json"
    cd_raw_path = cd_pack / "raw_http_capture_v1.json"
    if not usdc_raw_path.is_file() or not cd_raw_path.is_file():
        return _freshness_fail("SEALED_RAW_HTTP_CAPTURE_MISSING")

    usdc_claims = _load_json_object(usdc_pack / "claims.json")
    cd_claims = _load_json_object(cd_pack / "claims.json")
    usdc_capture = _capture_from_raw_http(
        pack_label="USDC_P1", raw_http=_load_json_object(usdc_raw_path)
    )
    cd_capture = _capture_from_raw_http(pack_label="CD", raw_http=_load_json_object(cd_raw_path))

    captures: Sequence[P1BoundObservationCaptureV1] = (cd_capture, usdc_capture)
    for capture in captures:
        err = _validate_capture_against_checkpoint_v1(
            capture=capture,
            checkpoint_id=d5.checkpoint_id,
            checkpoint_binding_id=d5.binding_id,
            checkpoint_observed_at=d5.observed_at_as_of,
            bound_identity_digest=d5.bound_account_identity_digest,
            claims_raw_persisted=str(
                (usdc_claims if capture.pack_label == "USDC_P1" else cd_claims).get(
                    "RAW_EVIDENCE_PERSISTED", ""
                )
            ).lower()
            == TRUE_TOKEN,
            claims_raw_sha256=str(
                (usdc_claims if capture.pack_label == "USDC_P1" else cd_claims).get(
                    "RAW_EVIDENCE_SHA256", ""
                )
            ),
        )
        if err is not None:
            return _freshness_fail(err)

    if SELECTED_SURFACE_ID not in RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET:
        return _freshness_fail("RATIFIED_QUERY_CLASS_SET_MISSING_P1_SURFACE")

    return {
        "layer": "CANONICAL_AUTHORITY",
        "WP_ID": WP_ID,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "P1_OBSERVATION_FRESHNESS_COMPLETENESS_PROVEN": TRUE_TOKEN,
        "P1_OBSERVATION_FRESHNESS_DETAIL": (
            "Sealed CD and USDC P1 interest-accrued observations bound to D5 "
            "checkpoint lineage with explicit request/response UTC timestamps; "
            "post-checkpoint acquisition; transport freshness within bound; "
            "not genesis-point window completeness"
        ),
        "FRESHNESS_MISSING_FACT": NONE_TOKEN,
        "CHECKPOINT_ID": d5.checkpoint_id,
        "CHECKPOINT_BINDING_ID": d5.binding_id,
        "CHECKPOINT_OBSERVED_AT_AS_OF": d5.observed_at_as_of,
        "FRESHNESS_SEMANTICS": _FRESHNESS_SEMANTICS,
        "FRESHNESS_POLICY_STATUS": FRESHNESS_EVIDENCE_STATUS,
        "BOUND_OBSERVATION_IDS": [c.observation_id for c in captures],
        "RATIFIED_QUERY_CLASS": SELECTED_SURFACE_ID,
        "EVENT_COMPLETENESS_FROM_WINDOW": FALSE_TOKEN,
    }


def _freshness_fail(detail: str) -> dict[str, Any]:
    return {
        "layer": "CANONICAL_AUTHORITY",
        "WP_ID": WP_ID,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "P1_OBSERVATION_FRESHNESS_COMPLETENESS_PROVEN": FALSE_TOKEN,
        "P1_OBSERVATION_FRESHNESS_DETAIL": detail,
        "FRESHNESS_MISSING_FACT": detail,
        "CHECKPOINT_ID": "",
        "CHECKPOINT_BINDING_ID": "",
        "FRESHNESS_SEMANTICS": _FRESHNESS_SEMANTICS,
        "FRESHNESS_POLICY_STATUS": FRESHNESS_EVIDENCE_STATUS,
    }


__all__ = [
    "AUTHORITY_EFFECT",
    "CANONICAL_CD_PACK",
    "CANONICAL_USDC_P1_PACK_RELPATH",
    "CONTRACT_VERSION",
    "P1BoundObservationCaptureV1",
    "P1D5CheckpointFreshnessWitnessError",
    "SCHEMA_CLASS",
    "WP_ID",
    "build_p1_d5_checkpoint_freshness_witness_adjudication_v1",
]
