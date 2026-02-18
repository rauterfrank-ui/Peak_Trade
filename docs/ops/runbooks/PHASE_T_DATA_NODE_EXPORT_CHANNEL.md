# Phase T — Data Node + Immutable Export Channel + GitHub Consumer (Runbook)

## Goal
Build a stable, safety-first data plane where:
- Docker stacks (collectors, shadow services, optional observability) run **24/7** on an **always-on Data Node** (VPS or Bare Metal).
- Data is exported as **immutable, audit-ready snapshots** (manifest + SHA256SUMS).
- GitHub Actions consumes exports **read-only** (download + verify + tests) without requiring inbound access to the Data Node.

This avoids "GitHub must reach into your Docker host" and minimizes attack surface.

---

## Non-goals
- No execution endpoints, no live trading actions.
- No direct CI access to internal volumes/databases by default (unless explicitly approved later via self-hosted runner).

---

## Architecture (high-level)
**Data Node (always-on)**
- Runs Docker Compose: collectors + shadow services + (optional) Prometheus/Grafana.
- Runs a scheduled Export Job (cron/systemd/timer/container) to produce immutable export packs.

**Export Channel (Object Storage, S3-compatible)**
- Export packs stored by timestamp/run_id.
- Each pack contains:
  - `manifest.json` (schema, time window, source refs, code/version hashes)
  - `SHA256SUMS.stable.txt` (deterministic)
  - Payload data files (`*.parquet`, `*.jsonl`, `*.csv`, etc.)

**GitHub (Consumer)**
- Workflow downloads latest export pack (read-only credentials).
- Verifies SHA256 + manifest contract.
- Runs paper/shadow tests, contract tests, evidence registry updates.

---

## Recommended baseline choice
- **VPS + Managed Object Storage** initially.
- Upgrade to **Bare Metal** when you need sustained IO + larger local retention volumes.

---

## Security model (default)
- **No inbound** to Data Node required for CI.
- Data Node performs **outbound-only** uploads to Object Storage.
- GitHub uses **read-only** Object Storage token for downloads.
- Registry pointers remain versioned in `docs/ops/registry/` and reference **run_id / export_id**.

---

## Phase T Tasks (Agents)

### T.0 Inputs & invariants (decide once)
- Provider: VPS or Bare Metal
- Region
- Object Storage: provider + bucket
- Retention policy:
  - local retention on Data Node
  - object storage retention + versioning
- Export cadence: hourly/daily
- Export format: parquet/jsonl
- Naming convention: `export_id = YYYYMMDDTHHMMSSZ_<source>_<scope>`

---

## T.1 Provision Data Node (VPS/Bare Metal)
### On the server
- OS: Ubuntu LTS
- Firewall: default deny inbound; allow only SSH (and VPN if used)
- Install Docker + docker compose plugin
- Create dedicated user `peaktrade` (no password login)
- Enable unattended security updates

**Hard guardrails**
- Never expose internal services publicly without auth.
- Prefer VPN (WireGuard) or SSH tunneling for admin access.

---

## T.2 Deploy stacks on Data Node (Docker Compose)
Repository contains compose files; deploy only **data-plane** services:
- collectors
- shadow services (e.g. Shadow-MVS)
- optional observability (Prometheus/Grafana)

**Rule:** treat the Data Node as a controlled appliance; changes go through PRs and versioned configs.

---

## T.3 Define the Export Contract
### Directory layout (example)
Object Storage bucket `peaktrade-exports`:
- `exports/`
  - `policy_telemetry_real/`
    - `export_<export_id>/`
      - `manifest.json`
      - `SHA256SUMS.stable.txt`
      - `data/....`

### Required fields in `manifest.json` (minimum)
- `schema_version`
- `export_id`
- `created_at_utc`
- `source` (collector/shadow pipeline)
- `time_window` (`start`, `end`)
- `producer` (host id, container image tags)
- `repo_head` (git SHA of Peak_Trade at build time, if applicable)
- `files` list with expected relative paths and sha256
- `notes` (optional)

### Hashing rule
- `SHA256SUMS.stable.txt` generated deterministically:
  - stable sort of file paths
  - sha256 computed on file bytes
  - exclude `SHA256SUMS.stable.txt` itself

---

## T.4 Implement Export Job (Data Node)
Export Job produces a pack locally under:
- `out/ops/exports/export_<export_id>/...`
Then uploads to object storage (outbound).

**Implementation options**
1) systemd timer running a script
2) cron
3) a dedicated exporter container

**Exporter must**
- be deterministic
- capture versions
- fail closed on missing decision context / invalid telemetry fields
- write manifest + sha sums

---

## T.5 GitHub Consumer Workflow (download + verify + test)
GitHub Actions should:
1) Determine latest export_id (or pinned export_id from registry pointer)
2) Download pack from object storage (read-only)
3) Verify SHA256SUMS + manifest schema
4) Run contract tests/backtests/paper-tests
5) Produce artifacts/evidence packs

**No inbound to Data Node** required.

---

## T.6 Registry integration
Update/extend registry pointers (versioned) to reference:
- `repo=...`
- `workflow=...` (if relevant)
- `run_id=...` (if relevant)
- `export_bucket=...`
- `export_prefix=...`
- `export_id=...`
- `artifact_hint=...`

Keep pointers minimal; prefer immutable identifiers.

---

## T.7 Operational playbook (failure modes)
### Data Node offline
- CI can still run against last known export packs.
- Alerts should fire (optional).

### Export job failure
- No new packs; CI downloads last good pack.
- Export job logs must be captured.

### Object storage credential rotation
- Rotate write token on Data Node
- Rotate read token in GitHub secrets (least privilege)

---

## T.8 "Later" optional upgrades
- Self-hosted runner on Data Node (only if you explicitly want "near-data CI")
- Dual region exports
- Encryption-at-rest + client-side encryption for packs

---

## Acceptance criteria
- Data Node can be turned on/off independently of developer laptops.
- GitHub Actions can always download + verify a known export pack.
- Evidence/registry remains stable and audit-ready.
- No execution endpoints touched.
