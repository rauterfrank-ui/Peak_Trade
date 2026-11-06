"""Idempotent Safari slot launcher (local observation infrastructure)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.ops.okx_multi_window_foundation_v1.config_v1 import SLOT_IDS
from src.ops.okx_multi_window_foundation_v1.safari_v1 import (
    SafariProbeError,
    SafariWindow,
    create_safari_window,
    list_safari_windows,
    set_window_tab_url,
)
from src.ops.okx_multi_window_foundation_v1.validate_v1 import (
    validate_slot_url,
    validate_url_bindings,
)


class LauncherStop(RuntimeError):
    """Fail-closed when window identity is ambiguous."""


@dataclass
class LaunchResult:
    status: str
    workstation_window_id: int | None
    slot_window_ids: dict[str, int | None]
    windows_created: int
    urls_applied: int
    message: str


def _identify_workstation(
    windows: list[SafariWindow],
    title_substring: str,
    required_tab_count: int,
) -> SafariWindow:
    matches = [
        w for w in windows if w.tab_count == required_tab_count and title_substring in w.name
    ]
    if len(matches) == 0:
        raise LauncherStop("workstation_not_found")
    if len(matches) > 1:
        raise LauncherStop("workstation_ambiguous")
    return matches[0]


def _neutral_slot_candidates(
    windows: list[SafariWindow], workstation_id: int
) -> list[SafariWindow]:
    return sorted(
        [w for w in windows if w.window_id != workstation_id and w.is_neutral_slot_window()],
        key=lambda w: w.window_id,
    )


def _registry_is_unbound(stored: dict[str, int | None]) -> bool:
    return all(stored.get(slot) is None for slot in SLOT_IDS)


def _stored_fingerprints(config: dict[str, Any]) -> dict[str, str]:
    raw = config.get("registry", {}).get("slot_fingerprints", {})
    if not isinstance(raw, dict):
        return {}
    return {slot: str(raw[slot]) for slot in SLOT_IDS if slot in raw and raw[slot]}


def _resolve_slot_ids(
    windows: list[SafariWindow],
    workstation_id: int,
    stored: dict[str, int | None],
    stored_fps: dict[str, str],
    allow_create: bool,
    create_fn: Callable[[], int],
) -> tuple[dict[str, int], int]:
    by_id = {w.window_id: w for w in windows}
    assigned: dict[str, int] = {}
    created = 0

    for slot in SLOT_IDS:
        wid = stored.get(slot)
        if wid is None or wid not in by_id or wid == workstation_id:
            continue
        win = by_id[wid]
        expected_fp = stored_fps.get(slot)
        if expected_fp is not None and win.slot_fingerprint() != expected_fp:
            raise LauncherStop(f"slot_fingerprint_mismatch:{slot}:{wid}")
        if not win.is_neutral_slot_window():
            raise LauncherStop(f"stored_slot_not_neutral:{slot}:{wid}")
        assigned[slot] = wid

    candidates = _neutral_slot_candidates(windows, workstation_id)
    candidate_ids = [w.window_id for w in candidates if w.window_id not in assigned.values()]

    if _registry_is_unbound(stored) and len(candidates) > len(SLOT_IDS):
        raise LauncherStop(
            f"slot_identity_ambiguous:expected_{len(SLOT_IDS)}_neutral_slot_windows_found_{len(candidates)}"
        )

    if len(candidates) >= len(SLOT_IDS):
        allow_create = False

    for slot in SLOT_IDS:
        if slot in assigned:
            continue
        if candidate_ids:
            assigned[slot] = candidate_ids.pop(0)
            continue
        if not allow_create:
            raise LauncherStop(f"missing_slot_window:{slot}")
        new_id = int(create_fn())
        created += 1
        assigned[slot] = new_id

    if len(set(assigned.values())) != len(SLOT_IDS):
        raise LauncherStop("slot_window_collision")

    for slot in SLOT_IDS:
        wid = stored.get(slot)
        if wid is not None and wid not in by_id:
            raise LauncherStop(f"stored_slot_window_missing:{slot}:{wid}")

    return assigned, created


def _apply_urls(slot_ids: dict[str, int], url_bindings: dict[str, str]) -> int:
    applied = 0
    for slot in SLOT_IDS:
        url_key = f"{slot}_URL"
        raw = url_bindings.get(url_key, "")
        ok, _ = validate_slot_url(raw)
        if not ok:
            raise LauncherStop(f"invalid_url_binding:{url_key}")
        if raw == "":
            continue
        set_window_tab_url(slot_ids[slot], raw)
        applied += 1
    return applied


def run_launch(
    config: dict[str, Any],
    *,
    allow_create: bool = True,
    apply_urls: bool = True,
    probe: Callable[[], list[SafariWindow]] | None = None,
    create_window: Callable[[], int] | None = None,
) -> LaunchResult:
    ok, errors = validate_url_bindings(config.get("url_bindings", {}))
    if not ok:
        raise LauncherStop("config_url_invalid:" + ",".join(errors))

    ws_cfg = config["workstation"]
    title_substring = ws_cfg["title_substring"]
    required_tab_count = int(ws_cfg["required_tab_count"])

    list_fn = probe or list_safari_windows
    create_fn = create_window or create_safari_window

    try:
        windows = list_fn()
    except SafariProbeError as exc:
        return LaunchResult("BLOCKED", None, {}, 0, 0, f"safari_probe_failed:{exc}")

    workstation = _identify_workstation(windows, title_substring, required_tab_count)
    stored_slots = config.get("registry", {}).get("slot_window_ids", {})
    stored_fps = _stored_fingerprints(config)

    try:
        slot_ids, created = _resolve_slot_ids(
            windows,
            workstation.window_id,
            stored_slots,
            stored_fps,
            allow_create=allow_create,
            create_fn=create_fn,
        )
    except LauncherStop:
        raise
    except SafariProbeError as exc:
        return LaunchResult(
            "BLOCKED", workstation.window_id, {}, 0, 0, f"safari_create_failed:{exc}"
        )

    if created > 0:
        windows = list_fn()
        workstation = _identify_workstation(windows, title_substring, required_tab_count)
        slot_ids, _ = _resolve_slot_ids(
            windows,
            workstation.window_id,
            {k: slot_ids[k] for k in SLOT_IDS},
            stored_fps,
            allow_create=False,
            create_fn=create_fn,
        )

    urls_applied = 0
    if apply_urls:
        try:
            urls_applied = _apply_urls(slot_ids, config.get("url_bindings", {}))
        except SafariProbeError as exc:
            return LaunchResult(
                "FAIL",
                workstation.window_id,
                slot_ids,
                created,
                0,
                f"url_apply_failed:{exc}",
            )

    final_windows = list_fn() if probe is None else windows
    by_id = {w.window_id: w for w in final_windows}
    fingerprints: dict[str, str] = {}
    for slot in SLOT_IDS:
        wid = slot_ids[slot]
        win = by_id.get(wid)
        if win is not None:
            fingerprints[slot] = win.slot_fingerprint()

    config.setdefault("registry", {})
    config["registry"]["workstation_window_id"] = workstation.window_id
    config["registry"]["slot_window_ids"] = {k: slot_ids[k] for k in SLOT_IDS}
    config["registry"]["slot_fingerprints"] = fingerprints

    return LaunchResult(
        status="PASS",
        workstation_window_id=workstation.window_id,
        slot_window_ids=slot_ids,
        windows_created=created,
        urls_applied=urls_applied,
        message="ok",
    )
