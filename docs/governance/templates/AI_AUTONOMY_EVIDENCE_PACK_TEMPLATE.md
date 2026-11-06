# EVP — Evidence Pack (Template)
**Evidence Pack ID:** EVP_YYYYMMDD_<session>_<env>  
**Related Policy Doc:** PT-GOV-AI-001  
**Env:** SHADOW / PAPER / LIVE_MANUAL_ONLY / LIVE_BOUNDED_AUTO  
**Date:** YYYY-MM-DD  
**Owner:** <name>  
**Reviewers:** <names>  
**TTL (Autonomy Lease):** <expires YYYY-MM-DD HH:MM TZ>

---

## 0. Mandatory: Layer + Model + Capability Scope

> **AUTHORITATIVE MATRIX:** `docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md` ⚠️  
> Alle Felder unten MÜSSEN mit der Matrix übereinstimmen.

### Layer Information
- **layer_id:** <L0-L6>
- **layer_name:** <e.g., Market Outlook>
- **autonomy_level:** <RO | REC | PROP> (EXEC forbidden)

### Model Assignment (Separation of Duties)
- **primary_model_id (Proposer):** <e.g., gpt-5.2-pro>
- **fallback_model_id (optional):** <e.g., gpt-5.2>
- **critic_model_id (Independent verifier):** <e.g., deepseek-r1>
- **SoD Check:** primary_model_id MUST differ from critic_model_id

### Capability Scope (Required)
- **capability_scope_id:** <e.g., L2_market_outlook_v1>
- **inputs_allowed:** <list or reference to config>
- **outputs_allowed:** <list or reference to config>
- **tooling_allowed:** <none | files | web | code-interpreter>
- **forbidden:** <execution, order placement, changing risk limits, live toggles, secrets handling>

### Logging (Required per Run)
- **run_id:** <UUID>
- **prompt_hash:** <SHA256>
- **artifact_hash:** <SHA256>
- **inputs_manifest:** <list of actual inputs used>
- **outputs_manifest:** <list of outputs generated>

---

## 0.1 Mandatory: Separation-of-Duties (SoD) Check

**SoD PASS criteria:**
- [ ] proposer_model_id != critic_model_id
- [ ] critic_decision in {APPROVE, APPROVE_WITH_CHANGES, REJECT}
- [ ] critic references evidence_ids and/or run_ids

### SoD Check Result
- **sod_result:** <PASS | FAIL>
- **proposer_run_id:** <UUID>
- **proposer_model_id:** <model_id>
- **critic_run_id:** <UUID>
- **critic_model_id:** <model_id>
- **critic_decision:** <APPROVE | APPROVE_WITH_CHANGES | REJECT>
- **critic_rationale:** <1-2 sentences>
- **evidence_ids:** <comma-separated list>

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

### 4.2 Proof / Artefacts
- **Risk Block Test Output:** <file/link>
- **Kill Switch Drill Output:** <file/link>
- **Limit Breach Simulation Output:** <file/link>
- **Flat-by-Time Evidence:** <file/link>
- **Runbook References:** <links>

---

## 5. Execution & Hot Path Integrity
- [ ] Order-Path works without AI dependency
- [ ] Execution is deterministic relative to inputs (as designed)
- [ ] Latency budget respected (if applicable)
- [ ] Error budget defined + monitored

**Artefacts:**
- **Execution Health Logs:** <file/link>
- **Latency/Errors Snapshot:** <file/link>

---

## 6. Reconstruction (Audit Trail)
### 6.1 Correlation & Event IDs
- **Decision Event IDs:** <list>
- **Order IDs / Broker IDs:** <list>
- **Correlation ID Scheme:** <description>

### 6.2 Decision Logs
- **Hold Reasons present:** yes/no
- **Inputs captured:** yes/no
- **Outputs captured:** yes/no
- **Policy/Model/Prompt versioning captured (if AI used):** yes/no

**Artefacts:**
- <paths/links>

---

## 7. Monitoring & Alerting
- **Primary On-Call:** <name/contact>
- **Escalation Path:** <steps>
- **Alert Channels:** <slack/email/ops dashboard>
- **Key Signals:** data feed, execution errors, limit breaches, drawdown, position flat-by-time

**Artefacts:**
- <paths/links>

---

## 8. Decision Summary
**Why GO/NO_GO (1–2 Absätze, klar, testbar):**  
<text>

**Known Risks & Mitigations:**  
- <risk> → <mitigation>

**Rollback/Stop Plan:**  
<text + runbook links>

---

## 9. Sign-off (Audit)
- **Owner (Constitution Authority):** ___________________ Date: ________
- **Risk Owner (if separate):** ________________________ Date: ________
- **Compliance/Observer (optional):** ___________________ Date: ________

**Next Review Trigger:** <time/event-based>
