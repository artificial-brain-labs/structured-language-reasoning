from src.graph import KnowledgeGraph
from src.inference import InferenceEngine
from src.ontology import Ontology


def test_cat_inherits_mammal_properties():
    ontology = Ontology()
    assert ontology.is_a("CAT", "MAMMAL")
    assert ontology.is_a("CAT", "LIVING_THING")
    properties = ontology.properties("CAT")
    assert properties["warm_blooded"] is True
    assert properties["alive"] is True


def test_entity_inherits_without_duplicate_storage():
    ontology = Ontology()
    graph = KnowledgeGraph()
    graph.add_entity("tom", "CAT")
    engine = InferenceEngine(ontology)

    assert engine.entity_is_a(graph, "tom", "MAMMAL")
    assert engine.entity_is_a(graph, "tom", "LIVING_THING")
    assert engine.inherited_properties(graph, "tom")["has_whiskers"] is True

    # Only the explicit type is stored for Tom.
    assert graph.entities["tom"] == {"type": "CAT"}
    assert not graph.has_edge("tom", "is_a", "MAMMAL")


def test_unknown_entity_does_not_get_guessed():
    ontology = Ontology()
    graph = KnowledgeGraph()
    graph.add_entity("tom")
    engine = InferenceEngine(ontology)

    assert not engine.entity_is_a(graph, "tom", "CAT")
    assert engine.inherited_properties(graph, "tom") == {}
    assert engine.explain_is_a(graph, "tom", "MAMMAL") is None


def test_explicit_fact_has_provenance():
    graph = KnowledgeGraph()
    graph.add_entity("tom", "CAT")
    edge = graph.add_edge("tom", "state", "SLEEPING", source="USER")

    assert edge.source == "USER"
    assert edge.status == "ASSERTED"
    assert graph.has_edge("tom", "state", "SLEEPING")
