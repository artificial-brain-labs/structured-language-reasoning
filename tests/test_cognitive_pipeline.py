from src.cognitive_pipeline import CognitivePipeline


def test_explicit_classification_flows_into_user_memory_and_query_reasoning():
    pipeline = CognitivePipeline()

    result = pipeline.process("Tom is a cat.")

    assert result.parse_status == "DETERMINED"
    assert result.operation == "ASSERT_CLASSIFICATION"
    assert len(result.memory_ids) == 1
    assert len(pipeline.user_memory.memories) == 1

    subject_id = pipeline.user_memory.find_named_entity("Tom")
    assert subject_id is not None
    memory = pipeline.user_memory.memories[0]
    assert memory.subject == subject_id
    assert memory.predicate == "IS_A"
    assert pipeline.user_memory.entities[memory.object]["concept"] == "CAT"
    assert memory.status == "ASSERTED"

    query = pipeline.query_is_a("Tom", "ANIMAL")
    assert query.status == "YES"
    assert "CAT" in query.path
    assert "FELINE" in query.path
    assert "MAMMAL" in query.path
    assert "ANIMAL" in query.path


def test_reasoning_does_not_promote_derived_facts_into_user_memory():
    pipeline = CognitivePipeline()
    pipeline.process("Tom is a cat.")

    before = list(pipeline.user_memory.memories)
    graph, reasoning = pipeline.reason_about_user()

    assert reasoning.edges
    assert all(edge.status == "DERIVED" for edge in reasoning.edges)
    assert list(pipeline.user_memory.memories) == before
    assert not any(
        memory.subject == pipeline.user_memory.find_named_entity("Tom")
        and pipeline.user_memory.entities[memory.object]["concept"] == "ANIMAL"
        for memory in pipeline.user_memory.memories
    )


def test_unknown_query_remains_unknown():
    pipeline = CognitivePipeline()
    pipeline.process("Tom is a cat.")

    result = pipeline.query_is_a("Tom", "UNKNOWN_CONCEPT")

    assert result.status == "UNKNOWN"
    assert result.reason == "unknown_target_concept"


def test_unparsed_interaction_is_not_written_to_user_memory():
    pipeline = CognitivePipeline()

    result = pipeline.process("Tom blorfles the moon.")

    assert result.parse_status == "UNPARSED"
    assert result.memory_ids == ()
    assert pipeline.user_memory.memories == []
    assert len(pipeline.tcm) == 1
