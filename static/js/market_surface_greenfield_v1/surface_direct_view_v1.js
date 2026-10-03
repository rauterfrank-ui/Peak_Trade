(function (global) {
  "use strict";

  var STORAGE_KEY = "peak_trade_surface_direct_view_v1";
  var VALID = ["MARKET", "01", "02", "03", "04", "05"];

  function normalize(view) {
    var v = String(view || "MARKET").toUpperCase();
    return VALID.indexOf(v) >= 0 ? v : "MARKET";
  }

  function load() {
    try {
      return normalize(localStorage.getItem(STORAGE_KEY));
    } catch (_e) {
      return "MARKET";
    }
  }

  function save(view) {
    var v = normalize(view);
    try {
      localStorage.setItem(STORAGE_KEY, v);
    } catch (_e) {
      /* UI-local only; ignore quota/private mode */
    }
    return v;
  }

  global.PeakTradeDirectViewV1 = {
    VALID: VALID,
    defaultView: "MARKET",
    load: load,
    save: save,
    normalize: normalize,
  };
})(typeof window !== "undefined" ? window : globalThis);
