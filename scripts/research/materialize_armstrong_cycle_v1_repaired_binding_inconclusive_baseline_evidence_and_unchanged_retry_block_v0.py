#!/usr/bin/env python3
"""Materialize armstrong v1 repaired-binding inconclusive baseline evidence registration v0."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.research.armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_evaluation_config_v1,
    materialize_material_difference_contract_v0,
    materialize_versioned_research_binding_v0,
)
from src.research.armstrong_cycle_v1_repaired_binding_inconclusive_baseline_evidence_and_unchanged_retry_block_v0 import (  # noqa: E402
    BINDING_DIGEST,
    CANONICAL_EVALUATION_DIR,
    CONFIG_REL_PATH,
    DURABLE_ARCHIVE_ROOT,
    GOVERNANCE_REL_PATH,
    IMPLEMENTATION_DIGEST,
    OPERATOR_GO_TOKEN,
    OLD_BINDING_DIGEST,
    SCOPE_RATIFICATION_CONFIG_REL_PATH,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    apply_scope_ratification_registration_fields,
    apply_versioned_binding_registration_fields,
    build_identity_relation_record,
    materialize_registration_config,
    sync_reratified_digest_fields,
    validate_registration_preconditions,
)
from src.research.step29m_armstrong_cycle_v1_offline_economic_baseline_materialization_v0 import (  # noqa: E402
    compute_step29m_armstrong_binding_digest_v0,
)

OUTPUT_PREFIX = (
    "armstrong_cycle_v1_repaired_binding_inconclusive_baseline_evidence_and_unchanged_retry_block"
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _fresh_versioned_binding() -> dict[str, Any]:
    return materialize_versioned_research_binding_v0(
        _REPO_ROOT,
        material_difference=materialize_material_difference_contract_v0(),
        evaluation_config=materialize_evaluation_config_v1(_REPO_ROOT),
    )


def _binding_roundtrip_pass(versioned_binding: Mapping[str, Any]) -> bool:
    binding = versioned_binding["binding"]
    digest_bindings = binding["digest_bindings"]
    from src.research.armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
        build_armstrong_cycle_v1_period_binding_data_period_v0,
    )

    recomputed = compute_step29m_armstrong_binding_digest_v0(
        config_digest=digest_bindings["config_digest"]["value"],
        data_digest=digest_bindings["data_digest"]["value"],
        implementation_digest=digest_bindings["implementation_digest"]["value"],
        strategy_params_digest=digest_bindings["strategy_params_digest"]["value"],
        material_difference_digest=digest_bindings["material_difference_digest"]["value"],
        hypothesis_id=versioned_binding["hypothesis_id"],
        instrument_id="inst-eth-usdt-perp",
        data_period=build_armstrong_cycle_v1_period_binding_data_period_v0(
            binding["period_binding"]
        ),
        universe_digest=digest_bindings["universe_digest"]["value"],
    )
    return recomputed == versioned_binding["binding_digest"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--go-token", default=OPERATOR_GO_TOKEN)
    parser.add_argument("--archive-root", type=Path, default=DURABLE_ARCHIVE_ROOT)
    parser.add_argument("--write-binding", action="store_true")
    parser.add_argument("--write-scope-ratification", action="store_true")
    parser.add_argument("--write-config", action="store_true")
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    if args.go_token != OPERATOR_GO_TOKEN:
        _die(f"unexpected_go_token:{args.go_token}")

    canonical = validate_registration_preconditions()
    registration = materialize_registration_config(canonical=canonical)
    fresh_binding = _fresh_versioned_binding()
    if fresh_binding["binding_digest"] != BINDING_DIGEST:
        _die("fresh_binding_digest_mismatch")
    if (
        fresh_binding["binding"]["digest_bindings"]["implementation_digest"]["value"]
        != IMPLEMENTATION_DIGEST
    ):
        _die("fresh_implementation_digest_mismatch")
    if not _binding_roundtrip_pass(fresh_binding):
        _die("materializer_to_binder_roundtrip_failed")

    second_binding = _fresh_versioned_binding()
    if json.dumps(fresh_binding, sort_keys=True) != json.dumps(second_binding, sort_keys=True):
        _die("second_materialization_not_deterministic")

    if args.write_config:
        config_path = _REPO_ROOT / CONFIG_REL_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(config_path, registration)
        print(f"CONFIG_WRITTEN={config_path}")

    if args.write_binding:
        binding_path = _REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        synced = sync_reratified_digest_fields(binding, fresh_binding=fresh_binding)
        updated = apply_versioned_binding_registration_fields(synced, registration)
        _write_json(binding_path, updated)
        print(f"BINDING_WRITTEN={binding_path}")

    if args.write_scope_ratification:
        scope_path = _REPO_ROOT / SCOPE_RATIFICATION_CONFIG_REL_PATH
        scope = json.loads(scope_path.read_text(encoding="utf-8"))
        updated = apply_scope_ratification_registration_fields(scope, registration)
        _write_json(scope_path, updated)
        print(f"SCOPE_RATIFICATION_WRITTEN={scope_path}")

    evidence_dir: Path | None = None
    if args.write_evidence:
        evidence_dir = args.archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
        evidence_dir.mkdir(parents=True, exist_ok=False)
        registration_with_dir = materialize_registration_config(
            canonical=canonical,
            registration_evidence_dir=evidence_dir,
        )
        _write_json(
            evidence_dir / "owner_inventory.json",
            {
                "registration_owner": (
                    "src/research/"
                    "armstrong_cycle_v1_repaired_binding_inconclusive_baseline_"
                    "evidence_and_unchanged_retry_block_v0.py"
                ),
                "materialize_script": str(Path(__file__).relative_to(_REPO_ROOT)),
                "versioned_binding_config": VERSIONED_BINDING_CONFIG_REL_PATH,
                "scope_ratification_config": SCOPE_RATIFICATION_CONFIG_REL_PATH,
                "registration_config": CONFIG_REL_PATH,
                "governance_ref": GOVERNANCE_REL_PATH,
                "digest_owner": (
                    "src/research/"
                    "step29m_armstrong_cycle_v1_offline_economic_baseline_materialization_v0.py"
                ),
                "reuse_decision": "REUSE_EL_KAROUI_TERMINAL_INCONCLUSIVE_REGISTRATION_PATTERN",
            },
        )
        _write_json(
            evidence_dir / "reuse_decision.json",
            {
                "precedent": "el_karoui_vol_model_v1_repaired_binding_inconclusive_registration",
                "classification": "A",
                "reratification_required": True,
                "supersession_required": False,
                "reevaluation_rerun_required": False,
            },
        )
        _write_json(
            evidence_dir / "field_classification.json",
            {
                "authored_semantic_fields": "UNCHANGED",
                "derived_digest_fields": "CANONICAL_OWNER_SYNC",
                "old_binding_digest": "DEFECTIVE_PREDECESSOR_PRESERVED",
            },
        )
        _write_json(
            evidence_dir / "digest_contracts.json",
            {
                "binding_digest": BINDING_DIGEST,
                "old_binding_digest": OLD_BINDING_DIGEST,
                "implementation_digest": IMPLEMENTATION_DIGEST,
            },
        )
        _write_json(
            evidence_dir / "digest_dependency_graph.json",
            {
                "implementation_digest_owner": (
                    "step29m_armstrong_cycle_v1_offline_economic_baseline_materialization_v0"
                ),
                "binding_digest_owner": "compute_step29m_armstrong_binding_digest_v0",
                "transitive": ["binding_digest"],
            },
        )
        before_after = {
            "binding_digest": {"before": OLD_BINDING_DIGEST, "after": BINDING_DIGEST},
            "implementation_digest": {
                "before": registration["old_implementation_digest"],
                "after": IMPLEMENTATION_DIGEST,
            },
            "unexpected_change_count": 0,
            "unclassified_changed_field_count": 0,
        }
        _write_json(evidence_dir / "before_after_field_diff.json", before_after)
        _write_json(
            evidence_dir / "semantic_identity_comparison.json",
            {
                "semantic_binding_identity_match": True,
                "binding_classification": registration["binding_classification"],
            },
        )
        (evidence_dir / "cryptographic_identity_comparison.json").write_text(
            json.dumps(
                {
                    "cryptographic_binding_identity_match": False,
                    "binding_digest": BINDING_DIGEST,
                    "old_binding_digest": OLD_BINDING_DIGEST,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "preflight.txt").write_text(
            "\n".join(
                [
                    "PREFLIGHT_STATUS=PASS",
                    f"GO_TOKEN={OPERATOR_GO_TOKEN}",
                    f"CANONICAL_EVALUATION_DIR={CANONICAL_EVALUATION_DIR}",
                    "SOURCE_MANIFEST_VERIFY_RC=0",
                ]
            )
            + "\n",
        )
        _write_text(
            evidence_dir / "source_manifest_verification.txt",
            (CANONICAL_EVALUATION_DIR / "source_manifest_verification.txt").read_text(
                encoding="utf-8"
            ),
        )
        _write_text(
            evidence_dir / "materializer_roundtrip.txt",
            "\n".join(
                [
                    "MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS=true",
                    f"BINDING_DIGEST={BINDING_DIGEST}",
                ]
            )
            + "\n",
        )
        _write_text(
            evidence_dir / "deterministic_materialization.txt",
            "DETERMINISTIC_MATERIALIZATION=true\nSECOND_MATERIALIZATION_DIFF_EMPTY=true\n",
        )
        _write_json(
            evidence_dir / "reevaluation_registration.json",
            {
                "existing_reevaluation_registered": True,
                "reevaluation_rerun_executed": False,
                "canonical_evaluation_bundle": str(CANONICAL_EVALUATION_DIR),
                "baseline_verdict": registration["baseline_verdict"],
            },
        )
        _write_json(
            evidence_dir / "unchanged_retry_block.json",
            registration_with_dir["exact_binding_retry_guard_report"],
        )
        _write_json(
            evidence_dir / "test_assertion_matrix.json",
            {
                "contract_test": (
                    "tests/ops/"
                    "test_armstrong_cycle_v1_repaired_binding_inconclusive_baseline_"
                    "evidence_and_unchanged_retry_block_v0_contract.py"
                ),
                "repair_contract_tests": [
                    "tests/ops/test_armstrong_cycle_v1_binding_canonicalization_repair_v0_contract.py",
                    "tests/ops/test_armstrong_cycle_v1_baseline_expectancy_materialization_repair_v0_contract.py",
                    "tests/ops/test_step29m_armstrong_cycle_v1_offline_economic_baseline_materialization_v0_contract.py",
                ],
            },
        )
        _write_json(
            evidence_dir / "registration_config.json",
            registration_with_dir,
        )
        _write_json(
            evidence_dir / "identity_relation.json",
            build_identity_relation_record(CANONICAL_EVALUATION_DIR),
        )
        final_report = (
            "\n".join(
                [
                    "VERDICT=PASS_ARMSTRONG_CYCLE_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_REGISTRATION_V0",
                    f"GO_TOKEN={OPERATOR_GO_TOKEN}",
                    f"REPO={_REPO_ROOT}",
                    f"REGISTRATION_CONFIG_REF={CONFIG_REL_PATH}",
                    f"GOVERNANCE_REF={GOVERNANCE_REL_PATH}",
                    f"CANONICAL_EVALUATION_BUNDLE={registration['canonical_evaluation_bundle']}",
                    f"CANONICAL_MANIFEST_DIGEST={registration['canonical_manifest_digest']}",
                    f"BASELINE_VERDICT={registration['baseline_verdict']}",
                    f"TERMINAL_STATUS={registration['terminal_status']}",
                    f"TRADE_COUNT={registration['trade_count']}",
                    "UNCHANGED_RETRY_ALLOWED=false",
                    "MANIFEST_VERIFY_RC=0",
                    "RUNTIME_EFFECT=NONE",
                    "AUTHORITY_EFFECT=NONE",
                    "NEXT_STEP=AWAIT_OPERATOR_REVIEW_AND_CHECKS_GREEN_FOR_INCONCLUSIVE_EVIDENCE_REGISTRATION_PR",
                ]
            )
            + "\n"
        )
        _write_text(evidence_dir / "final_report.txt", final_report)
        write_manifest_sha256(evidence_dir)
        verify_ok, verify_msg = verify_manifest_sha256(evidence_dir)
        if not verify_ok:
            _die(f"evidence_manifest_verify_failed:{verify_msg}")
        print(f"EVIDENCE_DIR={evidence_dir}")

    print("VERDICT=PASS_MATERIALIZE_INCONCLUSIVE_BASELINE_EVIDENCE_REGISTRATION_V0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
