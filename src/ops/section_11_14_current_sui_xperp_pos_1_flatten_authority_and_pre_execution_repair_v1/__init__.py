"""§11.14 current pos=1 flatten authority and pre-execution repair.

Defines the Flatten-GO contract, Owner issuance producer, productive
transport bind (no send), Owner Network-Session contract schema, Owner
Productive Wire-Send schema, offline wire-send evaluator, send-capable
bind, send adapter, send orchestrator, the network_session_authorized
instance-flag seam, the bound session-arming seam, the bound
send_permitted seam, the fake inner.send seam, the productive
inner.send fail-closed receipt boundary, the flatten pre-send
receipt authority adjudication, and the RECEIPT_MISSING attachable
mint. Does not flatten. Does not POST. Does not HMAC-sign.
Constructive NO_SEND adapter semantics are unchanged. Productive
inner.send is not HMAC generation, lease consume, HTTP POST, or
wire-send.
"""
