"""CURRENT_PRODUCTIVE EEA READ-ONLY universe inventory acquisition.

Input acquisition only. Not Cap-2.1 domain authority. No POST. No credentials.
Does not import IPSO / Phase-9.2 / Canary instrument authority.
"""

from __future__ import annotations

CAPABILITY_ID = "CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_ACQUISITION_V1"
OWNER = "ops.current_productive_eea_universe_inventory_acquisition_v1"
AUTHORIZED_HOST = "eea.okx.com"
FORBIDDEN_HOSTS = frozenset({"www.okx.com", "www.okx.com:443", "okx.com"})
REST_BASE = f"https://{AUTHORIZED_HOST}"
USER_AGENT = "PeakTrade-CurrentProductive-EEA-Universe-Inventory-Acquisition/1"
METHOD_GET = "GET"
CONNECT_TIMEOUT_SECONDS = 10.0
READ_TIMEOUT_SECONDS = 20.0
MAX_RETRIES = 0
MAX_REQUEST_COUNT = 4
ENDPOINT_PUBLIC_INSTRUMENTS = "/api/v5/public/instruments"
ENDPOINT_PUBLIC_MARK_PRICE = "/api/v5/public/mark-price"
REQUIRED_INST_TYPES = ("FUTURES", "SWAP")
SOURCE_KIND = "okx_eea_public_instruments"
VENUE = "okx_eea"
AUTHORITY_EFFECT = "NONE"
CAP21_NETWORK_OWNER = False
POST_COUNT = 0
LIVE_ENABLED = False
LIVE_ARMED = False
WIRE_SEND_PERMITTED = False
CANARY_INSTRUMENT_AUTHORITY_IMPORTED = False
