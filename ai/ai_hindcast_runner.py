from __future__ import annotations

import json
import sys
import os
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import ai.ai_forestation_model
from ai.ai_intervention_base import registry
from ai.ai_monte_carlo import run_monte_carlo
from getweather import fetch_history

EVENTS = [
    {
        "id":          1,
        "label":       "Vișeu de Sus — Maramureș",
        "lat":         47.73,
        "lon":         24.57,
        "clearcut_year": 2016,
        "parsed": {
            "in_scope":            True,
            "action":              "clear",
            "hectares":            300,
            "species":             "spruce",
            "sub_region":          "carpathians",
            "time_horizon_years":  5,
        },
        "baseline_start": "2013-01-01",
        "baseline_end":   "2015-12-31",
        "observed_start": "2016-01-01",
        "observed_end":   "2020-12-31",
    },
    {
        "id":          2,
        "label":       "Poienile de Sub Munte — Maramureș",
        "lat":         47.82,
        "lon":         24.78,
        "clearcut_year": 2017,
        "parsed": {
            "in_scope":            True,
            "action":              "clear",
            "hectares":            250,
            "species":             "spruce",
            "sub_region":          "carpathians",
            "time_horizon_years":  5,
        },
        "baseline_start": "2014-01-01",
        "baseline_end":   "2016-12-31",
        "observed_start": "2017-01-01",
        "observed_end":   "2021-12-31",
    },
    {
        "id":          3,
        "label":       "Apuseni — Beliș, Cluj",
        "lat":         46.63,
        "lon":         22.80,
        "clearcut_year": 2015,
        "parsed": {
            "in_scope":            True,
            "action":              "clear",
            "hectares":            200,
            "species":             "mixed",
            "sub_region":          "carpathians",
            "time_horizon_years":  5,
        },
        "baseline_start": "2012-01-01",
        "baseline_end":   "2014-12-31",
        "observed_start": "2015-01-01",
        "observed_end":   "2019-12-31",
    },
    {
        "id":          4,
        "label":       "Gurghiu — Mureș",
        "lat":         46.75,
        "lon":         24.95,
        "clearcut_year": 2018,
        "parsed": {
            "in_scope":            True,
            "action":              "clear",
            "hectares":            180,
            "species":             "spruce",
            "sub_region":          "carpathians",
            "time_horizon_years":  5,
        },
        "baseline_start": "2015-01-01",
        "baseline_end":   "2017-12-31",
        "observed_start": "2018-01-01",
        "observed_end":   "2022-12-31",
    },
    {
        "id":          5,
        "label":       "Bicaz — Neamț",
        "lat":         46.85,
        "lon":         25.90,
        "clearcut_year": 2014,
        "parsed": {
            "in_scope":            True,
            "action":              "clear",
            "hectares":            150,
            "species":             "mixed",
            "sub_region":          "subcarpathians",
            "time_horizon_years":  5,
        },
        "baseline_start": "2011-01-01",
        "baseline_end":   "2013-12-31",
        "observed_start": "2014-01-01",
        "observed_end":   "2018-12-31",
    },
]

def annual_mean(rows: list[dict]) -> tuple[float, float]:
    temps = [r["temp"] for r in rows if r.get("temp") is not None]
    hums  = [r["humidity"] for r in rows if r.get("humidity") is not None]
    t = sum(temps) / len(temps) if temps else None
    h = sum(hums)  / len(hums)  if hums  else None
    return t, h

def annual_means_by_year(rows: list[dict], start_year: int, n_years: int) -> list[tuple]:
    from collections import defaultdict
    by_year: dict[int, list] = defaultdict(list)
    for r in rows:
        yr = int(r["date"][:4])
        by_year[yr].append(r)

    result = []
    for yr in range(start_year, start_year + n_years):
        yr_rows = by_year.get(yr, [])
        t, h = annual_mean(yr_rows)
        result.append((yr, t, h))
    return result

def run_hindcast():
    module = registry.find_for({"in_scope": True, "action": "clear"})
    if module is None:
        print("ERROR: No module found in registry. ")
        return

    all_results = []
    all_temp_diffs = []
    all_hum_diffs  = []

    for ev in EVENTS:
        print(f"Event {ev['id']}: {ev['label']}")
        try:
            baseline_rows = fetch_history(
                ev["lat"], ev["lon"],
                ev["baseline_start"], ev["baseline_end"]
            )
            baseline_temp, baseline_hum = annual_mean(baseline_rows)
        except Exception as e:
            print(f"  ERROR fetching baseline: {e}")
            continue

        try:
            observed_rows = fetch_history(
                ev["lat"], ev["lon"],
                ev["observed_start"], ev["observed_end"]
            )
            observed_by_year = annual_means_by_year(
                observed_rows,
                ev["clearcut_year"],
                ev["parsed"]["time_horizon_years"]
            )
        except Exception as e:
            print(f"  ERROR fetching observed: {e}")
            continue

        baseline_dict = {
            "mean_temp_c":       baseline_temp,
            "mean_humidity_pct": baseline_hum,
        }
        result = module.predict(ev["parsed"], baseline_dict)

        mc = run_monte_carlo(ev["parsed"], baseline_dict, n_draws=1000)

        horizon = ev["parsed"]["time_horizon_years"]
        print(f" {'Yr':>3} | {'Model ΔT':>9} | {'Obs ΔT':>8} | {'Diff':>7} | "
              f"{'p05':>7} | {'p50':>7} | {'p95':>7} | "
              f"{'Model Δhum':>10} | {'Obs Δhum':>9} | {'Diff hum':>9}")
        print(f"  {'-'*3}-+-{'-'*9}-+-{'-'*8}-+-{'-'*7}-+-"
              f"{'-'*7}-+-{'-'*7}-+-{'-'*7}-+-{'-'*10}-+-{'-'*9}-+-{'-'*9}")

        event_temp_diffs = []
        event_hum_diffs  = []
        year_results = []

        for yr_idx in range(horizon):
            model_delta  = result.deltas[yr_idx].temp_delta_c
            model_hum    = result.deltas[yr_idx].humidity_delta_pct
            p05          = mc["temp_p05"][yr_idx]
            p50          = mc["temp_p50"][yr_idx]
            p95          = mc["temp_p95"][yr_idx]

            obs_year, obs_temp, obs_hum = observed_by_year[yr_idx]

            if obs_temp is not None:
                obs_delta_t = obs_temp - baseline_temp
                diff_t      = model_delta - obs_delta_t
                event_temp_diffs.append(diff_t)
                all_temp_diffs.append(diff_t)
            else:
                obs_delta_t = None
                diff_t      = None

            if obs_hum is not None and baseline_hum is not None:
                obs_delta_h = obs_hum - baseline_hum
                diff_h      = model_hum - obs_delta_h
                event_hum_diffs.append(diff_h)
                all_hum_diffs.append(diff_h)
            else:
                obs_delta_h = None
                diff_h      = None

            def fmt(v, w=8, d=4):
                return f"{v:+{w}.{d}f}" if v is not None else f"{'N/A':>{w}}"

            print(f"  {yr_idx+1:>3} | {fmt(model_delta,9,4)} | {fmt(obs_delta_t,8,4)} | "
                  f"{fmt(diff_t,7,4)} | {fmt(p05,7,4)} | {fmt(p50,7,4)} | {fmt(p95,7,4)} | "
                  f"{fmt(model_hum,10,4)} | {fmt(obs_delta_h,9,4)} | {fmt(diff_h,9,4)}")

            year_results.append({
                "year_offset":    yr_idx + 1,
                "calendar_year":  obs_year,
                "model_delta_t":  round(model_delta, 4),
                "obs_delta_t":    round(obs_delta_t, 4) if obs_delta_t is not None else None,
                "diff_t":         round(diff_t, 4)      if diff_t      is not None else None,
                "p05_t":          round(p05, 4),
                "p50_t":          round(p50, 4),
                "p95_t":          round(p95, 4),
                "model_delta_hum":round(model_hum, 4),
                "obs_delta_hum":  round(obs_delta_h, 4) if obs_delta_h is not None else None,
                "diff_hum":       round(diff_h, 4)      if diff_h      is not None else None,
            })

        if event_temp_diffs:
            mae_t  = statistics.mean(abs(d) for d in event_temp_diffs)
            bias_t = statistics.mean(event_temp_diffs)
        else:
            mae_t = bias_t = None

        if event_hum_diffs:
            mae_h  = statistics.mean(abs(d) for d in event_hum_diffs)
            bias_h = statistics.mean(event_hum_diffs)
        else:
            mae_h = bias_h = None

        def fmt2(v):
            return f"{v:+.4f}" if v is not None else "N/A"

        print(f" MAE temp={fmt2(mae_t)}°C  Bias temp={fmt2(bias_t)}°C  "
              f"MAE hum={fmt2(mae_h)}pp  Bias hum={fmt2(bias_h)}pp")

        final = year_results[-1]
        if (final["obs_delta_t"] is not None and
                final["p05_t"] is not None and final["p95_t"] is not None):
            in_band = final["p05_t"] <= final["obs_delta_t"] <= final["p95_t"]
            print(f" Final-year observed ΔT {'WITHIN' if in_band else 'OUTSIDE'} "
                  f"MC uncertainty band [{final['p05_t']:+.4f}, {final['p95_t']:+.4f}]")

        all_results.append({
            "id":            ev["id"],
            "label":         ev["label"],
            "baseline_temp": round(baseline_temp, 3),
            "baseline_hum":  round(baseline_hum, 1),
            "years":         year_results,
            "mae_temp":      round(mae_t, 4)  if mae_t  is not None else None,
            "bias_temp":     round(bias_t, 4) if bias_t is not None else None,
            "mae_hum":       round(mae_h, 4)  if mae_h  is not None else None,
            "bias_hum":      round(bias_h, 4) if bias_h is not None else None,
        })

    print(f"\n")
    print("OVERALL SUMMARY")
    if all_temp_diffs:
        overall_mae_t  = statistics.mean(abs(d) for d in all_temp_diffs)
        overall_bias_t = statistics.mean(all_temp_diffs)
        print(f"  Temperature — MAE: {overall_mae_t:+.4f}°C  Bias: {overall_bias_t:+.4f}°C")
        if overall_bias_t > 0:
            print(f"  → Model OVER-predicts warming ")
        else:
            print(f"  → Model UNDER-predicts warming ")
    if all_hum_diffs:
        overall_mae_h  = statistics.mean(abs(d) for d in all_hum_diffs)
        overall_bias_h = statistics.mean(all_hum_diffs)
        print(f"  Humidity   — MAE: {overall_mae_h:+.4f}pp  Bias: {overall_bias_h:+.4f}pp")

    out_path = os.path.join(os.path.dirname(__file__), "hindcast_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "events":       all_results,
            "overall": {
                "mae_temp":  round(overall_mae_t, 4)  if all_temp_diffs else None,
                "bias_temp": round(overall_bias_t, 4) if all_temp_diffs else None,
                "mae_hum":   round(overall_mae_h, 4)  if all_hum_diffs  else None,
                "bias_hum":  round(overall_bias_h, 4) if all_hum_diffs  else None,
            }
        }, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved to {out_path}")

if __name__ == "__main__":
    run_hindcast()
