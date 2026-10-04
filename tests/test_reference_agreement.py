import pytest

from src.contextual_reference_memory import ContextualReferenceMemory
from src.lexicon import Lexicon
from src.semantics import Entity


def test_lexical_agreement_returns_only_explicit_attributes():
    lexicon = Lexicon()
    assert lexicon.agreement("i") == {"number": "SINGULAR", "person": "FIRST"}
    assert lexicon.agreement("it") == {"number": "SINGULAR", "person": "THIRD"}
    assert lexicon.agreement("cat") == {}


def test_semantic_entity_preserves_explicit_lexical_agreement():
    entity = Entity("self_001", "SELF", agreement={"number": "SINGULAR", "person": "FIRST"})
    assert entity.agreement == {"number": "SINGULAR", "person": "FIRST"}


def test_contextual_reference_mention_can_carry_explicit_agreement():
    memory = ContextualReferenceMemory()
    mention = memory.add("cat_001", "cat", "subject", concepts=("CAT",), agreement={"number": "SINGULAR"})
    assert dict(mention.agreement) == {"number": "SINGULAR"}


def test_contextual_reference_mention_keeps_unknown_agreement_unknown():
    memory = ContextualReferenceMemory()
    mention = memory.add("cat_001", "cat", "subject", concepts=("CAT",))
    assert mention.agreement == ()
