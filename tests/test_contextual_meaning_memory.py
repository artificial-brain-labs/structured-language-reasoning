from src.main import SLR
from src.contextual_meaning_memory import ContextualMeaningMemory


def test_contextual_meaning_memory_learns_user_resolution():
    memory = ContextualMeaningMemory()
    memory.learn("bat", "bat.animal", ["bat.animal", "bat.sports"], "I saw the bat")
    assert memory.preferred_sense("bat", "I saw the bat") == "bat.animal"
    assert len(memory.find("bat")) == 1


def test_dictionary_is_not_mutated_by_contextual_learning():
    slr = SLR()
    before = [(s.sense_id, s.concept) for s in slr.lexicon.senses("bat")]
    memory = ContextualMeaningMemory()
    memory.learn("bat", "bat.animal", ["bat.animal", "bat.sports"], "I saw the bat")
    after = [(s.sense_id, s.concept) for s in slr.lexicon.senses("bat")]
    assert before == after


def test_learned_meaning_reused_for_related_context():
    memory = ContextualMeaningMemory()
    memory.learn("bat", "bat.animal", ["bat.animal", "bat.sports"], "I saw the bat")
    assert memory.preferred_sense("bat", "The bat was flying") == "bat.animal"


def test_unrelated_context_does_not_reuse_learned_meaning():
    memory = ContextualMeaningMemory()
    memory.learn("bat", "bat.animal", ["bat.animal", "bat.sports"], "I saw the bat")
    assert memory.preferred_sense("bat", "I bought the bat") is None


def test_conflicting_learned_contexts_do_not_create_a_guess():
    memory = ContextualMeaningMemory()
    memory.learn("bat", "bat.animal", ["bat.animal", "bat.sports"], "I saw the bat")
    memory.learn("bat", "bat.sports", ["bat.animal", "bat.sports"], "I saw the bat")
    assert memory.preferred_sense("bat", "I saw the bat") is None


def test_definition_semantics_can_resolve_a_related_future_context():
    slr = SLR()
    memory = ContextualMeaningMemory(slr.lexicon)
    memory.learn("bat", "bat.animal", ["bat.animal", "bat.sports"], "I saw the bat")
    assert memory.preferred_sense("bat", "The bat was flying") == "bat.animal"


def test_definition_semantics_does_not_resolve_without_evidence():
    slr = SLR()
    memory = ContextualMeaningMemory(slr.lexicon)
    memory.learn("bat", "bat.animal", ["bat.animal", "bat.sports"], "I saw the bat")
    assert memory.preferred_sense("bat", "The bat is expensive") is None
