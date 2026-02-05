# Testing Modes

## Default (restricted/sandbox-safe)

Runs the full suite and allows environment-dependent tests to skip gracefully.

```bash
python3 -m pytest -q -ra
```

Tests that need network (socket bind on localhost) or external tools (e.g. `uv`) are marked with `network` or `external_tools` and will skip in restricted environments instead of failing.

## Exclude network and external-tools tests (fast, sandbox)

To run only tests that do not require port bind or `uv`:

```bash
python3 -m pytest -q -ra -m "not network and not external_tools"
```

## CI-parity (run everything including network/external_tools)

On a machine or runner with permissions and `uv` available, run the full suite including network and external-tools tests:

```bash
python3 -m pytest -q -ra
```

To run *only* the environment-dependent tests (e.g. to verify they pass in CI):

```bash
python3 -m pytest -q -ra -m "network or external_tools"
```

## Markers

- **`network`** – requires permission to bind/listen on localhost ports (obs demos, prom helpers, port checks).
- **`external_tools`** – requires tools like `uv` to be installed and functional (e.g. recon_audit_gate wrapper).

Defined in `pytest.ini`. Use `PEAKTRADE_NO_UV_SMOKE=1` to force-skip uv-dependent wrapper smoke tests even when `uv` is present (e.g. when `uv` panics in the environment).
