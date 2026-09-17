from src.cognitive_pipeline import CognitivePipeline
from src.semantic_graph import GraphEdge, GraphNode, SemanticGraph


def test_observed_classification_is_not_reasoning_evidence():
    pipeline = CognitivePipeline()
    graph = SemanticGraph(relation_schemas=pipeline.user_memory.relations.schemas)
    subject = "ENTITY-TOM"
    cat = "concept:CAT"
    animal = "concept:ANIMAL"
    graph.add_node(GraphNode(subject, "ENTITY", "Tom", "UNKNOWN"))
    graph.add_node(GraphNode(cat, "CLASS", "CAT", "CAT"))
    graph.add_node(GraphNode(animal, "CLASS", "ANIMAL", "ANIMAL"))
    graph.add_edge(GraphEdge("observed_1", subject, "IS_A", cat, status="OBSERVED"))
    graph.add_edge(GraphEdge("observed_2", cat, "IS_A", animal, status="OBSERVED"))

    reasoning = pipeline.reasoner.reason(graph)

    assert reasoning.edges == ()


def test_query_reasoning_requires_asserted_classification():
    pipeline = CognitivePipeline()
    graph = SemanticGraph(relation_schemas=pipeline.user_memory.relations.schemas)
    subject = "ENTITY-TOM"
    cat = "concept:CAT"
    graph.add_node(GraphNode(subject, "ENTITY", "Tom", "UNKNOWN"))
    graph.add_node(GraphNode(cat, "CLASS", "CAT", "CAT"))
    graph.add_edge(GraphEdge("observed_1", subject, "IS_A", cat, status="OBSERVED"))

    result = pipeline.query_is_a("Tom", "ANIMAL")
    assert result is None

    from src.reasoning_query import GraphQueryReasoner
    result = GraphQueryReasoner(pipeline.ontology).is_a(graph, subject, "ANIMAL")
    assert result.status == "UNKNOWN"
    assert result.reason == "no_explicit_classification"
