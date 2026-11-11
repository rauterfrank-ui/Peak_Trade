"""Project the explicitly bound standing diagnostics snapshot into Ops Cockpit."""

from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import re
import stat

ENV_INCIDENT_DIAGNOSTICS_ROOT = "PEAK_TRADE_OPS_INCIDENT_DIAGNOSTICS_ROOT"
_LATEST = "execution-incident-diagnostics-latest-v1.json"
_MAX_BYTES = 65_536


def _read_snapshot(root):
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError("incident diagnostics root must be canonical")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(directory)
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError("incident diagnostics root must be private")
        fd = os.open(_LATEST, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.getuid()
                or info.st_mode & 0o022
                or info.st_nlink != 1
            ):
                raise ValueError("incident diagnostics snapshot must be owner-controlled")
            data = stream.read(_MAX_BYTES + 1)
    finally:
        os.close(directory)
    if len(data) > _MAX_BYTES:
        raise ValueError("incident diagnostics snapshot exceeds expected size")
    return json.loads(data)


def _timestamp(value):
    if isinstance(value, str):
        try:
            if datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is not None:
                return value
        except ValueError:
            pass
    return None


def _is_digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _load_display():
    """Render historical observation fields from a private worker output only."""
    configured = os.environ.get(ENV_INCIDENT_DIAGNOSTICS_ROOT)
    if not configured:
        return None
    try:
        data = _read_snapshot(Path(configured))
        if (
            type(data) is not dict
            or data.get("schema") != "standing_execution_incident_diagnostics.v1"
            or data.get("runtime_authorization_effect") != "NONE"
            or data.get("observation_status") != "OBSERVED"
        ):
            return {"available": False}
        observed = _timestamp(data.get("observed_at_utc"))
        if observed is None:
            return {"available": False}
        incident = data.get("incident_id")
        bound_incident = (
            _is_digest(incident)
            and _is_digest(data.get("kill_revision"))
            and data.get("incident_evidence_error") is None
        )
        state = data.get("state_name")
        if data.get("evidence_status") != "TRUSTED_PRESENT" or state not in (
            "KILLED",
            "RECOVERING",
            "ACTIVE",
            "DISABLED",
        ):
            state = None
        abort = data.get("transport_abort")
        aborted = None
        if (
            bound_incident
            and type(abort) is dict
            and abort.get("state") == "ABORTED_BEFORE_TRANSPORT"
            and _is_digest(abort.get("record_sha256"))
            and abort.get("kill_revision") is None
        ):
            aborted = _timestamp(abort.get("aborted_at_utc"))
        raw_get = data.get("raw_get_proof_status")
        return {
            "available": True,
            "observed_at": observed,
            "state": state,
            "incident_id": incident if _is_digest(incident) else None,
            "correlated_veto": (
                state == "KILLED"
                and bound_incident
                and data.get("correlated_incident_veto") is True
            ),
            "raw_get_status": raw_get
            if bound_incident and raw_get in ("VERIFIED", "UNPROVEN")
            else None,
            "transport_aborted_at": aborted,
        }
    except (OSError, RuntimeError, ValueError):
        return {"available": False}


def render_standing_incident_panel_v1() -> str:
    sample = _load_display()
    if sample is None:
        return ""
    start = (
        '<section class="card" aria-labelledby="standing-incident-title">'
        '<h2 id="standing-incident-title">EXECUTION GHOSV · Incident-Diagnose</h2>'
    )
    if not sample["available"]:
        return f"{start}<p>Kein lesbarer Diagnosebeleg vorhanden.</p></section>"

    observed = escape(sample["observed_at"])
    incident = sample["incident_id"]
    reference = f"<p>Incident <code>{escape(incident)}</code></p>" if incident else ""
    aborted_at = sample["transport_aborted_at"]
    transport = "Kein verifizierter Abbruchbeleg"
    if aborted_at is not None:
        transport = (
            f'<code>ABORTED_BEFORE_TRANSPORT</code> · <time datetime="{escape(aborted_at)}">'
            f"{escape(aborted_at)}</time><br>Zuordnung zur Sperrgeneration offen"
        )
    return (
        f'{start}<p>Letzte Beobachtung <time datetime="{observed}">{observed}</time></p>'
        "<dl>"
        f"<dt>FILEGATE</dt><dd><code>{escape(sample['state'] or 'Ungeklärt')}</code></dd>"
        "<dt>POST-Veto derselben Sperrgeneration</dt>"
        f"<dd>{'Bestätigt' if sample['correlated_veto'] else 'Offen'}</dd>"
        f"<dt>GET-Originalbeleg</dt><dd><code>{escape(sample['raw_get_status'] or '—')}</code></dd>"
        f"<dt>Transportabbruch derselben Ausführung</dt><dd>{transport}</dd>"
        f"</dl>{reference}</section>"
    )
