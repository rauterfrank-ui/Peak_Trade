# Peak_Trade — Cursor Multi-Agent Orchestrator Runbook v0

**Purpose:** Deterministic end-to-end runbook for using Cursor Multi-Agent Orchestrator to design, validate, and optionally populate a Notion-based Peak_Trade knowledge graph / ops registry without changing trading authority, runtime behavior, paper/test data, or the canonical repo truth.

**Primary outcome:** A clean, structured, linked Notion layer that makes the Peak_Trade repository understandable and navigable while preserving Git/repo as the sole technical source of truth.

**Operating principle:**

```text
Repo = truth
Notion = structure, navigation, operator cognition, evidence registry
Cursor = read-only analyzer and controlled writer/import helper
Trading runtime = must not depend on Notion as authority
```

---

## 0. Non-Negotiable Boundaries

### 0.1 Authority Boundary

Notion must never become a runtime authority source.

Forbidden:

```text
Notion Approved = true
→ bot reads Notion
→ live/testnet/paper runtime becomes authorized
```

Allowed:

```text
Notion entry documents approval/evidence/status
→ human/operator reviews
→ repo-side config/contracts/gates remain authoritative
→ tests and gates validate separately
```

### 0.2 Repo Boundary

The repository remains canonical for:

- code
- tests
- configs
- docs
- contracts
- runbooks
- safety gates
- live/testnet/paper authorization logic
- experiment/evidence artifacts that are committed
- branch and PR history

Notion may contain summaries and links, not canonical logic.

### 0.3 Runtime Boundary

Do not start, stop, mutate, or interfere with:

- Scheduler/daemon runs
- Paper runs
- Testnet runs
- Live processes
- Broker/exchange/order submission paths
- Any active run data
- Paper/test evidence artifacts unless explicitly requested

### 0.4 Master V2 / Double Play Boundary

Master V2 / Double Play remains top-priority protected logic.

Notion work must not modify:

- Master V2 decision logic
- Bull/Bear switching logic
- Scope/Capital logic
- Risk/KillSwitch logic
- Execution/Live gates
- strategy live authority
- dashboard authority boundaries

Notion may only describe, link, and classify these areas.

### 0.5 Reuse-Before-New Boundary

Before creating any new map/index/registry/readiness/evidence surface, Cursor must inventory existing repo surfaces and identify canonical owners.

Preferred order:

```text
Reuse existing surface
→ extend existing surface
→ add pointer/index only if needed
→ create new artifact only with duplicate-risk reasoning
```

---

## 1. Target Notion Model

The recommended Notion workspace root is:

```text
Peak_Trade Ops
```

Recommended child databases:

```text
01 System Map
02 Workstreams
03 Repo Assets
04 Safety Boundaries
05 Evidence & Closeouts
06 PR / Slice Registry
07 External Approvals
08 Runtime / Scheduler Records
09 Backlog / Parked Items
10 Operator Decisions
```

These databases form the Notion knowledge graph.

---

## 2. Database Specifications

### 2.1 System Map

Purpose: High-level architecture and operational domains.

Typical entries:

```text
Master V2
Double Play
Risk Layer
KillSwitch
Scope Engine
Capital Slot Ratchet
Execution Layer
Live Gates
Scheduler / Daemon
Paper Runtime
Testnet Orchestrator
Market Dashboard
Cybersecurity Visibility Chain
Evidence Layer
External Approvals
AI/KI Cost Governance
Notion Ops Registry
```

Recommended properties:

| Property | Type | Required | Meaning |
|---|---:|---:|---|
| Name | Title | yes | System area name |
| Status | Select | yes | Active / Stable / Draft / Parked / Deprecated / Unknown |
| Owner Area | Select | yes | Strategy / Risk / Execution / WebUI / Ops / Docs / Tests / Governance |
| Authority Level | Select | yes | None / Read-only / Advisory / Gated / Runtime / Live-critical |
| Runtime Impact | Select | yes | None / Possible / Direct / Unknown |
| Safety Criticality | Select | yes | Low / Medium / High / Critical |
| Canonical Docs | Relation | no | Related Repo Assets |
| Canonical Tests | Relation | no | Related Repo Assets |
| Canonical Code Paths | Relation | no | Related Repo Assets |
| Related Workstreams | Relation | no | Related Workstreams |
| Related Evidence | Relation | no | Evidence entries |
| Allowed Changes | Text | no | What may be changed safely |
| Forbidden Changes | Text | no | What may not be changed without explicit approval |
| Current Risk | Text | no | Known risk or ambiguity |
| Next Safe Slice | Text | no | Next bounded safe action |
| Last Reviewed At | Date | no | Last review date |
| Confidence | Select | yes | High / Medium / Low |

Deterministic status vocabulary:

```text
Active      = currently relevant and used
Stable      = mature and not currently changing
Draft       = planned or partially specified
Parked      = important backlog, not discarded
Deprecated  = superseded and should not be extended
Unknown     = not classified yet
```

---

### 2.2 Workstreams

Purpose: Track current large project chains and their state.

Typical entries:

```text
Market Dashboard
Cybersecurity Visibility Chain
Paper Runtime / Scheduler
Testnet Readiness
External Approvals
AI/KI Cost Controls
Evidence / Readiness
Live-Gate Hardening
Notion Knowledge Graph
Master V2 / Double Play Governance
```

Recommended properties:

| Property | Type | Required | Meaning |
|---|---:|---:|---|
| Name | Title | yes | Workstream name |
| Current State | Select | yes | Active / Idle / Hold / Closed / Parked / Needs Review |
| Last Completed Slice | Text | no | Human-readable last completed unit |
| Open Risks | Text | no | Known issues |
| Blocked By | Text | no | Blocking item |
| Next Safe Action | Text | no | Next bounded safe move |
| Related System Areas | Relation | no | System Map entries |
| Related Repo Assets | Relation | no | Repo Assets |
| Related Evidence | Relation | no | Evidence & Closeouts |
| Related PRs | Relation | no | PR / Slice Registry |
| Protected? | Checkbox | yes | Whether changes require explicit care |
| Runtime Touch Risk | Select | yes | None / Low / Medium / High / Unknown |
| Last Reviewed At | Date | no | Last review date |

---

### 2.3 Repo Assets

Purpose: File/path map across repo assets.

Recommended properties:

| Property | Type | Required | Meaning |
|---|---:|---:|---|
| Path | Title | yes | Repo-relative path |
| Asset Type | Select | yes | Code / Test / Doc / Config / Script / Template / Workflow / Evidence / Unknown |
| System Area | Relation | no | Related System Map entries |
| Workstream | Relation | no | Related Workstreams |
| Canonical Owner | Select | yes | WebUI / Execution / Risk / Live / Ops / Docs / Tests / Unknown |
| Safety Criticality | Select | yes | Low / Medium / High / Critical / Unknown |
| Runtime Touches? | Checkbox | yes | Direct or indirect runtime effect |
| Live-Relevant? | Checkbox | yes | Could affect live behavior |
| Read-only? | Checkbox | yes | Pure display/docs/tests/read-only path |
| Last Known PR | Relation | no | PR / Slice Registry |
| Linked Tests | Relation | no | Repo Assets of type Test |
| Linked Docs | Relation | no | Repo Assets of type Doc |
| Linked Runbooks | Relation | no | Repo Assets of type Doc/Runbook |
| Do Not Touch Without Approval? | Checkbox | yes | Hard protection flag |
| Notes | Text | no | Human-readable notes |
| Confidence | Select | yes | High / Medium / Low |

Deterministic path classification rules:

```text
src/             → Code unless clearly static/data
src/live/        → Live / Testnet / runtime-relevant candidate
src/execution/   → Execution layer; high-sensitivity candidate
tests/           → Test
scripts/         → Script
scripts/ops/     → Ops script
.github/         → Workflow
configs/         → Config
docs/            → Doc
templates/       → Template/WebUI
```

Sensitivity defaults:

```text
src/live/         = High or Critical
src/execution/    = High or Critical
risk/killswitch   = Critical
live gates         = Critical
broker/exchange    = Critical
web dashboard      = Medium unless authority-like behavior appears
docs only          = Low/Medium depending on authority claims
tests only         = Low/Medium unless they protect critical invariants
```

---

### 2.4 Safety Boundaries

Purpose: Explicitly preserve project rules and invariants.

Seed entries:

```text
Dashboard != Authority
AI != Authority
Signal != Trade
Docs != Approval
Notion != Runtime Authority
Live default blocked
Master V2 top priority
No paper/test data disruption
No duplicate readiness/evidence surfaces
Reuse before new registry surface
External approvals are evidence, not direct runtime authorization
```

Recommended properties:

| Property | Type | Required | Meaning |
|---|---:|---:|---|
| Boundary | Title | yes | Rule name |
| Applies To | Relation | no | System Map / Workstreams |
| Severity | Select | yes | Advisory / Important / Critical |
| Reason | Text | yes | Why this exists |
| Canonical Source | Relation | no | Repo Asset(s) |
| Protected Paths | Text | no | Path globs or path notes |
| Violation Examples | Text | no | What would violate it |
| Required Approval | Text | no | Human approval condition |
| Related Tests | Relation | no | Repo Assets |
| Active? | Checkbox | yes | Current applicability |

---

### 2.5 Evidence & Closeouts

Purpose: Import and classify reports, closeouts, PR readiness results, snapshots.

Recommended properties:

| Property | Type | Required | Meaning |
|---|---:|---:|---|
| Evidence ID | Title | yes | Stable ID or generated title |
| Type | Select | yes | Paper Run / Testnet Run / PR Readiness / CI Closeout / Risk Audit / Snapshot / Runbook / Other |
| Date | Date | no | Generated or observed date |
| Branch | Text | no | Branch if present |
| Commit SHA | Text | no | Commit if present |
| PR | Relation | no | PR / Slice Registry |
| Verdict | Select/Text | yes | Final verdict text |
| Next Action | Text | no | Next action line |
| Repo Changed? | Checkbox | no | Whether repo changed |
| Runtime Active? | Select | no | Yes / No / Unknown / Not Applicable |
| Scope | Text | no | Scope of report |
| Linked Workstream | Relation | no | Workstream |
| Linked System Areas | Relation | no | System Map |
| Report Path | URL/Text | yes | Path or URL |
| Imported Summary | Text | no | Short summary |
| Authority Impact | Select | yes | None / Read-only / Advisory / Requires Review / Unknown |
| Confidence | Select | yes | High / Medium / Low |

---

### 2.6 PR / Slice Registry

Purpose: Track PRs, branches, focused slices, validations, and follow-up status.

Recommended properties:

| Property | Type | Required | Meaning |
|---|---:|---:|---|
| Name | Title | yes | PR or slice title |
| PR Number | Number | no | GitHub PR number |
| Branch | Text | no | Branch name |
| Status | Select | yes | Draft / Open / Merged / Closed Invalid / Parked / Unknown |
| Scope | Select | yes | Docs / Tests / WebUI / Ops / Runtime / Execution / Mixed / Unknown |
| Changed Paths | Text | no | Summary or path list |
| Validation | Text | no | Tests/lint/docs gates |
| Merge State | Select | no | Mergeable / Blocked / Merged / Unknown |
| Closeout Report | Relation | no | Evidence entry |
| Related Workstream | Relation | no | Workstream |
| Related System Areas | Relation | no | System Map |
| Safety Impact | Select | yes | None / Low / Medium / High / Critical / Unknown |
| Follow-up Needed? | Checkbox | yes | True if next action exists |
| Notes | Text | no | Summary |

---

### 2.7 External Approvals

Purpose: Human-readable registry for external approvals without direct runtime authority.

Recommended properties:

| Property | Type | Required | Meaning |
|---|---:|---:|---|
| Approval ID | Title | yes | Stable approval identifier |
| Status | Select | yes | Draft / Proposed / Reviewed / Approved / Revoked / Expired |
| Account Type | Select | yes | Spot / Futures / Paper / Testnet / Unknown |
| Environment Scope | Select | yes | Research / Shadow / Paper / Testnet / Canary / Live |
| Exchange | Select | no | Kraken / Binance / Other |
| Strategy Scope | Text | no | Strategy or layer |
| Instrument Scope | Text | no | Symbol/instrument scope |
| Max Notional | Number/Text | no | Limit if applicable |
| Max Leverage | Number/Text | no | Limit if applicable |
| Risk Profile | Select | no | Conservative / Standard / Aggressive / Unknown |
| Valid From | Date | no | Start date |
| Valid Until | Date | no | Expiry |
| Linked PR | Relation | no | PR / Slice Registry |
| Linked Commit | Text | no | Commit SHA |
| Linked Evidence Package | Relation | no | Evidence |
| Linked Runbook | Relation | no | Repo Assets |
| Operator | Text | no | Human operator |
| Revocation Reason | Text | no | If revoked |
| Runtime Authority? | Checkbox | yes | Must remain false |

Hard rule:

```text
Runtime Authority? must be false for every Notion approval entry.
```

---

### 2.8 Runtime / Scheduler Records

Purpose: Document runtime observations, not control runtime.

Recommended properties:

| Property | Type | Required | Meaning |
|---|---:|---:|---|
| Run ID | Title | yes | Run identifier |
| Mode | Select | yes | Paper / Shadow / Testnet / Canary / Live / Unknown |
| Status | Select | yes | Planned / Running / Completed / Stopped / Unknown / Stale Closed |
| PID | Text | no | Observed PID |
| Started At | Date | no | Start time |
| Ended At | Date | no | End time |
| Config Path | Text | no | Config path |
| Artifact Path | Text | no | Artifact path |
| Verdict | Text | no | Observation verdict |
| Stop Condition | Text | no | Stop condition |
| Linked Evidence | Relation | no | Evidence |
| Linked Workstream | Relation | no | Workstream |
| Operator Notes | Text | no | Notes |

---

### 2.9 Backlog / Parked Items

Purpose: Keep important parked items visible and protected.

Recommended properties:

| Property | Type | Required | Meaning |
|---|---:|---:|---|
| Item | Title | yes | Backlog item |
| Status | Select | yes | Parked / Ready / Blocked / Rejected / Done |
| Reason Parked | Text | no | Why not now |
| Safety Preconditions | Text | no | What must be true first |
| Related System Areas | Relation | no | System Map |
| Related Workstreams | Relation | no | Workstreams |
| Related Evidence | Relation | no | Evidence |
| Priority | Select | yes | Low / Medium / High / Critical |
| Do Not Drop? | Checkbox | yes | For historically important items |
| Next Review Trigger | Text | no | When to revisit |

---

### 2.10 Operator Decisions

Purpose: Record human decisions that affect workflow direction.

Recommended properties:

| Property | Type | Required | Meaning |
|---|---:|---:|---|
| Decision | Title | yes | Decision title |
| Date | Date | no | Decision date |
| Decision Type | Select | yes | Proceed / Stop / Hold / Park / Merge / Review / Reject |
| Rationale | Text | yes | Why |
| Scope | Text | no | Affected scope |
| Related Workstream | Relation | no | Workstreams |
| Related Evidence | Relation | no | Evidence |
| Related PR | Relation | no | PR / Slice Registry |
| Follow-up | Text | no | Next action |
| Authority Impact | Select | yes | None / Advisory / Requires Repo Gate / Unknown |

---

## 3. Deterministic Execution Phases

This runbook uses phases. Do not skip phase gates.

```text
Phase A — Repo read-only inventory
Phase B — Existing surface discovery
Phase C — Domain classification
Phase D — Notion schema verification
Phase E — Import plan generation
Phase F — Dry-run export generation
Phase G — Operator review
Phase H — Optional Notion write/import
Phase I — Post-import consistency audit
Phase J — Maintenance loop
```

---

## 4. Phase A — Repo Read-Only Inventory

### Goal

Create a deterministic inventory of repo paths without modifying the repo or starting runtime processes.

### Git Context

Run on:

```text
Branch: main
Repo root: Peak_Trade repository root
Mode: read-only
```

### Command

```bash
cd /path/to/Peak_Trade && \
git checkout main && \
git fetch origin --prune && \
git pull --ff-only origin main && \
test -z "$(git status --porcelain)" && \
TS="$(date -u +%Y%m%dT%H%M%SZ)" && \
BASE="/tmp/peak_trade_notion_knowledge_graph_inventory_${TS}" && \
mkdir -p "$BASE" && \
printf 'BASE=%s\n' "$BASE" && \
git rev-parse --short HEAD | tee "$BASE/HEAD_SHORT.txt" && \
git rev-parse HEAD | tee "$BASE/HEAD_FULL.txt" && \
git ls-files | sort > "$BASE/REPO_FILES.txt" && \
find docs -type f 2>/dev/null | sort > "$BASE/DOC_FILES.txt" || true && \
find tests -type f 2>/dev/null | sort > "$BASE/TEST_FILES.txt" || true && \
find src -type f 2>/dev/null | sort > "$BASE/SRC_FILES.txt" || true && \
find scripts -type f 2>/dev/null | sort > "$BASE/SCRIPT_FILES.txt" || true && \
find templates -type f 2>/dev/null | sort > "$BASE/TEMPLATE_FILES.txt" || true && \
find .github -type f 2>/dev/null | sort > "$BASE/WORKFLOW_FILES.txt" || true && \
python - <<'PY' "$BASE"
from pathlib import Path
import json
import sys

base = Path(sys.argv[1])
repo_files = (base / "REPO_FILES.txt").read_text(encoding="utf-8").splitlines()

def classify(path: str) -> dict:
    p = path
    asset_type = "Unknown"
    owner = "Unknown"
    runtime_touches = False
    live_relevant = False
    safety = "Unknown"

    if p.startswith("src/"):
        asset_type = "Code"
        owner = "Code"
        runtime_touches = True
        safety = "Medium"
    if p.startswith("src/live/"):
        owner = "Live"
        live_relevant = True
        safety = "High"
    if p.startswith("src/execution/"):
        owner = "Execution"
        live_relevant = True
        safety = "Critical"
    if "risk" in p.lower() or "killswitch" in p.lower() or "kill_switch" in p.lower():
        safety = "Critical"
    if p.startswith("tests/"):
        asset_type = "Test"
        owner = "Tests"
        runtime_touches = False
        safety = "Medium" if any(x in p.lower() for x in ["live", "execution", "risk", "killswitch", "testnet"]) else "Low"
    if p.startswith("docs/"):
        asset_type = "Doc"
        owner = "Docs"
        runtime_touches = False
        safety = "Medium" if any(x in p.lower() for x in ["live", "execution", "risk", "approval", "authority"]) else "Low"
    if p.startswith("scripts/"):
        asset_type = "Script"
        owner = "Ops"
        safety = "Medium"
    if p.startswith(".github/"):
        asset_type = "Workflow"
        owner = "CI"
        safety = "Medium"
    if p.startswith("templates/"):
        asset_type = "Template"
        owner = "WebUI"
        safety = "Medium"
    if p.startswith("configs/"):
        asset_type = "Config"
        owner = "Config"
        safety = "High"
    return {
        "path": p,
        "asset_type": asset_type,
        "canonical_owner": owner,
        "runtime_touches": runtime_touches,
        "live_relevant": live_relevant,
        "safety_criticality": safety,
        "read_only_candidate": asset_type in {"Doc", "Test", "Template", "Workflow"},
        "confidence": "Medium",
    }

records = [classify(p) for p in repo_files]
(base / "REPO_ASSET_INVENTORY.json").write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
(base / "REPO_ASSET_INVENTORY.jsonl").write_text("\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n", encoding="utf-8")
print(f"INVENTORY_RECORDS={len(records)}")
print(f"RESULT_JSON={base / 'REPO_ASSET_INVENTORY.json'}")
print(f"RESULT_JSONL={base / 'REPO_ASSET_INVENTORY.jsonl'}")
PY
```

### Success Criteria

```text
git status --porcelain is empty
REPO_FILES.txt exists
REPO_ASSET_INVENTORY.json exists
REPO_ASSET_INVENTORY.jsonl exists
No runtime process started
No repo file modified
```

### Stop Conditions

Stop if:

```text
git status is dirty
git pull fails
repo root is wrong
inventory script errors
runtime command appears in proposed output
```

---

## 5. Phase B — Existing Surface Discovery

### Goal

Find existing map/index/evidence/readiness/handoff/package/pointer surfaces before creating anything new.

### Git Context

Run on:

```text
Branch: main
Repo root: Peak_Trade repository root
Mode: read-only
```

### Command

```bash
cd /path/to/Peak_Trade && \
test "$(git branch --show-current)" = "main" && \
test -z "$(git status --porcelain)" && \
TS="$(date -u +%Y%m%dT%H%M%SZ)" && \
BASE="/tmp/peak_trade_notion_existing_surfaces_${TS}" && \
mkdir -p "$BASE" && \
printf 'BASE=%s\n' "$BASE" && \
python - <<'PY' "$BASE"
from pathlib import Path
import json
import re
import sys

base = Path(sys.argv[1])
patterns = [
    "truth", "map", "index", "registry", "readiness", "evidence",
    "handoff", "package", "pointer", "surface", "approval",
    "authority", "runbook", "known limitation", "limitations",
    "dashboard", "market surface", "external approval",
]
files = [Path(p) for p in Path('.').glob('**/*') if p.is_file() and '.git/' not in str(p)]
records = []
for path in files:
    rel = str(path)
    name_l = path.name.lower()
    path_l = rel.lower()
    score = 0
    hits = []
    for pat in patterns:
        if pat in name_l or pat in path_l:
            score += 2
            hits.append(pat)
    if path.suffix.lower() in {'.md', '.yaml', '.yml', '.json', '.toml', '.py'}:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')[:50000].lower()
        except Exception:
            text = ''
        for pat in patterns:
            if pat in text:
                score += 1
                if pat not in hits:
                    hits.append(pat)
    if score:
        records.append({"path": rel, "score": score, "hits": sorted(hits)})
records.sort(key=lambda r: (-r['score'], r['path']))
(base / 'EXISTING_SURFACES.json').write_text(json.dumps(records, indent=2, sort_keys=True), encoding='utf-8')
(base / 'EXISTING_SURFACES.md').write_text(
    '# Existing Surfaces Discovery\n\n' +
    '\n'.join(f"- `{r['path']}` — score={r['score']} — hits={', '.join(r['hits'])}" for r in records[:300]) + '\n',
    encoding='utf-8'
)
print(f"SURFACE_CANDIDATES={len(records)}")
print(f"RESULT={base / 'EXISTING_SURFACES.md'}")
PY
```

### Success Criteria

```text
EXISTING_SURFACES.md exists
EXISTING_SURFACES.json exists
No repo changes
```

### Required Review

Before building Notion schema, review whether the repo already has canonical files for:

```text
truth map
docs truth map
runbook index
known limitations
external approvals
evidence registry
market surface docs
scheduler daemon docs
cybersecurity visibility docs
AI/KI cost docs
```

---

## 6. Phase C — Cursor Multi-Agent Classification Plan

### Goal

Ask Cursor to classify repo areas and propose Notion mappings in read-only planning mode.

### Git Context

Run on:

```text
Branch: main
Repo root: Peak_Trade repository root
Mode: cursor-agent ask/plan, read-only
```

### Command

```bash
cd /path/to/Peak_Trade && \
test "$(git branch --show-current)" = "main" && \
test -z "$(git status --porcelain)" && \
TS="$(date -u +%Y%m%dT%H%M%SZ)" && \
BASE="/tmp/peak_trade_notion_knowledge_graph_cursor_plan_${TS}" && \
mkdir -p "$BASE" && \
PROMPT="$BASE/CURSOR_NOTION_KNOWLEDGE_GRAPH_PLAN_PROMPT.md" && \
RESULT="$BASE/NOTION_KNOWLEDGE_GRAPH_PLAN.md" && \
python - <<'PY' "$PROMPT"
from pathlib import Path
import sys

prompt = Path(sys.argv[1])
prompt.write_text(r'''# Cursor Multi-Agent Orchestrator Task — Peak_Trade Notion Knowledge Graph v0 Plan

## Git Context

- Branch: main only
- Repo root: Peak_Trade repository root
- Mode: read-only planning
- Do not modify repo files
- Do not start scheduler/runtime/daemon/paper/testnet/live/broker/exchange/order-submission processes
- Do not touch paper/test data
- Do not alter Master V2 / Double Play / Bull-Bear / Scope / Capital / Risk / KillSwitch / Execution / Live Gates

## Goal

Create a deterministic implementation plan for a Notion-based Peak_Trade Knowledge Graph / Ops Registry.

The repo remains the technical source of truth. Notion is only a structure, navigation, review, and operator cognition layer.

## Required Output Sections

1. Executive Summary
2. Hard Safety Boundaries
3. Existing Repo Surfaces Inventory
4. Canonical Owner Candidates
5. Proposed Notion Databases
6. Proposed Notion Properties
7. Relation Graph
8. System Area Taxonomy
9. Repo Asset Classification Rules
10. Workstream Classification Rules
11. Safety Boundary Seed Entries
12. Evidence / Closeout Import Rules
13. PR / Slice Registry Import Rules
14. External Approval Registry Rules
15. Runtime / Scheduler Record Rules
16. Duplicate Surface Risk Analysis
17. Drift-Control Strategy
18. Notion Write Strategy
19. Dry-Run Export Format
20. Rollback / Revocation Strategy
21. Validation Checklist
22. Explicit Non-Goals
23. STOP Conditions
24. Recommended First Slice
25. Final Verdict

## Mandatory Invariants

- Repo = truth
- Notion = navigation/structure only
- Cursor may read repo and propose mappings
- Notion entries must never authorize runtime
- External approvals in Notion are evidence, not runtime authority
- No repo modification in this task
- No runtime modification in this task
- Reuse existing repo surfaces before proposing new ones
- Avoid duplicate evidence/readiness/map/index surfaces
- Keep Master V2 / Double Play protected

## Final Lines Required

VERDICT=<one_line>
NEXT_ACTION=<one_line>
IMPLEMENT_NOW=<true_or_false>
REPO_CHANGED=false
RUNTIME_STARTED=false
NOTION_RUNTIME_AUTHORITY=false
''', encoding='utf-8')
print(prompt)
PY
cursor-agent --print --mode ask --model gpt-5.5-extra-high < "$PROMPT" | tee "$BASE/CURSOR_AGENT_OUTPUT.txt" ; \
python - <<'PY' "$BASE/CURSOR_AGENT_OUTPUT.txt" "$RESULT"
from pathlib import Path
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding='utf-8', errors='replace')
text = text.replace('```markdown', '').replace('```', '')
dst.write_text(text.strip() + '\n', encoding='utf-8')
print(f"RESULT={dst}")
PY
```

### Success Criteria

```text
Cursor output captured
RESULT markdown exists
REPO_CHANGED=false appears or is manually verified
git status remains clean
No runtime started
```

### Stop Conditions

Stop if Cursor suggests:

```text
using Notion as direct runtime authority
modifying live/testnet/paper gates
starting runtime
changing Master V2 logic
creating duplicate surfaces without reuse analysis
```

---

## 7. Phase D — Notion Schema Verification

### Goal

Verify that Notion has the needed databases/properties or generate a schema creation plan.

### Modes

There are two valid modes:

```text
Mode 1: Manual Notion setup
Mode 2: Cursor/API-assisted setup
```

Manual mode is safer for v0.

### Required Databases

```text
01 System Map
02 Workstreams
03 Repo Assets
04 Safety Boundaries
05 Evidence & Closeouts
06 PR / Slice Registry
07 External Approvals
08 Runtime / Scheduler Records
09 Backlog / Parked Items
10 Operator Decisions
```

### Verification Checklist

For each database verify:

```text
Name exists
Required title property exists
Required select vocabularies exist
Relations are either created or intentionally deferred
No formula/automation authorizes runtime
No integration secret is stored in public text
No database is shared beyond intended scope
```

### Deterministic Manual Setup Order

Create in this order to simplify relation creation:

```text
1. System Map
2. Workstreams
3. Repo Assets
4. Safety Boundaries
5. Evidence & Closeouts
6. PR / Slice Registry
7. External Approvals
8. Runtime / Scheduler Records
9. Backlog / Parked Items
10. Operator Decisions
```

Then add relations:

```text
Workstreams ↔ System Map
Repo Assets ↔ System Map
Repo Assets ↔ Workstreams
Safety Boundaries ↔ System Map
Evidence ↔ Workstreams
Evidence ↔ System Map
PR Registry ↔ Workstreams
PR Registry ↔ Evidence
External Approvals ↔ Evidence
Runtime Records ↔ Evidence
Backlog ↔ Workstreams
Operator Decisions ↔ Evidence/Workstreams/PRs
```

---

## 8. Phase E — Dry-Run Export Generation

### Goal

Generate importable files without writing to Notion.

### Git Context

Run on:

```text
Branch: main
Repo root: Peak_Trade repository root
Mode: read-only export to /tmp
```

### Command

```bash
cd /path/to/Peak_Trade && \
test "$(git branch --show-current)" = "main" && \
test -z "$(git status --porcelain)" && \
TS="$(date -u +%Y%m%dT%H%M%SZ)" && \
BASE="/tmp/peak_trade_notion_dry_run_export_${TS}" && \
mkdir -p "$BASE" && \
printf 'BASE=%s\n' "$BASE" && \
python - <<'PY' "$BASE"
from pathlib import Path
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone

base = Path(sys.argv[1])
files = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def asset_type(path):
    if path.startswith('src/'): return 'Code'
    if path.startswith('tests/'): return 'Test'
    if path.startswith('docs/'): return 'Doc'
    if path.startswith('scripts/'): return 'Script'
    if path.startswith('templates/'): return 'Template'
    if path.startswith('.github/'): return 'Workflow'
    if path.startswith('configs/'): return 'Config'
    return 'Unknown'

def owner(path):
    if path.startswith('src/live/'): return 'Live'
    if path.startswith('src/execution/'): return 'Execution'
    if path.startswith('templates/') or 'webui' in path: return 'WebUI'
    if path.startswith('tests/'): return 'Tests'
    if path.startswith('docs/'): return 'Docs'
    if path.startswith('scripts/ops/'): return 'Ops'
    if path.startswith('.github/'): return 'CI'
    return 'Unknown'

def safety(path):
    low = path.lower()
    if any(x in low for x in ['killswitch', 'kill_switch', 'risk', 'live_gate', 'live-gate', 'broker', 'exchange', 'order']):
        return 'Critical'
    if path.startswith('src/live/') or path.startswith('src/execution/') or path.startswith('configs/'):
        return 'High'
    if path.startswith(('templates/', '.github/', 'scripts/')):
        return 'Medium'
    return 'Low'

repo_assets = []
for f in files:
    repo_assets.append({
        'Path': f,
        'Asset Type': asset_type(f),
        'Canonical Owner': owner(f),
        'Safety Criticality': safety(f),
        'Runtime Touches?': 'true' if f.startswith('src/') or f.startswith('scripts/') or f.startswith('configs/') else 'false',
        'Live-Relevant?': 'true' if f.startswith('src/live/') or f.startswith('src/execution/') or 'live' in f.lower() else 'false',
        'Read-only?': 'true' if f.startswith(('docs/', 'tests/', 'templates/', '.github/')) else 'false',
        'Do Not Touch Without Approval?': 'true' if safety(f) in {'High', 'Critical'} else 'false',
        'Confidence': 'Medium',
        'Import Batch': now,
        'Repo HEAD': head,
    })

system_map = [
    {'Name': 'Master V2', 'Status': 'Active', 'Owner Area': 'Strategy', 'Authority Level': 'Gated', 'Runtime Impact': 'Possible', 'Safety Criticality': 'Critical', 'Confidence': 'Medium'},
    {'Name': 'Double Play', 'Status': 'Active', 'Owner Area': 'Strategy', 'Authority Level': 'Gated', 'Runtime Impact': 'Possible', 'Safety Criticality': 'Critical', 'Confidence': 'Medium'},
    {'Name': 'Risk Layer', 'Status': 'Active', 'Owner Area': 'Risk', 'Authority Level': 'Runtime', 'Runtime Impact': 'Direct', 'Safety Criticality': 'Critical', 'Confidence': 'Medium'},
    {'Name': 'KillSwitch', 'Status': 'Active', 'Owner Area': 'Risk', 'Authority Level': 'Runtime', 'Runtime Impact': 'Direct', 'Safety Criticality': 'Critical', 'Confidence': 'Medium'},
    {'Name': 'Execution Layer', 'Status': 'Active', 'Owner Area': 'Execution', 'Authority Level': 'Runtime', 'Runtime Impact': 'Direct', 'Safety Criticality': 'Critical', 'Confidence': 'Medium'},
    {'Name': 'Live Gates', 'Status': 'Active', 'Owner Area': 'Governance', 'Authority Level': 'Live-critical', 'Runtime Impact': 'Direct', 'Safety Criticality': 'Critical', 'Confidence': 'Medium'},
    {'Name': 'Market Dashboard', 'Status': 'Active', 'Owner Area': 'WebUI', 'Authority Level': 'Read-only', 'Runtime Impact': 'None', 'Safety Criticality': 'Medium', 'Confidence': 'Medium'},
    {'Name': 'Evidence Layer', 'Status': 'Active', 'Owner Area': 'Governance', 'Authority Level': 'Advisory', 'Runtime Impact': 'None', 'Safety Criticality': 'Medium', 'Confidence': 'Medium'},
    {'Name': 'External Approvals', 'Status': 'Draft', 'Owner Area': 'Governance', 'Authority Level': 'Advisory', 'Runtime Impact': 'None', 'Safety Criticality': 'High', 'Confidence': 'Medium'},
    {'Name': 'Notion Ops Registry', 'Status': 'Draft', 'Owner Area': 'Ops', 'Authority Level': 'None', 'Runtime Impact': 'None', 'Safety Criticality': 'Medium', 'Confidence': 'High'},
]

safety_boundaries = [
    {'Boundary': 'Dashboard != Authority', 'Severity': 'Critical', 'Reason': 'Dashboard must remain display-only and never authorize trades.', 'Active?': 'true'},
    {'Boundary': 'AI != Authority', 'Severity': 'Critical', 'Reason': 'AI may assist analysis but must not authorize runtime trading.', 'Active?': 'true'},
    {'Boundary': 'Signal != Trade', 'Severity': 'Critical', 'Reason': 'Signals require governance, risk, and execution gates before orders.', 'Active?': 'true'},
    {'Boundary': 'Docs != Approval', 'Severity': 'Important', 'Reason': 'Documentation does not grant runtime approval.', 'Active?': 'true'},
    {'Boundary': 'Notion != Runtime Authority', 'Severity': 'Critical', 'Reason': 'Notion is operator cognition layer only.', 'Active?': 'true'},
    {'Boundary': 'Live default blocked', 'Severity': 'Critical', 'Reason': 'Live must remain gated by repo-side controls.', 'Active?': 'true'},
    {'Boundary': 'Master V2 top priority', 'Severity': 'Critical', 'Reason': 'Follow-up work must adapt to Master V2, not alter it casually.', 'Active?': 'true'},
    {'Boundary': 'No paper/test data disruption', 'Severity': 'Critical', 'Reason': 'Existing paper/test data and runs must not be disturbed.', 'Active?': 'true'},
    {'Boundary': 'No duplicate readiness/evidence surfaces', 'Severity': 'Important', 'Reason': 'Avoid parallel registries and drift.', 'Active?': 'true'},
]

def write_csv(name, rows):
    path = base / name
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    keys = list(rows[0].keys())
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

write_csv('notion_repo_assets_dry_run.csv', repo_assets)
write_csv('notion_system_map_seed.csv', system_map)
write_csv('notion_safety_boundaries_seed.csv', safety_boundaries)
(base / 'notion_export_manifest.json').write_text(json.dumps({
    'generated_at_utc': now,
    'repo_head': head,
    'files': {
        'repo_assets': 'notion_repo_assets_dry_run.csv',
        'system_map': 'notion_system_map_seed.csv',
        'safety_boundaries': 'notion_safety_boundaries_seed.csv',
    },
    'notion_runtime_authority': False,
    'repo_changed': False,
}, indent=2, sort_keys=True), encoding='utf-8')
print(f"RESULT={base}")
PY
```

### Output Files

```text
notion_repo_assets_dry_run.csv
notion_system_map_seed.csv
notion_safety_boundaries_seed.csv
notion_export_manifest.json
```

### Success Criteria

```text
CSV files generated in /tmp
Manifest says notion_runtime_authority=false
No repo changes
No Notion write yet
```

---

## 9. Phase F — Operator Review

### Goal

Human review before any Notion write/import.

### Review Checklist

Review generated files for:

```text
No secrets
No API keys
No private token leakage
No accidental runtime authorization field set to true
No false claim that Notion is source of truth
No duplicate canonical surfaces
No live/testnet/paper mutation instructions
No Master V2 logic modification
No paper/test data interference
```

### Required Manual Decisions

Operator must decide:

```text
Proceed with manual Notion CSV import?
Proceed with API-assisted Notion import?
Reduce scope to only System Map + Safety Boundaries?
Add Repo Assets now or later?
Keep relations manual for v0?
```

Recommended v0 decision:

```text
Import only:
1. System Map seed
2. Safety Boundaries seed
3. Workstreams seed

Defer full Repo Assets import until taxonomy is reviewed.
```

---

## 10. Phase G — Optional Notion Write / Import

### Goal

Populate Notion only after dry-run review.

### Preferred v0 Method

Use manual CSV import into Notion.

Reason:

```text
Lower integration risk
Human can inspect columns
No API token required in scripts
No accidental automated write loop
```

### Manual Import Steps

1. Open Notion page:

```text
Peak_Trade Ops
```

2. Open target database.

3. Import corresponding CSV.

4. Verify property mapping.

5. Verify select values.

6. Verify no runtime authority property is true.

7. Add relation links manually for initial high-value entries.

### Optional API-Assisted Import Rules

If using Notion API later:

```text
Use a dedicated integration token
Do not store token in repo
Do not print token to logs
Do not commit token
Use dry-run mode by default
Write only to explicit database IDs
Rate-limit requests
Record import manifest
Never run from trading runtime
Never allow runtime to read Notion for authorization
```

---

## 11. Phase H — Post-Import Consistency Audit

### Goal

Verify imported Notion structure matches intended model and does not create authority drift.

### Audit Checklist

For each imported database:

```text
Database exists
Properties exist
Required select values exist
Sample entries imported correctly
Relations are either correct or intentionally deferred
No property implies runtime authorization
No automation modifies repo/runtime
No secret/token exposed
```

For External Approvals:

```text
Runtime Authority? = false for all rows
Status does not directly control any bot
Approval entries link to evidence where possible
Expiry/revocation fields exist
```

For Safety Boundaries:

```text
Notion != Runtime Authority exists
Live default blocked exists
Dashboard != Authority exists
AI != Authority exists
Signal != Trade exists
```

---

## 12. Phase I — Maintenance Loop

### Goal

Keep Notion useful without turning it into a fragile duplicate source of truth.

### Recommended Maintenance Cadence

```text
After each merged PR:
  update PR / Slice Registry
  add or link closeout evidence
  update Workstream state if changed

After each major closeout:
  add Evidence & Closeout entry
  update Current State / Next Safe Action

Before starting a new workstream:
  check System Map and Workstreams
  check Safety Boundaries
  check Backlog/Parked Items

Monthly or after major architecture change:
  run read-only drift audit
```

### Drift Audit Questions

```text
Does Notion claim anything not supported by repo evidence?
Does repo have new canonical docs not linked in Notion?
Did a workstream close but Notion still says active?
Did a safety boundary change?
Did any Notion entry become stale or misleading?
Are there duplicate surfaces that should be consolidated?
```

---

## 13. Cursor Command — Repo-Wide Notion Drift Audit

### Git Context

Run on:

```text
Branch: main
Repo root: Peak_Trade repository root
Mode: read-only audit
```

### Command

```bash
cd /path/to/Peak_Trade && \
test "$(git branch --show-current)" = "main" && \
test -z "$(git status --porcelain)" && \
TS="$(date -u +%Y%m%dT%H%M%SZ)" && \
BASE="/tmp/peak_trade_notion_drift_audit_${TS}" && \
mkdir -p "$BASE" && \
PROMPT="$BASE/CURSOR_NOTION_DRIFT_AUDIT_PROMPT.md" && \
RESULT="$BASE/NOTION_DRIFT_AUDIT.md" && \
python - <<'PY' "$PROMPT"
from pathlib import Path
import sys
Path(sys.argv[1]).write_text(r'''# Cursor Multi-Agent Orchestrator Task — Peak_Trade Notion Drift Audit

## Git Context

- Branch: main
- Repo root: Peak_Trade repository root
- Mode: read-only audit
- Do not modify repo files
- Do not write to Notion
- Do not start runtime/scheduler/daemon/paper/testnet/live/broker/exchange/order-submission

## Goal

Audit whether the proposed/current Notion Knowledge Graph model would drift from repo truth.

## Required Sections

1. Executive Summary
2. Repo Truth Surfaces Found
3. Canonical Docs Found
4. Canonical Tests Found
5. Workstream State Signals Found
6. Safety Boundary Signals Found
7. Missing Notion Link Candidates
8. Potential Duplicate Surface Risks
9. Potential Stale Notion Claims
10. High-Value Updates for Notion
11. Entries That Must Remain Read-only
12. STOP Conditions
13. Final Verdict

## Required Final Lines

VERDICT=<one_line>
NEXT_ACTION=<one_line>
REPO_CHANGED=false
NOTION_CHANGED=false
RUNTIME_STARTED=false
''', encoding='utf-8')
PY
cursor-agent --print --mode ask --model gpt-5.5-extra-high < "$PROMPT" | tee "$BASE/CURSOR_AGENT_OUTPUT.txt" ; \
python - <<'PY' "$BASE/CURSOR_AGENT_OUTPUT.txt" "$RESULT"
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
text = text.replace('```markdown', '').replace('```', '')
Path(sys.argv[2]).write_text(text.strip() + '\n', encoding='utf-8')
print(f"RESULT={Path(sys.argv[2])}")
PY
```

---

## 14. First Recommended Implementation Slice

### Slice Name

```text
notion-ops-registry-v0-schema-and-seed
```

### Scope

Do:

```text
Design Notion databases
Create System Map seed
Create Safety Boundaries seed
Create Workstreams seed
Generate dry-run CSVs
Review manually
Optionally import manually into Notion
```

Do not:

```text
Modify repo code
Modify trading logic
Start runtime
Write automated Notion sync
Use Notion as gate source
Import every repo file immediately
```

### Best First Cursor Task

Use Cursor to produce:

```text
Notion schema specification
Seed entries
CSV dry-run files
Duplicate-surface risk report
Manual import checklist
```

---

## 15. Deterministic Prompt for Cursor — First Slice

### Git Context

Run on:

```text
Branch: main
Repo root: Peak_Trade repository root
Mode: read-only planning/export to /tmp only
```

### Command

```bash
cd /path/to/Peak_Trade && \
git checkout main && \
git fetch origin --prune && \
git pull --ff-only origin main && \
test -z "$(git status --porcelain)" && \
TS="$(date -u +%Y%m%dT%H%M%SZ)" && \
BASE="/tmp/peak_trade_notion_ops_registry_v0_first_slice_${TS}" && \
mkdir -p "$BASE" && \
PROMPT="$BASE/CURSOR_NOTION_OPS_REGISTRY_V0_FIRST_SLICE_PROMPT.md" && \
RESULT="$BASE/NOTION_OPS_REGISTRY_V0_FIRST_SLICE_PLAN.md" && \
python - <<'PY' "$PROMPT"
from pathlib import Path
import sys
Path(sys.argv[1]).write_text(r'''# Cursor Multi-Agent Orchestrator Task — Notion Ops Registry v0 First Slice

## Git Context

- Branch: main only
- Repo root: Peak_Trade repository root
- Mode: read-only planning plus /tmp dry-run artifacts only
- Do not modify repo files
- Do not write to Notion
- Do not start runtime/scheduler/daemon/paper/testnet/live/broker/exchange/order-submission
- Do not touch paper/test data
- Do not alter Master V2 / Double Play / Bull-Bear / Scope / Capital / Risk / KillSwitch / Execution / Live Gates

## Goal

Prepare the first safe slice for a Notion-based Peak_Trade Ops Registry / Knowledge Graph.

The repo remains the technical source of truth. Notion is only a structure, navigation, and operator review layer.

## Required Output Sections

1. Executive Summary
2. Safety Boundaries
3. Proposed v0 Databases
4. Exact Properties for Each Database
5. Select Vocabularies
6. Relations to Create
7. Seed Entries for System Map
8. Seed Entries for Workstreams
9. Seed Entries for Safety Boundaries
10. External Approvals v0 Schema
11. Evidence & Closeouts v0 Schema
12. Repo Asset Import Strategy
13. What to Defer
14. Duplicate-Surface Risk
15. Manual Notion Setup Steps
16. Manual CSV Import Steps
17. Validation Checklist
18. STOP Conditions
19. Final Verdict

## Hard Rules

- Repo = truth
- Notion = navigation only
- Notion must not authorize runtime
- External approvals in Notion are documentary evidence only
- Do not create duplicate repo surfaces unless justified
- Prefer manual CSV import for v0
- Keep full repo file import deferred unless operator approves

## Required Final Lines

VERDICT=<one_line>
NEXT_ACTION=<one_line>
IMPLEMENT_NOW=false
REPO_CHANGED=false
NOTION_CHANGED=false
RUNTIME_STARTED=false
NOTION_RUNTIME_AUTHORITY=false
''', encoding='utf-8')
PY
cursor-agent --print --mode ask --model gpt-5.5-extra-high < "$PROMPT" | tee "$BASE/CURSOR_AGENT_OUTPUT.txt" ; \
python - <<'PY' "$BASE/CURSOR_AGENT_OUTPUT.txt" "$RESULT"
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
text = text.replace('```markdown', '').replace('```', '')
Path(sys.argv[2]).write_text(text.strip() + '\n', encoding='utf-8')
print(f"RESULT={Path(sys.argv[2])}")
PY
```

---

## 16. Recommended Initial Seed Data

### 16.1 System Map Seed

```text
Master V2
Double Play
Risk Layer
KillSwitch
Scope Engine
Capital Slot Ratchet
Execution Layer
Live Gates
Scheduler / Daemon
Paper Runtime
Testnet Orchestrator
Market Dashboard
Cybersecurity Visibility Chain
Evidence Layer
External Approvals
AI/KI Cost Governance
Notion Ops Registry
```

### 16.2 Workstream Seed

```text
Market Dashboard
Cybersecurity Visibility Chain
Paper Runtime / Scheduler
Testnet Readiness
External Approvals
AI/KI Cost Controls
Evidence / Readiness
Live-Gate Hardening
Notion Knowledge Graph
Master V2 / Double Play Governance
```

### 16.3 Safety Boundary Seed

```text
Dashboard != Authority
AI != Authority
Signal != Trade
Docs != Approval
Notion != Runtime Authority
Live default blocked
Master V2 top priority
No paper/test data disruption
No duplicate readiness/evidence surfaces
Reuse before new registry surface
External approvals are evidence, not direct runtime authorization
```

---

## 17. Quality Gates

Before accepting Notion structure as useful, verify:

```text
Can I answer what each major repo area is?
Can I see which files belong to Market Dashboard?
Can I see which files are live-critical?
Can I see which docs/tests protect a system area?
Can I see what is parked but important?
Can I see recent closeouts/evidence?
Can I see why Notion is not runtime authority?
Can I see current safe next actions?
```

If the answer is no, improve structure before importing more data.

---

## 18. Failure Modes and Mitigations

### Failure Mode: Notion becomes stale

Mitigation:

```text
Treat Notion as index, not truth.
Add Last Reviewed At.
Run drift audits.
Link to repo paths and PRs.
Avoid duplicating full docs.
```

### Failure Mode: Too many repo files imported

Mitigation:

```text
Start with System Map + Workstreams + Safety Boundaries.
Import only high-value repo assets first.
Defer full file import.
```

### Failure Mode: Duplicate registries

Mitigation:

```text
Run existing surface discovery.
Mark canonical owner.
Use Notion as pointer layer.
Do not create new repo surfaces unnecessarily.
```

### Failure Mode: Notion used as approval source

Mitigation:

```text
Add Notion != Runtime Authority boundary.
Add Runtime Authority? false field.
Never connect trading runtime to Notion approvals.
Keep repo gates authoritative.
```

### Failure Mode: Cursor writes unintended changes

Mitigation:

```text
Use read-only prompts.
Assert git status before and after.
Write artifacts only to /tmp.
Review output manually.
```

---

## 19. Final Acceptance Definition

The Notion Knowledge Graph v0 is accepted when:

```text
Peak_Trade Ops root exists
Core databases exist
System Map seed exists
Workstreams seed exists
Safety Boundaries seed exists
External Approvals schema exists
Evidence & Closeouts schema exists
Repo remains unchanged unless explicitly intended
No runtime started
No Notion runtime authority exists
Operator can navigate repo concepts more clearly than before
```

---

## 20. Recommended Next Action

Recommended immediate next step:

```text
Run Phase C first: Cursor read-only Notion Knowledge Graph plan.
Then create Notion schema manually.
Then generate dry-run CSV seeds.
Then import only System Map, Workstreams, and Safety Boundaries.
```

Do not start with full repo import.

---

## 21. Final Runbook Verdict

```text
VERDICT=NOTION_KNOWLEDGE_GRAPH_V0_IS_SUITABLE_AS_OPERATOR_STRUCTURE_LAYER
NEXT_ACTION=RUN_CURSOR_READ_ONLY_PLAN_THEN_MANUAL_SCHEMA_SEED_IMPORT
REPO_REMAINS_SOURCE_OF_TRUTH=true
NOTION_RUNTIME_AUTHORITY=false
RUNTIME_START_REQUIRED=false
MASTER_V2_PROTECTED=true
```
