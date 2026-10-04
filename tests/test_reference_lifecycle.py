from src.contextual_reference_memory import ContextualReferenceMemory
from src.main import SLR


def test_unresolved_reference_does_not_mutate_context():
    slr = SLR()
    before = len(slr.contextual_reference_memory)
    result = slr.process("it sleeps")
    assert "resolve" in result.lower()
    assert len(slr.contextual_reference_memory) == before


def test_ambiguous_reference_preserves_context_without_selecting():
    slr = SLR()
    slr.process("cat sleeps")
    slr.process("dog sleeps")
    before = len(slr.contextual_reference_memory)
    result = slr.process("it sleeps")
    assert "determine" in result.lower()
    assert len(slr.contextual_reference_memory) == before


def test_successful_statement_creates_contextual_mentions():
    slr = SLR()
    slr.process("cat eats rat")
    assert len(slr.contextual_reference_memory) == 2


def test_context_capacity_evicts_old_mentions_only():
    memory = ContextualReferenceMemory(capacity=2)
    memory.add("entity_1", "cat", "subject")
    memory.add("entity_2", "dog", "subject")
    memory.add("entity_3", "mouse", "subject")
    assert len(memory) == 2
    candidates = memory.candidates()
    assert [item.entity_id for item in candidates] == ["entity_3", "entity_2"]


def test_context_clear_does_not_change_persistent_user_memory():
    slr = SLR()
    slr.process("cat sleeps")
    cat_id = slr.user_memory.find_named_entity("cat")
    assert cat_id is not None
    assert len(slr.contextual_reference_memory) == 1

    slr.contextual_reference_memory.clear()

    assert len(slr.contextual_reference_memory) == 0
    assert slr.user_memory.find_named_entity("cat") == cat_id
    assert slr.user_memory.query(subject=cat_id)


def test_contextual_mentions_use_canonical_identity():
    slr = SLR()
    slr.process("tom sleeps")
    slr.process("dom is tom")

    tom_id = slr.user_memory.find_named_entity("tom")
    dom_id = slr.user_memory.find_named_entity("dom")
    assert tom_id is not None
    assert dom_id is not None

    canonical_tom = slr.user_memory.canonical_entity(tom_id)
    canonical_dom = slr.user_memory.canonical_entity(dom_id)
    assert canonical_tom == canonical_dom

    mentions = slr.contextual_reference_memory.mentions
    assert mentions
    assert all(item.entity_id == canonical_tom for item in mentions)


def test_failed_statement_does_not_create_contextual_mention():
    slr = SLR()
    slr.process("cat sleeps")
    before = len(slr.contextual_reference_memory)

    slr.process("this is not a supported construction")

    assert len(slr.contextual_reference_memory) == before
