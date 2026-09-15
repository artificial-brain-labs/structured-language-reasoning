from src.executor import SemanticExecutor
from src.memory import DynamicMemory
from src.operation_registry import OperationRegistry
from src.semantics import SemanticOperation


def test_executor_assert_state():
    memory = DynamicMemory()
    subject = memory.create_entity("CAT", name="cat")
    operation = SemanticOperation(
        name="ASSERT_STATE",
        subject=subject,
        predicate="SLEEP",
    )

    result = SemanticExecutor(memory).execute(operation)

    assert result is not None
    assert len(memory.memories) == 1
    assert memory.memories[0].subject == subject
    assert memory.memories[0].predicate == "SLEEP"
    assert memory.memories[0].object is None


def test_executor_assert_relation():
    memory = DynamicMemory()
    subject = memory.create_entity("CAT", name="cat")
    object_ = memory.create_entity("MOUSE", name="mouse")
    operation = SemanticOperation(
        name="ASSERT_RELATION",
        subject=subject,
        predicate="EATS",
        object=object_,
    )

    result = SemanticExecutor(memory).execute(operation)

    assert result is not None
    assert len(memory.memories) == 1
    assert memory.memories[0].subject == subject
    assert memory.memories[0].predicate == "EATS"
    assert memory.memories[0].object == object_


def test_executor_does_not_contain_domain_specific_predicate_logic():
    memory = DynamicMemory()
    subject = memory.create_entity("THING", name="x")
    object_ = memory.create_entity("THING", name="y")
    operation = SemanticOperation(
        name="ASSERT_RELATION",
        subject=subject,
        predicate="ARBITRARY_RELATION",
        object=object_,
    )

    result = SemanticExecutor(memory).execute(operation)

    assert result is not None
    assert memory.memories[0].predicate == "ARBITRARY_RELATION"


def test_executor_uses_operation_registry():
    memory = DynamicMemory()
    registry = OperationRegistry()
    calls = []

    def custom_handler(operation, source, confidence):
        calls.append((operation.name, source, confidence))
        return "handled"

    registry.register("CUSTOM_OPERATION", custom_handler)
    operation = SemanticOperation(name="CUSTOM_OPERATION")

    result = SemanticExecutor(memory, registry=registry).execute(
        operation,
        source="TEST",
        confidence=0.7,
    )

    assert result == "handled"
    assert calls == [("CUSTOM_OPERATION", "TEST", 0.7)]
