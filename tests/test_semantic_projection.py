import json

from src.lexicon import Lexicon
from src.parser import Parser
from src.semantic_projector import SemanticGraphProjector


def projector():
    with open("knowledge/relations.json", "r", encoding="utf-8") as f:
        relations = json.load(f)
    return SemanticGraphProjector(relations)


def test_sentence_semantics_project_to_graph_with_modifiers_and_relation():
    parsed = Parser(Lexicon()).parse("The small black cat eats the mouse.")
    graph = projector().project(parsed.semantic_structure, source="USER:interaction-001", support=("interaction-001",))

    subject = graph.nodes["sentence:subject:cat"]
    object_ = graph.nodes["sentence:object:mouse"]
    assert subject.concept == "CAT"
    assert object_.concept == "MOUSE"

    properties = {graph.nodes[e.object].concept for e in graph.edges_from(subject.node_id, "HAS_PROPERTY")}
    assert properties == {"SMALL", "BLACK"}

    relations = graph.edges_from(subject.node_id, "EATS")
    assert len(relations) == 1
    assert relations[0].object == object_.node_id
    assert relations[0].source == "USER:interaction-001"
    assert relations[0].support == ("interaction-001",)
    assert relations[0].status == "OBSERVED"


def test_projection_can_reuse_existing_user_memory_entity_identifier():
    parsed = Parser(Lexicon()).parse("Tom eats the mouse.")

    def resolve(token, concept):
        return "ENTITY-TOM-001" if token == "tom" else None

    graph = projector().project(parsed.semantic_structure, entity_resolver=resolve)
    assert "ENTITY-TOM-001" in graph.nodes
    assert graph.nodes["ENTITY-TOM-001"].name == "tom"
    assert graph.edges_from("ENTITY-TOM-001", "EATS")


def test_unknown_sentence_does_not_project_guessed_semantics():
    parsed = Parser(Lexicon()).parse("The strange cat eats the mouse.")
    graph = projector().project(parsed.semantic_structure)

    assert parsed.parse_status == "UNPARSED"
    assert graph.nodes == {}
    assert graph.edges == {}


def test_property_relation_is_defined_in_knowledge_data():
    with open("knowledge/relations.json", "r", encoding="utf-8") as f:
        relations = json.load(f)
    assert relations["HAS_PROPERTY"]["role"] == "modifier"
