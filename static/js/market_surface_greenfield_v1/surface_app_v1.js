(function () {
  "use strict";

  var body = document.body;
  var stateApi = body.getAttribute("data-state-api") || "/api/operator-trading-surface/v1/state";
  var pollTimer = null;
  var chart = null;
  var candleSeries = null;
  var lastMarket = null;
  var directView = window.PeakTradeDirectViewV1 ? window.PeakTradeDirectViewV1.load() : "MARKET";
  var fmt = window.PeakTradeSurfaceFormatV1 || {
    formatPrice: function (v) {
      return String(v);
    },
    minMoveForPrice: function () {
      return 1e-8;
    },
  };

  function el(id) {
    return document.getElementById(id);
  }

  function setText(id, value) {
    var node = el(id);
    if (node) node.textContent = value == null ? "—" : String(value);
  }

  function buildUnavailableTop20Geometry() {
    var host = el("ots-top20-geometry");
    if (!host) return;
    host.innerHTML = "";
    for (var i = 0; i < 20; i++) {
      var d = document.createElement("span");
      d.className = "ots-dot unavailable";
      d.setAttribute("aria-hidden", "true");
      host.appendChild(d);
    }
  }

  function applyRankingUniverse(system) {
    buildUnavailableTop20Geometry();
    var unknown = (system && system.unknown_sources) || {};
    setText("ots-top20-caption", "TOP20 · " + ((unknown.top20 && unknown.top20.label) || "SOURCE UNAVAILABLE"));
    setText("ots-top5-caption", "TOP5 · " + ((unknown.top5 && unknown.top5.label) || "SOURCE UNAVAILABLE"));

    var sf = (system && system.selected_future) || {};
    var mark = el("ots-selected-future-mark");
    var label = el("ots-selected-future-label");
    if (sf.symbol && sf.classification === "PROVEN_CURRENT") {
      if (label) label.textContent = sf.symbol;
      if (mark) mark.classList.add("active");
    } else {
      if (label) label.textContent = sf.classification === "UNKNOWN_CURRENT" ? "UNKNOWN" : "—";
      if (mark) mark.classList.remove("active");
    }
  }

  function applyDirectViewUi() {
    var buttons = document.querySelectorAll(".ots-dv-btn");
    buttons.forEach(function (btn) {
      var v = btn.getAttribute("data-direct-view");
      var selected = v === directView;
      btn.setAttribute("aria-selected", selected ? "true" : "false");
    });
    var mode = el("ots-chart-mode");
    var banner = el("ots-projection-banner");
    if (directView === "MARKET") {
      if (mode) mode.textContent = "MARKET TRUTH · OKX";
      if (banner) {
        banner.hidden = true;
        banner.textContent = "";
      }
      body.classList.remove("ots-view-slot");
    } else {
      if (mode) mode.textContent = "DIRECT VIEW · SLOT " + directView;
      if (banner) {
        banner.hidden = false;
        banner.classList.add("visible");
        banner.textContent =
          "Feature slot " +
          directView +
          " projection · SOURCE UNAVAILABLE · OKX candles unchanged (market truth)";
      }
      body.classList.add("ots-view-slot");
    }
  }

  function bindDirectView() {
    document.querySelectorAll(".ots-dv-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var v = btn.getAttribute("data-direct-view");
        if (window.PeakTradeDirectViewV1) {
          directView = window.PeakTradeDirectViewV1.save(v);
        } else {
          directView = v || "MARKET";
        }
        applyDirectViewUi();
      });
      btn.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          btn.click();
        }
      });
    });
    applyDirectViewUi();
  }

  function ensureChart() {
    if (chart || typeof LightweightCharts === "undefined") return;
    var host = el("ots-chart");
    if (!host) return;
    chart = LightweightCharts.createChart(host, {
      layout: { background: { color: "#080a0e" }, textColor: "#9aa3b2" },
      grid: { vertLines: { color: "rgba(255,255,255,0.05)" }, horzLines: { color: "rgba(255,255,255,0.05)" } },
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.08)", scaleMargins: { top: 0.08, bottom: 0.12 } },
      timeScale: { borderColor: "rgba(255,255,255,0.08)", timeVisible: true, secondsVisible: false },
      localization: {
        priceFormatter: function (p) {
          return fmt.formatPrice(p);
        },
      },
    });
    candleSeries = chart.addCandlestickSeries({
      upColor: "#3d9668",
      downColor: "#b85450",
      borderVisible: false,
      wickUpColor: "#3d9668",
      wickDownColor: "#b85450",
      priceFormat: {
        type: "custom",
        formatter: function (p) {
          return fmt.formatPrice(p);
        },
        minMove: 1e-8,
      },
    });
    new ResizeObserver(function () {
      if (chart && host) {
        chart.applyOptions({ width: host.clientWidth, height: host.clientHeight });
      }
      if (window.PeakTradeSurfaceGeometryV1) {
        window.PeakTradeSurfaceGeometryV1.schedule();
      }
    }).observe(host);
    if (window.PeakTradeSurfaceGeometryV1) {
      window.PeakTradeSurfaceGeometryV1.schedule();
    }
  }

  function applyMarket(market) {
    if (!market) return;
    lastMarket = market;
    setText("ots-header-instrument", market.instrument || "—");
    setText("ots-header-price", fmt.formatPrice(market.last_price));
    setText(
      "ots-header-freshness",
      (market.market_freshness || "—") + " · " + (market.market_observed_at || market.market_timestamp || "—")
    );
    setText("ots-chart-sub", market.okx_inst_id ? "OKX " + market.okx_inst_id : "—");
    setText("ots-interval", market.interval || "—");
    setText("ots-connection", market.connection_status || "—");
    ensureChart();
    if (candleSeries && Array.isArray(market.candle_series) && market.candle_series.length) {
      var lastClose = market.candle_series[market.candle_series.length - 1].close;
      candleSeries.applyOptions({
        priceFormat: {
          type: "custom",
          formatter: function (p) {
            return fmt.formatPrice(p);
          },
          minMove: fmt.minMoveForPrice(lastClose),
        },
      });
      candleSeries.setData(market.candle_series);
      if (chart) chart.timeScale().fitContent();
    }
    applyDirectViewUi();
  }

  function applyMicrovisuals(state) {
    if (window.PeakTradeSurfaceInstrumentsV1) {
      window.PeakTradeSurfaceInstrumentsV1.applyUpper(state);
      window.PeakTradeSurfaceInstrumentsV1.applyLower(state);
    }
  }

  function applyTransitionBand(system) {
    var band = el("ots-transition-band");
    if (!band || !system || !system.unknown_sources) return;
    var conf = system.unknown_sources.confirmation;
    band.textContent = "Confirmation · " + ((conf && conf.label) || "NO CANONICAL SOURCE");
  }

  function applySafety(safety) {
    var secondary = el("ots-safety-secondary");
    if (!secondary || !safety) return;
    secondary.textContent =
      "POST=" +
      safety.post_allowed +
      " · REAL_VENUE_POST=" +
      safety.real_venue_post_allowed +
      " · browser_okx=" +
      safety.direct_browser_okx;
  }

  function tick() {
    fetch(stateApi, { method: "GET", credentials: "same-origin" })
      .then(function (r) {
        return r.json();
      })
      .then(function (state) {
        applyMarket(state.market);
        applyRankingUniverse(state.system);
        applyMicrovisuals(state);
        applyTransitionBand(state.system);
        applySafety(state.safety);
        var interval = (state.poll_interval_seconds || 1) * 1000;
        if (pollTimer) clearTimeout(pollTimer);
        pollTimer = setTimeout(tick, interval);
      })
      .catch(function () {
        pollTimer = setTimeout(tick, 3000);
      });
  }

  function init() {
    buildUnavailableTop20Geometry();
    bindDirectView();
    tick();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
