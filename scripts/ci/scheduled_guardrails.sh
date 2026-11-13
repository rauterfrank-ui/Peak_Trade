#!/usr/bin/env bash
set -euo pipefail

if [ -z "${PT_SCHEDULED_PAPER_TESTS_ENABLED:-}" ]; then
  echo "MISSING_REQUIRED_VAR=PT_SCHEDULED_PAPER_TESTS_ENABLED" >&2
  exit 1
fi

echo "GUARDRAILS: ok (paper only)"
