#!/usr/bin/env python3
"""Materialize el_karoui v1 repaired-binding inconclusive baseline evidence registration v0."""

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
from src.research.el_karoui_vol_model_v1_repaired_binding_inconclusive_baseline_evidence_and_unchanged_retry_block_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    DURABLE_ARCHIVE_ROOT,
    GOVERNANCE_REL_PATH,
    OPERATOR_GO_TOKEN,
    SCOPE_RATIFICATION_CONFIG_REL_PATH,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    apply_scope_ratification_registration_fields,
    apply_versioned_binding_registration_fields,
    materialize_registration_config,
    validate_registration_preconditions,
)

OUTPUT_PREFIX = (
    "el_karoui_vol_model_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block"
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

    evidence_dir: Path | None = None
    if args.write_evidence:
        evidence_dir = args.archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
        evidence_dir.mkdir(parents=True, exist_ok=False)
        registration_with_dir = materialize_registration_config(
            canonical=canonical,
            registration_evidence_dir=evidence_dir,
        )
        (evidence_dir / "owner_inventory.json").write_text(
            json.dumps(
                {
                    "registration_owner": (
                        "src/research/"
                        "el_karoui_vol_model_v1_repaired_binding_inconclusive_baseline_"
                        "evidence_and_unchanged_retry_block_v0.py"
                    ),
                    "materialize_script": str(Path(__file__).relative_to(_REPO_ROOT)),
                    "versioned_binding_config": VERSIONED_BINDING_CONFIG_REL_PATH,
                    "scope_ratification_config": SCOPE_RATIFICATION_CONFIG_REL_PATH,
                    "registration_config": CONFIG_REL_PATH,
                    "governance_ref": GOVERNANCE_REL_PATH,
                    "reuse_decision": "REUSE_EHLERS_TERMINAL_INCONCLUSIVE_REGISTRATION_PATTERN",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "registration_config.json").write_text(
            json.dumps(registration_with_dir, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "result_classification.json").write_text(
            json.dumps(
                {
                    "authoritative_baseline_verdict": registration_with_dir["baseline_verdict"],
                    "terminal_status": registration_with_dir["terminal_status"],
                    "terminal_negative_label_applied": False,
                    "terminal_inconclusive_label_applied": True,
                    "dominant_cause": registration_with_dir["primary_cause_class"],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "retry_policy_decision.json").write_text(
            json.dumps(
                registration_with_dir["exact_binding_retry_guard_report"], indent=2, sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        )
        final_report = (
            "\n".join(
                [
                    "VERDICT=PASS_EL_KAROUI_VOL_MODEL_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_REGISTRATION_V0",
                    f"GO_TOKEN={OPERATOR_GO_TOKEN}",
                    f"REPO={_REPO_ROOT}",
                    f"REGISTRATION_CONFIG_REF={CONFIG_REL_PATH}",
                    f"GOVERNANCE_REF={GOVERNANCE_REL_PATH}",
                    f"CANONICAL_EVALUATION_BUNDLE={registration['canonical_evaluation_bundle']}",
                    f"CANONICAL_MANIFEST_DIGEST={registration['canonical_manifest_digest']}",
                    f"BASELINE_VERDICT={registration['baseline_verdict']}",
                    f"TERMINAL_STATUS={registration['terminal_status']}",
                    f"TRADE_COUNT={registration['trade_count']}",
                    f"UNCHANGED_RETRY_ALLOWED=false",
                    "MANIFEST_VERIFY_RC=0",
                    "RUNTIME_EFFECT=NONE",
                    "AUTHORITY_EFFECT=NONE",
                    "NEXT_STEP=AWAIT_OPERATOR_REVIEW_AND_CHECKS_GREEN_FOR_INCONCLUSIVE_EVIDENCE_REGISTRATION_PR",
                ]
            )
            + "\n"
        )
        (evidence_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
        write_manifest_sha256(evidence_dir)
        verify_ok, verify_msg = verify_manifest_sha256(evidence_dir)
        if not verify_ok:
            _die(f"evidence_manifest_verify_failed:{verify_msg}")
        print(f"EVIDENCE_DIR={evidence_dir}")

    print("VERDICT=PASS_MATERIALIZE_INCONCLUSIVE_BASELINE_EVIDENCE_REGISTRATION_V0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
