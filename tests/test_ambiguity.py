from src.main import SLR


def test_dictionary_supplies_blue_meanings():
    slr = SLR()
    senses = slr.lexicon.senses("blue")
    assert len(senses) == 2
    assert {sense.concept for sense in senses} == {"COLOR", "EMOTIONAL_STATE"}


def test_blue_remains_ambiguous_without_context():
    slr = SLR()
    answer = slr.process("What is blue?")
    assert "multiple dictionary meanings" in answer.lower()
    assert "blue.color" in answer.lower()
    assert "blue.sadness" in answer.lower()


def test_explicit_blue_property_is_stored_without_turning_blue_into_a_type():
    slr = SLR()
    slr.process("zorb is blue")
    zorb = slr.user_memory.find_named_entity("zorb")
    blue = slr.user_memory.find_named_entity("blue")
    assert zorb is not None
    assert blue is not None
    assert any(
        m.subject == slr.user_memory.canonical_entity(zorb)
        and m.predicate == "HAS_PROPERTY"
        and m.object == slr.user_memory.canonical_entity(blue)
        and m.status == "ASSERTED"
        for m in slr.user_memory.memories
    )
    assert not any(m.predicate == "IS_A" and m.subject == zorb for m in slr.user_memory.memories)


def test_property_query_uses_explicit_relation():
    slr = SLR()
    slr.process("zorb is blue")
    assert slr.process("is zorb blue").lower().startswith("yes")


def test_unknown_word_is_not_given_dictionary_meaning():
    slr = SLR()
    assert slr.lexicon.senses("zorb") == []


def test_what_is_word_is_a_meaning_query():
    slr = SLR()
    parsed = slr.parser.parse("What is blue?")
    assert parsed.question_type == "MEANING"
    assert parsed.meaning == "QUERY_MEANING"


def test_meaning_query_returns_dictionary_senses_without_type_inference():
    slr = SLR()
    answer = slr.process("What is blue?")
    assert "dictionary meanings" in answer.lower()
    assert "blue.color" in answer.lower()
    assert "blue.sadness" in answer.lower()


def test_ambiguous_lexicon_entry_has_no_single_concept():
    slr = SLR()
    assert slr.lexicon.concept("bat") is None


def test_ontology_resolves_first_time_ambiguous_classification_without_learning():
    slr = SLR()
    answer = slr.process("bat is animal")
    assert "which meaning" not in answer.lower()
    assert slr.clarification.pending is None
    entity = slr.user_memory.find_named_entity("bat")
    assert entity is not None
    assert slr.user_memory.entities[entity]["concept"] == "BAT_ANIMAL"


def test_query_resolves_ambiguous_bat_as_animal_from_ontology():
    slr = SLR()
    answer = slr.process("Is bat an animal?")
    assert answer.startswith("Yes.")
    assert "BAT_ANIMAL -> ANIMAL" in answer
    assert slr.user_memory.find_named_entity("bat") is None


def test_query_resolves_ambiguous_bat_as_object_from_ontology():
    slr = SLR()
    answer = slr.process("Is bat an object?")
    assert answer.startswith("Yes.")
    assert "BAT_EQUIPMENT -> OBJECT" in answer
    assert slr.user_memory.find_named_entity("bat") is None


def test_query_keeps_bat_ambiguous_when_both_senses_fit_thing():
    slr = SLR()
    answer = slr.process("Is bat a thing?")
    assert "multiple dictionary meanings" in answer.lower()
    assert "bat.animal" in answer.lower()
    assert "bat.sports" in answer.lower()


def test_query_does_not_guess_bat_as_dog():
    slr = SLR()
    assert slr.process("Is bat a dog?") == "I don't know."


def test_query_reuses_explicit_property_for_ambiguous_blue():
    slr = SLR()
    slr.process("zorb is blue")
    assert slr.process("Is zorb blue?").lower().startswith("yes")
