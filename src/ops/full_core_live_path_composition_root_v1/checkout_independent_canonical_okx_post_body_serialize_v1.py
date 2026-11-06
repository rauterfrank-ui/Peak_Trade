"""CURRENT-owned canonical OKX POST-body serialization.

Byte-identical to the historical serialize_signed_post_body_v1 contract:
json.dumps(dict(payload), separators=(",", ":"), ensure_ascii=True).

Does not sign, load credentials, access Keychain, or send.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from typing import Any, Mapping


def serialize_canonical_okx_post_body_v1(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), separators=(",", ":"), ensure_ascii=True)
