from src.clarification_manager import ClarificationManager
from src.memory import DynamicMemory


def test_manager_creates_pending_request_without_classifying_entity():
    memory = DynamicMemory()
    entity = memory.create_named_entity("Tom")
    manager = ClarificationManager(memory)

    request = manager.request_entity_identity(entity)

    assert request is not None
    assert request.entity_id == entity
    assert "Who is Tom?" in request.question
    assert memory.entities[entity]["concept"] == "UNKNOWN"


def test_manager_matches_only_pending_entity():
    memory = DynamicMemory()
    tom = memory.create_named_entity("Tom")
    alex = memory.create_named_entity("Alex")
    manager = ClarificationManager(memory)
    manager.request_entity_identity(tom)

    assert manager.matches_entity(tom)
    assert not manager.matches_entity(alex)


def test_manager_clear_returns_request_and_removes_pending_state():
    memory = DynamicMemory()
    entity = memory.create_named_entity("Tom")
    manager = ClarificationManager(memory)
    manager.request_entity_identity(entity)

    request = manager.clear()

    assert request.entity_id == entity
    assert not manager.has_pending()
