import json

from src.ontology import Ontology
from src.semantic_graph import GraphEdge, GraphNode, SemanticGraph
from src.graph_reasoner import SemanticGraphReasoner


def ontology(tmp_path):
    with open("knowledge/ontology.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    path = tmp_path / "ontology.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return Ontology(path)


def build_cat_graph():
    graph = SemanticGraph()
    graph.add_node(GraphNode("entity:tom", "ENTITY", "Tom", "UNKNOWN"))
    graph.add_node(GraphNode("concept:cat", "CONCEPT", "cat", "CAT"))
    graph.add_node(GraphNode("concept:feline", "CONCEPT", "feline", "FELINE"))
    graph.add_node(GraphNode("concept:mammal", "CONCEPT", "mammal", "MAMMAL"))
    graph.add_node(GraphNode("concept:animal", "CONCEPT", "animal", "ANIMAL"))
    graph.add_node(GraphNode("concept:living", "CONCEPT", "living thing", "LIVING_THING"))
    graph.add_node(GraphNode("concept:thing", "CONCEPT", "thing", "THING"))
    graph.add_edge(GraphEdge("edge:tom-cat", "entity:tom", "IS_A", "concept:cat", status="ASSERTED"))
    return graph


def test_reasoner_derives_ontology_ancestors_without_persisting_them(tmp_path):
    graph = build_cat_graph()
    result = SemanticGraphReasoner(ontology(tmp_path)).reason(graph)

    derived_targets = {edge.object for edge in result.edges}
    assert derived_targets == {
        "concept:feline",
        "concept:mammal",
        "concept:animal",
        "concept:living",
        "concept:thing",
    }
    assert all(edge.status == "DERIVED" for edge in result.edges)
    assert all(edge.source == "ONTOLOGY" for edge in result.edges)
    assert graph.derived_edges() == []


def test_reasoner_preserves_asserted_subject_when_deriving_ontology_ancestors(tmp_path):
    graph = build_cat_graph()
    result = SemanticGraphReasoner(ontology(tmp_path)).reason(graph)

    assert result.edges
    assert all(edge.subject == "entity:tom" for edge in result.edges)


def test_reasoner_never_changes_asserted_graph(tmp_path):
    graph = build_cat_graph()
    before = graph.to_dict()

    SemanticGraphReasoner(ontology(tmp_path)).reason(graph)

    assert graph.to_dict() == before


def test_unknown_concept_is_not_guessed(tmp_path):
    graph = SemanticGraph()
    graph.add_node(GraphNode("entity:x", "ENTITY", "X", "UNKNOWN"))
    graph.add_node(GraphNode("concept:unknown", "CONCEPT", "mystery", "MYSTERY"))
    graph.add_edge(GraphEdge("edge:x-mystery", "entity:x", "IS_A", "concept:unknown", status="ASSERTED"))

    result = SemanticGraphReasoner(ontology(tmp_path)).reason(graph)

    assert result.edges == ()



def test_reasoner_ignores_conflicted_taxonomic_evidence(tmp_path):
    graph = build_cat_graph()
    graph.nodes["entity:alice"] = GraphNode("entity:alice", "ENTITY", "Alice", "UNKNOWN")
    graph.add_edge(
        GraphEdge(
            "edge:alice-cat",
            "entity:alice",
            "IS_A",
            "concept:cat",
            status="ASSERTED",
        )
    )
    graph.edges["edge:tom-cat"] = GraphEdge(
        "edge:tom-cat",
        "entity:tom",
        "IS_A",
        "concept:cat",
        status="CONFLICTED",
    )

    result = SemanticGraphReasoner(ontology(tmp_path)).reason(graph)

    tom_derived = [edge for edge in result.edges if edge.subject == "entity:tom"]
    alice_derived = [edge for edge in result.edges if edge.subject == "entity:alice"]

    assert tom_derived == []
    assert alice_derived
    assert all(edge.status == "DERIVED" for edge in alice_derived)


def test_conflicted_evidence_does_not_block_unrelated_valid_reasoning(tmp_path):
    graph = build_cat_graph()
    graph.nodes["entity:alice"] = GraphNode("entity:alice", "ENTITY", "Alice", "UNKNOWN")
    graph.add_edge(
        GraphEdge(
            "edge:alice-cat",
            "entity:alice",
            "IS_A",
            "concept:cat",
            status="ASSERTED",
        )
    )
    graph.edges["edge:tom-cat"] = GraphEdge(
        "edge:tom-cat",
        "entity:tom",
        "IS_A",
        "concept:cat",
        status="CONFLICTED",
    )

    before = graph.to_dict()
    result = SemanticGraphReasoner(ontology(tmp_path)).reason(graph)

    assert any(edge.subject == "entity:alice" for edge in result.edges)
    assert not any(edge.subject == "entity:tom" for edge in result.edges)
    assert graph.to_dict() == before
