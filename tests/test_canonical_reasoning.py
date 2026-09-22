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
        "UNKNOWN", "CAT", "FELINE", "MAMMAL"
    ]
    assert [slr.query.graph_query._node_concept(edge.object) for edge in path] == [
        "CAT", "FELINE", "MAMMAL", "ANIMAL"
    ]
    assert path[0].status == "ASSERTED"
    assert all(edge.status == "DERIVED" for edge in path[1:])
    assert all(edge.source == "ONTOLOGY" for edge in path[1:])


def test_explanation_path_is_composed_from_actual_graph_edges():
    slr = SLR()
    slr.process("Tom is a cat.")

    subject = slr.query._resolve("Tom")
    proof = slr.query.graph_query.explain_classification(subject, "ANIMAL")

    assert proof is not None
    assert len(proof["path"]) == 4

    for item in proof["path"]:
        if item["status"] == "ASSERTED":
            continue
        matches = [
            edge for edge in slr.graph.edges.values()
            if edge.status == "DERIVED"
            and edge.predicate == item["predicate"]
            and slr.query.graph_query._node_label(edge.subject) == item["subject"]
            and slr.query.graph_query._node_label(edge.object) == item["object"]
        ]
        assert matches
        assert item["support"] == list(matches[0].support)
