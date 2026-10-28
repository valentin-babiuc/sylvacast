from __future__ import annotations

import random
from contextlib import contextmanager
from typing import Any

import ai.ai_forestation_model as _model
from ai.ai_forestation_model import COEFF_RANGES

@contextmanager
def _override_coefficients(sampled: dict[str, Any]):
    originals = {k: getattr(_model, k) for k in sampled}
    try:
        for k, v in sampled.items():
            setattr(_model, k, v)
        yield
    finally:
        for k, v in originals.items():
            setattr(_model, k, v)

def _sample_coefficients() -> dict[str, Any]:
    def u(low, high):
        return random.uniform(low, high)

    et_temp  = u(*COEFF_RANGES["et_temp_cooling"])
    et_humid = u(*COEFF_RANGES["et_humidity_increase"])
    alb_temp = u(*COEFF_RANGES["albedo_temp_warming"])
    rou_temp = u(*COEFF_RANGES["roughness_temp_moderation"])
    half_sat = u(*COEFF_RANGES["half_sat_ha"])
    tau      = u(*COEFF_RANGES["growth_tau_years"])

    return {
        "_ET_TEMP":     et_temp,
        "_ET_HUMID":    et_humid,
        "_ALBEDO_TEMP": alb_temp,
        "_ROUGH_TEMP":  rou_temp,
        "_HALF_SAT_HA": half_sat,
        "_GROWTH_TAU":  tau,
    }

def run_monte_carlo(
    parsed: dict,
    baseline: dict,
    n_draws: int = 1000,
    seed: int | None = 42,
) -> dict:
    if seed is not None:
        random.seed(seed)

    horizon = int(parsed.get("time_horizon_years", 50))

    temp_draws  = [[] for _ in range(horizon)]
    humid_draws = [[] for _ in range(horizon)]

    from ai.ai_intervention_base import registry
    module = registry.find_for(parsed)
    if module is None:
        zeros = [0.0] * horizon
        return {
            "temp_p05": zeros, "temp_p50": zeros, "temp_p95": zeros,
            "humid_p05": zeros, "humid_p50": zeros, "humid_p95": zeros,
            "n_draws": 0,
            "method": "failed — no module found",
        }

    for _ in range(n_draws):
        sampled = _sample_coefficients()
        with _override_coefficients(sampled):
            result = module.predict(parsed, baseline)
        for yr_idx, delta in enumerate(result.deltas):
            temp_draws[yr_idx].append(delta.temp_delta_c)
            humid_draws[yr_idx].append(delta.humidity_delta_pct)

    def percentile(data: list[float], p: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        idx = (len(sorted_data) - 1) * p / 100
        lo = int(idx)
        hi = min(lo + 1, len(sorted_data) - 1)
        frac = idx - lo
        return round(sorted_data[lo] * (1 - frac) + sorted_data[hi] * frac, 4)

    return {
        "temp_p05":  [percentile(temp_draws[i],  5) for i in range(horizon)],
        "temp_p50":  [percentile(temp_draws[i], 50) for i in range(horizon)],
        "temp_p95":  [percentile(temp_draws[i], 95) for i in range(horizon)],
        "humid_p05": [percentile(humid_draws[i],  5) for i in range(horizon)],
        "humid_p50": [percentile(humid_draws[i], 50) for i in range(horizon)],
        "humid_p95": [percentile(humid_draws[i], 95) for i in range(horizon)],
        "n_draws":   n_draws,
        "method":    "uniform sampling over coefficient ranges",
    }
