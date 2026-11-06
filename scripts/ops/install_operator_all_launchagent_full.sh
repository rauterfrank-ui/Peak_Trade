#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "$0")/../.." && pwd)"
MODE=full ./scripts/ops/install_operator_all_launchagent.sh
