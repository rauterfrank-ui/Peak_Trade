# Paper/Shadow Artifact Read-model v0 (Observability — planning only)

## 1. Purpose

This document defines a **docs-only contract** for any **future** Paper/Shadow artifact visibility on **`GET &#47;observability`**. It does **not** implement UI, backend routes, artifact reads, or workflow integration.

## 2. Non-authority note

Nothing in this contract grants **execution**, **orders**, **Live&#47;Testnet** activation, **Capital&#47;Scope** approval, **Risk&#47;KillSwitch** override, **strategy authorization**, **readiness** certification, **promotion**, **deployment** approval, or **paper&#47;shadow** “go” semantics. Any future panel remains **display-only** and **non-authorizing**.

## 3. Why this doc exists before any UI panel

The Observability Hub intentionally avoids Paper/Shadow panels until a **canonical read-model** and **source boundary** exist (see [**Observability Hub v0**](OBSERVABILITY_HUB_V0.md)). Shipping UI first would risk implying readiness or evidence authority from **CI artifacts**, **`&#47;tmp`**, or ad-hoc file paths without an explicit owner and stale/snapshot contract.

## 4. Current known external artifact reviews

The following are **operator-local** offline reviews (paths illustrative; not repo paths):

- `&#47;tmp&#47;peak_trade_prj_shadow_paper_trend_review_20260501T153106Z&#47;PRJ_SHADOW_PAPER_TREND_REVIEW.md`
- `&#47;tmp&#47;peak_trade_prj_shadow_paper_semantic_review_20260501T153427Z&#47;PRJ_SHADOW_PAPER_SEMANTIC_REVIEW.md`
- `&#47;tmp&#47;peak_trade_latest_paper_shadow_artifact_inspection_20260501T152418Z&#47;LATEST_PAPER_SHADOW_ARTIFACT_INSPECTION.md`

They document **PR-J scheduled shadow+paper smoke** artifact structure and consistency findings. They are **inputs to planning**, not runtime dependencies of the WebUI.

## 5. Explicit limitation: `&#47;tmp` reviews are not WebUI data sources

Reviews under **`&#47;tmp`** are **external** to the operator WebUI process. The WebUI must **not** read **`&#47;tmp`**, mirror CI downloads into **`&#47;tmp`** for hub display, or treat these files as authoritative observability state. Linking “latest artifact” from **`&#47;tmp`** in production would be **out of scope** for this contract unless separately redesigned and approved.

## 6. Future source options (all blocked until separately implemented)

| Option | Gate |
|--------|------|
| **Existing safe `GET` read-model** | Must be documented (owner, JSON shape version, stale rules). No hub-side aggregation beyond that contract. |
| **Repo-local fixture&#47;read-model file** | Only if explicitly approved, versioned, and not a disguised evidence surface. |
| **CI artifact ingestion** | Requires source-bound design (provenance, retention, no secrets in browser, no WebUI calling GitHub Artifact API without separate security review). |

Until one option is implemented and documented, **no** Paper/Shadow hub panel.

## Source decision matrix v0.8b

This section records a **docs-only planning ranking** of candidate sources for a **future** Paper/Shadow read-model (candidates **B → A → C → D → E**; **not** alphabetical A–E). It **does not** approve any runtime source, implement a read-model, or relax §5–§8 gates.

For hub context, see [**Observability Hub v0**](OBSERVABILITY_HUB_V0.md).

### Rank 1 — Candidate B: WebUI Execution-Watch API

| Field | Detail |
|--------|--------|
| **Rank** | 1 — preferred **first** candidate for planning and field-mapping work |
| **Existing owner/surface** | Router module `src/webui/execution_watch_api_v0_2.py` — read-only **GET** list/detail/events (e.g. **`GET &#47;api&#47;execution&#47;runs`**, **`GET &#47;api&#47;execution&#47;runs&#47;{run_id}`**, events sub-path). Same WebUI process family as **`GET &#47;observability`**. |
| **Why ranked here** | Already **watch-only / read-only** in code intent; strong **testability** (fixture/query overrides); **no** separate app boundary when linking from the hub; clearest near-term **GET** inventory to document. |
| **Allowed future use** | Documented **field mapping** from Execution-Watch JSON to allowed §7 **display-only** facts; **companion links** to those GETs from the hub (when separately approved), with explicit **source-bound** and **stale/snapshot** copy. |
| **Blockers before UI** | **No** hub panel until: named **owner**, stable **schema/version** for the mapped subset, **stale** semantics and **non-readiness** copy review, and **no** hub-side **aggregation** beyond the written contract. Still **not** automatically the Paper/Shadow read-model until explicitly mapped and approved. |
| **Risk notes** | The word **execution** can suggest **authority** or **readiness**; copy and schema must stay **non-authorizing**. Payload may not match **PR-J bundle** shape without further design (**candidate C**). |

### Rank 2 — Candidate A: live.web / run snapshot

| Field | Detail |
|--------|--------|
| **Rank** | 2 |
| **Existing owner/surface** | **`src/live/web/app.py`** (and related live web models) — **`GET &#47;runs`**, **`GET &#47;runs&#47;{run_id}&#47;snapshot`**, etc. **Separate** operator web surface from the main Observability WebUI. |
| **Why ranked here** | Mature **run/snapshot** semantics; useful **operator** mental model; **file-backed** run metadata aligns with **snapshot** narrative in §9. |
| **Allowed future use** | **Companion** links or documented **cross-surface** read-model references — **not** silent merge into **`GET &#47;observability`** data plane; any future mapping must state **which process** serves the GET and **no authority** over paper/shadow **go**. |
| **Blockers before UI** | Explicit **owner** and **boundary** (separate host/port or path); **schema version** for snapshot fields used; **stale/snapshot** and **no-readiness** copy; security/ops review if cross-origin or credential boundaries apply. |
| **Risk notes** | **Second app** — easy to **confuse** with “hub truth”; must **not** imply Observability **aggregated** this data. Snapshot may reflect **execution** metrics — still **not** performance endorsement (§8). |

### Rank 3 — Candidate C: future dedicated Paper/Shadow summary endpoint

| Field | Detail |
|--------|--------|
| **Rank** | 3 — **target architecture** slot, not an existing GET today |
| **Existing owner/surface** | **None** yet; would be a **new** read-only **`GET`** (or equivalent server contract) designed for **bundle presence** / **manifest**-class fields (§7). |
| **Why ranked here** | **Cleanest** eventual fit for **PR-J / smoke bundle** shaped **presence** facts without overloading Execution-Watch or live snapshot fields; aligns with **single canonical** read-model story. |
| **Allowed future use** | **Canonical** display-only JSON (or file) with **schema version**, **generated_at**, **source label**, and **only** §7-safe fields; hub consumes **only** that contract. |
| **Blockers before UI** | **Design + implementation** (larger than wiring B/A); **owner**; **security review**; **tests**; **docs** change control; explicit **no GitHub from browser** if ingestion backs the endpoint. |
| **Risk notes** | **Scope creep** into **readiness/evidence** language — contract and copy must stay §2 / §8 clean. |

### Rank 4 — Candidate D: repo-local fixture / read-model file

| Field | Detail |
|--------|--------|
| **Rank** | 4 |
| **Existing owner/surface** | **Versioned repo paths** only if explicitly chosen (fixtures, examples); no default **canonical** path in this contract. |
| **Why ranked here** | **Excellent** for **tests** and **documentation examples**; **poor** as **live operator** truth; §6 already **gates** repo-local read-models. |
| **Allowed future use** | **CI/unit** fixtures, golden files, or **approved** static read-model snapshots — **never** as disguised **evidence** or **readiness** surface; must be **labeled** stale/example. |
| **Blockers before UI** | **Explicit approval** per §6; **no** panel that implies **repo file** == **production** artifact state; drift and **token policy** for paths. |
| **Risk notes** | **Fake readiness** — checked-in JSON can look like **sign-off**; **forbidden** framing per §8. |

### Rank 5 — Candidate E: CI artifact ingestion

| Field | Detail |
|--------|--------|
| **Rank** | 5 — **last**; highest integration and governance cost |
| **Existing owner/surface** | **No** approved WebUI or hub **GET** that surfaces GitHub Actions artifacts today; PR-J and CI semantics live under **separate** ops/CI docs, not hub runtime. |
| **Why ranked here** | Requires **provenance**, retention, **no secrets** in client, and **no** WebUI **GitHub Artifact API** without §6/§8 **separate design**; weakest **off-network** test story for the browser path. |
| **Allowed future use** | Only via a **backend** read-model (or operator pipeline) that **proxies** and **strips** secrets — **never** hidden hub **`fetch`** to CI; browser sees only an **approved** **`GET`**. |
| **Blockers before UI** | **Security review**; **no** token in browser; **no** **silent** polling; **ingestion** SLO and **stale** semantics; alignment with **RUNBOOK**-class CI authority boundaries (CI **not** hub authority). |
| **Risk notes** | **Highest** risk of **“green CI”** being read as **readiness**; **network/auth** coupling; violates hard boundaries if implemented as **WebUI-direct** artifact pull. |

### Planning-only disclaimer (v0.8b)

- This **ranking** is a **planning decision only**.
- It **does not** approve any source for **runtime** hub display.
- It **does not** implement a **runtime hub** read-model **`GET`**, production **ingest** route, or **artifact** fetch.
- It **does not** make **`&#47;tmp`**, **GitHub Actions** artifacts, or **PR-J** packs **WebUI runtime** data sources.
- The **Observability Hub** must remain **without** a wired Paper/Shadow panel until **one** source path is **separately** approved, **mapped** to §7 fields, and documented under §11.

## Dedicated summary schema v0

**Candidate C** (future dedicated Paper/Shadow summary read-model) is described by [**Paper/Shadow Summary Read-model Schema v0**](PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md) (**`paper_shadow_summary_readmodel_v0`**). A **fixture-only** in-repo **builder** materializes that schema for tests and explicit offline **`bundle_root`**; it is **not** a runtime hub source (**see that document**, Implementation status).

- The schema doc remains **planning** for **approved runtime `GET`s** and **hub** display.
- It does **not** approve a **hub** **`GET`**, **Observability** template wiring for this read-model, **browser-side artifact** fetch, or **readiness** semantics for operator truth.

## 7. Allowed future display fields (examples)

When a read-model exists, a **display-only** panel may surface **non-endorsement** facts, for example:

- Workflow **`run_id`** (or equivalent opaque id)
- **Workflow name** (as label text, not as “health”)
- **Created/updated** timestamp from the read-model (with **stale** disclaimer)
- **Artifact bundle presence** (boolean or coarse enum)
- **Manifest** / **index** presence
- **Paper** `account` / `fills` presence (not interpreted as performance)
- **Shadow** `shadow_session_summary` presence
- **P4c** / **P5a** JSON presence
- **Explicit stale&#47;snapshot** timestamp and **source label** (“from read-model X, not live infra”)

Numeric fields from smoke fixtures (e.g. cash, regime labels) may appear only as **raw snapshot** text if the read-model defines them — never as “good/bad” judgments.

## 8. Forbidden future display fields/claims

- **PnL&#47;performance endorsement** or rankings
- **Readiness approval** or “green light” language
- **Paper&#47;Testnet&#47;Live** readiness claims
- **Strategy authorization** or suggested promotion
- **Order** or **execution authority**
- **Capital&#47;Scope** approval, **Risk&#47;KillSwitch** override
- **Promotion** / **deployment** approval
- **Hidden** artifact fetch or background sync
- **`&#47;tmp`** as a **runtime** data source for the hub
- **GitHub Actions** artifact fetch from the WebUI **without** a separate approved design (API tokens, egress, abuse bounds)

## 9. Required semantics (any future UI)

- **Display-only** — no POSTs, no forms, no control plane.
- **Source-bound** — every value names its read-model source and version.
- **Stale&#47;snapshot** — operator must not treat the panel as live operator truth.
- **No mutation** — no writes to artifacts, packs, or indices from the hub.
- **No polling** unless separately approved (and then documented).
- **No hidden network calls** — no surprise `fetch` to CI or exchanges.
- **No approval semantics** — copy must not read like sign-off.

## 10. Required future `data-observability-*` markers (if a panel is ever built)

Stable contract markers (names reserved here; not yet present in templates until implementation):

- `data-observability-paper-shadow-panel=&quot;true&quot;`
- `data-observability-paper-shadow-readmodel=&quot;true&quot;`
- `data-observability-paper-shadow-no-readiness=&quot;true&quot;`
- `data-observability-paper-shadow-no-authority=&quot;true&quot;`

## 11. Future implementation prerequisites

Before adding a hub panel or route:

1. **Owner** for the read-model (team + code area).
2. **Canonical `GET`** or file contract with **schema version** and **change policy**.
3. **Security review** if the path touches CI, secrets, or cross-process data.
4. **Tests** that assert markers, forbidden phrases, and no `fetch(` in the hub template (aligned with existing hub tests).
5. **Docs update** to [**OBSERVABILITY_HUB_V0**](OBSERVABILITY_HUB_V0.md) panel table and non-goals.
6. **Drift&#47;token policy** pass for new docs paths.
7. **Fixture&#47;input path rules** — documented in [**Paper/Shadow Summary Read-model Schema v0**](PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md) (*Appendix: fixture and input path rules v0*). A **fixture-only** builder and curated **test** fixtures **exist** in-repo (see that document’s **Implementation status**). They are **not** an approved **runtime** or **hub** operator data plane; **no** **`GET &#47;observability`** wiring and **no** canonical operator **`GET`** for live bundle truth until items **1–2** and reviews **3–6** are satisfied. **No** **`&#47;tmp`** runtime source and **no** **GitHub Actions** artifact fetch **from the WebUI** without a **separate** approved design (unchanged).

## 12. Stop conditions

Stop and **do not** add UI if:

- The only available data is **`&#47;tmp`** copies or manual downloads.
- The design requires **GitHub Artifact API** from the browser or WebUI without an approved proxy read-model.
- Copy or stakeholders start using the panel language for **readiness**, **handoff**, or **promotion**.
- **PaperExecutionEngine** or live execution paths would need wiring through the hub.

## 13. References

- [**Observability Hub v0**](OBSERVABILITY_HUB_V0.md) — current hub scope; **no** Paper/Shadow artifact panel today.
- [**Paper/Shadow Summary Read-model Schema v0**](PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md) — normative JSON shape for **`paper_shadow_summary_readmodel_v0`** (Candidate C); fixture-only builder **shipped** (see Implementation status there); **no** hub **`GET`** approved here.
- [**Market Surface v0**](../MARKET_SURFACE_V0.md) — example of read-only display boundaries (orthogonal domain).
