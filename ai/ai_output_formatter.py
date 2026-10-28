ACTION_LABEL = {
    "ro": {"plant": "plantare", "clear": "defrișare"},
    "en": {"plant": "planting",  "clear": "clearing"},
}

SUB_REGION_LABEL = {
    "ro": {
        "carpathians":           "Carpați",
        "transylvanian_plateau": "Podișul Transilvaniei",
        "subcarpathians":        "Subcarpați",
        "dobrogea":              "Dobrogea",
        "moldavian_plain":       "Câmpia Moldovei",
        "unknown":               "regiune nespecificată",
    },
    "en": {
        "carpathians":           "Carpathians",
        "transylvanian_plateau": "Transylvanian Plateau",
        "subcarpathians":        "Subcarpathians",
        "dobrogea":              "Dobrogea",
        "moldavian_plain":       "Moldavian Plain",
        "unknown":               "unspecified region",
    },
}

SPECIES_LABEL = {
    "ro": {"oak": "stejar", "spruce": "molid", "beech": "fag", "pine": "pin", "mixed": "mixt"},
    "en": {"oak": "oak", "spruce": "spruce", "beech": "beech", "pine": "pine", "mixed": "mixed"},
}

UNIT_LABEL = {
    "ro": {"hectares": "ha", "trees": "copaci", "km2": "km²"},
    "en": {"hectares": "ha", "trees": "trees",  "km2": "km²"},
}

def _format_years_ro(n: int) -> str:
    if n == 1:
        return "1 an"
    if 2 <= n <= 19:
        return f"{n} ani"
    return f"{n} de ani"

def _format_years_en(n: int) -> str:
    return f"{n} year" if n == 1 else f"{n} years"

def _format_quantity(parsed: dict, lang: str) -> str:
    ha = parsed["hectares"]
    raw_qty = parsed.get("raw_quantity")
    raw_unit = parsed.get("raw_unit")
    unit_lbl = UNIT_LABEL[lang]

    if raw_unit and raw_unit != "hectares" and raw_qty is not None:
        return f"{raw_qty:g} {unit_lbl[raw_unit]} ({ha:g} ha)"
    return f"{ha:g} ha"

def format_scenario_summary(parsed: dict) -> str:
    lang = parsed.get("user_lang", "en")

    if not parsed.get("in_scope"):
        return parsed.get("refusal_reason") or (
            "Scenariu în afara domeniului suportat." if lang == "ro"
            else "Scenario is outside the supported scope."
        )

    action  = parsed["action"]
    loc     = parsed["location"] or ("România" if lang == "ro" else "Romania")
    region  = SUB_REGION_LABEL[lang][parsed["sub_region"]]
    years   = parsed["time_horizon_years"]
    species = parsed.get("species")
    qty_str = _format_quantity(parsed, lang)

    species_lbl = SPECIES_LABEL[lang].get(species, species) if species else None

    if lang == "ro":
        action_txt = ACTION_LABEL["ro"][action]

        head = f"{action_txt} {species_lbl}" if species_lbl else action_txt
        years_txt = _format_years_ro(years)

        loc_part = loc if loc.lower() != region.lower() else region
        return (
            f"Scenariu înțeles: {head} — {qty_str} "
            f"în zona {loc_part} ({region}), proiecție pe {years_txt}."
        )
    else:
        action_txt = ACTION_LABEL["en"][action]
        head = f"{action_txt} {species_lbl}" if species_lbl else action_txt
        years_txt = _format_years_en(years)
        loc_part = loc if loc.lower() != region.lower() else region
        return (
            f"Scenario understood: {head} — {qty_str} "
            f"near {loc_part} ({region}), {years_txt} projection."
        )
