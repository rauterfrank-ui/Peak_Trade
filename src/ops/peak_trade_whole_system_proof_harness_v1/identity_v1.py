"""Deterministic component and edge identities for whole-system proof."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def component_identity_v1(node: Mapping[str, Any]) -> str:
    """Stable identity: role + binding + resolved implementation anchor."""
    payload = {
        "id": node.get("id"),
        "role": node.get("role"),
        "owner": node.get("owner"),
        "binding": node.get("binding", "unknown"),
        "location": node.get("location"),
        "resolved_path": node.get("resolved_path"),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def edge_identity_v1(edge: Mapping[str, Any]) -> str:
    payload = {
        "producer": edge.get("producer"),
        "consumer": edge.get("consumer"),
        "contract": edge.get("contract"),
        "condition": edge.get("condition"),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def component_identity_schema_v1() -> dict[str, Any]:
    return {
        "schema_version": "whole_system_component_identity.v1",
        "fields": [
            "id",
            "role",
            "owner",
            "binding",
            "location",
            "resolved_path",
            "productive_or_test",
        ],
        "hash_algorithm": "sha256_trunc16",
        "function": "component_identity_v1",
    }


def edge_identity_schema_v1() -> dict[str, Any]:
    return {
        "schema_version": "whole_system_edge_identity.v1",
        "fields": ["producer", "consumer", "contract", "condition"],
        "hash_algorithm": "sha256_trunc16",
        "function": "edge_identity_v1",
    }
