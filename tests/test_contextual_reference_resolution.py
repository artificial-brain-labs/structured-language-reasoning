from src.main import SLR


def test_contextual_reference_resolves_single_established_antecedent():
    slr = SLR()
    slr.process("cat sleeps")

    resolution = slr.reference_resolver.resolve("it")

    assert resolution.status == "RESOLVED"
    assert resolution.reference == slr.user_memory.find_named_entity("cat")


def test_contextual_reference_remains_unknown_without_antecedent():
    slr = SLR()

    resolution = slr.reference_resolver.resolve("it")

    assert resolution.status == "UNKNOWN"
    assert resolution.reference is None


def test_contextual_reference_remains_ambiguous_with_multiple_candidates():
    slr = SLR()
    slr.process("cat eats rat")

    resolution = slr.reference_resolver.resolve("it")

    assert resolution.status == "AMBIGUOUS"
    assert len(resolution.candidates) == 2


def test_contextual_reference_does_not_create_a_new_entity_when_unresolved():
    slr = SLR()
    before = len(slr.user_memory.entities)

    result = slr.process("it sleeps")

    assert "resolve" in result.lower()
    assert len(slr.user_memory.entities) == before


def test_contextual_reference_can_bind_an_object_from_prior_context():
    slr = SLR()
    slr.process("cat sleeps")

    result = slr.process("dog sees it")

    assert "stored" in result.lower() or "understood" in result.lower()
    cat_id = slr.user_memory.find_named_entity("cat")
    dog_id = slr.user_memory.find_named_entity("dog")
    memories = slr.user_memory.query(subject=dog_id, predicate="SEES", object=cat_id)

    assert len(memories) == 1
