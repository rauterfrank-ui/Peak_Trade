#!/usr/bin/env bash
# Read-only Docker Desktop preflight checks. No changes, no Docker start.
# See: docs/ops/runbooks/local_docker_desktop_preflight.md

set -euo pipefail

echo "===== Docker Desktop Preflight (read-only) ====="

docker_raw="${HOME}/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
if [[ -f "$docker_raw" ]]; then
  size=$(ls -lh "$docker_raw" 2>/dev/null | awk '{print $5}')
  echo "Docker.raw: $docker_raw ($size)"
  if [[ "$size" == *G* ]]; then
    echo "  -> Large VM disk. See docs/ops/runbooks/local_docker_safe_start_guardrails.md"
  fi
else
  echo "Docker.raw: not found (Docker Desktop may not be installed)"
fi

echo ""
echo "Key dir sizes:"
du -sh ~/.docker 2>/dev/null || true
du -sh ~/Library/Containers/com.docker.docker 2>/dev/null || true
du -sh ~/Library/Group\ Containers/group.com.docker 2>/dev/null || true

echo ""
echo "Settings-store AutoStart:"
python3 -c "
import json
from pathlib import Path
p = Path.home() / 'Library/Group Containers/group.com.docker/settings-store.json'
if p.exists():
    d = json.loads(p.read_text())
    print('  AutoStart =', d.get('AutoStart', 'N/A'))
else:
    print('  (file not found)')
" 2>/dev/null || true

echo ""
echo "Preflight done. No changes made."
