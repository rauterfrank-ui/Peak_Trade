# EVP — Evidence Pack (Template v2 - Layer Map Compatible)

**Evidence Pack ID:** EVP_YYYYMMDD_<session>_<env>_<layer_id>  
**Related Policy Doc:** PT-GOV-AI-001  
**Layer ID:** L0 / L1 / L2 / L3 / L4 / L5 / L6  
**Env:** SHADOW / PAPER / LIVE_MANUAL_ONLY / LIVE_BOUNDED_AUTO  
**Date:** YYYY-MM-DD  
**Owner:** <name>  
**Reviewers:** <names>  
**TTL (Autonomy Lease):** <expires YYYY-MM-DD HH:MM TZ>

---

## METADATA (Layer Map v1 Integration)

> **AUTHORITATIVE MATRIX:** `docs/governance/ai_autonomy/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`  
> Alle Felder unten MÜSSEN mit der Matrix übereinstimmen.

### Layer Information
- **Matrix Version:** <version from AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md>
- **Layer ID:** <L0-L6>
- **Layer Name:** <Name from Matrix>
- **Layer Description:** <Purpose from Matrix>
- **Autonomy Level:** <RO / REC / PROP / EXEC (forbidden) from Matrix>
- **Capability Scope ID:** <capability_scope_id from config/capability_scopes/>
- **Capability Scope Version:** <version>

### Model Assignment (Separation of Duties)
- **Primary Model (Proposer):** <model_id>
- **Fallback Model:** <model_id>
- **Critic Model (Verifier):** <model_id>
- **SoD Check Status:** PASS / FAIL (Proposer ≠ Critic)
- **Model Registry Version:** <version from config/model_registry.toml>

### Run Artifacts
- **Proposer Run ID:** <run_id>
- **Critic Run ID:** <run_id>
- **Proposer Artifact Hash (SHA256):** <hash>
- **Critic Artifact Hash (SHA256):** <hash>
- **Prompt Hash (SHA256):** <hash>
- **Inputs Manifest:** <list or link>
- **Outputs Manifest:** <list or link>

### Decision (Critic Output)
- **Critic Decision:** APPROVE / APPROVE_WITH_CHANGES / REJECT
- **Rationale:** <1-2 sentences>
- **Evidence IDs Referenced:** <comma-separated EV-IDs>
- **Related Evidence Packs:** <comma-separated EVP-IDs>

---

## 1. Scope (Day Trading)
- **Instrument Universe:** <symbols/venues>
- **Session Window:** <start/end times>
- **Flat-by-Time:** <time + enforcement mechanism>
- **Max Trades/Day:** <number>
- **Max Exposure:** <definition>
- **Daily Loss Limit:** <value + enforcement>

---

## 2. System Identity (Reproducibility)
- **Repo Root:** <path>
- **Commit SHA:** <sha>
- **Branch/Tag:** <branch/tag>
- **Build/Package Version:** <version>
- **Config Snapshot:** <path or embedded excerpt, secrets redacted>
- **Runtime Mode:** <paper/live/shadow>
- **Dependencies Lock:** <poetry/uv/pip freeze ref, optional>

---

## 3. Governance / Policy
- **Go/No-Go Decision:** GO / NO_GO
- **Target State:** PAPER_GO / LIVE_MANUAL_ONLY / LIVE_BOUNDED_AUTO
- **Policy Version (PT-GOV-AI-001):** <version>
- **AI Roles Matrix Version:** <doc + version>
- **Model Placement Doc Version:** <doc + version>
- **Layer Map Version:** <version from docs/architecture/ai_autonomy_layer_map_v1.md>

### 3.1 Autonomy Lease (if GO)
- **TTL Expiry:** <timestamp>
- **Scope:** <instruments, sessions, constraints>
- **Autonomy Budget:** <limits: loss, exposure, trades, leverage>
- **Revocation Mechanism:** <how revoke is enforced + proof link>

---

## 4. Risk & Safety Controls (MUST)

### 4.1 Controls Status
- [ ] Risk can block orders (proof attached)
- [ ] Kill Switch functional and tested
- [ ] Daily Loss Limit functional and tested
- [ ] Flat-by-Time functional and tested
- [ ] Cooldown/Circuit Breaker rules defined and tested
- [ ] No online-learning influences live behavior (proof attached)

### 4.2 Layer-Specific Safety Checks (from Capability Scope)
- [ ] Capability Scope enforced (inputs/outputs/tooling validated)
- [ ] No forbidden outputs generated
- [ ] No forbidden tools accessed
- [ ] SoD Check passed (Proposer ≠ Critic)
- [ ] Logging complete (all required fields present)

### 4.3 Proof / Artefacts
- **Risk Block Test Output:** <file/link>
- **Kill Switch Drill Output:** <file/link>
- **Limit Breach Simulation Output:** <file/link>
- **Flat-by-Time Evidence:** <file/link>
- **Capability Scope Enforcement Log:** <file/link>
- **SoD Check Log:** <file/link>
- **Runbook References:** <links>

---

## 5. Execution & Hot Path Integrity
- [ ] Order-Path works without AI dependency
- [ ] Execution is deterministic relative to inputs (as designed)
- [ ] Latency budget respected (if applicable)
- [ ] Error budget defined + monitored
- [ ] AI Layer outputs are advisory only (not in hot path)

**Artefacts:**
- **Execution Health Logs:** <file/link>
- **Latency/Errors Snapshot:** <file/link>

---

## 6. Reconstruction (Audit Trail)

### 6.1 Correlation & Event IDs
- **Decision Event IDs:** <list>
- **Order IDs / Broker IDs:** <list>
- **Correlation ID Scheme:** <description>
- **AI Run IDs (Proposer + Critic):** <run_ids>

### 6.2 Decision Logs
- **Hold Reasons present:** yes/no
- **Inputs captured:** yes/no
- **Outputs captured:** yes/no
- **Policy/Model/Prompt versioning captured:** yes/no
- **Capability Scope logged:** yes/no
- **SoD Check logged:** yes/no

**Artefacts:**
- **AI Model Call Logs:** <file/link> (logs/ai_model_calls.jsonl)
- **Proposer Output:** <file/link>
- **Critic Output:** <file/link>

---

## 7. Monitoring & Alerting
- **Primary On-Call:** <name/contact>
- **Escalation Path:** <steps>
- **Alert Channels:** <slack/email/ops dashboard>
- **Key Signals:** data feed, execution errors, limit breaches, drawdown, position flat-by-time, capability scope violations, SoD failures

**Artefacts:**
- **Monitoring Dashboard:** <link>
- **Alert Config:** <file/link>

---

## 8. Layer-Specific Compliance (from Capability Scope)

### 8.1 Inputs Validation
- **Inputs Allowed (as per Capability Scope):** <list>
- **Inputs Forbidden (as per Capability Scope):** <list>
- **Actual Inputs Used:** <list>
- **Validation Status:** PASS / FAIL

### 8.2 Outputs Validation
- **Outputs Allowed (as per Capability Scope):** <list>
- **Outputs Forbidden (as per Capability Scope):** <list>
- **Actual Outputs Generated:** <list>
- **Validation Status:** PASS / FAIL

### 8.3 Tooling Validation
- **Tooling Allowed (as per Capability Scope):** <list>
- **Tooling Forbidden (as per Capability Scope):** <list>
- **Actual Tooling Used:** <list>
- **Validation Status:** PASS / FAIL

---

## 9. Decision Summary
**Why GO/NO_GO (1–2 Absätze, klar, testbar):**  
<text>

**Known Risks & Mitigations:**  
- <risk> → <mitigation>

**Rollback/Stop Plan:**  
<text + runbook links>

---

## 10. Sign-off (Audit)
- **Owner (Constitution Authority):** ___________________ Date: ________
- **Risk Owner (if separate):** ________________________ Date: ________
- **Compliance/Observer (optional):** ___________________ Date: ________

**Next Review Trigger:** <time/event-based>

---

## 11. Version History

| Version | Date | Changes | Author |
|---|---|---|---|
| v2.0 | 2026-01-08 | Added Layer Map v1 integration: layer_id, model_id, capability_scope_id, SoD checks | ops |
| v1.0 | <date> | Initial template | ops |

---

## 12. Referenzen

- **Layer Map v1:** `docs/architecture/ai_autonomy_layer_map_v1.md`
- **Capability Scope:** `config/capability_scopes/<layer_id>_*.toml`
- **Model Registry:** `config/model_registry.toml`
- **Policy Critic Charter:** `docs/governance/LLM_POLICY_CRITIC_CHARTER.md`
- **GoNoGo Overview:** `docs/governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`

---

**END OF EVIDENCE PACK**
