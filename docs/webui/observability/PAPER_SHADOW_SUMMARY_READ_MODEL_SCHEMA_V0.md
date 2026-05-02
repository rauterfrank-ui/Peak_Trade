# Paper/Shadow Summary Read-model Schema v0 (planning only)

## 1. Purpose

This document defines a **docs-only JSON schema contract** for **`paper_shadow_summary_readmodel_v0`**, the future **dedicated** Paper/Shadow **artifact presence** summary aligned with [**Paper/Shadow Artifact Read-model v0**](PAPER_SHADOW_ARTIFACT_READ_MODEL_V0.md) §7 (allowed facts) and §8 (forbidden claims).

It does **not** implement a backend route, runtime reader, UI panel, artifact fetch, CI integration, or any **readiness** / **evidence authority** surface.

## 2. Non-authority note

Nothing here grants **execution**, **orders**, **Live&#47;Testnet** activation, **Capital&#47;Scope** approval, **Risk&#47;KillSwitch** override, **strategy authorization**, **readiness** certification, **promotion**, **deployment** approval, or **paper&#47;shadow** “go” semantics.

The read-model is **display-only** and **non-authorizing** when consumed (future). Numeric aggregates, if present, are **source-bound counts** or **opaque snapshot** values — never performance endorsement.

## 3. Relationship to `PAPER_SHADOW_ARTIFACT_READ_MODEL_V0.md`

- The [**artifact read-model v0**](PAPER_SHADOW_ARTIFACT_READ_MODEL_V0.md) is the **parent hub contract** (gates, forbidden semantics, observability boundaries).
- **This schema** is **Candidate C**: the **canonical shape** for a **future** summary document that could back **§7**-style presence display **after** separate implementation approval.
- Until a producer and **`GET`** (or approved file contract) exist, **no** hub panel may imply this schema is live data.

## 4. Adjacent surfaces (not this schema)

| Surface | Role |
|---------|------|
| **WebUI Execution-Watch API** (`GET &#47;api&#47;execution&#47;runs`, etc.) | Read-only **pipeline / execution event** observation from local JSONL; **not** PR-J artifact bundle presence. |
| **live.web** (`GET &#47;runs&#47;{run_id}&#47;snapshot`, etc.) | Read-only **run monitoring** metrics; **not** smoke-bundle **manifest/index** contract. |

These remain **companion** observability links — **not** substitutes for **`paper_shadow_summary_readmodel_v0`**.

## 5. Schema name

**`paper_shadow_summary_readmodel_v0`**

- Payload MUST include `schema_version` with value **`paper_shadow_summary_readmodel.v0`** (or a documented alias locked to this doc).

## 6. Future endpoint placeholder (unimplemented)

A **possible** future read-only route namespace ( **not** registered; **no** implementation today ):

- **`GET &#47;api&#47;observability&#47;paper-shadow-summary`**

Any real path may change under governance, but MUST remain a **single** documented **`GET`** with **no** browser-side GitHub Artifact API and **no** **`&#47;tmp`** runtime source. This section is **naming only**.

## 7. Envelope fields

| Field | Type | Meaning |
|--------|------|---------|
| `schema_version` | string | Constant identifying this contract revision. |
| `generated_at_utc` | string (ISO-8601 UTC) | When this JSON object was **materialized** (not “artifact freshness”). |
| `source_label` | string | Human-readable source label (e.g. `ingested_pack_v0`, `fixture_smoke_v0`). |
| `source_kind` | string | Machine enum for producer class (`operator_staging`, `ci_ingest_server`, `fixture`, … — exact enum TBD at implementation). |
| `source_owner` | string | Owning team or component name for the **producer** (docs accountability). |
| `stale` | boolean | **`true`** if the snapshot MUST NOT be read as current operator truth. |
| `stale_reason` | string | Short reason (e.g. `max_age_exceeded`, `ingest_partial`, `fixture`). |
| `snapshot_time_utc` | string (ISO-8601 UTC) | Boundary time for “as-of” semantics (often latest known artifact mtime or ingest cut-off). |
| `warnings` | array of string | Non-fatal caveats (no authority semantics). |
| `errors` | array of string | Fatal-to-trust issues (e.g. `manifest_unreadable`); still **not** “CI failed = go/no-go”. |

## 8. Run / source identity fields

| Field | Type | Meaning |
|--------|------|---------|
| `workflow_name` | string | **Label text only** (e.g. scheduled smoke display name). Not “health”. |
| `workflow_run_id` | string | Opaque workflow run id (e.g. CI run id string). |
| `source_commit` | string | **Optional** git SHA for traceability only — not approval. |
| `artifact_bundle_id` | string | Opaque id for the bundle root (e.g. timestamp-scoped smoke dir id). |
| `artifact_bundle_label` | string | Human-readable label for the same bundle (non-authorizing). |

## 9. Artifact presence fields (bundle / pack)

| Field | Type | Meaning |
|--------|------|---------|
| `manifest_present` | boolean | Evidence pack or root **manifest** JSON present (policy defines path). |
| `index_present` | boolean | Pack **index** JSON present. |
| `summary_present` | boolean | Root **`summary.json`** (or equivalent root summary) present. |
| `operator_context_present` | boolean | Optional operator/debug context slice present (path policy TBD; **not** extra authority). |

## 10. Paper presence fields

| Field | Type | Meaning |
|--------|------|---------|
| `paper_account_present` | boolean | Paper **`account`** JSON present. |
| `paper_fills_present` | boolean | Paper **`fills`** JSON present. |
| `paper_evidence_manifest_present` | boolean | Paper **`evidence_manifest`** present. |

## 11. Shadow presence fields

| Field | Type | Meaning |
|--------|------|---------|
| `shadow_session_summary_present` | boolean | **`shadow_session_summary`** JSON present. |
| `shadow_evidence_manifest_present` | boolean | Shadow **`evidence_manifest`** present. |
| `p4c_present` | boolean | P4c JSON artifact(s) present per policy (e.g. under **`shadow&#47;p4c`**). |
| `p5a_present` | boolean | P5a JSON artifact(s) present per policy (e.g. under **`shadow&#47;p5a`**). |

## 12. Safe aggregate fields (optional)

Included **only** if **source-bound** and **explicitly labeled** as counts from the ingest path (not interpretive):

| Field | Type | Meaning |
|--------|------|---------|
| `artifact_count` | integer (optional) | Count of enumerated artifact slots in pack index (or `null` if unknown). |
| `paper_fill_count` | integer (optional) | Count of fill rows in paper **`fills.json`** as ingested — **opaque**, not PnL or performance. |

Rules:

- MUST NOT derive **good/bad** or **ranking** from these integers.
- If counts are omitted, presence booleans still suffice for v0.

## 13. Forbidden payload semantics

The following MUST **not** appear as claims in this read-model (see §2 and parent §8):

- **PnL&#47;performance endorsement** or rankings
- **Readiness approval** or “green light”
- **Paper&#47;Testnet&#47;Live** readiness language
- **Strategy authorization** or promotion
- **Order** or **execution authority**
- **Capital&#47;Scope** approval, **Risk&#47;KillSwitch** override
- **Promotion** / **deployment** approval
- **Hidden** sync to **`&#47;tmp`**, or **`&#47;tmp`** as declared **`source_kind`**
- **GitHub Actions** artifact fetch **from the WebUI** without a **separate** approved design
- Framing as **evidence index**, **handoff**, or **sign-off** surface

## 14. Example JSON object (illustrative)

Illustrative object only — not live data:

```json
{
  "schema_version": "paper_shadow_summary_readmodel.v0",
  "generated_at_utc": "2026-05-02T00:30:00+00:00",
  "source_label": "fixture_prj_smoke_example",
  "source_kind": "fixture",
  "source_owner": "observability-docs-only-example",
  "stale": true,
  "stale_reason": "fixture",
  "snapshot_time_utc": "2026-05-02T00:29:55+00:00",
  "warnings": ["example_only_not_operational"],
  "errors": [],
  "workflow_name": "PR-J / Scheduled Shadow+Paper Features Smoke (example)",
  "workflow_run_id": "25218566510",
  "source_commit": "ef9d209a",
  "artifact_bundle_id": "20260501T144102Z",
  "artifact_bundle_label": "prj_smoke 20260501T144102Z (example)",
  "manifest_present": true,
  "index_present": true,
  "summary_present": true,
  "operator_context_present": false,
  "paper_account_present": true,
  "paper_fills_present": true,
  "paper_evidence_manifest_present": true,
  "shadow_session_summary_present": true,
  "shadow_evidence_manifest_present": true,
  "p4c_present": true,
  "p5a_present": true,
  "artifact_count": 10,
  "paper_fill_count": 2
}
```

## 15. Required future tests (when implemented)

When a producer or endpoint exists:

1. **Schema shape** tests (required keys, types, enum bounds).
2. **Hub / template** tests: reserved **`data-observability-paper-shadow-*`** markers; forbidden **readiness** phrases; **no** `fetch(` in hub unless separately approved.
3. **Regression** tests: counts present → still **no** authority strings in rendered copy.

Until then, **docs-only**; tests are **planned**, not required for merge of this schema document alone.

## 16. Stop conditions

Do **not** implement producer, **`GET`**, or UI if:

- The only path is **`&#47;tmp`** operator mirrors without an approved staging contract.
- Browser or hub template would call **GitHub Artifact API** without server-side proxy design.
- Stakeholders treat **`workflow_run_id`** or **`source_commit`** as **approval**.
- Copy drifts into **readiness**, **handoff**, or **promotion** language.

## 17. Future implementation phases (ordered)

1. **Fixture-only** builder — deterministic JSON fixture checked into **`tests`** or **`docs`** example dirs (governed).
2. **Source-bound reader** — trusted server component reads **approved** storage only; **no** WebUI secrets.
3. **Optional read-only endpoint** — e.g. **`GET &#47;api&#47;observability&#47;paper-shadow-summary`** (name may change); **GET** only.
4. **Observability display panel** — **`GET &#47;observability`** static link or server-rendered stub; **display-only**.

Each phase requires docs + security review before the next.

## Appendix: fixture and input path rules v0

### A.1 Purpose

This appendix defines **normative path and input rules** for a **future** fixture builder / bundle scanner that materializes **`paper_shadow_summary_readmodel_v0`**.

- **Docs-only:** no builder code, **no** fixture files in repo, **no** runtime reader, **no** endpoint, **no** UI exist at the time of this appendix.
- **Intent:** lock **mechanical** rules early so implementation cannot silently broaden scope.

### A.2 Allowed future fixture root

When implemented, curated fixtures are **expected** under:

- **`tests&#47;fixtures&#47;paper_shadow_summary_readmodel_v0&#47;...`**

This path is **planning-only** until separately approved; **no** tree is required to exist for this document to be valid.

### A.3 Allowed future input bundle shape (relative to bundle root)

The builder assumes a **single explicit root directory** (`bundle_root`) passed by CLI or tests — **never** an implicit global scan. Relative paths under that root:

| Relative path | Role |
|---------------|------|
| **`evidence_packs&#47;pack_prj_smoke_&lt;stamp&gt;&#47;manifest.json`** | Primary pack manifest |
| **`evidence_packs&#47;pack_prj_smoke_&lt;stamp&gt;&#47;index.json`** | Pack index (optional **`artifact_count`**) |
| **`prj_smoke&#47;&lt;stamp&gt;&#47;summary.json`** | Root summary |
| **`prj_smoke&#47;&lt;stamp&gt;&#47;paper&#47;account.json`** | Paper account |
| **`prj_smoke&#47;&lt;stamp&gt;&#47;paper&#47;fills.json`** | Paper fills |
| **`prj_smoke&#47;&lt;stamp&gt;&#47;paper&#47;evidence_manifest.json`** | Paper evidence manifest |
| **`prj_smoke&#47;&lt;stamp&gt;&#47;shadow&#47;shadow_session_summary.json`** | Shadow session summary |
| **`prj_smoke&#47;&lt;stamp&gt;&#47;shadow&#47;evidence_manifest.json`** | Shadow evidence manifest |
| **`prj_smoke&#47;&lt;stamp&gt;&#47;shadow&#47;p4c&#47;*.json`** | At least one P4c JSON (glob) |
| **`prj_smoke&#47;&lt;stamp&gt;&#47;shadow&#47;p5a&#47;*.json`** | At least one P5a JSON (glob) |

`<stamp>` is an opaque token (e.g. UTC compact timestamp); **`artifact_bundle_id`** in the summary SHOULD align with it when the directory names match.

### A.4 Required vs optional semantics

- **Complete mirror (PR-J-shaped):** **`manifest_present`**, **`index_present`**, **`summary_present`**, **`paper_account_present`**, **`paper_fills_present`**, **`paper_evidence_manifest_present`**, **`shadow_session_summary_present`**, **`shadow_evidence_manifest_present`**, **`p4c_present`**, **`p5a_present`** all reflect successful path resolution and (where applicable) minimum parse checks per implementation spec.
- **`operator_context_present`:** **not** defined in v0; reserved until a **separate** path policy exists.
- **Partial bundle:** builder MUST set **`stale: true`**, populate **`warnings`** / **`errors`**, and MUST **not** coerce missing slots to **`true`**.

### A.5 Mapping rules

- **Presence** is **`true`** only when the governed path exists (and glob rule satisfied for P4c/P5a).
- **`artifact_count`** / **`paper_fill_count`:** only from **successful** parse of **`index.json`** / **`fills.json`** per written rules; on failure → `null` + warning.
- **`workflow_run_id`**, **`workflow_name`**, **`source_commit`:** only from **explicit** builder input (CLI args or **approved** sidecar JSON) — **no** hidden **network** or **git** inference.

### A.6 Missing / malformed handling

- **Missing file** → corresponding **`_present`** field **`false`**; add **`warnings`** or **`errors`** per severity.
- **Malformed JSON** where **parse is required** for that slot → **`_present`** **`false`** (or keep **`false`** for derived counts), record **`errors`** (e.g. `fills_json_unreadable`).
- **Never** coerce unknown or ambiguous state to **`true`**.

### A.7 Forbidden runtime / source behavior

- **No** **`&#47;tmp`** as an approved **runtime** source for WebUI-facing chains (parent contract §5).
- **No** **GitHub Actions** artifact **fetch** inside the builder for **v0** tests; fixtures are **local directory** only.
- **No** **network** I/O, **no** **polling**, **no** recursive scan outside **`bundle_root`**.

### A.8 Forbidden inference

The builder MUST NOT emit summary semantics that imply:

- **Readiness**, **sign-off**, **handoff**
- **PnL&#47;performance endorsement**, strategy merit, promotion, deployment approval
- **Order** or **execution authority**, **Paper&#47;Testnet&#47;Live** readiness
- **Capital&#47;Scope** approval, **Risk&#47;KillSwitch** override

(Structural **`errors`** about missing files are allowed — they are **not** CI go/no-go.)

### A.9 Future test strategy (when builder exists)

- **Fixture-only** unit tests under **`tests&#47;fixtures&#47;paper_shadow_summary_readmodel_v0&#47;...`**
- Optional **golden** JSON comparison (deterministic key order policy).
- **No** **`gh`**, **no** network, in the default test path.
- Assert **exact** **`warnings`** / **`errors`** for missing and malformed files in negative fixtures.

## 18. References

- [**Paper/Shadow Artifact Read-model v0**](PAPER_SHADOW_ARTIFACT_READ_MODEL_V0.md) — parent contract, §7–§8, source matrix v0.8b.
- [**Observability Hub v0**](OBSERVABILITY_HUB_V0.md) — hub boundaries; no wired Paper/Shadow panel today.
- [**Market Surface v0**](../MARKET_SURFACE_V0.md) — orthogonal read-only display precedent.
