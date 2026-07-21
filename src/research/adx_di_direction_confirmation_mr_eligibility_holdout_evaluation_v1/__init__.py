"""Research-only HOLDOUT evaluation for ADX DI direction-confirmation MR eligibility v1.

Exactly one authorized holdout run of the already terminal DEVELOPMENT PASS of
``ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1``.
No productive Master-V2 / Double-Play / risk / sizing / execution mutation.
No promotion / runtime / orders. Requires a separate explicit operator GO
(``PEAK_TRADE_ADX_DI_HOLDOUT_EXECUTION_GO=true``) in addition to this package
existing; import alone does not access sealed holdout data or execute anything.
"""

ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_HOLDOUT_EVALUATION_V1 = True
HOLDOUT_EXECUTION_IMPLEMENTED = True

PACKAGE_MARKER = "ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_HOLDOUT_EVALUATION_V1=true"
