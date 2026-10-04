import json


def _load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def test_v1_grammar_coverage_production_links_are_valid():
    coverage = _load_json("knowledge/grammar_coverage.json")
    grammar = _load_json("knowledge/grammar_foundation.json")
    production_names = {production["name"] for production in grammar["productions"]}

    required_families = set(coverage["v1_completion_gate"]["required_families"])
    families = {
        family["id"]: family
        for family in coverage["construction_families"]
    }

    assert required_families <= families.keys()

    for family_id in required_families:
        family = families[family_id]
        production_map = family.get("production_map", {})
        for construction in family["constructions"]:
            assert construction in production_map
            assert production_map[construction]
            assert set(production_map[construction]) <= production_names
