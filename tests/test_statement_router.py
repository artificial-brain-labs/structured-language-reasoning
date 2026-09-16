from src.main import SLR
from src.semantics import SemanticOperation
from src.statement_router import StatementRouter


def test_router_dispatches_registered_operations_without_operation_specific_logic():
    router = StatementRouter()
    calls = []
    def handler(operation, context):
        calls.append((operation.name, context))
        return "handled"
    router.register("CUSTOM_OPERATION", handler)
    operation = SemanticOperation(name="CUSTOM_OPERATION")
    result = router.dispatch(operation, context={"source": "test"})
    assert result.result == "handled"
    assert result.operation is operation
    assert calls == [("CUSTOM_OPERATION", {"source": "test"})]


def test_router_does_not_invent_unknown_operations():
    router = StatementRouter()
    operation = SemanticOperation(name="UNKNOWN_OPERATION")
    result = router.dispatch(operation)
    assert result.result is None
    assert result.operation is operation


def test_main_registers_all_declarative_operations():
    slr = SLR()
    for operation_name in slr.executor.definitions.operations:
        assert operation_name in slr.router._handlers


def test_unknown_entity_is_not_classified_by_routing():
    slr = SLR()
    response = slr.process("Alex is running.")
    assert "Who is Alex?" in response
    alex = slr.memory.find_named_entity("Alex")
    assert alex is not None
    assert slr.memory.entities[alex]["concept"] == "UNKNOWN"


def test_operation_mechanisms_are_selected_by_execution_policy_data():
    slr = SLR()
    policies = slr.operation_engine.policies.mechanisms
    for mechanism, policy in policies.items():
        handler_name = policy.get("handler")
        assert handler_name
        assert mechanism in slr.operation_engine._handlers
        assert slr.operation_engine._handlers[mechanism].__name__ == f"_{handler_name}"


def test_clarification_acceptance_is_selected_by_policy_data():
    slr = SLR()
    assert "TYPE_ASSIGNMENT" in slr.clarification_policy.accepted_meanings("entity_identity")
