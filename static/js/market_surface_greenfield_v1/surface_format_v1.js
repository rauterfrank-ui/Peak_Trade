/** @typedef {typeof globalThis} G */
(function (global) {
  "use strict";

  /**
   * Format price for display and chart axes; preserves sub-cent precision.
   * @param {number|null|undefined} value
   * @returns {string}
   */
  function formatPrice(value) {
    if (value == null || Number.isNaN(Number(value))) return "—";
    var n = Number(value);
    if (n === 0) return "0";
    var abs = Math.abs(n);
    if (abs >= 1) return n.toLocaleString(undefined, { maximumFractionDigits: 8 });
    if (abs >= 0.0001) return n.toFixed(8).replace(/\.?0+$/, "");
    return n.toExponential(4);
  }

  /** Min move for Lightweight Charts from magnitude of last price. */
  function minMoveForPrice(value) {
    var n = Math.abs(Number(value));
    if (!n || Number.isNaN(n)) return 1e-8;
    if (n >= 1) return 0.01;
    var exp = Math.floor(Math.log10(n));
    return Math.pow(10, exp - 2);
  }

  global.PeakTradeSurfaceFormatV1 = {
    formatPrice: formatPrice,
    minMoveForPrice: minMoveForPrice,
  };
})(typeof window !== "undefined" ? window : globalThis);
