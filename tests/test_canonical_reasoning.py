from src.main import SLR
from src.graph_reasoner import SemanticGraphReasoner


def test_runtime_uses_canonical_graph_reasoner():
    slr = SLR()
    assert isinstance(slr.graph_reasoner, SemanticGraphReasoner)
    slr.process("Tom is a cat.")
    derived = [edge for edge in slr.graph.derived_edges() if edge.predicate == "IS_A"]
    assert derived
    assert all(edge.source == "ONTOLOGY" for edge in derived)
    assert all(edge.support for edge in derived)


def test_ontology_proof_support_points_to_asserted_evidence():
    slr = SLR()
    slr.process("Tom is a cat.")
    parsed = slr.parser.parse("Is Tom an animal?")
    result = slr.query.answer(parsed)[0]
    proof = result["proof"]
    root = proof["path"][0]
    assert root["status"] == "ASSERTED"
    root_support = root["support"]
    assert root_support
    for step in proof["path"][1:]:
        assert step["status"] == "DERIVED"
        assert step["rule"] == "ONTOLOGY_PARENT"
        assert step["support"] == root_support


def test_ontology_derived_edges_form_the_canonical_proof_chain():
    slr = SLR()
    slr.process("Tom is a cat.")

    subject = slr.query._resolve("Tom")
    path = slr.query.graph_query.classification(subject, "ANIMAL")

    assert path
    assert [slr.query.graph_query._node_concept(edge.subject) for edge in path] == [
        "CAT", "FELINE", "MAMMAL"
    ]
    assert [slr.query.graph_query._node_concept(edge.object) for edge in path] == [
        "FELINE", "MAMMAL", "ANIMAL"
    ]
    assert all(edge.status == "DERIVED" for edge in path)
    assert all(edge.source == "ONTOLOGY" for edge in path)


def test_explanation_path_is_composed_from_actual_graph_edges():
    slr = SLR()
    slr.process("Tom is a cat.")

    subject = slr.query._resolve("Tom")
    proof = slr.query.graph_query.explain_classification(subject, "ANIMAL")

    assert proof is not None
    assert len(proof["path"]) == 4
    graph_edges = {edge.edge_id: edge for edge in slr.graph.edges.values()}
    for item in proof["path"]:
        if item["status"] == "ASSERTED":
            continue
        matches = [
            edge for edge in graph_edges.values()
            if edge.subject == item["subject"]
            and edge.predicate == item["predicate"]
            and edge.object == next(
                (node_id for node_id, node in slr.graph.nodes.items() if node.concept == item["object"]),
                item["object"],
            )
            and edge.status == "DERIVED"
        ]
        assert matches
        assert item["support"] == list(matches[0].support)
