"""URL validation for OKX multi-window slot bindings."""

from __future__ import annotations

from urllib.parse import urlparse

_ALLOWED_SCHEMES = frozenset({"http", "https", "about", "favorites"})
_SLOT_URL_KEYS = ("SLOT_1_URL", "SLOT_2_URL", "SLOT_3_URL", "SLOT_4_URL")


def validate_slot_url(raw: str) -> tuple[bool, str]:
    """Return (ok, reason). Empty string means no navigation."""
    if raw == "":
        return True, "empty"
    parsed = urlparse(raw.strip())
    if not parsed.scheme:
        return False, "missing_scheme"
    scheme = parsed.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        return False, f"scheme_not_allowed:{scheme}"
    if scheme in {"http", "https"} and not parsed.netloc:
        return False, "missing_host"
    if scheme == "about" and parsed.path not in {"blank", "home"}:
        return False, "about_path_not_allowed"
    return True, "ok"


def validate_url_bindings(bindings: dict[str, str]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for key in _SLOT_URL_KEYS:
        if key not in bindings:
            errors.append(f"missing_key:{key}")
            continue
        value = bindings[key]
        if not isinstance(value, str):
            errors.append(f"invalid_type:{key}")
            continue
        ok, reason = validate_slot_url(value)
        if not ok:
            errors.append(f"{key}:{reason}")
    return len(errors) == 0, errors
