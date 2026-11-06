    # RECOVERY_METADATA — scope_event_noop_root_cause_audit_v1

    RECOVERY_MODE=REGENERATED_AFTER_UNTRACKED_DELETE
    ORIGINAL_BYTES_AVAILABLE=false
    BYTE_IDENTICAL_TO_ORIGINAL=UNKNOWN
    SOURCE_BRANCH=audit/scope-event-noop-root-cause-v1
    SOURCE_BASE_SHA=a55c4000f33269a98107fd1294b1c9ba82433cad
    SOURCE_HEAD_SHA=a55c4000f33269a98107fd1294b1c9ba82433cad
    SOURCE_PRS=5338(followup_fix)
    SOURCE_TRANSCRIPTS=eaf5b5ce-7b8a-40a3-b2d4-06f8c960c4d2;00424c4d-fc3f-47a0-917a-39b5822590e2
    GENERATOR_COMMANDS=transcript Write recovery + audit_probe_v1.py re-run in temp worktree at a55c4000; bearish_bar_samples.csv preserved read-only
    SEMANTIC_MATCH=PARTIAL
    RECOVERED_AT=2026-07-18T23:23:10Z
    RECOVERY_BRANCH=recovery/reconstruct-deleted-evidence-packs-v1
    BASELINE_HEAD_AT_INCIDENT=bcf359ae5102d5e6d5d540dc42225439ad41b204
    PRESERVED_BEARISH_BAR_SAMPLES_SHA256=3d420d4d90b1f8dd869ab8fee336bf4ed0d1a2f6bb802f9f2199fb3587c941f7

    ## Present files
    - `README.md`
- `audit_probe_v1.py`
- `authority_scan.txt`
- `authority_scan_raw.txt`
- `bearish_bar_samples.csv`
- `bull_bear_candidate_counts.txt`
- `cmc_binding_analysis.txt`
- `commands.txt`
- `confirmation_analysis.txt`
- `environment.txt`
- `first_value_loss_boundary.txt`
- `fixture_short_armed_proof.txt`
- `generator_call_chain.txt`
- `generator_input_contract.txt`
- `generator_owner_map.txt`
- `noop_reason_counts.txt`
- `probe_run_log.txt`
- `probe_summary.json`
- `ruff.txt`
- `scope_state_trailing_analysis.txt`
- `test_results.txt`
- `threshold_analysis.txt`
- `verdict.txt`
- `worktree_after.txt`
- `worktree_before.txt`

    ## Placeholder / regenerated-non-original notes
    - `authority_scan_raw.txt`
- `environment.txt`
- `ruff.txt`
- `test_results.txt`
- `worktree_after.txt`
- `worktree_before.txt`

    ## Gaps / deviations
    Core analysis + verdict recovered; probe_summary regenerated at a55c4000 (UNIT_MISMATCH). bearish_bar_samples.csv unchanged. Some env/ruff/test/worktree/authority_scan_raw are placeholders.
