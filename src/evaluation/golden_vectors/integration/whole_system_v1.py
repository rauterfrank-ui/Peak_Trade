"""BWP-9 whole-system integration helpers (fail-closed reproof fan-out)."""

from __future__ import annotations

from src.evaluation.golden_vectors.contracts.enums import FanOutEvaluationClass
from src.evaluation.golden_vectors.runner.generic_runner_v1 import GenericRunnerV1

BWP_ID = "BWP-9"
INTEGRATED_REPROOF_CLASS = FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF


def whole_system_runner_v1() -> GenericRunnerV1:
    return GenericRunnerV1(integrated_fail_closed_reproof=INTEGRATED_REPROOF_CLASS)
