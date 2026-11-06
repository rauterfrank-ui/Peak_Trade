"""Compute research stratification v2 from CURRENT inputs."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.constants_v2 import (
    BLOCKER_CMC_PROVENANCE_INCOMPLETE,
    BLOCKER_MARKET_STATE_PARAMETER_AUTHORITY_UNSET,
    BLOCKER_VOLATILITY_PARAMETER_AUTHORITY_UNSET,
    RESEARCH_STRATIFICATION_CONTRACT_VERSION,
    VOLATILITY_INPUT_AUTHORITY,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.mark_path_v2 import (
    realized_vol_sample_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.models_v2 import (
    CmcVolatilityInputProvenanceV2,
    ResearchStratificationResultV2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.parameter_authority_v2 import (
    ParameterAuthorityEntryV2,
    entries_as_map,
    parameter_authority_complete_v2,
    parameter_authority_digest_v2,
    verify_parameter_digest_v2,
)


def _classify_volatility_stratum_v2(
    *,
    vol: float,
    params: Mapping[str, ParameterAuthorityEntryV2],
) -> tuple[str, tuple[str, ...]]:
    low = params.get("volatility_stratum_low_threshold")
    high = params.get("volatility_stratum_high_threshold")
    if (
        low is None
        or high is None
        or low.authority_status != "RATIFIED"
        or low.value is None
        or high.value is None
    ):
        return "UNKNOWN", (BLOCKER_VOLATILITY_PARAMETER_AUTHORITY_UNSET,)
    lv = float(low.value)
    hv = float(high.value)
    if vol < lv:
        return "LOW_VOLATILITY_STRATUM", ()
    if vol >= hv:
        return "HIGH_VOLATILITY_STRATUM", ()
    return "MID_VOLATILITY_STRATUM", ()


def _classify_market_state_stratum_v2(
    *,
    mark_prices: Sequence[float],
    params: Mapping[str, ParameterAuthorityEntryV2],
) -> tuple[str, tuple[str, ...]]:
    lookback = params.get("research_mark_path_lookback_observations")
    min_obs = params.get("minimum_mark_path_observations")
    low = params.get("market_state_realized_vol_low_threshold")
    high = params.get("market_state_realized_vol_high_threshold")
    if (
        lookback is None
        or min_obs is None
        or low is None
        or high is None
        or lookback.authority_status != "RATIFIED"
    ):
        return "UNKNOWN", (BLOCKER_MARKET_STATE_PARAMETER_AUTHORITY_UNSET,)
    if any(p.value is None for p in (lookback, min_obs, low, high)):
        return "UNKNOWN", (BLOCKER_MARKET_STATE_PARAMETER_AUTHORITY_UNSET,)
    window = int(lookback.value)
    min_n = int(min_obs.value)
    if len(mark_prices) < min_n:
        return "INSUFFICIENT_DATA", ()
    path = list(mark_prices)[-window:]
    rv = realized_vol_sample_v2(path)
    if rv is None:
        return "INSUFFICIENT_DATA", ()
    lv = float(low.value)
    hv = float(high.value)
    if rv < lv:
        return "LOW_REALIZED_VOL_STATE", ()
    if rv >= hv:
        return "HIGH_REALIZED_VOL_STATE", ()
    return "MID_REALIZED_VOL_STATE", ()


def compute_research_stratification_v2(
    *,
    cmc: CmcVolatilityInputProvenanceV2 | None,
    mark_prices: Sequence[float],
    parameter_entries: Sequence[ParameterAuthorityEntryV2],
    expected_parameter_digest: str | None,
    legacy_regime_label_v1: str | None = None,
) -> ResearchStratificationResultV2:
    blockers: list[str] = []
    param_digest = parameter_authority_digest_v2(parameter_entries)
    param_provenance = {
        "parameter_digest": param_digest,
        "parameter_authority_complete": parameter_authority_complete_v2(parameter_entries),
    }
    if expected_parameter_digest and not verify_parameter_digest_v2(
        entries=parameter_entries, expected_digest=expected_parameter_digest
    ):
        blockers.append("STRATIFICATION_PARAMETER_DIGEST_MISMATCH")

    if cmc is None or not cmc.volatility_source_digest:
        blockers.append(BLOCKER_CMC_PROVENANCE_INCOMPLETE)
        vol_stratum = "MISSING"
        market_stratum = "MISSING"
    elif not parameter_authority_complete_v2(parameter_entries):
        vol_stratum = "UNKNOWN"
        market_stratum = "UNKNOWN"
        blockers.append(BLOCKER_VOLATILITY_PARAMETER_AUTHORITY_UNSET)
        blockers.append(BLOCKER_MARKET_STATE_PARAMETER_AUTHORITY_UNSET)
    else:
        params = entries_as_map(parameter_entries)
        vol_stratum, vol_blockers = _classify_volatility_stratum_v2(
            vol=float(cmc.volatility_value), params=params
        )
        market_stratum, mkt_blockers = _classify_market_state_stratum_v2(
            mark_prices=mark_prices, params=params
        )
        blockers.extend(vol_blockers)
        blockers.extend(mkt_blockers)

    blockers = sorted(set(blockers))
    ok = (
        not blockers
        and vol_stratum not in {"UNKNOWN", "MISSING", "INSUFFICIENT_DATA", "UNCLASSIFIED"}
        and market_stratum not in {"UNKNOWN", "MISSING", "INSUFFICIENT_DATA", "UNCLASSIFIED"}
    )
    key = (
        f"{RESEARCH_STRATIFICATION_CONTRACT_VERSION}|{vol_stratum}|{market_stratum}"
        if ok
        else f"{RESEARCH_STRATIFICATION_CONTRACT_VERSION}|FAIL_CLOSED"
    )
    return ResearchStratificationResultV2(
        research_stratification_version=RESEARCH_STRATIFICATION_CONTRACT_VERSION,
        volatility_regime_stratum_v2=vol_stratum,
        market_state_stratum_v2=market_stratum,
        stratification_key_v2=key,
        stratification_ok=ok,
        stratification_blockers=tuple(blockers),
        input_provenance={
            "cmc_volatility": None if cmc is None else cmc.to_dict(),
            "cmc_input_authority": VOLATILITY_INPUT_AUTHORITY,
            "mark_path_len": len(mark_prices),
        },
        parameter_authority_provenance=param_provenance,
        legacy_regime_label_v1=legacy_regime_label_v1,
        legacy_regime_label_is_v1=True,
    )


def cmc_from_cycle_binding_v2(cycle: Mapping[str, Any]) -> CmcVolatilityInputProvenanceV2 | None:
    binding = dict(cycle.get("canonical_volatility_typed_binding") or {})
    value = binding.get("volatility_value")
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    unit = str(binding.get("volatility_unit") or "")
    horizon = binding.get("volatility_horizon_seconds")
    obs = binding.get("observation_count")
    est = str(binding.get("volatility_estimator") or binding.get("estimator") or "")
    digest = str(binding.get("source_digest") or "")
    if not unit or horizon is None or obs is None or not digest:
        return None
    return CmcVolatilityInputProvenanceV2(
        volatility_value=numeric,
        volatility_unit=unit,
        volatility_horizon_seconds=float(horizon),
        volatility_estimator=est,
        volatility_observation_count=int(obs),
        volatility_source_digest=digest,
    )
