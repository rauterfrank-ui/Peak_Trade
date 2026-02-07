#!/usr/bin/env python3
"""Build INTEGRATION_MAP.md from rg hit files. Idempotent."""
import pathlib
import datetime

base = pathlib.Path("out/ops/runbook_b")
out = base / "integration"
p_exec = out / "rg_execution_entrypoints.txt"
p_exch = out / "rg_exchange_adapters.txt"
p_gate = out / "rg_gate_related.txt"


def read(p):
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def files_from_hits(txt, limit=60):
    files = []
    for ln in txt.splitlines():
        if not ln.strip():
            continue
        fp = ln.split(":", 1)[0]
        if fp not in files:
            files.append(fp)
        if len(files) >= limit:
            break
    return files


now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
md = []
md.append(f"# Integration Map (auto) — {now}\n")
md.append("## Candidate execution entrypoints (order submit path)\n")
for f in files_from_hits(read(p_exec), 60):
    md.append(f"- `{f}`\n")
md.append("\n## Candidate exchange adapters / clients\n")
for f in files_from_hits(read(p_exch), 60):
    md.append(f"- `{f}`\n")
md.append("\n## Gate-related code hotspots\n")
for f in files_from_hits(read(p_gate), 60):
    md.append(f"- `{f}`\n")

md.append("\n## Next concrete wiring plan\n")
md.append("1) Identify the single order-submit function used by live paths.\n")
md.append("2) Wrap that call with:\n")
md.append("   - ArmedGate.require_armed(state)\n")
md.append(
    "   - RiskDecision = evaluate_risk(limits, ctx); if deny -> raise + audit\n"
)
md.append(
    "3) Add dry-run mode to execution adapter: build request, log, return simulated ack.\n"
)
md.append(
    "4) Add recon hook post-submit: record expected deltas; later compare with observed snapshots.\n"
)

(base / "INTEGRATION_MAP.md").write_text("".join(md), encoding="utf-8")
