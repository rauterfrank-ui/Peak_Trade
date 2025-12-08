# scripts/run_web_dashboard.py
from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

# src/ zum Pythonpfad hinzufügen, damit "webui" gefunden wird
ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


if __name__ == "__main__":
    # Import-String für reload-Modus verwenden
    uvicorn.run(
        "webui.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(SRC_DIR), str(ROOT / "templates")],
    )
