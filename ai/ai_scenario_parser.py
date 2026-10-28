import json
import os
import re

import ollama

MODEL_NAME = os.environ.get("OLLAMA_MODEL", "mistral:7b-instruct")

VALID_ACTIONS = {"plant", "clear"}
VALID_SUB_REGIONS = {
    "carpathians", "transylvanian_plateau", "subcarpathians",
    "dobrogea", "moldavian_plain", "unknown",
}
VALID_TIME_HORIZONS = [1, 5, 10, 25]
VALID_AREA_UNITS = {"hectares", "trees", "km2"}

DEFAULT_TREES_PER_HECTARE = 1000
DEFAULT_TIME_HORIZON = 5

_DIACRITIC_MAP = str.maketrans({
    "ă": "a", "â": "a", "î": "i", "ș": "s", "ş": "s", "ț": "t", "ţ": "t",
    "Ă": "A", "Â": "A", "Î": "I", "Ș": "S", "Ş": "S", "Ț": "T", "Ţ": "T",
})

def _strip_diacritics(text: str) -> str:
    return text.translate(_DIACRITIC_MAP)

RO_FUNCTION_WORDS = {
    "plantez", "plantam", "planteaza", "planta", "plantand", "plantarea",
    "impaduresc", "impadurim", "impaduresti", "impadurire",
    "reimpaduresc", "reimpadurim", "reimpaduresti", "reimpadurire",
    "defrisez", "defrisam", "defriseaza", "defrisa", "defrisare", "defrisat",
    "taie", "taiem", "taia", "taiat", "tai", "taiere",
    "doboram", "doboara", "doborat", "doborare",
    "padure", "paduri", "padurea", "padurile",
    "copaci", "copac", "copacii", "arbori", "arborii", "arbore",
    "hectare", "hectar",
    "stejar", "stejari", "stejarii", "molid", "molizi", "fag", "fagi", "pini",
    "daca", "cum", "cand", "unde",
    "langa", "lânga", "jur", "jurul", "zona",
    "anul", "luna", "luni", "ani",
    "viitor", "viitoare", "urmatori", "urmatoarele",
    "vreau", "pentru", "intampla", "intampli",
    "modifica", "modifice", "schimba", "schimbam",
    "asta", "asa", "atunci",
    "mixti", "diversi", "amestec",
    "electrice", "electrica",
    "convingi", "convinge", "convins",
    "oameni", "oamenii", "omul",
    "conduca", "conducem",
    "masini", "masina", "masinile",
    "ploua", "ploaie", "plouat",
    "este", "sunt",
}

def _detect_language(text: str) -> str:
    normalized = _strip_diacritics(text).lower()
    tokens = re.findall(r"\b[a-z]+\b", normalized)
    hits = sum(1 for t in tokens if t in RO_FUNCTION_WORDS)
    return "ro" if hits >= 2 else "en"

_PLANT_PATTERNS = [
    r"\bplant", r"\breforest", r"\breplant", r"\bafforest",
    r"impadur", r"reimpadur",
]
_CLEAR_PATTERNS = [
    r"\bclear", r"\bdeforest", r"clear-?cut",
    r"defris", r"\btaie", r"\btaiem\b", r"\btai\b", r"\btaiere\b",
    r"doboar", r"doborar", r"\blog\b", r"\blogging\b",
    r"\bcut\b", r"\bchop", r"\bfell\b",
]

_KM2_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:km\s*(?:2|²|\^2|patrati|patrate)|km²|kilometri\s+patrati)",
    re.IGNORECASE,
)
_HA_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:de\s+)?(?:ha\b|hectares?\b|hectare\b|hectar[ei]?\b)",
    re.IGNORECASE,
)
_TREES_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:de\s+)?"
    r"(?:(?:oak|spruce|beech|pine|mixed|young|mature)\s+)?"
    r"(?:copaci|copac|arbori|arbore|trees|tree|puieti|"
    r"stejari|stejar|molizi|molid|fagi|fag|pini)",
    re.IGNORECASE,
)

_YEAR_RE = re.compile(r"(\d+)\s*(?:de\s+)?(?:years?|ani\b|an\b|yr)", re.IGNORECASE)

def _regex_detect_action(text_norm: str):
    plant = any(re.search(p, text_norm) for p in _PLANT_PATTERNS)
    clear = any(re.search(p, text_norm) for p in _CLEAR_PATTERNS)
    if plant and not clear:
        return "plant"
    if clear and not plant:
        return "clear"
    return None

def _regex_detect_quantity_unit(text_norm: str):
    m = _KM2_RE.search(text_norm)
    if m:
        return float(m.group(1)), "km2"
    m = _HA_RE.search(text_norm)
    if m:
        return float(m.group(1)), "hectares"
    m = _TREES_RE.search(text_norm)
    if m:
        return float(m.group(1)), "trees"
    return None, None

def _regex_detect_years(text_norm: str):
    m = _YEAR_RE.search(text_norm)
    return int(m.group(1)) if m else None

SYSTEM_PROMPT = """You are a scenario parser for a Romanian forestation climate-impact tool.

The user may write in Romanian, English, or a mix. Romanian is often typed WITHOUT DIACRITICS — treat "padure" = "pădure", "Brasov" = "Brașov", "Iasi" = "Iași", "Maramures" = "Maramureș", "Carpati" = "Carpați" as identical.

Output a SINGLE JSON object with English keys and English enum values. No preamble, no markdown fences.

YOUR JOB: judge the SCOPE and map the LOCATION. (Numbers, units, and year counts are handled separately by other code — you may fill them in, but they are not your priority.)

SCOPE — set in_scope:
- in_scope = true ONLY IF: the scenario is about planting OR clearing forest, AND the location is inside Romania (or unspecified/just "Romania").
- in_scope = false IF: the location is outside Romania (Bavaria, Bulgaria, Germany, anywhere non-Romanian), OR the scenario is not about forest planting/clearing (electric cars, emissions, weather, agriculture, urban heat, etc.).

ACTION:
- "plant" for: plant, reforest, replant, afforest, plantez, plantam, impadurim, reimpadurim, etc.
- "clear" for: clear, cut, log, deforest, clear-cut, defrisez, defrisam, taie, doboram, etc.

LOCATION — output the location EXACTLY as the user typed it, a single clean token. Do NOT translate it, do NOT add slashes, do NOT add alternate spellings. If user typed "Maramures", output "Maramures" (never "Maramures/Maramureș"). If user typed "Brasov", output "Brasov". If no location, output "".

SUB-REGION — map the location to one of:
- carpathians: Brasov, Sibiu (mountains), Apuseni, Retezat, Fagaras, Bucegi, Maramures (mountain), Carpati
- transylvanian_plateau: Cluj, Cluj-Napoca, Targu Mures, Alba Iulia, Medias, Sibiu (city), central Transylvania, Podisul Transilvaniei
- subcarpathians: Valcea, Arges, Buzau, Prahova hills, Subcarpati
- dobrogea: Constanta, Tulcea, Mangalia, Dobrogea
- moldavian_plain: Iasi, Bacau, Botosani, Suceava, Vaslui, Campia Moldovei
- unknown: just "Romania", or no location, or any unclear case

SPECIES — "oak" (stejar), "spruce" (molid), "beech" (fag), "pine" (pin), "mixed" (mixt/amestec), or null.

QUANTITY / UNIT / YEARS — fill these in if obvious, else use null. Other code will verify them.
- quantity: the raw number; area_unit: "hectares" | "trees" | "km2"; time_horizon_years: integer or null.

OUTPUT SCHEMA:
{
  "action": "plant" | "clear" | null,
  "quantity": number | null,
  "area_unit": "hectares" | "trees" | "km2" | null,
  "location": string,
  "sub_region": "carpathians" | "transylvanian_plateau" | "subcarpathians" | "dobrogea" | "moldavian_plain" | "unknown",
  "time_horizon_years": integer | null,
  "species": "oak" | "spruce" | "beech" | "pine" | "mixed" | null,
  "in_scope": boolean,
  "refusal_reason": null
}

(Leave refusal_reason as null — the wording is generated separately.)

OUTPUT ONLY THE JSON OBJECT."""

def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output: {raw!r}")
    return json.loads(match.group(0))

def _snap_time_horizon(years) -> int:
    try:
        y = int(years)
    except (TypeError, ValueError):
        return DEFAULT_TIME_HORIZON
    if y < 1:
        return 1
    if y > 25:
        return 25
    return min(VALID_TIME_HORIZONS, key=lambda v: abs(v - y))

def _convert_to_hectares(quantity: float, unit: str) -> float:
    if unit == "hectares":
        return quantity
    if unit == "trees":
        return quantity / DEFAULT_TREES_PER_HECTARE
    if unit == "km2":
        return quantity * 100.0
    raise ValueError(f"Unknown area unit: {unit!r}")

def _refusal_messages(lang: str) -> dict:
    table = {
        "ro": {
            "empty":        "Scenariu gol.",
            "action":       "Nu am identificat o acțiune de plantare sau defrișare.",
            "quantity":     "Nu am putut determina suprafața afectată.",
            "out_of_scope": "Scenariu în afara domeniului suportat.",
            "outside_ro":   "Scenariul este în afara României.",
            "error":        "Eroare la procesarea scenariului.",
        },
        "en": {
            "empty":        "Empty scenario.",
            "action":       "No planting or clearing action was identified.",
            "quantity":     "Could not determine the affected area.",
            "out_of_scope": "Scenario is outside the supported scope .",
            "outside_ro":   "Scenario is outside Romania.",
            "error":        "Error processing the scenario.",
        },
    }
    return table.get(lang, table["en"])

def _blank_result(user_lang: str, reason: str) -> dict:
    return {
        "action": None, "hectares": None, "raw_quantity": None, "raw_unit": None,
        "location": "", "sub_region": "unknown",
        "time_horizon_years": DEFAULT_TIME_HORIZON, "species": None,
        "in_scope": False, "refusal_reason": reason, "user_lang": user_lang,
    }

def _looks_foreign(location: str) -> bool:
    loc = _strip_diacritics(str(location)).strip().lower()
    return bool(loc) and loc not in ("romania", "")

def _build_result(data: dict, user_lang: str, raw_text: str) -> dict:
    msg = _refusal_messages(user_lang)
    text_norm = _strip_diacritics(raw_text).lower()

    if data.get("in_scope") is False:
        reason = msg["outside_ro"] if _looks_foreign(data.get("location", "")) else msg["out_of_scope"]
        return _blank_result(user_lang, reason)

    regex_action = _regex_detect_action(text_norm)
    llm_action = data.get("action")
    llm_action = str(llm_action).lower().strip() if llm_action else ""
    action = regex_action or (llm_action if llm_action in VALID_ACTIONS else None)
    if action not in VALID_ACTIONS:
        return _blank_result(user_lang, msg["action"])

    qty, unit = _regex_detect_quantity_unit(text_norm)
    if qty is None:
        try:
            qv = float(data.get("quantity"))
            uu = str(data.get("area_unit", "")).lower().strip()
            if qv > 0 and uu in VALID_AREA_UNITS:
                qty, unit = qv, uu
        except (TypeError, ValueError):
            pass
    if qty is None or qty <= 0 or unit not in VALID_AREA_UNITS:
        return _blank_result(user_lang, msg["quantity"])

    hectares = _convert_to_hectares(qty, unit)

    regex_years = _regex_detect_years(text_norm)
    if regex_years is not None:
        horizon = _snap_time_horizon(regex_years)
    elif data.get("time_horizon_years") is not None:
        horizon = _snap_time_horizon(data.get("time_horizon_years"))
    else:
        horizon = DEFAULT_TIME_HORIZON

    location = str(data.get("location", "")).strip()

    if "/" in location:
        location = location.split("/")[0].strip()

    sub = data.get("sub_region")
    sub = str(sub).lower().strip() if sub else "unknown"
    sub_region = sub if sub in VALID_SUB_REGIONS else "unknown"

    species = data.get("species")
    species = str(species).lower().strip() if species else None
    if species not in {"oak", "spruce", "beech", "pine", "mixed", None}:
        species = None

    return {
        "action": action,
        "hectares": hectares,
        "raw_quantity": qty,
        "raw_unit": unit,
        "location": location,
        "sub_region": sub_region,
        "time_horizon_years": horizon,
        "species": species,
        "in_scope": True,
        "refusal_reason": None,
        "user_lang": user_lang,
    }

def parse_scenario(text: str) -> dict:
    if not text or not text.strip():
        return _blank_result("en", "Empty scenario.")

    user_lang = _detect_language(text)

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text.strip()},
            ],
            options={"temperature": 0.1, "num_predict": 400},
            format="json",
        )
        raw = response["message"]["content"]
        parsed = _extract_json(raw)
        return _build_result(parsed, user_lang, text)

    except Exception as e:
        msg = _refusal_messages(user_lang)
        return _blank_result(user_lang, f"{msg['error']} ({type(e).__name__})")
