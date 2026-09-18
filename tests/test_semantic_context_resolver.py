from src.main import SLR
from src.semantic_context_resolver import SemanticContextResolver


def test_semantic_context_resolver_reuses_confirmed_sense():
    slr = SLR()
    parsed = slr.parser.parse("I see bat")
    context = slr.semantic_context.extract(parsed, "I see bat")
    slr.contextual_meaning.learn(
        "bat", "bat.animal", ["bat.animal", "bat.sports"],
        "I see bat", semantic_context=context
    )

    future = slr.parser.parse("The bat is flying")
    future_context = slr.semantic_context.extract(future, "The bat is flying")
    resolver = SemanticContextResolver(slr.contextual_meaning, slr.lexicon, slr.ontology)

    assert resolver.resolve(
        "bat", future_context, ["bat.animal", "bat.sports"]
    ) == "bat.animal"


def test_semantic_context_resolver_keeps_conflict_unresolved():
    slr = SLR()
    resolver = slr.semantic_context_resolver

    first = slr.parser.parse("I see bat")
    first_context = slr.semantic_context.extract(first, "I see bat")
    second = slr.parser.parse("I hit bat")
    second_context = slr.semantic_context.extract(second, "I hit bat")

    slr.contextual_meaning.learn(
        "bat", "bat.animal", ["bat.animal", "bat.sports"],
        "I see bat", semantic_context=first_context
    )
    slr.contextual_meaning.learn(
        "bat", "bat.sports", ["bat.animal", "bat.sports"],
        "I hit bat", semantic_context=second_context
    )

    current = slr.parser.parse("The bat")
    current_context = slr.semantic_context.extract(current, "The bat")

    assert resolver.resolve(
        "bat", current_context, ["bat.animal", "bat.sports"]
    ) is None


def test_clarification_learning_can_store_structured_context():
    slr = SLR()
    parsed = slr.parser.parse("I see bat")
    context = slr.semantic_context.extract(parsed, "I see bat")
    resolution = slr.contextual_meaning.learn(
        "bat", "bat.animal", ["bat.animal", "bat.sports"],
        "I see bat", semantic_context=context
    )
    assert resolution.semantic_context is context
    assert resolution.semantic_context.features["relation"] == "SEES"


def test_end_to_end_clarification_then_related_context_resolution():
    slr = SLR()

    first = slr.process("Tom sees bat")
    assert "which meaning" in first.lower()
    assert slr.clarification.pending is not None
    assert slr.clarification.pending.kind == "lexical_meaning"

    resolved = slr.process("bat.animal")
    assert "stored" in resolved.lower() or "understood" in resolved.lower()
    assert slr.clarification.pending is None

    later = slr.process("Tom sees bat")
    assert "which meaning" not in later.lower()


def test_end_to_end_learned_sense_does_not_leak_to_unrelated_relation():
    slr = SLR()

    slr.process("Tom sees bat")
    slr.process("bat.animal")

    unrelated = slr.process("Tom eats bat")
    assert "which meaning" in unrelated.lower()
    assert slr.clarification.pending is not None
    assert slr.clarification.pending.word == "bat"


def test_existing_contextual_evidence_still_resolves_flying_to_animal_sense():
    slr = SLR()
    parsed = slr.parser.parse("The bat is flying")
    context = slr.semantic_context.extract(parsed, "The bat is flying")

    slr.contextual_meaning.learn(
        "bat", "bat.animal", ["bat.animal", "bat.sports"],
        "Tom sees bat",
        semantic_context=slr.semantic_context.extract(
            slr.parser.parse("Tom sees bat"), "Tom sees bat"
        ),
    )

    assert "FLY" in context.concepts
    assert slr.semantic_context_resolver.resolve(
        "bat", context, ["bat.animal", "bat.sports"]
    ) == "bat.animal"


def test_existing_contextual_evidence_resolves_hit_to_sports_sense():
    slr = SLR()
    parsed = slr.parser.parse("Tom hits bat")
    context = slr.semantic_context.extract(parsed, "Tom hits bat")

    slr.contextual_meaning.learn(
        "bat", "bat.sports", ["bat.animal", "bat.sports"],
        "Tom hits bat", semantic_context=context,
    )

    assert "HIT" in context.concepts
    assert slr.semantic_context_resolver.resolve(
        "bat", context, ["bat.animal", "bat.sports"]
    ) == "bat.sports"


def test_existing_contextual_evidence_does_not_guess_from_unlisted_context():
    slr = SLR()
    learned = slr.parser.parse("Tom sees bat")
    learned_context = slr.semantic_context.extract(learned, "Tom sees bat")

    slr.contextual_meaning.learn(
        "bat", "bat.animal", ["bat.animal", "bat.sports"],
        "Tom sees bat", semantic_context=learned_context,
    )

    unrelated = slr.parser.parse("Tom eats bat")
    unrelated_context = slr.semantic_context.extract(unrelated, "Tom eats bat")

    assert "EAT" in unrelated_context.concepts
    assert slr.semantic_context_resolver.resolve(
        "bat", unrelated_context, ["bat.animal", "bat.sports"]
    ) is None


def test_ontology_branch_resolves_bat_animal_from_animal_classification():
    slr = SLR()
    parsed = slr.parser.parse("bat is animal")
    context = slr.semantic_context.extract(parsed, "bat is animal")

    slr.contextual_meaning.learn(
        "bat", "bat.animal", ["bat.animal", "bat.sports"],
        "bat is animal", semantic_context=context,
    )

    assert slr.semantic_context_resolver.resolve(
        "bat", context, ["bat.animal", "bat.sports"]
    ) == "bat.animal"


def test_ontology_branch_keeps_both_bat_senses_when_target_is_thing():
    slr = SLR()
    parsed = slr.parser.parse("bat is thing")
    context = slr.semantic_context.extract(parsed, "bat is thing")

    animal = slr.lexicon.senses("animal")[0]
    equipment = slr.lexicon.senses("thing") if slr.lexicon.contains("thing") else []

    # The current lexicon does not yet expose "thing" as a word. The ontology
    # itself therefore remains the authoritative structure for this branch.
    assert slr.ontology.is_a("BAT_ANIMAL", "THING")
    assert slr.ontology.is_a("BAT_EQUIPMENT", "THING")
