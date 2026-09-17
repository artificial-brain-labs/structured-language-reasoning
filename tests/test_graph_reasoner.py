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
    assert all(edge.source == "REASONER" for edge in result.edges)
    assert graph.derived_edges() == []


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
