"""Settings cartography for GHV productive path and Shadow continuation."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1 import constants_v1 as shadow_const
from src.ops.ghv_regression_corpus_provenance_v1 import (
    GHV_E2E_EXPECTED_CYCLE_COUNT,
    GHV_E2E_EXPECTED_FLIGHT_COUNT,
    GHV_E2E_PRODUCTIVE_REPROOF_OWNER,
)


def _setting(
    *,
    setting_id: str,
    name: str,
    owner: str,
    source_file: str,
    source_symbol: str,
    default_value: Any,
    effective_ghv: Any,
    effective_current: Any,
    consumer: str,
    stage: str,
    authority: str,
    mutability: str,
    shadow_relevance: str,
    safety_relevance: str,
    semantic_class: str,
) -> dict[str, Any]:
    return {
        "SETTING_ID": setting_id,
        "SETTING_NAME": name,
        "OWNER": owner,
        "SOURCE_FILE": source_file,
        "SOURCE_SYMBOL": source_symbol,
        "DEFAULT_VALUE": default_value,
        "EFFECTIVE_GHV_VALUE": effective_ghv,
        "EFFECTIVE_CURRENT_VALUE": effective_current,
        "RUNTIME_CONSUMER": consumer,
        "STAGE": stage,
        "AUTHORITY": authority,
        "MUTABILITY": mutability,
        "SHADOW_RELEVANCE": shadow_relevance,
        "SAFETY_RELEVANCE": safety_relevance,
        "PROVENANCE": "canonical_shadow_runtime_closure_v2",
        "SEMANTIC_CLASS": semantic_class,
    }


def build_canonical_settings_cartography_v1(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
    preflight_path = root / "config/ops/paper_shadow_247_preflight.toml"
    preflight = (
        tomllib.loads(preflight_path.read_text(encoding="utf-8"))
        if preflight_path.is_file()
        else {}
    )
    settings: list[dict[str, Any]] = [
        _setting(
            setting_id="GHV_E2E_CYCLE_COUNT",
            name="GHV E2E expected cycle count",
            owner=GHV_E2E_PRODUCTIVE_REPROOF_OWNER,
            source_file="src/ops/ghv_regression_corpus_provenance_v1.py",
            source_symbol="GHV_E2E_EXPECTED_CYCLE_COUNT",
            default_value=GHV_E2E_EXPECTED_CYCLE_COUNT,
            effective_ghv=GHV_E2E_EXPECTED_CYCLE_COUNT,
            effective_current=GHV_E2E_EXPECTED_CYCLE_COUNT,
            consumer="preservation_reproof",
            stage="GHV",
            authority="PRESERVATION",
            mutability="IMMUTABLE_REFERENCE",
            shadow_relevance="FORENSIC_INSTRUMENT",
            safety_relevance="REGRESSION",
            semantic_class="PRODUCTIVE_SEMANTIC_INVARIANT",
        ),
        _setting(
            setting_id="GHV_E2E_FLIGHT_COUNT",
            name="GHV E2E expected flight count",
            owner=GHV_E2E_PRODUCTIVE_REPROOF_OWNER,
            source_file="src/ops/ghv_regression_corpus_provenance_v1.py",
            source_symbol="GHV_E2E_EXPECTED_FLIGHT_COUNT",
            default_value=GHV_E2E_EXPECTED_FLIGHT_COUNT,
            effective_ghv=GHV_E2E_EXPECTED_FLIGHT_COUNT,
            effective_current=GHV_E2E_EXPECTED_FLIGHT_COUNT,
            consumer="preservation_reproof",
            stage="GHV",
            authority="PRESERVATION",
            mutability="IMMUTABLE_REFERENCE",
            shadow_relevance="FORENSIC_INSTRUMENT",
            safety_relevance="REGRESSION",
            semantic_class="PRODUCTIVE_SEMANTIC_INVARIANT",
        ),
        _setting(
            setting_id="POST_ALLOWED",
            name="Real POST allowed",
            owner="canonical_shadow_runtime_enablement_v1",
            source_file="src/ops/canonical_shadow_runtime_enablement_v1/constants_v1.py",
            source_symbol="POST_ALLOWED",
            default_value=False,
            effective_ghv=False,
            effective_current=shadow_const.POST_ALLOWED,
            consumer="shadow_execution_sink_v1",
            stage="SHADOW_BOUNDARY",
            authority="SAFETY",
            mutability="INVARIANT",
            shadow_relevance="SHADOW_SINK_GATE",
            safety_relevance="CRITICAL",
            semantic_class="SAFETY_INVARIANT",
        ),
        _setting(
            setting_id="SHADOW_RUNTIME_MODE",
            name="Shadow runtime mode label",
            owner="canonical_shadow_runtime_enablement_v1",
            source_file="src/ops/canonical_shadow_runtime_enablement_v1/constants_v1.py",
            source_symbol="SHADOW_RUNTIME_MODE",
            default_value="SHADOW",
            effective_ghv="PRODUCTIVE",
            effective_current=shadow_const.SHADOW_RUNTIME_MODE,
            consumer="shadow_cycle_entrypoint_v1",
            stage="SHADOW",
            authority="LANE",
            mutability="SHADOW_LANE_ONLY",
            shadow_relevance="LANE_IDENTITY",
            safety_relevance="LOW",
            semantic_class="SHADOW_LANE_CONFIGURATION",
        ),
        _setting(
            setting_id="SHADOW_ACTIVATION_OPERATOR_GO",
            name="Shadow runtime activation operator GO token",
            owner="canonical_shadow_runtime_enablement_v1",
            source_file="src/ops/canonical_shadow_runtime_enablement_v1/constants_v1.py",
            source_symbol="SHADOW_ACTIVATION_OPERATOR_GO",
            default_value=shadow_const.SHADOW_ACTIVATION_OPERATOR_GO,
            effective_ghv=None,
            effective_current=shadow_const.SHADOW_ACTIVATION_OPERATOR_GO,
            consumer="shadow_runtime_bridge_v1",
            stage="SHADOW_BOUNDARY",
            authority="OPERATOR",
            mutability="RUNTIME_ONLY",
            shadow_relevance="ACTIVATION",
            safety_relevance="CRITICAL",
            semantic_class="OPERATOR_AUTHORIZATION",
        ),
        _setting(
            setting_id="SHADOW_OBSERVATION_OPERATOR_GO",
            name="Shadow observation operator GO token",
            owner="canonical_shadow_runtime_enablement_v1",
            source_file="src/ops/canonical_shadow_runtime_enablement_v1/constants_v1.py",
            source_symbol="SHADOW_OBSERVATION_OPERATOR_GO",
            default_value=shadow_const.SHADOW_OBSERVATION_OPERATOR_GO,
            effective_ghv=None,
            effective_current=shadow_const.SHADOW_OBSERVATION_OPERATOR_GO,
            consumer="observation_authorization_v1",
            stage="OBSERVATION",
            authority="OPERATOR",
            mutability="RUNTIME_ONLY",
            shadow_relevance="OBSERVATION_AUTH",
            safety_relevance="CRITICAL",
            semantic_class="OPERATOR_AUTHORIZATION",
        ),
        _setting(
            setting_id="shadow_runtime_authorized",
            name="247 preflight shadow runtime authorized flag",
            owner="paper_shadow_247_preflight",
            source_file="config/ops/paper_shadow_247_preflight.toml",
            source_symbol="shadow_runtime_authorized",
            default_value=False,
            effective_ghv=False,
            effective_current=preflight.get("shadow_runtime_authorized", False),
            consumer="report_paper_shadow_247_preflight_status",
            stage="PREFLIGHT",
            authority="OPERATOR",
            mutability="CONFIG_FALSE_DEFAULT",
            shadow_relevance="247_PREFLIGHT",
            safety_relevance="CRITICAL",
            semantic_class="OPERATOR_AUTHORIZATION",
        ),
    ]
    classes = {s["SEMANTIC_CLASS"] for s in settings}
    return {
        "SETTINGS": settings,
        "SETTINGS_DISCOVERED_COUNT": len(settings),
        "PRODUCTIVE_SEMANTIC_INVARIANT_COUNT": sum(
            1 for s in settings if s["SEMANTIC_CLASS"] == "PRODUCTIVE_SEMANTIC_INVARIANT"
        ),
        "SHADOW_LANE_SETTING_COUNT": sum(
            1 for s in settings if s["SEMANTIC_CLASS"] == "SHADOW_LANE_CONFIGURATION"
        ),
        "OPERATOR_AUTHORIZATION_SETTING_COUNT": sum(
            1 for s in settings if s["SEMANTIC_CLASS"] == "OPERATOR_AUTHORIZATION"
        ),
        "SAFETY_INVARIANT_SETTING_COUNT": sum(
            1 for s in settings if s["SEMANTIC_CLASS"] == "SAFETY_INVARIANT"
        ),
        "UNKNOWN_SETTING_COUNT": sum(
            1 for s in settings if s["SEMANTIC_CLASS"] == "UNKNOWN_CURRENT"
        ),
        "SEMANTIC_CLASSES_PRESENT": sorted(classes),
    }
