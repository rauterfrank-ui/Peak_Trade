"""Shadow Preparation Readiness offline operator entrypoint v0.

Invokes the canonical offline projection pipeline exactly once and exposes
PASS / BLOCKED / ERROR via process exit codes and text/json stdout.

Non-activating. Not a scheduler or runtime entrypoint.
No Shadow/Paper/Testnet/Runtime/Scheduler/Orders/Live side effects.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence, TextIO

from src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0 import (
    PIPELINE_STATUS_BLOCKED,
    PIPELINE_STATUS_ERROR,
    PIPELINE_STATUS_PASS,
    ShadowPreparationReadinessOfflineProjectionPipelineResultV0,
    run_shadow_preparation_readiness_offline_projection_pipeline_v0,
)

PACKAGE_MARKER = "SHADOW_PREPARATION_READINESS_OFFLINE_OPERATOR_ENTRYPOINT_V0=true"
PRODUCER_FAMILY = "ops.shadow_preparation_readiness_offline_operator_entrypoint_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"

EXIT_PASS = 0
EXIT_ERROR = 1
EXIT_BLOCKED = 2


def exit_code_for_pipeline_result(
    result: ShadowPreparationReadinessOfflineProjectionPipelineResultV0,
) -> int:
    """Map canonical pipeline status to stable process exit codes."""
    if result.pipeline_status == PIPELINE_STATUS_PASS:
        return EXIT_PASS
    if result.pipeline_status == PIPELINE_STATUS_BLOCKED:
        return EXIT_BLOCKED
    return EXIT_ERROR


def format_text_result(
    result: ShadowPreparationReadinessOfflineProjectionPipelineResultV0,
) -> str:
    """Human-readable, deterministic summary; no stack traces for BLOCKED."""
    lines = [
        f"status={result.pipeline_status}",
        f"readiness_status={result.readiness_status}",
        f"projection_path={result.projection_path}",
        f"verification_status={result.verification_status}",
        f"verification_verified={result.verification_verified}",
        f"evaluated_at={result.evaluated_at}",
        f"authority_effect=NONE",
        f"activation_authority=false",
        f"projection_only=true",
    ]
    if result.reason_codes:
        lines.append(f"reason_codes={','.join(result.reason_codes)}")
    else:
        lines.append("reason_codes=")
    return "\n".join(lines) + "\n"


def format_json_result(
    result: ShadowPreparationReadinessOfflineProjectionPipelineResultV0,
) -> str:
    """Emit the canonical pipeline result dict; no second semantic truth."""
    return (
        json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0",
        description=(
            "Offline operator entrypoint for Shadow Preparation Readiness "
            "projection pipeline v0. Non-activating; not a scheduler/runtime entrypoint."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        required=True,
        help="Repository root used for gate evaluation and projection I/O.",
    )
    parser.add_argument(
        "--output-path",
        default=None,
        help="Optional relative projection output path (repo-rooted).",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        default=None,
        help="Optional path to readiness gate config TOML.",
    )
    parser.add_argument(
        "--evaluated-at",
        default=None,
        help="Optional ISO-8601 evaluation timestamp passed to the pipeline.",
    )
    parser.add_argument(
        "--as-of",
        default=None,
        help="Optional ISO-8601 verifier as-of timestamp passed to the pipeline.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="output_format",
        help="Stdout format: text (default) or json.",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Parse args, invoke the canonical pipeline once, emit result, return exit code."""
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    parser = build_arg_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:
        # argparse uses exit code 2 for usage errors; map to ERROR (1) so BLOCKED
        # remains uniquely exit 2. Do not run the pipeline.
        code = exc.code
        if code in (None, 0):
            return EXIT_PASS
        return EXIT_ERROR

    repo_root = Path(args.repo_root)
    if not repo_root.is_dir():
        print(f"status={PIPELINE_STATUS_ERROR}", file=out)
        print(f"reason_codes=ENTRYPOINT_REPO_ROOT_INVALID:{repo_root}", file=out)
        return EXIT_ERROR

    result = run_shadow_preparation_readiness_offline_projection_pipeline_v0(
        repo_root=repo_root,
        output_path=args.output_path,
        config_path=args.config_path,
        evaluated_at=args.evaluated_at,
        as_of=args.as_of,
    )

    if args.output_format == "json":
        out.write(format_json_result(result))
    else:
        out.write(format_text_result(result))

    # Never reinterpret BLOCKED as success.
    code = exit_code_for_pipeline_result(result)
    if code == EXIT_BLOCKED:
        # Explicit non-authorization reminder on stderr (no stack trace).
        print(
            "BLOCKED authorizes nothing; no Shadow/Paper/Testnet/Scheduler/Runtime activation.",
            file=err,
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "EXIT_BLOCKED",
    "EXIT_ERROR",
    "EXIT_PASS",
    "PACKAGE_MARKER",
    "PRODUCER_FAMILY",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "build_arg_parser",
    "exit_code_for_pipeline_result",
    "format_json_result",
    "format_text_result",
    "main",
]
