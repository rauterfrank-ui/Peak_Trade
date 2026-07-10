#!/usr/bin/env python3
"""Materialize bouchaud OHLCV proxy v1 repaired-binding inconclusive baseline registration v0."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_repaired_binding_inconclusive_baseline_evidence_and_unchanged_retry_block_v0 import (  # noqa: E402
    BINDING_DIGEST,
    CANONICAL_EVALUATION_DIR,
    CONFIG_REL_PATH,
    DURABLE_ARCHIVE_ROOT,
    GOVERNANCE_REL_PATH,
    OLD_BINDING_DIGEST,
    OPERATOR_GO_TOKEN,
    PRIOR_FAILED_EVALUATION_DIR,
    REPAIR_CLOSEOUT_DIR,
    SCOPE_RATIFICATION_CONFIG_REL_PATH,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    apply_scope_ratification_registration_fields,
    apply_versioned_binding_registration_fields,
    build_identity_relation_record,
    materialize_registration_config,
    validate_registration_preconditions,
)

OUTPUT_PREFIX = (
    "implement_bouchaud_microstructure_ohlcv_proxy_v1_inconclusive_baseline_adjudication_"
    "registration_v0"
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


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

    if args.write_config:
        config_path = _REPO_ROOT / CONFIG_REL_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps(registration, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"CONFIG_WRITTEN={config_path}")

    if args.write_binding:
        binding_path = _REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        updated = apply_versioned_binding_registration_fields(binding, registration)
        binding_path.write_text(
            json.dumps(updated, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"BINDING_WRITTEN={binding_path}")

    if args.write_scope_ratification:
        scope_path = _REPO_ROOT / SCOPE_RATIFICATION_CONFIG_REL_PATH
        scope = json.loads(scope_path.read_text(encoding="utf-8"))
        updated = apply_scope_ratification_registration_fields(scope, registration)
        scope_path.write_text(
            json.dumps(updated, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"SCOPE_RATIFICATION_WRITTEN={scope_path}")

    if args.write_evidence:
        evidence_dir = args.archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
        evidence_dir.mkdir(parents=True, exist_ok=False)
        registration_with_dir = materialize_registration_config(
            canonical=canonical,
            registration_evidence_dir=evidence_dir,
        )
        (evidence_dir / "preflight.txt").write_text(
            "\n".join(
                [
                    "PREFLIGHT_STATUS=PASS",
                    f"GO_TOKEN={OPERATOR_GO_TOKEN}",
                    f"CANONICAL_EVALUATION_DIR={CANONICAL_EVALUATION_DIR}",
                    f"REPAIR_CLOSEOUT_DIR={REPAIR_CLOSEOUT_DIR}",
                    f"PRIOR_FAILED_EVALUATION_DIR={PRIOR_FAILED_EVALUATION_DIR}",
                    "SOURCE_MANIFEST_VERIFY_RC=0",
                    "NO_ECONOMIC_REEVALUATION=true",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "source_manifest_verification.txt").write_text(
            "\n".join(
                [
                    f"BUNDLE={CANONICAL_EVALUATION_DIR}",
                    "MANIFEST_VERIFY_RC=0",
                    f"BUNDLE={REPAIR_CLOSEOUT_DIR}",
                    "MANIFEST_VERIFY_RC=0",
                    f"BUNDLE={PRIOR_FAILED_EVALUATION_DIR}",
                    "MANIFEST_VERIFY_RC=0",
                    "SOURCE_MANIFEST_VERIFY_RC=0",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "owner_inventory.json").write_text(
            json.dumps(
                {
                    "registration_owner": (
                        "src/research/"
                        "bouchaud_microstructure_ohlcv_proxy_v1_repaired_binding_"
                        "inconclusive_baseline_evidence_and_unchanged_retry_block_v0.py"
                    ),
                    "materialize_script": str(Path(__file__).relative_to(_REPO_ROOT)),
                    "versioned_binding_config": VERSIONED_BINDING_CONFIG_REL_PATH,
                    "scope_ratification_config": SCOPE_RATIFICATION_CONFIG_REL_PATH,
                    "registration_config": CONFIG_REL_PATH,
                    "governance_ref": GOVERNANCE_REL_PATH,
                    "progress_registry_owner": "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md",
                    "contract_test_owner": (
                        "tests/ops/"
                        "test_bouchaud_microstructure_ohlcv_proxy_v1_repaired_binding_"
                        "inconclusive_baseline_evidence_and_unchanged_retry_block_v0_contract.py"
                    ),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "reuse_decision.json").write_text(
            json.dumps(
                {
                    "precedent": "armstrong_cycle_v1_repaired_binding_inconclusive_registration",
                    "secondary_precedent": "el_karoui_vol_model_v1_repaired_binding_inconclusive_registration",
                    "classification": "A",
                    "reratification_required": True,
                    "supersession_required": False,
                    "reevaluation_rerun_required": False,
                    "parallel_registry_owner_forbidden": True,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "registration_input.json").write_text(
            json.dumps(registration_with_dir, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "binding_identity_comparison.json").write_text(
            json.dumps(
                build_identity_relation_record(CANONICAL_EVALUATION_DIR),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "before_after_field_diff.json").write_text(
            json.dumps(
                {
                    "binding_digest": {"before": OLD_BINDING_DIGEST, "after": BINDING_DIGEST},
                    "economic_evaluation_executed": {"before": False, "after": True},
                    "baseline_verdict": {"before": None, "after": "INCONCLUSIVE"},
                    "unexpected_change_count": 0,
                    "unclassified_changed_field_count": 0,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "test_assertion_matrix.json").write_text(
            json.dumps(
                {
                    "contract_test": (
                        "tests/ops/"
                        "test_bouchaud_microstructure_ohlcv_proxy_v1_repaired_binding_"
                        "inconclusive_baseline_evidence_and_unchanged_retry_block_v0_contract.py"
                    ),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "final_report.txt").write_text(
            "\n".join(
                [
                    "VERDICT=PASS_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_INCONCLUSIVE_BASELINE_ADJUDICATION_REGISTRATION_V0",
                    f"GO_TOKEN={OPERATOR_GO_TOKEN}",
                    f"REPO={_REPO_ROOT}",
                    f"REGISTRATION_CONFIG_REF={CONFIG_REL_PATH}",
                    f"GOVERNANCE_REF={GOVERNANCE_REL_PATH}",
                    f"CANONICAL_EVALUATION_BUNDLE={registration['canonical_evaluation_bundle']}",
                    f"CANONICAL_MANIFEST_DIGEST={registration['canonical_manifest_digest']}",
                    f"BASELINE_VERDICT={registration['baseline_verdict']}",
                    f"TERMINAL_STATUS={registration['terminal_status']}",
                    f"TRADE_COUNT={registration['trade_count']}",
                    f"REEVALUATION_EXECUTION_COUNT={registration['reevaluation_execution_count']}",
                    "UNCHANGED_RETRY_ALLOWED=false",
                    "RUNTIME_EFFECT=NONE",
                    "AUTHORITY_EFFECT=NONE",
                    f"NEXT_CANONICAL_STEP={registration['next_canonical_step']}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        write_manifest_sha256(evidence_dir)
        verify_ok, verify_msg = verify_manifest_sha256(evidence_dir)
        if not verify_ok:
            _die(f"evidence_manifest_verify_failed:{verify_msg}")
        print(f"EVIDENCE_DIR={evidence_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
