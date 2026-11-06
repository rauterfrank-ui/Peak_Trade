"""Bind original MI numeric readbacks before invoking the original MI evaluator.

One domain's integrity/mechanism evidence, never whole-system or economic acceptance.
No evaluator registration, promotion, Governance ACK, or Safety state is created.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.evaluation.golden_vectors.evaluators.market_intelligence_v1 import (
    MarketIntelligenceEvaluatorV1,
)
from .forecast_measurement_integration_v1 import read_calibrated_intelligence_v1
from .integration_contracts_v1 import assert_offline_v1, bytes_v1, digest_v1, require_v1, seal_v1


def intelligence_evaluation_bundle_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build exact values from already-read original artifacts, not caller-made scores."""
    frozen = packet["frozen"]
    ack = packet["calibration_ack"]
    measured = packet["measurement_inputs"]
    return {
        "TEST_ONLY_SYNTHETIC": frozen["forecast_evidence"]["provenance"].get("TEST_ONLY_SYNTHETIC")
        is True,
        "leakage_detected": False,
        "causality_proof_present": True,
        "causality_proof": {
            "frozen_digest": frozen["exact_content_digest"],
            "measurement_inputs_digest": measured["exact_content_digest"],
            "source_generation": frozen["job_key"]["dataset_generation"],
        },
        "freshness_token": digest_v1(
            {
                "as_of": frozen["context_package"]["as_of"],
                "evaluation_time": measured["evaluation_observation"]["evaluation_time_utc"],
                "source_bindings": frozen["context_package"]["source_bindings"],
            }
        ),
        "calibration_readback_digest": ack["exact_content_digest"],
        # Native GVEF replay artifacts forbid float values. Transport the full
        # original JSON bytes as a typed string, never a rounded numeric projection.
        "numeric_calibration": {
            "codec": "exact-json-values-v1",
            "utf8": bytes_v1(ack["calibration_result"]).decode("utf-8"),
            "sha256": digest_v1(ack["calibration_result"]),
        },
    }


def evaluate_exact_intelligence_v1(
    *,
    context,
    replay,
    original_sources_by_label: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Strict source admission, then actual native baseline/candidate evaluator calls."""
    assert_offline_v1()
    from src.evaluation.golden_vectors.contracts.serialization import sha256_hex

    require_v1(
        bytes_v1(context.replay_trace.model_dump(mode="json", by_alias=True))
        == bytes_v1(replay.model_dump(mode="json", by_alias=True)),
        "CONTEXT_REPLAY_MISMATCH",
    )
    require_v1(
        sha256_hex({"entries": replay.entries}) == replay.trace_digest,
        "ORIGINAL_REPLAY_DIGEST_MISMATCH",
    )
    mi_entries = [e for e in replay.entries if e.get("kind") == "market_intelligence"]
    require_v1(
        len(mi_entries) == 2 and {e.get("label") for e in mi_entries} == {"baseline", "candidate"},
        "AMBIGUOUS_MI_ENTRIES",
    )
    require_v1(
        set(original_sources_by_label) == {"baseline", "candidate"}, "EXACT_TWO_LABELS_REQUIRED"
    )
    bindings = {}
    # Admit both sides before either evaluator runs. Missing proof is not interpreted as false.
    for label in ("baseline", "candidate"):
        source = original_sources_by_label[label]
        packet = read_calibrated_intelligence_v1(
            store_root=source["store_root"], job_key=source["job_key"]
        )
        entries = [
            entry
            for entry in replay.entries
            if entry.get("kind") == "market_intelligence" and entry.get("label") == label
        ]
        require_v1(len(entries) == 1, "EXACT_ONE_MI_ENTRY_PER_LABEL_REQUIRED")
        entry = entries[0]
        require_v1(
            entry.get("run_id") == context.run_manifest.run_id, "EXPLICIT_EVALUATION_RUN_MISMATCH"
        )
        require_v1(
            bytes_v1(entry.get("mi_context_bundle"))
            == bytes_v1(intelligence_evaluation_bundle_v1(packet)),
            "EXACT_MI_BUNDLE_MISMATCH",
        )
        bindings[label] = {
            "job_key": packet["frozen"]["job_key"],
            "frozen_digest": packet["frozen"]["exact_content_digest"],
            "original_record_exact_digest": packet["calibration_ack"][
                "original_record_exact_digest"
            ],
            "numeric_calibration": packet["calibration_ack"]["calibration_result"],
        }
    # Retain native results, including their limited native evidence labels, without reinterpretation.
    evaluator = MarketIntelligenceEvaluatorV1()
    results = {
        "baseline": evaluator.evaluate_baseline(context=context, replay=replay).model_dump(
            mode="json", by_alias=True
        ),
        "candidate": evaluator.evaluate_candidate(context=context, replay=replay).model_dump(
            mode="json", by_alias=True
        ),
    }
    return seal_v1(
        {
            "schema_version": "exact_intelligence_domain_evaluation_v1",
            "authority": "NONE",
            "domain": "MARKET_INTELLIGENCE",
            "run_id": context.run_manifest.run_id,
            "evaluation_context_exact_digest": digest_v1(
                context.model_dump(mode="json", by_alias=True)
            ),
            "replay_exact_digest": digest_v1(replay.model_dump(mode="json", by_alias=True)),
            "original_numeric_bindings": bindings,
            "native_results": results,
            "claim_scope": "ORIGINAL_MI_REPLAY_MECHANISM_AND_NUMERIC_INTEGRITY_ONLY",
            "source_authenticated": False,
            "numeric_feature_usefulness_proven": False,
            "forecast_quality": "NOT_PROVEN",
            "economic_quality": "NOT_PROVEN",
            "governance_disposition": "BLOCKED_NO_EXPLICIT_RECEIVER",
            "productive_apply_authorized": False,
        }
    )
