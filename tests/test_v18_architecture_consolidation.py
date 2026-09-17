from src.cognitive_pipeline import CognitivePipeline
from src.graph_reasoner import SemanticGraphReasoner
from src.ontology import Ontology
from src.reasoning_query import GraphQueryReasoner


def test_reasoning_and_query_use_relation_role_data_not_embedded_predicate_names():
    pipeline = CognitivePipeline()
    assert pipeline.reasoner._relation_for_role("canonical_taxonomic") == "IS_A"
    assert pipeline.query_reasoner._relation_for_role("canonical_taxonomic") == "IS_A"


def test_asserted_graph_edges_are_traceable_to_user_evidence():
    pipeline = CognitivePipeline()
    pipeline.process("Tom is a cat.")

    graph = pipeline.build_user_graph()
    tom = pipeline.user_memory.find_named_entity("Tom")
    edge = next(edge for edge in graph.edges_from(tom) if edge.predicate == "IS_A")

    assert edge.status == "ASSERTED"
    assert edge.attributes["evidence"]
    assert edge.attributes["evidence"][0]["kind"] == "ASSERTION"
    assert edge.attributes["evidence"][0]["confirmed"] is True


def test_derived_graph_edges_reference_asserted_support_without_persisting():
    pipeline = CognitivePipeline()
    pipeline.process("Tom is a cat.")
    before = list(pipeline.user_memory.memories)

    graph, reasoning = pipeline.reason_about_user()

    assert reasoning.edges
    assert all(edge.status == "DERIVED" for edge in reasoning.edges)
    assert all(edge.support for edge in reasoning.edges)
    assert list(pipeline.user_memory.memories) == before


def test_legacy_inference_facade_does_not_create_competing_reasoning_state():
    pipeline = CognitivePipeline()
    pipeline.process("Tom is a cat.")
    legacy = __import__("src.inference", fromlist=["InferenceEngine"]).InferenceEngine(
        pipeline.ontology,
        pipeline.user_memory.relations.schemas,
    )
    graph = pipeline.build_user_graph()
    tom = pipeline.user_memory.find_named_entity("Tom")

    assert legacy.reasoner.__class__ is SemanticGraphReasoner
    assert legacy.entity_is_a(graph, tom, "ANIMAL") is True


def test_legacy_graph_facade_does_not_keep_an_independent_edge_store():
    legacy_graph = __import__("src.graph", fromlist=["KnowledgeGraph"]).KnowledgeGraph()
    legacy_graph.add_entity("tom", "CAT")
    legacy_graph.add_entity("concept:ANIMAL", "ANIMAL")
    legacy_graph.add_edge("tom", "IS_A", "concept:ANIMAL")

    assert len(legacy_graph._graph.edges) == 1
    assert legacy_graph.has_edge("tom", "IS_A", "concept:ANIMAL")
