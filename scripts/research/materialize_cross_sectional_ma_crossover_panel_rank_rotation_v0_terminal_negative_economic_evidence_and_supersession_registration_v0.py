#!/usr/bin/env python3
"""Materialize CS MA-crossover v0 terminal-negative evidence and supersession registration v0."""

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
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_terminal_negative_economic_evidence_and_supersession_registration_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    DURABLE_ARCHIVE_ROOT,
    GOVERNANCE_REL_PATH,
    OPERATOR_GO_TOKEN,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    apply_versioned_binding_registration_fields,
    materialize_registration_config,
    validate_registration_preconditions,
)

OUTPUT_PREFIX = (
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_"
    "terminal_negative_economic_evidence_and_supersession_registration"
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
    parser.add_argument("--write-config", action="store_true")
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    if args.go_token != OPERATOR_GO_TOKEN:
        _die(f"unexpected_go_token:{args.go_token}")

    original, corrected = validate_registration_preconditions()
    registration = materialize_registration_config(original=original, corrected=corrected)

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

    evidence_dir: Path | None = None
    if args.write_evidence:
        evidence_dir = args.archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
        evidence_dir.mkdir(parents=True, exist_ok=False)
        registration_with_dir = materialize_registration_config(
            original=original,
            corrected=corrected,
            registration_evidence_dir=evidence_dir,
        )
        (evidence_dir / "registration_config.json").write_text(
            json.dumps(registration_with_dir, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        final_report = (
            "\n".join(
                [
                    "VERDICT=PASS_TERMINAL_NEGATIVE_EVIDENCE_AND_SUPERSESSION_REGISTRATION_V0",
                    f"GO_TOKEN={OPERATOR_GO_TOKEN}",
                    f"REPO={_REPO_ROOT}",
                    f"REGISTRATION_CONFIG_REF={CONFIG_REL_PATH}",
                    f"GOVERNANCE_REF={GOVERNANCE_REL_PATH}",
                    f"CANONICAL_EVALUATION_BUNDLE={registration['canonical_evaluation_bundle']}",
                    f"CANONICAL_MANIFEST_DIGEST={registration['canonical_manifest_digest']}",
                    f"SUPERSEDED_EVALUATION_BUNDLE={registration['superseded_evaluation_bundle']}",
                    f"SUPERSEDED_MANIFEST_DIGEST={registration['superseded_manifest_digest']}",
                    f"REGISTRATION_DIGEST={registration_with_dir['registration_digest']}",
                    "MANIFEST_VERIFY_RC=0",
                    "RUNTIME_EFFECT=NONE",
                    "AUTHORITY_EFFECT=NONE",
                    "NEXT_STEP=AWAIT_OPERATOR_REVIEW_AND_CHECKS_GREEN_FOR_TERMINAL_NEGATIVE_SUPERSESSION_REGISTRATION_PR",
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

    print("VERDICT=PASS_MATERIALIZE_TERMINAL_NEGATIVE_SUPERSESSION_REGISTRATION_V0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
