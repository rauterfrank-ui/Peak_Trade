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

from webui.app import create_app  # noqa: E402


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
