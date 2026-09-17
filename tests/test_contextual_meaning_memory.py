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
