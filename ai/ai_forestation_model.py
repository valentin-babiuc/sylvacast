from __future__ import annotations

import math

from ai.ai_coefficients import COEFFICIENTS as _C
from ai.ai_intervention_base import (
    InterventionModule,
    PredictionResult,
    YearlyDelta,
    registry,
)

_ET_TEMP       = _C["et_temp_cooling"]["value"]
_ET_HUMID      = _C["et_humidity_increase"]["value"]
_ALBEDO_TEMP   = _C["albedo_temp_warming"]["value"]
_ROUGH_TEMP    = _C["roughness_temp_moderation"]["value"]
_HALF_SAT_HA   = _C["half_sat_ha"]["value"]
_GROWTH_TAU    = _C["growth_tau_years"]["value"]

_SPECIES_MULT = {
    k: v["value"]
    for k, v in _C["species_et_mult"].items()
    if not k.startswith("_")
}

_SUBREGION_MAP = {
    "carpathians":        "carpathians",
    "subcarpathians":     "subcarpathians",
    "transylvania":       "transylvania",
    "transylvanian_plateau": "transylvania",
    "moldavian_plain":    "moldavian_plain",
    "dobrogea":           "dobrogea",
}
_SUBREGION_MULT = {
    k: v["value"]
    for k, v in _C["subregion_mult"].items()
    if not k.startswith("_")
}

COEFF_RANGES = {
    "et_temp_cooling":           (_C["et_temp_cooling"]["low"],           _C["et_temp_cooling"]["high"]),
    "et_humidity_increase":      (_C["et_humidity_increase"]["low"],      _C["et_humidity_increase"]["high"]),
    "albedo_temp_warming":       (_C["albedo_temp_warming"]["low"],       _C["albedo_temp_warming"]["high"]),
    "roughness_temp_moderation": (_C["roughness_temp_moderation"]["low"], _C["roughness_temp_moderation"]["high"]),
    "half_sat_ha":               (_C["half_sat_ha"]["low"],               _C["half_sat_ha"]["high"]),
    "growth_tau_years":          (_C["growth_tau_years"]["low"],          _C["growth_tau_years"]["high"]),
}

def _michaelis_menten(area_ha: float, half_sat: float) -> float:
    if area_ha <= 0:
        return 0.0
    return area_ha / (area_ha + half_sat)

def _growth_ramp(year: int, tau: float) -> float:
    if year <= 0:
        return 0.0
    return 1.0 - math.exp(-year / tau)

class RomaniaForestationModule(InterventionModule):
    module_id = "romania_forestation"

    _SOURCES = [
        "ET cooling: Li et al. (2025) Nat. Commun. 16, 8412 | "
        "Li et al. (2025) Nat. Commun. 16, 2335",

        "Albedo: Bright et al. (2025) GRL 52, e2024GL112739 | "
        "Li et al. (2025) Nat. Commun. 16, 8412",

        "Roughness: Wei et al. (2025) GCB 31, e70634 | "
        "Bright et al. (2025) GRL 52, e2024GL112739",

        "HALF_SAT_HA: Wei et al. (2025) GCB 31, e70634 | "
        "Meeussen et al. (2021) Agric. For. Meteorol. 311, 108699",

        "GROWTH_TAU: Fuentes-Montemayor et al. (2022) Forestry 95, 28 | "
        "Palmero-Barrachina et al. (2025) Front. For. Glob. Change 8, 1586743",

        "Species ET: Novosadová et al. (2023) Water 15, 285 | "
        "Luong et al. (2025) SSRN 5900264",

        "Sub-regions: Chivulescu et al. (2025) Forests 16, 941 | "
        "Mihai et al. (2022) Forests 13, 1203",
    ]

    _NOTES = [
        "ET humidity effect near-negligible at 2 m measurement height "
        "(Callejas-Rodelas et al. 2025); literature gap confirmed by Wright et al. 2026.",

        "Albedo warming is winter-dominant and weakening as Romanian snow cover declines.",

        "Roughness channel is a conservative residual estimate — no study isolates "
        "this effect independently. Documented gap, not a sourcing failure.",

        "HALF_SAT_HA revised from 500 ha → 2 ha: edge effects stabilise within "
        "12.5–100 m of forest edge in European deciduous forests.",

        "GROWTH_TAU revised from 8 → 20 years: canopy closure takes 10–30 years "
        "for broadleaf species in temperate Europe.",

        "Model reports local patch-interior effect only (not regional or city-level). "
        "Annual-mean values; seasonal split not yet implemented (Phase 2 future work).",
    ]

    def accepts(self, parsed: dict) -> bool:
        return bool(parsed.get("in_scope")) and parsed.get("action") in ("plant", "clear")

    def predict(self, parsed: dict, baseline: dict) -> PredictionResult:
        action    = parsed.get("action", "plant")
        area_ha   = float(parsed.get("hectares", 100))
        species   = str(parsed.get("species", "mixed")).lower()
        sub_raw   = str(parsed.get("sub_region", "transylvania")).lower()
        horizon   = int(parsed.get("time_horizon_years", 50))

        sub_key  = _SUBREGION_MAP.get(sub_raw, "transylvania")

        sp_mult  = _SPECIES_MULT.get(species, _SPECIES_MULT["mixed"])
        reg_mult = _SUBREGION_MULT.get(sub_key, _SUBREGION_MULT["transylvania"])

        area_frac = _michaelis_menten(area_ha, _HALF_SAT_HA)

        sign = 1.0 if action == "plant" else -1.0

        albedo_sp = 1.15 if species in ("spruce", "pine") else 1.0

        deltas: list[YearlyDelta] = []
        for yr in range(1, horizon + 1):
            ramp = _growth_ramp(yr, _GROWTH_TAU)

            et_temp    = _ET_TEMP    * sp_mult * reg_mult * area_frac * ramp * sign
            albedo_tmp = _ALBEDO_TEMP * albedo_sp            * area_frac * ramp * sign
            rough_tmp  = _ROUGH_TEMP                         * area_frac * ramp * sign
            et_humid   = _ET_HUMID   * sp_mult * reg_mult * area_frac * ramp * sign

            deltas.append(YearlyDelta(
                year_offset=yr,
                temp_delta_c=round(et_temp + albedo_tmp + rough_tmp, 4),
                humidity_delta_pct=round(et_humid, 4),
            ))

        peak_temp  = deltas[-1].temp_delta_c if deltas else 0.0
        peak_humid = deltas[-1].humidity_delta_pct if deltas else 0.0
        negligible = abs(peak_temp) < 0.01 and abs(peak_humid) < 0.05

        effect_summary = {
            "area_fraction":         round(area_frac, 4),
            "species_et_mult":       sp_mult,
            "subregion_mult":        reg_mult,
            "peak_temp_delta_c":     peak_temp,
            "peak_humidity_delta_pct": peak_humid,
            "negligible":            negligible,
            "half_sat_ha":           _HALF_SAT_HA,
            "growth_tau_years":      _GROWTH_TAU,
            "channel_at_maturity": {
                "et_temp_c":    round(_ET_TEMP    * sp_mult * reg_mult * area_frac, 4),
                "albedo_temp_c":round(_ALBEDO_TEMP * albedo_sp           * area_frac, 4),
                "rough_temp_c": round(_ROUGH_TEMP                        * area_frac, 4),
                "et_humid_pp":  round(_ET_HUMID   * sp_mult * reg_mult * area_frac, 4),
            },
        }

        return PredictionResult(
            deltas=deltas,
            sources=self._SOURCES,
            notes=self._NOTES,
            effect_summary=effect_summary,
        )

    def cite(self) -> list:
        return self._SOURCES

registry.register(RomaniaForestationModule())
