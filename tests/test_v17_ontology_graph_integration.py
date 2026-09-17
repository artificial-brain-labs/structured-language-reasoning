from src.cognitive_pipeline import CognitivePipeline


def test_reasoning_has_ontology_targets_without_persisting_them_to_user_memory():
    pipeline = CognitivePipeline()
    pipeline.process("Tom is a cat.")

    graph, reasoning = pipeline.reason_about_user()

    assert reasoning.edges
    assert all(edge.status == "DERIVED" for edge in reasoning.edges)
    assert any(graph.nodes[edge.object].concept == "ANIMAL" for edge in reasoning.edges)
    assert len(pipeline.user_memory.memories) == 1
    assert pipeline.user_memory.entities[pipeline.user_memory.memories[0].object]["concept"] == "CAT"


def test_observed_classification_never_enters_reasoning_even_with_ontology_nodes():
    pipeline = CognitivePipeline()
    graph = pipeline.build_user_graph()
    subject = pipeline.user_memory.create_named_entity("Tom")
    cat = "concept:CAT"

    from src.semantic_graph import GraphEdge
    graph.add_edge(GraphEdge("observed_test", subject, "IS_A", cat, status="OBSERVED"))

    reasoning = pipeline.reasoner.reason(graph)
    assert reasoning.edges == ()
