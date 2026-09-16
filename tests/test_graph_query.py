from src.graph_query import SemanticGraphQuery
from src.main import SLR


def test_graph_query_finds_asserted_classification():
    slr = SLR()
    slr.process("Tom is a cat.")

    tom = slr.user_memory.find_named_entity("Tom")
    path = SemanticGraphQuery(slr.graph).classification(tom, "CAT")

    assert path
    assert len(path) == 1
    assert path[0].status == "ASSERTED"
    assert path[0].source == "USER"


def test_graph_query_finds_derived_classification_without_memory_promotion():
    slr = SLR()
    slr.process("Tom is a cat.")

    tom = slr.user_memory.find_named_entity("Tom")
    path = SemanticGraphQuery(slr.graph).classification(tom, "ANIMAL")

    assert path
    assert path[-1].status == "DERIVED"
    assert slr.graph.nodes[path[-1].object].concept == "ANIMAL"
    assert not any(
        memory.subject == tom
        and memory.predicate == "IS_A"
        and slr.user_memory.entities.get(memory.object, {}).get("concept") == "ANIMAL"
        and memory.status == "ASSERTED"
        for memory in slr.user_memory.memories
    )


def test_graph_query_returns_no_type_for_unknown_entity():
    slr = SLR()
    slr.process("Dragon is sleeping.")

    dragon = slr.user_memory.find_named_entity("Dragon")
    path = SemanticGraphQuery(slr.graph).classification(dragon, "ANIMAL")

    assert path is None


def test_graph_query_object_and_subject_traversal():
    slr = SLR()
    slr.process("Tom is a cat.")
    slr.process("Tom eats mouse.")

    tom = slr.user_memory.find_named_entity("Tom")
    mouse = slr.user_memory.find_entity("MOUSE")
    graph_query = SemanticGraphQuery(slr.graph)

    objects = graph_query.objects(tom, "EATS")
    subjects = graph_query.subjects(mouse, "EATS")

    assert objects == [mouse]
    assert subjects == [tom]


def test_graph_query_is_read_only():
    slr = SLR()
    slr.process("Tom is a cat.")
    before = list(slr.user_memory.memories)

    tom = slr.user_memory.find_named_entity("Tom")
    SemanticGraphQuery(slr.graph).classification(tom, "ANIMAL")

    assert slr.user_memory.memories == before
