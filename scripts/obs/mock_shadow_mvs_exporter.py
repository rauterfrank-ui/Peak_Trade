#!/usr/bin/env python3
"""
Mock metrics exporter for the Shadow Pipeline MVS Grafana dashboard.

Scope:
- watch-only / local demo
- no secrets
- deterministic(ish) counters/histograms based on uptime
"""

from __future__ import annotations

import argparse
import math
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _now_s() -> float:
    return time.time()


def _render_metrics(uptime_s: float, mode: str, exchange: str) -> str:
    # Counters: monotonic based on uptime.
    # Keep stage set aligned with dashboard queries (signal/intent/submit/ack/fill/cancel/risk_block/error).
    stages = {
        "signal": 3.0,
        "intent": 10.0,
        "submit": 9.0,
        "ack": 9.0,
        "fill": 8.0,
        "cancel": 0.4,
        "risk_block": 0.7,
        "error": 0.2,
    }

    # Make values integers (Prometheus accepts floats for counters too, but integers are nicer).
    events = {stage: max(0, int(uptime_s * per_s)) for stage, per_s in stages.items()}

    # Risk blocks: low rate, but non-zero over time.
    risk_blocks = {
        "exposure_limit": max(0, int(uptime_s * 0.12)),
        "spread_too_wide": max(0, int(uptime_s * 0.05)),
    }

    # Feed gaps: very low rate.
    feed_gaps = {"ohlcv": max(0, int(uptime_s * 0.01))}

    # Run state: gauge; keep "running" at 1 for the demo exporter.
    run_state = {"running": 1.0, "stopped": 0.0}

    # Histogram: intent_to_ack latency distribution. Produce cumulative buckets that grow.
    # Buckets should match typical seconds-based buckets. Grafana panel uses rate() over 5m.
    buckets = [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")]
    edge = "intent_to_ack"

    # Total observations: grows with uptime, at least 1 so quantile isn't NaN.
    obs_count = max(1, int(uptime_s * 6.0))

    # Model a log-normal-ish distribution; compute expected CDF values per bucket.
    mu = math.log(0.12)  # median ~120ms
    sigma = 0.5

    def cdf(x: float) -> float:
        if math.isinf(x):
            return 1.0
        # lognormal CDF via erf (normal CDF)
        z = (math.log(max(x, 1e-9)) - mu) / (sigma * math.sqrt(2))
        return 0.5 * (1.0 + math.erf(z))

    bucket_counts = []
    last = 0
    for b in buckets:
        c = int(round(obs_count * cdf(b)))
        c = max(c, last)
        last = c
        bucket_counts.append(c)

    # Ensure +Inf bucket equals count.
    bucket_counts[-1] = obs_count

    # Sum: approximate mean ~ exp(mu + sigma^2/2)
    approx_mean = math.exp(mu + (sigma * sigma) / 2.0)
    obs_sum = obs_count * approx_mean

    lines: list[str] = []

    # Minimal health signal (host-exporter oriented).
    lines += [
        "# HELP shadow_mvs_up 1 when exporter is serving.",
        "# TYPE shadow_mvs_up gauge",
        f'shadow_mvs_up{{mode="{mode}",exchange="{exchange}"}} 1',
    ]

    # Events counter
    lines += [
        "# HELP peak_trade_pipeline_events_total Shadow pipeline stage events (mock).",
        "# TYPE peak_trade_pipeline_events_total counter",
    ]
    for stage, val in events.items():
        lines.append(
            f'peak_trade_pipeline_events_total{{mode="{mode}",stage="{stage}",exchange="{exchange}"}} {val}'
        )

    # Latency histogram
    lines += [
        "# HELP peak_trade_pipeline_latency_seconds Pipeline latency histogram seconds (mock).",
        "# TYPE peak_trade_pipeline_latency_seconds histogram",
    ]
    # Python 3.9 compatibility: zip() has no strict= kwarg.
    for le, c in zip(buckets, bucket_counts):
        le_str = "+Inf" if math.isinf(le) else f"{le:g}"
        lines.append(
            'peak_trade_pipeline_latency_seconds_bucket'
            f'{{mode="{mode}",edge="{edge}",exchange="{exchange}",le="{le_str}"}} {c}'
        )
    lines.append(
        'peak_trade_pipeline_latency_seconds_sum'
        f'{{mode="{mode}",edge="{edge}",exchange="{exchange}"}} {obs_sum}'
    )
    lines.append(
        'peak_trade_pipeline_latency_seconds_count'
        f'{{mode="{mode}",edge="{edge}",exchange="{exchange}"}} {obs_count}'
    )

    # Risk blocks counter
    lines += [
        "# HELP peak_trade_risk_blocks_total Risk blocks by reason (mock).",
        "# TYPE peak_trade_risk_blocks_total counter",
    ]
    for reason, val in risk_blocks.items():
        lines.append(f'peak_trade_risk_blocks_total{{mode="{mode}",reason="{reason}"}} {val}')

    # Feed gaps counter (optional in dashboard)
    lines += [
        "# HELP peak_trade_feed_gaps_total Feed gaps by feed (mock).",
        "# TYPE peak_trade_feed_gaps_total counter",
    ]
    for feed, val in feed_gaps.items():
        lines.append(f'peak_trade_feed_gaps_total{{mode="{mode}",feed="{feed}"}} {val}')

    # Run state gauge (optional in dashboard)
    lines += [
        "# HELP peak_trade_run_state Run state gauge (mock).",
        "# TYPE peak_trade_run_state gauge",
    ]
    for state, val in run_state.items():
        lines.append(f'peak_trade_run_state{{mode="{mode}",state="{state}"}} {val}')

    return "\n".join(lines) + "\n"


class _Handler(BaseHTTPRequestHandler):
    server_version = "pt-shadow-mvs-exporter/1.0"

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in ("/metrics", "/"):
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return

        server: "_Server" = self.server  # type: ignore[assignment]
        uptime_s = _now_s() - server.start_time_s
        body = _render_metrics(uptime_s=uptime_s, mode=server.mode, exchange=server.exchange).encode("utf-8")

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:  # silence default logs
        return


class _Server(ThreadingHTTPServer):
    def __init__(self, host: str, port: int, mode: str, exchange: str) -> None:
        super().__init__((host, port), _Handler)
        self.start_time_s = _now_s()
        self.mode = mode
        self.exchange = exchange


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    # Default port chosen to be collision-arm in typical local stacks.
    p.add_argument("--port", type=int, default=9109)
    p.add_argument("--mode", default="shadow")
    p.add_argument("--exchange", default="sim")
    args = p.parse_args()

    srv = _Server(host=args.host, port=args.port, mode=args.mode, exchange=args.exchange)
    try:
        srv.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        return 0
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
