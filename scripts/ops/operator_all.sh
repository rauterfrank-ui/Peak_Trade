#!/usr/bin/env bash
set -euo pipefail

cd "$(cd "$(dirname "$0")/../.." && pwd)"

RUN_E2E="${RUN_E2E:-true}"
RUN_ONE_SHOT="${RUN_ONE_SHOT:-true}"
RUN_REGISTRY="${RUN_REGISTRY:-true}"
STRICT_ALERTS="${STRICT_ALERTS:-false}"

echo "OPERATOR_ALL"
echo "RUN_E2E=${RUN_E2E}"
echo "RUN_ONE_SHOT=${RUN_ONE_SHOT}"
echo "RUN_REGISTRY=${RUN_REGISTRY}"
echo "STRICT_ALERTS=${STRICT_ALERTS}"

if [ "${RUN_E2E}" = "true" ] && [ -x "./scripts/ops/run_end_to_end_verification.sh" ]; then
  ./scripts/ops/run_end_to_end_verification.sh
fi

if [ "${RUN_ONE_SHOT}" = "true" ] && [ -x "./scripts/ops/run_morning_one_shot.sh" ]; then
  ./scripts/ops/run_morning_one_shot.sh
fi

if [ "${RUN_REGISTRY}" = "true" ] && [ -x "./scripts/ops/run_registry_suite.sh" ]; then
  STRICT_ALERTS="${STRICT_ALERTS}" ./scripts/ops/run_registry_suite.sh
fi

if [ -x "./scripts/ops/ops_status.sh" ]; then
  ./scripts/ops/ops_status.sh
fi

echo "DONE: operator_all"
