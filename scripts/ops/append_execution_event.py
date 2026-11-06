import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_OUT = Path("out/ops/execution_events/execution_events.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    ap = argparse.ArgumentParser(description="Append one execution event to JSONL (NO_TRADE).")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--event-type", required=True)
    ap.add_argument("--level", default="info")
    ap.add_argument("--is-anomaly", action="store_true", default=False)
    ap.add_argument("--is-error", action="store_true", default=False)
    ap.add_argument("--msg", default="")
    args = ap.parse_args()

    out = Path(args.out)
    # guard: must write under out/
    try:
        out.resolve().relative_to(Path.cwd().resolve() / "out")
    except ValueError:
        raise SystemExit("Refusing to write outside out/")

    out.parent.mkdir(parents=True, exist_ok=True)

    evt = {
        "ts": _now(),
        "event_type": args.event_type,
        "level": args.level,
        "is_anomaly": bool(args.is_anomaly),
        "is_error": bool(args.is_error),
        "msg": args.msg,
    }

    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
