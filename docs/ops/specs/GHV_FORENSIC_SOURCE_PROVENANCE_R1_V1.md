# GHV Forensic Source Provenance R1

Authority: **NONE** (forensic reporting only; no runtime activation).

## Scope

R1-A `forensic_source_provenance.v1` record fields emitted with every crosswalk CLI run.

R1-B fail-closed `PROOF_ELIGIBILITY` — true only when declared CURRENT SHA, actual source SHA, GHV source SHA, test execution SHA, strict snapshot binding, and `CURRENT_GRAPH_VERIFIED` align with no dirty-source ambiguity.

R1-C caller rule enforced in `scripts/ops/ghv_forensic_whole_system_crosswalk_v1/cli.py` (provenance sidecar + CLI fields).

## CLI

```bash
./scripts/pt scripts/ops/ghv_forensic_whole_system_crosswalk_v1/cli.py \
  --repo-root /path/to/pinned/checkout \
  --declared-current-sha 85908da9fd50bcda4193fd8792acb4d782cf46d9 \
  --test-execution-sha 85908da9fd50bcda4193fd8792acb4d782cf46d9
```

Output: `forensic_source_provenance_report.v1.json` in `--output-dir`.

## P01–P06 (closure summary)

| ID | Mitigation |
|----|------------|
| P01 | Declared pin + eligibility reasons; no mixed baseline in proof flag |
| P02 | `--repo-root` + actual `code_snapshot.git_head` vs declared |
| P03 | Optional strict remains contract; eligibility requires STRICT_CURRENT pass |
| P04 | NAVIGATION_ONLY → `PROOF_ELIGIBILITY=false` |
| P05 | Reporting interprets composed `source_validation_pass` vs coverage (no GHV core change) |
| P06 | New adjudication in report `p05_adjudication`; historical artifacts untouched |
