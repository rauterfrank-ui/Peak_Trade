# §11.12.9.27 DEPENDENCY_AUDIT RB-01/RB-02 remediation + re-run

- Owner-GO: `OWNER_GO_REQUIRED_SEPARATE_FOR_DEPENDENCY_AUDIT_REMEDIATION_BATCH_RB01_RB02_THEN_RERUN`
- Bound working SHA at evidence generation: `04aac4b99ae1cce173b0f669e0712fbdee729342`
- Run ID: `20260811T035809Z`

## Remediation

- RB-01 CLOSED: urllib3 2.6.1, pyarrow 20.0.0, msgpack 1.1.2
- RB-02 CLOSED: starlette 0.49.3 (+ fastapi 0.124.2); GAP-FGR-002 CLOSED
- requires-python raised to >=3.10 (fix versions require it); CI matrix 3.10/3.11

## Re-run (comparable lean scope)

- DEPENDENCY_AUDIT=PASS
- HIGH=0 CRITICAL=0 MEDIUM=8 LOW=2
- Original 6 blocking HIGH GHSAs: CLOSED
- Gate remains NOT_PASSED; next package SBOM_PRESENT if PASS

## Distinctions

- Remediation ≠ Pre-Live gate PASS
- PR #5862 merge not authorized by this GO
