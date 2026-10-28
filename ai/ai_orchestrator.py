from __future__ import annotations
from datetime import date, timedelta

from ai.ai_scenario_parser import parse_scenario
from ai.ai_output_formatter import format_scenario_summary
from ai.ai_intervention_base import registry
import ai.ai_forestation_model
from ai.ai_monte_carlo import run_monte_carlo

SUBREGION_COORDS = {
    "carpathians":           (45.65, 25.60),
    "transylvanian_plateau": (46.77, 23.59),
    "subcarpathians":        (45.10, 24.37),
    "dobrogea":              (44.17, 28.65),
    "moldavian_plain":       (47.16, 27.59),
    "unknown":               (46.07, 23.57),
}

BASELINE_YEARS   = 3
ARCHIVE_LAG_DAYS = 10
FALLBACK_BASELINE = {"mean_temp_c": 10.0, "mean_humidity_pct": 75.0}

MC_DRAWS = 1000

def _get_baseline(lat: float, lon: float) -> dict:
    from getweather import fetch_history

    end   = date.today() - timedelta(days=ARCHIVE_LAG_DAYS)
    start = end - timedelta(days=365 * BASELINE_YEARS)
    rows  = fetch_history(lat, lon, start.isoformat(), end.isoformat())

    temps = [r["temp"]     for r in rows if r.get("temp")     is not None]
    hums  = [r["humidity"] for r in rows if r.get("humidity") is not None]
    if not temps:
        return dict(FALLBACK_BASELINE)
    return {
        "mean_temp_c":      sum(temps) / len(temps),
        "mean_humidity_pct": (sum(hums) / len(hums)) if hums
                              else FALLBACK_BASELINE["mean_humidity_pct"],
    }

def _year_labels(horizon: int, lang: str) -> list:
    word = "Anul" if lang == "ro" else "Year"
    return [f"{word} {i + 1}" for i in range(horizon)]

def handle_scenario(text: str, lat=None, lon=None) -> dict:
    parsed  = parse_scenario(text)
    lang    = parsed.get("user_lang", "en")
    summary = format_scenario_summary(parsed)

    if not parsed.get("in_scope"):
        return {
            "ok": False,
            "in_scope": False,
            "user_lang": lang,
            "summary": summary,
            "refusal": parsed.get("refusal_reason") or summary,
        }

    module = registry.find_for(parsed)
    if module is None:
        msg = ("Niciun modul disponibil nu poate procesa acest scenariu."
               if lang == "ro" else "No available module can handle this scenario.")
        return {
            "ok": False, "in_scope": True, "user_lang": lang,
            "summary": summary, "refusal": msg,
        }

    if lat is None or lon is None:
        lat, lon = SUBREGION_COORDS.get(
            parsed.get("sub_region", "unknown"), SUBREGION_COORDS["unknown"]
        )

    try:
        baseline = _get_baseline(float(lat), float(lon))
    except Exception:
        baseline = dict(FALLBACK_BASELINE)

    result = module.predict(parsed, baseline)

    try:
        mc = run_monte_carlo(parsed, baseline, n_draws=MC_DRAWS)
    except Exception as e:
        mc = {"error": str(e), "n_draws": 0}

    bt = baseline["mean_temp_c"]
    bh = baseline["mean_humidity_pct"]
    horizon = int(parsed["time_horizon_years"])

    series = {
        "labels":            _year_labels(horizon, lang),
        "baseline_temp":     [round(bt, 3)] * horizon,
        "scenario_temp":     [round(bt + d.temp_delta_c, 3) for d in result.deltas],
        "baseline_humidity": [round(bh, 3)] * horizon,
        "scenario_humidity": [round(bh + d.humidity_delta_pct, 3) for d in result.deltas],
    }

    if "temp_p50" in mc:
        series["temp_p05"] = [round(bt + v, 3) for v in mc["temp_p05"]]
        series["temp_p50"] = [round(bt + v, 3) for v in mc["temp_p50"]]
        series["temp_p95"] = [round(bt + v, 3) for v in mc["temp_p95"]]
        series["humid_p05"] = [round(bh + v, 3) for v in mc["humid_p05"]]
        series["humid_p50"] = [round(bh + v, 3) for v in mc["humid_p50"]]
        series["humid_p95"] = [round(bh + v, 3) for v in mc["humid_p95"]]

    deltas = [
        {
            "year":               d.year_offset + 1,
            "temp_delta_c":       d.temp_delta_c,
            "humidity_delta_pct": d.humidity_delta_pct,
        }
        for d in result.deltas
    ]

    negligible_note = None
    if "temp_p05" in mc and "temp_p95" in mc:
        final_p05 = mc["temp_p05"][-1]
        final_p95 = mc["temp_p95"][-1]
        if final_p05 < 0 < final_p95:
            negligible_note = (
                "Banda de incertitudine pentru temperatura finală cuprinde zero — "
                "efectul net la nivelul anului final nu poate fi distins cu certitudine "
                "de variabilitatea naturală a climei."
                if lang == "ro" else
                "The final-year temperature uncertainty band straddles zero — "
                "the net effect cannot be confidently distinguished from natural "
                "climate variability at that time horizon."
            )

    return {
        "ok":             True,
        "in_scope":       True,
        "user_lang":      lang,
        "summary":        summary,
        "baseline":       {"mean_temp_c": round(bt, 2), "mean_humidity_pct": round(bh, 2)},
        "horizon_years":  horizon,
        "series":         series,
        "deltas":         deltas,
        "effect_summary": result.effect_summary,
        "uncertainty": {
            "n_draws":         mc.get("n_draws", 0),
            "method":          mc.get("method", ""),
            "negligible_note": negligible_note,
        },
        "notes":   result.notes,
        "sources": result.sources,
    }
