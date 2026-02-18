#!/usr/bin/env bash
set -euo pipefail

# Build an immutable export pack (manifest + stable sha256sums).
# No execution endpoints. Data production step is a placeholder (user integrates collectors/shadow outputs).
#
# Usage:
#   scripts/ops/export_packs/build_export_pack.sh --export-id <id> --out-dir <dir>
#
# Outputs:
#   <out-dir>/export_<id>/manifest.json
#   <out-dir>/export_<id>/SHA256SUMS.stable.txt
#   <out-dir>/export_<id>/data/...

EXPORT_ID=""
OUT_DIR="out/ops/exports"
SOURCE="data_node"
SCHEMA_VERSION="v0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --export-id) EXPORT_ID="${2:-}"; shift 2 ;;
    --out-dir) OUT_DIR="${2:-}"; shift 2 ;;
    --source) SOURCE="${2:-}"; shift 2 ;;
    --schema-version) SCHEMA_VERSION="${2:-}"; shift 2 ;;
    *) echo "ERR: unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "${EXPORT_ID}" ]]; then
  echo "ERR: --export-id required" >&2
  exit 2
fi

PACK="${OUT_DIR}/export_${EXPORT_ID}"
DATA_DIR="${PACK}/data"
mkdir -p "${DATA_DIR}"

# Placeholder: user copies/produces data files into ${DATA_DIR}
# Example:
#   cp -v /path/to/collector_output/*.parquet "${DATA_DIR}/"
:
echo "INFO: data placeholder ok (no-op). Put payload files under: ${DATA_DIR}"

# Build manifest.json (minimal)
MANIFEST="${PACK}/manifest.json"
python3 - <<PY
import json
from pathlib import Path
from datetime import datetime, timezone

pack = Path("${PACK}")
data_dir = pack / "data"
files = []
for p in sorted(data_dir.rglob("*")):
    if p.is_file():
        files.append(p.relative_to(pack).as_posix())

doc = {
  "schema_version": "${SCHEMA_VERSION}",
  "export_id": "${EXPORT_ID}",
  "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
  "source": "${SOURCE}",
  "files": files,
}
(pack / "manifest.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY

# Stable SHA256SUMS (exclude itself)
(
  cd "${PACK}"
  find . -type f ! -name "SHA256SUMS.stable.txt" -print0 | LC_ALL=C sort -z \
    | xargs -0 shasum -a 256 > SHA256SUMS.stable.txt
  shasum -a 256 -c SHA256SUMS.stable.txt >/dev/null
)

echo "OK: export pack built: ${PACK}"
echo "OK: sha256 verified: ${PACK}/SHA256SUMS.stable.txt"
