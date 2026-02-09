from __future__ import annotations

from typing import Sequence

from .base import CollectorContext, RawEvent
from ..db import utc_now_iso


class ManualSeedCollector:
    name = "manual_seed"

    def collect(self, ctx: CollectorContext) -> Sequence[RawEvent]:
        ts = utc_now_iso()
        return [
            RawEvent(
                source=self.name,
                venue_type="seed",
                observed_at=ts,
                payload={
                    "note": "P1 manual seed collector",
                    "run_id": ctx.run_id,
                    "observed_at": ts,
                },
            )
        ]
