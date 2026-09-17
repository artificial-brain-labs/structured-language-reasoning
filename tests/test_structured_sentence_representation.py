from src.lexicon import Lexicon
from src.parser import Parser


def test_cat_sleeping_produces_compositional_structure():
    parser = Parser(Lexicon())

    parsed = parser.parse("A cat is sleeping.")
    structure = parsed.semantic_structure

    assert parsed.parse_status == "DETERMINED"
    assert structure["category"] == "STATEMENT"
    assert structure["production"] == "statement_state_np_aux_state"
    assert structure["features"] == {"tense": "PRESENT"}

    subject = structure["roles"]["subject"]
    assert subject["category"] == "NP"
    assert subject["head"]["category"] == "NOUN"
    assert subject["head"]["token"] == "cat"
    assert subject["head"]["concept"] == "CAT"
    assert subject["head"]["pos"] == "NOUN"

    predicate = structure["roles"]["verb"]
    assert predicate["category"] == "STATE"
    assert predicate["token"] == "sleeping"
    assert predicate["concept"] == "SLEEP"
    assert predicate["pos"] == "STATE"
    assert predicate["features"] == {
        "base": "sleep",
        "aspect": "PROGRESSIVE",
    }


def test_unknown_word_remains_unknown_in_structured_representation():
    parser = Parser(Lexicon())

    parsed = parser.parse("A zorb is sleeping.")
    structure = parsed.semantic_structure

    assert parsed.parse_status == "DETERMINED"
    subject = structure["roles"]["subject"]
    assert subject["category"] == "NP"
    assert subject["head"]["category"] == "ENTITY"
    assert subject["head"]["token"] == "zorb"
    assert subject["head"]["concept"] is None
    assert subject["head"]["pos"] is None
