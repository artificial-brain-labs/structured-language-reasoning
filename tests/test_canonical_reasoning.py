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
