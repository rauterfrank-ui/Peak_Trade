"""Load and persist foundation_v1.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "okx_multi_window_foundation_v1"
SLOT_IDS = ("SLOT_1", "SLOT_2", "SLOT_3", "SLOT_4")
URL_KEYS = ("SLOT_1_URL", "SLOT_2_URL", "SLOT_3_URL", "SLOT_4_URL")


def default_config_dict() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "workstation": {
            "title_substring": "PEAK TRADE – OKX WORKSTATION",
            "required_tab_count": 7,
        },
        "registry": {
            "workstation_window_id": None,
            "slot_window_ids": {slot: None for slot in SLOT_IDS},
        },
        "url_bindings": {key: "" for key in URL_KEYS},
    }


def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported_schema:{data.get('schema_version')}")
    return data


def save_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
