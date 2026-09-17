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
    resolver = SemanticContextResolver(slr.contextual_meaning, slr.lexicon)

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
