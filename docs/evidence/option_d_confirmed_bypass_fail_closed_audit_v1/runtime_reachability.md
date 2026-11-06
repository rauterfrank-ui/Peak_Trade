# Runtime Reachability

| Surface | Reachable from Classic `run_realistic`? | Notes |
|---------|----------------------------------------|-------|
| Classic offline research loop | **yes** | Many scripts&#47;tests call it |
| Integrated offline trading logic replay | **no** | Separate orchestrator; uses agreement material |
| `transition_state` &#47; Dynamic Scope | **no** | Not invoked |
| Composition matrix | **no** | Not invoked |
| Runtime integration bridge | **no** | Bridge status `BOUND_NOT_ACTIVATED` |
| Live runtime | **no** | LIVE false |

Classification of classic reachability: productive for **legacy research**, unreachable for **canonical runtime authority**.
