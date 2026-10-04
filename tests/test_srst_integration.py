from src.main import SLR
from src.reasoning.integration import SRSTObservationValidator
from src.reasoning.state import GoalStatus, ValidationStatus


def test_schema_bound_observation_passes_through_srst():
    validator = SRSTObservationValidator()
    valid, state, result = validator.validate("cat_001", "EAT", "mouse_001")

    assert valid
    assert result.terminated
    assert state.goal.status == GoalStatus.SATISFIED
    assert state.claims["observation_1"].status == ValidationStatus.SUPPORTED
    assert state.proof.has_node("validation_goal")


def test_slr_persists_canonical_eat_predicate():
    slr = SLR()
    result = slr.process("The cat eats the mouse.")

    assert "stored" in result.lower()
    assert any(memory.predicate == "EAT" for memory in slr.memory.memories)


def test_slr_rejects_type_invalid_eat_relation():
    slr = SLR()
    result = slr.process("The dog eats the cat.")

    # DOG is an ANIMAL and CAT is currently a THING, so the relation schema
    # should be enforced before durable storage.
    assert "cannot add" in result.lower()
    assert slr.memory.memories == []


def test_canonical_negation_detects_conflict():
    slr = SLR()
    slr.process("The cat eats the mouse.")
    result = slr.process("The cat does not eat the mouse.")

    assert "conflicts" in result.lower()
    assert all(
        memory.status == "CONFLICTED"
        for memory in slr.memory.memories
    )
