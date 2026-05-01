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

## 12. Stop conditions

Stop and **do not** add UI if:

- The only available data is **`&#47;tmp`** copies or manual downloads.
- The design requires **GitHub Artifact API** from the browser or WebUI without an approved proxy read-model.
- Copy or stakeholders start using the panel language for **readiness**, **handoff**, or **promotion**.
- **PaperExecutionEngine** or live execution paths would need wiring through the hub.

## 13. References

- [**Observability Hub v0**](OBSERVABILITY_HUB_V0.md) — current hub scope; **no** Paper/Shadow artifact panel today.
- [**Market Surface v0**](../MARKET_SURFACE_V0.md) — example of read-only display boundaries (orthogonal domain).
