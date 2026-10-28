import ai.ai_forestation_model
from ai.ai_intervention_base import registry

BASELINE = {"mean_temp_c": 9.5, "mean_humidity_pct": 75.0}

SCENARIOS = [
    {"label": "Plant 10 ha oak (Carpathians), 5y",
     "parsed": {"in_scope": True, "action": "plant", "hectares": 10.0,
                "species": "oak", "sub_region": "carpathians",
                "time_horizon_years": 5, "user_lang": "en"}},

    {"label": "Plant 2000 ha mixed (Transylvania), 25y",
     "parsed": {"in_scope": True, "action": "plant", "hectares": 2000.0,
                "species": "mixed", "sub_region": "transylvanian_plateau",
                "time_horizon_years": 25, "user_lang": "en"}},

    {"label": "Clear 2000 ha spruce (Carpathians), 25y",
     "parsed": {"in_scope": True, "action": "clear", "hectares": 2000.0,
                "species": "spruce", "sub_region": "carpathians",
                "time_horizon_years": 25, "user_lang": "en"}},

    {"label": "Plant 5000 ha (Dobrogea, dry SE), 10y",
     "parsed": {"in_scope": True, "action": "plant", "hectares": 5000.0,
                "species": "oak", "sub_region": "dobrogea",
                "time_horizon_years": 10, "user_lang": "ro"}},
]

def main():
    for s in SCENARIOS:
        parsed = s["parsed"]
        module = registry.find_for(parsed)
        print("\n")
        print(s["label"])
        if module is None:
            print("  NO MODULE ACCEPTED THIS SCENARIO")
            continue
        result = module.predict(parsed, BASELINE)
        es = result.effect_summary
        print(f"  module={module.module_id}  area_fraction={es['area_fraction']}")
        print(f"  peak ΔT={es['peak_temp_delta_c']:+.3f}°C  "
              f"Δhum={es['peak_humidity_delta_pct']:+.2f}pp  "
              f"negligible={es['negligible']}")
        print("  year |   ΔT(°C)  | Δhumidity(pp) | abs.temp | abs.hum")
        for d in result.deltas:
            t_abs = BASELINE["mean_temp_c"] + d.temp_delta_c
            h_abs = BASELINE["mean_humidity_pct"] + d.humidity_delta_pct
            print(f"   {d.year_offset:>3} | {d.temp_delta_c:+8.4f} | "
                  f"{d.humidity_delta_pct:+11.4f}  | {t_abs:7.3f}  | {h_abs:6.2f}")
        print("  sources:", result.sources[0])

if __name__ == "__main__":
    main()
