"""R12 EG-I44 dedicated funding accounting contract v1.

Read-only forensic overlay. Does not activate funding, close Master G16,
or implement IG-I44-FUNDING-IF-ACTIVATED.
"""

from __future__ import annotations

from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    PACKAGE_MARKER,
    REMEDIATION_ID,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.contract_v1 import (
    STRUCTURAL_CONTRACT,
    require_contract_item,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.dimensions_v1 import (
    require_dimension,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.models_v1 import (
    ContractItemStatus,
    R12EgI44FundError,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.verifier_v1 import (
    evaluate_r12_eg_i44_fund_dedicated_funding_accounting_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "ContractItemStatus",
    "PACKAGE_MARKER",
    "R12EgI44FundError",
    "REMEDIATION_ID",
    "STRUCTURAL_CONTRACT",
    "evaluate_r12_eg_i44_fund_dedicated_funding_accounting_v1",
    "require_contract_item",
    "require_dimension",
]
