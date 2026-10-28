import json
import time

from ai.ai_scenario_parser import parse_scenario
from ai.ai_output_formatter import format_scenario_summary

TEST_SCENARIOS = [

    "Plant 10000 oak trees near Brașov over the next 5 years.",
    "What if we reforest 500 hectares in the Apuseni mountains?",
    "Clear-cut 200 hectares of spruce in Maramureș, 10 year impact.",
    "Reforest 1000 ha around Cluj-Napoca for 25 years.",
    "Deforest 100 hectares near Iași.",

    "Ce s-ar întâmpla dacă plantăm 10000 de stejari lângă Brașov în următorii 5 ani?",
    "Plantăm 500 de hectare de fag în Apuseni.",
    "Defrișare a 200 de hectare de molid în Maramureș, impact pe 10 ani.",

    "plantez 10 hectare de copaci in Alba Iulia - cum se modifica vremea in 5 ani?",
    "ce se intampla daca plantam 5000 de stejari langa Brasov?",
    "vreau sa plantez 200 hectare de fag in Apuseni pentru 10 ani",
    "daca taie 100 hectare de padure langa Iasi, ce se intampla?",
    "defrisez 50 hectare de molid in Maramures, impact pe 25 ani",
    "reimpadurim 1000 ha in jurul Cluj-Napoca pentru 25 de ani",
    "plantam 50000 de copaci mixti in Dobrogea",
    "cum se modifica clima daca defrisam 300 ha langa Sibiu?",

    "Plant trees on 5 km² near Brașov for 10 years.",
    "plantez 3 km patrati de padure in Apuseni",

    "Plantăm 2000 ha în Romania for 30 years.",
    "plantam 500 ha de fag in Carpati pentru 50 de ani",

    "Plant some trees in Romania.",
    "plantam niste copaci in Romania",

    "What if we plant 5000 trees in Bavaria?",
    "plantez 5000 de stejari in Bavaria",

    "Convince 100000 people to drive electric cars.",
    "convingi 100000 de oameni sa conduca masini electrice",
    "ce se intampla daca ploua mult anul viitor?",
    "",
]

def main():
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n{'='*72}")
        print(f"[{i}] INPUT: {scenario!r}")
        t0 = time.time()
        result = parse_scenario(scenario)
        elapsed = time.time() - t0
        print(f"    ({elapsed:.1f}s, lang={result.get('user_lang')})")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"    SUMMARY: {format_scenario_summary(result)}")

if __name__ == "__main__":
    main()
