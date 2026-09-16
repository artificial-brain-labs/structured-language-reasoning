from src.main import SLR


def test_new_domain_concept_and_relation_are_driven_by_knowledge_data():
    """A new concept/relation should work without domain-specific Python logic."""
    slr = SLR()

    response = slr.process("The tree sees the garden.")

    assert response == "I have stored that in memory."

    tree = slr.user_memory.find_entity("TREE")
    garden = slr.user_memory.find_entity("GARDEN")

    assert any(
        memory.subject == tree
        and memory.predicate == "SEES"
        and memory.object == garden
        for memory in slr.user_memory.memories
    )


def test_new_concept_inherits_properties_from_data_defined_parent():
    slr = SLR()

    tree = slr.user_memory.find_entity("TREE")

    assert slr.ontology.is_a("TREE", "PLANT")
    assert slr.ontology.is_a("TREE", "LIVING_THING")
    assert slr.ontology.properties("TREE")["alive"] is True
    assert slr.ontology.properties("TREE")["can_grow"] is True
    assert slr.user_memory.entities[tree]["concept"] == "TREE"


def test_unknown_domain_word_is_not_guessed():
    slr = SLR()

    response = slr.process("The dragon sees the garden.")

    assert "Who is dragon?" in response
    dragon = slr.user_memory.find_named_entity("dragon")
    assert dragon is not None
    assert slr.user_memory.entities[dragon]["concept"] == "UNKNOWN"
