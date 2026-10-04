from src.main import SLR


def test_negated_transitive_statement_parses_declaratively():
    slr = SLR()
    parsed = slr.parser.parse("cat does not eat rat")

    assert parsed.parse_status == "DETERMINED"
    assert parsed.meaning == "SUBJECT_VERB_OBJECT"
    assert parsed.operation == "ASSERT_RELATION"
    assert parsed.relation is None
    assert parsed.subject_word == "cat"
    assert parsed.verb_word == "eat"
    assert parsed.object_word == "rat"
    assert parsed.negated is True


def test_negated_relation_is_stored_and_conflicts_with_positive_relation():
    slr = SLR()
    slr.process("cat eats rat")
    answer = slr.process("cat does not eat rat")

    assert "conflicts" in answer.lower()

    query = slr.process("what cat eats")
    assert "don't know" in query.lower()
