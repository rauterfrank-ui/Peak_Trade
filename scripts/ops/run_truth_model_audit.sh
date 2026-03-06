#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

mkdir -p out/ops
TRUTH_DIR="out/ops/peak_trade_truth_model_$(date -u +"%Y%m%dT%H%M%SZ")"
mkdir -p "$TRUTH_DIR"

{
  echo "=== CONTEXT ==="
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  echo
  git status -sb
  echo
  git log --oneline -n 30
  echo
  echo "=== TOP LEVEL ==="
  ls -la
} > "$TRUTH_DIR/00_context.txt"

{
  echo "=== DOMAIN SCAN ==="
  grep -RniE 'research|backtest|execution|shadow|paper|testnet|live|ops|governance|incident|pilot|webui|dashboard|observability|prometheus|grafana|registry|experiment|mlflow|otel|evidence|snapshot|treasury|NO_TRADE|deny_by_default' \
    src scripts docs config tests .github 2>/dev/null || true
} > "$TRUTH_DIR/01_domain_scan.txt"

{
  echo "=== AI / LAYER / MODEL SCAN ==="
  grep -RniE 'AI_AUTONOMY|AUTONOMY|layer|L0|L1|L2|L3|L4|L5|critic|proposer|SoD|model matrix|provider|assigned model|ollama|openai|anthropic|claude|gpt|llama|mistral|qwen|gemini|inference|agent model|decision model|policy model' \
    src scripts docs config tests 2>/dev/null || true
} > "$TRUTH_DIR/02_ai_layer_scan.txt"

{
  echo "=== EXECUTION / GATES / FINAL AUTHORITY SCAN ==="
  grep -RniE 'start-shadow|start-testnet|environment.mode|allowed_environments|NO_TRADE|deny_by_default|enabled|armed|confirm|critic|policy|risk|routing|readiness|health_gate|execution_events|order|fill|adapter|connector|treasury|withdraw|deposit_address|internal_transfer' \
    src scripts docs config tests 2>/dev/null || true
} > "$TRUTH_DIR/03_execution_scan.txt"

{
  echo "=== LEARNING / SELF-IMPROVEMENT SCAN ==="
  grep -RniE 'learn|learning|self-improv|self improve|auto-tune|autotune|reinforcement|rl|train|training|fit\(|partial_fit|online learning|feedback loop|adapt|optimizer|walk-forward|monte-carlo|experiment tracking|registry' \
    src scripts docs config tests 2>/dev/null || true
} > "$TRUTH_DIR/04_learning_scan.txt"

{
  echo "=== WEBUI / DASHBOARD TRUTH SCAN ==="
  grep -RniE 'ops-cockpit|/ops|/api/ops-cockpit|dashboard|cockpit|webui|FastAPI|streamlit|operator' \
    src scripts docs tests 2>/dev/null || true
} > "$TRUTH_DIR/05_webui_scan.txt"

python3 - <<'PY'
from pathlib import Path
import json

truth_dir = sorted(Path("out/ops").glob("peak_trade_truth_model_*"))[-1]

def read(name: str) -> str:
    p = truth_dir / name
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

domain = read("01_domain_scan.txt")
ai = read("02_ai_layer_scan.txt")
execs = read("03_execution_scan.txt")
learn = read("04_learning_scan.txt")
web = read("05_webui_scan.txt")

def has(text: str, token: str) -> bool:
    return token.lower() in text.lower()

truth_model = {
    "research_backtest": "IMPLEMENTED" if any(has(domain, t) for t in ["research", "backtest"]) else "UNKNOWN",
    "execution_stack": "IMPLEMENTED" if any(has(execs, t) for t in ["execution_events", "order", "fill", "adapter", "connector"]) else "UNKNOWN",
    "shadow_testnet_paper_live_modes": "IMPLEMENTED" if all(has(execs, t) for t in ["start-shadow", "start-testnet", "environment.mode"]) else "PARTIAL",
    "governance_ops_evidence": "IMPLEMENTED" if any(has(domain, t) for t in ["ops", "governance", "incident", "pilot", "snapshot", "evidence"]) else "PARTIAL",
    "webui_ops_cockpit": "IMPLEMENTED" if any(has(web, t) for t in ["ops-cockpit", "/ops", "FastAPI"]) else "PARTIAL",
    "observability": "IMPLEMENTED" if any(has(domain, t) for t in ["prometheus", "grafana", "otel", "mlflow"]) else "PARTIAL",
    "ai_layer_model_orchestration": "PARTIAL" if any(has(ai, t) for t in ["critic", "provider", "L5", "layer"]) else "UNKNOWN",
    "online_self_improving_autonomy": "DOC-ONLY" if any(has(learn, t) for t in ["train", "walk-forward", "registry", "experiment tracking"]) and not any(has(learn, t) for t in ["online learning", "partial_fit", "self-improv", "reinforcement"]) else ("PARTIAL" if any(has(learn, t) for t in ["online learning", "partial_fit", "self-improv", "reinforcement"]) else "UNKNOWN"),
    "ai_final_trade_authority": "UNKNOWN",
}

not_allowed = [
    "unguarded live activation",
    "bypassing enabled/armed/confirm-token style controls",
    "bypassing treasury separation",
    "treating stale evidence as current proof",
]
if has(execs, "NO_TRADE"):
    not_allowed.append("unguarded trade escalation beyond NO_TRADE baseline")

ai_rows = []
layer_tokens = []
for token in ["L0", "L1", "L2", "L3", "L4", "L5", "critic", "proposer", "provider"]:
    if has(ai, token):
        layer_tokens.append(token)

for layer in sorted(dict.fromkeys(layer_tokens or ["critic", "provider", "L5"])):
    purpose = "UNKNOWN"
    if layer.lower() == "critic":
        purpose = "pre-execution critique / policy gate signal"
    elif layer.lower() == "provider":
        purpose = "provider reference present, exact assignment unclear"
    elif layer.upper() == "L5":
        purpose = "layer reference found, exact autonomy semantics unclear"
    ai_rows.append({
        "layer": layer,
        "purpose": purpose,
        "inputs": "UNKNOWN",
        "outputs": "UNKNOWN",
        "model": "UNKNOWN",
        "provider": "UNKNOWN",
        "gate_level": "UNKNOWN",
        "role": "supervisory" if layer.lower() == "critic" else "unknown",
        "status": "PARTIAL" if layer.lower() == "critic" else "UNKNOWN",
    })

execution_truth = []
if has(execs, "NO_TRADE"):
    execution_truth.append("NO_TRADE baseline present")
if has(execs, "deny_by_default"):
    execution_truth.append("deny-by-default routing present")
if has(execs, "treasury"):
    execution_truth.append("treasury separation present")
if has(execs, "allowed_environments"):
    execution_truth.append("strategy environment gating present")
if has(execs, "critic") or has(execs, "policy"):
    execution_truth.append("policy/critic gates influence pre-execution flow")
if has(execs, "execution_events"):
    execution_truth.append("execution events persisted")
execution_truth.append("closest-to-trade authority currently evidenced as deterministic gated path, not explicit LLM-final authority")

learning_truth = {
    "offline_learning_research": "IMPLEMENTED" if any(has(learn, t) for t in ["train", "training", "walk-forward", "monte-carlo", "experiment tracking", "registry"]) else "UNKNOWN",
    "online_learning": "PARTIAL" if any(has(learn, t) for t in ["online learning", "partial_fit"]) else "DOC-ONLY" if any(has(learn, t) for t in ["learn", "learning"]) else "UNKNOWN",
    "self_improvement_loop": "PARTIAL" if any(has(learn, t) for t in ["self-improv", "self improve", "feedback loop", "adapt"]) else "DOC-ONLY",
    "autonomous_model_updating": "UNKNOWN",
}

dashboard_show = [
    "system state",
    "guard state",
    "evidence / snapshots / incident state",
    "testnet / pilot status",
    "readiness / routing / health",
    "strategy environment gating",
    "offline research / experiment history",
]
dashboard_avoid = [
    "fully autonomous AI operating system",
    "self-improving live engine",
    "LLM is final trade authority",
    "implemented model assignments where repo evidence is missing",
]

truth_md = "# PEAK_TRADE TRUTH MODEL\n\n## IMPLEMENTED\n"
for k, v in truth_model.items():
    if v == "IMPLEMENTED":
        truth_md += f"- {k}\n"
truth_md += "\n## PARTIAL\n"
for k, v in truth_model.items():
    if v == "PARTIAL":
        truth_md += f"- {k}\n"
truth_md += "\n## DOC-ONLY\n"
for k, v in truth_model.items():
    if v == "DOC-ONLY":
        truth_md += f"- {k}\n"
truth_md += "\n## NOT ALLOWED\n"
for x in not_allowed:
    truth_md += f"- {x}\n"
truth_md += "\n## UNKNOWN\n"
for k, v in truth_model.items():
    if v == "UNKNOWN":
        truth_md += f"- {k}\n"

ai_md = "# AI LAYER REALITY MATRIX\n\n| Layer | Purpose | Inputs | Outputs | Model | Provider | Gate Level | Role | Status |\n|---|---|---|---|---|---|---|---|---|\n"
for row in ai_rows:
    ai_md += f"| {row['layer']} | {row['purpose']} | {row['inputs']} | {row['outputs']} | {row['model']} | {row['provider']} | {row['gate_level']} | {row['role']} | {row['status']} |\n"
if not ai_rows:
    ai_md += "| UNKNOWN | No repo-near AI layer assignment evidenced | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |\n"

exec_md = "# EXECUTION TRUTH STATE\n\n"
for x in execution_truth:
    exec_md += f"- {x}\n"

learn_md = "# LEARNING REALITY CHECK\n\n"
for k, v in learning_truth.items():
    learn_md += f"- {k}: {v}\n"
learn_md += "\n- Current evidence supports offline/research-oriented learning, not a proven online self-improving live system.\n"

dash_md = "# DASHBOARD TRUTH GUIDANCE\n\n## Dashboard may truthfully show today\n"
for x in dashboard_show:
    dash_md += f"- {x}\n"
dash_md += "\n## Dashboard must not imply today\n"
for x in dashboard_avoid:
    dash_md += f"- {x}\n"

final_md = "# FINAL TRUTH SUMMARY\n\n"
final_md += "- Peak_Trade is currently strong as a system, governance/ops stack, reproducible execution stack, and guarded execution platform.\n"
final_md += "- Peak_Trade is not yet evidenced as a fully autonomous self-improving AI operating system.\n"
final_md += "- Peak_Trade is not yet evidenced as an LLM-final trade executor.\n"
final_md += "- Truth-first positioning should guide both internal docs and dashboard language.\n"

(truth_dir / "PEAK_TRADE_TRUTH_MODEL.md").write_text(truth_md, encoding="utf-8")
(truth_dir / "AI_LAYER_REALITY_MATRIX.md").write_text(ai_md, encoding="utf-8")
(truth_dir / "EXECUTION_TRUTH_STATE.md").write_text(exec_md, encoding="utf-8")
(truth_dir / "LEARNING_REALITY_CHECK.md").write_text(learn_md, encoding="utf-8")
(truth_dir / "DASHBOARD_TRUTH_GUIDANCE.md").write_text(dash_md, encoding="utf-8")
(truth_dir / "FINAL_TRUTH_SUMMARY.md").write_text(final_md, encoding="utf-8")
(truth_dir / "truth_model.json").write_text(json.dumps({
    "truth_model": truth_model,
    "not_allowed": not_allowed,
    "ai_rows": ai_rows,
    "execution_truth": execution_truth,
    "learning_truth": learning_truth,
    "dashboard_show": dashboard_show,
    "dashboard_avoid": dashboard_avoid,
}, indent=2), encoding="utf-8")
PY

echo "TRUTH_DIR=$TRUTH_DIR"
ls -la "$TRUTH_DIR"
sed -n '1,220p' "$TRUTH_DIR/PEAK_TRADE_TRUTH_MODEL.md"
sed -n '1,220p' "$TRUTH_DIR/AI_LAYER_REALITY_MATRIX.md"
sed -n '1,220p' "$TRUTH_DIR/EXECUTION_TRUTH_STATE.md"
sed -n '1,220p' "$TRUTH_DIR/LEARNING_REALITY_CHECK.md"
sed -n '1,220p' "$TRUTH_DIR/DASHBOARD_TRUTH_GUIDANCE.md"
sed -n '1,220p' "$TRUTH_DIR/FINAL_TRUTH_SUMMARY.md"
