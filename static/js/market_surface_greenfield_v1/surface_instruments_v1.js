(function () {
  "use strict";

  function el(id) {
    return document.getElementById(id);
  }

  function setText(id, value) {
    var node = el(id);
    if (node) node.textContent = value == null ? "—" : String(value);
  }

  function clearHost(id) {
    var host = el(id);
    if (host) host.innerHTML = "";
    return host;
  }

  function classificationLabel(cls) {
    if (cls === "PROVEN_CURRENT") return "PROVEN";
    if (cls === "UNKNOWN_CURRENT") return "UNKNOWN";
    return "UNAVAILABLE";
  }

  function renderSelectionLane(system) {
    var host = clearHost("ots-selection-lane");
    if (!host) return;
    var sf = (system && system.selected_future) || {};
    if (sf.classification === "PROVEN_CURRENT" && sf.symbol) {
      var rank = document.createElement("span");
      rank.className = "ots-lane-mark proven";
      rank.style.setProperty("--ots-lane-pos", String(Math.min(100, Math.max(0, ((sf.rank || 1) - 1) * 8))));
      rank.title = "rank " + sf.rank;
      host.appendChild(rank);
      var track = document.createElement("span");
      track.className = "ots-lane-track proven";
      host.appendChild(track);
      setText(
        "ots-selection-detail",
        sf.symbol + " · rank " + (sf.rank != null ? sf.rank : "—") + " · PROVEN"
      );
      return;
    }
    var unknown = document.createElement("span");
    unknown.className = "ots-lane-track unknown";
    host.appendChild(unknown);
    setText("ots-selection-detail", "UNKNOWN · " + classificationLabel(sf.classification));
  }

  function renderMarketHealthLane(market) {
    var host = clearHost("ots-market-health-lane");
    if (!host) return;
    var freshness = ((market && market.market_freshness) || "UNKNOWN").toUpperCase();
    var connection = ((market && market.connection_status) || "UNKNOWN").toUpperCase();
    var refresh = ((market && market.refresh_status) || "—").toString().toUpperCase();
    var segFresh = document.createElement("span");
    segFresh.className = "ots-lane-seg ots-lane-seg-" + freshness.toLowerCase();
    segFresh.title = "freshness " + freshness;
    host.appendChild(segFresh);
    var segConn = document.createElement("span");
    segConn.className = "ots-lane-seg ots-lane-seg-" + connection.toLowerCase();
    segConn.title = "connection " + connection;
    host.appendChild(segConn);
    var segRefresh = document.createElement("span");
    segRefresh.className =
      refresh.indexOf("OK") >= 0 || refresh.indexOf("SKIPPED") >= 0
        ? "ots-lane-seg ots-lane-seg-fresh"
        : "ots-lane-seg ots-lane-seg-unknown";
    segRefresh.title = "refresh " + refresh;
    host.appendChild(segRefresh);
    setText(
      "ots-market-health-detail",
      freshness + " · " + connection + " · refresh " + (market && market.refresh_status ? market.refresh_status : "UNKNOWN")
    );
  }

  function renderSafetyLane(safety) {
    var host = clearHost("ots-safety-lane");
    if (!host) return;
    if (!safety) {
      setText("ots-safety-lane-detail", "UNKNOWN");
      return;
    }
    var blocks = [
      { key: "post", on: safety.post_allowed === true, label: "POST" },
      { key: "venue", on: safety.real_venue_post_allowed === true, label: "VENUE POST" },
      { key: "ext", on: safety.external_effect_authorized === true, label: "EXT EFFECT" },
      { key: "okx", on: safety.direct_browser_okx === true, label: "BROWSER OKX" },
    ];
    blocks.forEach(function (b) {
      var seg = document.createElement("span");
      seg.className = "ots-lane-seg " + (b.on ? "ots-lane-seg-hot" : "ots-lane-seg-blocked");
      seg.title = b.label + "=" + b.on;
      host.appendChild(seg);
    });
    setText(
      "ots-safety-lane-detail",
      "READ ONLY · POST blocked · mutations " + (safety.pt_mutation_routes != null ? safety.pt_mutation_routes : "—")
    );
  }

  function renderConfirmationLane(system) {
    var host = clearHost("ots-confirmation-lane");
    if (!host) return;
    var conf = system && system.unknown_sources && system.unknown_sources.confirmation;
    var label = (conf && conf.label) || "NO CANONICAL SOURCE";
    var track = document.createElement("span");
    track.className = "ots-lane-track unavailable";
    host.appendChild(track);
    setText("ots-confirmation-detail", label + " · " + classificationLabel("UNKNOWN_CURRENT"));
  }

  function renderGapMatrix(system) {
    var host = clearHost("ots-gap-matrix");
    if (!host || !system || !system.unknown_sources) return;
    var keys = Object.keys(system.unknown_sources);
    keys.forEach(function (key) {
      var cell = document.createElement("span");
      cell.className = "ots-gap-cell unavailable";
      cell.title = key + ": " + (system.unknown_sources[key].label || "UNKNOWN");
      host.appendChild(cell);
    });
    setText("ots-gap-detail", keys.length + " canonical gaps · no synthesis");
  }

  function renderTradeTrace(system) {
    var host = clearHost("ots-micro-trades");
    if (!host) return;
    var tc = (system && system.trade_counters) || {};
    if (tc.classification !== "PROVEN_CURRENT") {
      var unk = document.createElement("span");
      unk.className = "ots-trace-unknown";
      host.appendChild(unk);
      setText("ots-trade-detail", "UNKNOWN · no run/events");
      return;
    }
    var setN = tc.trades_set || 0;
    var rejN = tc.trades_rejected || 0;
    var maxDots = 14;
    var total = setN + rejN;
    var scale = total > maxDots ? maxDots / total : 1;
    var setDots = Math.round(setN * scale);
    var rejDots = Math.round(rejN * scale);
    for (var i = 0; i < setDots; i++) {
      var d = document.createElement("span");
      d.className = "ots-trace-dot set";
      host.appendChild(d);
    }
    for (var j = 0; j < rejDots; j++) {
      var r = document.createElement("span");
      r.className = "ots-trace-dot rejected";
      host.appendChild(r);
    }
    if (setDots === 0 && rejDots === 0) {
      var zero = document.createElement("span");
      zero.className = "ots-trace-zero";
      host.appendChild(zero);
    }
    setText(
      "ots-trade-detail",
      "set " + setN + " · rejected " + rejN + (tc.run_id ? " · run " + tc.run_id : "")
    );
  }

  function renderRdSpark(system) {
    var host = clearHost("ots-micro-rd");
    if (!host) return;
    var opt = (system && system.optimization) || {};
    if (opt.classification !== "PROVEN_CURRENT") {
      host.innerHTML = '<span class="ots-spark-unknown"></span>';
      setText("ots-rd-detail", opt.note || "UNKNOWN");
      return;
    }
    var count = opt.experiment_count != null ? Number(opt.experiment_count) : null;
    var withTrades = opt.experiments_with_trades != null ? Number(opt.experiments_with_trades) : null;
    var byStatus = opt.by_status || {};
    var statusKeys = Object.keys(byStatus);
    if (statusKeys.length) {
      statusKeys.forEach(function (sk) {
        var bar = document.createElement("span");
        bar.className = "ots-spark-bar";
        bar.style.setProperty("--ots-spark-h", String(Math.min(100, (byStatus[sk] || 0) * 12)));
        bar.title = sk + ": " + byStatus[sk];
        host.appendChild(bar);
      });
    } else if (count === 0) {
      host.innerHTML = '<span class="ots-spark-zero"></span>';
    }
    var detail = count != null ? count + " experiments" : "—";
    if (withTrades != null) detail += " · " + withTrades + " with trades";
    if (opt.unique_strategies != null) detail += " · " + opt.unique_strategies + " strategies";
    setText("ots-rd-detail", detail);
  }

  function renderFreshnessPulse(market) {
    var host = clearHost("ots-micro-freshness");
    if (!host) return;
    var freshness = ((market && market.market_freshness) || "UNKNOWN").toUpperCase();
    var pulse = document.createElement("span");
    pulse.className = "ots-pulse-core ots-pulse-" + freshness.toLowerCase();
    host.appendChild(pulse);
    setText(
      "ots-freshness-detail",
      freshness + " · " + ((market && market.connection_status) || "UNKNOWN")
    );
  }

  function renderSourceMatrix(system, market) {
    var host = clearHost("ots-micro-sources");
    if (!host) return;
    var slots = [
      { key: "market", proven: market && market.classification === "PROVEN_CURRENT", label: "market" },
      { key: "selection", proven: system && system.selected_future && system.selected_future.classification === "PROVEN_CURRENT", label: "selection" },
      { key: "trades", proven: system && system.trade_counters && system.trade_counters.classification === "PROVEN_CURRENT", label: "trades" },
      { key: "rd", proven: system && system.optimization && system.optimization.classification === "PROVEN_CURRENT", label: "r&d" },
    ];
    if (system && system.unknown_sources) {
      Object.keys(system.unknown_sources).forEach(function (k) {
        slots.push({ key: k, proven: false, label: k });
      });
    }
    slots.forEach(function (s) {
      var cell = document.createElement("span");
      cell.className = s.proven ? "on" : "";
      cell.title = s.label + ": " + (s.proven ? "PROVEN" : "UNAVAILABLE/UNKNOWN");
      host.appendChild(cell);
    });
  }

  function renderMiEvidence(system) {
    var host = clearHost("ots-micro-mi");
    if (!host) return;
    var mi = (system && system.mi_evidence) || {};
    if (mi.classification === "PROVEN_CURRENT") {
      var n = mi.experiment_count != null ? Number(mi.experiment_count) : 0;
      for (var i = 0; i < Math.min(n, 8); i++) {
        var dot = document.createElement("span");
        dot.className = "ots-mi-dot";
        host.appendChild(dot);
      }
      if (n === 0) host.innerHTML = '<span class="ots-spark-zero"></span>';
      setText("ots-mi-detail", "MI proxy · " + (mi.note || "R&D aggregate") + " · n=" + n);
      return;
    }
    host.innerHTML = '<span class="ots-spark-unknown"></span>';
    setText("ots-mi-detail", mi.note || "UNKNOWN");
  }

  function renderFeatureSlots(system) {
    var host = clearHost("ots-micro-feature-slots");
    if (!host) return;
    var slotState = system && system.unknown_sources && system.unknown_sources.feature_slots;
    var label = (slotState && slotState.label) || "SOURCE UNAVAILABLE";
    ["01", "02", "03", "04", "05"].forEach(function (slot) {
      var cell = document.createElement("span");
      cell.className = "ots-slot-cell unavailable";
      cell.title = "slot " + slot + " · " + label;
      host.appendChild(cell);
    });
    setText("ots-feature-slots-detail", "5 slots · " + label);
  }

  function renderArchiveLane(archiveConfigured, system) {
    var host = clearHost("ots-micro-archive");
    if (!host) return;
    var seg = document.createElement("span");
    seg.className = "ots-lane-seg " + (archiveConfigured ? "ots-lane-seg-fresh" : "ots-lane-seg-unknown");
    host.appendChild(seg);
    setText(
      "ots-archive-detail",
      (archiveConfigured ? "archive root configured" : "archive UNKNOWN") +
        " · observed " +
        ((system && system.system_observed_at) || "—")
    );
  }

  function applyUpperInstruments(state) {
    renderSelectionLane(state.system);
    renderMarketHealthLane(state.market);
    renderSafetyLane(state.safety);
    renderConfirmationLane(state.system);
    renderGapMatrix(state.system);
  }

  function applyLowerInstruments(state) {
    renderTradeTrace(state.system);
    renderRdSpark(state.system);
    renderFreshnessPulse(state.market);
    renderSourceMatrix(state.system, state.market);
    renderMiEvidence(state.system);
    renderFeatureSlots(state.system);
    renderArchiveLane(state.archive_root_configured, state.system);
  }

  window.PeakTradeSurfaceInstrumentsV1 = {
    applyUpper: applyUpperInstruments,
    applyLower: applyLowerInstruments,
  };
})();
