"""Generic evaluation-runner lifecycle observability (process death / fail-closed).

Research infrastructure only. Does not alter strategy, Master-V2, Double-Play,
risk, sizing, execution, or economic decision semantics. Does not start
evaluation runs and does not access holdout data.
"""

from __future__ import annotations

from src.research.evaluation_runner_lifecycle_observability_v1.classification_v1 import (
    INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
    RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
    classify_incomplete_run_v1,
    normalize_process_exit_v1,
)
from src.research.evaluation_runner_lifecycle_observability_v1.lifecycle_v1 import (
    EvaluationRunnerLifecycleObservabilityV1,
)
from src.research.evaluation_runner_lifecycle_observability_v1.supervised_process_v1 import (
    SupervisedProcessResultV1,
    run_supervised_python_worker_v1,
)

__all__ = [
    "INCONCLUSIVE_INFRASTRUCTURE_FAILURE",
    "RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE",
    "EvaluationRunnerLifecycleObservabilityV1",
    "SupervisedProcessResultV1",
    "classify_incomplete_run_v1",
    "normalize_process_exit_v1",
    "run_supervised_python_worker_v1",
]
