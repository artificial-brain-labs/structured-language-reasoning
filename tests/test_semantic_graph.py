from src.main import SLR
from src.graph_builder import SemanticGraphBuilder
from src.memory import DynamicMemory


def test_explicit_statement_becomes_asserted_graph_edge():
    slr = SLR()
    slr.process("Tom is a cat.")

    tom = slr.user_memory.find_named_entity("Tom")
    cat = slr.user_memory.find_entity("CAT")
    edges = [
        edge for edge in slr.graph.edges_from(tom, "IS_A")
        if edge.status == "ASSERTED"
    ]

    assert len(edges) == 1
    assert edges[0].object == cat
    assert edges[0].source == "USER"


def test_ontology_reasoning_appears_as_derived_graph_edge_only():
    slr = SLR()
    slr.process("Tom is a cat.")

    tom = slr.user_memory.find_named_entity("Tom")
    derived = [
        edge for edge in slr.graph.edges.values()
        if edge.status == "DERIVED"
        and edge.predicate == "IS_A"
    ]

    concepts = [
        (slr.graph.nodes[edge.subject].concept, slr.graph.nodes[edge.object].concept)
        for edge in derived
    ]

    assert ("CAT", "FELINE") in concepts
    assert ("FELINE", "MAMMAL") in concepts
    assert ("MAMMAL", "ANIMAL") in concepts
    assert all(edge.source == "ONTOLOGY" for edge in derived)
    assert not any(
        memory.subject == tom
        and memory.predicate == "IS_A"
        and slr.user_memory.entities.get(memory.object, {}).get("concept") == "ANIMAL"
        and memory.status == "ASSERTED"
        for memory in slr.user_memory.memories
    )


def test_unknown_entity_remains_unknown_in_graph():
    slr = SLR()
    result = slr.process("Dragon is sleeping.")

    dragon = slr.user_memory.find_named_entity("Dragon")
    assert "Who is Dragon?" in result
    assert slr.graph.nodes[dragon].concept == "UNKNOWN"
    assert slr.graph.nodes[dragon].node_type == "ENTITY"


def test_graph_does_not_modify_system_memory():
    slr = SLR()
    slr.process("Tom is a cat.")

    assert slr.memory.entities == {}
    assert slr.memory.memories == []


def test_graph_serialization_contains_nodes_edges_and_provenance():
    slr = SLR()
    slr.process("Tom is a cat.")

    data = slr.graph.to_dict()

    assert data["nodes"]
    assert data["edges"]
    classification = next(
        edge for edge in data["edges"]
        if edge["predicate"] == "IS_A" and edge["status"] == "ASSERTED"
    )
    assert classification["source"] == "USER"
    assert "confidence" in classification


def test_graph_builder_is_a_projection_and_does_not_mutate_memory():
    memory = DynamicMemory()
    tom = memory.create_named_entity("Tom")
    cat = memory.find_entity("CAT")
    memory.add_memory(tom, "IS_A", cat)
    before = list(memory.memories)

    graph = SemanticGraphBuilder().build(memory)

    assert graph.edges
    assert memory.memories == before
