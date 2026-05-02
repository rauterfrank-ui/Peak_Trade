# Paper/Shadow Runtime Source Contract v0 (docs only)

## 1. Purpose

This document defines a **docs-only runtime source contract** for any **future** server-side exposure of **`paper_shadow_summary_readmodel_v0`** (e.g. a single read-only **`GET`**). It does **not** register a route, read files at runtime, or change application configuration.

It locks **who may configure the source**, **which source modes are allowed**, and **which behaviors remain forbidden** before implementation work is approved.

## 2. Non-authority note

Nothing here grants **execution**, **orders**, **Live&#47;Testnet** activation, **Capital&#47;Scope** approval, **Risk&#47;KillSwitch** override, **strategy authorization**, **readiness** certification, **promotion**, **deployment** approval, or **paper&#47;shadow** “go” semantics.

Any future **`GET`** remains **display-only** and **non-authorizing**. Numeric fields stay **source-bound counts** or **opaque snapshot** values — never performance endorsement.

## 3. Relationship to adjacent contracts

| Document | Role |
|----------|------|
| [**Paper/Shadow Summary Read-model Schema v0**](PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md) | **Normative JSON shape** for **`paper_shadow_summary_readmodel_v0`**; **Implementation status** lists the **fixture-only** builder. |
| [**Paper/Shadow Artifact Read-model v0**](PAPER_SHADOW_ARTIFACT_READ_MODEL_V0.md) | Parent **hub / observability** contract; §11 prerequisites and **forbidden** display semantics. |
| **Fixture-only builder** ([`src/webui/paper_shadow_summary_readmodel_v0/`](../../../src/webui/paper_shadow_summary_readmodel_v0/) — code path illustrative) | **Offline** materialization for **explicit `bundle_root`** (tests, scripts, operator-invoked tools). **Not** the same as an approved **runtime** WebUI source until this contract + §11 gates are satisfied. |

**This contract** governs the **runtime configuration boundary** (server-side only). **It does not** replace the schema doc or the artifact read-model; **it narrows** how a future handler may obtain **`bundle_root`**.

## 4. Direct decisions (planning)

- **No endpoint is implemented** under this document alone; naming below is **placeholder only**.
- **Preferred first runtime source mode** (when implemented): **explicit local bundle directory**, known only to the **server** via **configuration or environment** set by the **source owner** — **no** per-request path from the browser, **no** **`&#47;tmp`** default.
- **Fixture&#47;dev** exposure, if ever allowed, is **explicitly gated** (separate mode; never the implied production truth).

## 5. Source owner model

- **Owner:** the team or role responsible for **Operator WebUI &#47; Observability runtime** configuration (server process that would host the future **`GET`**).
- **Operator &#47; user &#47; browser** MUST **not** supply a **filesystem path** (query, header, path segment, or body) that maps directly to **`bundle_root`**.
- **Configuration** of the bundle location (or mode = disabled &#47; dev fixture) is **server-side only**, **auditable**, and **documented** per deployment; no “pick any directory” escape hatch.

## 6. Allowed future source modes

Modes are **planning labels**; at most **one** active mode per deployment should be documented.

| Mode | Meaning |
|------|---------|
| **Disabled &#47; no source** | Future **`GET`** (if mounted) returns **unavailable** per §10 — handler MUST NOT silently invent bundle paths. |
| **Fixture &#47; dev (gated)** | Reads only an **approved** repo-relative or server-allowlisted fixture tree; enabled **only** when an **explicit** server flag &#47; environment gate is set; MUST NOT be enabled by default in production-like environments. |
| **Explicit local bundle root** | **`bundle_root`** is a single directory on the server host, set only via **config &#47; environment** by the **source owner**; same **mechanical** bundle shape as schema **Appendix A.3**. |
| **Ingestion cache (future)** | Stable **server-local** cache populated by a **separate** ingestion &#47; promotion process; **this contract does not** design that pipeline — only acknowledges it as a **later** mode requiring its own security review. |

## 7. Forbidden source modes

The following MUST **not** be used (now or without a **new** governed contract revision):

- **Query**, **path**, or **header** parameters that carry an **arbitrary filesystem path** for **`bundle_root`**.
- **Browser-supplied** or **user-supplied** path strings.
- **Implicit default** to **`&#47;tmp`**, “latest smoke”, or any **hidden** directory guessing.
- **GitHub Actions** artifact **download** or **fetch** in the **request path** of the WebUI **`GET`**.
- **Network** I/O, **polling**, or **workflow execution** inside the handler to “refresh” bundles.
- **Recursive scan** of the host filesystem outside the **single** configured **`bundle_root`** (scan rules remain those of the **fixture builder**: only governed paths under that root; see schema appendix).

## Env/config contract v0

**Docs-only.** Names and semantics for a **future** handler; **no** code reads these variables today.

### Future route and source mode

- **Route (placeholder):** **`GET &#47;api&#47;observability&#47;paper-shadow-summary`**
- **Preferred source mode when enabled:** **explicit local bundle root** on the server host, identical mechanical shape to [**Paper/Shadow Summary Read-model Schema v0**](PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md) appendix A.3.

### Environment variables

| Variable | Semantics |
|----------|-----------|
| **`PEAK_TRADE_PAPER_SHADOW_SUMMARY_ENABLED`** | **`0`** or **`1`** only. **Default when unset:** treat as **`0`** (**disabled**). If not **`1`**, the handler MUST return **HTTP 503** with the **disabled** envelope below (no builder run). |
| **`PEAK_TRADE_PAPER_SHADOW_SUMMARY_BUNDLE_ROOT`** | **Required** only when **`ENABLED`** is **`1`**. **Server-side only** (process environment or equivalent server config); **never** from query, path, header, or body. MUST refer to an **existing directory** after `Path` resolution (implementation detail). **No** default value when required; **never** default to **`&#47;tmp`**. If **`ENABLED`** is **`1`** but this variable is **missing, empty, or not a directory**, the handler MUST return **HTTP 503** with the **unconfigured** envelope below (no builder run). |

### Request constraints (unchanged)

- **Browser &#47; client** MUST **not** supply a **filesystem path** for the bundle.
- **No** query parameter that encodes **`bundle_root`** or arbitrary FS paths.
- **`GET`** only; **no** **`POST`**.
- **No** network I/O or **GitHub Actions** artifact fetch in the handler.

### HTTP 503 JSON envelopes (disabled / unconfigured)

These bodies are **diagnostic envelopes** for **503** responses when **no** bundle scan runs. They reuse **`schema_version`** for versioning alignment but are **not** full [**Paper/Shadow Summary Read-model Schema v0**](PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md) **§7–§12** payloads (presence booleans and other required read-model fields are **absent** by design). Clients MUST **not** infer artifact presence from omitted keys.

**Disabled** (`PEAK_TRADE_PAPER_SHADOW_SUMMARY_ENABLED` unset or not **`1`**):

```json
{
  "schema_version": "paper_shadow_summary_readmodel.v0",
  "generated_at_utc": "<server-time>",
  "source_kind": "disabled",
  "stale": true,
  "warnings": ["paper_shadow_summary_source_disabled"],
  "errors": ["runtime_source_unavailable"],
  "runtime_source_status": "disabled"
}
```

**Unconfigured** (`ENABLED` is **`1`** but **`PEAK_TRADE_PAPER_SHADOW_SUMMARY_BUNDLE_ROOT`** missing, empty, or not a directory):

```json
{
  "schema_version": "paper_shadow_summary_readmodel.v0",
  "generated_at_utc": "<server-time>",
  "source_kind": "disabled",
  "stale": true,
  "warnings": ["paper_shadow_summary_bundle_root_unconfigured"],
  "errors": ["runtime_source_unavailable"],
  "runtime_source_status": "unconfigured"
}
```

**Extension field:** **`runtime_source_status`** is **not** part of the normative read-model field tables; it exists **only** on these **503** envelopes for client routing. **`200`** success responses MUST use the full read-model shape per schema (or governance-approved subset documented in OpenAPI).

## 8. Proposed future endpoint placeholder (unimplemented)

**Naming only** — not registered in code by this document:

- **`GET &#47;api&#47;observability&#47;paper-shadow-summary`**

Rules when implemented:

- **`GET`** only; **no** **`POST`**, **no** mutation semantics.
- **No** query parameter that supplies **`bundle_root`** or a subpath override for untrusted path selection.

The real path MAY change under governance but MUST remain **one** documented read-only **`GET`** consistent with [**Paper/Shadow Summary Read-model Schema v0**](PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md) §7 placeholder intent.

## 9. Request &#47; response semantics

When a handler exists and the **runtime source mode** is not **disabled**:

- **Method:** **`GET`** only.
- **Request body:** none (no body).
- **User-provided path:** none (see §5).
- **Success body (HTTP 200):** a JSON object conforming to **`paper_shadow_summary_readmodel_v0`** (i.e. **`schema_version`**, **`generated_at_utc`**, presence fields, **`stale`**, **`warnings`**, **`errors`**, etc.). **Partial** bundles and parse issues surface as **`warnings`** &#47; **`errors`** inside the **200** body — not as hidden success.
- **Unavailable source (disabled &#47; unconfigured):** see §10 — **explicit** machine-readable response; **no** silent fallback to **`&#47;tmp`**, repo fixture, or synthetic “all true”.

## 10. HTTP status guidance

| Situation | Status | Rationale |
|-----------|--------|-----------|
| Handler ran; bundle read &#47; builder completed (including domain **`warnings`** &#47; **`errors`**) | **200** | **Read-model** is the success carrier; trust caveats live in **`stale`**, **`warnings`**, **`errors`**. |
| Runtime source **disabled** or **not configured** (no valid server-side **`bundle_root`**, or mode = off) | **503 Service Unavailable** | **Canonical JSON bodies:** [**Env/config contract v0**](#envconfig-contract-v0) (disabled vs unconfigured). **Not** a full read-model payload; avoids implying a bundle was scanned. Headers: JSON (**Content-Type:** `application&#47;json`). |
| Route not mounted or feature not shipped | **404** **or** omission from OpenAPI | Deployment choice; if the route is registered but permanently off, prefer **503** with **`reason`**. |
| Unexpected handler failure (bug, uncaught exception) | **500** | Operator incident; not a domain **`errors`** list inside read-model. |

**503** is preferred over **200** with a fabricated read-model when **no** bundle was evaluated, so consumers do not misread **presence booleans** as meaningful.

## 11. Security &#47; safety constraints

- **No** secrets (tokens, Basic auth, artifact download credentials) in **URLs**, **logs**, or **responses**.
- **No** exposure of raw artifact file contents in logs; **safe metadata only** (e.g. configured mode, high-level error codes).
- **No** **WebUI** **GitHub Artifact API** from browser clients for this read-model chain.
- **Path traversal:** server MUST resolve and constrain reads to the configured root (same spirit as builder **`bundle_root`** discipline).

## 12. Stale &#47; snapshot ownership

- **`generated_at_utc`** and **`snapshot_time_utc`** in the read-model are defined by the **schema**; the **handler** does not reinterpret them as **freshness guarantees**.
- **`stale: true`** and **`stale_reason`** remain **mandatory** conservative defaults unless a **separate** governance decision documents otherwise (default expectation: **offline &#47; bundle scan** remains **non-operator-truth**).

## 13. Logging &#47; audit notes

- Log **mode** (disabled, dev-fixture, local-bundle, future-cache), **request id** if available, and **outcome** (success, 503 reason).
- **Do not** log **full paths** if they contain sensitive host layouts; prefer hashed or redacted identifiers if required by ops policy.
- **Do not** log **artifact JSON** bodies or **index** contents.

## 14. Future tests required (when implemented)

1. **Contract tests:** **`GET`** only; no accepted path query; **503** when unconfigured.
2. **Response shape:** **200** body validates required **`paper_shadow_summary_readmodel.v0`** keys for happy path (test bundle under temp dir + server-side test config).
3. **Hub &#47; template** (if linked): markers and **no** `fetch(` to GitHub; **no** readiness copy (aligned with artifact read-model §10).
4. **Regression:** presence **`true`** in JSON still implies **no** approval semantics in UI copy.

## 15. Stop conditions

Do **not** implement the **`GET`** if:

- Source **owner** and **configuration** story are undefined.
- The only story is **`&#47;tmp`** mirrors without an approved staging contract.
- Stakeholders treat **`workflow_run_id`** or **`source_commit`** as **approval**.
- **Readiness**, **handoff**, or **promotion** language would attach to the panel or **`GET`**.

## 16. Future implementation phases (ordered)

1. **Adopt** this contract in implementation specs + code review checklist.
2. **Mount** read-only **`GET`** (name per §8) with **explicit local bundle** mode only (or **disabled** by default).
3. **Optional** gated dev-fixture mode for UI development (never default prod).
4. **Later:** ingestion-backed cache mode + **Observability Hub** link **only** as **`GET`** target (no hub-side artifact read).

Each phase requires **security &#47; copy** review per [**Paper/Shadow Artifact Read-model v0**](PAPER_SHADOW_ARTIFACT_READ_MODEL_V0.md) §11.

## 17. References

- [**Paper/Shadow Summary Read-model Schema v0**](PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md)
- [**Paper/Shadow Artifact Read-model v0**](PAPER_SHADOW_ARTIFACT_READ_MODEL_V0.md)
- [**Observability Hub v0**](OBSERVABILITY_HUB_V0.md)
