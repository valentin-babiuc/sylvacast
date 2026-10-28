COEFFICIENTS = {

    "et_temp_cooling": {
        "value": -0.20,
        "low":   -0.35,
        "high":  -0.05,
        "unit":  "°C",
        "notes": "Summer mean air-temperature effect, temperate Europe. "
    },

    "et_humidity_increase": {
        "value": 0.5,
        "low":  -0.9,
        "high":  1.7,
        "unit":  "pp",
        "notes": "RH difference agroforestry and open cropland. "
    },

    "albedo_temp_warming": {
        "value": 0.05,
        "low":   0.02,
        "high":  0.08,
        "unit":  "°C",
                "notes": "converted to air temperature and annually averaged. "
    },

    "roughness_temp_moderation": {
        "value": -0.08,
        "low":   -0.15,
        "high":  -0.02,
        "unit":  "°C",
        "notes": "Conservative residual estimate "
    },

    "half_sat_ha": {
        "value": 2.0,
        "low":   0.8,
        "high":  5.0,
        "unit":  "ha",
        "notes": "Edge effects stabilize at 12.5–35 m from forest edge "
    },

    "growth_tau_years": {
        "value": 20.0,
        "low":   10.0,
        "high":  30.0,
        "unit":  "years",
        "notes": "0–30 years for unmanaged woodland "
    },

    "species_et_mult": {
        "oak":   {"value": 1.10, "low": 1.05, "high": 1.15},
        "beech": {"value": 1.05, "low": 1.00, "high": 1.10},
        "spruce":{"value": 0.90, "low": 0.85, "high": 0.95},
        "pine":  {"value": 0.85, "low": 0.80, "high": 0.90},
        "mixed": {"value": 1.00, "low": 1.00, "high": 1.00},
        "_notes": (
            "Mixed oak-beech-linden transpires 451 mm/yr vs 318 mm/yr beech monoculture "
        ),
    },

    "subregion_mult": {
        "carpathians":      {"value": 0.90, "low": 0.85, "high": 0.95},
        "subcarpathians":   {"value": 0.95, "low": 0.90, "high": 1.00},
        "transylvania":     {"value": 1.00, "low": 1.00, "high": 1.00},
        "moldavian_plain":  {"value": 1.10, "low": 1.05, "high": 1.15},
        "dobrogea":         {"value": 1.20, "low": 1.10, "high": 1.30},
        "_notes": (
            "Carpathians: highest precipitation, Dobrogea: driest region "
        ),
    },
}
