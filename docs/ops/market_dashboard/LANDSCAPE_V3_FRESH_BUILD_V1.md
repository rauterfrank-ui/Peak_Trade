# Landscape V3 Fresh Build (AUTHORITY=NONE)

Presentation-only Landscape rebuild on CURRENT EEA Public-MD runtime semantics.

- HTML: `GET &#47;market&#47;v3`
- Snapshot: `GET &#47;api&#47;market&#47;v3&#47;snapshot`
- Stream: WebSocket `&#47;api&#47;market&#47;v3&#47;stream`
- Upstream live WS: `PEAK_TRADE_PUBLIC_MARKET_DATA_RUNTIME_V1` via `OkxEeaPublicWsNetworkConnectorV1`
- Persistent host (acceptance): `scripts/webui/landscape_v3_dashboard_persistent_local_host.sh` — `RunAtLoad=false` until acceptance gates pass

V2 `/market` remains reference-only; V3 does not import V2 templates, JS, CSS, or OKX global REST polling.
