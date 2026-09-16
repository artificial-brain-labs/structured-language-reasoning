from src.execution_policy import ExecutionPolicies
from src.main import SLR


def test_execution_policies_are_loaded_from_knowledge_data():
    policies = ExecutionPolicies()
    assert policies.value("FACT", "resolve_object") == "literal"
    assert policies.value("RELATION", "resolve_object") == "entity"
    assert policies.value("CLASSIFICATION", "resolve_object") == "ontology_class"


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
