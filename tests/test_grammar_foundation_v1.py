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
    parsed = slr.parser.parse("The dom eats the mouse")
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


def test_v1_declarative_foundation_semantics():
    slr = SLR()

    transitive = slr.semantic_parser.parse(slr.parser.parse("cat eats mouse"))
    assert transitive.facts[0].predicate == "EATS"

    state = slr.semantic_parser.parse(slr.parser.parse("cat is tired"))
    assert state.facts[0].predicate == "TIRED"

    classification = slr.semantic_parser.parse(slr.parser.parse("cat is an animal"))
    assert classification.facts[0].predicate == "IS_A"

    identity = slr.semantic_parser.parse(slr.parser.parse("tom is dom"))
    assert identity.facts[0].predicate == "SAME_AS"

    property_assignment = slr.semantic_parser.parse(slr.parser.parse("cat is blue"))
    assert property_assignment.facts[0].predicate == "HAS_PROPERTY"


def test_v1_grammar_foundation_matrix():
    slr = SLR()

    cases = [
        ("cat", "SUBJECT_STATE", "state"),
        ("Tom", "SUBJECT_STATE", "entity_state"),
        ("the cat eats the mouse", "SUBJECT_VERB_OBJECT", "determiner_transitive"),
        ("Tom eats mouse", "SUBJECT_VERB_OBJECT", "entity_transitive"),
        ("the dom eats the mouse", "SUBJECT_VERB_OBJECT", "determiner_entity_transitive"),
        ("small cat eats mouse", "SUBJECT_VERB_OBJECT", "adjective_transitive"),
        ("the small black cat eats the mouse", "SUBJECT_VERB_OBJECT", "multiple_adjective_transitive"),
        ("Tom is a cat", "TYPE_ASSIGNMENT", "classification"),
        ("tom is dom", "SUBJECT_RELATION", "identity"),
        ("cat is blue", "PROPERTY_ASSIGNMENT", "property"),
        ("cat does not eat mouse", "SUBJECT_VERB_OBJECT", "negated_transitive"),
        ("cat is not tired", "SUBJECT_STATE", "negated_state"),
        ("Tom is not a cat", "TYPE_ASSIGNMENT", "negated_classification"),
        ("Tom is not blue", "PROPERTY_ASSIGNMENT", "negated_property"),
        ("what does the cat eat", "QUERY_OBJECT", "object_question"),
        ("what cat eats", "QUERY_OBJECT", "object_question_np"),
        ("who eats the mouse", "QUERY_SUBJECT", "subject_question"),
        ("what is Tom", "QUERY_TYPE", "type_question"),
        ("is the cat an animal", "QUERY_CLASSIFICATION", "classification_question"),
        ("is the cat blue", "QUERY_PROPERTY", "property_question"),
        ("what is blue", "QUERY_MEANING", "meaning_question"),
        ("I eat mouse", "SUBJECT_VERB_OBJECT", "pronoun_transitive"),
        ("I am tired", "SUBJECT_STATE", "pronoun_state"),
    ]

    for sentence, meaning, _construction in cases:
        parsed = slr.parser.parse(sentence)
        assert parsed.parse_status == "DETERMINED", sentence
        assert parsed.meaning == meaning, sentence


def test_v1_grammar_foundation_does_not_guess_unsupported_constructions():
    slr = SLR()

    for sentence in (
        "cat and dog eat mouse",
        "cat will eat mouse",
        "cat eats mouse in garden",
        "cat that eats mouse sleeps",
    ):
        parsed = slr.parser.parse(sentence)
        assert parsed.parse_status == "UNPARSED", sentence
