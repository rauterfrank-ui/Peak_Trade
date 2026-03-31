"""
Learning Loop Bridge — rein funktionale Normalisierung auf Patch-Dicts.

Kein Dateizugriff, kein Emitter, kein TOML. Ausgabe ist kompatibel mit
``scripts/run_learning_apply_cycle.py`` (Skalar-``new_value``, ``target`` als Dotted Path).

Erste Quelle: generisches ``Mapping`` bzw. verschachtelte ``patches``-Liste wie in JSON-Snippets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

RawInput = Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]


def normalize_patches(raw: RawInput) -> List[Dict[str, Any]]:
    """
    Normalisiert Rohdaten zu einer Liste kanonischer Patch-Dicts.

    Unterstützt dieselbe Struktur wie ``_extract_patches_from_json_payload`` im
    Apply-Cycle-Skript: Top-Level-Liste von Dicts, oder ein Dict mit
    ``"patches"``: ``[...]``, oder ein einzelnes Patch-Dict mit ``target``.

    Patches ohne gültiges ``target`` oder ohne skalares ``new_value``/``value``
    werden übersprungen (wie der Apply-Cycle bei Overrides).

    Args:
        raw: Mapping oder Sequenz von Mappings (keine Domänen-spezifischen Typen v1).

    Returns:
        Liste von Dicts mit mindestens ``target`` und ``new_value`` (str/int/float/bool).

    Raises:
        TypeError: Wenn ``raw`` weder Mapping noch Sequenz von Mappings ist.
    """
    if isinstance(raw, (str, bytes)):
        raise TypeError("raw must not be str or bytes")
    extracted = _extract_patch_dicts(raw)
    out: List[Dict[str, Any]] = []
    for p in extracted:
        one = _normalize_one_patch(p)
        if one is not None:
            out.append(one)
    return out


def _extract_patch_dicts(raw: RawInput) -> List[Dict[str, Any]]:
    if isinstance(raw, Mapping):
        if "patches" in raw and isinstance(raw["patches"], list):
            return [x for x in raw["patches"] if isinstance(x, dict)]
        if isinstance(raw, dict) and _looks_like_patch(raw):
            return [raw]
        return []
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        return [x for x in raw if isinstance(x, dict)]
    raise TypeError(f"raw must be a mapping or a sequence of mappings, got {type(raw).__name__}")


def _looks_like_patch(d: Mapping[str, Any]) -> bool:
    return "target" in d


def _normalize_one_patch(patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    target = patch.get("target")
    if not isinstance(target, str) or not target.strip():
        return None

    if "new_value" in patch:
        new_value = patch.get("new_value")
    else:
        new_value = patch.get("value")

    if isinstance(new_value, (dict, list)) or new_value is None:
        return None
    if not isinstance(new_value, (bool, int, float, str)):
        return None

    out: Dict[str, Any] = {"target": target.strip(), "new_value": new_value}
    if "old_value" in patch:
        out["old_value"] = patch["old_value"]
    if "reason" in patch and isinstance(patch.get("reason"), str):
        out["reason"] = patch["reason"]
    if "source_experiment_id" in patch and isinstance(patch.get("source_experiment_id"), str):
        out["source_experiment_id"] = patch["source_experiment_id"]
    return out


__all__ = ["normalize_patches"]
