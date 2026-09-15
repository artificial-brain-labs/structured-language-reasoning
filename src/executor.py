from .operation_registry import OperationRegistry
from .operations import OperationDefinitions


class SemanticExecutor:
    """Execute semantic operations through a mechanism registry.

    Operation metadata is loaded from declarative knowledge. The registry
    selects execution mechanisms; domain concepts and relation behavior
    remain data-driven through knowledge and memory schemas.
    """

    def __init__(self, memory, registry=None, definitions=None):
        self.memory = memory
        self.registry = registry or OperationRegistry()
        self.definitions = definitions or OperationDefinitions()
        self._register_default_operations()

    def _register_default_operations(self):
        for operation_name in self.definitions.operations:
            self.registry.register(operation_name, self._assert_memory)

    def _assert_memory(self, operation, source="USER", confidence=1.0):
        schema = self.memory.relations.get(operation.predicate) or {}
        if schema.get("type") == "IDENTITY":
            return self.memory.add_identity(
                operation.subject,
                operation.object,
                source,
                confidence,
            )
        return self.memory.add_memory(
            operation.subject,
            operation.predicate,
            operation.object,
            source,
            confidence,
        )

    def execute(self, operation, source="USER", confidence=1.0):
        if operation is None:
            return None

        definition = self.definitions.get(operation.name)
        if definition is None:
            return None

        handler = self.registry.get(operation.name)
        if handler is None:
            return None

        return handler(operation, source, confidence)
