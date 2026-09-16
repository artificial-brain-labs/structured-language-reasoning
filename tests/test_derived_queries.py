from src.main import SLR


def test_classification_query_uses_ontology_derived_knowledge():
    slr = SLR()
    slr.process("Tom is a cat.")

    parsed = slr.parser.parse("Is Tom an animal?")
    result = slr.query.answer(parsed)

    assert result
    evidence = result[0]
    assert evidence["entity"] == slr.memory.find_named_entity("Tom")
    assert evidence["predicate"] == "IS_A"
    assert evidence["object"] == "ANIMAL"
    assert evidence["status"] == "DERIVED"
    assert evidence["source"] == "ONTOLOGY"


def test_classification_query_does_not_store_derived_fact():
    slr = SLR()
    slr.process("Tom is a cat.")

    slr.process("Is Tom an animal?")

    tom = slr.memory.find_named_entity("Tom")
    animal = slr.memory.find_entity("ANIMAL")
    assert not any(
        memory.subject == slr.memory.canonical_entity(tom)
        and memory.predicate == "IS_A"
        and memory.object == animal
        and memory.status == "ASSERTED"
        for memory in slr.memory.memories
    )


def test_unknown_classification_is_not_false():
    slr = SLR()
    slr.process("Tom is a cat.")

    parsed = slr.parser.parse("Is Tom a bird?")
    result = slr.query.answer(parsed)

    assert result == []


def test_classification_query_returns_asserted_knowledge_when_available():
    slr = SLR()
    slr.process("Tom is a cat.")

    parsed = slr.parser.parse("Is Tom a cat?")
    result = slr.query.answer(parsed)

    assert result
    evidence = result[0]
    assert evidence["object"] == "CAT"
    assert evidence["status"] == "ASSERTED"
