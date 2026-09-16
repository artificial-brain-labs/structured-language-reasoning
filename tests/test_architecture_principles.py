from pathlib import Path

from src.main import SLR


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"



def test_user_memory_isolated_between_slr_instances():
    first = SLR()
    second = SLR()

    first.process("Tom is a cat.")

    assert first.user_memory.find_named_entity("Tom") is not None
    assert second.user_memory.find_named_entity("Tom") is None
    assert not second.user_memory.memories


def test_system_memory_is_not_used_for_user_assertions():
    slr = SLR()

    slr.process("Tom is a cat.")

    assert not slr.memory.memories
    assert slr.user_memory.memories


def test_explicit_classification_does_not_mutate_cached_entity_concept():
    slr = SLR()

    slr.process("Tom is a cat.")
    tom = slr.user_memory.find_named_entity("Tom")

    assert tom is not None
    assert slr.user_memory.entities[tom]["concept"] == "UNKNOWN"
    assert any(
        memory.subject == slr.user_memory.canonical_entity(tom)
        and memory.predicate == "IS_A"
        and memory.status == "ASSERTED"
        for memory in slr.user_memory.memories
    )


def test_derived_knowledge_never_enters_asserted_user_memory():
    slr = SLR()

    slr.process("Tom is a cat.")
    tom = slr.user_memory.find_named_entity("Tom")

    derived = slr.reasoner.infer_is_a(tom)

    assert any(item["object"] == "FELINE" for item in derived)
    assert any(item["object"] == "ANIMAL" for item in derived)
    assert not any(
        memory.subject == slr.user_memory.canonical_entity(tom)
        and memory.status == "DERIVED"
        for memory in slr.user_memory.memories
    )


def test_unknown_entity_is_not_promoted_to_a_type_by_relation():
    slr = SLR()

    slr.process("Tom is a cat.")
    slr.process("Tom eats the bird.")
    bird = slr.user_memory.find_named_entity("bird")

    assert bird is not None
    assert slr.user_memory.entities[bird]["concept"] == "UNKNOWN"
    assert not slr.reasoner.explicit_types(bird)


def test_unknown_is_not_false_for_unresolved_relation_object():
    slr = SLR()

    slr.process("Tom is a cat.")
    response = slr.process("Tom eats the bird.")

    bird = slr.user_memory.find_named_entity("bird")
    assert bird is not None
    assert slr.user_memory.entities[bird]["concept"] == "UNKNOWN"
    assert any(
        memory.predicate == "EATS"
        and memory.object == bird
        and memory.status == "ASSERTED"
        for memory in slr.user_memory.memories
    )
    assert response is not None


def test_no_known_linguistic_facts_are_embedded_as_word_specific_branches():
    forbidden_literals = {
        '"cat"', "'cat'",
        '"dog"', "'dog'",
        '"mouse"', "'mouse'",
        '"eats"', "'eats'",
        '"sleeping"', "'sleeping'",
    }

    violations = []
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for literal in forbidden_literals:
            if literal in text:
                violations.append(f"{path.relative_to(ROOT)} contains {literal}")

    assert not violations, "Knowledge appears embedded in procedural code: " + "; ".join(violations)
