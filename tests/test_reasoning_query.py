import json

from src.ontology import Ontology
from src.reasoning_query import GraphQueryReasoner
from src.semantic_graph import GraphEdge, GraphNode, SemanticGraph


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
    graph.add_edge(GraphEdge("edge:tom-cat", "entity:tom", "IS_A", "concept:cat", status="ASSERTED"))
    return graph


def test_query_derives_animal_from_cat_without_persisting(tmp_path):
    graph = build_cat_graph()
    before = graph.to_dict()

    result = GraphQueryReasoner(ontology(tmp_path)).is_a(graph, "entity:tom", "ANIMAL")

    assert result.status == "YES"
    assert result.path[0] == "edge:tom-cat"
    assert result.path[-1] == "ANIMAL"
    assert graph.to_dict() == before
    assert graph.derived_edges() == []


def test_query_returns_unknown_when_no_classification_exists(tmp_path):
    graph = SemanticGraph()
    graph.add_node(GraphNode("entity:x", "ENTITY", "X", "UNKNOWN"))

    result = GraphQueryReasoner(ontology(tmp_path)).is_a(graph, "entity:x", "ANIMAL")

    assert result.status == "UNKNOWN"
    assert result.reason == "no_explicit_classification"


def test_query_does_not_treat_unknown_as_false(tmp_path):
    graph = build_cat_graph()

    result = GraphQueryReasoner(ontology(tmp_path)).is_a(graph, "entity:tom", "MAMMAL")

    assert result.status == "YES"
    assert result.reason is None


def test_query_does_not_guess_unknown_target_concept(tmp_path):
    graph = build_cat_graph()

    result = GraphQueryReasoner(ontology(tmp_path)).is_a(graph, "entity:tom", "MYSTERY")

    assert result.status == "UNKNOWN"
    assert result.reason == "unknown_target_concept"
