"""EG-I82-JOIN U-I82-R24 — durable end-to-end live-owner graph attestation.

Traverses the six registered named-lane live-owner parse/join contracts and
attests all 42 required Plane×Lane edges as one fail-closed graph bound to a
single Package-N SHA256 identity. This is not a static PROVEN-flag aggregator.

Does not activate Cap 7.2 or src.execution, and does not persist, migrate,
backfill, or rewrite historical CSV/registry records.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from src.analytics.explorer import parse_experiment_summary_with_identity_join_v1
from src.analytics.i65_explorer_named_lane_identity_join_v1 import (
    I65ExplorerNamedLaneIdentityJoinError,
    is_i65_named_lane_identity_join_registered,
)
from src.experiments.cross_lane_identity_join_v1 import (
    CONTRACT_VERSION,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    JOIN_PLANES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PLANE_VALUE_FIELDS,
    PlanePresence,
    RUNTIME_AUTHORITY_IMPACT,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    CrossLaneIdentityJoinV1,
    is_package_n_sha256_canonical_id,
)
from src.experiments.eg_i82_join_verifier_v1 import (
    EgI82JoinVerifierError,
    NAMED_JOIN_LANES,
    verify_eg_i82_cross_lane_join_v1,
)
from src.experiments.experiment_identity_manifest_v1 import ARTIFACT_FILENAME
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import LineageRef
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    ExperimentLineageRefProducerError,
    build_experiment_lineage_ref_from_manifest,
)
from src.governance.promotion_loop.i16_lineage_remaining_planes_live_join_v1 import (
    I16LineageRemainingPlanesLiveJoinError,
    is_i16_lineage_remaining_planes_join_registered,
    join_i16_lineage_remaining_planes_v1,
)
from src.ingress.capsules.evidence_capsule import parse_evidence_capsule_with_identity_join_v1
from src.ingress.capsules.i56_ingress_named_lane_identity_join_v1 import (
    I56IngressNamedLaneIdentityJoinError,
    is_i56_named_lane_identity_join_registered,
)
from src.levelup.i52_levelup_named_lane_identity_join_v1 import (
    I52LevelUpNamedLaneIdentityJoinError,
    is_i52_named_lane_identity_join_registered,
)
from src.levelup.v0_models import parse_levelup_manifest_with_identity_join_v1
from src.live_eval.i61_live_eval_named_lane_identity_join_v1 import (
    I61LiveEvalNamedLaneIdentityJoinError,
    is_i61_named_lane_identity_join_registered,
)
from src.live_eval.live_session_eval import parse_live_session_metrics_with_identity_join_v1
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_named_lane_identity_join_v1 import (
    I17PaperShadowNamedLaneIdentityJoinError,
    is_i17_named_lane_identity_join_registered,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    PreregistrationContractError,
    parse_preregistration_contract_with_identity_join_v1,
)

CONTRACT_ID = "eg_i82_end_to_end_live_owner_graph_attestation_v1"
EG_I82_END_TO_END_LIVE_OWNER_GRAPH_ATTESTATION_REGISTERED = True
EXPECTED_EDGE_COUNT = 42
EXPECTED_LANE_COUNT = 7
EXPECTED_OWNER_COUNT = 6

REAL_LIVE_OWNER_PATHS: Mapping[str, str] = MappingProxyType(
    {
        "I16": "src/governance/promotion_loop/experiment_lineage_ref_producer_v1.py",
        "I17": (
            "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/"
            "preregistration_contract_v1.py"
        ),
        "I52": "src/levelup/v0_models.py",
        "I56": "src/ingress/capsules/evidence_capsule.py",
        "I61": "src/live_eval/live_session_eval.py",
        "I65": "src/analytics/explorer.py",
    }
)

REQUIRED_GRAPH_EDGE_IDS: tuple[str, ...] = tuple(
    f"{lane}x{plane}" for lane in NAMED_JOIN_LANES for plane in JOIN_PLANES
)

_REGISTRATION_CHECKERS: Mapping[str, Any] = MappingProxyType(
    {
        "I16": is_i16_lineage_remaining_planes_join_registered,
        "I17": is_i17_named_lane_identity_join_registered,
        "I52": is_i52_named_lane_identity_join_registered,
        "I56": is_i56_named_lane_identity_join_registered,
        "I61": is_i61_named_lane_identity_join_registered,
        "I65": is_i65_named_lane_identity_join_registered,
    }
)

_LANE_ENVELOPE_KEYS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "I16": frozenset(
            {"manifest", "artifact_path", "run_id", "campaign_id", "session_id", "ref"}
        ),
        "I17": frozenset(
            {
                "live",
                "experiment_identity_id",
                "run_id",
                "legacy_alias_md5_12",
                "content_sha256",
                "historical_provenance",
            }
        ),
        "I52": frozenset(
            {
                "live",
                "experiment_identity_id",
                "run_id",
                "campaign_id",
                "session_id",
                "legacy_alias_md5_12",
                "content_sha256",
                "evidence_ref",
                "historical_provenance",
            }
        ),
        "I56": frozenset(
            {
                "live",
                "experiment_identity_id",
                "campaign_id",
                "session_id",
                "legacy_alias_md5_12",
                "content_sha256",
                "evidence_ref",
                "historical_provenance",
            }
        ),
        "I61": frozenset(
            {
                "live",
                "experiment_identity_id",
                "run_id",
                "campaign_id",
                "session_id",
                "session_dir",
                "legacy_alias_md5_12",
                "content_sha256",
                "evidence_ref",
                "historical_provenance",
            }
        ),
        "I65": frozenset(
            {
                "live",
                "experiment_identity_id",
                "campaign_id",
                "session_id",
                "legacy_alias_md5_12",
                "content_sha256",
                "evidence_ref",
                "historical_provenance",
            }
        ),
    }
)

_NONCANONICAL_IDENTITY_KEYS = frozenset(
    {
        "run_id",
        "experiment_id",
        "campaign_id",
        "session_id",
        "evidence_id",
        "evidence_ref",
        "alias",
        "legacy_alias_md5_12",
        "legacy_experiment_id",
        "package_n_sha256",
        "canonical_id",
        "canonical_identity_id",
        "identity_id",
        "ref_id",
        "content_sha256",
    }
)
_CLASSIFIED_PREFIXES = (
    "implicit absence rejected",
    "noncanonical ID substitution rejected",
    "conflicting identity rejected",
    "cross-lane substitution rejected",
    "cross-plane substitution rejected",
    "malformed plane data rejected",
    "ambiguous join rejected",
    "missing required edge rejected",
    "duplicate/conflicting edge registration rejected",
    "unexpected extra edge rejected",
    "missing owner registration rejected",
    "static join record rejected",
)


class EgI82EndToEndLiveOwnerGraphAttestationError(ValueError):
    """Fail-closed EG-I82 end-to-end live-owner graph attestation error."""


def _reject(message: str) -> None:
    raise EgI82EndToEndLiveOwnerGraphAttestationError(message)


def is_eg_i82_end_to_end_live_owner_graph_attestation_registered() -> bool:
    """True iff the durable live-owner graph attestation surface is registered."""
    return EG_I82_END_TO_END_LIVE_OWNER_GRAPH_ATTESTATION_REGISTERED is True


def _freeze_mapping(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    frozen: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, Mapping):
            frozen[str(key)] = _freeze_mapping(value)
        elif isinstance(value, list):
            frozen[str(key)] = tuple(
                _freeze_mapping(item) if isinstance(item, Mapping) else copy.deepcopy(item)
                for item in value
            )
        else:
            frozen[str(key)] = copy.deepcopy(value)
    return MappingProxyType(frozen)


def _snapshot(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _snapshot(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_snapshot(item) for item in value]
    if isinstance(value, LineageRef):
        return {
            "ref_type": str(value.ref_type),
            "ref_id": value.ref_id,
            "digest": value.digest,
            "artifact_path": value.artifact_path,
            "relation": str(value.relation),
            "owner_domain": value.owner_domain,
        }
    return copy.deepcopy(value)


def _raise_from_live(exc: BaseException, *, lane: str) -> None:
    if isinstance(exc, EgI82EndToEndLiveOwnerGraphAttestationError):
        raise exc
    message = str(exc)
    lowered = message.lower()
    for prefix in _CLASSIFIED_PREFIXES:
        if lowered.startswith(prefix.lower()) or prefix.lower() in lowered:
            _reject(message)
    if "ambiguous" in lowered:
        _reject(f"ambiguous join rejected: named lane {lane}: {exc}")
    for other in NAMED_JOIN_LANES:
        if other != lane and other in message and ("extra" in lowered or "forbidden" in lowered):
            _reject(f"cross-lane substitution rejected: named lane {lane}: {exc}")
    if (
        "uuid" in lowered
        or "md5" in lowered
        or "package-n" in lowered
        or "run_id" in lowered
        or "experiment_id" in lowered
    ):
        _reject(f"noncanonical ID substitution rejected: named lane {lane}: {exc}")
    if "conflict" in lowered:
        _reject(f"conflicting identity rejected: named lane {lane}: {exc}")
    if "cross-lane" in lowered:
        _reject(f"cross-lane substitution rejected: named lane {lane}: {exc}")
    if "cross-plane" in lowered:
        _reject(f"cross-plane substitution rejected: named lane {lane}: {exc}")
    _reject(f"malformed plane data rejected: named lane {lane}: {exc}")


def _require_owner_mapping(raw: object, *, lane: str) -> Mapping[str, Any]:
    if raw is None:
        _reject(f"implicit absence rejected: named lane {lane} is missing")
    if isinstance(raw, (list, tuple)):
        _reject(f"ambiguous join rejected: named lane {lane} has multiple Package-N assignments")
    if isinstance(raw, CrossLaneIdentityJoinV1):
        _reject(f"static join record rejected: named lane {lane} is not a live owner payload")
    if not isinstance(raw, Mapping):
        _reject(f"malformed plane data rejected: named lane {lane} is not an object")
    extra = sorted(str(key) for key in raw.keys() if str(key) not in _LANE_ENVELOPE_KEYS[lane])
    if extra:
        if extra[0] in NAMED_JOIN_LANES:
            _reject(f"cross-lane substitution rejected: named lane {lane} contains {extra[0]}")
        if extra[0] in {"plane_presence", "join_key"}:
            _reject(f"cross-plane substitution rejected: named lane {lane} contains {extra[0]}")
        if extra[0] in _NONCANONICAL_IDENTITY_KEYS:
            _reject(f"noncanonical ID substitution rejected: named lane {lane} uses {extra[0]}")
        _reject(f"malformed plane data rejected: named lane {lane} unknown field {extra[0]}")
    looks_static = (
        "plane_presence" in raw
        and "experiment_identity_id" in raw
        and "manifest" not in raw
        and "live" not in raw
    )
    if looks_static:
        _reject(f"static join record rejected: named lane {lane} is not a live owner payload")
    return raw


def _optional_sidecar(payload: Mapping[str, Any], key: str) -> str | None:
    if key not in payload:
        return None
    value = payload[key]
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _reject(f"malformed plane data rejected: sidecar {key} is invalid")
    return value


def _require_identity_sidecar(payload: Mapping[str, Any], *, lane: str) -> str:
    if "experiment_identity_id" not in payload or payload.get("experiment_identity_id") is None:
        _reject(f"implicit absence rejected: named lane {lane} IDENTITY is missing")
    identity = payload.get("experiment_identity_id")
    if not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: named lane "
            f"{lane} IDENTITY is not Package-N SHA256"
        )
    return str(identity)


def _require_live_payload(payload: Mapping[str, Any], *, lane: str) -> Mapping[str, Any]:
    if "live" not in payload:
        _reject(f"implicit absence rejected: named lane {lane} live payload is missing")
    live = payload["live"]
    if live is None:
        _reject(f"implicit absence rejected: named lane {lane} live payload is missing")
    if isinstance(live, (list, tuple)):
        _reject(f"ambiguous join rejected: named lane {lane} live payload has multiple assignments")
    if not isinstance(live, Mapping):
        _reject(f"malformed plane data rejected: named lane {lane} live payload is not an object")
    return live


def _require_registrations() -> None:
    for lane, checker in _REGISTRATION_CHECKERS.items():
        if checker() is not True:
            _reject(f"missing owner registration rejected: {lane}")


def _traverse_i16(payload: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    if "manifest" not in payload or payload.get("manifest") is None:
        _reject("implicit absence rejected: named lane I16 manifest is missing")
    manifest = payload["manifest"]
    if not isinstance(manifest, Mapping):
        _reject("malformed plane data rejected: named lane I16 manifest is not an object")
    artifact_path = payload.get("artifact_path", ARTIFACT_FILENAME)
    if not isinstance(artifact_path, str) or not artifact_path.strip():
        _reject("malformed plane data rejected: named lane I16 artifact_path is invalid")
    run_id = _optional_sidecar(payload, "run_id")
    campaign_id = _optional_sidecar(payload, "campaign_id")
    session_id = _optional_sidecar(payload, "session_id")
    ref_raw = payload.get("ref")
    try:
        if ref_raw is None:
            ref = build_experiment_lineage_ref_from_manifest(
                manifest,
                artifact_path=artifact_path,
                run_id=run_id,
                campaign_id=campaign_id,
                session_id=session_id,
            )
        elif not isinstance(ref_raw, LineageRef):
            _reject("malformed plane data rejected: named lane I16 ref is not a LineageRef")
            raise AssertionError("unreachable")
        else:
            ref = ref_raw
        return join_i16_lineage_remaining_planes_v1(
            manifest,
            ref=ref,
            artifact_path=artifact_path,
            run_id=run_id,
            campaign_id=campaign_id,
            session_id=session_id,
        )
    except (
        I16LineageRemainingPlanesLiveJoinError,
        ExperimentLineageRefProducerError,
        EgI82EndToEndLiveOwnerGraphAttestationError,
    ) as exc:
        _raise_from_live(exc, lane="I16")
        raise AssertionError("unreachable") from exc


def _traverse_i17(payload: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    live = _require_live_payload(payload, lane="I17")
    identity = _require_identity_sidecar(payload, lane="I17")
    try:
        result = parse_preregistration_contract_with_identity_join_v1(
            live,
            experiment_identity_id=identity,
            run_id=_optional_sidecar(payload, "run_id"),
            legacy_alias_md5_12=_optional_sidecar(payload, "legacy_alias_md5_12"),
            content_sha256=_optional_sidecar(payload, "content_sha256"),
            historical_provenance=payload.get("historical_provenance"),
        )
        return result.join
    except (
        I17PaperShadowNamedLaneIdentityJoinError,
        PreregistrationContractError,
        TypeError,
        ValueError,
        EgI82EndToEndLiveOwnerGraphAttestationError,
    ) as exc:
        _raise_from_live(exc, lane="I17")
        raise AssertionError("unreachable") from exc


def _traverse_i52(payload: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    live = _require_live_payload(payload, lane="I52")
    identity = _require_identity_sidecar(payload, lane="I52")
    try:
        result = parse_levelup_manifest_with_identity_join_v1(
            live,
            experiment_identity_id=identity,
            run_id=_optional_sidecar(payload, "run_id"),
            campaign_id=_optional_sidecar(payload, "campaign_id"),
            session_id=_optional_sidecar(payload, "session_id"),
            legacy_alias_md5_12=_optional_sidecar(payload, "legacy_alias_md5_12"),
            content_sha256=_optional_sidecar(payload, "content_sha256"),
            evidence_ref=_optional_sidecar(payload, "evidence_ref"),
            historical_provenance=payload.get("historical_provenance"),
        )
        return result.join
    except (
        I52LevelUpNamedLaneIdentityJoinError,
        TypeError,
        ValueError,
        EgI82EndToEndLiveOwnerGraphAttestationError,
    ) as exc:
        _raise_from_live(exc, lane="I52")
        raise AssertionError("unreachable") from exc


def _traverse_i56(payload: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    live = _require_live_payload(payload, lane="I56")
    identity = _require_identity_sidecar(payload, lane="I56")
    if "run_id" in payload:
        _reject("noncanonical ID substitution rejected: named lane I56 uses run_id")
    try:
        result = parse_evidence_capsule_with_identity_join_v1(
            live,
            experiment_identity_id=identity,
            campaign_id=_optional_sidecar(payload, "campaign_id"),
            session_id=_optional_sidecar(payload, "session_id"),
            legacy_alias_md5_12=_optional_sidecar(payload, "legacy_alias_md5_12"),
            content_sha256=_optional_sidecar(payload, "content_sha256"),
            evidence_ref=_optional_sidecar(payload, "evidence_ref"),
            historical_provenance=payload.get("historical_provenance"),
        )
        return result.join
    except (
        I56IngressNamedLaneIdentityJoinError,
        TypeError,
        ValueError,
        EgI82EndToEndLiveOwnerGraphAttestationError,
    ) as exc:
        _raise_from_live(exc, lane="I56")
        raise AssertionError("unreachable") from exc


def _traverse_i61(payload: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    live = _require_live_payload(payload, lane="I61")
    identity = _require_identity_sidecar(payload, lane="I61")
    try:
        result = parse_live_session_metrics_with_identity_join_v1(
            live,
            experiment_identity_id=identity,
            run_id=_optional_sidecar(payload, "run_id"),
            campaign_id=_optional_sidecar(payload, "campaign_id"),
            session_id=_optional_sidecar(payload, "session_id"),
            session_dir=_optional_sidecar(payload, "session_dir"),
            legacy_alias_md5_12=_optional_sidecar(payload, "legacy_alias_md5_12"),
            content_sha256=_optional_sidecar(payload, "content_sha256"),
            evidence_ref=_optional_sidecar(payload, "evidence_ref"),
            historical_provenance=payload.get("historical_provenance"),
        )
        return result.join
    except (
        I61LiveEvalNamedLaneIdentityJoinError,
        TypeError,
        ValueError,
        EgI82EndToEndLiveOwnerGraphAttestationError,
    ) as exc:
        _raise_from_live(exc, lane="I61")
        raise AssertionError("unreachable") from exc


def _traverse_i65(payload: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    live = _require_live_payload(payload, lane="I65")
    identity = _require_identity_sidecar(payload, lane="I65")
    if "run_id" in payload:
        _reject("noncanonical ID substitution rejected: named lane I65 uses run_id")
    try:
        result = parse_experiment_summary_with_identity_join_v1(
            live,
            experiment_identity_id=identity,
            campaign_id=_optional_sidecar(payload, "campaign_id"),
            session_id=_optional_sidecar(payload, "session_id"),
            legacy_alias_md5_12=_optional_sidecar(payload, "legacy_alias_md5_12"),
            content_sha256=_optional_sidecar(payload, "content_sha256"),
            evidence_ref=_optional_sidecar(payload, "evidence_ref"),
            historical_provenance=payload.get("historical_provenance"),
        )
        return result.join
    except (
        I65ExplorerNamedLaneIdentityJoinError,
        TypeError,
        ValueError,
        EgI82EndToEndLiveOwnerGraphAttestationError,
    ) as exc:
        _raise_from_live(exc, lane="I65")
        raise AssertionError("unreachable") from exc


_TRAVERSERS: Mapping[str, Any] = MappingProxyType(
    {
        "I16": _traverse_i16,
        "I17": _traverse_i17,
        "I52": _traverse_i52,
        "I56": _traverse_i56,
        "I61": _traverse_i61,
        "I65": _traverse_i65,
    }
)


@dataclass(frozen=True)
class EgI82GraphEdgeAttestationV1:
    edge_id: str
    lane: str
    plane: str
    presence: str
    canonical_join_key: str
    proven: bool

    def to_canonical_mapping(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "lane": self.lane,
            "plane": self.plane,
            "presence": self.presence,
            "canonical_join_key": self.canonical_join_key,
            "proven": self.proven,
        }


def require_eg_i82_complete_live_edge_matrix_v1(
    edges: Sequence[Mapping[str, Any]],
    *,
    package_n_sha256: str,
) -> tuple[EgI82GraphEdgeAttestationV1, ...]:
    """Fail-closed exact 42-edge matrix. Extra edges are never part of the canonical graph."""
    if not is_package_n_sha256_canonical_id(package_n_sha256):
        _reject("noncanonical ID substitution rejected: graph join key is not Package-N SHA256")
    if not isinstance(edges, Sequence) or isinstance(edges, (str, bytes)):
        _reject("malformed plane data rejected: edge matrix is not a sequence")

    seen: dict[str, Mapping[str, Any]] = {}
    for item in edges:
        if not isinstance(item, Mapping):
            _reject("malformed plane data rejected: edge entry is not an object")
        lane = item.get("lane")
        plane = item.get("plane")
        edge_id = item.get("edge_id")
        if edge_id is None and isinstance(lane, str) and isinstance(plane, str):
            edge_id = f"{lane}x{plane}"
        if not isinstance(edge_id, str) or not edge_id.strip():
            _reject("malformed plane data rejected: edge_id missing")
        if edge_id in seen:
            _reject(f"duplicate/conflicting edge registration rejected: {edge_id}")
        if edge_id not in REQUIRED_GRAPH_EDGE_IDS:
            _reject(
                f"unexpected extra edge rejected: {edge_id} is not part of the canonical 42-edge graph"
            )
        parts = edge_id.split("x", 1)
        if len(parts) != 2:
            _reject(f"malformed plane data rejected: edge_id {edge_id}")
        derived_lane, derived_plane = parts
        if lane is None:
            lane = derived_lane
        if plane is None:
            plane = derived_plane
        if lane != derived_lane or plane != derived_plane:
            _reject(f"malformed plane data rejected: edge {edge_id} lane/plane mismatch")
        if lane not in NAMED_JOIN_LANES:
            _reject(
                f"unexpected extra edge rejected: {edge_id} is not part of the canonical 42-edge graph"
            )
        if plane not in JOIN_PLANES:
            _reject(
                f"unexpected extra edge rejected: {edge_id} is not part of the canonical 42-edge graph"
            )
        presence = item.get("presence")
        if presence not in (
            PlanePresence.PRESENT.value,
            PlanePresence.ABSENT_DECLARED.value,
        ):
            _reject(f"implicit absence rejected: {edge_id} presence is not declared")
        join_key = item.get("canonical_join_key", package_n_sha256)
        if join_key != package_n_sha256:
            _reject(f"conflicting identity rejected: {edge_id} join key disagrees")
        if not is_package_n_sha256_canonical_id(join_key):
            _reject(f"noncanonical ID substitution rejected: {edge_id} join key")
        seen[edge_id] = item

    missing = [edge_id for edge_id in REQUIRED_GRAPH_EDGE_IDS if edge_id not in seen]
    if missing:
        _reject(f"missing required edge rejected: {missing[0]}")

    attested: list[EgI82GraphEdgeAttestationV1] = []
    for edge_id in REQUIRED_GRAPH_EDGE_IDS:
        item = seen[edge_id]
        lane, plane = edge_id.split("x", 1)
        attested.append(
            EgI82GraphEdgeAttestationV1(
                edge_id=edge_id,
                lane=str(item.get("lane", lane)),
                plane=str(item.get("plane", plane)),
                presence=str(item["presence"]),
                canonical_join_key=package_n_sha256,
                proven=True,
            )
        )
    return tuple(attested)


def _edges_from_live_records(
    records: Mapping[str, CrossLaneIdentityJoinV1],
    *,
    package_n_sha256: str,
) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for lane in NAMED_JOIN_LANES:
        record = records[lane]
        presence_map = record.plane_presence
        identity = record.experiment_identity_id
        if identity != package_n_sha256:
            _reject(f"conflicting identity rejected: named lane {lane} IDENTITY disagrees")
        if presence_map.get("IDENTITY") != PlanePresence.PRESENT.value:
            _reject(f"missing required edge rejected: {lane}xIDENTITY must be PRESENT")
        for plane in JOIN_PLANES:
            if plane not in presence_map:
                _reject(f"missing required edge rejected: {lane}x{plane}")
            presence = presence_map[plane]
            if presence not in (
                PlanePresence.PRESENT.value,
                PlanePresence.ABSENT_DECLARED.value,
            ):
                _reject(f"implicit absence rejected: {lane}x{plane}")
            if presence == PlanePresence.PRESENT.value:
                value = getattr(record, PLANE_VALUE_FIELDS[plane])
                if value is None:
                    _reject(f"implicit absence rejected: {lane}x{plane} PRESENT without value")
            edges.append(
                {
                    "edge_id": f"{lane}x{plane}",
                    "lane": lane,
                    "plane": plane,
                    "presence": presence,
                    "canonical_join_key": package_n_sha256,
                }
            )
    return edges


@dataclass(frozen=True)
class EgI82EndToEndLiveOwnerGraphAttestationV1:
    schema_version: str
    contract_version: str
    contract_id: str
    attestation_registered: bool
    package_n_sha256: str
    live_owner_paths: Mapping[str, str]
    named_lanes: tuple[str, ...]
    expected_edge_count: int
    edges_evaluated: int
    edges_proven: int
    edges_disproven: int
    edges_not_proven: int
    edges_not_applicable: int
    all_required_edges_proven: bool
    static_flag_aggregation_only: bool
    full_graph_traversal: bool
    end_to_end_join_graph_proven: bool
    eg_i82_join_closure_proven: bool
    eg_i82_join_status: str
    edges: tuple[EgI82GraphEdgeAttestationV1, ...]
    lane_identity_presence: Mapping[str, str]
    safety: Mapping[str, Any]

    def to_canonical_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
            "contract_id": self.contract_id,
            "attestation_registered": self.attestation_registered,
            "package_n_sha256": self.package_n_sha256,
            "live_owner_paths": {lane: REAL_LIVE_OWNER_PATHS[lane] for lane in NAMED_JOIN_LANES},
            "named_lanes": list(self.named_lanes),
            "expected_edge_count": self.expected_edge_count,
            "edges_evaluated": self.edges_evaluated,
            "edges_proven": self.edges_proven,
            "edges_disproven": self.edges_disproven,
            "edges_not_proven": self.edges_not_proven,
            "edges_not_applicable": self.edges_not_applicable,
            "all_required_edges_proven": self.all_required_edges_proven,
            "static_flag_aggregation_only": self.static_flag_aggregation_only,
            "full_graph_traversal": self.full_graph_traversal,
            "end_to_end_join_graph_proven": self.end_to_end_join_graph_proven,
            "eg_i82_join_closure_proven": self.eg_i82_join_closure_proven,
            "eg_i82_join_status": self.eg_i82_join_status,
            "edges": [edge.to_canonical_mapping() for edge in self.edges],
            "lane_identity_presence": {
                lane: self.lane_identity_presence[lane] for lane in NAMED_JOIN_LANES
            },
            "safety": copy.deepcopy(dict(self.safety)),
        }


def attest_eg_i82_end_to_end_live_owner_graph_v1(
    owners: Mapping[str, Any],
) -> EgI82EndToEndLiveOwnerGraphAttestationV1:
    """Traverse live-owner contracts and attest the canonical 42-edge join graph."""
    if not isinstance(owners, Mapping):
        _reject("malformed plane data rejected: owners root must be an object")
    snapshot = _snapshot(owners)
    extra = sorted(str(key) for key in owners.keys() if str(key) not in NAMED_JOIN_LANES)
    if extra:
        if extra[0] in _NONCANONICAL_IDENTITY_KEYS:
            _reject(f"noncanonical ID substitution rejected: context key {extra[0]}")
        _reject(
            f"unexpected extra edge rejected: {extra[0]} is not part of the canonical 42-edge graph"
        )
    missing_owners = [lane for lane in NAMED_JOIN_LANES if lane not in owners]
    if missing_owners:
        _reject(f"implicit absence rejected: named lane {missing_owners[0]} is missing")

    _require_registrations()

    records: dict[str, CrossLaneIdentityJoinV1] = {}
    for lane in NAMED_JOIN_LANES:
        payload = _require_owner_mapping(owners[lane], lane=lane)
        records[lane] = _TRAVERSERS[lane](payload)

    try:
        cross = verify_eg_i82_cross_lane_join_v1(records)
    except EgI82JoinVerifierError as exc:
        _raise_from_live(exc, lane="GRAPH")
        raise AssertionError("unreachable") from exc

    package_n = cross.package_n_sha256
    if not is_package_n_sha256_canonical_id(package_n):
        _reject("noncanonical ID substitution rejected: agreed identity is not Package-N SHA256")
    for lane, record in records.items():
        if record.experiment_identity_id != package_n:
            _reject(f"conflicting identity rejected: named lane {lane} IDENTITY disagrees")
        if record.plane_presence.get("IDENTITY") != PlanePresence.PRESENT.value:
            _reject(f"missing required edge rejected: {lane}xIDENTITY must be PRESENT")

    raw_edges = _edges_from_live_records(records, package_n_sha256=str(package_n))
    attested_edges = require_eg_i82_complete_live_edge_matrix_v1(
        raw_edges,
        package_n_sha256=str(package_n),
    )
    proven_count = sum(1 for edge in attested_edges if edge.proven)
    closed = (
        len(attested_edges) == EXPECTED_EDGE_COUNT
        and proven_count == EXPECTED_EDGE_COUNT
        and all(edge.canonical_join_key == package_n for edge in attested_edges)
    )
    if not closed:
        _reject("missing required edge rejected: live-owner graph is incomplete")

    if _snapshot(owners) != snapshot:
        _reject("owners input was mutated")

    return EgI82EndToEndLiveOwnerGraphAttestationV1(
        schema_version=CONTRACT_VERSION,
        contract_version=CONTRACT_VERSION,
        contract_id=CONTRACT_ID,
        attestation_registered=True,
        package_n_sha256=str(package_n),
        live_owner_paths=REAL_LIVE_OWNER_PATHS,
        named_lanes=NAMED_JOIN_LANES,
        expected_edge_count=EXPECTED_EDGE_COUNT,
        edges_evaluated=EXPECTED_EDGE_COUNT,
        edges_proven=EXPECTED_EDGE_COUNT,
        edges_disproven=0,
        edges_not_proven=0,
        edges_not_applicable=0,
        all_required_edges_proven=True,
        static_flag_aggregation_only=False,
        full_graph_traversal=True,
        end_to_end_join_graph_proven=True,
        eg_i82_join_closure_proven=True,
        eg_i82_join_status="CLOSED_PROVEN",
        edges=attested_edges,
        lane_identity_presence=MappingProxyType(
            {lane: records[lane].plane_presence["IDENTITY"] for lane in NAMED_JOIN_LANES}
        ),
        safety=_freeze_mapping(
            {
                "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
                "evidence_does_not_authorize_runtime": True,
                "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
                "SECOND_EXECUTION_AUTHORITY_AUTHORIZED": SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
                "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS": (
                    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS
                ),
            }
        ),
    )


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "EG_I82_END_TO_END_LIVE_OWNER_GRAPH_ATTESTATION_REGISTERED",
    "EXPECTED_EDGE_COUNT",
    "EXPECTED_LANE_COUNT",
    "EXPECTED_OWNER_COUNT",
    "EgI82EndToEndLiveOwnerGraphAttestationError",
    "EgI82EndToEndLiveOwnerGraphAttestationV1",
    "EgI82GraphEdgeAttestationV1",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "REAL_LIVE_OWNER_PATHS",
    "REQUIRED_GRAPH_EDGE_IDS",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "attest_eg_i82_end_to_end_live_owner_graph_v1",
    "is_eg_i82_end_to_end_live_owner_graph_attestation_registered",
    "require_eg_i82_complete_live_edge_matrix_v1",
]
