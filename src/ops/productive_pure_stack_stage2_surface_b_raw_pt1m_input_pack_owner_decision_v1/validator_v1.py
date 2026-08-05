"""Fail-closed validator for Surface-B raw PT1M input-pack Owner Decision v1.

Does not invent candles/marks/instance values. Does not start campaigns.
Reuses Surface-B instrument/candle/mark invariants without mutating collector
semantics.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.boundary_guards_v1 import (
    assert_forbidden_effects_remain_false,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InstrumentBindingV1,
    MarkPriceInputV1,
    VenueNativeCandleInputV1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.pt1m_finalized_ohlcv_producer_v1 import (
    produce_pt1m_finalized_ohlcv_bars_v1,
    validate_instrument_binding,
)
from src.ops.productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_owner_decision_v1 import (
    constants_v1 as C,
)

_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class RawInputPackOwnerDecisionErrorV1(ValueError):
    """Fail-closed Owner Decision / binding-claim error."""


def _require_mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RawInputPackOwnerDecisionErrorV1(f"{label}_MUST_BE_OBJECT")
    return value


def _assert_null(value: Any, *, label: str) -> None:
    if value is not None:
        raise RawInputPackOwnerDecisionErrorV1(f"{label}_MUST_REMAIN_NULL")


def _assert_false(value: Any, *, label: str) -> None:
    if value is not True and value is not False:
        raise RawInputPackOwnerDecisionErrorV1(f"{label}_MUST_BE_BOOL")
    if value:
        raise RawInputPackOwnerDecisionErrorV1(f"{label}_MUST_REMAIN_FALSE")


def _assert_source_token_allowed(token: str) -> None:
    lowered = str(token or "").strip().lower()
    if not lowered:
        raise RawInputPackOwnerDecisionErrorV1("SOURCE_TOKEN_EMPTY")
    for forbidden in C.FORBIDDEN_SOURCE_TOKENS:
        if forbidden in lowered:
            raise RawInputPackOwnerDecisionErrorV1(f"FORBIDDEN_SOURCE:{forbidden}")


def load_canonical_decisions_manifest_v1(repo_root: Path) -> dict[str, Any]:
    path = Path(repo_root).resolve() / C.DECISIONS_MANIFEST_REL
    if not path.is_file():
        raise RawInputPackOwnerDecisionErrorV1("DECISIONS_MANIFEST_MISSING")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RawInputPackOwnerDecisionErrorV1("DECISIONS_MANIFEST_NOT_OBJECT")
    return data


def validate_owner_decision_manifest_v1(
    manifest: Mapping[str, Any],
    *,
    require_structure_open_status: bool = True,
) -> dict[str, Any]:
    """Validate machine-readable Owner Decision manifest structure."""
    assert_forbidden_effects_remain_false()
    for key in C.REQUIRED_MANIFEST_TOP_KEYS:
        if key not in manifest:
            raise RawInputPackOwnerDecisionErrorV1(f"MANIFEST_MISSING_KEY:{key}")

    if manifest.get("schema_version") != C.SCHEMA_VERSION:
        raise RawInputPackOwnerDecisionErrorV1("SCHEMA_VERSION_MISMATCH")
    if manifest.get("document_type") != C.DOCUMENT_TYPE:
        raise RawInputPackOwnerDecisionErrorV1("DOCUMENT_TYPE_MISMATCH")
    if manifest.get("capability_scope") != C.CAPABILITY_SCOPE:
        raise RawInputPackOwnerDecisionErrorV1("CAPABILITY_SCOPE_MISMATCH")
    if require_structure_open_status:
        if manifest.get("status") != C.STATUS_STRUCTURE_OPEN:
            raise RawInputPackOwnerDecisionErrorV1("STATUS_MUST_BE_STRUCTURE_OPEN")
    if manifest.get("baseline_origin_main_sha") != C.BASELINE_ORIGIN_MAIN_SHA:
        raise RawInputPackOwnerDecisionErrorV1("BASELINE_ORIGIN_MAIN_SHA_MISMATCH")
    if not _SHA40.match(str(manifest.get("baseline_origin_main_sha") or "")):
        raise RawInputPackOwnerDecisionErrorV1("BASELINE_ORIGIN_MAIN_SHA_INVALID")
    if manifest.get("authority_surface") != C.AUTHORITY_SURFACE:
        raise RawInputPackOwnerDecisionErrorV1("AUTHORITY_SURFACE_MUST_BE_B")

    _assert_false(manifest.get("input_authority"), label="input_authority")
    _assert_false(manifest.get("runtime_implemented"), label="runtime_implemented")
    if require_structure_open_status:
        _assert_false(
            manifest.get("campaign_start_authorized"),
            label="campaign_start_authorized",
        )
        _assert_false(
            manifest.get("raw_input_pack_materialization_authorized"),
            label="raw_input_pack_materialization_authorized",
        )
    if int(manifest.get("productive_numeric_values_set", -1)) != 0:
        raise RawInputPackOwnerDecisionErrorV1("PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO")
    _assert_null(manifest.get("purge"), label="purge")
    _assert_null(manifest.get("embargo"), label="embargo")
    _assert_null(manifest.get("fold_sizes"), label="fold_sizes")

    if manifest.get("dashboard_authority_effect") not in (None, "NONE"):
        if manifest.get("dashboard_authority_effect") != "NONE":
            raise RawInputPackOwnerDecisionErrorV1("DASHBOARD_AUTHORITY_MUST_BE_NONE")
    if manifest.get("notion_ssot") is True:
        raise RawInputPackOwnerDecisionErrorV1("NOTION_SSOT_MUST_REMAIN_FALSE")
    if manifest.get("repository_is_ssot") is False:
        raise RawInputPackOwnerDecisionErrorV1("REPOSITORY_MUST_REMAIN_SSOT")

    instance = _require_mapping(manifest.get("campaign_instance"), label="campaign_instance")
    for key in C.REQUIRED_INSTANCE_KEYS:
        if key not in instance:
            raise RawInputPackOwnerDecisionErrorV1(f"INSTANCE_MISSING_KEY:{key}")

    if require_structure_open_status:
        for key in (
            "campaign_id",
            "dataset_id",
            "scenario_id",
            "instrument_binding",
            "seed",
            "event_time_epoch_s",
            "partition_boundaries_event_time_epoch_s",
            "fold_ids",
            "bootstrap_seeds",
            "regime_coverage",
        ):
            _assert_null(instance.get(key), label=f"campaign_instance.{key}")
        candle = _require_mapping(instance.get("candle_authority"), label="candle_authority")
        mark = _require_mapping(instance.get("mark_price_authority"), label="mark_price_authority")
        prov = _require_mapping(instance.get("pack_provenance"), label="pack_provenance")
        _assert_null(candle.get("candles"), label="candle_authority.candles")
        _assert_null(candle.get("source_ref"), label="candle_authority.source_ref")
        _assert_null(mark.get("marks"), label="mark_price_authority.marks")
        _assert_null(mark.get("source_ref"), label="mark_price_authority.source_ref")
        for pk in (
            "observation_pack_digest",
            "raw_source_digest",
            "repository_sha",
            "config_digest",
            "ingestion_timestamp",
            "finalization_timestamp",
            "event_time_range",
        ):
            _assert_null(prov.get(pk), label=f"pack_provenance.{pk}")
        if candle.get("open_tip_bars") is not False:
            raise RawInputPackOwnerDecisionErrorV1("OPEN_TIP_BARS_MUST_BE_FALSE")
        if mark.get("candle_mark_trade_equivalence") != "FORBIDDEN":
            raise RawInputPackOwnerDecisionErrorV1(
                "CANDLE_MARK_TRADE_EQUIVALENCE_MUST_REMAIN_FORBIDDEN"
            )

    decisions = _require_mapping(manifest.get("decisions"), label="decisions")
    for key in (
        "INSTRUMENT_BINDING",
        "CANDLE_AUTHORITY",
        "MARK_PRICE_AUTHORITY",
        "PIT_NO_LOOKAHEAD",
        "PACK_IDENTITY",
        "CAMPAIGN_INSTANCE_BINDING",
        "FORBIDDEN_SOURCES",
    ):
        if key not in decisions:
            raise RawInputPackOwnerDecisionErrorV1(f"DECISIONS_MISSING:{key}")
    mark_dec = _require_mapping(decisions.get("MARK_PRICE_AUTHORITY"), label="MARK_PRICE_AUTHORITY")
    if mark_dec.get("candle_mark_trade_equivalence") != "FORBIDDEN":
        raise RawInputPackOwnerDecisionErrorV1(
            "DECISION_CANDLE_MARK_TRADE_EQUIVALENCE_MUST_REMAIN_FORBIDDEN"
        )
    camp_dec = _require_mapping(
        decisions.get("CAMPAIGN_INSTANCE_BINDING"), label="CAMPAIGN_INSTANCE_BINDING"
    )
    _assert_null(camp_dec.get("purge"), label="decisions.CAMPAIGN_INSTANCE_BINDING.purge")
    _assert_null(camp_dec.get("embargo"), label="decisions.CAMPAIGN_INSTANCE_BINDING.embargo")
    _assert_null(camp_dec.get("fold_sizes"), label="decisions.CAMPAIGN_INSTANCE_BINDING.fold_sizes")

    return {
        "ok": True,
        "capability_scope": C.CAPABILITY_SCOPE,
        "status": manifest.get("status"),
        "input_authority": False,
        "runtime_implemented": False,
        "campaign_start_authorized": bool(manifest.get("campaign_start_authorized")),
        "raw_input_pack_materialization_authorized": bool(
            manifest.get("raw_input_pack_materialization_authorized")
        ),
        "productive_numeric_values_set": 0,
        "purge": None,
        "embargo": None,
        "fold_sizes": None,
        "dashboard_authority_effect": "NONE",
        "notion_ssot": False,
        "repository_is_ssot": True,
    }


def _parse_binding(raw: Any) -> InstrumentBindingV1:
    mapping = _require_mapping(raw, label="instrument_binding")
    try:
        binding = InstrumentBindingV1(**{k: mapping[k] for k in C.REQUIRED_INSTRUMENT_FIELDS})
    except (KeyError, TypeError) as exc:
        raise RawInputPackOwnerDecisionErrorV1("INSTRUMENT_BINDING_INCOMPLETE") from exc
    validate_instrument_binding(binding)
    for token in (binding.venue, binding.venue_instrument_id, binding.canonical_instrument_id):
        _assert_source_token_allowed(token)
    mode = str(mapping.get("binding_mode", "SINGLE_SELECTED_FUTURE_VENUE_NATIVE")).upper()
    if mode not in {"SINGLE_SELECTED_FUTURE_VENUE_NATIVE", "VENUE_NATIVE"}:
        raise RawInputPackOwnerDecisionErrorV1("INSTRUMENT_BINDING_NOT_VENUE_NATIVE")
    return binding


def _parse_candles(raw: Any) -> tuple[VenueNativeCandleInputV1, ...]:
    if raw is None:
        raise RawInputPackOwnerDecisionErrorV1("CANDLES_REQUIRED")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise RawInputPackOwnerDecisionErrorV1("CANDLES_MUST_BE_SEQUENCE")
    if len(raw) == 0:
        raise RawInputPackOwnerDecisionErrorV1("CANDLES_REQUIRED")
    out: list[VenueNativeCandleInputV1] = []
    for row in raw:
        item = _require_mapping(row, label="candle")
        try:
            candle = VenueNativeCandleInputV1(
                event_time_epoch_s=int(item["event_time_epoch_s"]),
                open=float(item["open"]),
                high=float(item["high"]),
                low=float(item["low"]),
                close=float(item["close"]),
                volume=float(item["volume"]),
                venue_finalized=bool(item["venue_finalized"]),
                open_tip=bool(item.get("open_tip", False)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RawInputPackOwnerDecisionErrorV1("CANDLE_ROW_INVALID") from exc
        if candle.open_tip:
            raise RawInputPackOwnerDecisionErrorV1("OPEN_TIP_BARS_FORBIDDEN")
        if not candle.venue_finalized:
            raise RawInputPackOwnerDecisionErrorV1("VENUE_CANDLE_NOT_FINALIZED")
        out.append(candle)
    return tuple(out)


def _parse_marks(raw: Any) -> tuple[MarkPriceInputV1, ...]:
    if raw is None:
        raise RawInputPackOwnerDecisionErrorV1("MARKS_REQUIRED")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise RawInputPackOwnerDecisionErrorV1("MARKS_MUST_BE_SEQUENCE")
    if len(raw) == 0:
        raise RawInputPackOwnerDecisionErrorV1("MARKS_REQUIRED")
    out: list[MarkPriceInputV1] = []
    for row in raw:
        item = _require_mapping(row, label="mark")
        try:
            mark = MarkPriceInputV1(
                event_time_epoch_s=int(item["event_time_epoch_s"]),
                mark_price=float(item["mark_price"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RawInputPackOwnerDecisionErrorV1("MARK_ROW_INVALID") from exc
        out.append(mark)
    return tuple(out)


def _assert_seed_structure(seed: Any) -> int:
    if seed is None:
        raise RawInputPackOwnerDecisionErrorV1("SEED_REQUIRED")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise RawInputPackOwnerDecisionErrorV1("SEED_MUST_BE_INT")
    return int(seed)


def _assert_partition_boundaries(raw: Any) -> dict[str, int]:
    mapping = _require_mapping(raw, label="partition_boundaries")
    if set(mapping.keys()) != set(C.PARTITION_SEGMENTS):
        raise RawInputPackOwnerDecisionErrorV1("PARTITION_SEGMENTS_INCOMPLETE")
    out: dict[str, int] = {}
    for seg in C.PARTITION_SEGMENTS:
        value = mapping[seg]
        if isinstance(value, bool) or not isinstance(value, int):
            raise RawInputPackOwnerDecisionErrorV1(f"PARTITION_BOUNDARY_NOT_INT:{seg}")
        out[seg] = int(value)
    ordered = [out[s] for s in C.PARTITION_SEGMENTS]
    if ordered != sorted(ordered):
        raise RawInputPackOwnerDecisionErrorV1("PARTITION_NOT_CHRONOLOGICAL")
    return out


def validate_candle_mark_instrument_inputs_v1(
    *,
    binding_raw: Any,
    dataset_id: str,
    candles_raw: Any,
    marks_raw: Any,
    allow_candle_mark_equivalence: bool = False,
    event_time_epoch_s: Optional[int] = None,
) -> dict[str, Any]:
    """Fail-closed candle/mark/binding hygiene (no pack materialization, no start)."""
    assert_forbidden_effects_remain_false()
    if allow_candle_mark_equivalence:
        raise RawInputPackOwnerDecisionErrorV1("CANDLE_MARK_TRADE_EQUIVALENCE_FORBIDDEN")
    if not dataset_id or not str(dataset_id).strip():
        raise RawInputPackOwnerDecisionErrorV1("DATASET_ID_REQUIRED")
    binding = _parse_binding(binding_raw)
    candles = _parse_candles(candles_raw)
    marks = _parse_marks(marks_raw)
    bars = produce_pt1m_finalized_ohlcv_bars_v1(
        binding=binding,
        dataset_id=str(dataset_id),
        candles=candles,
        marks=marks,
        allow_candle_mark_equivalence=False,
    )
    exclusive_tip = int(bars[-1].event_time_epoch_s) + 60
    if event_time_epoch_s is not None and int(event_time_epoch_s) != exclusive_tip:
        raise RawInputPackOwnerDecisionErrorV1("EVENT_TIME_EPOCH_S_MUST_EQUAL_PACK_EXCLUSIVE_TIP")
    return {
        "ok": True,
        "bar_count": len(bars),
        "exclusive_tip_event_time_epoch_s": exclusive_tip,
        "instrument_id": binding.canonical_instrument_id,
        "dataset_id": str(dataset_id),
        "input_authority": False,
        "runtime_implemented": False,
        "campaign_start_authorized": False,
        "raw_input_pack_materialization_authorized": False,
    }


def validate_raw_input_pack_campaign_binding_claim_v1(
    claim: Mapping[str, Any],
    *,
    owner_manifest: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Validate a pack/campaign binding claim fail-closed.

    While this Owner Decision keeps materialization and campaign-start flags
    false, any materialization or start attempt is rejected. Optional candle /
    mark / binding payloads are still hygiene-checked when present.
    """
    assert_forbidden_effects_remain_false()
    claim_map = _require_mapping(claim, label="claim")

    if claim_map.get("input_authority") is True:
        raise RawInputPackOwnerDecisionErrorV1("INPUT_AUTHORITY_FLIP_FORBIDDEN")
    if claim_map.get("runtime_implemented") is True:
        raise RawInputPackOwnerDecisionErrorV1("RUNTIME_IMPLEMENTED_FLIP_FORBIDDEN")
    if int(claim_map.get("productive_numeric_values_set", 0)) != 0:
        raise RawInputPackOwnerDecisionErrorV1("PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO")

    for label in ("purge", "embargo", "fold_sizes", "purge_seconds", "embargo_seconds"):
        if label in claim_map:
            _assert_null(claim_map.get(label), label=label)

    for src_key in ("source_id", "candle_source", "mark_source", "authority_source"):
        if src_key in claim_map and claim_map.get(src_key) is not None:
            _assert_source_token_allowed(str(claim_map.get(src_key)))

    if owner_manifest is not None:
        validate_owner_decision_manifest_v1(owner_manifest, require_structure_open_status=False)

    materialize = bool(claim_map.get("raw_input_pack_materialization_authorized", False))
    start = bool(claim_map.get("campaign_start_authorized", False))
    attempt_start = bool(
        claim_map.get("attempt_campaign_start") or claim_map.get("start_evidence_collection")
    )

    # Package-level authorization remains false until a later Owner GO.
    if start or attempt_start or materialize:
        if not C.CAMPAIGN_START_AUTHORIZED and (start or attempt_start):
            raise RawInputPackOwnerDecisionErrorV1("CAMPAIGN_START_UNAUTHORIZED")
        if not C.RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED and materialize:
            raise RawInputPackOwnerDecisionErrorV1("PACK_MATERIALIZATION_UNAUTHORIZED")
        if owner_manifest is not None:
            if (start or attempt_start) and not bool(
                owner_manifest.get("campaign_start_authorized")
            ):
                raise RawInputPackOwnerDecisionErrorV1(
                    "CAMPAIGN_START_NOT_AUTHORIZED_BY_OWNER_MANIFEST"
                )
            if materialize and not bool(
                owner_manifest.get("raw_input_pack_materialization_authorized")
            ):
                raise RawInputPackOwnerDecisionErrorV1(
                    "PACK_MATERIALIZATION_NOT_AUTHORIZED_BY_OWNER_MANIFEST"
                )

    # Optional hygiene when candle/mark/binding payloads are supplied.
    hygiene_requested = (
        claim_map.get("instrument_binding") is not None
        or "candles" in claim_map
        or "marks" in claim_map
    )
    if hygiene_requested:
        if claim_map.get("instrument_binding") is None:
            raise RawInputPackOwnerDecisionErrorV1("INSTRUMENT_BINDING_REQUIRED")
        if claim_map.get("dataset_id") is None:
            raise RawInputPackOwnerDecisionErrorV1("DATASET_ID_REQUIRED")
        if "candles" in claim_map and claim_map.get("candles") is None:
            raise RawInputPackOwnerDecisionErrorV1("CANDLES_REQUIRED")
        if "marks" in claim_map and claim_map.get("marks") is None:
            raise RawInputPackOwnerDecisionErrorV1("MARKS_REQUIRED")
        if claim_map.get("candles") is not None or claim_map.get("marks") is not None:
            validate_candle_mark_instrument_inputs_v1(
                binding_raw=claim_map["instrument_binding"],
                dataset_id=str(claim_map["dataset_id"]),
                candles_raw=claim_map.get("candles"),
                marks_raw=claim_map.get("marks"),
                allow_candle_mark_equivalence=bool(
                    claim_map.get("allow_candle_mark_equivalence", False)
                ),
                event_time_epoch_s=(
                    int(claim_map["event_time_epoch_s"])
                    if claim_map.get("event_time_epoch_s") is not None
                    else None
                ),
            )

    # Identity consistency checks when both sides present.
    if claim_map.get("campaign_id") is not None and claim_map.get("dataset_id") is not None:
        if not str(claim_map["campaign_id"]).strip() or not str(claim_map["dataset_id"]).strip():
            raise RawInputPackOwnerDecisionErrorV1("INSTANCE_IDENTITY_EMPTY")
        if (
            claim_map.get("dataset_id_binding") is not None
            and str(claim_map["dataset_id_binding"]).strip() != str(claim_map["dataset_id"]).strip()
        ):
            raise RawInputPackOwnerDecisionErrorV1("DATASET_CAMPAIGN_IDENTITY_INCONSISTENT")

    if "seed" in claim_map and claim_map.get("seed") is not None:
        _assert_seed_structure(claim_map.get("seed"))
    if claim_map.get("seed") is None and claim_map.get("require_seed") is True:
        raise RawInputPackOwnerDecisionErrorV1("SEED_REQUIRED")

    if claim_map.get("partition_boundaries_event_time_epoch_s") is not None:
        _assert_partition_boundaries(claim_map["partition_boundaries_event_time_epoch_s"])
    if claim_map.get("fold_ids") is not None:
        fold_ids = claim_map["fold_ids"]
        if not isinstance(fold_ids, Sequence) or isinstance(fold_ids, (str, bytes)):
            raise RawInputPackOwnerDecisionErrorV1("FOLD_IDS_MUST_BE_SEQUENCE")
        if len(fold_ids) < 1:
            raise RawInputPackOwnerDecisionErrorV1("FOLD_IDS_REQUIRED")
        if len(set(fold_ids)) != len(fold_ids):
            raise RawInputPackOwnerDecisionErrorV1("FOLD_IDS_NOT_UNIQUE")
    if claim_map.get("bootstrap_seeds") is not None:
        bootstrap_seeds = claim_map["bootstrap_seeds"]
        if not isinstance(bootstrap_seeds, Sequence) or isinstance(bootstrap_seeds, (str, bytes)):
            raise RawInputPackOwnerDecisionErrorV1("BOOTSTRAP_SEEDS_MUST_BE_SEQUENCE")
        if len(bootstrap_seeds) < 1:
            raise RawInputPackOwnerDecisionErrorV1("BOOTSTRAP_SEEDS_REQUIRED")
        for s in bootstrap_seeds:
            if isinstance(s, bool) or not isinstance(s, int):
                raise RawInputPackOwnerDecisionErrorV1("BOOTSTRAP_SEED_MUST_BE_INT")

    return {
        "ok": True,
        "validated": "binding_claim",
        "campaign_start_authorized": False,
        "raw_input_pack_materialization_authorized": False,
        "input_authority": False,
        "runtime_implemented": False,
        "productive_numeric_values_set": 0,
        "purge": None,
        "embargo": None,
        "fold_sizes": None,
        "dashboard_authority_effect": "NONE",
        "notion_ssot": False,
        "repository_is_ssot": True,
    }
