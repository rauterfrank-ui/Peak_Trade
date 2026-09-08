"""§11.14 current pos=1 flatten authority and pre-execution repair.

Defines the Flatten-GO contract, Owner issuance producer, productive
transport bind (no send), Owner Network-Session contract schema, Owner
Productive Wire-Send schema, offline wire-send evaluator, send-capable
bind, send adapter, send orchestrator, the network_session_authorized
instance-flag seam, the bound session-arming seam, and the bound
send_permitted seam. Does not flatten. Does not POST. Does not invoke
inner.send. Evaluator does not mint. Constructive NO_SEND adapter
semantics are unchanged. send_permitted is not inner.send. Fake inner.send is not productive
inner.send.
"""
