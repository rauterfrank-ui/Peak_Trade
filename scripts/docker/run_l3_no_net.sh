#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-peaktrade-l3:latest}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${OUT_DIR:-${REPO_ROOT}/out/l3}"
CACHE_DIR="${CACHE_DIR:-${REPO_ROOT}/.cache/l3}"

mkdir -p "${OUT_DIR}" "${CACHE_DIR}"

docker run --rm \
  --name peaktrade-l3 \
  --network=none \
  --cpus="${CPUS:-2}" --memory="${MEM:-4g}" \
  -v "${REPO_ROOT}:/work:ro" \
  -v "${OUT_DIR}:/out:rw" \
  -v "${CACHE_DIR}:/cache:rw" \
  -w /work \
  "${IMAGE}" \
  bash -lc '
    set -euo pipefail
    # Deps are installed in the image at build time (no network at run time).
    python3 scripts/aiops/run_layer_dry_run.py \
      --layer L3 \
      --primary "${PRIMARY_MODEL:-gpt-5.2-pro}" \
      --critic "${CRITIC_MODEL:-o3}" \
      --out /out
  '
