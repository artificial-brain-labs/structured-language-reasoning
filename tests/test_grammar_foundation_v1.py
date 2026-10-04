from src.main import SLR


def test_v1_noun_phrase_pronoun_composes_as_subject():
    slr = SLR()
    parsed = slr.parser.parse("I am tired")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.meaning == "SUBJECT_STATE"
    assert parsed.subject_word == "i"
    assert parsed.verb_word == "tired"


def test_v1_negated_state_is_declarative():
    slr = SLR()
    parsed = slr.parser.parse("I am not tired")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.meaning == "SUBJECT_STATE"
    assert parsed.negated is True
    meaning = slr.semantic_parser.parse(parsed)
    assert meaning.facts[0].predicate == "NOT_TIRED"


def test_v1_negated_classification_is_declarative():
    slr = SLR()
    parsed = slr.parser.parse("Tom is not a cat")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.meaning == "TYPE_ASSIGNMENT"
    assert parsed.negated is True
    assert parsed.subject_word == "tom"
    assert parsed.object_word == "cat"
    meaning = slr.semantic_parser.parse(parsed)
    assert meaning.facts[0].predicate == "NOT_IS_A"


def test_v1_negated_property_is_declarative():
    slr = SLR()
    parsed = slr.parser.parse("Tom is not blue")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.meaning == "PROPERTY_ASSIGNMENT"
    assert parsed.negated is True
    meaning = slr.semantic_parser.parse(parsed)
    assert meaning.facts[0].predicate == "NOT_HAS_PROPERTY"
