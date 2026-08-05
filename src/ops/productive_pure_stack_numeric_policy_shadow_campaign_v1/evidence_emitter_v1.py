"""Fail-closed evidence emission for Stage-2 shadow campaign packs."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    ALLOWED_PRODUCER_CLASSES,
    CAMPAIGN_RESULT_FILENAME,
    CAMPAIGN_STATE_COMPLETE,
    CAMPAIGN_STATE_DECLARED,
    CAMPAIGN_STATE_IN_PROGRESS,
    CAMPAIGN_STATE_REJECTED,
    EVIDENCE_PACK_FILENAME,
    FORBIDDEN_AUTHORITY_SOURCES,
    FORBIDDEN_OUTPUT_PATH_MARKERS,
    FORBIDDEN_PRODUCER_CLASSES,
    MANIFEST_FILENAME,
    MECHANICAL_COUPLING_RULE,
    MECHANICAL_COUPLING_TOKEN,
    OBSERVATION_IDENTITY,
    PACK_STATUS_EVIDENCE_COMPLETE_PENDING_OWNER,
    PACK_STATUS_IN_PROGRESS,
    PACK_STATUS_REJECTED_FAIL_CLOSED,
    PRODUCTIVE_NUMERIC_VALUES_SET,
    RELATIVE_OUTPUT_ROOT,
    REPRODUCIBILITY_FILENAME,
    SHADOW_DATA_COLLECTION_GROUPS,
    SOLE_TRADING_AUTHORITY,
    STAGE2_TOKENS,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    CampaignStateV1,
    EmptyCapableManifestV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    canonical_json_text,
    sha256_file,
    sha256_hex,
)


class ShadowCampaignEmitError(ValueError):
    """Fail-closed emission / path validation error."""


def _norm(text: str) -> str:
    return text.strip().lower().replace("\\", "/")


def validate_campaign_id(campaign_id: str) -> str:
    cid = campaign_id.strip()
    if not cid:
        raise ShadowCampaignEmitError("campaign_id_required")
    if "/" in cid or "\\" in cid or ".." in cid:
        raise ShadowCampaignEmitError("campaign_id_path_traversal_rejected")
    if not all(ch.isalnum() or ch in {"_", "-", "."} for ch in cid):
        raise ShadowCampaignEmitError("campaign_id_invalid_charset")
    return cid


def resolve_and_validate_output_dir(
    *,
    repo_root: Path,
    output_root: Path,
    campaign_id: str,
) -> Path:
    """Require explicit output root under the isolated evidence relative path."""
    cid = validate_campaign_id(campaign_id)
    repo = repo_root.resolve()
    out_root = output_root
    if out_root.is_symlink():
        raise ShadowCampaignEmitError("output_root_symlink_rejected")
    out_resolved = out_root.resolve()

    required_rel = (repo / RELATIVE_OUTPUT_ROOT).resolve()
    try:
        out_resolved.relative_to(required_rel)
    except ValueError as exc:
        raise ShadowCampaignEmitError(
            "output_root_must_be_under_isolated_shadow_campaign_evidence_path"
        ) from exc

    marker_blob = _norm(str(out_resolved))
    for marker in FORBIDDEN_OUTPUT_PATH_MARKERS:
        if marker in marker_blob:
            raise ShadowCampaignEmitError(f"forbidden_output_archive_path:{marker}")

    campaign_dir = (out_resolved / cid).resolve()
    try:
        campaign_dir.relative_to(out_resolved)
    except ValueError as exc:
        raise ShadowCampaignEmitError("campaign_dir_escape_rejected") from exc

    if campaign_dir != out_resolved / cid:
        # Defend against odd normalize cases.
        raise ShadowCampaignEmitError("campaign_dir_path_mismatch")

    return campaign_dir


def assert_no_overwrite(campaign_dir: Path, *, allow_overwrite: bool) -> None:
    if allow_overwrite:
        raise ShadowCampaignEmitError("overwrite_not_authorized_for_shadow_campaign")
    if campaign_dir.exists():
        raise ShadowCampaignEmitError("campaign_output_already_exists")


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def map_internal_state_to_pack_status(state: CampaignStateV1) -> str:
    if state is CampaignStateV1.REJECTED:
        return PACK_STATUS_REJECTED_FAIL_CLOSED
    if state is CampaignStateV1.COMPLETE:
        return PACK_STATUS_EVIDENCE_COMPLETE_PENDING_OWNER
    if state in {CampaignStateV1.DECLARED, CampaignStateV1.IN_PROGRESS}:
        return PACK_STATUS_IN_PROGRESS
    raise ShadowCampaignEmitError(f"unknown_campaign_state:{state}")


def manifests_all_complete(
    manifests: Mapping[str, EmptyCapableManifestV1],
) -> bool:
    for manifest in manifests.values():
        if (
            manifest.status != "COMPLETE"
            or not manifest.populated
            or not manifest.entries
            or not manifest.digest
        ):
            return False
    return True


def decide_campaign_state(
    *,
    rejection_reasons: Sequence[str],
    manifests: Mapping[str, EmptyCapableManifestV1],
    evidence_requirements_met: bool,
) -> CampaignStateV1:
    if rejection_reasons:
        return CampaignStateV1.REJECTED
    if evidence_requirements_met and manifests_all_complete(manifests):
        return CampaignStateV1.COMPLETE
    if any(m.status != "EMPTY_SCAFFOLD" or m.populated for m in manifests.values()):
        return CampaignStateV1.IN_PROGRESS
    return CampaignStateV1.DECLARED


def _empty_manifest_dict(manifest: EmptyCapableManifestV1) -> dict[str, Any]:
    return manifest.to_dict()


def build_token_rows_from_scaffold(
    scaffold_rows: Sequence[Mapping[str, Any]],
    *,
    observation_notes: Mapping[str, Sequence[str]] | None = None,
    blockers: Mapping[str, Sequence[str]] | None = None,
) -> list[dict[str, Any]]:
    notes = observation_notes or {}
    block = blockers or {}
    by_token = {str(row["token"]): dict(row) for row in scaffold_rows}
    missing = [t for t in STAGE2_TOKENS if t not in by_token]
    if missing:
        raise ShadowCampaignEmitError("scaffold_missing_tokens:" + ",".join(missing))
    if MECHANICAL_COUPLING_TOKEN in by_token:
        raise ShadowCampaignEmitError("independent_reinvest_fraction_token_forbidden")

    rows: list[dict[str, Any]] = []
    for token in STAGE2_TOKENS:
        row = dict(by_token[token])
        row["token"] = token
        row["productive_numeric_value"] = None
        row["input_authority"] = False
        row["runtime_implemented"] = False
        row["owner_ratification_status"] = "NOT_RATIFIED"
        # Never allow forbidden authority declarations on emitted rows.
        for field in ("authority_source", "derivation_source"):
            value = row.get(field)
            if value is None:
                continue
            lowered = _norm(str(value))
            for marker in FORBIDDEN_AUTHORITY_SOURCES:
                if marker.lower() in lowered:
                    raise ShadowCampaignEmitError(
                        f"forbidden_authority_source:{token}:{field}:{marker}"
                    )
        extra_notes = list(notes.get(token, ()))
        rejection = list(row.get("rejection_reasons") or [])
        rejection.extend(block.get(token, ()))
        if extra_notes:
            # Keep schema-compatible fields; encode observation status in rejection notes
            # only when blocked. Otherwise leave acceptance empty for IN_PROGRESS.
            row.setdefault("acceptance_gate_results", [])
            if not isinstance(row["acceptance_gate_results"], list):
                row["acceptance_gate_results"] = []
            row["acceptance_gate_results"].append(
                {
                    "gate_id": "shadow_observation_note",
                    "status": "NOT_EVALUATED",
                    "notes": ";".join(extra_notes),
                }
            )
        row["rejection_reasons"] = rejection
        rows.append(row)
    return rows


def build_evidence_pack(
    *,
    campaign_id: str,
    campaign_state: CampaignStateV1,
    origin_main_sha: str,
    stage1_manifest_digest: str,
    calibration_protocol_digest: str,
    scaffold_rows: Sequence[Mapping[str, Any]],
    manifests: Mapping[str, EmptyCapableManifestV1],
    rejection_reasons: Sequence[str],
    observation_notes: Mapping[str, Sequence[str]] | None = None,
    blockers: Mapping[str, Sequence[str]] | None = None,
    metric_definition_digests: Optional[Mapping[str, Optional[str]]] = None,
) -> dict[str, Any]:
    if len(origin_main_sha) != 40:
        raise ShadowCampaignEmitError("origin_main_sha_invalid")
    pack_status = map_internal_state_to_pack_status(campaign_state)
    evidence_complete = campaign_state is CampaignStateV1.COMPLETE
    if evidence_complete and not manifests_all_complete(manifests):
        raise ShadowCampaignEmitError("complete_requires_all_manifests_complete")
    if evidence_complete is True and rejection_reasons:
        raise ShadowCampaignEmitError("complete_with_rejections_forbidden")

    rows = build_token_rows_from_scaffold(
        scaffold_rows,
        observation_notes=observation_notes,
        blockers=blockers,
    )
    metric_digests = {
        "block_allow_rate": None,
        "false_allow_rate": None,
        "false_block_rate": None,
        "path_survival": None,
        "early_loss_toxicity": None,
        "liquidation_near_miss_rate": None,
        "governance_breach_frequency": None,
        "effective_leverage": None,
        "liquidation_buffer": None,
        "adverse_fill_loss": None,
    }
    if metric_definition_digests:
        metric_digests.update(dict(metric_definition_digests))

    pack: dict[str, Any] = {
        "schema_version": "productive_pure_stack_numeric_policy_evidence_pack/v1",
        "campaign_id": campaign_id,
        "campaign_status": pack_status,
        "origin_main_sha": origin_main_sha,
        "stage1_manifest_digest": stage1_manifest_digest,
        "calibration_protocol_digest": calibration_protocol_digest,
        "sole_trading_authority_symbol": SOLE_TRADING_AUTHORITY,
        "observation_identity": dict(OBSERVATION_IDENTITY),
        "producer_identity": {
            "status": "SHADOW_DECLARED",
            "productive_activation": False,
            "allowed_producer_classes": list(ALLOWED_PRODUCER_CLASSES),
            "forbidden_producer_classes": list(FORBIDDEN_PRODUCER_CLASSES),
        },
        "dataset_manifest": _empty_manifest_dict(manifests["dataset_manifest"]),
        "train_calibration_validation_partition_manifest": _empty_manifest_dict(
            manifests["train_calibration_validation_partition_manifest"]
        ),
        "walk_forward_manifest": _empty_manifest_dict(manifests["walk_forward_manifest"]),
        "bootstrap_monte_carlo_manifest": _empty_manifest_dict(
            manifests["bootstrap_monte_carlo_manifest"]
        ),
        "stress_pack_manifest": _empty_manifest_dict(manifests["stress_pack_manifest"]),
        "metric_definition_digests": metric_digests,
        "per_token_evidence": rows,
        "acceptance_gate_results": [
            {
                "gate_id": "shadow_campaign_integrity",
                "status": "NOT_EVALUATED"
                if campaign_state is not CampaignStateV1.REJECTED
                else "REJECTED_FAIL_CLOSED",
                "notes": (
                    "Shadow evidence collection only; not productive calibration; "
                    "groups are data-collection only (no auto-ratification); "
                    f"mechanical_coupling={MECHANICAL_COUPLING_TOKEN}:{MECHANICAL_COUPLING_RULE}"
                ),
            }
        ],
        "rejection_reasons": list(rejection_reasons),
        "owner_ratification_status": "NOT_RATIFIED",
        "productive_numeric_values_set": PRODUCTIVE_NUMERIC_VALUES_SET,
        "evidence_complete": evidence_complete,
        "owner_ratified": False,
        "input_authority": False,
        "runtime_implemented": False,
        "dashboard_role": "READ_ONLY_CONSUMER",
        "forbidden_authority_declarations": {
            "fixture_scenario_webui_as_authority": False,
            "cmc_volatility_estimate_as_realized_volatility": False,
            "survival_result_v1_as_numeric_authority": False,
            "suitability_result_v1_as_numeric_authority": False,
            "dashboard_as_authority": False,
            "archive_as_authority": False,
            "reinvest_fraction_independent_numeric": False,
            "capital_slot_time_quantum_wallclock_seconds": False,
            "initial_slot_base_from_account_equity": False,
        },
    }
    if len(pack["per_token_evidence"]) != 18:
        raise ShadowCampaignEmitError("token_count_must_be_18")
    return pack


def write_campaign_artifacts(
    *,
    campaign_dir: Path,
    pack: Mapping[str, Any],
    result_payload: Mapping[str, Any],
    reproducibility_payload: Mapping[str, Any],
) -> str:
    campaign_dir.mkdir(parents=True, exist_ok=False)
    pack_path = campaign_dir / EVIDENCE_PACK_FILENAME
    result_path = campaign_dir / CAMPAIGN_RESULT_FILENAME
    repro_path = campaign_dir / REPRODUCIBILITY_FILENAME

    pack_text = canonical_json_text(dict(pack)) + "\n"
    result_text = canonical_json_text(dict(result_payload)) + "\n"
    repro_text = canonical_json_text(dict(reproducibility_payload)) + "\n"

    atomic_write_text(pack_path, pack_text)
    atomic_write_text(result_path, result_text)
    atomic_write_text(repro_path, repro_text)

    relative_files = (
        EVIDENCE_PACK_FILENAME,
        CAMPAIGN_RESULT_FILENAME,
        REPRODUCIBILITY_FILENAME,
    )
    lines = []
    for rel in relative_files:
        digest = sha256_file(campaign_dir / rel)
        lines.append(f"{digest}  {rel}")
    manifest_body = "\n".join(lines) + "\n"
    atomic_write_text(campaign_dir / MANIFEST_FILENAME, manifest_body)
    return sha256_hex(pack_text.encode("utf-8"))


def data_collection_groups_payload() -> dict[str, list[str]]:
    return {k: list(v) for k, v in SHADOW_DATA_COLLECTION_GROUPS.items()}


# Silence unused-import lint for state constants re-exported via map helpers.
_ = (
    CAMPAIGN_STATE_DECLARED,
    CAMPAIGN_STATE_IN_PROGRESS,
    CAMPAIGN_STATE_COMPLETE,
    CAMPAIGN_STATE_REJECTED,
)
