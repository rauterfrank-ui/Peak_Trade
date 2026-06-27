#!/usr/bin/env python3
"""Offline CLI for Package N experiment identity manifest producer v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.experiments.experiment_identity_manifest_v1 import (  # noqa: E402
    ExperimentIdentityManifestError,
    experiment_config_from_mapping,
    produce_experiment_identity_manifest_v1,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Produce offline experiment_identity_manifest_v1.json from ExperimentConfig JSON."
    )
    parser.add_argument(
        "--config-json",
        required=True,
        help="Path to ExperimentConfig JSON input (no runner invocation).",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory that must not exist and must be outside /tmp.",
    )
    parser.add_argument(
        "--source-experiment-id",
        default=None,
        help="Optional external provenance alias (metadata only; not identity SSOT).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config_path = Path(args.config_json)
    output_dir = Path(args.output_dir)

    if not config_path.is_file():
        print(f"config-json not found: {config_path}", file=sys.stderr)
        return 2

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        config = experiment_config_from_mapping(raw)
        artifact_path = produce_experiment_identity_manifest_v1(
            config,
            output_dir,
            source_experiment_id=args.source_experiment_id,
        )
    except ExperimentIdentityManifestError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
        print(f"invalid config-json: {exc}", file=sys.stderr)
        return 1

    print(artifact_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
