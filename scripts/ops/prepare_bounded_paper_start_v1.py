#!/usr/bin/env python3
"""Read-only input preflight for the bounded Paper path."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, DecimalException
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ops.economic_md_input_producer_v1.purpose_admission_v1 import (  # noqa: E402
    PublicFactPurposePolicyV1,
)
from src.ops.economic_md_input_producer_v1.purpose_consumers_v1 import (  # noqa: E402
    PurposeBoundPublicFactSourceV1,
    purpose_profile_digest_v1,
)
from src.ops.economic_md_input_producer_v1.validation_v1 import (  # noqa: E402
    select_finalized_contiguous_pt1m_marks_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_candidate_input_gate_v1 import (  # noqa: E402
    finalized_candidate_candle_history_rejection_codes_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (  # noqa: E402
    PublicRuntimeEconomicMdPublicSourceV1,
)
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (  # noqa: E402
    compute_b03_ratified_raw_features_pure_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (  # noqa: E402
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (  # noqa: E402
    ContractMetadataV1,
)


def _sources(raw: dict, as_of_ms: int) -> dict[str, PurposeBoundPublicFactSourceV1]:
    sources = {}
    for purpose, source in raw.items():
        fields = dict(source)
        policy = dict(fields.pop("policy"))
        for name in ("allowed_sources", "maximum_ages_seconds"):
            policy[name] = tuple(tuple(row) for row in policy[name])
        policy["finalized_kinds"] = tuple(policy["finalized_kinds"])
        sources[purpose] = PurposeBoundPublicFactSourceV1(
            **fields, policy=PublicFactPurposePolicyV1(**policy), as_of_ms=as_of_ms
        )
    return sources


def _flat_accounting(raw: dict, native_id: str) -> dict:
    if set(raw) != {"initial_equity", "contract"}:
        raise ValueError("PAPER_EXPLICIT_VIRTUAL_ACCOUNTING_REQUIRED")
    fields = dict(raw["contract"])
    if set(fields) != set(ContractMetadataV1.__dataclass_fields__) or fields["symbol"] != native_id:
        raise ValueError("PAPER_EXPLICIT_CONTRACT_METADATA_OR_INSTRUMENT_MISMATCH")
    for name in fields.keys() - {"symbol", "quote_currency", "contract_type"}:
        fields[name] = Decimal(fields[name])
    initial_equity = Decimal(raw["initial_equity"])
    session = ProductiveFuturesAccountingSessionV1(
        contract=ContractMetadataV1(**fields), initial_equity=initial_equity
    )
    portfolio = session.portfolio_state()
    return {
        "status": "VALIDATED_VIRTUAL_ACCOUNTING",
        "instrument": session.contract.symbol,
        "contract_digest": session.contract.digest(),
        "virtual_equity": str(portfolio.equity),
        "currency": session.contract.quote_currency,
        "fill_count": portfolio.fill_count,
    }


def prepare_paper_start_v1(
    *, profile: dict, accounting: dict, native_id: str, as_of_ms: int, run_root: Path
) -> dict:
    if type(as_of_ms) is not int or as_of_ms <= 0 or not native_id.strip():
        raise ValueError("PAPER_AS_OF_AND_NATIVE_INSTRUMENT_REQUIRED")
    sources = _sources(profile, as_of_ms)
    profile_digest = purpose_profile_digest_v1(sources)
    if (
        run_root.resolve() != run_root
        or run_root.exists()
        or run_root.is_relative_to(REPO_ROOT)
        or any(
            run_root.is_relative_to(Path(source.store_root))
            or Path(source.store_root).is_relative_to(run_root)
            for source in sources.values()
        )
    ):
        raise ValueError("PAPER_NEW_ISOLATED_RUN_ROOT_REQUIRED")
    canonical_ids = {source.policy.canonical_instrument_id for source in sources.values()}
    if len(canonical_ids) != 1:
        raise ValueError("PAPER_DATA_PROFILE_INSTRUMENT_MISMATCH")
    ranking = sources["RANKING"]
    result = {
        "authority": "NONE",
        "session_started": False,
        "as_of_ms": as_of_ms,
        "canonical_instrument_id": canonical_ids.pop(),
        "native_instrument_id": native_id,
        "proposed_run_root": str(run_root),
        "data_profile_digest": profile_digest,
        "checks": {},
        "launch_ready": False,
        "launch_blockers": [
            "PAPER_CORE_TO_SIMULATED_FILL_STARTER_UNBOUND",
            "PAPER_CYCLE_MARK_INDEX_OI_FUNDING_AND_COST_BINDINGS_UNVERIFIED",
        ],
    }
    checks = result["checks"]

    def trading_input() -> dict:
        payload = sources["TRADING"].trading_c1_v1(native_id=native_id)
        reasons = finalized_candidate_candle_history_rejection_codes_v1(payload)
        if reasons:
            raise ValueError(",".join(reasons))
        return {"finalized_bars": len(payload["data"])}

    for name, check in (
        ("ACCOUNTING", lambda: _flat_accounting(accounting, native_id)),
        ("TRADING", trading_input),
        (
            "LIQUIDITY",
            lambda: sources["LIQUIDITY"].liquidity_input_v1(
                native_id=native_id,
                required_features=("TOP_OF_BOOK_PRICES", "DEPTH", "ADV", "SLIPPAGE"),
            ),
        ),
    ):
        try:
            checks[name] = check()
        except (ValueError, TypeError, KeyError, OSError, RuntimeError, DecimalException) as exc:
            checks[name] = {"status": "BLOCKED", "reason": str(exc)}
    try:
        raw = PublicRuntimeEconomicMdPublicSourceV1(
            Path(ranking.store_root), ranking.policy, as_of_ms
        ).collect_instrument_raw_input_v1(venue_native_id=native_id)
        marks, failures = select_finalized_contiguous_pt1m_marks_v1(raw.marks)
        if failures:
            raise ValueError(",".join(failures))
        features = compute_b03_ratified_raw_features_pure_v1(tuple(mark.mark_px for mark in marks))
        if any(feature.raw_value is None for feature in features):
            raise ValueError("PAPER_RANKING_FEATURE_COMPUTATION_BLOCKED")
        checks["RANKING"] = {"finalized_mark_prices": len(marks)}
    except (ValueError, OSError, RuntimeError) as exc:
        checks["RANKING"] = {"status": "BLOCKED", "reason": str(exc)}
    result["input_preflight_ok"] = all(
        checks[purpose].get("status") != "BLOCKED"
        for purpose in ("ACCOUNTING", "TRADING", "RANKING")
    )
    if checks["LIQUIDITY"].get("risk_admitted") is not True:
        result["launch_blockers"].append("PAPER_LIQUIDITY_RISK_INPUT_UNPROVEN")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-profile", type=Path, required=True)
    parser.add_argument("--virtual-accounting", type=Path, required=True)
    parser.add_argument("--native-instrument", required=True)
    parser.add_argument("--as-of-ms", type=int, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = prepare_paper_start_v1(
            profile=json.loads(args.data_profile.read_bytes()),
            accounting=json.loads(args.virtual_accounting.read_bytes()),
            native_id=args.native_instrument,
            as_of_ms=args.as_of_ms,
            run_root=args.run_root,
        )
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        parser.exit(2, f"Paper input preflight stopped: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["input_preflight_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
