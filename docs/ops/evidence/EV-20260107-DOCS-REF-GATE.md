# Evidence Entry: Docs Reference Targets Gate - Link Debt Tracking System

**Evidence ID:** EV-20260107-DOCS-REF-GATE
**Date:** 2026-01-07
**Category:** Ci/Workflow
**Owner:** ops
**Status:** DRAFT

---

## Scope
Docs Reference Targets Gate CI workflow and link debt tracking system. Covers automated validation of markdown internal links, baseline tracking (DOCS_REFERENCE_TARGETS_BASELINE.json), and triage process for broken references.

---

## Claims
- CI workflow `docs-reference-targets-gate.yml` validates all markdown internal links on every PR
- Baseline tracking system established: 600 markdown files, 4250 references tracked (as of 2026-01-01)
- Triage process documented: Priority 1 (ops/risk-critical), Priority 2 (merge logs), Priority 3 (legacy docs)
- Gate prevents new broken links from merging (exit 1 on missing targets)
- Debt reduction workflow: verify_docs_reference_targets.sh + DEBT_GUIDE.md + TRIAGE doc

---

## Evidence / Source Links
- [CI Workflow: docs-reference-targets-gate.yml](../../../.github/workflows/docs_reference_targets_gate.yml)
- [Triage Report 2026-01-01](../DOCS_REFERENCE_TARGETS_TRIAGE_20260101.md)
- [Debt Guide](../DOCS_REFERENCE_TARGETS_DEBT_GUIDE.md)
- [Gate Style Guide](../DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md)
- [Baseline Snapshot](../DOCS_REFERENCE_TARGETS_BASELINE.json)
- [Validator Script](../../../scripts/ops/verify_docs_reference_targets.sh)

---

## Verification Steps
1. Check CI workflow exists: `cat .github/workflows/docs_reference_targets_gate.yml`
2. Run validator locally: `./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main`
3. Inspect baseline: `jq '.metadata' docs&#47;ops&#47;DOCS_REFERENCE_TARGETS_BASELINE.json`
4. Expected: Gate runs on every PR, fails on new broken links, baseline tracks 4250+ references

---

## Risk Notes
- Gate is **preventive only**: does not fix existing debt (198 missing targets as of 2026-01-01)
- Priority 1 debt (ops/risk-critical) requires manual triage and fixes
- False positives possible for dynamically generated files or external links
- Baseline drift: requires periodic regeneration via `collect_docs_reference_targets_fullscan.py`

---

## Related PRs / Commits
- Baseline established: commit b9171fec (2026-01-01)
- Triage session: 2026-01-01 (Priority 1: 198 missing targets identified)
- CI workflow: active in `.github/workflows/docs_reference_targets_gate.yml`

---

## Owner / Responsibility
**Owner:** ops
**Contact:** [TBD]

---

**Entry Created:** 2026-01-07
**Last Updated:** 2026-01-07
**Template Version:** v0.2
