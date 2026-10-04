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


def test_v1_noun_phrase_adjective_composition():
    slr = SLR()
    parsed = slr.parser.parse("The small black cat eats the mouse")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.meaning == "SUBJECT_VERB_OBJECT"
    assert parsed.subject_word == "cat"
    assert parsed.object_word == "mouse"


def test_v1_determiner_entity_composition():
    slr = SLR()
    parsed = slr.parser.parse("The Tom eats the mouse")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.meaning == "SUBJECT_VERB_OBJECT"


def test_v1_object_question_supports_determiner_noun_subject():
    slr = SLR()
    parsed = slr.parser.parse("What does the cat eat")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.question_type == "OBJECT"
    assert parsed.subject_word == "cat"
    assert parsed.verb_word == "eat"


def test_v1_subject_question_supports_determiner_noun_object():
    slr = SLR()
    parsed = slr.parser.parse("Who eats the mouse")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.question_type == "SUBJECT"
    assert parsed.verb_word == "eats"
    assert parsed.object_word == "mouse"


def test_v1_classification_question_supports_noun_phrases():
    slr = SLR()
    parsed = slr.parser.parse("Is the cat an animal")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.question_type == "CLASSIFICATION"
    assert parsed.subject_word == "cat"
    assert parsed.object_word == "animal"


def test_v1_type_question_supports_entity():
    slr = SLR()
    parsed = slr.parser.parse("What is Tom")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.question_type == "TYPE"
    assert parsed.subject_word == "tom"


def test_v1_property_question_supports_noun_phrase():
    slr = SLR()
    parsed = slr.parser.parse("Is the cat blue")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.question_type == "PROPERTY"
    assert parsed.subject_word == "cat"
    assert parsed.object_word == "blue"


def test_v1_meaning_question_supports_adjective():
    slr = SLR()
    parsed = slr.parser.parse("What is blue")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.question_type == "MEANING"
    assert parsed.subject_word == "blue"
