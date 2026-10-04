from src.main import SLR
from src.reference_resolver import ReferenceResolver


def test_reference_anchor_is_declared_in_lexicon():
    slr = SLR(user_id="USER-001", username="Purnendu")
    assert slr.lexicon.get("i")["referent"] == "USER"


def test_declarative_reference_resolves_active_user_identity():
    slr = SLR(user_id="USER-001", username="Purnendu")
    resolution = slr.reference_resolver.resolve("i")

    assert resolution.status == "RESOLVED"
    assert resolution.reference is not None
    assert slr.user_memory.entities[resolution.reference]["name"] == "Purnendu"


def test_reference_resolution_is_unknown_without_anchor():
    slr = SLR(user_id="USER-001", username="Purnendu")
    resolution = slr.reference_resolver.resolve("unknown")

    assert resolution.status == "UNKNOWN"


def test_pronoun_subject_uses_resolved_runtime_entity():
    slr = SLR(user_id="USER-001", username="Purnendu")
    parsed = slr.parser.parse("I am tired")
    meaning = slr.semantic_parser.parse(parsed)

    assert meaning.operation is not None
    entity_id = slr.user_memory.find_named_entity("Purnendu")
    assert entity_id == meaning.operation.subject
    assert meaning.operation.predicate == "TIRED"


def test_process_pronoun_statement_stores_fact_for_active_user():
    slr = SLR(user_id="USER-001", username="Purnendu")
    result = slr.process("I am tired")

    assert "stored" in result.lower() or "understood" in result.lower()
    entity_id = slr.user_memory.find_named_entity("Purnendu")
    memories = slr.user_memory.query(subject=entity_id, predicate="TIRED")

    assert len(memories) == 1
