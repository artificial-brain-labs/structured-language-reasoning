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
    assert subject["category"] == "NOUN"
    assert subject["token"] == "cat"
    assert subject["concept"] == "CAT"
    assert subject["pos"] == "NOUN"

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
    assert structure["roles"]["subject"]["token"] == "zorb"
    assert structure["roles"]["subject"]["concept"] is None
    assert structure["roles"]["subject"]["pos"] is None
