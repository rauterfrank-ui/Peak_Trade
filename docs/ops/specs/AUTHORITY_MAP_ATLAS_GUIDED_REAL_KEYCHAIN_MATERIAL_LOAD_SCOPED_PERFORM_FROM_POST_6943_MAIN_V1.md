# Authority-Map-/Atlas-Guided real Keychain material load scoped perform (post-6943 main, v1)

Scoped perform under `REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_OWNER_GO` only.
Uses governed ephemeral Keychain acquisition; no K1 handle, no signing, no POST, no permit mint.

## Scope

- Validate policy admission and scoped Owner-GO decision record.
- Perform `attempt_governed_credential_material_acquisition_v1` with productive macOS backend when authorized.
- Capture non-secret runtime evidence; wipe opaque material before exit.

## Non-goals

- K1 opaque signing, request signing, venue POST, permit mint perform, standing pin mutation.

## Stop boundary

Adjudicate material load perform; next Owner-GO remains K1 pre-POST boundary.
