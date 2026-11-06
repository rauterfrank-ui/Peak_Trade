"""Historical bounded-band reference only; no Double-Play runtime caller."""


def clamp_band_width(raw, rules, env):
    lo = max(rules.min_band_width, env.static.min_band_width)
    hi = min(rules.max_band_width, env.static.max_band_width)
    if hi < lo:
        return lo
    return max(lo, min(hi, raw))
