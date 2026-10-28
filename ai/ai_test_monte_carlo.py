import ai.ai_forestation_model
from ai.ai_monte_carlo import run_monte_carlo

BASELINE = {"mean_temp_c": 9.5, "mean_humidity_pct": 75.0}

SCENARIOS = [
    {
        "label": "10 ha oak Carpathians 5y — small patch, expect narrow band",
        "parsed": {
            "in_scope": True, "action": "plant", "hectares": 10.0,
            "species": "oak", "sub_region": "carpathians",
            "time_horizon_years": 5,
        },
    },
    {
        "label": "2000 ha mixed Transylvania 25y — large patch, wider band",
        "parsed": {
            "in_scope": True, "action": "plant", "hectares": 2000.0,
            "species": "mixed", "sub_region": "transylvanian_plateau",
            "time_horizon_years": 25,
        },
    },
    {
        "label": "5000 ha oak Dobrogea 10y — dry region, expect largest effect",
        "parsed": {
            "in_scope": True, "action": "plant", "hectares": 5000.0,
            "species": "oak", "sub_region": "dobrogea",
            "time_horizon_years": 10,
        },
    },
]

def main():
    for s in SCENARIOS:
        print("\n")
        print(s["label"])
        mc = run_monte_carlo(s["parsed"], BASELINE, n_draws=1000)

        horizon = s["parsed"]["time_horizon_years"]
        print(f"  n_draws={mc['n_draws']}  method={mc['method'][:40]}...")
        print(f"  {'Year':>4} | {'p05 ΔT':>9} | {'p50 ΔT':>9} | {'p95 ΔT':>9} | "
              f"{'band width':>10} | {'straddles 0':>11}")

        for i in range(horizon):
            p05 = mc["temp_p05"][i]
            p50 = mc["temp_p50"][i]
            p95 = mc["temp_p95"][i]
            width = p95 - p05
            straddles = "YES " if p05 < 0 < p95 else "no"

            assert p05 <= p50 <= p95, f"Year {i+1}: ordering violated!"

            print(f"  {i+1:>4} | {p05:+9.4f} | {p50:+9.4f} | {p95:+9.4f} | "
                  f"{width:>10.4f} | {straddles:>11}")

        final_p05 = mc["temp_p05"][-1]
        final_p95 = mc["temp_p95"][-1]
        final_p50 = mc["temp_p50"][-1]
        print(f"\n  Final year: p50={final_p50:+.4f}°C  "
              f"[{final_p05:+.4f}, {final_p95:+.4f}]  "
              f"band={final_p95 - final_p05:.4f}°C")

        if final_p05 < 0 < final_p95:
            print("  Band straddles zero — negligibility note should fire in UI.")
        else:
            print("  Band does not straddle zero — effect direction is confident.")

    print("\nAll Monte Carlo tests passed.")

if __name__ == "__main__":
    main()
