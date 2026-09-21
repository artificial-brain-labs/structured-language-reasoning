from src.execution_policy import ExecutionPolicies
from src.main import SLR


def test_execution_policies_are_loaded_from_knowledge_data():
    policies = ExecutionPolicies()
    assert policies.value("FACT", "resolve_object") == "literal"
    assert policies.value("RELATION", "resolve_object") == "entity"
    assert policies.value("CLASSIFICATION", "resolve_object") == "ontology_class"


def test_architectural_principles_are_machine_readable():
    policies = ExecutionPolicies()
    expected = {
        "no_guessing",
        "unknown_is_not_false",
        "derived_knowledge_is_not_asserted",
        "explicit_user_knowledge_only_enters_user_memory",
        "system_knowledge_is_immutable_at_runtime",
        "knowledge_must_be_data_driven",
        "knowledge_provenance_required",
    }
    assert expected <= set(policies.principles)
    assert all(policies.principle(name) is True for name in expected)
    assert policies.memory_boundaries["derived_knowledge"]["may_be_asserted"] is False
    assert policies.memory_boundaries["derived_knowledge"]["promotion_requires_explicit_confirmation"] is True


def test_operation_engine_uses_policy_for_relation_validation():
    slr = SLR()
    slr.process("The cat eats the mouse.")

    memories = slr.user_memory.query(predicate="EATS")
    assert len(memories) == 1
    assert memories[0].object in slr.user_memory.entities


def test_identity_relation_can_resolve_unknown_entities_without_guessing_type():
    slr = SLR()
    slr.process("Tom is Alex.")

    tom = slr.user_memory.find_named_entity("Tom")
    alex = slr.user_memory.find_named_entity("Alex")
    assert tom is not None
    assert alex is not None
    assert slr.user_memory.entities[tom]["concept"] == "UNKNOWN"
    assert slr.user_memory.entities[alex]["concept"] == "UNKNOWN"
    assert slr.user_memory.canonical_entity(tom) == slr.user_memory.canonical_entity(alex)


def test_asserted_user_memory_has_provenance():
    slr = SLR()
    slr.process("Tom is a cat.")

    tom = slr.user_memory.find_named_entity("Tom")
    cat = slr.user_memory.find_entity("CAT")
    memory = next(
        item for item in slr.user_memory.memories
        if item.subject == tom and item.predicate == "IS_A" and item.object == cat
    )
    assert memory.status == "ASSERTED"
    assert memory.source == "USER"


def test_unknown_is_not_false_and_does_not_gain_a_type_from_context():
    slr = SLR()
    slr.process("Dragon is sleeping.")

    dragon = slr.user_memory.find_named_entity("Dragon")
    assert dragon is not None
    assert slr.user_memory.entities[dragon]["concept"] == "UNKNOWN"

    parsed = slr.parser.parse("Is Dragon a cat?")
    assert slr.query.answer(parsed) == []


def test_derived_knowledge_has_provenance_and_is_not_stored():
    slr = SLR()
    slr.process("Tom is a cat.")

    tom = slr.user_memory.find_named_entity("Tom")
    derived = slr.reasoner.infer_is_a(tom)
    animal = next(item for item in derived if item["object"] == "ANIMAL")

    assert animal["status"] == "DERIVED"
    assert animal["source"] == "ONTOLOGY"
    assert animal["support"] == ["asserted_0001"]
    assert not any(
        item.subject == tom
        and item.predicate == "IS_A"
        and item.object == slr.user_memory.find_entity("ANIMAL")
        and item.status == "ASSERTED"
        for item in slr.user_memory.memories
    )
