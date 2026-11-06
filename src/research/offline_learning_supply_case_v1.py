"""Bounded captured-evaluation → learning → optimization intake experiment.

This composes existing contracts on a private ledger copy. It does not recreate
missing market observations, assign economic labels, or start optimization.
Run with ``./scripts/pt -m src.research.offline_learning_supply_case_v1``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    ingest_evaluation_bundle_into_learning_state_v1,
    validate_evaluation_bundle_for_ingest_v1,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("TIMEZONE_REQUIRED")
    return parsed


def _one_linked(rows: tuple, schema: str, outcome_id: str) -> Mapping[str, Any]:
    matches = [
        row
        for row in rows
        if row["schema_name"] == schema and row.get("outcome_record_ref") == outcome_id
    ]
    if len(matches) != 1:
        raise ValueError(f"EXPECTED_ONE_LINKED_RECORD:{schema}:{outcome_id}:{len(matches)}")
    return matches[0]


def _select_bundles(rows: tuple, outcome_ids: list[str]) -> list[dict[str, Any]]:
    if not outcome_ids or len(set(outcome_ids)) != len(outcome_ids):
        raise ValueError("EXPLICIT_UNIQUE_OUTCOME_IDS_REQUIRED")
    by_id = {str(row["record_id"]): row for row in rows}
    bundles = []
    previous_time = None
    for outcome_id in outcome_ids:
        outcome = by_id[outcome_id]
        attribution = _one_linked(rows, "attribution_record", outcome_id)
        counterfactual = _one_linked(rows, "counterfactual_record", outcome_id)
        bundle = validate_evaluation_bundle_for_ingest_v1(outcome, attribution, counterfactual)
        decision = by_id[str(outcome["decision_event_ref"])]
        if decision["schema_name"] != "decision_event":
            raise ValueError("DECISION_RECORD_REQUIRED")
        for record in (attribution, counterfactual):
            if record.get("decision_event_ref") != decision["record_id"]:
                raise ValueError("BUNDLE_DECISION_REF_MISMATCH")
        outcome_time = _time(str(outcome["event_time_utc"]))
        if outcome_time < _time(str(decision["event_time_utc"])):
            raise ValueError("OUTCOME_PRECEDES_DECISION")
        if previous_time is not None and outcome_time < previous_time:
            raise ValueError("OUTCOMES_NOT_CHRONOLOGICAL")
        previous_time = outcome_time
        bundles.append({**bundle, "decision": dict(decision)})
    return bundles


def run_case(manifest: Mapping[str, Any], output: Path) -> dict[str, Any]:
    """Replay an explicitly selected suffix; always leave upstream proof open.

    Exit/result semantics distinguish contract acceptance from data sufficiency.
    Diagnostic missing-fields are observations, not a new admission policy.
    """
    source = Path(manifest["source_ledger"]).resolve(strict=True)
    output = output.resolve()
    if output == source.parent or output.is_relative_to(source.parent):
        raise ValueError("OUTPUT_MUST_BE_OUTSIDE_SOURCE_DIRECTORY")
    if manifest["source_kind"] not in {"HISTORICAL_CAPTURE", "TEST_FIXTURE"}:
        raise ValueError("EXPLICIT_SOURCE_KIND_REQUIRED")
    captured = source.read_bytes()
    source_digest = _sha(captured)
    if source_digest != manifest["source_sha256"]:
        raise ValueError("SOURCE_SHA256_MISMATCH")
    case_id = str(manifest["case_id"])
    if not case_id.strip():
        raise ValueError("CASE_ID_REQUIRED")
    # Exclusive directory creation prevents accidental reuse/overwrite.
    output.mkdir(parents=True, exist_ok=False)
    _write_json(output / "request.json", dict(manifest))
    snapshot = output / "source_snapshot.jsonl"
    snapshot.write_bytes(captured)
    rows = AppendOnlyDdoLedgerV0(snapshot).read_all()
    bundles = _select_bundles(rows, list(manifest["outcome_ids"]))
    scope = "ddo.lscope.offline-case." + _sha(f"{case_id}|{source_digest}".encode())[:32]
    if any(row.get("state_scope_id") == scope for row in rows):
        raise ValueError("PILOT_SCOPE_ALREADY_PRESENT_IN_SOURCE")
    working_path = output / "pilot_ledger.jsonl"
    working_path.write_bytes(captured)
    ledger = AppendOnlyDdoLedgerV0(working_path)
    results = []
    for index, bundle in enumerate(bundles, start=1):
        outcome = bundle["outcome"]
        decision = bundle["decision"]
        ingest = ingest_evaluation_bundle_into_learning_state_v1(
            ledger,
            state_scope_id=scope,
            outcome=outcome,
            attribution=bundle["attribution"],
            counterfactual=bundle["counterfactual"],
            event_time_utc=outcome["event_time_utc"],
            correlation_id=f"offline-case:{case_id}:{index}",
        )
        state = ingest["learning_state_record"]
        evidence = export_learning_evidence_from_state_v1(state)
        intake = dict(
            validate_canonical_optimization_universe_learning_input_v1(
                CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
            )
        )
        provenance = outcome["outcome_evidence_provenance"]
        missing = [
            key
            for key in (
                "instrument_id",
                "venue_native_id",
                "lineage_digest",
                "ddo_ledger_environment",
                "trading_epoch",
                "market_timestamp_utc",
            )
            if provenance.get(key) in (None, "", "UNKNOWN")
        ]
        trace = {
            "decision_id": decision["record_id"],
            "decision_time_utc": decision["event_time_utc"],
            "selected_instrument_ref": decision.get("selected_instrument_ref"),
            "outcome_id": outcome["record_id"],
            "outcome_time_utc": outcome["event_time_utc"],
            "evaluation_horizon": outcome["evaluation_horizon"],
            "actual_outcome_ref": outcome.get("actual_outcome_ref"),
            "evaluation_information_set_ref": bundle["counterfactual"].get(
                "evaluation_time_information_set_ref"
            ),
            "outcome_source_code_sha": outcome.get("code_sha"),
            "outcome_source_config_hash": outcome.get("config_hash"),
            "provenance": provenance,
            "missing_provenance_fields": missing,
            "economic_label_before": outcome.get("economic_score"),
            "economic_label_after": evidence["economic_score_label"],
            "new_learning_state_id": state["record_id"],
            "state_version": state["state_version"],
            "bundle_fingerprint": bundle["evaluation_bundle_fingerprint"],
            "idempotent_replay": ingest["idempotent_replay"],
            "intake": intake,
        }
        _write_json(output / f"{index:03d}_learning_state.json", state)
        _write_json(output / f"{index:03d}_learning_evidence.json", evidence)
        results.append(trace)
    ledger.verify_integrity()
    if _sha(source.read_bytes()) != source_digest:
        raise ValueError("SOURCE_CHANGED_DURING_CASE")
    if snapshot.read_bytes() != captured:
        raise ValueError("SOURCE_SNAPSHOT_CHANGED")
    repo = Path(__file__).resolve().parents[2]
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    loaded_sources = {
        name: {"path": module.__file__, "sha256": _sha(Path(module.__file__).read_bytes())}
        for name, module in list(sys.modules.items())
        if name.startswith(("src.learning.deterministic_decision_outcome_v0", "src.experiments"))
        and getattr(module, "__file__", None)
        and str(module.__file__).endswith(".py")
    }
    loaded_sources[__name__] = {"path": __file__, "sha256": _sha(Path(__file__).read_bytes())}
    accepted = all(
        result["intake"]["status"] == STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT for result in results
    )
    report = {
        "schema_version": "offline_learning_supply_case_v1",
        "case_id": case_id,
        "source_kind": manifest["source_kind"],
        "source_ledger": str(source),
        "source_sha256": source_digest,
        "source_record_count": len(rows),
        "source_unchanged": True,
        "code_revision": revision,
        "loaded_source_files": loaded_sources,
        "executed_boundary": "CAPTURED_EVALUATION_BUNDLE_TO_OPTIMIZATION_INTAKE",
        "suffix_status": "PASS" if accepted else "REJECTED_BY_CANONICAL_INTAKE",
        "upstream_recalculation_status": "NOT_TESTED_SOURCE_OBSERVATIONS_NOT_SUPPLIED",
        "end_to_end_supply_status": "NOT_PROVEN",
        "search_effect_status": "NOT_TESTED",
        "productive_authority": "NONE",
        "external_effect_authorized": False,
        "new_state_scope_id": scope,
        "results": results,
    }
    _write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run_case(json.loads(args.manifest.read_text()), args.output)
    except Exception as exc:
        print(f"CASE_FAILED:{type(exc).__name__}:{exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                key: report[key]
                for key in ("suffix_status", "end_to_end_supply_status", "source_unchanged")
            }
        )
    )
    # 2 explicitly means the end-to-end supply remains unproven, even if intake accepts.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
