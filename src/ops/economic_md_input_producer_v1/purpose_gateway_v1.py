"""One read-only gateway with distinct instrument/purpose policies; no selection."""

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from src.ops.economic_md_input_producer_v1.purpose_consumers_v1 import purpose_profile_digest_v1
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1


@dataclass(frozen=True)
class PurposeBoundEconomicMdGatewayV1:
    routes: object
    as_of_ms: int

    def __post_init__(self):
        if type(self.as_of_ms) is not int or self.as_of_ms <= 0:
            raise ValueError("DATA_GATEWAY_EXPLICIT_ASOF_REQUIRED")
        if not isinstance(self.routes, dict) or not self.routes:
            raise ValueError("DATA_GATEWAY_INSTRUMENT_ROUTES_REQUIRED")
        canonical = set()
        profiles = {}
        for native, sources in self.routes.items():
            if not isinstance(native, str) or not native:
                raise ValueError("DATA_GATEWAY_NATIVE_REQUIRED")
            purpose_profile_digest_v1(sources)
            ids = {s.policy.canonical_instrument_id for s in sources.values()}
            if len(ids) != 1 or canonical.intersection(ids):
                raise ValueError("DATA_GATEWAY_CANONICAL_IDENTITY_ALIAS")
            canonical.update(ids)
            profiles[native] = MappingProxyType(dict(sources))
        object.__setattr__(self, "routes", MappingProxyType(profiles))

    def profile_digest_v1(self):
        return canonical_digest_v1(
            {
                native: purpose_profile_digest_v1(dict(sources))
                for native, sources in self.routes.items()
            }
        )

    def collect_instrument_raw_input_v1(self, *, venue_native_id):
        from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
            PublicRuntimeEconomicMdPublicSourceV1,
        )

        if venue_native_id not in self.routes:
            raise ValueError("DATA_GATEWAY_INSTRUMENT_UNBOUND")
        source = self.routes[venue_native_id]["RANKING"]
        return PublicRuntimeEconomicMdPublicSourceV1(
            Path(source.store_root), source.policy, self.as_of_ms
        ).collect_instrument_raw_input_v1(venue_native_id=venue_native_id)
