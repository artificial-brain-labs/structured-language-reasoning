import json

from src.lexicon import Lexicon
from src.parser import Parser
from src.semantic_projector import SemanticGraphProjector
from src.user_memory import UserMemory
from src.graph_memory_boundary import GraphMemoryBoundary


def relations():
    with open("knowledge/relations.json", "r", encoding="utf-8") as f:
        return json.load(f)


def build_graph():
    parsed = Parser(Lexicon()).parse("The cat eats the mouse.")
    return SemanticGraphProjector(relations()).project(parsed.semantic_structure)


def test_observed_graph_is_not_automatically_promoted():
    graph = build_graph()
    memory = UserMemory()
    boundary = GraphMemoryBoundary(memory, endpoint_resolver=lambda node_id: node_id)

    edge = graph.edges_from("sentence:subject:cat", "EATS")[0]
    result = boundary.promote_edge(edge)

    assert result.status == "PENDING_CONFIRMATION"
    assert memory.memories == []


def test_promotion_requires_explicit_endpoint_resolution():
    graph = build_graph()
    memory = UserMemory()
    boundary = GraphMemoryBoundary(memory)

    edge = graph.edges_from("sentence:subject:cat", "EATS")[0]
    result = boundary.promote_edge(edge, confirmed=True)

    assert result.status == "REJECTED"
    assert result.reason == "explicit_endpoint_resolution_required"
    assert memory.memories == []


def test_confirmed_graph_edge_promotes_into_user_memory():
    graph = build_graph()
    memory = UserMemory()
    cat_id = memory.create_named_entity("cat")
    mouse_id = memory.create_named_entity("mouse")

    mapping = {
        "sentence:subject:cat": cat_id,
        "sentence:object:mouse": mouse_id,
    }
    boundary = GraphMemoryBoundary(memory, endpoint_resolver=mapping.get)

    edge = graph.edges_from("sentence:subject:cat", "EATS")[0]
    result = boundary.promote_edge(edge, confirmed=True, source="USER:interaction-001")

    assert result.status == "PROMOTED"
    assert result.memory.subject == cat_id
    assert result.memory.predicate == "EATS"
    assert result.memory.object == mouse_id
    assert result.memory.status == "ASSERTED"
    assert len(memory.memories) == 1
    assert len(memory.evidence.records) == 1


def test_derived_or_hypothetical_edges_cannot_cross_boundary():
    graph = build_graph()
    memory = UserMemory()
    boundary = GraphMemoryBoundary(memory, endpoint_resolver=lambda node_id: node_id)

    observed = graph.edges_from("sentence:subject:cat", "EATS")[0]
    derived = type(observed)(
        edge_id="derived-001",
        subject=observed.subject,
        predicate=observed.predicate,
        object=observed.object,
        status="DERIVED",
    )

    result = boundary.promote_edge(derived, confirmed=True)

    assert result.status == "REJECTED"
    assert result.reason == "edge_not_observed"
    assert memory.memories == []
