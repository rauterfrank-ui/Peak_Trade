"""Owner-scoped standing autonomy record (evidence only; no POST activation)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.constants_v1 import (
    STANDING_AUTONOMY_RECORD_KIND,
)


@dataclass(frozen=True)
class StandingPreExternalAutonomyRecordV1:
    record_kind: str
    utc_timestamp: str
    tested_code_sha: str
    standing_runtime_admitted: bool
    post_allowed: bool
    external_effect_authorized: bool
    real_venue_post_allowed: bool
    continuous_run_authorized_pin_flipped: bool
    owner_scope: str
    note: str

    @classmethod
    def from_admission_flags_v1(
        cls,
        *,
        tested_code_sha: str,
        mechanical_gate_ok: bool,
        post_allowed: bool,
        external_effect_authorized: bool,
        real_venue_post_allowed: bool,
    ) -> StandingPreExternalAutonomyRecordV1:
        return cls(
            record_kind=STANDING_AUTONOMY_RECORD_KIND,
            utc_timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            tested_code_sha=tested_code_sha,
            standing_runtime_admitted=mechanical_gate_ok,
            post_allowed=post_allowed,
            external_effect_authorized=external_effect_authorized,
            real_venue_post_allowed=real_venue_post_allowed,
            continuous_run_authorized_pin_flipped=False,
            owner_scope="PRE_EXTERNAL_STANDING_N1_EVIDENCE_ONLY",
            note=(
                "Program-level standing admission record after WP-04; "
                "does not authorize POST, live venue effect, or pin flips."
            ),
        )


def write_standing_pre_external_autonomy_record_v1(
    *,
    out_dir: Path,
    record: StandingPreExternalAutonomyRecordV1,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{STANDING_AUTONOMY_RECORD_KIND}.json"
    path.write_text(json.dumps(asdict(record), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
