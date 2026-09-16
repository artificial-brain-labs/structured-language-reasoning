from src.main import SLR


def test_ontology_derived_classification_is_not_stored_as_asserted_memory():
    slr = SLR()
    slr.process("Tom is a cat.")

    tom = slr.memory.find_named_entity("Tom")
    derived = slr.reasoner.infer_is_a(tom)

    assert any(item["object"] == "MAMMAL" for item in derived)
    assert any(item["object"] == "ANIMAL" for item in derived)
    assert not any(
        memory.subject == slr.memory.canonical_entity(tom)
        and memory.predicate == "IS_A"
        and memory.object == slr.memory.find_entity("MAMMAL")
        for memory in slr.memory.memories
    )


def test_inference_rules_are_loaded_from_knowledge_data():
    slr = SLR()
    assert any(rule["name"] == "transitive_is_a" for rule in slr.reasoner.inference_rules.enabled())


def test_derived_facts_are_marked_as_derived_and_have_support():
    slr = SLR()
    cat = slr.memory.find_entity("CAT")
    mammal = slr.memory.find_entity("MAMMAL")
    animal = slr.memory.find_entity("ANIMAL")

    slr.memory.add_memory("cat_999", "IS_A", mammal)
    slr.memory.add_memory(mammal, "IS_A", animal)

    derived = slr.reasoner.derive()

    result = next(
        item for item in derived
        if item["subject"] == "cat_999"
        and item["predicate"] == "IS_A"
        and item["object"] == animal
    )
    assert result["status"] == "DERIVED"
    assert result["source"] == "INFERENCE"
    assert len(result["support"]) == 2
