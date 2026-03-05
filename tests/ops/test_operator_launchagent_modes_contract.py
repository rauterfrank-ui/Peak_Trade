from pathlib import Path


def test_launchagent_install_supports_mode_registry_only():
    s = Path("scripts/ops/install_operator_all_launchagent.sh").read_text(encoding="utf-8")
    assert 'MODE="${MODE:-full}"' in s
    assert 'if [ "${MODE}" = "registry_only" ]; then' in s
    assert 'RUN_E2E="false"' in s
    assert 'RUN_ONE_SHOT="false"' in s
    assert 'RUN_REGISTRY="true"' in s
