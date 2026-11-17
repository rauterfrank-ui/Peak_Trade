"""Bind a caller-owned POST source to the existing N1 manifest startup port."""

from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import json

from src.ops.full_core_live_path_composition_root_v1.current_productive_shared_post_owner_authority_v1 import (
    PostOwnerAuthorityStoreV1,
    PostOwnerGrantV1,
    SharedPostOwnerAuthorityError,
    SharedPostOwnerAuthorizationV1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    OccupiedNetReversalPostPortV1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import (
    PreparedN1RequestV1,
)


def bind_occupied_n1_post_authority_v1(
    prepared: PreparedN1RequestV1,
    *,
    authority: PostOwnerAuthorityStoreV1,
    port: OccupiedNetReversalPostPortV1,
) -> PreparedN1RequestV1:
    """Extend a factory's prepared request with an explicitly supplied POST port.

    The owner provisions the store and the grant source. Reading the generation
    here keeps the authority binding out of the mark-to-grant lookup.
    """
    account = prepared.request["config"].expected_account_identity
    store_binding = authority.binding_digest_v1()
    runtime_config = {
        "n1_runtime_config_digest": prepared.runtime_config_digest,
        "post_account": account,
        "post_store_binding_digest": store_binding,
    }
    digest = sha256(json.dumps(runtime_config, sort_keys=True).encode()).hexdigest()

    def ready_authorization(envelope):
        authorization = port.ready_authorization(envelope)
        if authorization is not None and (
            type(authorization) is not SharedPostOwnerAuthorizationV1
            or authorization.authority != authority
            or type(authorization.grant) is not PostOwnerGrantV1
            or authorization.grant.store_binding_digest != store_binding
            or authorization.grant.account != account
        ):
            raise SharedPostOwnerAuthorityError("N1_POST_SOURCE_BINDING_MISMATCH")
        return authorization

    @contextmanager
    def open_ports(authorization):
        with prepared.open_ports(authorization) as opened:
            if "net_reversal_post_port" in opened:
                raise ValueError("N1_POST_PORT_ALREADY_BOUND")
            yield {
                **opened,
                "net_reversal_post_port": replace(port, ready_authorization=ready_authorization),
            }

    return replace(prepared, runtime_config_digest=digest, open_ports=open_ports)
