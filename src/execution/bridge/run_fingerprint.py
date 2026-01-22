from __future__ import annotations

import hashlib
from typing import Any, Mapping

from .canonical_json import dumps_canonical


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_fingerprint(
    *,
    normalized_events_jsonl_bytes: bytes,
    prices_manifest_or_ref: Mapping[str, Any],
    bridge_config: Mapping[str, Any],
) -> str:
    """
    Stable run fingerprint derived ONLY from input manifests and config.

    Spec:
    {
      "events_fingerprint": sha256(bytes_of_normalized_events_jsonl),
      "prices_fingerprint": sha256(canonical JSON of prices manifest OR provided ref),
      "config_fingerprint": sha256(canonical JSON of bridge config)
    }
    """
    input_manifest = {
        "events_fingerprint": _sha256_hex(normalized_events_jsonl_bytes),
        "prices_fingerprint": _sha256_hex(dumps_canonical(dict(prices_manifest_or_ref))),
        "config_fingerprint": _sha256_hex(dumps_canonical(dict(bridge_config))),
    }
    return _sha256_hex(dumps_canonical(input_manifest))
