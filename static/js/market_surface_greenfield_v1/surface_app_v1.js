(function () {
  "use strict";

  var body = document.body;
  var stateApi = body.getAttribute("data-state-api") || "/api/operator-trading-surface/v1/state";
  var pollTimer = null;
  var chart = null;
  var candleSeries = null;

  function el(id) {
    return document.getElementById(id);
  }

  function setText(id, value) {
    var node = el(id);
    if (node) node.textContent = value == null ? "—" : String(value);
  }

  function renderUnknown(list) {
    var ul = el("ots-unknown-list");
    if (!ul || !list) return;
    ul.innerHTML = "";
    Object.keys(list).forEach(function (key) {
      var li = document.createElement("li");
      var entry = list[key] || {};
      li.textContent = key.toUpperCase() + "  " + (entry.label || entry.status || "UNKNOWN");
      ul.appendChild(li);
    });
  }

  function ensureChart() {
    if (chart || typeof LightweightCharts === "undefined") return;
    var host = el("ots-chart");
    if (!host) return;
    chart = LightweightCharts.createChart(host, {
      layout: { background: { color: "#0a0c10" }, textColor: "#9aa3b2" },
      grid: { vertLines: { color: "rgba(255,255,255,0.04)" }, horzLines: { color: "rgba(255,255,255,0.04)" } },
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
      timeScale: { borderColor: "rgba(255,255,255,0.08)" },
    });
    candleSeries = chart.addCandlestickSeries({
      upColor: "#3d9668",
      downColor: "#b85450",
      borderVisible: false,
      wickUpColor: "#3d9668",
      wickDownColor: "#b85450",
    });
    new ResizeObserver(function () {
      if (chart && host) chart.applyOptions({ width: host.clientWidth, height: host.clientHeight });
    }).observe(host);
  }

  function applyMarket(market) {
    if (!market) return;
    setText("ots-instrument", market.instrument || "—");
    setText("ots-okx-inst", market.okx_inst_id ? "OKX " + market.okx_inst_id : "—");
    setText("ots-last-price", market.last_price != null ? market.last_price : "—");
    setText("ots-market-freshness", market.market_freshness + " · " + (market.market_timestamp || "—"));
    setText("ots-interval", market.interval || "—");
    setText("ots-connection", market.connection_status || "—");
    ensureChart();
    if (candleSeries && Array.isArray(market.candle_series) && market.candle_series.length) {
      candleSeries.setData(market.candle_series);
    }
  }

  function applySystem(system) {
    if (!system) return;
    var sf = system.selected_future || {};
    setText(
      "ots-selected-future",
      sf.symbol ? sf.symbol + " (" + (sf.classification || "") + ")" : sf.classification || "UNKNOWN"
    );
    var tc = system.trade_counters || {};
    if (tc.trades_set == null && tc.trades_rejected == null) {
      setText("ots-trade-counters", "UNKNOWN (no run/events)");
    } else {
      setText("ots-trade-counters", "set=" + tc.trades_set + " rejected=" + tc.trades_rejected);
    }
    var opt = system.optimization || {};
    setText("ots-optimization", opt.experiment_count != null ? "experiments=" + opt.experiment_count : opt.note || "—");
    renderUnknown(system.unknown_sources);
  }

  function applySafety(safety) {
    if (!safety) return;
    setText(
      "ots-safety",
      "POST=" +
        safety.post_allowed +
        " REAL_VENUE_POST=" +
        safety.real_venue_post_allowed +
        " browser_okx=" +
        safety.direct_browser_okx
    );
  }

  function tick() {
    fetch(stateApi, { method: "GET", credentials: "same-origin" })
      .then(function (r) {
        return r.json();
      })
      .then(function (state) {
        applyMarket(state.market);
        applySystem(state.system);
        applySafety(state.safety);
        var interval = (state.poll_interval_seconds || 1) * 1000;
        if (pollTimer) clearTimeout(pollTimer);
        pollTimer = setTimeout(tick, interval);
      })
      .catch(function () {
        pollTimer = setTimeout(tick, 3000);
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", tick);
  } else {
    tick();
  }
})();
